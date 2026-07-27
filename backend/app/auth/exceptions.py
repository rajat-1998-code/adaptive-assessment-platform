"""Authentication-specific exceptions."""

from fastapi import status


class AuthError(Exception):
    """Base exception for authentication module errors."""

    def __init__(self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class AuthenticationRequiredError(AuthError):
    """Raised when an authenticated user is required."""

    def __init__(self, message: str = "Authentication required"):
        super().__init__(message, status.HTTP_401_UNAUTHORIZED)


class AuthConfigurationError(AuthError):
    """Raised when auth configuration is missing or invalid."""

    def __init__(self, message: str = "Authentication configuration is invalid"):
        super().__init__(message, status.HTTP_500_INTERNAL_SERVER_ERROR)


class InvalidTokenError(AuthError):
    """Raised when a JWT is missing, invalid, or expired."""

    def __init__(self, message: str = "Invalid authentication token"):
        super().__init__(message, status.HTTP_401_UNAUTHORIZED)


class DuplicateEmailError(AuthError):
    """Raised when registering with an email that is already in use."""

    def __init__(self, message: str = "An account with this email already exists"):
        super().__init__(message, status.HTTP_409_CONFLICT)


class InvalidCredentialsError(AuthError):
    """Raised when login credentials do not match a known, active account."""

    def __init__(self, message: str = "Invalid email or password"):
        super().__init__(message, status.HTTP_401_UNAUTHORIZED)


class InactiveAccountError(AuthError):
    """Raised when a valid credential check succeeds but the account is disabled."""

    def __init__(self, message: str = "This account has been deactivated"):
        super().__init__(message, status.HTTP_403_FORBIDDEN)
