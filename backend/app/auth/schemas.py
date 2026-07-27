"""Schemas used by the authentication module."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


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
