from fastapi import APIRouter

from app.errors import ConflictError, ForbiddenError, NotFoundError
from app.mock import store
from app.mock.deps import LoginUser
from app.pagination import PageQuery, PageResponse
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


def _get_recruitment(recruitment_id: int) -> dict:
    recruitment = store.find_recruitment(recruitment_id)
    if recruitment is None:
        raise NotFoundError("모집을 찾을 수 없습니다.")
    return recruitment


def _get_application(application_id: int) -> dict:
    application = store.find_application(application_id)
    if application is None:
        raise NotFoundError("지원을 찾을 수 없습니다.")
    return application


def _author_id(recruitment: dict) -> int:
    return store.find_post(recruitment["post_id"])["author_id"]


@router.patch(
    "/recruitments/{recruitment_id}",
    response_model=RecruitmentOut,
    summary="모집 마감",
    description="글 작성자만 마감할 수 있습니다.",
    responses=errors(401, 403, 404, 422),
)
def close_recruitment(recruitment_id: int, _: RecruitmentUpdate, user: LoginUser):
    recruitment = _get_recruitment(recruitment_id)
    if _author_id(recruitment) != user.id:
        raise ForbiddenError()
    store.close_recruitment(recruitment)
    return store.recruitment_out(recruitment, user.id)


@router.get(
    "/recruitments/{recruitment_id}/applications",
    response_model=PageResponse[ApplicationOut],
    summary="지원자 목록 조회",
    description="글 작성자만 볼 수 있습니다.",
    responses=errors(401, 403, 404, 422),
)
def list_applications(recruitment_id: int, user: LoginUser, page: PageQuery):
    if _author_id(_get_recruitment(recruitment_id)) != user.id:
        raise ForbiddenError()
    rows = store.list_applications(recruitment_id, limit=page.fetch_limit, offset=page.offset)
    return PageResponse.from_rows(rows, page)


@router.post(
    "/recruitments/{recruitment_id}/applications",
    status_code=201,
    response_model=ApplicationOut,
    summary="모집 지원",
    description="작성자는 지원할 수 없고, 마감됐거나 이미 지원한 모집에는 지원할 수 없습니다.",
    responses=errors(401, 403, 404, 409, 422),
)
def apply(recruitment_id: int, body: ApplicationCreate, user: LoginUser):
    recruitment = _get_recruitment(recruitment_id)
    author_id = _author_id(recruitment)
    if author_id == user.id:
        raise ForbiddenError("내 모집에는 지원할 수 없습니다.")
    if store.find_my_application(recruitment_id, user.id):
        raise ConflictError("이미 지원한 모집입니다.")
    if not store.is_recruiting(recruitment):
        raise ConflictError("마감된 모집입니다.")
    application = store.create_application(recruitment_id, user.id, body.message)
    store.notify(
        author_id, "application", user.id, recruitment["post_id"], "님이 회원님의 모집에 지원했습니다."
    )
    return store.application_out(application)


@router.patch(
    "/applications/{application_id}",
    response_model=ApplicationOut,
    summary="지원 수락/거절",
    description="글 작성자만 처리할 수 있고, 대기 중인 지원만 처리합니다. 정원이 차면 수락할 수 없습니다.",
    responses=errors(401, 403, 404, 409, 422),
)
def decide_application(application_id: int, body: ApplicationUpdate, user: LoginUser):
    application = _get_application(application_id)
    recruitment = _get_recruitment(application["recruitment_id"])
    if _author_id(recruitment) != user.id:
        raise ForbiddenError()
    if application["status"] != "pending":
        raise ConflictError("이미 처리한 지원입니다.")
    if body.status == "accepted" and store.is_full(recruitment):
        raise ConflictError("모집 인원이 다 찼습니다.")
    store.set_application_status(application, body.status)
    store.notify(
        application["member_id"],
        "application_result",
        user.id,
        recruitment["post_id"],
        _RESULT_MESSAGES[body.status],
    )
    return store.application_out(application)


@router.delete(
    "/applications/{application_id}",
    status_code=204,
    summary="지원 취소",
    description="지원한 본인만, 대기 중일 때만 취소할 수 있습니다.",
    responses=errors(401, 403, 404, 409, 422),
)
def cancel_application(application_id: int, user: LoginUser):
    application = _get_application(application_id)
    if application["member_id"] != user.id:
        raise ForbiddenError()
    if application["status"] != "pending":
        raise ConflictError("이미 처리된 지원은 취소할 수 없습니다.")
    store.delete_application(application_id)
    recruitment = _get_recruitment(application["recruitment_id"])
    store.retract_notification(
        _author_id(recruitment), "application", user.id, recruitment["post_id"]
    )
