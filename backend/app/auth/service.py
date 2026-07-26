"""Service layer for authentication workflows."""

from app.auth.schemas import AuthStatusResponse
from app.core.config import settings


def get_auth_status() -> AuthStatusResponse:
    """Return module-level auth configuration useful for validation and smoke tests."""

    return AuthStatusResponse(
        enabled=settings.AUTH_ENABLED,
        token_type="jwt",
        access_token_expire_minutes=settings.AUTH_ACCESS_TOKEN_EXPIRE_MINUTES,
        refresh_token_expire_days=settings.AUTH_REFRESH_TOKEN_EXPIRE_DAYS,
    )
