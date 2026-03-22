"""
JWT Token Blacklist — invalidate tokens on logout.

Layer: Infrastructure (Cache)
Uses Redis SET with TTL matching token expiry.
Falls back to in-memory set when Redis is unavailable.
"""

import logging
from datetime import timedelta
from app.infrastructure.cache.redis_client import get_redis, is_redis_available
from app.core.config import settings

logger = logging.getLogger("smart_inventory.token_blacklist")

# ── In-memory fallback (only for dev without Redis) ────────────────────────
_memory_blacklist: set[str] = set()

# Redis key prefix
_PREFIX = "blacklist:"


def blacklist_token(token: str, expires_in_minutes: int = None) -> None:
    """
    Add a JWT to the blacklist.

    Args:
        token: The JWT string to blacklist
        expires_in_minutes: TTL for the blacklist entry (defaults to access token expiry)
    """
    if expires_in_minutes is None:
        expires_in_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES

    r = get_redis()
    if r and is_redis_available():
        try:
            r.setex(
                f"{_PREFIX}{token}",
                timedelta(minutes=expires_in_minutes),
                "1",
            )
            return
        except Exception as e:
            logger.warning("Redis blacklist write failed: %s", e)

    # Fallback to in-memory
    _memory_blacklist.add(token)
    logger.debug("Token blacklisted (in-memory fallback)")


def is_token_blacklisted(token: str) -> bool:
    """Check if a JWT has been blacklisted (logged out)."""
    r = get_redis()
    if r and is_redis_available():
        try:
            return r.exists(f"{_PREFIX}{token}") > 0
        except Exception as e:
            logger.warning("Redis blacklist read failed: %s", e)

    # Fallback to in-memory
    return token in _memory_blacklist


def blacklist_refresh_token(token: str) -> None:
    """Blacklist a refresh token (longer TTL)."""
    blacklist_token(token, expires_in_minutes=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60)
