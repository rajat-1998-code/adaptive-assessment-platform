import logging
import time

from fastapi import FastAPI, Request
from starlette.middleware.sessions import SessionMiddleware

from app.core.config import settings

logger = logging.getLogger(__name__)


def register_middleware(app: FastAPI) -> None:
    """
    Registers custom middleware. Call this once from app/main.py
    during app setup, alongside register_exception_handlers.
    """

    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.AUTH_SESSION_SECRET_KEY.get_secret_value(),
        same_site=settings.AUTH_COOKIE_SAMESITE,
        https_only=settings.AUTH_COOKIE_SECURE,
    )

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start_time = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start_time) * 1000

        logger.info(
            "%s %s -> %s (%.1fms)",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        return response
