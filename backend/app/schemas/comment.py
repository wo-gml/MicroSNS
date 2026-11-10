from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, StringConstraints

from app.schemas.user import UserSummary


class CommentCreate(BaseModel):
    content: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=300)]


class CommentOut(BaseModel):
    id: int
    post_id: int
    author: UserSummary
    content: str
    created_at: datetime
