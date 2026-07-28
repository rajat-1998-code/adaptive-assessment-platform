"""Upload persistence model.

This is intentionally metadata-only for now (filename/content-type/size,
no actual file bytes or object storage) — the point of this stage is the
guest-session ownership and migration mechanics, not a full upload
pipeline. Real file storage (S3/MinIO) is future work.
"""

from __future__ import annotations

import uuid

from sqlalchemy import CheckConstraint, Index, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.mixins import GuestOwnableMixin, TimestampMixin


class Upload(GuestOwnableMixin, TimestampMixin, Base):
    """A file uploaded by either a guest session or an authenticated user."""

    __tablename__ = "uploads"
    __table_args__ = (
        CheckConstraint(
            "(owner_user_id IS NOT NULL) != (owner_guest_id IS NOT NULL)",
            name="ck_uploads_single_owner",
        ),
        Index("ix_uploads_owner_user_id", "owner_user_id"),
        Index("ix_uploads_owner_guest_id", "owner_guest_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    content_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
