"""라우터에서 주입받아 쓰는 공통 의존성.

    @router.post("/posts")
    def create_post(body: PostCreate, db: DbConn, user: LoginUser): ...
"""

from typing import Annotated, Optional

from fastapi import Depends
from fastapi.security import APIKeyCookie
from pymysql.connections import Connection

from app.db import get_db
from app.errors import UnauthorizedError
from app.repositories import user_repo
from app.schemas.user import CurrentUser
from app.security import AUTH_COOKIE_NAME, decode_access_token

DbConn = Annotated[Connection, Depends(get_db)]

# Swagger 문서에 쿠키 인증으로 표시됩니다. 쿠키가 없을 때의 응답은 아래에서 직접 정합니다.
_auth_cookie = APIKeyCookie(name=AUTH_COOKIE_NAME, auto_error=False)
AuthToken = Annotated[Optional[str], Depends(_auth_cookie)]


def get_current_user(db: DbConn, token: AuthToken) -> CurrentUser:
    if not token:
        raise UnauthorizedError()
    row = user_repo.find_by_id(db, decode_access_token(token))
    if row is None:
        raise UnauthorizedError("로그인 정보가 유효하지 않습니다.")
    return CurrentUser(**row)


def get_optional_user(db: DbConn, token: AuthToken) -> Optional[CurrentUser]:
    """로그인하지 않아도 되는 조회용입니다. 쿠키가 만료됐으면 비로그인으로 봅니다."""
    try:
        return get_current_user(db, token)
    except UnauthorizedError:
        return None


LoginUser = Annotated[CurrentUser, Depends(get_current_user)]
OptionalUser = Annotated[Optional[CurrentUser], Depends(get_optional_user)]
