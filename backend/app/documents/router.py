"""Document upload routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.documents.service import DocumentValidationError, create_document_from_upload
from app.guest.dependencies import get_current_identity
from app.guest.schemas import Identity
from app.storage.service import StorageError, StorageService, get_storage_service
from app.uploads.schemas import DocumentResponse

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: Annotated[UploadFile, File(...)],
    identity: Identity = Depends(get_current_identity),
    db: Session = Depends(get_db),
    storage: StorageService = Depends(get_storage_service),
) -> DocumentResponse:
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

    return DocumentResponse.model_validate(document)
