from fastapi import APIRouter

from app.errors import NotFoundError
from app.mock import store
from app.mock.deps import OptionalUser
from app.pagination import PageQuery, PageResponse
from app.schemas.error import errors
from app.schemas.post import PostOut
from app.schemas.user import UserProfile

router = APIRouter(prefix="/users", tags=["회원"])


def _get_user(user_id: int) -> dict:
    user = store.find_user(user_id)
    if user is None:
        raise NotFoundError("회원을 찾을 수 없습니다.")
    return user


@router.get(
    "/{user_id}",
    response_model=UserProfile,
    summary="프로필 조회",
    responses=errors(404, 422),
)
def get_user(user_id: int, viewer: OptionalUser):
    return store.user_profile(_get_user(user_id), viewer.id if viewer else None)


@router.get(
    "/{user_id}/posts",
    response_model=PageResponse[PostOut],
    summary="회원이 쓴 글 조회",
    responses=errors(404, 422),
)
def get_user_posts(user_id: int, viewer: OptionalUser, page: PageQuery):
    _get_user(user_id)
    rows = store.posts_by_author(
        user_id, viewer.id if viewer else None, limit=page.fetch_limit, offset=page.offset
    )
    return PageResponse.from_rows(rows, page)


@router.get(
    "/{user_id}/likes",
    response_model=PageResponse[PostOut],
    summary="회원이 좋아요한 글 조회",
    responses=errors(404, 422),
)
def get_user_likes(user_id: int, viewer: OptionalUser, page: PageQuery):
    _get_user(user_id)
    rows = store.posts_liked_by(
        user_id, viewer.id if viewer else None, limit=page.fetch_limit, offset=page.offset
    )
    return PageResponse.from_rows(rows, page)
