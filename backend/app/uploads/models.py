"""Document persistence model.

The uploads package remains as a compatibility boundary for the original
metadata-only upload API. The persisted resource is now a Document; actual
file storage is intentionally deferred to the storage integration milestone.
"""

from __future__ import annotations

import os
import uuid

from sqlalchemy import CheckConstraint, Index, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.mixins import GuestOwnableMixin, TimestampMixin


def _title_from_filename(filename: str) -> str:
    """Return a user-friendly default title without the final extension."""

    title = os.path.splitext(filename.strip())[0].strip()
    return title or filename.strip()


class Document(GuestOwnableMixin, TimestampMixin, Base):
    """A document owned by either a guest session or an authenticated user."""

    __tablename__ = "documents"
    __table_args__ = (
        CheckConstraint(
            "(owner_user_id IS NOT NULL) != (owner_guest_id IS NOT NULL)",
            name="ck_documents_single_owner",
        ),
        Index("ix_documents_owner_user_id", "owner_user_id"),
        Index("ix_documents_owner_guest_id", "owner_guest_id"),
        Index("ix_documents_title", "title"),
        Index("ix_documents_original_filename", "original_filename"),
        Index("ix_documents_processing_status", "processing_status"),
        Index("ix_documents_created_at", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(512), nullable=False)
    content_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # Nullable during the metadata-only phase and for legacy row migration.
    storage_key: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    processing_status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="uploaded", server_default="uploaded"
    )

    def __init__(self, **kwargs: object) -> None:
        """Set the initial title from the filename when one is not supplied."""

        original_filename = kwargs.get("original_filename")
        if kwargs.get("title") is None and isinstance(original_filename, str):
            kwargs["title"] = _title_from_filename(original_filename)
        if kwargs.get("processing_status") is None:
            kwargs["processing_status"] = "uploaded"
        super().__init__(**kwargs)


# Compatibility alias for code importing the old model name.
Upload = Document
