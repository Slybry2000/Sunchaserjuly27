"""
Redis caching utilities
"""
import json
import os
from functools import wraps
from typing import Any

import redis.asyncio as redis


class CacheClient:
    """Async Redis cache client"""

    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL")
        self.redis_token = os.getenv("REDIS_TOKEN")
        self._client = None

    async def get_client(self):
        """Get or create Redis client"""
        if self._client is None:
            if self.redis_url and self.redis_token:
                # Upstash Redis format
                self._client = redis.from_url(
                    self.redis_url,
                    password=self.redis_token,
                    decode_responses=True
                )
            else:
                # Local Redis fallback (for development)
                self._client = redis.Redis(
                    host='localhost',
                    port=6379,
                    decode_responses=True
                )
        return self._client

    async def get(self, key: str) -> Any | None:
        """Get value from cache"""
        try:
            client = await self.get_client()
            value = await client.get(key)
            return json.loads(value) if value else None
        except Exception:
            # Fail gracefully if cache is unavailable
            return None

    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set value in cache with TTL"""
        try:
            client = await self.get_client()
            await client.setex(key, ttl, json.dumps(value))
            return True
        except Exception:
            # Fail gracefully if cache is unavailable
            return False


# Global cache instance
cache = CacheClient()


def cached(ttl: int = 3600, key_prefix: str = ""):
    """
    Decorator for caching function results

    Args:
        ttl: Time to live in seconds
        key_prefix: Prefix for cache key
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            cache_key = f"{key_prefix}:{func.__name__}:{hash(str(args) + str(kwargs))}"

            # Try to get from cache first
            cached_result = await cache.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Execute function and cache result
            result = await func(*args, **kwargs)
            await cache.set(cache_key, result, ttl)
            return result

        return wrapper
    return decorator
