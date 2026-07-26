"""Authentication API router."""

from fastapi import APIRouter

from app.auth.constants import AUTH_TAG
from app.auth.schemas import AuthStatusResponse
from app.auth.service import get_auth_status
from app.core.config import settings

router = APIRouter(prefix=settings.AUTH_PREFIX, tags=[AUTH_TAG])


@router.get("", response_model=AuthStatusResponse, summary="Authentication module status")
def auth_status() -> AuthStatusResponse:
    """
    Foundation endpoint that confirms the authentication package is registered.

    This gives the OpenAPI docs a concrete auth surface now, while later stages
    add registration, login, verification, and session endpoints here.
    """

    return get_auth_status()
