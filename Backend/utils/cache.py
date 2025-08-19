"""
Redis caching utilities
"""
import json
import os
from functools import wraps
from typing import Any

import redis.asyncio as redis
import asyncio


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


import time

# Simple in-memory cache shim used for tests. Implements minimal SWR and
# single-flight semantics expected by the test-suite. This keeps tests fast
# and avoids an external Redis dependency.
_shim_cache: dict[str, dict] = {}
_shim_lock = asyncio.Lock()


async def get_or_set(key: str, factory, ttl: int = 300, stale_reval: int = 60):
    """Simple async get_or_set with SWR and single-flight.

    Returns (value, status) where status is one of 'miss', 'hit_fresh', 'hit_stale'.
    Concurrent callers should await the same in-flight producer (single-flight)
    instead of receiving a placeholder None value.
    """
    now = time.time()

    # Fast path: check existing entry under lock
    async with _shim_lock:
        entry = _shim_cache.get(key)
        if entry:
            task = entry.get("task")
            age = now - entry["created_at"]
            ttl_sec = entry["ttl"]
            swr = entry["swr"]

            # If a producer is already running, await it (single-flight)
            if task is not None and not task.done():
                running_task = task
            else:
                running_task = None

            # Fresh value
            if age < ttl_sec and entry["value"] is not None:
                return entry["value"], "hit_fresh"

            # Stale but within SWR window: trigger background refresh if not running
            if ttl_sec <= age < (ttl_sec + swr):
                if running_task is None:
                    async def _refresh():
                        try:
                            val = await factory() if asyncio.iscoroutinefunction(factory) else await asyncio.to_thread(factory)
                            async with _shim_lock:
                                ent = _shim_cache.get(key)
                                if ent is not None:
                                    ent["value"] = val
                                    ent["created_at"] = time.time()
                        finally:
                            async with _shim_lock:
                                ent = _shim_cache.get(key)
                                if ent is not None:
                                    ent["task"] = None

                    entry["task"] = asyncio.create_task(_refresh())
                # return stale value to caller
                return entry["value"], "hit_stale"

            # Evict expired beyond SWR
            if ttl_sec + swr <= age:
                del _shim_cache[key]

            # If a producer was running, await it (outside lock)
            if running_task is not None:
                # we'll await below outside the lock
                pass
            else:
                # fall through to start a new producer
                pass
        else:
            running_task = None

        # If there's a running producer, await it and return the produced value
        if entry and running_task is not None:
            # release lock then await
            await running_task
            async with _shim_lock:
                ent = _shim_cache.get(key)
                if ent is None:
                    return None, "miss"
                return ent["value"], "miss"

        # Not present or we need to start a new producer: create task and placeholder
        future = asyncio.create_task(factory() if asyncio.iscoroutinefunction(factory) else asyncio.to_thread(factory))
        _shim_cache[key] = {"value": None, "created_at": now, "ttl": ttl, "swr": stale_reval, "task": future}

    # Await the producer outside the lock
    try:
        val = await future
    except Exception:
        # If the producer failed, clean up placeholder
        async with _shim_lock:
            ent = _shim_cache.get(key)
            if ent and ent.get("task") is future:
                del _shim_cache[key]
        raise

    # Store the produced value
    async with _shim_lock:
        ent = _shim_cache.get(key)
        if ent is not None:
            ent["value"] = val
            ent["created_at"] = time.time()
            ent["task"] = None

    return val, "miss"
