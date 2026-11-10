from fastapi import APIRouter, Response

from app.errors import ConflictError, UnauthorizedError
from app.deps import DbConn, LoginUser
from app.repositories import user_repo
from app.schemas.error import errors
from app.schemas.user import CurrentUser, LoginRequest, SignupRequest
from app.security import (
    clear_auth_cookie,
    create_access_token,
    hash_password,
    set_auth_cookie,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["인증"])


@router.post(
    "/signup",
    status_code=201,
    response_model=CurrentUser,
    summary="회원가입",
    description="가입과 동시에 로그인 쿠키를 심습니다.",
    responses=errors(409, 422),
)
def signup(body: SignupRequest, response: Response, db: DbConn):
    if user_repo.find_by_email(db, body.email):
        raise ConflictError("이미 가입된 이메일입니다.")
    user = user_repo.create(db, body.email, hash_password(body.password), body.name, body.bio or None)
    set_auth_cookie(response, create_access_token(user["id"]))
    return user


@router.post(
    "/login",
    response_model=CurrentUser,
    summary="로그인",
    description="성공하면 httpOnly 쿠키 `access_token`을 심습니다.",
    responses=errors(401, 422),
)
def login(body: LoginRequest, response: Response, db: DbConn):
    user = user_repo.find_by_email(db, body.email)
    if not user or not verify_password(body.password, user["password_hash"]):
        raise UnauthorizedError("이메일 또는 비밀번호가 올바르지 않습니다.")
    set_auth_cookie(response, create_access_token(user["id"]))
    return user


@router.post("/logout", status_code=204, summary="로그아웃")
def logout(response: Response):
    clear_auth_cookie(response)


@router.get("/me", response_model=CurrentUser, summary="내 정보 조회", responses=errors(401))
def me(user: LoginUser):
    return user
