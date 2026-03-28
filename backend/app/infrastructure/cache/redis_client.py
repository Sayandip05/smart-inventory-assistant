"""
Redis client — connection pool with graceful fallback.

Layer: Infrastructure
Uses a connection pool (max 20 connections) for efficient reuse.
When Redis is unavailable the app continues without caching — all callers
check is_redis_available() or receive None from get_redis().

Key namespaces used by this app:
  cache:*       → analytics / dashboard response cache (TTL 2-5 min)
  blacklist:*   → JWT token blacklist (TTL = token expiry)
  lockout:*     → login attempt counters (TTL = lockout window)
  ratelimit:*   → managed by slowapi automatically
"""

import logging
import redis
from redis import ConnectionPool
from typing import Any, Optional
import json

from app.core.config import settings

logger = logging.getLogger("smart_inventory.redis")

_pool: ConnectionPool | None = None
_redis_client: redis.Redis | None = None
_redis_available: bool = False


def _safe_url_log(url: str) -> str:
    """Mask password in Redis URL for safe logging."""
    if "@" in url:
        return "redis://***@" + url.split("@")[-1]
    return url


def _build_pool() -> ConnectionPool:
    """Build a Redis connection pool with sensible production defaults."""
    return redis.ConnectionPool.from_url(
        settings.REDIS_URL,
        max_connections=20,
        decode_responses=True,
        socket_connect_timeout=3,
        socket_timeout=3,
        retry_on_timeout=True,
        health_check_interval=30,   # background ping every 30s
    )


def get_redis() -> redis.Redis | None:
    """
    Get the singleton Redis client backed by a connection pool.
    Returns None if Redis is unavailable or not configured.
    """
    global _pool, _redis_client, _redis_available

    if _redis_client is not None:
        return _redis_client if _redis_available else None

    if not settings.REDIS_URL:
        logger.info("REDIS_URL not set — running without Redis (in-memory fallback active)")
        _redis_available = False
        return None

    try:
        _pool = _build_pool()
        _redis_client = redis.Redis(connection_pool=_pool)
        _redis_client.ping()
        _redis_available = True
        logger.info("Redis connected via pool → %s", _safe_url_log(settings.REDIS_URL))
        return _redis_client
    except Exception as e:
        logger.warning("Redis connection failed — running without cache: %s", e)
        _redis_available = False
        _redis_client = None
        return None


def is_redis_available() -> bool:
    """Ping Redis to confirm it's still healthy."""
    global _redis_available
    if _redis_available and _redis_client:
        try:
            _redis_client.ping()
            return True
        except Exception:
            _redis_available = False
            logger.warning("Redis health check failed — marking unavailable")
    return False


def close_redis() -> None:
    """Graceful shutdown — disconnect all pool connections."""
    global _pool, _redis_client, _redis_available
    if _pool:
        try:
            _pool.disconnect()
            logger.info("Redis connection pool closed")
        except Exception:
            pass
    _pool = None
    _redis_client = None
    _redis_available = False


# ── Typed helpers (used by cache_service, token_blacklist, login_attempts) ─

def redis_get_json(key: str) -> Optional[Any]:
    """Get a JSON-deserialized value from Redis. Returns None on any failure."""
    r = get_redis()
    if not r:
        return None
    try:
        raw = r.get(key)
        return json.loads(raw) if raw is not None else None
    except Exception as e:
        logger.debug("redis_get_json failed key=%s: %s", key, e)
        return None


def redis_set_json(key: str, value: Any, ttl_seconds: int) -> bool:
    """Set a JSON-serialized value with TTL. Returns True on success."""
    r = get_redis()
    if not r:
        return False
    try:
        r.setex(key, ttl_seconds, json.dumps(value, default=str))
        return True
    except Exception as e:
        logger.debug("redis_set_json failed key=%s: %s", key, e)
        return False


def redis_delete(key: str) -> bool:
    """Delete a key. Returns True on success."""
    r = get_redis()
    if not r:
        return False
    try:
        r.delete(key)
        return True
    except Exception as e:
        logger.debug("redis_delete failed key=%s: %s", key, e)
        return False


def redis_increment(key: str, ttl_seconds: int) -> int:
    """
    Atomic increment with TTL (used for login attempt counters).
    Sets TTL only on first creation. Returns new count.
    """
    r = get_redis()
    if not r:
        return 0
    try:
        pipe = r.pipeline()
        pipe.incr(key)
        pipe.expire(key, ttl_seconds, nx=True)   # nx=True: only set if not already set
        results = pipe.execute()
        return results[0]
    except Exception as e:
        logger.debug("redis_increment failed key=%s: %s", key, e)
        return 0


def redis_get_int(key: str) -> int:
    """Get an integer counter value. Returns 0 if missing or unavailable."""
    r = get_redis()
    if not r:
        return 0
    try:
        val = r.get(key)
        return int(val) if val is not None else 0
    except Exception as e:
        logger.debug("redis_get_int failed key=%s: %s", key, e)
        return 0
