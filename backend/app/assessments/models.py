"""Minimal assessment persistence model.

This stage (guest session management) only needs assessments to prove
out the same guest/user ownership pattern as uploads — the actual
assessment-generation pipeline (RAG, question generation, scoring) is
future work and deliberately not built here. Treat this as a structural
placeholder: the shape future stages build on, not the finished feature.
"""

from __future__ import annotations

import uuid

from sqlalchemy import CheckConstraint, Index, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.mixins import GuestOwnableMixin, TimestampMixin


class Assessment(GuestOwnableMixin, TimestampMixin, Base):
    """An assessment started by either a guest session or an authenticated user."""

    __tablename__ = "assessments"
    __table_args__ = (
        CheckConstraint(
            "(owner_user_id IS NOT NULL) != (owner_guest_id IS NOT NULL)",
            name="ck_assessments_single_owner",
        ),
        Index("ix_assessments_owner_user_id", "owner_user_id"),
        Index("ix_assessments_owner_guest_id", "owner_guest_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
