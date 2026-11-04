"""라우터에서 주입받아 쓰는 공통 의존성.

    @router.post("/posts")
    def create_post(body: PostCreate, db: DbConn, user: LoginUser): ...
"""

from typing import Annotated, Optional

from fastapi import Cookie, Depends
from pymysql.connections import Connection

from app.db import get_db
from app.errors import UnauthorizedError
from app.repositories import user_repo
from app.schemas.user import CurrentUser
from app.security import AUTH_COOKIE_NAME, decode_access_token

DbConn = Annotated[Connection, Depends(get_db)]


def get_current_user(
    db: DbConn,
    token: Annotated[Optional[str], Cookie(alias=AUTH_COOKIE_NAME)] = None,
) -> CurrentUser:
    if not token:
        raise UnauthorizedError()
    row = user_repo.find_by_id(db, decode_access_token(token))
    if row is None:
        raise UnauthorizedError("로그인 정보가 유효하지 않습니다.")
    return CurrentUser(**row)


LoginUser = Annotated[CurrentUser, Depends(get_current_user)]
