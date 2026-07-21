import logging
import sys

from app.core.config import settings


def setup_logging() -> None:
    """
    Configure application-wide logging.

    Call this once at application startup (see app/main.py). All modules
    should retrieve their logger via `logging.getLogger(__name__)` rather
    than configuring their own handlers.
    """
    log_level = logging.DEBUG if settings.DEBUG else logging.INFO

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    # Quiet down noisy third-party loggers unless we're debugging
    if not settings.DEBUG:
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
