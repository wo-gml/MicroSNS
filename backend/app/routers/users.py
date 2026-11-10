from fastapi import APIRouter

from app.deps import DbConn, OptionalUser
from app.errors import NotFoundError
from app.pagination import PageQuery, PageResponse
from app.repositories import post_repo, user_repo
from app.schemas.error import errors
from app.schemas.post import PostOut
from app.schemas.user import UserProfile

router = APIRouter(prefix="/users", tags=["회원"])


def _require_user(db: DbConn, user_id: int) -> None:
    if not user_repo.exists(db, user_id):
        raise NotFoundError("회원을 찾을 수 없습니다.")


@router.get(
    "/{user_id}",
    response_model=UserProfile,
    summary="프로필 조회",
    responses=errors(404, 422),
)
def get_user(user_id: int, db: DbConn, viewer: OptionalUser):
    profile = user_repo.profile(db, user_id, viewer.id if viewer else None)
    if profile is None:
        raise NotFoundError("회원을 찾을 수 없습니다.")
    return profile


@router.get(
    "/{user_id}/posts",
    response_model=PageResponse[PostOut],
    summary="회원이 쓴 글 조회",
    responses=errors(404, 422),
)
def get_user_posts(user_id: int, db: DbConn, viewer: OptionalUser, page: PageQuery):
    _require_user(db, user_id)
    rows = post_repo.by_author(
        db, user_id, viewer.id if viewer else None, limit=page.fetch_limit, offset=page.offset
    )
    return PageResponse.from_rows(rows, page)


@router.get(
    "/{user_id}/likes",
    response_model=PageResponse[PostOut],
    summary="회원이 좋아요한 글 조회",
    responses=errors(404, 422),
)
def get_user_likes(user_id: int, db: DbConn, viewer: OptionalUser, page: PageQuery):
    _require_user(db, user_id)
    rows = post_repo.liked_by(
        db, user_id, viewer.id if viewer else None, limit=page.fetch_limit, offset=page.offset
    )
    return PageResponse.from_rows(rows, page)
