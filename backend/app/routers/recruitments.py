from fastapi import APIRouter

from app.db import transaction
from app.deps import DbConn, LoginUser
from app.errors import ConflictError, ForbiddenError, NotFoundError
from app.pagination import PageQuery, PageResponse
from app.repositories import notification_repo, recruitment_repo
from app.schemas.error import errors
from app.schemas.recruitment import (
    ApplicationCreate,
    ApplicationOut,
    ApplicationUpdate,
    RecruitmentOut,
    RecruitmentUpdate,
)

router = APIRouter(tags=["모집/지원"])

_RESULT_MESSAGES = {
    "accepted": "님이 회원님의 지원을 수락했습니다.",
    "rejected": "님이 회원님의 지원을 거절했습니다.",
}


def _get_recruitment(db: DbConn, recruitment_id: int) -> dict:
    recruitment = recruitment_repo.find(db, recruitment_id)
    if recruitment is None:
        raise NotFoundError("모집을 찾을 수 없습니다.")
    return recruitment


def _get_application(db: DbConn, application_id: int) -> dict:
    application = recruitment_repo.find_application(db, application_id)
    if application is None:
        raise NotFoundError("지원을 찾을 수 없습니다.")
    return application


@router.patch(
    "/recruitments/{recruitment_id}",
    response_model=RecruitmentOut,
    summary="모집 마감",
    description="글 작성자만 마감할 수 있습니다.",
    responses=errors(401, 403, 404, 422),
)
def close_recruitment(recruitment_id: int, _: RecruitmentUpdate, db: DbConn, user: LoginUser):
    if _get_recruitment(db, recruitment_id)["author_id"] != user.id:
        raise ForbiddenError()
    recruitment_repo.close(db, recruitment_id)
    return recruitment_repo.out(db, recruitment_id, user.id)


@router.get(
    "/recruitments/{recruitment_id}/applications",
    response_model=PageResponse[ApplicationOut],
    summary="지원자 목록 조회",
    description="글 작성자만 볼 수 있습니다.",
    responses=errors(401, 403, 404, 422),
)
def list_applications(recruitment_id: int, db: DbConn, user: LoginUser, page: PageQuery):
    if _get_recruitment(db, recruitment_id)["author_id"] != user.id:
        raise ForbiddenError()
    rows = recruitment_repo.list_applications(
        db, recruitment_id, limit=page.fetch_limit, offset=page.offset
    )
    return PageResponse.from_rows(rows, page)


@router.post(
    "/recruitments/{recruitment_id}/applications",
    status_code=201,
    response_model=ApplicationOut,
    summary="모집 지원",
    description="작성자는 지원할 수 없고, 마감됐거나 이미 지원한 모집에는 지원할 수 없습니다.",
    responses=errors(401, 403, 404, 409, 422),
)
def apply(recruitment_id: int, body: ApplicationCreate, db: DbConn, user: LoginUser):
    recruitment = _get_recruitment(db, recruitment_id)
    if recruitment["author_id"] == user.id:
        raise ForbiddenError("내 모집에는 지원할 수 없습니다.")
    if recruitment_repo.has_applied(db, recruitment_id, user.id):
        raise ConflictError("이미 지원한 모집입니다.")
    if not recruitment_repo.is_recruiting(db, recruitment_id):
        raise ConflictError("마감된 모집입니다.")
    # 동시에 두 번 지원하면 UNIQUE(recruitment_id, member_id)가 하나를 409로 막습니다.
    with transaction(db):
        application_id = recruitment_repo.create_application(
            db, recruitment_id, user.id, body.message
        )
        notification_repo.notify(
            db,
            recruitment["author_id"],
            "application",
            user.id,
            recruitment["post_id"],
            "님이 회원님의 모집에 지원했습니다.",
        )
    return recruitment_repo.application_out(db, application_id)


@router.patch(
    "/applications/{application_id}",
    response_model=ApplicationOut,
    summary="지원 수락/거절",
    description="글 작성자만 처리할 수 있고, 대기 중인 지원만 처리합니다. 정원이 차면 수락할 수 없습니다.",
    responses=errors(401, 403, 404, 409, 422),
)
def decide_application(application_id: int, body: ApplicationUpdate, db: DbConn, user: LoginUser):
    application = _get_application(db, application_id)
    recruitment = _get_recruitment(db, application["recruitment_id"])
    if recruitment["author_id"] != user.id:
        raise ForbiddenError()

    # 두 지원을 동시에 수락해도 정원을 넘지 않도록 모집 행을 잠근 뒤 다시 확인합니다.
    with transaction(db):
        locked = recruitment_repo.lock(db, recruitment["id"])
        current = recruitment_repo.find_application(db, application_id)
        if locked is None or current is None:
            raise NotFoundError("지원을 찾을 수 없습니다.")
        if current["status"] != "pending":
            raise ConflictError("이미 처리한 지원입니다.")
        if (
            body.status == "accepted"
            and recruitment_repo.accepted_count(db, recruitment["id"]) >= locked["capacity"]
        ):
            raise ConflictError("모집 인원이 다 찼습니다.")
        if not recruitment_repo.decide(db, application_id, body.status):
            raise ConflictError("이미 처리한 지원입니다.")
        notification_repo.notify(
            db,
            application["member_id"],
            "application_result",
            user.id,
            recruitment["post_id"],
            _RESULT_MESSAGES[body.status],
        )
    return recruitment_repo.application_out(db, application_id)


@router.delete(
    "/applications/{application_id}",
    status_code=204,
    summary="지원 취소",
    description="지원한 본인만, 대기 중일 때만 취소할 수 있습니다.",
    responses=errors(401, 403, 404, 409, 422),
)
def cancel_application(application_id: int, db: DbConn, user: LoginUser):
    application = _get_application(db, application_id)
    if application["member_id"] != user.id:
        raise ForbiddenError()
    recruitment = _get_recruitment(db, application["recruitment_id"])
    with transaction(db):
        # 그사이 작성자가 수락·거절했으면 지우지 않습니다.
        if not recruitment_repo.delete_pending(db, application_id):
            raise ConflictError("이미 처리된 지원은 취소할 수 없습니다.")
        notification_repo.retract(
            db, recruitment["author_id"], "application", user.id, recruitment["post_id"]
        )
