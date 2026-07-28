"""Shared SQLAlchemy declarative mixins used across domain models."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column


class TimestampMixin:
    """Common created_at/updated_at columns shared across models."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class GuestOwnableMixin:
    """
    Adds dual ownership columns for resources that can belong to either
    an anonymous guest session (Redis-backed, see app.guest) or an
    authenticated user — e.g. uploads or assessments started before login.

    Subclasses must add a matching CheckConstraint to their own
    __table_args__ so exactly one owner column is ever set, e.g.:

        __table_args__ = (
            CheckConstraint(
                "(owner_user_id IS NOT NULL) != (owner_guest_id IS NOT NULL)",
                name="ck_<table>_single_owner",
            ),
        )
    """

    owner_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=True
    )
    # Not a foreign key: guest identities live in Redis (app.guest), not
    # Postgres, since they're meant to be short-lived and disposable.
    owner_guest_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
