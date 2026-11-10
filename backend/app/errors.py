"""공통 에러 형식과 예외 처리기.

모든 에러 응답은 {"error": {"code": ..., "message": ...}} 형식입니다.
라우터와 서비스에서는 아래 AppError 계열을 raise하면 됩니다.

    raise NotFoundError("게시글을 찾을 수 없습니다.")
"""

import logging
from typing import Optional

import pymysql
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


class AppError(Exception):
    status_code = 400
    code = "BAD_REQUEST"
    default_message = "잘못된 요청입니다."

    def __init__(self, message: Optional[str] = None):
        self.message = message or self.default_message
        super().__init__(self.message)


class BadRequestError(AppError):
    pass


class UnauthorizedError(AppError):
    status_code = 401
    code = "UNAUTHORIZED"
    default_message = "로그인이 필요합니다."


class ForbiddenError(AppError):
    status_code = 403
    code = "FORBIDDEN"
    default_message = "권한이 없습니다."


class NotFoundError(AppError):
    status_code = 404
    code = "NOT_FOUND"
    default_message = "대상을 찾을 수 없습니다."


class ConflictError(AppError):
    status_code = 409
    code = "CONFLICT"
    default_message = "현재 상태와 충돌하는 요청입니다."


# MySQL 에러 번호 -> (HTTP 상태, 에러 코드, 메시지)
_DB_UNAVAILABLE = (503, "DB_UNAVAILABLE", "데이터베이스에 연결할 수 없습니다.")
_DB_BUSY = (503, "DB_BUSY", "요청이 몰리고 있습니다. 잠시 후 다시 시도해 주세요.")
MYSQL_ERRORS = {
    1062: (409, "CONFLICT", "이미 존재하는 데이터입니다."),
    1451: (409, "CONFLICT", "다른 데이터가 참조하고 있어 삭제할 수 없습니다."),
    1452: (404, "NOT_FOUND", "참조하는 대상을 찾을 수 없습니다."),
    3819: (400, "BAD_REQUEST", "허용되지 않는 값입니다."),
    1406: (400, "BAD_REQUEST", "입력값이 너무 깁니다."),
    1205: _DB_BUSY,
    1213: _DB_BUSY,
    1045: _DB_UNAVAILABLE,
    1049: _DB_UNAVAILABLE,
    2002: _DB_UNAVAILABLE,
    2003: _DB_UNAVAILABLE,
    2006: _DB_UNAVAILABLE,
    2013: _DB_UNAVAILABLE,
}

HTTP_ERROR_CODES = {
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
}


def _error_response(status_code: int, code: str, message: str, **extra) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message, **extra}},
    )


async def _handle_app_error(_: Request, exc: AppError) -> JSONResponse:
    return _error_response(exc.status_code, exc.code, exc.message)


async def _handle_http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
    response = _error_response(
        exc.status_code,
        HTTP_ERROR_CODES.get(exc.status_code, "HTTP_ERROR"),
        str(exc.detail),
    )
    if exc.headers:
        response.headers.update(exc.headers)
    return response


async def _handle_validation_error(
    _: Request, exc: RequestValidationError
) -> JSONResponse:
    # 입력값(비밀번호 등)이 응답에 되돌아가지 않도록 위치와 메시지만 담습니다.
    details = [
        {"field": ".".join(str(part) for part in error["loc"]), "message": error["msg"]}
        for error in exc.errors()
    ]
    return _error_response(
        422, "VALIDATION_ERROR", "입력값을 확인해 주세요.", details=details
    )


async def _handle_mysql_error(_: Request, exc: pymysql.MySQLError) -> JSONResponse:
    errno = exc.args[0] if exc.args else None
    mapped = MYSQL_ERRORS.get(errno)
    if mapped is None:
        # SQL이나 테이블 정보가 클라이언트에 노출되지 않도록 로그에만 남깁니다.
        logger.error("처리되지 않은 MySQL 에러: %r", exc)
        return _error_response(500, "INTERNAL_ERROR", "서버 오류가 발생했습니다.")
    status_code, code, message = mapped
    if status_code >= 500:
        logger.error("MySQL 에러: %r", exc)
    return _error_response(status_code, code, message)


async def _handle_unexpected_error(_: Request, exc: Exception) -> JSONResponse:
    logger.error("처리되지 않은 예외", exc_info=exc)
    return _error_response(500, "INTERNAL_ERROR", "서버 오류가 발생했습니다.")


async def _catch_unexpected_error(request: Request, call_next) -> Response:
    # Exception 처리기로 등록하면 CORS 미들웨어 바깥에서 실행되어 500 응답에 CORS 헤더가 빠지고,
    # 브라우저는 실제 에러 대신 CORS 오류를 보여줍니다. 그래서 미들웨어로 안쪽에서 잡습니다.
    try:
        return await call_next(request)
    except Exception as exc:
        return await _handle_unexpected_error(request, exc)


def register_error_handlers(app: FastAPI) -> None:
    """CORS 미들웨어보다 먼저 호출해야 합니다. 나중에 추가한 미들웨어가 바깥쪽에 놓입니다."""
    app.add_exception_handler(AppError, _handle_app_error)
    app.add_exception_handler(StarletteHTTPException, _handle_http_error)
    app.add_exception_handler(RequestValidationError, _handle_validation_error)
    app.add_exception_handler(pymysql.MySQLError, _handle_mysql_error)
    app.middleware("http")(_catch_unexpected_error)
