"""Document upload routes."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.documents.service import (
    DocumentValidationError,
    create_document_from_upload,
    get_owned_document,
    list_documents,
    page_count,
)
from app.guest.dependencies import get_current_identity
from app.guest.schemas import Identity
from app.storage.service import StorageError, StorageService, get_storage_service
from app.uploads.schemas import (
    DocumentListQuery,
    DocumentMetadataResponse,
    PaginatedDocumentResponse,
)

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("", response_model=DocumentMetadataResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: Annotated[UploadFile, File(...)],
    identity: Identity = Depends(get_current_identity),
    db: Session = Depends(get_db),
    storage: StorageService = Depends(get_storage_service),
) -> DocumentMetadataResponse:
    """Upload a validated document and persist its metadata."""

    try:
        document = await create_document_from_upload(
            db,
            identity=identity,
            upload=file,
            storage=storage,
        )
    except DocumentValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except StorageError as exc:
        raise HTTPException(status_code=502, detail="Document storage is unavailable") from exc

    return DocumentMetadataResponse.model_validate(document)


@router.get("", response_model=PaginatedDocumentResponse)
def list_document_library(
    options: Annotated[DocumentListQuery, Query()],
    identity: Identity = Depends(get_current_identity),
    db: Session = Depends(get_db),
) -> PaginatedDocumentResponse:
    """List documents owned by the current guest or authenticated user."""

    documents, total = list_documents(db, identity=identity, options=options)
    return PaginatedDocumentResponse(
        items=[DocumentMetadataResponse.model_validate(document) for document in documents],
        page=options.page,
        page_size=options.page_size,
        total=total,
        pages=page_count(total, options.page_size),
    )


@router.get("/{document_id}", response_model=DocumentMetadataResponse)
def get_document_metadata(
    document_id: uuid.UUID,
    identity: Identity = Depends(get_current_identity),
    db: Session = Depends(get_db),
) -> DocumentMetadataResponse:
    """Return metadata only when the document belongs to the current identity."""

    document = get_owned_document(db, identity=identity, document_id=document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentMetadataResponse.model_validate(document)
