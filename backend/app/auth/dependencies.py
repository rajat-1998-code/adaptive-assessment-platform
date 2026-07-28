"""FastAPI dependencies for authentication."""

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.auth.exceptions import AuthenticationRequiredError
from app.auth.models import User
from app.auth.utils import build_auth_cookie_names, decode_jwt_token
from app.core.database import get_db


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """
    Resolve the authenticated user from the access token cookie.

    Raises AuthenticationRequiredError if the cookie is missing or the
    token is invalid/expired (decode_jwt_token raises InvalidTokenError,
    which is also a 401, in that case), or if the user no longer exists
    or has been deactivated since the token was issued.
    """

    cookie_names = build_auth_cookie_names()
    access_token = request.cookies.get(cookie_names["access_token"])

    if not access_token:
        raise AuthenticationRequiredError()

    payload = decode_jwt_token(access_token, expected_token_type="access")

    user = db.get(User, payload.user_id)
    if user is None or not user.is_active:
        raise AuthenticationRequiredError()

    return user
