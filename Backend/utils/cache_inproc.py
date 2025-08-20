"""
In-process cache with SWR (Stale-While-Revalidate) support
"""
import asyncio
import time
from typing import Any, Callable, Optional
from dataclasses import dataclass
from threading import Lock
import logging

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Cache entry with TTL and SWR support"""
    value: Any
    created_at: float
    ttl_seconds: int
    swr_seconds: int

    @property
    def is_fresh(self) -> bool:
        """Check if entry is within TTL"""
        return time.time() - self.created_at < self.ttl_seconds

    @property
    def is_stale_but_revalidatable(self) -> bool:
        """Check if entry is stale but within SWR window"""
        age = time.time() - self.created_at
        return self.ttl_seconds <= age < (self.ttl_seconds + self.swr_seconds)

    @property
    def should_evict(self) -> bool:
        """Check if entry should be evicted"""
        age = time.time() - self.created_at
        return age >= (self.ttl_seconds + self.swr_seconds)


class InProcessCache:
    """
    In-process LRU cache with TTL and Stale-While-Revalidate support
    
    Features:
    - LRU eviction when maxsize is reached
    - TTL-based expiration
    - SWR: serve stale data while refreshing in background
    - Single-flight: prevent duplicate concurrent requests for same key
    """
    
    def __init__(self, maxsize: int = 1000, default_ttl: int = 300, default_swr: int = 60):
        self.maxsize = maxsize
        self.default_ttl = default_ttl
        self.default_swr = default_swr
        self._cache: dict[str, CacheEntry] = {}
        self._access_order: list[str] = []  # For LRU tracking
        self._lock = Lock()
        self._refresh_tasks: dict[str, asyncio.Task] = {}  # Single-flight tracking

    def _evict_expired(self) -> None:
        """Remove expired entries"""
        to_remove = []
        for key, entry in self._cache.items():
            if entry.should_evict:
                to_remove.append(key)
        
        for key in to_remove:
            self._remove_key(key)

    def _remove_key(self, key: str) -> None:
        """Remove key from cache and access order"""
        if key in self._cache:
            del self._cache[key]
        if key in self._access_order:
            self._access_order.remove(key)

    def _update_access_order(self, key: str) -> None:
        """Update LRU access order"""
        if key in self._access_order:
            self._access_order.remove(key)
        self._access_order.append(key)

    def _evict_lru(self) -> None:
        """Evict least recently used items if over maxsize"""
        while len(self._cache) >= self.maxsize and self._access_order:
            lru_key = self._access_order[0]
            self._remove_key(lru_key)

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        with self._lock:
            self._evict_expired()
            
            if key not in self._cache:
                return None
            
            entry = self._cache[key]
            self._update_access_order(key)
            
            if entry.is_fresh:
                logger.debug(f"Cache hit (fresh): {key}")
                return entry.value
            elif entry.is_stale_but_revalidatable:
                logger.debug(f"Cache hit (stale): {key}")
                return entry.value
            else:
                # Entry is too old, remove it
                self._remove_key(key)
                return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None, swr: Optional[int] = None) -> None:
        """Set value in cache"""
        if ttl is None:
            ttl = self.default_ttl
        if swr is None:
            swr = self.default_swr
        
        entry = CacheEntry(
            value=value,
            created_at=time.time(),
            ttl_seconds=ttl,
            swr_seconds=swr
        )
        
        with self._lock:
            self._evict_expired()
            self._evict_lru()
            
            self._cache[key] = entry
            self._update_access_order(key)
            
        logger.debug(f"Cache set: {key} (TTL: {ttl}s, SWR: {swr}s)")

    async def get_or_set(
        self,
        key: str,
        factory: Callable[[], Any],
        ttl: Optional[int] = None,
        swr: Optional[int] = None
    ) -> Any:
        """
        Get value from cache or compute it using factory and cache it.
        Returns the cached/computed value.
        """
        if ttl is None:
            ttl = self.default_ttl
        if swr is None:
            swr = self.default_swr

        should_refresh = False
        value_to_return: Optional[Any] = None

        with self._lock:
            self._evict_expired()
            entry = self._cache.get(key)
            if entry is not None:
                self._update_access_order(key)
                if entry.is_fresh:
                    return entry.value
                if entry.is_stale_but_revalidatable:
                    value_to_return = entry.value
                    if key not in self._refresh_tasks:
                        should_refresh = True
                else:
                    # Too old, evict and fall through to fetch
                    self._remove_key(key)

        # Start background refresh outside the lock
        if should_refresh:
            logger.debug(f"Starting background refresh for: {key}")
            task = asyncio.create_task(self._background_refresh(key, factory, ttl, swr))
            self._refresh_tasks[key] = task
            return value_to_return

        if value_to_return is not None:
            return value_to_return

        # Not in cache or was evicted: fetch now
        value = await self._fetch_and_cache(key, factory, ttl, swr)
        return value

    async def _fetch_and_cache(
        self,
        key: str,
        factory: Callable[[], Any],
        ttl: Optional[int],
        swr: Optional[int]
    ) -> Any:
        """Fetch value and cache it"""
        # Check for single-flight
        if key in self._refresh_tasks:
            logger.debug(f"Waiting for existing fetch: {key}")
            try:
                return await self._refresh_tasks[key]
            except Exception as e:
                logger.warning(f"Shared task failed for {key}: {e}")
                # Fall through to retry
        
        # Start new task
        logger.debug(f"Fetching new value: {key}")
        
        async def fetch_task():
            try:
                if asyncio.iscoroutinefunction(factory):
                    value = await factory()
                else:
                    value = factory()
                
                await self.set(key, value, ttl, swr)
                return value
            finally:
                # Clean up refresh task
                self._refresh_tasks.pop(key, None)
        
        # Store task for single-flight
        task = asyncio.create_task(fetch_task())
        self._refresh_tasks[key] = task
        
        return await task

    async def _background_refresh(
        self,
        key: str,
        factory: Callable[[], Any],
        ttl: Optional[int],
        swr: Optional[int]
    ) -> None:
        """Background refresh task"""
        try:
            # Debug: indicate background refresh started
            logger.debug(f"Background refresh starting: {key}")
            if asyncio.iscoroutinefunction(factory):
                value = await factory()
            else:
                value = factory()
            
            await self.set(key, value, ttl, swr)
            logger.debug(f"Background refresh completed: {key}")
        except Exception as e:
            logger.warning(f"Background refresh failed for {key}: {e}")
        finally:
            # Clean up
            self._refresh_tasks.pop(key, None)

    async def get_status(self, key: str) -> tuple[Optional[Any], str]:
        """Return (value, status) for a key.

        Status is one of: 'miss', 'hit_fresh', 'hit_stale'. This is a best-effort
        helper used by the outer `utils.cache.get_or_set` wrapper to maintain
        compatibility with tests expecting a (value, status) tuple.
        """
        with self._lock:
            self._evict_expired()
            entry = self._cache.get(key)
            if entry is None:
                return None, "miss"
            self._update_access_order(key)
            if entry.is_fresh:
                return entry.value, "hit_fresh"
            if entry.is_stale_but_revalidatable:
                return entry.value, "hit_stale"
            # else: treated as miss
            return None, "miss"

    async def wait_for_bg_refresh(
        self,
        key: str,
        timeout: Optional[float] = None,
        swallow_exceptions: bool = False,
    ) -> bool:
        """Test helper: wait for an active background refresh for `key` to complete.

        Returns True if there was an active refresh and it completed within the timeout.
        Returns False immediately if there is no active refresh for the key.

        Raises asyncio.TimeoutError if the wait times out. If the background task
        raises an exception, that exception will propagate to the caller.
        """
        task = self._refresh_tasks.get(key)
        if not task:
            return False

        try:
            await asyncio.wait_for(task, timeout)
            return True
        except Exception:
            if swallow_exceptions:
                # Caller wants to wait for completion but ignore errors
                return True
            raise

    def clear(self) -> None:
        """Clear all cache entries"""
        with self._lock:
            self._cache.clear()
            self._access_order.clear()

    def stats(self) -> dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            total_entries = len(self._cache)
            now = time.time()
            fresh_entries = sum(1 for entry in self._cache.values() if not (now - entry.created_at >= entry.ttl_seconds))
            stale_entries = sum(1 for entry in self._cache.values() if entry.ttl_seconds <= (now - entry.created_at) < (entry.ttl_seconds + entry.swr_seconds))
            
            return {
                "total_entries": total_entries,
                "fresh_entries": fresh_entries,
                "stale_entries": stale_entries,
                "active_refreshes": len(self._refresh_tasks),
                "maxsize": self.maxsize,
            }


# Global cache instance
cache = InProcessCache()
