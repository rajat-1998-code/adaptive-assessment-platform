"""Integration tests for Google/GitHub OAuth login and account linking."""

from dataclasses import dataclass

import pytest
from sqlalchemy import select

from app.auth.constants import ACCESS_TOKEN_COOKIE_NAME, REFRESH_TOKEN_COOKIE_NAME
from app.auth.models import User
from app.auth.oauth import OAuthIdentity, get_oauth_service
from app.core.database import SessionLocal
from app.main import app

REGISTER_URL = "/api/v1/auth/register"
GOOGLE_AUTHORIZE_URL = "/api/v1/auth/oauth/google"
GOOGLE_CALLBACK_URL = "/api/v1/auth/oauth/google/callback"
GITHUB_CALLBACK_URL = "/api/v1/auth/oauth/github/callback"


@dataclass
class _RecordedRedirect:
    provider: str | None = None


class FakeOAuthService:
    """Test double that lets the suite drive callback identities deterministically."""

    def __init__(self) -> None:
        self.identities: dict[str, OAuthIdentity] = {}
        self.redirects = _RecordedRedirect()

    async def authorize_redirect(self, request, provider: str):
        from starlette.responses import RedirectResponse

        self.redirects.provider = provider
        return RedirectResponse(url=f"https://{provider}.example.test/authorize")

    async def fetch_identity(self, request, provider: str) -> OAuthIdentity:
        return self.identities[provider]


@pytest.fixture
def fake_oauth_service():
    service = FakeOAuthService()
    app.dependency_overrides[get_oauth_service] = lambda: service
    yield service
    app.dependency_overrides.pop(get_oauth_service, None)


def _register(client, email="oauth-user@example.com", password="OAuthPass123"):
    return client.post(REGISTER_URL, json={"email": email, "password": password})


def _get_user(email: str) -> User | None:
    with SessionLocal() as db:
        return db.scalar(select(User).where(User.email == email))


def test_oauth_authorize_redirects_to_google(client, fake_oauth_service):
    response = client.get(GOOGLE_AUTHORIZE_URL, follow_redirects=False)

    assert response.status_code in (302, 307)
    assert response.headers["location"] == "https://google.example.test/authorize"
    assert fake_oauth_service.redirects.provider == "google"


def test_google_oauth_callback_creates_account_and_sets_cookies(client, fake_oauth_service):
    fake_oauth_service.identities["google"] = OAuthIdentity(
        email="google.user@example.com",
        email_verified=True,
        provider="google",
        subject="google-subject-123",
    )

    response = client.get(GOOGLE_CALLBACK_URL)

    assert response.status_code == 200
    assert response.json()["email"] == "google.user@example.com"
    assert response.json()["is_email_verified"] is True
    assert ACCESS_TOKEN_COOKIE_NAME in response.cookies
    assert REFRESH_TOKEN_COOKIE_NAME in response.cookies

    user = _get_user("google.user@example.com")
    assert user is not None
    assert user.google_oauth_subject == "google-subject-123"
    assert user.github_oauth_subject is None


def test_github_oauth_callback_creates_account_and_sets_cookies(client, fake_oauth_service):
    fake_oauth_service.identities["github"] = OAuthIdentity(
        email="github.user@example.com",
        email_verified=True,
        provider="github",
        subject="github-subject-456",
    )

    response = client.get(GITHUB_CALLBACK_URL)

    assert response.status_code == 200
    assert response.json()["email"] == "github.user@example.com"
    assert ACCESS_TOKEN_COOKIE_NAME in response.cookies
    assert REFRESH_TOKEN_COOKIE_NAME in response.cookies

    user = _get_user("github.user@example.com")
    assert user is not None
    assert user.github_oauth_subject == "github-subject-456"
    assert user.google_oauth_subject is None


def test_oauth_callback_links_existing_account_by_email(client, fake_oauth_service):
    register_response = _register(client, email="linked@example.com")
    assert register_response.status_code == 201

    fake_oauth_service.identities["github"] = OAuthIdentity(
        email="linked@example.com",
        email_verified=True,
        provider="github",
        subject="github-linked-999",
    )

    response = client.get(GITHUB_CALLBACK_URL)

    assert response.status_code == 200
    assert response.json()["email"] == "linked@example.com"
    assert response.json()["is_email_verified"] is True

    user = _get_user("linked@example.com")
    assert user is not None
    assert user.github_oauth_subject == "github-linked-999"
    assert user.password_hash is not None


def test_oauth_callback_rejects_linking_existing_account_with_unverified_provider_email(
    client, fake_oauth_service
):
    register_response = _register(client, email="unverified-link@example.com")
    assert register_response.status_code == 201

    fake_oauth_service.identities["google"] = OAuthIdentity(
        email="unverified-link@example.com",
        email_verified=False,
        provider="google",
        subject="google-unverified-link",
    )

    response = client.get(GOOGLE_CALLBACK_URL)

    assert response.status_code == 409
    assert (
        response.json()["error"] == "This Google account cannot be linked without a verified email."
    )

    user = _get_user("unverified-link@example.com")
    assert user is not None
    assert user.google_oauth_subject is None


def test_oauth_callback_rejects_different_subject_for_already_linked_provider(
    client, fake_oauth_service
):
    register_response = _register(client, email="conflict@example.com")
    assert register_response.status_code == 201

    fake_oauth_service.identities["github"] = OAuthIdentity(
        email="conflict@example.com",
        email_verified=True,
        provider="github",
        subject="github-original-subject",
    )
    first_link_response = client.get(GITHUB_CALLBACK_URL)
    assert first_link_response.status_code == 200

    fake_oauth_service.identities["github"] = OAuthIdentity(
        email="conflict@example.com",
        email_verified=True,
        provider="github",
        subject="github-conflicting-subject",
    )
    second_link_response = client.get(GITHUB_CALLBACK_URL)

    assert second_link_response.status_code == 409
    assert (
        second_link_response.json()["error"]
        == "This Github account cannot be linked automatically."
    )

    user = _get_user("conflict@example.com")
    assert user is not None
    assert user.github_oauth_subject == "github-original-subject"
