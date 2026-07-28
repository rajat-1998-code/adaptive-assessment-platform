"""Reusable email rendering and delivery services."""

from __future__ import annotations

import smtplib
from dataclasses import dataclass
from datetime import UTC, datetime
from email.message import EmailMessage
from pathlib import Path
from typing import Protocol

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.core.config import settings


@dataclass(slots=True)
class EmailMessagePayload:
    """Normalized email payload used by the email transport abstraction."""

    to_address: str
    subject: str
    html_body: str
    text_body: str
    from_name: str
    from_address: str


class EmailTransport(Protocol):
    """Abstract transport that can deliver email payloads."""

    def send(self, payload: EmailMessagePayload) -> None:
        """Send the given email payload."""


class SMTPEmailTransport:
    """SMTP-backed transport compatible with MailHog and real SMTP servers."""

    def send(self, payload: EmailMessagePayload) -> None:
        message = EmailMessage()
        message["Subject"] = payload.subject
        message["From"] = f"{payload.from_name} <{payload.from_address}>"
        message["To"] = payload.to_address
        message.set_content(payload.text_body)
        message.add_alternative(payload.html_body, subtype="html")

        password = (
            settings.SMTP_PASSWORD.get_secret_value()
            if settings.SMTP_PASSWORD is not None
            else None
        )

        smtp_class = smtplib.SMTP_SSL if settings.SMTP_USE_TLS else smtplib.SMTP

        with smtp_class(settings.SMTP_HOST, settings.SMTP_PORT) as smtp:
            if settings.SMTP_USE_STARTTLS:
                smtp.starttls()

            if settings.SMTP_USERNAME:
                smtp.login(settings.SMTP_USERNAME, password or "")

            smtp.send_message(message)


class EmailTemplateRenderer:
    """Renders HTML and text emails from Jinja templates."""

    def __init__(self, template_dir: Path | None = None):
        self.template_dir = template_dir or settings.EMAIL_TEMPLATE_DIR
        self.environment = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def render(self, template_name: str, context: dict[str, object]) -> str:
        template = self.environment.get_template(template_name)
        return template.render(**context)


class EmailService:
    """Coordinates template rendering and email delivery."""

    def __init__(
        self,
        transport: EmailTransport | None = None,
        renderer: EmailTemplateRenderer | None = None,
    ):
        self.transport = transport or SMTPEmailTransport()
        self.renderer = renderer or EmailTemplateRenderer()

    def build_welcome_email(self, *, to_address: str, recipient_name: str) -> EmailMessagePayload:
        context = self._build_base_context(
            headline="Welcome to Adaptive Assessment Platform",
            preheader="Your account is ready for smarter assessments and personalized learning.",
            recipient_name=recipient_name,
        )
        context["dashboard_url"] = settings.FRONTEND_BASE_URL

        return EmailMessagePayload(
            to_address=to_address,
            subject="Welcome to Adaptive Assessment Platform",
            html_body=self.renderer.render("welcome.html", context),
            text_body=(
                f"Welcome to Adaptive Assessment Platform, {recipient_name}.\n\n"
                f"Visit your dashboard: {settings.FRONTEND_BASE_URL}"
            ),
            from_name=settings.EMAIL_FROM_NAME,
            from_address=settings.EMAIL_FROM_ADDRESS,
        )

    def build_otp_email(
        self,
        *,
        to_address: str,
        recipient_name: str,
        otp_code: str,
    ) -> EmailMessagePayload:
        context = self._build_base_context(
            headline="Verify your email address",
            preheader="Use the one-time code below to verify your Adaptive Assessment account.",
            recipient_name=recipient_name,
        )
        context["otp_code"] = otp_code
        context["otp_expiry_minutes"] = settings.AUTH_OTP_EXPIRE_MINUTES

        return EmailMessagePayload(
            to_address=to_address,
            subject="Your verification code",
            html_body=self.renderer.render("otp.html", context),
            text_body=(
                f"Hi {recipient_name},\n\n"
                f"Your verification code is {otp_code}. "
                f"It expires in {settings.AUTH_OTP_EXPIRE_MINUTES} minutes."
            ),
            from_name=settings.EMAIL_FROM_NAME,
            from_address=settings.EMAIL_FROM_ADDRESS,
        )

    def build_magic_link_email(
        self,
        *,
        to_address: str,
        recipient_name: str,
        magic_link_url: str,
    ) -> EmailMessagePayload:
        context = self._build_base_context(
            headline="Your secure sign-in link",
            preheader="Use the magic link below to sign in without a password.",
            recipient_name=recipient_name,
        )
        context["magic_link_url"] = magic_link_url
        context["magic_link_expiry_minutes"] = settings.AUTH_MAGIC_LINK_EXPIRE_MINUTES

        return EmailMessagePayload(
            to_address=to_address,
            subject="Your magic sign-in link",
            html_body=self.renderer.render("magic_link.html", context),
            text_body=(
                f"Hi {recipient_name},\n\n"
                f"Use this sign-in link: {magic_link_url}\n"
                f"It expires in {settings.AUTH_MAGIC_LINK_EXPIRE_MINUTES} minutes."
            ),
            from_name=settings.EMAIL_FROM_NAME,
            from_address=settings.EMAIL_FROM_ADDRESS,
        )

    def send_welcome_email(self, *, to_address: str, recipient_name: str) -> None:
        self.transport.send(
            self.build_welcome_email(to_address=to_address, recipient_name=recipient_name)
        )

    def send_otp_email(self, *, to_address: str, recipient_name: str, otp_code: str) -> None:
        self.transport.send(
            self.build_otp_email(
                to_address=to_address,
                recipient_name=recipient_name,
                otp_code=otp_code,
            )
        )

    def send_magic_link_email(
        self,
        *,
        to_address: str,
        recipient_name: str,
        magic_link_url: str,
    ) -> None:
        self.transport.send(
            self.build_magic_link_email(
                to_address=to_address,
                recipient_name=recipient_name,
                magic_link_url=magic_link_url,
            )
        )

    @staticmethod
    def _build_base_context(
        *,
        headline: str,
        preheader: str,
        recipient_name: str,
    ) -> dict[str, object]:
        return {
            "app_name": settings.APP_NAME,
            "headline": headline,
            "preheader": preheader,
            "recipient_name": recipient_name,
            "support_email": settings.EMAIL_FROM_ADDRESS,
            "mailhog_ui_url": settings.MAILHOG_UI_URL,
            "frontend_base_url": settings.FRONTEND_BASE_URL,
            "app_environment": settings.ENVIRONMENT,
            "current_year": datetime.now(UTC).year,
        }


def get_email_service() -> EmailService:
    """
    FastAPI dependency provider for EmailService.

    Routes should depend on this (rather than instantiating EmailService
    directly) so tests can override it with a fake transport instead of
    talking to a real SMTP server.
    """

    return EmailService()
