"""Shared pytest fixtures for the backend test suite."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.core.database import engine
from app.main import app


@pytest.fixture(autouse=True)
def _clean_auth_tables():
    """
    Ensure each test starts with empty auth tables.

    This suite talks to a real Postgres database (see test_readiness.py's
    docstring for why), so tests that create users/sessions/tokens need a
    predictable, isolated starting point rather than leftover rows from a
    previous test.
    """
    with engine.begin() as connection:
        connection.execute(
            text(
                "TRUNCATE TABLE magic_link_tokens, refresh_tokens, "
                "user_sessions, users RESTART IDENTITY CASCADE"
            )
        )
    yield


@pytest.fixture
def client():
    """A fresh TestClient per test, so cookies never leak between tests."""

    return TestClient(app)
"""Shared pytest fixtures for the backend test suite."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.core.database import engine
from app.core.redis_client import redis_client
from app.main import app
from app.services.email.service import EmailMessagePayload, EmailService, get_email_service


class RecordingEmailTransport:
    """Test transport that records payloads instead of sending them over SMTP."""

    def __init__(self):
        self.messages: list[EmailMessagePayload] = []

    def send(self, payload: EmailMessagePayload) -> None:
        self.messages.append(payload)


@pytest.fixture(autouse=True)
def _clean_auth_tables():
    """
    Ensure each test starts with empty auth tables.

    This suite talks to a real Postgres database (see test_readiness.py's
    docstring for why), so tests that create users/sessions/tokens need a
    predictable, isolated starting point rather than leftover rows from a
    previous test.
    """
    with engine.begin() as connection:
        connection.execute(
            text(
                "TRUNCATE TABLE magic_link_tokens, refresh_tokens, "
                "user_sessions, users RESTART IDENTITY CASCADE"
            )
        )
    yield


@pytest.fixture(autouse=True)
def _clean_otp_keys():
    """Flush leftover OTP/cooldown keys from Redis between tests."""
    for pattern in ("auth:otp:*", "auth:otp:cooldown:*"):
        keys = redis_client.keys(pattern)
        if keys:
            redis_client.delete(*keys)
    yield


@pytest.fixture
def fake_email_transport():
    """Exposes sent messages so tests can inspect (e.g. extract) OTP codes."""

    return RecordingEmailTransport()


@pytest.fixture(autouse=True)
def _override_email_service(fake_email_transport):
    """
    Never let tests send real email.

    This repo has no SMTP/MailHog service in CI (see backend-ci.yml), so
    without this override, any test that registers a user or resends an
    OTP would try to connect to a real SMTP server and fail/hang.
    """
    app.dependency_overrides[get_email_service] = lambda: EmailService(
        transport=fake_email_transport
    )
    yield
    app.dependency_overrides.pop(get_email_service, None)


@pytest.fixture
def client():
    """A fresh TestClient per test, so cookies never leak between tests."""

    return TestClient(app)
