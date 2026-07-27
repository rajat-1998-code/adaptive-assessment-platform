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
