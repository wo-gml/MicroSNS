"""목록 API 공통 페이지네이션.

    @router.get("/posts", response_model=PageResponse[PostOut])
    def list_posts(db: DbConn, page: PageQuery):
        rows = post_repo.list_posts(db, limit=page.fetch_limit, offset=page.offset)
        return PageResponse.from_rows(rows, page)

리포지토리는 limit + 1개(fetch_limit)를 조회합니다. 초과분이 있으면 다음 페이지가 있다는
뜻이므로 COUNT 쿼리를 따로 실행하지 않아도 됩니다.
"""

from typing import Annotated, Generic, List, Sequence, TypeVar

from fastapi import Depends, Query
from pydantic import BaseModel

T = TypeVar("T")


class PageParams:
    def __init__(
        self,
        limit: Annotated[int, Query(ge=1, le=100)] = 20,
        offset: Annotated[int, Query(ge=0)] = 0,
    ):
        self.limit = limit
        self.offset = offset

    @property
    def fetch_limit(self) -> int:
        return self.limit + 1


PageQuery = Annotated[PageParams, Depends()]


class PageResponse(BaseModel, Generic[T]):
    items: List[T]
    limit: int
    offset: int
    has_more: bool

    @classmethod
    def from_rows(cls, rows: Sequence[T], page: PageParams) -> "PageResponse[T]":
        return cls(
            items=list(rows[: page.limit]),
            limit=page.limit,
            offset=page.offset,
            has_more=len(rows) > page.limit,
        )
