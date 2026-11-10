from typing import Annotated, List

from fastapi import APIRouter, Query

from app.mock import store
from app.mock.deps import OptionalUser
from app.pagination import PageQuery, PageResponse
from app.schemas.error import errors
from app.schemas.hashtag import HashtagStat
from app.schemas.post import PostOut

router = APIRouter(prefix="/hashtags", tags=["해시태그"])


@router.get(
    "/trending",
    response_model=List[HashtagStat],
    summary="인기 해시태그 조회",
    responses=errors(422),
)
def get_trending(limit: Annotated[int, Query(ge=1, le=20)] = 5):
    return store.trending_hashtags(limit)


@router.get(
    "/{tag}",
    response_model=HashtagStat,
    summary="해시태그 정보 조회",
    description="글이 없는 태그는 `post_count`가 0입니다.",
    responses=errors(422),
)
def get_hashtag(tag: str):
    return store.hashtag_stat(tag)


@router.get(
    "/{tag}/posts",
    response_model=PageResponse[PostOut],
    summary="해시태그가 달린 글 조회",
    responses=errors(422),
)
def get_hashtag_posts(tag: str, viewer: OptionalUser, page: PageQuery):
    rows = store.posts_by_hashtag(
        tag, viewer.id if viewer else None, limit=page.fetch_limit, offset=page.offset
    )
    return PageResponse.from_rows(rows, page)
