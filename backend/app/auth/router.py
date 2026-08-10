"""Authentication API router."""

from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Path,
    Query,
    Request,
    Response,
    status,
)
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse

from app.auth.constants import (
    AUTH_TAG,
    PERMISSION_ASSESSMENTS_CREATE,
    PERMISSION_USERS_MANAGE,
    PERMISSION_USERS_READ,
    ROLE_STUDENT,
)
from app.auth.dependencies import (
    get_current_user,
    get_role_permissions,
    require_permissions,
    require_roles,
)
from app.auth.models import User
from app.auth.oauth import OAuthService, get_oauth_service
from app.auth.schemas import (
    AuthenticatedUser,
    AuthMessageResponse,
    AuthStatusResponse,
    LoginRequest,
    MagicLinkRequest,
    ProtectedResourceMessage,
    RegisterRequest,
    UserAuthorizationSummary,
    UserRoleUpdateRequest,
    UserSummary,
    VerifyEmailRequest,
)
from app.auth.service import (
    authenticate_oauth_user,
    get_auth_status,
    list_users,
    login_user,
    logout_user,
    refresh_session,
    register_user,
    request_magic_link,
    resend_verification_otp,
    update_user_role,
    verify_email_otp,
    verify_magic_link,
)
from app.core.config import settings
from app.core.database import get_db
from app.services.email.service import EmailService, get_email_service

router = APIRouter(prefix=settings.AUTH_PREFIX, tags=[AUTH_TAG])

# Module-level singleton dependencies (avoids calling functions in argument
# defaults, which ruff flags as B008).
_require_student_role = require_roles(ROLE_STUDENT)
_require_assessments_create = require_permissions(PERMISSION_ASSESSMENTS_CREATE)
_require_users_read = require_permissions(PERMISSION_USERS_READ)
_require_users_manage = require_permissions(PERMISSION_USERS_MANAGE)
_user_id_path = Path(
    ...,
    description="The id of the user whose role should be changed",
)
_magic_link_token_query = Query(
    ...,
    min_length=1,
    description="The token from the emailed magic link",
)


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


@router.get(
    "/oauth/{provider}",
    summary="Start a social login redirect flow",
)
async def oauth_authorize_endpoint(
    provider: str,
    request: Request,
    oauth_service: OAuthService = Depends(get_oauth_service),
):
    """Redirect the browser to the selected OAuth provider."""

    return await oauth_service.authorize_redirect(request, provider)


@router.get(
    "/oauth/{provider}/callback",
    response_model=AuthenticatedUser,
    summary="Handle an OAuth provider callback and sign the user in",
)
async def oauth_callback_endpoint(
    provider: str,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    oauth_service: OAuthService = Depends(get_oauth_service),
) -> AuthenticatedUser | RedirectResponse:
    """Complete provider login, then issue the normal application auth cookies."""

    identity = await oauth_service.fetch_identity(request, provider)
    accept_header = request.headers.get("accept", "").lower()
    is_browser_request = "text/html" in accept_header

    callback_response: Response = response
    if is_browser_request:
        callback_response = RedirectResponse(
            url=settings.FRONTEND_BASE_URL,
            status_code=status.HTTP_303_SEE_OTHER,
        )

    authenticated_user = authenticate_oauth_user(
        db,
        identity=identity,
        request=request,
        response=callback_response,
    )

    if is_browser_request:
        return callback_response

    return authenticated_user


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


@router.get(
    "/me",
    response_model=AuthenticatedUser,
    summary="Get the currently authenticated user",
)
def get_me(current_user: User = Depends(get_current_user)) -> AuthenticatedUser:
    """Return the signed-in user's public account profile."""

    return AuthenticatedUser.model_validate(current_user)


@router.get(
    "/me/authorization",
    response_model=UserAuthorizationSummary,
    summary="Get the current user's role and granted permissions",
)
def get_my_authorization(
    current_user: User = Depends(get_current_user),
) -> UserAuthorizationSummary:
    """Expose the effective RBAC role and permission view for the current user."""

    return UserAuthorizationSummary(
        role=current_user.role,
        permissions=sorted(get_role_permissions(current_user.role)),
    )


@router.get(
    "/student/portal",
    response_model=ProtectedResourceMessage,
    summary="Protected portal for student users only",
)
def student_portal(
    current_user: User = Depends(_require_student_role),
) -> ProtectedResourceMessage:
    """Probe route used to validate strict student-only authorization."""

    return ProtectedResourceMessage(
        message="Student portal access granted",
        role=current_user.role,
    )


@router.get(
    "/professional/workspace",
    response_model=ProtectedResourceMessage,
    summary="Protected workspace for professional and admin users",
)
def professional_workspace(
    current_user: User = Depends(_require_assessments_create),
) -> ProtectedResourceMessage:
    """Probe route used to validate professional-level permissions."""

    return ProtectedResourceMessage(
        message="Professional workspace access granted",
        role=current_user.role,
    )


@router.post(
    "/magic-link",
    response_model=AuthMessageResponse,
    summary="Request a passwordless sign-in link by email",
)
def request_magic_link_endpoint(
    payload: MagicLinkRequest,
    request: Request,
    db: Session = Depends(get_db),
    email_service: EmailService = Depends(get_email_service),
) -> AuthMessageResponse:
    """
    Email a one-time sign-in link if the address belongs to an account.

    Always returns the same generic message regardless of whether the
    email is registered, to avoid leaking which addresses have accounts.
    """

    request_magic_link(db, email=payload.email, request=request, email_service=email_service)
    return AuthMessageResponse(
        message="If an account exists for that email, a sign-in link has been sent."
    )


@router.get(
    "/magic-link/verify",
    response_model=AuthenticatedUser,
    summary="Verify a magic link token and sign in",
)
def verify_magic_link_endpoint(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    token: str = _magic_link_token_query,
) -> AuthenticatedUser:
    """Consume a magic link token exactly once and start an authenticated session."""

    return verify_magic_link(db, token=token, request=request, response=response)


@router.get(
    "/admin/users",
    response_model=list[UserSummary],
    summary="List users (admin only)",
)
def admin_list_users(
    _: User = Depends(_require_users_read),
    db: Session = Depends(get_db),
) -> list[UserSummary]:
    """Return a compact list of users for admin management surfaces."""

    return list_users(db)


@router.patch(
    "/admin/users/{user_id}/role",
    response_model=AuthenticatedUser,
    summary="Update a user's role (admin only)",
)
def admin_update_user_role(
    payload: UserRoleUpdateRequest,
    user_id: UUID = _user_id_path,
    _: User = Depends(_require_users_manage),
    db: Session = Depends(get_db),
) -> AuthenticatedUser:
    """Change a user's RBAC role."""

    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return update_user_role(db, user=user, role=payload.role)
