"""Schemas for the guest session module."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from pydantic import BaseModel

from app.auth.models import User


@dataclass(slots=True)
class Identity:
    """
    Represents "who is making this request" — exactly one of the two
    fields is set. Routes that should work for both guests and signed-in
    users (like uploads) depend on this instead of requiring a full login.
    """

    user: User | None
    guest_id: uuid.UUID | None

    @property
    def is_authenticated(self) -> bool:
        return self.user is not None


class GuestSessionResponse(BaseModel):
    """Public response for GET /guest/session."""

    authenticated: bool
    guest_id: uuid.UUID | None
