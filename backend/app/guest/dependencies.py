"""FastAPI dependencies for resolving the current request's identity."""

from fastapi import Depends, Request, Response
from sqlalchemy.orm import Session

from app.auth.exceptions import InvalidTokenError
from app.auth.models import User
from app.auth.utils import build_auth_cookie_names, decode_jwt_token
from app.core.database import get_db
from app.guest.schemas import Identity
from app.guest.service import get_or_create_guest_id


def get_current_identity(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> Identity:
    """
    Resolve "who is making this request" without requiring login.

    If a valid access token cookie is present, resolves to the
    authenticated user. Otherwise (including a missing, expired, or
    otherwise invalid access token — this dependency never raises 401,
    unlike get_current_user) falls back to a guest identity, minting a
    fresh guest session/cookie if one doesn't already exist.
    """

    cookie_names = build_auth_cookie_names()
    access_token = request.cookies.get(cookie_names["access_token"])

    if access_token:
        try:
            payload = decode_jwt_token(access_token, expected_token_type="access")
        except InvalidTokenError:
            payload = None

        if payload is not None:
            user = db.get(User, payload.user_id)
            if user is not None and user.is_active:
                return Identity(user=user, guest_id=None)

    guest_id = get_or_create_guest_id(request, response)
    return Identity(user=None, guest_id=guest_id)
