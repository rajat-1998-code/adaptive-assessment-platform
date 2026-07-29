"""Service layer for authentication workflows."""

from __future__ import annotations

import logging
import secrets
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import Request, Response
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.assessments.service import migrate_guest_assessments_to_user
from app.auth.constants import (
    MAGIC_LINK_RESEND_COOLDOWN_SECONDS,
    MAGIC_LINK_TOKEN_BYTES,
    OAUTH_PROVIDER_GITHUB,
    OAUTH_PROVIDER_GOOGLE,
    ROLE_STUDENT,
)
from app.auth.exceptions import (
    AlreadyVerifiedError,
    DuplicateEmailError,
    ExpiredMagicLinkError,
    InactiveAccountError,
    InvalidCredentialsError,
    InvalidMagicLinkError,
    InvalidTokenError,
    MagicLinkAlreadyUsedError,
    OAuthAccountLinkError,
)
from app.auth.models import MagicLinkToken, RefreshToken, User, UserSession
from app.auth.oauth import OAuthIdentity
from app.auth.schemas import (
    AuthenticatedUser,
    AuthStatusResponse,
    LoginRequest,
    RegisterRequest,
    UserSummary,
)
from app.auth.utils import (
    build_auth_cookie_names,
    clear_auth_cookies,
    create_jwt_token,
    create_refresh_token_bundle,
    decode_jwt_token,
    hash_password,
    hash_refresh_token,
    hash_token,
    set_auth_cookie,
    verify_password,
)
from app.core.config import settings
from app.guest.service import end_guest_session, get_guest_id_from_request
from app.services.email.service import EmailService
from app.services.otp import issue_otp, verify_otp
from app.uploads.service import migrate_guest_uploads_to_user

logger = logging.getLogger(__name__)

OAUTH_SUBJECT_FIELD_BY_PROVIDER = {
    OAUTH_PROVIDER_GOOGLE: "google_oauth_subject",
    OAUTH_PROVIDER_GITHUB: "github_oauth_subject",
}


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


def _oauth_subject_field(provider: str) -> str:
    try:
        return OAUTH_SUBJECT_FIELD_BY_PROVIDER[provider]
    except KeyError as exc:
        raise OAuthAccountLinkError(f"Unsupported OAuth provider '{provider}'") from exc


def _display_name(user: User) -> str:
    """Derive a friendly name for emails — the User model has no full_name field."""

    return user.email.split("@", 1)[0]


def _send_verification_otp(user: User, *, email_service: EmailService) -> None:
    """Generate an OTP, store it in Redis, and email it to the user.

    The OTP is generated and stored first, so it exists even if the actual
    send fails (e.g. a transient SMTP outage) — the user can then use
    resend-otp to get a fresh code once delivery is working again, rather
    than the whole request (registration or resend) failing outright.
    """

    code = issue_otp(user.id)

    if not settings.EMAILS_ENABLED:
        return

    try:
        email_service.send_otp_email(
            to_address=user.email,
            recipient_name=_display_name(user),
            otp_code=code,
        )
    except Exception:
        logger.exception("Failed to send verification OTP email to %s", user.email)


def _client_metadata(request: Request) -> tuple[str | None, str | None]:
    user_agent = request.headers.get("user-agent")
    ip_address = request.client.host if request.client else None
    return user_agent, ip_address


def _merge_guest_session(db: Session, *, request: Request, response: Response, user: User) -> None:
    """
    If the caller had an active guest session, reassign anything it owned
    (uploads, assessments) to the newly authenticated user, then end the
    guest session — it has nothing left to distinguish it.

    A no-op if there's no guest cookie, which is the common case for
    someone who registers/logs in without having used the app anonymously
    first.
    """

    guest_id = get_guest_id_from_request(request)
    if guest_id is None:
        return

    migrated_uploads = migrate_guest_uploads_to_user(db, guest_id=guest_id, user_id=user.id)
    migrated_assessments = migrate_guest_assessments_to_user(db, guest_id=guest_id, user_id=user.id)
    db.commit()

    if migrated_uploads or migrated_assessments:
        logger.info(
            "Merged guest session %s into user %s (%d uploads, %d assessments)",
            guest_id,
            user.id,
            migrated_uploads,
            migrated_assessments,
        )

    end_guest_session(response, guest_id=guest_id)


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


def _find_user_by_oauth_identity(db: Session, identity: OAuthIdentity) -> User | None:
    """Look up an existing account already linked to the provider subject."""

    subject_field = _oauth_subject_field(identity.provider)
    return db.scalar(select(User).where(getattr(User, subject_field) == identity.subject))


def _link_oauth_identity(db: Session, *, user: User, identity: OAuthIdentity) -> User:
    """
    Attach a provider subject to an existing user if it is safe to do so.

    If the user already linked the same provider to a different subject,
    do not silently overwrite it: that would let a second social identity
    hijack the same local account solely because the provider reported the
    same email address.
    """

    subject_field = _oauth_subject_field(identity.provider)
    existing_subject = getattr(user, subject_field)

    if existing_subject and existing_subject != identity.subject:
        raise OAuthAccountLinkError(
            f"This {identity.provider.title()} account cannot be linked automatically."
        )

    setattr(user, subject_field, identity.subject)

    # Successful social login proves inbox ownership for providers that
    # return a verified email signal. If the provider could not confirm it,
    # keep the prior state rather than upgrading trust.
    if identity.email_verified:
        user.is_email_verified = True

    db.add(user)
    db.flush()
    return user


def register_user(
    db: Session,
    *,
    payload: RegisterRequest,
    request: Request,
    response: Response,
    email_service: EmailService,
) -> AuthenticatedUser:
    """Create a new email/password account, start a session, and send a verification OTP."""

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
    _send_verification_otp(user, email_service=email_service)
    _merge_guest_session(db, request=request, response=response, user=user)

    return AuthenticatedUser.model_validate(user)


def authenticate_oauth_user(
    db: Session,
    *,
    identity: OAuthIdentity,
    request: Request,
    response: Response,
) -> AuthenticatedUser:
    """Create or link a social-login account, then issue the normal session cookies."""

    linked_user = _find_user_by_oauth_identity(db, identity)
    if linked_user is not None:
        if not linked_user.is_active:
            raise InactiveAccountError()

        _issue_session_tokens(db, user=linked_user, request=request, response=response)
        _merge_guest_session(db, request=request, response=response, user=linked_user)
        return AuthenticatedUser.model_validate(linked_user)

    email = _normalize_email(identity.email)
    existing_user = db.scalar(select(User).where(User.email == email))

    if existing_user is not None:
        if not existing_user.is_active:
            raise InactiveAccountError()
        if not identity.email_verified:
            raise OAuthAccountLinkError(
                f"This {identity.provider.title()} account cannot be linked "
                "without a verified email."
            )

        user = _link_oauth_identity(db, user=existing_user, identity=identity)
    else:
        user = User(
            email=email,
            password_hash=None,
            role=ROLE_STUDENT,
            is_email_verified=identity.email_verified,
            is_active=True,
            google_oauth_subject=(
                identity.subject if identity.provider == OAUTH_PROVIDER_GOOGLE else None
            ),
            github_oauth_subject=(
                identity.subject if identity.provider == OAUTH_PROVIDER_GITHUB else None
            ),
        )
        db.add(user)
        db.flush()

    _issue_session_tokens(db, user=user, request=request, response=response)
    _merge_guest_session(db, request=request, response=response, user=user)
    db.refresh(user)
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
    _merge_guest_session(db, request=request, response=response, user=user)

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


def verify_email_otp(db: Session, *, user: User, code: str) -> AuthenticatedUser:
    """Mark a user's email as verified once they submit a matching, unexpired OTP."""

    if user.is_email_verified:
        raise AlreadyVerifiedError()

    verify_otp(user.id, code=code)

    user.is_email_verified = True
    db.add(user)
    db.commit()
    db.refresh(user)

    return AuthenticatedUser.model_validate(user)


def resend_verification_otp(user: User, *, email_service: EmailService) -> None:
    """Issue and send a fresh OTP, subject to the resend cooldown in app.services.otp."""

    if user.is_email_verified:
        raise AlreadyVerifiedError()

    _send_verification_otp(user, email_service=email_service)


def request_magic_link(
    db: Session,
    *,
    email: str,
    request: Request,
    email_service: EmailService,
) -> None:
    """
    Issue and email a passwordless sign-in link, if the email belongs to
    an active account.

    Always completes silently either way (no return value, never raises
    for an unknown email or an active cooldown) — the router always sends
    back the same generic message, so this never leaks which emails are
    registered or how recently a link was last requested.
    """

    normalized = _normalize_email(email)
    user = db.scalar(select(User).where(User.email == normalized))

    if user is None or not user.is_active:
        return

    now = datetime.now(UTC)
    cooldown_cutoff = now - timedelta(seconds=MAGIC_LINK_RESEND_COOLDOWN_SECONDS)
    recent_token = db.scalar(
        select(MagicLinkToken.id)
        .where(
            MagicLinkToken.user_id == user.id,
            MagicLinkToken.created_at >= cooldown_cutoff,
        )
        .limit(1)
    )
    if recent_token is not None:
        return

    raw_token = secrets.token_urlsafe(MAGIC_LINK_TOKEN_BYTES)
    user_agent, ip_address = _client_metadata(request)

    db.add(
        MagicLinkToken(
            user_id=user.id,
            email=normalized,
            token_hash=hash_token(raw_token),
            expires_at=now + timedelta(minutes=settings.AUTH_MAGIC_LINK_EXPIRE_MINUTES),
            requested_ip=ip_address,
            user_agent=user_agent,
        )
    )
    db.commit()

    if not settings.EMAILS_ENABLED:
        return

    magic_link_url = f"{settings.FRONTEND_BASE_URL}/auth/magic-link?token={raw_token}"

    try:
        email_service.send_magic_link_email(
            to_address=user.email,
            recipient_name=_display_name(user),
            magic_link_url=magic_link_url,
        )
    except Exception:
        logger.exception("Failed to send magic link email to %s", user.email)


def verify_magic_link(
    db: Session,
    *,
    token: str,
    request: Request,
    response: Response,
) -> AuthenticatedUser:
    """Consume a magic link token exactly once and start an authenticated session."""

    stored_token = db.scalar(
        select(MagicLinkToken).where(MagicLinkToken.token_hash == hash_token(token))
    )

    if stored_token is None:
        raise InvalidMagicLinkError()

    if stored_token.used_at is not None:
        raise MagicLinkAlreadyUsedError()

    now = datetime.now(UTC)
    if stored_token.expires_at <= now:
        raise ExpiredMagicLinkError()

    user = db.get(User, stored_token.user_id)
    if user is None or not user.is_active:
        raise InvalidCredentialsError()

    # Single-use: mark it consumed before doing anything else with it.
    stored_token.used_at = now

    # Clicking an emailed link proves inbox ownership just as strongly as
    # submitting an OTP would, so treat a successful login as verification.
    if not user.is_email_verified:
        user.is_email_verified = True

    db.commit()

    _issue_session_tokens(db, user=user, request=request, response=response)
    _merge_guest_session(db, request=request, response=response, user=user)

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


def list_users(db: Session) -> list[UserSummary]:
    """Return users in deterministic order for admin-only management endpoints."""

    users = db.scalars(select(User).order_by(User.created_at.asc(), User.email.asc())).all()
    return [UserSummary.model_validate(user) for user in users]


def update_user_role(db: Session, *, user: User, role: str) -> AuthenticatedUser:
    """Persist a new RBAC role for a user and return the updated public model."""

    user.role = role
    db.add(user)
    db.commit()
    db.refresh(user)
    return AuthenticatedUser.model_validate(user)
