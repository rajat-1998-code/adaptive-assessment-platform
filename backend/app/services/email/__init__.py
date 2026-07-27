"""Reusable email infrastructure."""

from app.services.email.service import (
    EmailMessagePayload,
    EmailService,
    EmailTemplateRenderer,
    EmailTransport,
    SMTPEmailTransport,
)

__all__ = [
    "EmailMessagePayload",
    "EmailService",
    "EmailTemplateRenderer",
    "EmailTransport",
    "SMTPEmailTransport",
]
