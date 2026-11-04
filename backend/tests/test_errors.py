"""DB 없이 확인하는 에러 형식, 인증 의존성, 페이지네이션 테스트."""

import pymysql
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel

from app.db import get_db
from app.deps import LoginUser
from app.errors import ConflictError, ForbiddenError, NotFoundError, register_error_handlers
from app.pagination import PageQuery, PageResponse
from app.repositories import user_repo
from app.security import AUTH_COOKIE_NAME, create_access_token


class SignupBody(BaseModel):
    email: str
    password: str


def build_client() -> TestClient:
    app = FastAPI()
    register_error_handlers(app)
    app.dependency_overrides[get_db] = lambda: object()

    errors = {
        "forbidden": ForbiddenError("내 글이 아닙니다."),
        "not-found": NotFoundError(),
        "conflict": ConflictError("이미 신청했습니다."),
        "unexpected": RuntimeError("숨겨야 할 내부 정보"),
        "dup": pymysql.err.IntegrityError(1062, "Duplicate entry 'a@b.c'"),
        "fk": pymysql.err.IntegrityError(1452, "fk detail"),
        "check": pymysql.err.OperationalError(3819, "check detail"),
        "down": pymysql.err.OperationalError(2003, "Can't connect to 10.0.0.1"),
        "syntax": pymysql.err.ProgrammingError(1064, "near SELECT password_hash"),
    }

    @app.get("/raise/{name}")
    def raise_error(name: str):
        raise errors[name]

    @app.post("/signup")
    def signup(body: SignupBody):
        return body

    @app.get("/me")
    def me(user: LoginUser):
        return user

    @app.get("/items", response_model=PageResponse[int])
    def items(page: PageQuery):
        rows = list(range(100, 125))[page.offset : page.offset + page.fetch_limit]
        return PageResponse.from_rows(rows, page)

    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def client():
    return build_client()


@pytest.mark.parametrize(
    "name, status, code, message",
    [
        ("forbidden", 403, "FORBIDDEN", "내 글이 아닙니다."),
        ("not-found", 404, "NOT_FOUND", "대상을 찾을 수 없습니다."),
        ("conflict", 409, "CONFLICT", "이미 신청했습니다."),
        ("dup", 409, "CONFLICT", "이미 존재하는 데이터입니다."),
        ("fk", 404, "NOT_FOUND", "참조하는 대상을 찾을 수 없습니다."),
        ("check", 400, "BAD_REQUEST", "허용되지 않는 값입니다."),
        ("down", 503, "DB_UNAVAILABLE", "데이터베이스에 연결할 수 없습니다."),
        ("syntax", 500, "INTERNAL_ERROR", "서버 오류가 발생했습니다."),
        ("unexpected", 500, "INTERNAL_ERROR", "서버 오류가 발생했습니다."),
    ],
)
def test_errors_use_common_format_without_leaking_details(
    client, name, status, code, message
):
    response = client.get(f"/raise/{name}")
    assert response.status_code == status
    assert response.json() == {"error": {"code": code, "message": message}}


def test_unknown_route_uses_common_format(client):
    response = client.get("/no-such-route")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_validation_error_does_not_echo_input(client):
    response = client.post("/signup", json={"password": "my-secret-password"})
    assert response.status_code == 422
    body = response.json()["error"]
    assert body["code"] == "VALIDATION_ERROR"
    assert body["details"][0]["field"] == "body.email"
    assert "my-secret-password" not in response.text


def test_login_required_without_cookie(client):
    response = client.get("/me")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_invalid_token_is_rejected(client):
    client.cookies.set(AUTH_COOKIE_NAME, "garbage")
    assert client.get("/me").status_code == 401


def test_token_of_missing_member_is_rejected(client, monkeypatch):
    monkeypatch.setattr(user_repo, "find_by_id", lambda db, member_id: None)
    client.cookies.set(AUTH_COOKIE_NAME, create_access_token(999))
    assert client.get("/me").status_code == 401


@pytest.mark.parametrize(
    "query, items, has_more",
    [
        ("limit=2", [100, 101], True),
        ("limit=2&offset=2", [102, 103], True),
        ("limit=5&offset=20", [120, 121, 122, 123, 124], False),
        ("limit=5&offset=25", [], False),
    ],
)
def test_pagination(client, query, items, has_more):
    body = client.get(f"/items?{query}").json()
    assert body["items"] == items
    assert body["has_more"] is has_more


def test_pagination_default_limit(client):
    body = client.get("/items").json()
    assert body["limit"] == 20
    assert len(body["items"]) == 20
    assert body["has_more"] is True


@pytest.mark.parametrize("query", ["limit=0", "limit=101", "offset=-1"])
def test_pagination_rejects_out_of_range(client, query):
    assert client.get(f"/items?{query}").status_code == 422
