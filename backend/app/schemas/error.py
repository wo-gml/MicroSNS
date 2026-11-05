"""공통 에러 응답 형식. Swagger 문서에 실제 형식이 보이도록 라우터에서 errors()로 지정합니다."""

from typing import List, Optional

from pydantic import BaseModel


class FieldError(BaseModel):
    field: str
    message: str


class ErrorBody(BaseModel):
    code: str
    message: str
    details: Optional[List[FieldError]] = None


class ErrorResponse(BaseModel):
    error: ErrorBody


def errors(*status_codes: int) -> dict:
    return {status_code: {"model": ErrorResponse} for status_code in status_codes}
