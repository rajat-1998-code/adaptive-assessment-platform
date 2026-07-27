"""Service layer for authentication workflows."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from fastapi import Request, Response
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.constants import ROLE_STUDENT
from app.auth.exceptions import (
    DuplicateEmailError,
    InactiveAccountError,
    InvalidCredentialsError,
    InvalidTokenError,
)
from app.auth.models import RefreshToken, User, UserSession
from app.auth.schemas import (
    AuthenticatedUser,
    AuthStatusResponse,
    LoginRequest,
    RegisterRequest,
)
from app.auth.utils import (
    build_auth_cookie_names,
    clear_auth_cookies,
    create_jwt_token,
    create_refresh_token_bundle,
    decode_jwt_token,
    hash_password,
    hash_refresh_token,
    set_auth_cookie,
    verify_password,
)
from app.core.config import settings


def get_auth_status() -> AuthStatusResponse:
    """Return module-level auth configuration useful for validation and smoke tests."""

    return AuthStatusResponse(
        enabled=settings.AUTH_ENABLED,
        token_type="jwt",
        access_token_expire_minutes=settings.AUTH_ACCESS_TOKEN_EXPIRE_MINUTES,
        refresh_token_expire_days=settings.AUTH_REFRESH_TOKEN_EXPIRE_DAYS,
    )


def _normalize_email(email: str) -> str:
    """Keep email lookups and storage case-insensitive and whitespace-safe."""

    return email.strip().lower()


def _client_metadata(request: Request) -> tuple[str | None, str | None]:
    user_agent = request.headers.get("user-agent")
    ip_address = request.client.host if request.client else None
    return user_agent, ip_address


def _issue_session_tokens(
    db: Session,
    *,
    user: User,
    request: Request,
    response: Response,
) -> None:
    """Create a session + refresh token record, then cookie both signed tokens."""

    user_agent, ip_address = _client_metadata(request)
    now = datetime.now(UTC)

    session = UserSession(
        user_id=user.id,
        session_identifier=uuid.uuid4(),
        user_agent=user_agent,
        ip_address=ip_address,
        expires_at=now + timedelta(days=settings.AUTH_REFRESH_TOKEN_EXPIRE_DAYS),
        last_seen_at=now,
        is_active=True,
    )
    db.add(session)
    db.flush()

    access_token = create_jwt_token(
        user_id=user.id,
        token_type="access",
        expires_delta=timedelta(minutes=settings.AUTH_ACCESS_TOKEN_EXPIRE_MINUTES),
        session_id=session.id,
        role=user.role,
    )
    refresh_bundle = create_refresh_token_bundle(
        user_id=user.id,
        session_id=session.id,
        role=user.role,
    )

    db.add(
        RefreshToken(
            user_id=user.id,
            session_id=session.id,
            token_identifier=refresh_bundle.token_identifier,
            token_hash=refresh_bundle.token_hash,
            expires_at=refresh_bundle.expires_at,
            user_agent=user_agent,
            ip_address=ip_address,
        )
    )

    user.last_login_at = now
    db.commit()

    set_auth_cookie(response, token=access_token.token, token_type="access")
    set_auth_cookie(response, token=refresh_bundle.token, token_type="refresh")


def register_user(
    db: Session,
    *,
    payload: RegisterRequest,
    request: Request,
    response: Response,
) -> AuthenticatedUser:
    """Create a new email/password account and start an authenticated session."""

    email = _normalize_email(payload.email)

    existing_user = db.scalar(select(User).where(User.email == email))
    if existing_user is not None:
        raise DuplicateEmailError()

    user = User(
        email=email,
        password_hash=hash_password(payload.password),
        role=ROLE_STUDENT,
        is_email_verified=False,
        is_active=True,
    )
    db.add(user)

    try:
        db.flush()
    except IntegrityError:
        # Guards against a race where two registrations for the same email
        # both pass the SELECT check above before either commits.
        db.rollback()
        raise DuplicateEmailError() from None

    _issue_session_tokens(db, user=user, request=request, response=response)

    return AuthenticatedUser.model_validate(user)


def login_user(
    db: Session,
    *,
    payload: LoginRequest,
    request: Request,
    response: Response,
) -> AuthenticatedUser:
    """Verify email/password credentials and start an authenticated session."""

    email = _normalize_email(payload.email)
    user = db.scalar(select(User).where(User.email == email))

    if user is None or user.password_hash is None:
        # Same generic error whether the account doesn't exist or has no
        # password set (e.g. an OAuth-only account) — avoids leaking which.
        raise InvalidCredentialsError()

    if not verify_password(payload.password, user.password_hash):
        raise InvalidCredentialsError()

    if not user.is_active:
        raise InactiveAccountError()

    _issue_session_tokens(db, user=user, request=request, response=response)

    return AuthenticatedUser.model_validate(user)


def _get_refresh_cookie(request: Request) -> str | None:
    cookie_names = build_auth_cookie_names()
    return request.cookies.get(cookie_names["refresh_token"])


def refresh_session(
    db: Session,
    *,
    request: Request,
    response: Response,
) -> AuthenticatedUser:
    """Validate the refresh cookie, rotate it, and issue a fresh access token."""

    composite_token = _get_refresh_cookie(request)
    if not composite_token:
        raise InvalidTokenError("Refresh token is missing")

    # The stored token is "<random-secret>.<signed-jwt>" — the random secret
    # never contains a dot, so splitting on the first one recovers the JWT.
    _, _, jwt_part = composite_token.partition(".")
    token_payload = decode_jwt_token(jwt_part, expected_token_type="refresh")

    now = datetime.now(UTC)
    token_hash = hash_refresh_token(composite_token)
    stored_token = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == token_hash))

    if stored_token is None:
        # The JWT is validly signed but we have no matching row, which means
        # this refresh token was already rotated (or never issued by us).
        # Treat it as potential token theft and revoke the user's sessions.
        db.execute(
            update(RefreshToken)
            .where(
                RefreshToken.user_id == token_payload.user_id,
                RefreshToken.revoked_at.is_(None),
            )
            .values(revoked_at=now)
        )
        db.commit()
        raise InvalidTokenError("Refresh token has already been used")

    if stored_token.revoked_at is not None or stored_token.expires_at <= now:
        raise InvalidTokenError("Refresh token is no longer valid")

    user = db.get(User, stored_token.user_id)
    if user is None or not user.is_active:
        raise InvalidCredentialsError()

    stored_token.revoked_at = now

    session = db.get(UserSession, stored_token.session_id) if stored_token.session_id else None
    if session is not None:
        session.last_seen_at = now

    user_agent, ip_address = _client_metadata(request)

    access_token = create_jwt_token(
        user_id=user.id,
        token_type="access",
        expires_delta=timedelta(minutes=settings.AUTH_ACCESS_TOKEN_EXPIRE_MINUTES),
        session_id=stored_token.session_id,
        role=user.role,
    )
    refresh_bundle = create_refresh_token_bundle(
        user_id=user.id,
        session_id=stored_token.session_id,
        role=user.role,
    )
    db.add(
        RefreshToken(
            user_id=user.id,
            session_id=stored_token.session_id,
            token_identifier=refresh_bundle.token_identifier,
            token_hash=refresh_bundle.token_hash,
            expires_at=refresh_bundle.expires_at,
            user_agent=user_agent,
            ip_address=ip_address,
        )
    )
    db.commit()

    set_auth_cookie(response, token=access_token.token, token_type="access")
    set_auth_cookie(response, token=refresh_bundle.token, token_type="refresh")

    return AuthenticatedUser.model_validate(user)


def logout_user(
    db: Session,
    *,
    request: Request,
    response: Response,
) -> None:
    """Revoke the current refresh token/session and clear auth cookies.

    Always succeeds — logging out with a missing or already-invalid token
    is treated as a no-op rather than an error, since the end state
    (no active session, no cookies) is the same either way.
    """

    composite_token = _get_refresh_cookie(request)

    if composite_token:
        token_hash = hash_refresh_token(composite_token)
        stored_token = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == token_hash))

        if stored_token is not None and stored_token.revoked_at is None:
            stored_token.revoked_at = datetime.now(UTC)

            if stored_token.session_id:
                session = db.get(UserSession, stored_token.session_id)
                if session is not None:
                    session.is_active = False

            db.commit()

    clear_auth_cookies(response)
