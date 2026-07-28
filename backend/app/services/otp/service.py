"""Redis-backed one-time-passcode storage for email verification.

OTPs are intentionally kept out of Postgres: they are short-lived,
high-churn, and don't need to survive a database backup/restore, so
Redis's native TTL support is a better fit than a table + a cron job.
"""

from __future__ import annotations

import hashlib
import secrets
import string
import uuid

from app.auth.constants import (
    OTP_LENGTH,
    OTP_MAX_ATTEMPTS,
    OTP_RESEND_COOLDOWN_SECONDS,
)
from app.auth.exceptions import (
    InvalidOtpError,
    OtpAttemptsExceededError,
    OtpExpiredError,
    OtpResendCooldownError,
)
from app.core.config import settings
from app.core.redis_client import redis_client


def _otp_key(user_id: uuid.UUID) -> str:
    return f"auth:otp:{user_id}"


def _cooldown_key(user_id: uuid.UUID) -> str:
    return f"auth:otp:cooldown:{user_id}"


def _hash_code(code: str) -> str:
    # A plain SHA-256 hash is sufficient here (unlike passwords/refresh
    # tokens): the search space is tiny, so the real protections are the
    # short TTL and the attempt limit below, not the hash's cost function.
    return hashlib.sha256(code.encode("utf-8")).hexdigest()


def _generate_code(length: int = OTP_LENGTH) -> str:
    return "".join(secrets.choice(string.digits) for _ in range(length))


def issue_otp(user_id: uuid.UUID) -> str:
    """
    Generate a new OTP, store its hash in Redis, and return the raw code
    so the caller can email it. Raises OtpResendCooldownError if called
    again before the previous cooldown window has elapsed.
    """

    if redis_client.exists(_cooldown_key(user_id)):
        raise OtpResendCooldownError()

    code = _generate_code()
    ttl_seconds = settings.AUTH_OTP_EXPIRE_MINUTES * 60

    key = _otp_key(user_id)
    redis_client.hset(key, mapping={"code_hash": _hash_code(code), "attempts": 0})
    redis_client.expire(key, ttl_seconds)
    redis_client.set(_cooldown_key(user_id), "1", ex=OTP_RESEND_COOLDOWN_SECONDS)

    return code


def verify_otp(user_id: uuid.UUID, *, code: str) -> None:
    """
    Validate a submitted OTP against Redis.

    Raises OtpExpiredError if no OTP is on record (never issued, already
    consumed, or its TTL ran out), OtpAttemptsExceededError once the retry
    limit is hit, or InvalidOtpError for an incorrect-but-still-live code.
    """

    key = _otp_key(user_id)
    stored = redis_client.hgetall(key)

    if not stored:
        raise OtpExpiredError()

    attempts = int(stored.get("attempts", 0))
    if attempts >= OTP_MAX_ATTEMPTS:
        raise OtpAttemptsExceededError()

    if not secrets.compare_digest(stored.get("code_hash", ""), _hash_code(code)):
        redis_client.hincrby(key, "attempts", 1)
        raise InvalidOtpError()

    # Single use — remove immediately on success rather than waiting for TTL.
    redis_client.delete(key)
