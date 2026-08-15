"""Document upload validation and persistence workflow."""

from __future__ import annotations

import logging
import uuid
from pathlib import PurePath

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.guest.schemas import Identity
from app.storage.service import StorageError, StorageService
from app.uploads.models import Document

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
