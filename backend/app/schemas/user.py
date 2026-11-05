from datetime import datetime
from typing import Annotated, Optional

from pydantic import BaseModel, Field, StringConstraints


class CurrentUser(BaseModel):
    """로그인한 회원 본인 정보. password_hash는 포함하지 않습니다."""

    id: int
    email: str
    name: str
    bio: Optional[str] = None
    created_at: datetime


class LoginRequest(BaseModel):
    email: str = Field(max_length=255)
    password: str = Field(max_length=128)


class SignupRequest(BaseModel):
    email: str = Field(max_length=255, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str = Field(min_length=8, max_length=128)
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=50)]
    bio: Optional[Annotated[str, StringConstraints(strip_whitespace=True, max_length=200)]] = None


class UserSummary(BaseModel):
    id: int
    name: str


class UserListItem(UserSummary):
    bio: Optional[str] = None
    is_following: bool


class UserProfile(UserListItem):
    created_at: datetime
    post_count: int
    follower_count: int
    following_count: int
