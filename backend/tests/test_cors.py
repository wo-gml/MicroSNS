"""브라우저가 백엔드를 직접 호출할 때의 CORS 동작 테스트. DB 없이 실행됩니다."""

import pytest
from fastapi.testclient import TestClient

from app.errors import NotFoundError
from app.main import create_app

ALLOWED = "http://localhost:3000"
DISALLOWED = "http://evil.example"


@pytest.fixture
def client():
    app = create_app()

    @app.get("/raise/not-found")
    def raise_not_found():
        raise NotFoundError()

    @app.get("/raise/unexpected")
    def raise_unexpected():
        raise RuntimeError("숨겨야 할 내부 정보")

    return TestClient(app, raise_server_exceptions=False)


def preflight(client, origin, method="POST", headers="content-type"):
    return client.options(
        "/openapi.json",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": method,
            "Access-Control-Request-Headers": headers,
        },
    )


@pytest.mark.parametrize("method", ["GET", "POST", "PATCH", "DELETE"])
def test_preflight_allows_listed_origin_with_credentials(client, method):
    response = preflight(client, ALLOWED, method)
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == ALLOWED
    assert response.headers["access-control-allow-credentials"] == "true"


def test_preflight_rejects_unlisted_origin(client):
    response = preflight(client, DISALLOWED)
    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers


def test_response_to_unlisted_origin_has_no_cors_headers(client):
    response = client.get("/openapi.json", headers={"Origin": DISALLOWED})
    assert "access-control-allow-origin" not in response.headers


@pytest.mark.parametrize(
    "path, status, code",
    [
        ("/raise/not-found", 404, "NOT_FOUND"),
        ("/raise/unexpected", 500, "INTERNAL_ERROR"),
    ],
)
def test_error_responses_keep_cors_headers(client, path, status, code):
    # 헤더가 빠지면 브라우저는 실제 에러 대신 CORS 오류만 보여줍니다.
    response = client.get(path, headers={"Origin": ALLOWED})
    assert response.status_code == status
    assert response.json()["error"]["code"] == code
    assert response.headers["access-control-allow-origin"] == ALLOWED
