"""메모리 저장소에서 로그인 회원을 찾는 의존성. DB가 준비되면 app.deps로 바꿉니다."""

from typing import Annotated, Optional

from fastapi import Depends
from fastapi.security import APIKeyCookie

from app.errors import UnauthorizedError
from app.mock import store
from app.schemas.user import CurrentUser
from app.security import AUTH_COOKIE_NAME, decode_access_token

# Swagger 문서에 쿠키 인증으로 표시됩니다. 쿠키가 없을 때의 응답은 아래에서 직접 정합니다.
_auth_cookie = APIKeyCookie(name=AUTH_COOKIE_NAME, auto_error=False)
AuthToken = Annotated[Optional[str], Depends(_auth_cookie)]


def get_current_user(token: AuthToken) -> CurrentUser:
    if not token:
        raise UnauthorizedError()
    user = store.find_user(decode_access_token(token))
    if user is None:
        raise UnauthorizedError("로그인 정보가 유효하지 않습니다.")
    return CurrentUser(**user)


def get_optional_user(token: AuthToken) -> Optional[CurrentUser]:
    """로그인하지 않아도 되는 조회용입니다. 쿠키가 만료됐으면 비로그인으로 봅니다."""
    try:
        return get_current_user(token)
    except UnauthorizedError:
        return None


LoginUser = Annotated[CurrentUser, Depends(get_current_user)]
OptionalUser = Annotated[Optional[CurrentUser], Depends(get_optional_user)]
