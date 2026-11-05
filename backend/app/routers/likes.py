from fastapi import APIRouter

from app.errors import NotFoundError
from app.mock import store
from app.mock.deps import LoginUser
from app.schemas.error import errors

router = APIRouter(prefix="/posts/{post_id}/like", tags=["좋아요"])


def _get_post(post_id: int) -> dict:
    post = store.find_post(post_id)
    if post is None:
        raise NotFoundError("게시글을 찾을 수 없습니다.")
    return post


@router.post(
    "",
    status_code=204,
    summary="좋아요",
    description="이미 좋아요한 글이면 아무 일도 일어나지 않습니다.",
    responses=errors(401, 404, 422),
)
def like_post(post_id: int, user: LoginUser):
    post = _get_post(post_id)
    if store.like(post, user.id):
        store.notify(post["author_id"], "like", user.id, post_id, "님이 회원님의 글을 좋아합니다.")


@router.delete("", status_code=204, summary="좋아요 취소", responses=errors(401, 404, 422))
def unlike_post(post_id: int, user: LoginUser):
    store.unlike(_get_post(post_id), user.id)
