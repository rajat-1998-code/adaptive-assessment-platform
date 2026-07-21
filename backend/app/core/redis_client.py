import logging

import redis

from app.core.config import settings

logger = logging.getLogger(__name__)

redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)


def check_redis_connection() -> bool:
    """
    Used by the readiness health check to confirm Redis is actually
    reachable, not just configured.
    """
    try:
        redis_client.ping()
        return True
    except Exception as exc:
        logger.error("Redis connection check failed: %s", exc)
        return False
