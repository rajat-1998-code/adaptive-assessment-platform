"""Shared authentication and security helpers."""

from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import Argon2Error, VerifyMismatchError
from fastapi import Response
from jwt import ExpiredSignatureError
from jwt import InvalidTokenError as JWTInvalidTokenError

from app.auth.constants import ACCESS_TOKEN_COOKIE_NAME, REFRESH_TOKEN_COOKIE_NAME
from app.auth.exceptions import AuthConfigurationError, InvalidTokenError
from app.auth.schemas import (
    AuthCookieConfig,
    GeneratedToken,
    RefreshTokenBundle,
    TokenPayload,
)
from app.core.config import settings

password_hasher = PasswordHasher()


def build_auth_cookie_names() -> dict[str, str]:
    """Return cookie names in one place so routes and services stay consistent."""

    return {
        "access_token": ACCESS_TOKEN_COOKIE_NAME,
        "refresh_token": REFRESH_TOKEN_COOKIE_NAME,
    }


def hash_password(password: str) -> str:
    """Hash a password using Argon2id."""

    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a plain-text password against an Argon2id hash."""

    try:
        return password_hasher.verify(password_hash, password)
    except (VerifyMismatchError, Argon2Error):
        return False


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _get_jwt_secret() -> str:
    secret = settings.AUTH_JWT_SECRET_KEY.get_secret_value().strip()

    if not secret:
        raise AuthConfigurationError("AUTH_JWT_SECRET_KEY must not be empty")

    return secret


def create_jwt_token(
    *,
    user_id: uuid.UUID,
    token_type: str,
    expires_delta: timedelta,
    session_id: uuid.UUID | None = None,
    role: str | None = None,
    subject: str | None = None,
    token_identifier: uuid.UUID | None = None,
) -> GeneratedToken:
    """Create a signed JWT for access or refresh workflows."""

    issued_at = _utcnow()
    expires_at = issued_at + expires_delta
    jwt_id = token_identifier or uuid.uuid4()
    payload = {
        "sub": subject or str(user_id),
        "token_type": token_type,
        "exp": expires_at,
        "iat": issued_at,
        "jti": str(jwt_id),
        "iss": settings.AUTH_ISSUER,
        "aud": settings.AUTH_AUDIENCE,
        "user_id": str(user_id),
        "session_id": str(session_id) if session_id else None,
        "role": role,
    }
    token = jwt.encode(payload, _get_jwt_secret(), algorithm=settings.AUTH_JWT_ALGORITHM)
    return GeneratedToken(token=token, expires_at=expires_at)


def decode_jwt_token(token: str, *, expected_token_type: str | None = None) -> TokenPayload:
    """Decode and validate a JWT."""

    try:
        payload = jwt.decode(
            token,
            _get_jwt_secret(),
            algorithms=[settings.AUTH_JWT_ALGORITHM],
            audience=settings.AUTH_AUDIENCE,
            issuer=settings.AUTH_ISSUER,
        )
    except ExpiredSignatureError as exc:
        raise InvalidTokenError("Authentication token has expired") from exc
    except JWTInvalidTokenError as exc:
        raise InvalidTokenError() from exc

    token_payload = TokenPayload.model_validate(payload)

    if expected_token_type and token_payload.token_type != expected_token_type:
        raise InvalidTokenError(f"Expected a {expected_token_type} token")

    return token_payload


def hash_token(token: str) -> str:
    """Hash an opaque token for safe persistence (shared by refresh + magic link tokens)."""

    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def hash_refresh_token(token: str) -> str:
    """Hash a refresh token for safe persistence."""

    return hash_token(token)


def create_refresh_token_bundle(
    *,
    user_id: uuid.UUID,
    session_id: uuid.UUID | None = None,
    role: str | None = None,
) -> RefreshTokenBundle:
    """Create a refresh token plus the metadata needed to persist and rotate it."""

    token_identifier = uuid.uuid4()
    raw_token = secrets.token_urlsafe(48)
    signed_token = create_jwt_token(
        user_id=user_id,
        token_type="refresh",
        expires_delta=timedelta(days=settings.AUTH_REFRESH_TOKEN_EXPIRE_DAYS),
        session_id=session_id,
        role=role,
        token_identifier=token_identifier,
    )

    composite_token = f"{raw_token}.{signed_token.token}"
    return RefreshTokenBundle(
        token=composite_token,
        token_hash=hash_refresh_token(composite_token),
        token_identifier=token_identifier,
        expires_at=signed_token.expires_at,
    )


def get_cookie_config(*, token_type: str) -> AuthCookieConfig:
    """Build the cookie configuration for access or refresh tokens."""

    cookie_names = build_auth_cookie_names()

    if token_type == "access":
        return AuthCookieConfig(
            key=cookie_names["access_token"],
            httponly=True,
            secure=settings.AUTH_COOKIE_SECURE,
            samesite=settings.AUTH_COOKIE_SAMESITE,
            domain=settings.AUTH_COOKIE_DOMAIN,
            path="/",
            max_age=settings.AUTH_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    if token_type == "refresh":
        return AuthCookieConfig(
            key=cookie_names["refresh_token"],
            httponly=True,
            secure=settings.AUTH_COOKIE_SECURE,
            samesite=settings.AUTH_COOKIE_SAMESITE,
            domain=settings.AUTH_COOKIE_DOMAIN,
            path=f"{settings.API_V1_PREFIX}{settings.AUTH_PREFIX}",
            max_age=settings.AUTH_REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        )

    raise AuthConfigurationError(f"Unsupported cookie token type: {token_type}")


def set_auth_cookie(response: Response, *, token: str, token_type: str) -> None:
    """Attach a configured auth cookie to a response."""

    config = get_cookie_config(token_type=token_type)
    response.set_cookie(
        key=config.key,
        value=token,
        httponly=config.httponly,
        secure=config.secure,
        samesite=config.samesite,
        domain=config.domain,
        path=config.path,
        max_age=config.max_age,
    )


def clear_auth_cookies(response: Response) -> None:
    """Remove access and refresh cookies from a response."""

    for token_type in ("access", "refresh"):
        config = get_cookie_config(token_type=token_type)
        response.delete_cookie(
            key=config.key,
            domain=config.domain,
            path=config.path,
            secure=config.secure,
            httponly=config.httponly,
            samesite=config.samesite,
        )
