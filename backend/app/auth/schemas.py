"""Schemas used by the authentication module."""

import re
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator

from app.auth.constants import PASSWORD_MAX_LENGTH, PASSWORD_MIN_LENGTH


class AuthStatusResponse(BaseModel):
    """Simple response used to verify the auth module is wired correctly."""

    enabled: bool
    token_type: str
    access_token_expire_minutes: int
    refresh_token_expire_days: int

    model_config = ConfigDict(from_attributes=True)


class TokenPayload(BaseModel):
    """Canonical JWT payload used across the authentication layer."""

    sub: str
    token_type: str
    exp: datetime
    iat: datetime
    jti: str
    iss: str
    aud: str
    user_id: UUID
    session_id: UUID | None = None
    role: str | None = None


class GeneratedToken(BaseModel):
    """Represents a signed JWT and its expiry."""

    token: str
    expires_at: datetime


class RefreshTokenBundle(BaseModel):
    """Raw refresh token plus the persisted metadata derived from it."""

    token: str
    token_hash: str
    token_identifier: UUID
    expires_at: datetime


class AuthCookieConfig(BaseModel):
    """Cookie settings returned by auth utilities."""

    key: str
    httponly: bool
    secure: bool
    samesite: str
    domain: str | None
    path: str
    max_age: int


def _validate_password_strength(value: str) -> str:
    """Shared password strength check used by registration (and future flows)."""

    if len(value) < PASSWORD_MIN_LENGTH:
        raise ValueError(f"Password must be at least {PASSWORD_MIN_LENGTH} characters long")

    if len(value) > PASSWORD_MAX_LENGTH:
        raise ValueError(f"Password must be at most {PASSWORD_MAX_LENGTH} characters long")

    if not re.search(r"[a-zA-Z]", value):
        raise ValueError("Password must contain at least one letter")

    if not re.search(r"[0-9]", value):
        raise ValueError("Password must contain at least one number")

    return value


class RegisterRequest(BaseModel):
    """Payload for POST /auth/register."""

    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        return _validate_password_strength(value)


class LoginRequest(BaseModel):
    """Payload for POST /auth/login."""

    email: EmailStr
    password: str


class AuthenticatedUser(BaseModel):
    """Public representation of a user returned by auth endpoints."""

    id: UUID
    email: str
    role: str
    is_email_verified: bool
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AuthMessageResponse(BaseModel):
    """Simple message payload, e.g. for logout confirmation."""

    message: str
