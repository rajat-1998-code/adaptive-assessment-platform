"""Integration tests for Stage 7: magic link (passwordless) authentication."""

import re
from urllib.parse import parse_qs, urlparse

from app.auth.constants import ACCESS_TOKEN_COOKIE_NAME, REFRESH_TOKEN_COOKIE_NAME

REGISTER_URL = "/api/v1/auth/register"
MAGIC_LINK_REQUEST_URL = "/api/v1/auth/magic-link"
MAGIC_LINK_VERIFY_URL = "/api/v1/auth/magic-link/verify"

GENERIC_MESSAGE = "If an account exists for that email, a sign-in link has been sent."
URL_PATTERN = re.compile(r"(https?://\S+)")


def _register(client, email="magiclink@example.com", password="MagicPass123"):
    return client.post(REGISTER_URL, json={"email": email, "password": password})


def _request_magic_link(client, email="magiclink@example.com"):
    return client.post(MAGIC_LINK_REQUEST_URL, json={"email": email})


def _latest_magic_link_token(fake_email_transport) -> str:
    """Pull the token straight out of the most recently captured email body."""

    message = fake_email_transport.messages[-1]
    match = URL_PATTERN.search(message.text_body)
    assert match, f"No magic link URL found in captured email: {message.text_body!r}"
    query = parse_qs(urlparse(match.group(1)).query)
    assert "token" in query, f"Magic link URL had no token param: {match.group(1)!r}"
    return query["token"][0]


# --- Requesting a link --------------------------------------------------------


def test_request_magic_link_sends_email_for_existing_active_user(client, fake_email_transport):
    _register(client)
    fake_email_transport.messages.clear()  # registration itself sends an OTP email

    response = _request_magic_link(client)

    assert response.status_code == 200
    assert response.json() == {"message": GENERIC_MESSAGE}
    assert len(fake_email_transport.messages) == 1
    assert fake_email_transport.messages[0].to_address == "magiclink@example.com"


def test_request_magic_link_returns_generic_message_for_unknown_email(client, fake_email_transport):
    response = _request_magic_link(client, email="ghost@example.com")

    assert response.status_code == 200
    assert response.json() == {"message": GENERIC_MESSAGE}
    assert len(fake_email_transport.messages) == 0


def test_request_magic_link_rejects_malformed_email(client):
    response = client.post(MAGIC_LINK_REQUEST_URL, json={"email": "not-an-email"})

    assert response.status_code == 422


def test_request_magic_link_is_cooldown_limited(client, fake_email_transport):
    _register(client)
    fake_email_transport.messages.clear()

    first = _request_magic_link(client)
    second = _request_magic_link(client)

    assert first.status_code == 200
    assert second.status_code == 200
    # Same generic message both times, but only the first actually sent mail.
    assert len(fake_email_transport.messages) == 1


def test_request_magic_link_skips_inactive_account(client, fake_email_transport):
    from sqlalchemy import text

    from app.core.database import engine

    _register(client, email="inactive-ml@example.com")
    fake_email_transport.messages.clear()

    with engine.begin() as connection:
        connection.execute(
            text("UPDATE users SET is_active = false WHERE email = :email"),
            {"email": "inactive-ml@example.com"},
        )

    response = _request_magic_link(client, email="inactive-ml@example.com")

    assert response.status_code == 200
    assert len(fake_email_transport.messages) == 0


# --- Verifying a link ----------------------------------------------------------


def test_verify_magic_link_logs_in_and_sets_cookies(client, fake_email_transport):
    _register(client)
    fake_email_transport.messages.clear()
    _request_magic_link(client)
    token = _latest_magic_link_token(fake_email_transport)

    response = client.get(MAGIC_LINK_VERIFY_URL, params={"token": token})

    assert response.status_code == 200
    assert response.json()["email"] == "magiclink@example.com"
    assert ACCESS_TOKEN_COOKIE_NAME in response.cookies
    assert REFRESH_TOKEN_COOKIE_NAME in response.cookies


def test_verify_magic_link_marks_email_verified(client, fake_email_transport):
    register_response = _register(client)
    assert register_response.json()["is_email_verified"] is False

    fake_email_transport.messages.clear()
    _request_magic_link(client)
    token = _latest_magic_link_token(fake_email_transport)

    response = client.get(MAGIC_LINK_VERIFY_URL, params={"token": token})

    assert response.json()["is_email_verified"] is True


def test_verify_magic_link_rejects_unknown_token(client):
    response = client.get(MAGIC_LINK_VERIFY_URL, params={"token": "this-was-never-issued"})

    assert response.status_code == 400
    assert response.json()["error"] == "This sign-in link is invalid."


def test_verify_magic_link_is_single_use(client, fake_email_transport):
    _register(client)
    fake_email_transport.messages.clear()
    _request_magic_link(client)
    token = _latest_magic_link_token(fake_email_transport)

    first = client.get(MAGIC_LINK_VERIFY_URL, params={"token": token})
    second = client.get(MAGIC_LINK_VERIFY_URL, params={"token": token})

    assert first.status_code == 200
    assert second.status_code == 400
    assert second.json()["error"] == "This sign-in link has already been used."


def test_verify_magic_link_rejects_expired_token(client, fake_email_transport):
    from datetime import UTC, datetime, timedelta

    from sqlalchemy import text

    from app.core.database import engine

    _register(client)
    fake_email_transport.messages.clear()
    _request_magic_link(client)
    token = _latest_magic_link_token(fake_email_transport)

    expired_at = datetime.now(UTC) - timedelta(minutes=1)
    with engine.begin() as connection:
        connection.execute(
            text("UPDATE magic_link_tokens SET expires_at = :expires_at"),
            {"expires_at": expired_at},
        )

    response = client.get(MAGIC_LINK_VERIFY_URL, params={"token": token})

    assert response.status_code == 400
    assert response.json()["error"] == "This sign-in link has expired. Please request a new one."


def test_verify_magic_link_rejects_inactive_account(client, fake_email_transport):
    from sqlalchemy import text

    from app.core.database import engine

    _register(client, email="ml-goes-inactive@example.com")
    fake_email_transport.messages.clear()
    _request_magic_link(client, email="ml-goes-inactive@example.com")
    token = _latest_magic_link_token(fake_email_transport)

    with engine.begin() as connection:
        connection.execute(
            text("UPDATE users SET is_active = false WHERE email = :email"),
            {"email": "ml-goes-inactive@example.com"},
        )

    response = client.get(MAGIC_LINK_VERIFY_URL, params={"token": token})

    assert response.status_code == 401
