"""
backend/app/core/redis.py
─────────────────────────
Redis connection pool, caching utilities, and JWT blacklist manager.
"""

import redis

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Initialize connection pool
try:
    redis_pool = redis.ConnectionPool.from_url(
        settings.redis_url, max_connections=20, decode_responses=True
    )
    redis_client = redis.Redis(connection_pool=redis_pool)
except Exception as exc:
    logger.error(f"Failed to connect to Redis pool: {exc}")
    redis_client = None


def get_redis():
    """Return the global Redis client instance."""
    return redis_client


def cache_get(key: str) -> str | None:
    """Retrieve string value from Redis cache."""
    if not redis_client:
        return None
    try:
        return redis_client.get(key)
    except Exception as exc:
        logger.warning(f"Redis cache get error for key '{key}': {exc}")
        return None


def cache_set(key: str, value: str, ttl: int = 3600) -> bool:
    """Store string value in Redis cache with custom TTL."""
    if not redis_client:
        return False
    try:
        return bool(redis_client.setex(key, ttl, value))
    except Exception as exc:
        logger.warning(f"Redis cache set error for key '{key}': {exc}")
        return False


def cache_delete(key: str) -> bool:
    """Delete a key from Redis cache."""
    if not redis_client:
        return False
    try:
        return bool(redis_client.delete(key))
    except Exception as exc:
        logger.warning(f"Redis cache delete error for key '{key}': {exc}")
        return False


# ── JWT Blacklisting ──────────────────────────────────────────────────────────


def blacklist_token(token: str, expires_in_seconds: int) -> bool:
    """Blacklist a JWT token upon user logout."""
    if not redis_client:
        return False
    try:
        key = f"jwt_blacklist:{token}"
        return bool(redis_client.setex(key, expires_in_seconds, "true"))
    except Exception as exc:
        logger.warning(f"Failed to blacklist token: {exc}")
        return False


def is_token_blacklisted(token: str) -> bool:
    """Check if a JWT token has been blacklisted."""
    if not redis_client:
        return False
    try:
        key = f"jwt_blacklist:{token}"
        return bool(redis_client.exists(key))
    except Exception as exc:
        logger.warning(f"Failed to check token blacklist: {exc}")
        return False
