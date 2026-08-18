"""Document schemas and backwards-compatible upload schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
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


class DocumentMetadataResponse(BaseModel):
    """Public document metadata returned to the document library."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    original_filename: str
    content_type: str | None
    file_size: int | None
    processing_status: str
    created_at: datetime
    updated_at: datetime


class DocumentListQuery(BaseModel):
    """Validated query options for the document library."""

    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    search: str | None = Field(default=None, max_length=256)
    file_type: str | None = Field(default=None, max_length=16)
    status: str | None = Field(default=None, max_length=32)
    sort_by: Literal["created_at", "title", "original_filename", "processing_status"] = "created_at"
    sort_order: Literal["asc", "desc"] = "desc"


class PaginatedDocumentResponse(BaseModel):
    """Page of documents plus pagination metadata."""

    items: list[DocumentMetadataResponse]
    page: int
    page_size: int
    total: int
    pages: int


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
