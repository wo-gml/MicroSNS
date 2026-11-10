from fastapi import APIRouter

from app.db import transaction
from app.deps import DbConn, LoginUser
from app.errors import ForbiddenError, NotFoundError
from app.pagination import PageQuery, PageResponse
from app.repositories import comment_repo, notification_repo, post_repo
from app.schemas.comment import CommentCreate, CommentOut
from app.schemas.error import errors

router = APIRouter(tags=["댓글"])


def _get_post(db: DbConn, post_id: int) -> dict:
    post = post_repo.find(db, post_id)
    if post is None:
        raise NotFoundError("게시글을 찾을 수 없습니다.")
    return post


@router.get(
    "/posts/{post_id}/comments",
    response_model=PageResponse[CommentOut],
    summary="댓글 목록 조회",
    description="작성 시각 오름차순입니다.",
    responses=errors(404, 422),
)
def list_comments(post_id: int, db: DbConn, page: PageQuery):
    _get_post(db, post_id)
    rows = comment_repo.list_by_post(db, post_id, limit=page.fetch_limit, offset=page.offset)
    return PageResponse.from_rows(rows, page)


@router.post(
    "/posts/{post_id}/comments",
    status_code=201,
    response_model=CommentOut,
    summary="댓글 작성",
    responses=errors(401, 404, 422),
)
def create_comment(post_id: int, body: CommentCreate, db: DbConn, user: LoginUser):
    post = _get_post(db, post_id)
    with transaction(db):
        comment_id = comment_repo.create(db, post_id, user.id, body.content)
        notification_repo.notify(
            db, post["author_id"], "comment", user.id, post_id, "님이 회원님의 글에 댓글을 남겼습니다."
        )
    return comment_repo.out(db, comment_id)


@router.delete(
    "/comments/{comment_id}",
    status_code=204,
    summary="댓글 삭제",
    description="작성자만 지울 수 있습니다.",
    responses=errors(401, 403, 404, 422),
)
def delete_comment(comment_id: int, db: DbConn, user: LoginUser):
    comment = comment_repo.find(db, comment_id)
    if comment is None:
        raise NotFoundError("댓글을 찾을 수 없습니다.")
    if comment["author_id"] != user.id:
        raise ForbiddenError()
    with transaction(db):
        if comment_repo.delete(db, comment_id):
            notification_repo.retract(
                db, comment["post_author_id"], "comment", user.id, comment["post_id"]
            )
