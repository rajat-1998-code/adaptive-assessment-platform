import logging
import time

from fastapi import FastAPI, Request

logger = logging.getLogger(__name__)


def register_middleware(app: FastAPI) -> None:
    """
    Registers custom middleware. Call this once from app/main.py
    during app setup, alongside register_exception_handlers.
    """

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
