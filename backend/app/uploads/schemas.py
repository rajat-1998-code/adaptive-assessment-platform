"""Schemas for the uploads module."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class CreateUploadRequest(BaseModel):
    """Payload for POST /uploads."""

    filename: str = Field(min_length=1, max_length=512)
    content_type: str | None = None
    size_bytes: int | None = Field(default=None, ge=0)


class UploadResponse(BaseModel):
    """Public representation of an upload, for either a guest or a user."""

    id: UUID
    filename: str
    content_type: str | None
    size_bytes: int | None
    created_at: datetime
    owner_type: str
