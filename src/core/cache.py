"""
Redis-backed distributed caching for rate limiting and AI response caching.
Provides fallback to in-memory when Redis is unavailable.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass

from src.core.config import settings

logger = logging.getLogger(__name__)

# Try to import redis, but don't fail if not available
try:
    import redis.asyncio as redis

    REDIS_AVAILABLE = True
except ImportError:
    redis = None
    REDIS_AVAILABLE = False
    logger.warning("Redis library not installed. Falling back to in-memory caching.")


# Global Redis connection pool
_redis_pool: Optional[redis.ConnectionPool] = None


# ==================== Data Classes ====================


@dataclass
class CachedResponse:
    """Cached AI response."""

    content: str
    tokens_used: int
    cached: bool = True
    provider: str = "cache"
    model: str = "cache"
    duration_ms: int = 0


# ==================== In-Memory Implementations ====================


class InMemoryRateLimiter:
    """In-memory rate limiter with sliding window algorithm."""

    def __init__(self, requests: int, window_seconds: int):
        self.requests = requests
        self.window_seconds = window_seconds
        self._store: Dict[str, list[datetime]] = {}

    async def is_allowed(self, key: str) -> Tuple[bool, int]:
        """
        Check if request is allowed.
        Returns: (is_allowed, retry_after_seconds)
        """
        now = datetime.utcnow()

        # Clean old entries
        if key in self._store:
            self._store[key] = [
                t
                for t in self._store[key]
                if (now - t).total_seconds() < self.window_seconds
            ]
        else:
            self._store[key] = []

        # Check limit
        if len(self._store[key]) >= self.requests:
            oldest = min(self._store[key])
            retry_after = int(self.window_seconds - (now - oldest).total_seconds())
            return False, max(1, retry_after)

        # Record request
        self._store[key].append(now)
        return True, 0

    async def get_remaining(self, key: str) -> int:
        """Get remaining requests for a key."""
        if key not in self._store:
            return self.requests

        now = datetime.utcnow()
        valid_requests = [
            t
            for t in self._store[key]
            if (now - t).total_seconds() < self.window_seconds
        ]
        return max(0, self.requests - len(valid_requests))

    async def reset(self, key: str) -> None:
        """Reset rate limit for a key."""
        if key in self._store:
            del self._store[key]


class InMemoryAnalysisCache:
    """In-memory cache for AI responses."""

    def __init__(self, ttl_seconds: int = 3600):
        self.cache: Dict[str, Tuple[str, datetime, int]] = {}
        self.ttl_seconds = ttl_seconds

    async def get(self, key: str) -> Optional[CachedResponse]:
        """Get cached response."""
        if key in self.cache:
            content, timestamp, tokens = self.cache[key]
            if (datetime.utcnow() - timestamp).total_seconds() < self.ttl_seconds:
                return CachedResponse(
                    content=content,
                    tokens_used=tokens,
                )
            else:
                del self.cache[key]
        return None

    async def set(self, key: str, content: str, tokens: int) -> None:
        """Cache a response."""
        self.cache[key] = (content, datetime.utcnow(), tokens)

    async def clear(self) -> None:
        """Clear cache."""
        self.cache.clear()


# ==================== Redis-Backed Implementations ====================


class RedisRateLimiter:
    """Redis-backed distributed rate limiter with sliding window."""

    def __init__(
        self,
        redis_client: Optional[redis.Redis],
        requests: int,
        window_seconds: int,
        fallback_to_memory: bool = True,
    ):
        self.redis_client = redis_client
        self.requests = requests
        self.window_seconds = window_seconds
        self.fallback_to_memory = fallback_to_memory
        self._using_fallback = False

        # Create fallback if needed
        if redis_client is None and fallback_to_memory:
            self._fallback = InMemoryRateLimiter(requests, window_seconds)
            self._using_fallback = True
            logger.info("Using in-memory rate limiter as fallback")
        else:
            self._fallback = None

    async def is_allowed(self, key: str) -> Tuple[bool, int]:
        """
        Check if request is allowed using Redis sliding window.
        Returns: (is_allowed, retry_after_seconds)
        """
        if self._using_fallback and self._fallback:
            return await self._fallback.is_allowed(key)

        if not self.redis_client:
            if self.fallback_to_memory:
                self._fallback = InMemoryRateLimiter(self.requests, self.window_seconds)
                self._using_fallback = True
                return await self._fallback.is_allowed(key)
            raise RuntimeError("Redis client not available and fallback disabled")

        try:
            redis_key = f"ratelimit:{key}"

            # Use Redis INCR to atomically increment counter
            count = await self.redis_client.incr(redis_key)

            # Set expiry on first request
            if count == 1:
                await self.redis_client.expire(redis_key, self.window_seconds)

            # Check if over limit
            if count > self.requests:
                # Get TTL for retry_after
                ttl = await self.redis_client.ttl(redis_key)
                return False, max(1, ttl)

            return True, 0

        except Exception as e:
            logger.error(f"Redis error in rate limiter: {e}")
            if self.fallback_to_memory:
                if not self._fallback:
                    self._fallback = InMemoryRateLimiter(
                        self.requests, self.window_seconds
                    )
                self._using_fallback = True
                return await self._fallback.is_allowed(key)
            raise

    async def get_remaining(self, key: str) -> int:
        """Get remaining requests for a key."""
        if self._using_fallback and self._fallback:
            return await self._fallback.get_remaining(key)

        if not self.redis_client:
            return self.requests

        try:
            redis_key = f"ratelimit:{key}"
            count = await self.redis_client.get(redis_key)

            if count is None:
                return self.requests

            return max(0, self.requests - int(count))

        except Exception as e:
            logger.error(f"Redis error getting remaining: {e}")
            return self.requests

    async def reset(self, key: str) -> None:
        """Reset rate limit for a key."""
        if self._using_fallback and self._fallback:
            return await self._fallback.reset(key)

        if self.redis_client:
            try:
                redis_key = f"ratelimit:{key}"
                await self.redis_client.delete(redis_key)
            except Exception as e:
                logger.error(f"Redis error resetting rate limit: {e}")


class RedisAnalysisCache:
    """Redis-backed AI response cache."""

    def __init__(
        self,
        redis_client: Optional[redis.Redis],
        ttl_seconds: int = 3600,
        fallback_to_memory: bool = True,
    ):
        self.redis_client = redis_client
        self.ttl_seconds = ttl_seconds
        self.fallback_to_memory = fallback_to_memory
        self._using_fallback = False

        # Create fallback if needed
        if redis_client is None and fallback_to_memory:
            self._fallback = InMemoryAnalysisCache(ttl_seconds)
            self._using_fallback = True
            logger.info("Using in-memory analysis cache as fallback")
        else:
            self._fallback = None

    async def get(self, key: str) -> Optional[CachedResponse]:
        """Get cached response from Redis."""
        if self._using_fallback and self._fallback:
            return await self._fallback.get(key)

        if not self.redis_client:
            if self.fallback_to_memory:
                self._fallback = InMemoryAnalysisCache(self.ttl_seconds)
                self._using_fallback = True
                return await self._fallback.get(key)
            return None

        try:
            redis_key = f"cache:{key}"
            data = await self.redis_client.get(redis_key)

            if data is None:
                return None

            # Deserialize cached data
            cached = json.loads(data.decode("utf-8"))

            return CachedResponse(
                content=cached["content"],
                tokens_used=cached["tokens"],
            )

        except Exception as e:
            logger.error(f"Redis error getting cached response: {e}")
            if self.fallback_to_memory:
                if not self._fallback:
                    self._fallback = InMemoryAnalysisCache(self.ttl_seconds)
                return await self._fallback.get(key)
            return None

    async def set(self, key: str, content: str, tokens: int) -> None:
        """Cache a response in Redis."""
        if self._using_fallback and self._fallback:
            return await self._fallback.set(key, content, tokens)

        if not self.redis_client:
            if self.fallback_to_memory:
                if not self._fallback:
                    self._fallback = InMemoryAnalysisCache(self.ttl_seconds)
                return await self._fallback.set(key, content, tokens)
            return

        try:
            redis_key = f"cache:{key}"

            # Serialize data
            data = {
                "content": content,
                "tokens": tokens,
                "timestamp": datetime.utcnow().isoformat(),
            }

            await self.redis_client.set(
                redis_key, json.dumps(data), ex=self.ttl_seconds
            )

        except Exception as e:
            logger.error(f"Redis error setting cached response: {e}")
            if self.fallback_to_memory:
                if not self._fallback:
                    self._fallback = InMemoryAnalysisCache(self.ttl_seconds)
                return await self._fallback.set(key, content, tokens)

    async def clear(self) -> None:
        """Clear all cached items."""
        if self._using_fallback and self._fallback:
            return await self._fallback.clear()

        if self.redis_client:
            try:
                # Find all cache keys
                keys = await self.redis_client.keys("cache:*")
                if keys:
                    # Delete all keys
                    for key in keys:
                        await self.redis_client.delete(key)
            except Exception as e:
                logger.error(f"Redis error clearing cache: {e}")


# ==================== Redis Pool Management ====================


async def get_redis_pool() -> Optional[redis.ConnectionPool]:
    """Get or create Redis connection pool."""
    global _redis_pool

    if not REDIS_AVAILABLE:
        logger.warning("Redis not available, using in-memory fallback")
        return None

    if _redis_pool is None:
        try:
            _redis_pool = redis.ConnectionPool.from_url(
                settings.redis.url, decode_responses=False
            )
            logger.info(f"Created Redis connection pool: {settings.redis.url}")
        except Exception as e:
            logger.error(f"Failed to create Redis pool: {e}")
            return None

    return _redis_pool


async def close_redis_pool() -> None:
    """Close Redis connection pool."""
    global _redis_pool

    if _redis_pool is not None:
        try:
            await _redis_pool.disconnect()
            _redis_pool = None
            logger.info("Closed Redis connection pool")
        except Exception as e:
            logger.error(f"Error closing Redis pool: {e}")


async def get_redis_client() -> Optional[redis.Redis]:
    """Get Redis client from connection pool."""
    pool = await get_redis_pool()

    if pool is None:
        return None

    try:
        return redis.Redis(connection_pool=pool)
    except Exception as e:
        logger.error(f"Failed to create Redis client: {e}")
        return None
