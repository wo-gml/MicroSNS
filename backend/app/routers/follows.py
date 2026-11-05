from fastapi import APIRouter

from app.errors import BadRequestError, NotFoundError
from app.mock import store
from app.mock.deps import LoginUser, OptionalUser
from app.pagination import PageQuery, PageResponse
from app.schemas.error import errors
from app.schemas.user import UserListItem

router = APIRouter(prefix="/users/{user_id}", tags=["팔로우"])


def _require_user(user_id: int) -> None:
    if store.find_user(user_id) is None:
        raise NotFoundError("회원을 찾을 수 없습니다.")


@router.post(
    "/follow",
    status_code=204,
    summary="팔로우",
    description="이미 팔로우 중이면 아무 일도 일어나지 않습니다. 자기 자신은 팔로우할 수 없습니다.",
    responses=errors(400, 401, 404, 422),
)
def follow_user(user_id: int, user: LoginUser):
    _require_user(user_id)
    if user_id == user.id:
        raise BadRequestError("자기 자신은 팔로우할 수 없습니다.")
    if store.follow(user.id, user_id):
        store.notify(user_id, "follow", user.id, None, "님이 회원님을 팔로우하기 시작했습니다.")


@router.delete("/follow", status_code=204, summary="언팔로우", responses=errors(401, 404, 422))
def unfollow_user(user_id: int, user: LoginUser):
    _require_user(user_id)
    store.unfollow(user.id, user_id)


@router.get(
    "/followers",
    response_model=PageResponse[UserListItem],
    summary="팔로워 목록 조회",
    responses=errors(404, 422),
)
def list_followers(user_id: int, viewer: OptionalUser, page: PageQuery):
    _require_user(user_id)
    rows = store.list_followers(
        user_id, viewer.id if viewer else None, limit=page.fetch_limit, offset=page.offset
    )
    return PageResponse.from_rows(rows, page)


@router.get(
    "/following",
    response_model=PageResponse[UserListItem],
    summary="팔로잉 목록 조회",
    responses=errors(404, 422),
)
def list_following(user_id: int, viewer: OptionalUser, page: PageQuery):
    _require_user(user_id)
    rows = store.list_following(
        user_id, viewer.id if viewer else None, limit=page.fetch_limit, offset=page.offset
    )
    return PageResponse.from_rows(rows, page)
