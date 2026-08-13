"""OAuth provider integration via Authlib."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from authlib.integrations.starlette_client import OAuth, OAuthError
from fastapi import Request
from starlette.responses import Response

from app.auth.constants import OAUTH_PROVIDER_GITHUB, OAUTH_PROVIDER_GOOGLE
from app.auth.exceptions import (
    OAuthAuthenticationError,
    OAuthConfigurationError,
    OAuthEmailRequiredError,
    UnsupportedOAuthProviderError,
)
from app.core.config import settings


@dataclass(slots=True)
class OAuthIdentity:
    """Normalized provider identity used by the auth service."""

    email: str
    email_verified: bool
    provider: str
    subject: str
    first_name: str | None = None
    last_name: str | None = None


class OAuthService:
    """Thin Authlib-backed wrapper used by routes and easily overridable in tests."""

    def __init__(self) -> None:
        self._oauth = OAuth()
        self._register_clients()

    def _register_clients(self) -> None:
        self._oauth.register(
            name=OAUTH_PROVIDER_GOOGLE,
            client_id=settings.AUTH_GOOGLE_CLIENT_ID,
            client_secret=(
                settings.AUTH_GOOGLE_CLIENT_SECRET.get_secret_value()
                if settings.AUTH_GOOGLE_CLIENT_SECRET
                else None
            ),
            server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
            client_kwargs={"scope": "openid email profile"},
        )
        self._oauth.register(
            name=OAUTH_PROVIDER_GITHUB,
            client_id=settings.AUTH_GITHUB_CLIENT_ID,
            client_secret=(
                settings.AUTH_GITHUB_CLIENT_SECRET.get_secret_value()
                if settings.AUTH_GITHUB_CLIENT_SECRET
                else None
            ),
            authorize_url="https://github.com/login/oauth/authorize",
            access_token_url="https://github.com/login/oauth/access_token",
            api_base_url="https://api.github.com/",
            client_kwargs={"scope": "read:user user:email"},
        )

    def _client(self, provider: str):
        client = self._oauth.create_client(provider)
        if client is None:
            raise UnsupportedOAuthProviderError()
        return client

    def _assert_provider_configured(self, provider: str) -> None:
        if provider == OAUTH_PROVIDER_GOOGLE:
            configured = bool(settings.AUTH_GOOGLE_CLIENT_ID and settings.AUTH_GOOGLE_CLIENT_SECRET)
        elif provider == OAUTH_PROVIDER_GITHUB:
            configured = bool(settings.AUTH_GITHUB_CLIENT_ID and settings.AUTH_GITHUB_CLIENT_SECRET)
        else:
            raise UnsupportedOAuthProviderError()

        if not configured:
            raise OAuthConfigurationError(f"{provider.title()} OAuth is not configured")

    async def authorize_redirect(self, request: Request, provider: str) -> Response:
        """Start the browser redirect flow for a configured provider."""

        self._assert_provider_configured(provider)
        client = self._client(provider)
        redirect_uri = request.url_for("oauth_callback_endpoint", provider=provider)

        try:
            return await client.authorize_redirect(request, redirect_uri)
        except OAuthError as exc:
            raise OAuthAuthenticationError(str(exc)) from exc

    async def fetch_identity(self, request: Request, provider: str) -> OAuthIdentity:
        """Finish the provider callback and normalize the identity payload."""

        self._assert_provider_configured(provider)
        client = self._client(provider)

        try:
            token = await client.authorize_access_token(request)
        except OAuthError as exc:
            raise OAuthAuthenticationError(str(exc)) from exc

        if provider == OAUTH_PROVIDER_GOOGLE:
            return await self._fetch_google_identity(client, token)
        if provider == OAUTH_PROVIDER_GITHUB:
            return await self._fetch_github_identity(client, token)

        raise UnsupportedOAuthProviderError()

    async def _fetch_google_identity(self, client: Any, token: dict[str, Any]) -> OAuthIdentity:
        userinfo = token.get("userinfo")
        if userinfo is None:
            userinfo = await client.userinfo(token=token)

        email = str(userinfo.get("email") or "").strip().lower()
        subject = str(userinfo.get("sub") or "").strip()

        if not email or not subject:
            raise OAuthEmailRequiredError("Google OAuth did not return a usable identity payload")

        return OAuthIdentity(
            email=email,
            email_verified=bool(userinfo.get("email_verified", False)),
            provider=OAUTH_PROVIDER_GOOGLE,
            subject=subject,
            first_name=str(userinfo.get("given_name") or "").strip() or None,
            last_name=str(userinfo.get("family_name") or "").strip() or None,
        )

    async def _fetch_github_identity(self, client: Any, token: dict[str, Any]) -> OAuthIdentity:
        profile_response = await client.get("user", token=token)
        emails_response = await client.get("user/emails", token=token)

        profile = profile_response.json()
        emails = emails_response.json()

        subject = str(profile.get("id") or "").strip()
        selected_email = self._select_github_email(emails)

        if not subject:
            raise OAuthAuthenticationError("GitHub OAuth did not return a usable subject")
        if selected_email is None:
            raise OAuthEmailRequiredError(
                "GitHub OAuth did not return a verified primary email address"
            )

        return OAuthIdentity(
            email=selected_email["email"].strip().lower(),
            email_verified=bool(selected_email.get("verified", False)),
            provider=OAUTH_PROVIDER_GITHUB,
            subject=subject,
            first_name=(str(profile.get("name") or "").strip().split(" ", 1)[0] or None),
            last_name=(
                str(profile.get("name") or "").strip().split(" ", 1)[1]
                if " " in str(profile.get("name") or "").strip()
                else None
            ),
        )

    def _select_github_email(self, emails: list[dict[str, Any]]) -> dict[str, Any] | None:
        verified_primary = next(
            (
                entry
                for entry in emails
                if entry.get("email") and entry.get("primary") and entry.get("verified")
            ),
            None,
        )
        if verified_primary is not None:
            return verified_primary

        return next(
            (entry for entry in emails if entry.get("email") and entry.get("verified")),
            None,
        )


_oauth_service = OAuthService()


def get_oauth_service() -> OAuthService:
    """Dependency accessor for the Authlib-backed OAuth service."""

    return _oauth_service
