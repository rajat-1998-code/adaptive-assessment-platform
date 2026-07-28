"""Authentication API router."""

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session

from app.auth.constants import AUTH_TAG
from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.auth.schemas import (
    AuthenticatedUser,
    AuthMessageResponse,
    AuthStatusResponse,
    LoginRequest,
    RegisterRequest,
    VerifyEmailRequest,
)
from app.auth.service import (
    get_auth_status,
    login_user,
    logout_user,
    refresh_session,
    register_user,
    resend_verification_otp,
    verify_email_otp,
)
from app.core.config import settings
from app.core.database import get_db
from app.services.email.service import EmailService, get_email_service

router = APIRouter(prefix=settings.AUTH_PREFIX, tags=[AUTH_TAG])


@router.get("", response_model=AuthStatusResponse, summary="Authentication module status")
def auth_status() -> AuthStatusResponse:
    """
    Foundation endpoint that confirms the authentication package is registered.

    This gives the OpenAPI docs a concrete auth surface now, while later stages
    add registration, login, verification, and session endpoints here.
    """

    return get_auth_status()


@router.post(
    "/register",
    response_model=AuthenticatedUser,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new account with email and password",
)
def register(
    payload: RegisterRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    email_service: EmailService = Depends(get_email_service),
) -> AuthenticatedUser:
    """Create a new user, sign them in immediately, and email a verification OTP."""

    return register_user(
        db,
        payload=payload,
        request=request,
        response=response,
        email_service=email_service,
    )


@router.post(
    "/login",
    response_model=AuthenticatedUser,
    summary="Sign in with email and password",
)
def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> AuthenticatedUser:
    """Verify credentials and start a new authenticated session."""

    return login_user(db, payload=payload, request=request, response=response)


@router.post(
    "/refresh",
    response_model=AuthenticatedUser,
    summary="Rotate the refresh token and issue a new access token",
)
def refresh(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> AuthenticatedUser:
    """Exchange a valid refresh cookie for a new access/refresh token pair."""

    return refresh_session(db, request=request, response=response)


@router.post(
    "/logout",
    response_model=AuthMessageResponse,
    summary="Sign out and revoke the current session",
)
def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> AuthMessageResponse:
    """Revoke the current refresh token/session and clear auth cookies."""

    logout_user(db, request=request, response=response)
    return AuthMessageResponse(message="Logged out successfully")


@router.post(
    "/verify-email",
    response_model=AuthenticatedUser,
    summary="Verify a newly registered account with the emailed OTP",
)
def verify_email(
    payload: VerifyEmailRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AuthenticatedUser:
    """Confirm a submitted OTP and mark the current user's email as verified."""

    return verify_email_otp(db, user=current_user, code=payload.code)


@router.post(
    "/resend-otp",
    response_model=AuthMessageResponse,
    summary="Resend the email verification code",
)
def resend_otp(
    current_user: User = Depends(get_current_user),
    email_service: EmailService = Depends(get_email_service),
) -> AuthMessageResponse:
    """Issue and send a fresh OTP to the current (unverified) user."""

    resend_verification_otp(current_user, email_service=email_service)
    return AuthMessageResponse(message="Verification code sent")
