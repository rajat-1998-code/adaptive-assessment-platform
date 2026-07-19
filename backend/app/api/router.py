from fastapi import APIRouter

from app.core.database import check_db_connection
from app.core.redis_client import check_redis_connection

router = APIRouter()


@router.get("/health", tags=["Health"])
def health_check():
    """
    Liveness check.

    Confirms the API process is running and able to respond to requests.
    Does NOT check database or Redis — see /health/ready for that.
    """
    return {"status": "ok"}


@router.get("/health/ready", tags=["Health"])
def readiness_check():
    """
    Readiness check.

    Confirms the API is not just running, but actually able to reach
    its dependencies (PostgreSQL and Redis). Useful for orchestration
    tools (Docker, Kubernetes) deciding whether to route traffic here.
    """
    db_ok = check_db_connection()
    redis_ok = check_redis_connection()

    return {
        "status": "ok" if (db_ok and redis_ok) else "unavailable",
        "database": "connected" if db_ok else "unreachable",
        "redis": "connected" if redis_ok else "unreachable",
    }