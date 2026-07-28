"""Schemas used by the authentication module."""

import re
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.auth.constants import (
    OTP_LENGTH,
    PASSWORD_MAX_LENGTH,
    PASSWORD_MIN_LENGTH,
    SUPPORTED_ROLES,
)


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


class VerifyEmailRequest(BaseModel):
    """Payload for POST /auth/verify-email."""

    code: str = Field(min_length=OTP_LENGTH, max_length=OTP_LENGTH)

    @field_validator("code")
    @classmethod
    def validate_code_is_numeric(cls, value: str) -> str:
        if not value.isdigit():
            raise ValueError("Verification code must be a numeric code")
        return value


class MagicLinkRequest(BaseModel):
    """Payload for POST /auth/magic-link."""

    email: EmailStr


class AuthenticatedUser(BaseModel):
    """Public representation of a user returned by auth endpoints."""

    id: UUID
    email: str
    role: str
    is_email_verified: bool
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserAuthorizationSummary(BaseModel):
    """Current user's role and the permissions implied by that role."""

    role: str
    permissions: list[str]


class ProtectedResourceMessage(BaseModel):
    """Simple success response used by protected authorization probe routes."""

    message: str
    role: str


class UserSummary(BaseModel):
    """Compact user representation returned by admin-only listing endpoints."""

    id: UUID
    email: str
    role: str
    is_active: bool
    is_email_verified: bool

    model_config = ConfigDict(from_attributes=True)


class UserRoleUpdateRequest(BaseModel):
    """Payload for admin role-management actions."""

    role: str = Field(description="The target RBAC role for the user")

    @field_validator("role")
    @classmethod
    def validate_role(cls, value: str) -> str:
        normalized = value.strip().lower()

        if normalized not in SUPPORTED_ROLES:
            supported = ", ".join(SUPPORTED_ROLES)
            raise ValueError(f"Role must be one of: {supported}")

        return normalized


class AuthMessageResponse(BaseModel):
    """Simple message payload, e.g. for logout confirmation."""

    message: str
