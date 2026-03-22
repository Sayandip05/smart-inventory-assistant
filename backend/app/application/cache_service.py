"""
Cache Service — generic caching for expensive queries (analytics, dashboard).

Layer: Application
Uses Redis with JSON serialization. Falls back to no-cache when unavailable.
"""

import json
import logging
from typing import Any, Optional
from app.infrastructure.cache.redis_client import get_redis, is_redis_available

logger = logging.getLogger("smart_inventory.cache")

# Default TTL in seconds
DEFAULT_TTL = 300  # 5 minutes
ANALYTICS_TTL = 300  # 5 minutes — analytics data doesn't change frequently
DASHBOARD_TTL = 120  # 2 minutes — dashboard stats slightly more fresh

# Key prefix
_PREFIX = "cache:"


def cache_get(key: str) -> Optional[Any]:
    """
    Retrieve a cached value by key.

    Returns:
        Deserialized value, or None if not found / Redis unavailable
    """
    r = get_redis()
    if not r or not is_redis_available():
        return None

    try:
        raw = r.get(f"{_PREFIX}{key}")
        if raw is None:
            return None
        return json.loads(raw)
    except Exception as e:
        logger.warning("Cache read failed for key=%s: %s", key, e)
        return None


def cache_set(key: str, value: Any, ttl: int = DEFAULT_TTL) -> None:
    """
    Store a value in cache with TTL.

    Args:
        key: Cache key
        value: JSON-serializable value
        ttl: Time-to-live in seconds (default 5 min)
    """
    r = get_redis()
    if not r or not is_redis_available():
        return

    try:
        r.setex(f"{_PREFIX}{key}", ttl, json.dumps(value, default=str))
    except Exception as e:
        logger.warning("Cache write failed for key=%s: %s", key, e)


def cache_delete(key: str) -> None:
    """Delete a specific cache entry."""
    r = get_redis()
    if not r or not is_redis_available():
        return

    try:
        r.delete(f"{_PREFIX}{key}")
    except Exception as e:
        logger.warning("Cache delete failed for key=%s: %s", key, e)


def cache_invalidate_pattern(pattern: str) -> None:
    """
    Invalidate all cache keys matching a pattern.

    Args:
        pattern: Glob pattern (e.g., "analytics:*")
    """
    r = get_redis()
    if not r or not is_redis_available():
        return

    try:
        keys = r.keys(f"{_PREFIX}{pattern}")
        if keys:
            r.delete(*keys)
            logger.debug("Invalidated %d cache keys matching '%s'", len(keys), pattern)
    except Exception as e:
        logger.warning("Cache invalidation failed for pattern=%s: %s", pattern, e)
