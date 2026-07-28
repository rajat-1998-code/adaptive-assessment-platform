"""Guest session API router."""

from fastapi import APIRouter, Depends

from app.guest.constants import GUEST_TAG
from app.guest.dependencies import get_current_identity
from app.guest.schemas import GuestSessionResponse, Identity

router = APIRouter(prefix="/guest", tags=[GUEST_TAG])


@router.get(
    "/session",
    response_model=GuestSessionResponse,
    summary="Resolve (and bootstrap, if needed) the current guest or user identity",
)
def guest_session(identity: Identity = Depends(get_current_identity)) -> GuestSessionResponse:
    """
    Lets a frontend check who it currently is before making other calls.

    For an already-authenticated caller, returns authenticated=true with
    no guest_id. For anyone else, this is also what mints the guest
    session cookie on first visit if one doesn't exist yet.
    """

    return GuestSessionResponse(
        authenticated=identity.is_authenticated,
        guest_id=identity.guest_id,
    )
