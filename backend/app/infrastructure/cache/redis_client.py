"""
Redis client — singleton connection with graceful fallback.

Layer: Infrastructure
When Redis is unavailable, the app continues without caching.
All consumers check `is_available` before use.
"""

import logging
import redis
from app.core.config import settings

logger = logging.getLogger("smart_inventory.redis")

_redis_client: redis.Redis | None = None
_redis_available: bool = False


def get_redis() -> redis.Redis | None:
    """Get the singleton Redis client. Returns None if unavailable."""
    global _redis_client, _redis_available

    if _redis_client is not None:
        return _redis_client if _redis_available else None

    if not settings.REDIS_URL:
        logger.info("REDIS_URL not set — running without Redis (in-memory fallback)")
        _redis_available = False
        return None

    try:
        _redis_client = redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=3,
            socket_timeout=3,
            retry_on_timeout=True,
        )
        _redis_client.ping()
        _redis_available = True
        logger.info("Redis connected: %s", settings.REDIS_URL.split("@")[-1] if "@" in settings.REDIS_URL else settings.REDIS_URL)
        return _redis_client
    except Exception as e:
        logger.warning("Redis connection failed — running without cache: %s", e)
        _redis_available = False
        _redis_client = None
        return None


def is_redis_available() -> bool:
    """Check if Redis is connected and healthy."""
    global _redis_available
    if _redis_available and _redis_client:
        try:
            _redis_client.ping()
            return True
        except Exception:
            _redis_available = False
    return False


def close_redis() -> None:
    """Graceful shutdown — close Redis connection."""
    global _redis_client, _redis_available
    if _redis_client:
        try:
            _redis_client.close()
            logger.info("Redis connection closed")
        except Exception:
            pass
    _redis_client = None
    _redis_available = False
