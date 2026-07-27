import logging

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.auth.exceptions import AuthError

logger = logging.getLogger(__name__)


def _sanitize_validation_errors(errors: list[dict]) -> list[dict]:
    """
    Make Pydantic's raw error list JSON-safe.

    When a field_validator raises ValueError (e.g. our password strength
    check), Pydantic includes the original exception instance at
    error["ctx"]["error"]. That instance isn't JSON serializable on its
    own, so we stringify it before encoding the rest as usual.
    """

    sanitized = []
    for error in errors:
        cleaned = dict(error)
        ctx = cleaned.get("ctx")
        if isinstance(ctx, dict) and isinstance(ctx.get("error"), Exception):
            cleaned["ctx"] = {**ctx, "error": str(ctx["error"])}
        sanitized.append(cleaned)
    return jsonable_encoder(sanitized)


def register_exception_handlers(app: FastAPI) -> None:
    """
    Registers global exception handlers so errors always return a
    consistent JSON shape, instead of leaking raw tracebacks to clients.

    Call this once from app/main.py during app setup.
    """

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.detail, "path": str(request.url.path)},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "Validation failed",
                "details": _sanitize_validation_errors(exc.errors()),
                "path": str(request.url.path),
            },
        )

    @app.exception_handler(AuthError)
    async def auth_exception_handler(request: Request, exc: AuthError):
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.message, "path": str(request.url.path)},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        # Log the full error server-side for debugging, but never leak
        # internal details (stack traces, exception messages) to the client.
        logger.exception("Unhandled exception on %s", request.url.path)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "Internal server error", "path": str(request.url.path)},
        )
