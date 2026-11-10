"""Swagger 문서 테스트. DB 없이 실행됩니다."""

from fastapi.testclient import TestClient

from app.main import create_app


def test_swagger_documents_the_real_error_format():
    spec = TestClient(create_app()).get("/openapi.json").json()
    assert "HTTPValidationError" not in spec["components"]["schemas"]
    assert "access_token" in str(spec["components"]["securitySchemes"])
    for path, methods in spec["paths"].items():
        for method, operation in methods.items():
            assert operation["summary"], f"{method} {path}"
            assert operation["tags"], f"{method} {path}"
