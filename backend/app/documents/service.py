"""Document upload validation and persistence workflow."""

from __future__ import annotations

import logging
import math
import uuid
from pathlib import PurePath

from fastapi import UploadFile
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.guest.schemas import Identity
from app.storage.service import StorageError, StorageService
from app.uploads.models import Document
from app.uploads.schemas import DocumentListQuery

logger = logging.getLogger(__name__)

SUPPORTED_CONTENT_TYPES: dict[str, frozenset[str]] = {
    ".pdf": frozenset({"application/pdf"}),
    ".docx": frozenset(
        {
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        }
    ),
    ".txt": frozenset({"text/plain", "application/octet-stream"}),
    ".md": frozenset({"text/markdown", "text/plain", "application/octet-stream"}),
    ".pptx": frozenset(
        {
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        }
    ),
    ".png": frozenset({"image/png"}),
    ".jpg": frozenset({"image/jpeg"}),
    ".jpeg": frozenset({"image/jpeg"}),
}
DEFAULT_CONTENT_TYPES = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".txt": "text/plain",
    ".md": "text/markdown",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
}


class DocumentValidationError(ValueError):
    """Raised when an uploaded file violates document policy."""


def validate_filename(filename: str | None, content_type: str | None) -> tuple[str, str]:
    """Validate the filename/type pair and return normalized values."""

    safe_name = PurePath(filename or "").name.strip()
    extension = PurePath(safe_name).suffix.lower()
    if not safe_name or not extension:
        raise DocumentValidationError("A supported file extension is required")

    allowed_types = SUPPORTED_CONTENT_TYPES.get(extension)
    if allowed_types is None:
        supported = ", ".join(sorted(SUPPORTED_CONTENT_TYPES))
        raise DocumentValidationError(f"Unsupported file type. Supported types: {supported}")

    normalized_type = (
        (content_type or DEFAULT_CONTENT_TYPES[extension]).split(";", 1)[0].strip().lower()
    )
    if normalized_type not in allowed_types:
        raise DocumentValidationError("File content type does not match its extension")

    return safe_name, normalized_type


async def get_upload_size(upload: UploadFile) -> int:
    """Measure the parsed upload without loading it into application memory."""

    upload.file.seek(0, 2)
    file_size = upload.file.tell()
    await upload.seek(0)
    return file_size


async def create_document_from_upload(
    db: Session,
    *,
    identity: Identity,
    upload: UploadFile,
    storage: StorageService,
) -> Document:
    """Upload bytes and persist metadata with compensating object cleanup."""

    filename, content_type = validate_filename(upload.filename, upload.content_type)
    file_size = await get_upload_size(upload)
    if file_size > settings.DOCUMENT_MAX_SIZE_BYTES:
        raise DocumentValidationError("File exceeds the 25 MiB maximum size")

    document_id = uuid.uuid4()
    storage_key = f"documents/{document_id}/{uuid.uuid4().hex}"
    document = Document(
        id=document_id,
        original_filename=filename,
        content_type=content_type,
        file_size=file_size,
        storage_key=storage_key,
        owner_user_id=identity.user.id if identity.user is not None else None,
        owner_guest_id=identity.guest_id,
    )

    uploaded = False
    committed = False
    try:
        await upload.seek(0)
        storage.upload_fileobj(
            upload.file,
            storage_key=storage_key,
            content_type=content_type,
            file_size=file_size,
        )
        uploaded = True

        db.add(document)
        db.commit()
        db.refresh(document)
        committed = True
        return document
    except StorageError:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise
    finally:
        if uploaded and not committed:
            try:
                storage.delete_object(storage_key)
            except StorageError:
                logger.exception("Failed to clean up object %s after database failure", storage_key)


def _owned_documents_query(identity: Identity):
    """Return the base query scoped to the current guest or user."""

    if identity.user is not None:
        return select(Document).where(Document.owner_user_id == identity.user.id)
    return select(Document).where(Document.owner_guest_id == identity.guest_id)


def _owned_documents_count_query(identity: Identity):
    """Return a count query scoped to the current guest or user."""

    if identity.user is not None:
        return (
            select(func.count())
            .select_from(Document)
            .where(Document.owner_user_id == identity.user.id)
        )
    return (
        select(func.count())
        .select_from(Document)
        .where(Document.owner_guest_id == identity.guest_id)
    )


def _apply_document_filters(query, options: DocumentListQuery):
    """Apply shared search and filter predicates to a document query."""

    if options.search and options.search.strip():
        search = f"%{options.search.strip()}%"
        query = query.where(
            or_(Document.title.ilike(search), Document.original_filename.ilike(search))
        )

    if options.file_type and options.file_type.strip():
        file_type = options.file_type.strip().lower().lstrip(".")
        query = query.where(Document.original_filename.ilike(f"%.{file_type}"))

    if options.status and options.status.strip():
        query = query.where(Document.processing_status == options.status.strip().lower())

    return query


def list_documents(
    db: Session, *, identity: Identity, options: DocumentListQuery
) -> tuple[list[Document], int]:
    """Return the current owner's filtered document page and total count."""

    filtered_query = _apply_document_filters(_owned_documents_query(identity), options)
    count_query = _apply_document_filters(_owned_documents_count_query(identity), options)
    total = db.scalar(count_query) or 0

    sort_column = {
        "created_at": Document.created_at,
        "title": Document.title,
        "original_filename": Document.original_filename,
        "processing_status": Document.processing_status,
    }[options.sort_by]
    sort_expression = sort_column.asc() if options.sort_order == "asc" else sort_column.desc()
    query = filtered_query.order_by(sort_expression, Document.id.asc())
    offset = (options.page - 1) * options.page_size
    documents = db.scalars(query.offset(offset).limit(options.page_size)).all()
    return documents, total


def get_owned_document(
    db: Session, *, identity: Identity, document_id: uuid.UUID
) -> Document | None:
    """Fetch one document only when it belongs to the current identity."""

    query = _owned_documents_query(identity).where(Document.id == document_id)
    return db.scalar(query)


def page_count(total: int, page_size: int) -> int:
    """Calculate the number of available pages, including zero for no results."""

    return math.ceil(total / page_size) if total else 0
