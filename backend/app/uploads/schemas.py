"""Document schemas and backwards-compatible upload schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DocumentResponse(BaseModel):
    """Public metadata representation of a document."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    owner_user_id: UUID | None
    owner_guest_id: UUID | None
    title: str
    original_filename: str
    content_type: str | None
    file_size: int | None
    storage_key: str | None
    processing_status: str
    created_at: datetime
    updated_at: datetime


class DocumentRenameRequest(BaseModel):
    """Payload for renaming a document without changing its file metadata."""

    title: str = Field(min_length=1, max_length=512)


class CreateDocumentMetadata(BaseModel):
    """Metadata contract used by the upcoming document upload endpoint."""

    title: str | None = Field(default=None, min_length=1, max_length=512)
    original_filename: str = Field(min_length=1, max_length=512)
    content_type: str | None = Field(default=None, max_length=128)
    file_size: int | None = Field(default=None, ge=0)
    storage_key: str | None = Field(default=None, max_length=1024)
    processing_status: str = Field(default="uploaded", min_length=1, max_length=32)


class CreateUploadRequest(BaseModel):
    """Legacy payload for the metadata-only `/uploads` compatibility route."""

    filename: str = Field(min_length=1, max_length=512)
    content_type: str | None = None
    size_bytes: int | None = Field(default=None, ge=0)


class UploadResponse(BaseModel):
    """Legacy response shape retained for existing upload clients."""

    id: UUID
    filename: str
    content_type: str | None
    size_bytes: int | None
    created_at: datetime
    owner_type: str
