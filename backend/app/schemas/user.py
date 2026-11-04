from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class CurrentUser(BaseModel):
    """로그인한 회원 본인 정보. password_hash는 포함하지 않습니다."""

    id: int
    email: str
    name: str
    bio: Optional[str] = None
    created_at: datetime
