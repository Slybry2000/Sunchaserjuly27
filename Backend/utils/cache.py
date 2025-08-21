"""Cache utilities abstraction.

This module exposes a simple `cached` decorator and a `get_or_set` helper.
If Redis is configured via `REDIS_URL` (and optionally `REDIS_TOKEN`) the
Redis-backed `CacheClient` will be used. Otherwise the in-process
implementation in `cache_inproc.py` is used by default (recommended for
development and tests).
"""

import json
import os
from functools import wraps
from typing import Any, Any as _Any, Callable

try:
    import redis.asyncio as redis  # type: ignore
except Exception:
    redis = None  # type: ignore

import asyncio
import inspect

from .cache_inproc import cache as _inproc_cache


class CacheClient:
    """Async Redis cache client (optional).

    This is only used when REDIS_URL (or REDIS_TOKEN) is set. For local
    development and tests the in-process cache is preferred.
    """

    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL")
        self.redis_token = os.getenv("REDIS_TOKEN")
        self._client = None

    async def get_client(self):
        if self._client is None:
            if self.redis_url and redis is not None:
                # Upstash or other URL
                self._client = redis.from_url(
                    self.redis_url,
                    password=self.redis_token,
                    decode_responses=True,
                )
            else:
                # No Redis available
                raise RuntimeError("Redis not configured or unavailable")
        return self._client

    async def get(self, key: str) -> Any | None:
        try:
            client = await self.get_client()
            value = await client.get(key)
            return json.loads(value) if value else None
        except Exception:
            return None

    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        try:
            client = await self.get_client()
            await client.setex(key, ttl, json.dumps(value))
            return True
        except Exception:
            return False


# Choose cache implementation: prefer Redis when configured, else use in-proc
_use_redis = bool(os.getenv("REDIS_URL") or os.getenv("REDIS_TOKEN")) and redis is not None
# `cache` may be either a CacheClient or the in-process cache instance; annotate
# as Any so static typecheckers accept the runtime flexibility.

cache: _Any
if _use_redis:
    cache = CacheClient()
else:
    cache = _inproc_cache


def cached(ttl: int = 3600, key_prefix: str = "") -> Callable:
    """Decorator for caching coroutine function results.

    When applied it will attempt to read from the configured cache and
    otherwise execute the function and cache the result.
    """

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = f"{key_prefix}:{func.__name__}:{hash(str(args) + str(kwargs))}"

            # Try cache get
            try:
                cached_result = await cache.get(cache_key)
            except Exception:
                cached_result = None

            if cached_result is not None:
                return cached_result

            # Compute and set
            result = await func(*args, **kwargs)
            try:
                await cache.set(cache_key, result, ttl)
            except Exception:
                # Best-effort; don't fail the request
                pass
            return result

        # Preserve the original function signature so FastAPI can detect parameters
        try:
            wrapper.__signature__ = inspect.signature(func)
        except Exception:
            # best-effort: if signature cannot be set, continue without failing
            pass

        return wrapper

    return decorator


async def get_or_set(key: str, factory: Callable, ttl: int = 300, stale_reval: int = 60):
    """Unified get_or_set abstraction.

    If the underlying cache implements `get_or_set` (in-process cache) it
    will be used. Otherwise this wrapper falls back to a simple get+set
    implementation against the Redis client.
    Returns (value, status) where status is one of 'miss','hit_fresh','hit_stale'.
    """
    # Prefer atomic get_or_set if available (inproc cache)
    if hasattr(cache, "get_or_set"):
        # If the cache supports get_status, ask first so we can return the
        # appropriate (value, status) tuple. This preserves the expected
        # behavior where the first call that computes the value returns
        # status 'miss'. Only call get_or_set to trigger computation when
        # get_status reports a miss.
        if hasattr(cache, "get_status"):
            val, status = await cache.get_status(key)
            if status != "miss":
                return val, status
            # else: fall through to compute

        # Compute (may be fresh or cached depending on race)
        val = await cache.get_or_set(key, factory, ttl, stale_reval)
        return val, "miss"

    # Fallback: simple get then set
    try:
        val = await cache.get(key)
    except Exception:
        val = None

    if val is not None:
        return val, "hit_fresh"

    # compute and store
    if asyncio.iscoroutinefunction(factory):
        val = await factory()
    else:
        val = await asyncio.to_thread(factory)

    try:
        await cache.set(key, val, ttl)
    except Exception:
        pass

    return val, "miss"
