from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi import Response

from app.config import Settings, get_settings
from app.errors import UnauthorizedError
from app.security import (
    AUTH_COOKIE_NAME,
    JWT_ALGORITHM,
    clear_auth_cookie,
    create_access_token,
    decode_access_token,
    hash_password,
    set_auth_cookie,
    verify_password,
)


def test_password_is_hashed_and_verified():
    hashed = hash_password("correct horse")
    assert "correct horse" not in hashed
    assert verify_password("correct horse", hashed)
    assert not verify_password("wrong", hashed)


def test_verify_password_rejects_plain_text_stored_value():
    assert not verify_password("password", "password")


def test_token_round_trip():
    assert decode_access_token(create_access_token(42)) == 42


@pytest.mark.parametrize(
    "payload_change",
    [
        {"exp": datetime.now(timezone.utc) - timedelta(minutes=1)},
        {"sub": "not-a-number"},
    ],
)
def test_invalid_token_payload_is_rejected(payload_change):
    payload = {"sub": "1", "exp": datetime.now(timezone.utc) + timedelta(minutes=5)}
    payload.update(payload_change)
    token = jwt.encode(payload, get_settings().jwt_secret, algorithm=JWT_ALGORITHM)
    with pytest.raises(UnauthorizedError):
        decode_access_token(token)


def test_token_signed_with_other_secret_is_rejected():
    token = jwt.encode(
        {"sub": "1", "exp": datetime.now(timezone.utc) + timedelta(minutes=5)},
        "another-secret-" * 4,
        algorithm=JWT_ALGORITHM,
    )
    with pytest.raises(UnauthorizedError):
        decode_access_token(token)


def test_token_without_expiry_is_rejected():
    token = jwt.encode({"sub": "1"}, get_settings().jwt_secret, algorithm=JWT_ALGORITHM)
    with pytest.raises(UnauthorizedError):
        decode_access_token(token)


def test_auth_cookie_flags():
    response = Response()
    set_auth_cookie(response, "token-value")
    cookie = response.headers["set-cookie"]
    assert cookie.startswith(f"{AUTH_COOKIE_NAME}=token-value")
    assert "HttpOnly" in cookie
    assert "SameSite=lax" in cookie
    assert "Max-Age=3600" in cookie


def test_clear_auth_cookie_expires_it():
    response = Response()
    clear_auth_cookie(response)
    assert "Max-Age=0" in response.headers["set-cookie"]


def test_short_jwt_secret_is_rejected(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", "too-short")
    with pytest.raises(ValueError):
        Settings(_env_file=None)
