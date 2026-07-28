"""Uploads API router."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.guest.dependencies import get_current_identity
from app.guest.schemas import Identity
from app.uploads.schemas import CreateUploadRequest, UploadResponse
from app.uploads.service import create_upload_record, list_upload_records

router = APIRouter(prefix="/uploads", tags=["Uploads"])


@router.post(
    "",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an upload (works for guests and signed-in users)",
)
def create_upload(
    payload: CreateUploadRequest,
    identity: Identity = Depends(get_current_identity),
    db: Session = Depends(get_db),
) -> UploadResponse:
    """
    Records an upload owned by the caller's current identity.

    Anonymous callers are assigned a guest session automatically (see
    app.guest) — no login required. Those uploads later transfer to the
    caller's account the moment they register, log in, or use a magic
    link, via app.uploads.service.migrate_guest_uploads_to_user.
    """

    return create_upload_record(db, identity=identity, payload=payload)


@router.get(
    "",
    response_model=list[UploadResponse],
    summary="List uploads owned by the current guest or user",
)
def list_uploads(
    identity: Identity = Depends(get_current_identity),
    db: Session = Depends(get_db),
) -> list[UploadResponse]:
    return list_upload_records(db, identity=identity)
