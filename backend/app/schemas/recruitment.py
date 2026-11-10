from datetime import datetime
from typing import Annotated, Literal, Optional

from pydantic import AwareDatetime, BaseModel, Field, StringConstraints

from app.schemas.user import UserSummary

RecruitmentType = Literal["study", "project"]
RecruitmentStatus = Literal["open", "closed"]
ApplicationStatus = Literal["pending", "accepted", "rejected"]


class RecruitmentCreate(BaseModel):
    type: RecruitmentType
    capacity: int = Field(ge=1)
    deadline: AwareDatetime


class RecruitmentUpdate(BaseModel):
    status: Literal["closed"]


class MyApplication(BaseModel):
    id: int
    message: Optional[str] = None
    status: ApplicationStatus


class RecruitmentOut(BaseModel):
    id: int
    post_id: int
    type: RecruitmentType
    capacity: int
    deadline: datetime
    status: RecruitmentStatus
    created_at: datetime
    updated_at: datetime
    accepted_count: int
    my_application: Optional[MyApplication] = None


class ApplicationCreate(BaseModel):
    message: Optional[Annotated[str, StringConstraints(max_length=300)]] = None


class ApplicationUpdate(BaseModel):
    status: Literal["accepted", "rejected"]


class ApplicationOut(MyApplication):
    recruitment_id: int
    applicant: UserSummary
    created_at: datetime
    updated_at: datetime
