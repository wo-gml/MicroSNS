from datetime import datetime
from typing import Annotated, List, Optional

from pydantic import BaseModel, Field, StringConstraints

from app.schemas.recruitment import RecruitmentCreate, RecruitmentOut
from app.schemas.user import UserSummary

# 외부 주소를 글에 넣지 못하도록 이 서버가 제공하는 사진만 허용합니다.
ImageUrl = Annotated[str, StringConstraints(pattern=r"^/api/(uploads|mock-photos)/[\w-]+\.\w+$")]


class PostCreate(BaseModel):
    content: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]
    image_urls: List[ImageUrl] = Field(default=[], max_length=2)
    recruitment: Optional[RecruitmentCreate] = None


class PostAuthor(UserSummary):
    is_following: bool


class PostOut(BaseModel):
    id: int
    author: PostAuthor
    content: str
    image_urls: List[str]
    created_at: datetime
    like_count: int
    comment_count: int
    liked_by_me: bool
    recruitment: Optional[RecruitmentOut] = None


class UploadOut(BaseModel):
    url: str
