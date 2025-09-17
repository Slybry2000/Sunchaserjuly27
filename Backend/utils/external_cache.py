import logging
import os
from abc import ABC, abstractmethod
from typing import Any, Optional, Tuple

logger = logging.getLogger(__name__)

# Cache status constants
CACHE_MISS = "miss"
CACHE_HIT = "hit"
CACHE_STALE = "stale"


class CacheBackend(ABC):
    """Abstract base class for cache backends."""

    @abstractmethod
    async def get_status(self, key: str) -> Tuple[Optional[Any], str]:
        """Get value and cache status for key."""
        pass

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int, swr: int = 0) -> None:
        """Set value with TTL and optional stale-while-revalidate."""
        pass

    @abstractmethod
    async def get_or_set(self, key: str, factory, ttl: int, swr: int = 0) -> Any:
        """Get value or compute and set it."""
        pass


class InProcCacheBackend(CacheBackend):
    """In-process cache backend using the existing inproc cache."""

    def __init__(self):
        from Backend.utils.cache_inproc import cache as inproc_cache

        self._cache = inproc_cache

    async def get_status(self, key: str) -> Tuple[Optional[Any], str]:
        return await self._cache.get_status(key)

    async def set(self, key: str, value: Any, ttl: int, swr: int = 0) -> None:
        await self._cache.set(key, value, ttl=ttl, swr=swr)

    async def get_or_set(self, key: str, factory, ttl: int, swr: int = 0) -> Any:
        return await self._cache.get_or_set(key, factory, ttl=ttl, swr=swr)


class RedisCacheBackend(CacheBackend):
    """Redis cache backend for multi-instance deployments.

    Notes:
        We intentionally avoid adding a hard dependency on redis stubs; for type
        checking we silence the missing type information. At runtime, if redis
        is unavailable this backend shouldn't be constructed (callers fall back
        to the in-process cache)."""

    def __init__(self):
        try:
            import redis.asyncio as redis  # type: ignore[import-untyped]
        except Exception as exc:  # pragma: no cover - defensive
            raise RuntimeError(
                "redis.asyncio is required for RedisCacheBackend but is not installed"
            ) from exc

        redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379")
        self._client = redis.from_url(redis_url, decode_responses=True)  # type: ignore[attr-defined]

    async def get_status(self, key: str) -> Tuple[Optional[Any], str]:
        try:
            import json

            value = await self._client.get(key)
            if value is None:
                return None, CACHE_MISS

            # Check if value has expired (simple TTL check)
            # In production, you'd want Redis TTL, but this works for our use case
            return json.loads(value), CACHE_HIT
        except Exception:
            logger.warning("Redis cache error")
            return None, CACHE_MISS

    async def set(self, key: str, value: Any, ttl: int, swr: int = 0) -> None:
        try:
            import json

            await self._client.setex(key, ttl, json.dumps(value))
        except Exception:
            logger.warning("Redis cache set error")

    async def get_or_set(self, key: str, factory, ttl: int, swr: int = 0) -> Any:
        value, status = await self.get_status(key)
        if status != CACHE_MISS:
            return value

        # Compute new value
        try:
            value = factory()
            await self.set(key, value, ttl, swr)
            return value
        except Exception:
            logger.exception("Error computing cache value for %s", key)
            raise


# Global cache instance
_cache_backend: Optional[CacheBackend] = None


def get_cache_backend() -> CacheBackend:
    """Get the configured cache backend."""
    global _cache_backend
    if _cache_backend is None:
        # Check if Redis is configured and available
        redis_url = os.environ.get("REDIS_URL")
        if redis_url:
            try:
                _cache_backend = RedisCacheBackend()
                logger.info("Using Redis cache backend")
            except Exception:
                logger.warning(
                    "Failed to initialize Redis cache, falling back to in-process"
                )
                _cache_backend = InProcCacheBackend()
        else:
            _cache_backend = InProcCacheBackend()
            logger.info("Using in-process cache backend")

    return _cache_backend


async def close_cache():
    """Close cache connections (call on shutdown)."""
    global _cache_backend
    if _cache_backend and hasattr(_cache_backend, "_client"):
        await _cache_backend._client.close()
    _cache_backend = None
