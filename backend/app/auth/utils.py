"""Shared authentication helpers."""

from app.auth.constants import ACCESS_TOKEN_COOKIE_NAME, REFRESH_TOKEN_COOKIE_NAME


def build_auth_cookie_names() -> dict[str, str]:
    """Return cookie names in one place so routes and services stay consistent."""

    return {
        "access_token": ACCESS_TOKEN_COOKIE_NAME,
        "refresh_token": REFRESH_TOKEN_COOKIE_NAME,
    }
