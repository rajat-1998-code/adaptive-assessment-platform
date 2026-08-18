"""Integration tests for document library queries."""

import uuid

from app.core.database import SessionLocal
from app.documents.service import get_owned_document, list_documents, page_count
from app.guest.schemas import Identity
from app.uploads.models import Document
from app.uploads.schemas import DocumentListQuery


def _documents(*, owner_id: uuid.UUID, titles: list[str]) -> list[Document]:
    return [
        Document(
            owner_guest_id=owner_id,
            title=title,
            original_filename=f"{title.lower().replace(' ', '-')}.pdf",
            content_type="application/pdf",
            file_size=100,
            storage_key=f"documents/{uuid.uuid4()}",
        )
        for title in titles
    ]


def test_document_library_filters_searches_sorts_and_paginates():
    owner_id = uuid.uuid4()
    other_owner_id = uuid.uuid4()

    with SessionLocal() as db:
        owned = _documents(owner_id=owner_id, titles=["Zebra Guide", "Alpha Guide", "Other Notes"])
        other = _documents(owner_id=other_owner_id, titles=["Alpha Guide"])
        db.add_all([*owned, *other])
        db.commit()

        try:
            documents, total = list_documents(
                db,
                identity=Identity(user=None, guest_id=owner_id),
                options=DocumentListQuery(
                    search="guide",
                    file_type="pdf",
                    sort_by="title",
                    sort_order="asc",
                    page=1,
                    page_size=1,
                ),
            )

            assert total == 2
            assert len(documents) == 1
            assert documents[0].title == "Alpha Guide"
            assert page_count(total, 1) == 2
        finally:
            for document in [*owned, *other]:
                db.delete(document)
            db.commit()


def test_document_detail_is_scoped_to_owner():
    owner_id = uuid.uuid4()
    other_owner_id = uuid.uuid4()

    with SessionLocal() as db:
        document = Document(
            owner_guest_id=owner_id,
            original_filename="private.pdf",
            storage_key=f"documents/{uuid.uuid4()}",
        )
        db.add(document)
        db.commit()
        db.refresh(document)

        try:
            assert (
                get_owned_document(
                    db,
                    identity=Identity(user=None, guest_id=owner_id),
                    document_id=document.id,
                )
                is not None
            )
            assert (
                get_owned_document(
                    db,
                    identity=Identity(user=None, guest_id=other_owner_id),
                    document_id=document.id,
                )
                is None
            )
        finally:
            db.delete(document)
            db.commit()
