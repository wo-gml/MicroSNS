from datetime import datetime, timezone

from fastapi import APIRouter

from app.errors import BadRequestError, ForbiddenError, NotFoundError
from app.mock import store
from app.mock.deps import LoginUser, OptionalUser
from app.pagination import PageQuery, PageResponse
from app.schemas.error import errors
from app.schemas.post import PostCreate, PostOut

router = APIRouter(prefix="/posts", tags=["게시글"])


@router.get(
    "/feed",
    response_model=PageResponse[PostOut],
    summary="홈 피드 조회",
    description="내 글과 내가 팔로우한 회원의 글을 최신순으로 돌려줍니다.",
    responses=errors(401, 422),
)
def get_feed(user: LoginUser, page: PageQuery):
    rows = store.feed(user.id, limit=page.fetch_limit, offset=page.offset)
    return PageResponse.from_rows(rows, page)


@router.post(
    "",
    status_code=201,
    response_model=PostOut,
    summary="글 작성",
    description="모집 정보를 함께 보내면 모집 글이 됩니다. 사진은 먼저 `POST /uploads`로 올립니다.",
    responses=errors(400, 401, 422),
)
def create_post(body: PostCreate, user: LoginUser):
    recruitment = body.recruitment
    if recruitment and recruitment.deadline <= datetime.now(timezone.utc):
        raise BadRequestError("마감일은 지금 이후로 정해 주세요.")
    post = store.create_post(
        user.id,
        body.content,
        body.image_urls,
        recruitment.model_dump() if recruitment else None,
    )
    return store.post_out(post, user.id)


@router.get(
    "/{post_id}",
    response_model=PostOut,
    summary="글 상세 조회",
    responses=errors(404, 422),
)
def get_post(post_id: int, viewer: OptionalUser):
    post = store.find_post(post_id)
    if post is None:
        raise NotFoundError("게시글을 찾을 수 없습니다.")
    return store.post_out(post, viewer.id if viewer else None)


@router.delete(
    "/{post_id}",
    status_code=204,
    summary="글 삭제",
    description="작성자만 지울 수 있습니다. 댓글, 모집, 지원, 알림도 함께 지워집니다.",
    responses=errors(401, 403, 404, 422),
)
def delete_post(post_id: int, user: LoginUser):
    post = store.find_post(post_id)
    if post is None:
        raise NotFoundError("게시글을 찾을 수 없습니다.")
    if post["author_id"] != user.id:
        raise ForbiddenError()
    store.delete_post(post_id)
