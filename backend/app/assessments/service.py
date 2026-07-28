"""Service layer for the assessments module (ownership migration only, for now)."""

from __future__ import annotations

import uuid

from sqlalchemy import update
from sqlalchemy.orm import Session

from app.assessments.models import Assessment


def migrate_guest_assessments_to_user(
    db: Session, *, guest_id: uuid.UUID, user_id: uuid.UUID
) -> int:
    """
    Reassign every assessment owned by a guest session to a newly
    authenticated user. Mirrors app.uploads.service.migrate_guest_uploads_to_user.
    """

    result = db.execute(
        update(Assessment)
        .where(Assessment.owner_guest_id == guest_id)
        .values(owner_guest_id=None, owner_user_id=user_id)
    )
    return result.rowcount
