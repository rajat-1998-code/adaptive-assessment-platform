import uuid
from datetime import UTC, datetime, timedelta

import jwt
import pytest
from fastapi import Response

from app.auth.exceptions import InvalidTokenError
from app.auth.utils import (
    clear_auth_cookies,
    create_jwt_token,
    create_refresh_token_bundle,
    decode_jwt_token,
    get_cookie_config,
    hash_password,
    hash_refresh_token,
    set_auth_cookie,
    verify_password,
)
from app.core.config import settings


def test_password_hash_and_verification():
    password = "Sup3rSecure!Password"

    password_hash = hash_password(password)

    assert password_hash != password
    assert password_hash.startswith("$argon2id$")
    assert verify_password(password, password_hash) is True
    assert verify_password("wrong-password", password_hash) is False


def test_jwt_generation_and_validation():
    user_id = uuid.uuid4()
    session_id = uuid.uuid4()

    generated_token = create_jwt_token(
        user_id=user_id,
        token_type="access",
        expires_delta=timedelta(minutes=15),
        session_id=session_id,
        role="student",
    )

    payload = decode_jwt_token(generated_token.token, expected_token_type="access")

    assert payload.user_id == user_id
    assert payload.session_id == session_id
    assert payload.token_type == "access"
    assert payload.role == "student"


def test_invalid_jwt_is_rejected():
    with pytest.raises(InvalidTokenError):
        decode_jwt_token("not-a-real-token", expected_token_type="access")


def test_expired_jwt_is_rejected():
    user_id = uuid.uuid4()
    now = datetime.now(UTC)
    expired_token = jwt.encode(
        {
            "sub": str(user_id),
            "token_type": "access",
            "exp": now - timedelta(minutes=5),
            "iat": now - timedelta(minutes=10),
            "jti": str(uuid.uuid4()),
            "iss": settings.AUTH_ISSUER,
            "aud": settings.AUTH_AUDIENCE,
            "user_id": str(user_id),
            "session_id": None,
            "role": "student",
        },
        settings.AUTH_JWT_SECRET_KEY.get_secret_value(),
        algorithm=settings.AUTH_JWT_ALGORITHM,
    )

    with pytest.raises(InvalidTokenError):
        decode_jwt_token(expired_token, expected_token_type="access")


def test_refresh_token_bundle_contains_hashable_token_and_identifier():
    user_id = uuid.uuid4()
    session_id = uuid.uuid4()

    bundle = create_refresh_token_bundle(user_id=user_id, session_id=session_id, role="student")

    assert "." in bundle.token
    assert bundle.token_hash == hash_refresh_token(bundle.token)
    assert bundle.expires_at > datetime.now(UTC)
    payload = decode_jwt_token(bundle.token.split(".", 1)[1], expected_token_type="refresh")
    assert payload.user_id == user_id
    assert payload.session_id == session_id
    assert payload.jti == str(bundle.token_identifier)


def test_cookie_configuration_and_response_helpers():
    response = Response()
    access_config = get_cookie_config(token_type="access")
    refresh_config = get_cookie_config(token_type="refresh")

    set_auth_cookie(response, token="access-token", token_type="access")
    set_auth_cookie(response, token="refresh-token", token_type="refresh")

    cookie_headers = response.headers.getlist("set-cookie")
    assert any(access_config.key in header for header in cookie_headers)
    assert any(refresh_config.key in header for header in cookie_headers)

    clear_auth_cookies(response)

    cleared_cookie_headers = response.headers.getlist("set-cookie")
    assert any(f"{access_config.key}=" in header for header in cleared_cookie_headers)
    assert any(f"{refresh_config.key}=" in header for header in cleared_cookie_headers)
