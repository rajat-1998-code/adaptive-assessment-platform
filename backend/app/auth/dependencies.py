"""FastAPI dependencies for authentication."""

from collections.abc import Generator

from app.auth.exceptions import AuthenticationRequiredError


def get_current_user() -> Generator[None, None, None]:
    """
    Placeholder dependency for future protected routes.

    Stage 1 intentionally stops at wiring and configuration, so this raises a
    clear auth-specific exception until token validation is implemented.
    """

    raise AuthenticationRequiredError()
    yield
