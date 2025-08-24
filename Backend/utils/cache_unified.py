"""Cache utilities with unified in-process implementation.

This module exposes a simple `cached` decorator and a `get_or_set` helper
using the high-performance in-process cache implementation with LRU eviction,
TTL expiration, and stale-while-revalidate capabilities.

The previous Redis-based implementation has been removed in favor of a
simplified single-cache approach optimized for serverless and container
deployments where in-process caching provides better performance and
reduced complexity.
"""

import os
from functools import wraps
from typing import Any, Callable
import asyncio
import inspect

from .cache_inproc import cache


def cached(ttl: int = 3600, key_prefix: str = "") -> Callable:
    """Decorator for caching coroutine function results.

    Caches function results using the in-process cache implementation with
    LRU eviction and TTL expiration. Supports stale-while-revalidate for
    high availability.

    Args:
        ttl: Time-to-live in seconds for cached results
        key_prefix: Optional prefix for cache keys to avoid collisions

    Returns:
        Decorated function with caching behavior
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

            # Cache miss: execute function and cache result
            if inspect.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            try:
                await cache.set(cache_key, result, ttl)
            except Exception:
                # Cache set failure doesn't break functionality
                pass

            return result

        # Preserve the original function signature so FastAPI can detect parameters
        try:
            # use setattr so static checkers (mypy) don't complain about setting
            # arbitrary attributes on Callable objects
            setattr(wrapper, "__signature__", inspect.signature(func))
        except Exception:
            # best-effort: if signature cannot be set, continue without failing
            pass

        return wrapper

    return decorator


async def get_or_set(key: str, factory: Callable, ttl: int = 3600) -> Any:
    """Get value from cache or set it using the factory function.

    Args:
        key: Cache key to retrieve/store value
        factory: Function to generate value if not in cache
        ttl: Time-to-live for the cached value in seconds

    Returns:
        Cached value or newly generated value from factory
    """
    try:
        cached_result = await cache.get(key)
        if cached_result is not None:
            return cached_result
    except Exception:
        pass

    # Generate new value
    if inspect.iscoroutinefunction(factory):
        result = await factory()
    else:
        result = factory()

    try:
        await cache.set(key, result, ttl)
    except Exception:
        # Cache set failure doesn't break functionality
        pass

    return result
