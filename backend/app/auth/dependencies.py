"""FastAPI dependencies for authentication."""

from collections.abc import Callable

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.auth.constants import ROLE_PERMISSIONS, SUPPORTED_ROLES
from app.auth.exceptions import (
    AuthenticationRequiredError,
    AuthorizationDeniedError,
    InvalidRoleError,
)
from app.auth.models import User
from app.auth.utils import build_auth_cookie_names, decode_jwt_token
from app.core.database import get_db


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """
    Resolve the authenticated user from the access token cookie.

    Raises AuthenticationRequiredError if the cookie is missing or the
    token is invalid/expired (decode_jwt_token raises InvalidTokenError,
    which is also a 401, in that case), or if the user no longer exists
    or has been deactivated since the token was issued.
    """

    cookie_names = build_auth_cookie_names()
    access_token = request.cookies.get(cookie_names["access_token"])

    if not access_token:
        raise AuthenticationRequiredError()

    payload = decode_jwt_token(access_token, expected_token_type="access")

    user = db.get(User, payload.user_id)
    if user is None or not user.is_active:
        raise AuthenticationRequiredError()

    return user


def get_role_permissions(role: str) -> frozenset[str]:
    """Return the permissions granted to a supported role."""

    if role not in SUPPORTED_ROLES:
        raise InvalidRoleError()

    return ROLE_PERMISSIONS[role]


def require_roles(*allowed_roles: str) -> Callable[..., User]:
    """Build a dependency that allows only users whose role is in allowed_roles."""

    allowed = frozenset(allowed_roles)

    if not allowed:
        raise ValueError("require_roles must be given at least one role")

    invalid_roles = allowed.difference(SUPPORTED_ROLES)
    if invalid_roles:
        invalid = ", ".join(sorted(invalid_roles))
        raise ValueError(f"Unsupported roles passed to require_roles: {invalid}")

    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed:
            raise AuthorizationDeniedError()

        return current_user

    return dependency


def require_permissions(*required_permissions: str) -> Callable[..., User]:
    """Build a dependency that checks whether the current user's role grants permissions."""

    required = frozenset(required_permissions)

    if not required:
        raise ValueError("require_permissions must be given at least one permission")

    def dependency(current_user: User = Depends(get_current_user)) -> User:
        granted_permissions = get_role_permissions(current_user.role)

        if not required.issubset(granted_permissions):
            raise AuthorizationDeniedError()

        return current_user

    return dependency
