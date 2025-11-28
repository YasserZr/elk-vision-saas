"""
Redis connection and caching utilities
"""

import json
import logging
from typing import Any, Optional

import redis
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

# Global Redis client for direct operations
_redis_client: Optional[redis.Redis] = None


def get_redis_client() -> redis.Redis:
    """
    Get or create Redis client for direct operations

    Returns:
        redis.Redis: Redis client instance
    """
    global _redis_client

    if _redis_client is None:
        _redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=2,  # Use DB 2 for application cache (0: Celery, 1: Django cache)
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
        )
        try:
            _redis_client.ping()
            logger.info(
                f"Connected to Redis: {settings.REDIS_HOST}:{settings.REDIS_PORT}"
            )
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    return _redis_client


def health_check_redis() -> dict:
    """
    Check Redis connection health

    Returns:
        dict: Health status
    """
    try:
        client = get_redis_client()
        response = client.ping()

        info = client.info("memory")

        return {
            "status": "healthy",
            "connected": True,
            "used_memory_human": info.get("used_memory_human"),
            "connected_clients": info.get("connected_clients"),
        }
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return {"status": "unhealthy", "connected": False, "error": str(e)}


# Session Cache Utilities
class SessionCache:
    """Utility class for session caching operations"""

    @staticmethod
    def set_user_session(user_id: int, session_data: dict, ttl: int = 3600):
        """
        Cache user session data

        Args:
            user_id: User ID
            session_data: Session data to cache
            ttl: Time to live in seconds (default 1 hour)
        """
        cache_key = f"session:user:{user_id}"
        cache.set(cache_key, session_data, timeout=ttl)
        logger.debug(f"Cached session for user {user_id}")

    @staticmethod
    def get_user_session(user_id: int) -> Optional[dict]:
        """
        Get cached user session

        Args:
            user_id: User ID

        Returns:
            dict: Session data or None
        """
        cache_key = f"session:user:{user_id}"
        return cache.get(cache_key)

    @staticmethod
    def delete_user_session(user_id: int):
        """
        Delete user session from cache

        Args:
            user_id: User ID
        """
        cache_key = f"session:user:{user_id}"
        cache.delete(cache_key)
        logger.debug(f"Deleted session for user {user_id}")

    @staticmethod
    def set_jwt_blacklist(token: str, ttl: int = 3600):
        """
        Blacklist a JWT token

        Args:
            token: JWT token to blacklist
            ttl: Time to live (should match token expiry)
        """
        cache_key = f"jwt:blacklist:{token}"
        cache.set(cache_key, True, timeout=ttl)
        logger.debug("JWT token blacklisted")

    @staticmethod
    def is_jwt_blacklisted(token: str) -> bool:
        """
        Check if JWT token is blacklisted

        Args:
            token: JWT token to check

        Returns:
            bool: True if blacklisted
        """
        cache_key = f"jwt:blacklist:{token}"
        return cache.get(cache_key, False)


# Query Result Cache
class QueryCache:
    """Utility class for caching query results"""

    @staticmethod
    def set(key: str, data: Any, ttl: int = 300):
        """
        Cache query result

        Args:
            key: Cache key
            data: Data to cache
            ttl: Time to live in seconds (default 5 minutes)
        """
        cache_key = f"query:{key}"
        cache.set(cache_key, data, timeout=ttl)

    @staticmethod
    def get(key: str) -> Optional[Any]:
        """
        Get cached query result

        Args:
            key: Cache key

        Returns:
            Cached data or None
        """
        cache_key = f"query:{key}"
        return cache.get(cache_key)

    @staticmethod
    def delete(key: str):
        """
        Delete cached query result

        Args:
            key: Cache key
        """
        cache_key = f"query:{key}"
        cache.delete(cache_key)

    @staticmethod
    def invalidate_pattern(pattern: str):
        """
        Invalidate all cache keys matching pattern

        Args:
            pattern: Pattern to match (e.g., "user:123:*")
        """
        client = get_redis_client()
        keys = client.keys(f"query:{pattern}")
        if keys:
            client.delete(*keys)
            logger.debug(f"Invalidated {len(keys)} cache keys matching {pattern}")


# Rate Limiting
class RateLimiter:
    """Redis-based rate limiter"""

    @staticmethod
    def is_allowed(key: str, max_requests: int, window: int) -> bool:
        """
        Check if request is allowed under rate limit

        Args:
            key: Rate limit key (e.g., "api:user:123")
            max_requests: Maximum requests allowed
            window: Time window in seconds

        Returns:
            bool: True if allowed, False if rate limited
        """
        client = get_redis_client()
        cache_key = f"ratelimit:{key}"

        try:
            current = client.incr(cache_key)

            if current == 1:
                # First request, set expiry
                client.expire(cache_key, window)

            return current <= max_requests

        except Exception as e:
            logger.error(f"Rate limiter error: {e}")
            # On error, allow request (fail open)
            return True

    @staticmethod
    def get_remaining(key: str, max_requests: int) -> int:
        """
        Get remaining requests in current window

        Args:
            key: Rate limit key
            max_requests: Maximum requests allowed

        Returns:
            int: Remaining requests
        """
        client = get_redis_client()
        cache_key = f"ratelimit:{key}"

        current = int(client.get(cache_key) or 0)
        return max(0, max_requests - current)


# Distributed Lock
class DistributedLock:
    """Redis-based distributed lock"""

    def __init__(self, lock_key: str, timeout: int = 10):
        """
        Initialize distributed lock

        Args:
            lock_key: Lock key
            timeout: Lock timeout in seconds
        """
        self.lock_key = f"lock:{lock_key}"
        self.timeout = timeout
        self.client = get_redis_client()

    def acquire(self) -> bool:
        """
        Acquire lock

        Returns:
            bool: True if acquired, False if locked by another process
        """
        return self.client.set(self.lock_key, "locked", nx=True, ex=self.timeout)

    def release(self):
        """Release lock"""
        self.client.delete(self.lock_key)

    def __enter__(self):
        """Context manager entry"""
        if not self.acquire():
            raise RuntimeError(f"Could not acquire lock: {self.lock_key}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.release()


# Cache decorators
def cache_result(ttl: int = 300):
    """
    Decorator to cache function results

    Args:
        ttl: Time to live in seconds
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"

            # Try to get from cache
            result = QueryCache.get(cache_key)
            if result is not None:
                logger.debug(f"Cache hit: {cache_key}")
                return result

            # Execute function and cache result
            result = func(*args, **kwargs)
            QueryCache.set(cache_key, result, ttl=ttl)
            logger.debug(f"Cache miss: {cache_key}")

            return result

        return wrapper

    return decorator
