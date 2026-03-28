"""
Cache Service — generic Redis caching for expensive queries.

Layer: Application

Features:
  - cache_get / cache_set / cache_delete / cache_invalidate_pattern
  - @cached(key, ttl) decorator for clean endpoint caching
  - SCAN-based key iteration (production-safe, non-blocking unlike KEYS)
  - User-scoped caching support via key suffixes

TTL reference:
  DASHBOARD_TTL   = 120s  (2 min)   — stats shown on dashboard
  ANALYTICS_TTL   = 300s  (5 min)   — deeper analytics queries
  REALTIME_TTL    = 30s   (30 sec)  — near-realtime feeds
"""

import json
import logging
import functools
from typing import Any, Optional, Callable
from app.infrastructure.cache.redis_client import get_redis

logger = logging.getLogger("smart_inventory.cache")

# ── TTL constants ─────────────────────────────────────────────────────────
DASHBOARD_TTL  = 120   # 2 minutes
ANALYTICS_TTL  = 300   # 5 minutes
REALTIME_TTL   = 30    # 30 seconds
DEFAULT_TTL    = 300

# Key prefix — separates our app keys from slowapi rate-limit keys in Redis
_PREFIX = "cache:"


# ── Core primitives ───────────────────────────────────────────────────────

def cache_get(key: str) -> Optional[Any]:
    """
    Retrieve a cached value by key.

    Returns deserialized value, or None if not found / Redis unavailable.
    """
    r = get_redis()
    if not r:
        return None
    try:
        raw = r.get(f"{_PREFIX}{key}")
        return json.loads(raw) if raw is not None else None
    except Exception as e:
        logger.warning("cache_get failed key=%s: %s", key, e)
        return None


def cache_set(key: str, value: Any, ttl: int = DEFAULT_TTL) -> bool:
    """
    Store a JSON-serializable value with TTL.

    Returns True on success, False if Redis unavailable.
    """
    r = get_redis()
    if not r:
        return False
    try:
        r.setex(f"{_PREFIX}{key}", ttl, json.dumps(value, default=str))
        return True
    except Exception as e:
        logger.warning("cache_set failed key=%s: %s", key, e)
        return False


def cache_delete(key: str) -> None:
    """Delete a specific cache entry."""
    r = get_redis()
    if not r:
        return
    try:
        r.delete(f"{_PREFIX}{key}")
    except Exception as e:
        logger.warning("cache_delete failed key=%s: %s", key, e)


def cache_invalidate_pattern(pattern: str) -> int:
    """
    Invalidate all cache keys matching a glob pattern.

    Uses SCAN (not KEYS) — safe for large Redis keyspaces in production.
    Returns the number of keys deleted.

    Example:
        cache_invalidate_pattern("analytics:*")
    """
    r = get_redis()
    if not r:
        return 0

    try:
        full_pattern = f"{_PREFIX}{pattern}"
        deleted = 0
        cursor = 0
        while True:
            cursor, keys = r.scan(cursor=cursor, match=full_pattern, count=100)
            if keys:
                r.delete(*keys)
                deleted += len(keys)
            if cursor == 0:
                break
        if deleted:
            logger.debug("Cache invalidated %d keys matching '%s'", deleted, pattern)
        return deleted
    except Exception as e:
        logger.warning("cache_invalidate_pattern failed pattern=%s: %s", pattern, e)
        return 0


# ── @cached decorator ─────────────────────────────────────────────────────

def cached(key: str, ttl: int = DEFAULT_TTL):
    """
    Decorator to cache a function's return value in Redis.

    Usage:
        @cached("analytics:dashboard_stats", ttl=DASHBOARD_TTL)
        def get_dashboard_stats(db):
            ...

    The decorated function is called only on cache miss.
    Result must be JSON-serializable.
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            cached_value = cache_get(key)
            if cached_value is not None:
                logger.debug("Cache HIT key=%s", key)
                return cached_value

            logger.debug("Cache MISS key=%s — calling function", key)
            result = func(*args, **kwargs)
            cache_set(key, result, ttl)
            return result
        return wrapper
    return decorator
