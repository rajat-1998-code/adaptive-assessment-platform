"""Redis-backed anonymous guest session management.

Mirrors the pattern used for OTPs (app.services.otp): short-lived,
high-churn state that doesn't need to survive a database backup, so
Redis's native TTL does the expiry work for us instead of a cleanup job.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import Request, Response

from app.core.config import settings
from app.core.redis_client import redis_client
from app.guest.constants import GUEST_SESSION_COOKIE_NAME

GUEST_SESSION_TTL_SECONDS = settings.GUEST_SESSION_EXPIRE_DAYS * 24 * 60 * 60


def _guest_key(guest_id: uuid.UUID) -> str:
    return f"guest:session:{guest_id}"


def _parse_guest_cookie(request: Request) -> uuid.UUID | None:
    raw_value = request.cookies.get(GUEST_SESSION_COOKIE_NAME)
    if not raw_value:
        return None

    try:
        return uuid.UUID(raw_value)
    except ValueError:
        return None


def _set_guest_cookie(response: Response, guest_id: uuid.UUID) -> None:
    response.set_cookie(
        key=GUEST_SESSION_COOKIE_NAME,
        value=str(guest_id),
        httponly=True,
        secure=settings.AUTH_COOKIE_SECURE,
        samesite=settings.AUTH_COOKIE_SAMESITE,
        domain=settings.AUTH_COOKIE_DOMAIN,
        path="/",
        max_age=GUEST_SESSION_TTL_SECONDS,
    )


def get_guest_id_from_request(request: Request) -> uuid.UUID | None:
    """
    Read an existing, still-live guest id from the cookie, without minting
    a new session. Returns None if there's no cookie, it's malformed, or
    the Redis-backed session it points to has already expired.
    """

    guest_id = _parse_guest_cookie(request)
    if guest_id is None:
        return None

    if not redis_client.exists(_guest_key(guest_id)):
        return None

    return guest_id


def get_or_create_guest_id(request: Request, response: Response) -> uuid.UUID:
    """
    Resolve the current guest id, refreshing its session if it's still
    live, or minting a brand new one (and cookie-ing it) if not.
    """

    existing_guest_id = get_guest_id_from_request(request)

    if existing_guest_id is not None:
        redis_client.expire(_guest_key(existing_guest_id), GUEST_SESSION_TTL_SECONDS)
        _set_guest_cookie(response, existing_guest_id)
        return existing_guest_id

    guest_id = uuid.uuid4()
    redis_client.hset(
        _guest_key(guest_id),
        mapping={"created_at": datetime.now(UTC).isoformat()},
    )
    redis_client.expire(_guest_key(guest_id), GUEST_SESSION_TTL_SECONDS)
    _set_guest_cookie(response, guest_id)

    return guest_id


def end_guest_session(response: Response, *, guest_id: uuid.UUID) -> None:
    """Delete the Redis-backed session and clear the cookie (post-merge)."""

    redis_client.delete(_guest_key(guest_id))
    response.delete_cookie(
        key=GUEST_SESSION_COOKIE_NAME,
        domain=settings.AUTH_COOKIE_DOMAIN,
        path="/",
        secure=settings.AUTH_COOKIE_SECURE,
        httponly=True,
        samesite=settings.AUTH_COOKIE_SAMESITE,
    )
