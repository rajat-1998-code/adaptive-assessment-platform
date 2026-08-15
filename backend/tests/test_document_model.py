"""Unit tests for document persistence contracts."""

import uuid

import pytest
from pydantic import ValidationError

from app.uploads.models import Document, Upload
from app.uploads.schemas import CreateDocumentMetadata, DocumentRenameRequest


def test_document_uses_documents_table_and_upload_is_compatibility_alias():
    assert Document.__table__.name == "documents"
    assert Upload is Document


def test_document_defaults_title_from_filename_and_processing_status():
    document = Document(
        owner_guest_id=uuid.uuid4(),
        original_filename="lesson.notes.pdf",
    )

    assert document.title == "lesson.notes"
    assert document.processing_status == "uploaded"
    assert document.storage_key is None


def test_document_exposes_required_columns_and_indexes():
    columns = set(Document.__table__.columns.keys())
    assert columns == {
        "id",
        "owner_user_id",
        "owner_guest_id",
        "title",
        "original_filename",
        "content_type",
        "file_size",
        "storage_key",
        "processing_status",
        "created_at",
        "updated_at",
    }

    index_names = {index.name for index in Document.__table__.indexes}
    assert {
        "ix_documents_owner_user_id",
        "ix_documents_owner_guest_id",
        "ix_documents_title",
        "ix_documents_original_filename",
        "ix_documents_processing_status",
        "ix_documents_created_at",
    }.issubset(index_names)


def test_document_has_exactly_one_owner_constraint():
    constraints = {constraint.name for constraint in Document.__table__.constraints}
    assert "ck_documents_single_owner" in constraints

    check = next(
        constraint
        for constraint in Document.__table__.constraints
        if constraint.name == "ck_documents_single_owner"
    )
    assert "owner_user_id" in str(check.sqltext)
    assert "owner_guest_id" in str(check.sqltext)


def test_document_metadata_schema_defaults_status_and_validates_bounds():
    metadata = CreateDocumentMetadata(original_filename="notes.txt")

    assert metadata.processing_status == "uploaded"
    assert metadata.title is None

    with pytest.raises(ValidationError):
        CreateDocumentMetadata(original_filename="")

    with pytest.raises(ValidationError):
        DocumentRenameRequest(title="")
