"""Constants shared across authentication components."""

AUTH_TAG = "Authentication"

ACCESS_TOKEN_COOKIE_NAME = "adaptive_access_token"
REFRESH_TOKEN_COOKIE_NAME = "adaptive_refresh_token"
GUEST_SESSION_COOKIE_NAME = "adaptive_guest_session"

ROLE_STUDENT = "student"
ROLE_INSTRUCTOR = "instructor"
ROLE_REVIEWER = "reviewer"
ROLE_ADMIN = "admin"

SUPPORTED_ROLES = (
    ROLE_STUDENT,
    ROLE_INSTRUCTOR,
    ROLE_REVIEWER,
    ROLE_ADMIN,
)
