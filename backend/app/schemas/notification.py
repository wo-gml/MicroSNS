from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel

from app.schemas.user import UserSummary

NotificationType = Literal["like", "comment", "follow", "application", "application_result"]


class NotificationOut(BaseModel):
    id: int
    type: NotificationType
    actor: UserSummary
    post_id: Optional[int] = None
    content: str
    is_read: bool
    created_at: datetime


class UnreadCount(BaseModel):
    count: int
