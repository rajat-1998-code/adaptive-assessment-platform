"""Service layer for the uploads module."""

from __future__ import annotations

import uuid

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.guest.schemas import Identity
from app.uploads.models import Document
from app.uploads.schemas import CreateUploadRequest, UploadResponse


def _to_response(upload: Document) -> UploadResponse:
    return UploadResponse(
        id=upload.id,
        filename=upload.original_filename,
        content_type=upload.content_type,
        size_bytes=upload.file_size,
        created_at=upload.created_at,
        owner_type="user" if upload.owner_user_id is not None else "guest",
    )


def create_upload_record(
    db: Session, *, identity: Identity, payload: CreateUploadRequest
) -> UploadResponse:
    """Create an upload owned by whichever identity (guest or user) made the request."""

    upload = Document(
        original_filename=payload.filename,
        content_type=payload.content_type,
        file_size=payload.size_bytes,
        owner_user_id=identity.user.id if identity.user is not None else None,
        owner_guest_id=identity.guest_id,
    )
    db.add(upload)
    db.commit()
    db.refresh(upload)

    return _to_response(upload)


def list_upload_records(db: Session, *, identity: Identity) -> list[UploadResponse]:
    """List uploads owned by the current identity, newest first."""

    if identity.user is not None:
        stmt = select(Document).where(Document.owner_user_id == identity.user.id)
    else:
        stmt = select(Document).where(Document.owner_guest_id == identity.guest_id)

    uploads = db.scalars(stmt.order_by(Document.created_at.desc())).all()
    return [_to_response(upload) for upload in uploads]


def migrate_guest_documents_to_user(db: Session, *, guest_id: uuid.UUID, user_id: uuid.UUID) -> int:
    """
    Reassign every document owned by a guest session to a newly authenticated
    user. Returns the number of rows migrated (useful for tests/logging).
    """

    result = db.execute(
        update(Document)
        .where(Document.owner_guest_id == guest_id)
        .values(owner_guest_id=None, owner_user_id=user_id)
    )
    return result.rowcount


def migrate_guest_uploads_to_user(db: Session, *, guest_id: uuid.UUID, user_id: uuid.UUID) -> int:
    """Compatibility wrapper for callers using the former upload name."""

    return migrate_guest_documents_to_user(db, guest_id=guest_id, user_id=user_id)
