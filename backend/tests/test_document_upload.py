"""Tests for document upload validation and storage/database coordination."""

from __future__ import annotations

import asyncio
import io
import uuid

import pytest
from fastapi import UploadFile

from app.documents.service import (
    DocumentValidationError,
    create_document_from_upload,
    validate_filename,
)
from app.guest.schemas import Identity
from app.uploads.models import Document


class FakeStorage:
    def __init__(self, *, fail_upload: bool = False):
        self.fail_upload = fail_upload
        self.uploads: list[dict] = []
        self.deleted: list[str] = []

    def upload_fileobj(self, fileobj, *, storage_key, content_type, file_size):
        if self.fail_upload:
            from app.storage.service import StorageError

            raise StorageError("upload failed")
        self.uploads.append(
            {
                "key": storage_key,
                "content": fileobj.read(),
                "content_type": content_type,
                "file_size": file_size,
            }
        )

    def delete_object(self, storage_key):
        self.deleted.append(storage_key)


class FakeSession:
    def __init__(self, *, fail_commit: bool = False):
        self.fail_commit = fail_commit
        self.added: list[Document] = []
        self.rolled_back = False

    def add(self, document):
        self.added.append(document)

    def commit(self):
        if self.fail_commit:
            raise RuntimeError("database failed")

    def refresh(self, document):
        return None

    def rollback(self):
        self.rolled_back = True


def _upload(filename: str, content: bytes, content_type: str | None = None) -> UploadFile:
    return UploadFile(
        file=io.BytesIO(content),
        filename=filename,
        headers={"content-type": content_type} if content_type else None,
    )


def test_validate_filename_accepts_supported_type_and_normalizes_extension():
    filename, content_type = validate_filename(
        "folder/REPORT.PDF", "application/pdf; charset=binary"
    )

    assert filename == "REPORT.PDF"
    assert content_type == "application/pdf"


@pytest.mark.parametrize("filename", ["notes.exe", "notes", ""])
def test_validate_filename_rejects_unsupported_or_missing_extension(filename):
    with pytest.raises(DocumentValidationError):
        validate_filename(filename, "application/octet-stream")


def test_validate_filename_rejects_mismatched_content_type():
    with pytest.raises(DocumentValidationError, match="does not match"):
        validate_filename("notes.pdf", "text/plain")


def test_upload_persists_document_after_storage_upload():
    db = FakeSession()
    storage = FakeStorage()
    guest_id = uuid.uuid4()

    document = asyncio.run(
        create_document_from_upload(
            db,
            identity=Identity(user=None, guest_id=guest_id),
            upload=_upload("lesson.txt", b"hello", "text/plain"),
            storage=storage,
        )
    )

    assert document.owner_guest_id == guest_id
    assert document.title == "lesson"
    assert document.file_size == 5
    assert document.storage_key.startswith(f"documents/{document.id}/")
    assert storage.uploads[0]["content"] == b"hello"
    assert storage.deleted == []


def test_database_failure_removes_uploaded_object():
    db = FakeSession(fail_commit=True)
    storage = FakeStorage()

    with pytest.raises(RuntimeError, match="database failed"):
        asyncio.run(
            create_document_from_upload(
                db,
                identity=Identity(user=None, guest_id=uuid.uuid4()),
                upload=_upload("lesson.txt", b"hello", "text/plain"),
                storage=storage,
            )
        )

    assert db.rolled_back is True
    assert len(storage.uploads) == 1
    assert storage.deleted == [storage.uploads[0]["key"]]


def test_storage_failure_does_not_add_database_record():
    db = FakeSession()
    storage = FakeStorage(fail_upload=True)

    with pytest.raises(Exception, match="upload failed"):
        asyncio.run(
            create_document_from_upload(
                db,
                identity=Identity(user=None, guest_id=uuid.uuid4()),
                upload=_upload("lesson.txt", b"hello", "text/plain"),
                storage=storage,
            )
        )

    assert db.added == []
    assert db.rolled_back is True
