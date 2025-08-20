"""
Tests for in-process cache with SWR support
"""
import asyncio
import time
import pytest
from unittest.mock import AsyncMock, Mock
from freezegun import freeze_time

from utils.cache_inproc import InProcessCache, CacheEntry


class TestCacheEntry:
    """Test CacheEntry dataclass"""
    
    def test_is_fresh(self):
        """Test fresh entry detection"""
        with freeze_time("2025-01-01 12:00:00") as frozen_time:
            entry = CacheEntry(value="test", created_at=time.time(), ttl_seconds=300, swr_seconds=60)
            
            # Fresh within TTL
            assert entry.is_fresh
            
            # Still fresh at TTL boundary
            frozen_time.tick(delta=299)
            assert entry.is_fresh
            
            # No longer fresh after TTL
            frozen_time.tick(delta=2)
            assert not entry.is_fresh

    def test_is_stale_but_revalidatable(self):
        """Test SWR window detection"""
        with freeze_time("2025-01-01 12:00:00") as frozen_time:
            entry = CacheEntry(value="test", created_at=time.time(), ttl_seconds=300, swr_seconds=60)
            
            # Not stale when fresh
            assert not entry.is_stale_but_revalidatable
            
            # Stale but revalidatable after TTL
            frozen_time.tick(delta=310)
            assert entry.is_stale_but_revalidatable
            
            # Still revalidatable at SWR boundary
            frozen_time.tick(delta=49)
            assert entry.is_stale_but_revalidatable
            
            # No longer revalidatable after SWR window
            frozen_time.tick(delta=2)
            assert not entry.is_stale_but_revalidatable

    def test_should_evict(self):
        """Test eviction condition"""
        with freeze_time("2025-01-01 12:00:00") as frozen_time:
            entry = CacheEntry(value="test", created_at=time.time(), ttl_seconds=300, swr_seconds=60)
            
            # Should not evict when fresh
            assert not entry.should_evict
            
            # Should not evict when stale but in SWR window
            frozen_time.tick(delta=310)
            assert not entry.should_evict
            
            # Should evict after SWR window
            frozen_time.tick(delta=61)
            assert entry.should_evict


class TestInProcessCache:
    """Test InProcessCache"""

    @pytest.fixture
    def cache(self):
        """Create a fresh cache instance"""
        return InProcessCache(maxsize=10, default_ttl=300, default_swr=60)

    async def test_basic_get_set(self, cache):
        """Test basic cache operations"""
        # Cache miss
        result = await cache.get("key1")
        assert result is None
        
        # Set and get
        await cache.set("key1", "value1")
        result = await cache.get("key1")
        assert result == "value1"

    async def test_ttl_expiration(self, cache):
        """Test TTL-based expiration"""
        with freeze_time("2025-01-01 12:00:00") as frozen_time:
            await cache.set("key1", "value1", ttl=300)
            
            # Fresh
            result = await cache.get("key1")
            assert result == "value1"
            
            # Expired
            frozen_time.tick(delta=400)
            result = await cache.get("key1")
            assert result is None

    async def test_swr_behavior(self, cache):
        """Test stale-while-revalidate behavior"""
        with freeze_time("2025-01-01 12:00:00") as frozen_time:
            await cache.set("key1", "value1", ttl=300, swr=60)
            
            # Fresh
            result = await cache.get("key1")
            assert result == "value1"
            
            # Stale but still served
            frozen_time.tick(delta=310)
            result = await cache.get("key1")
            assert result == "value1"
            
            # Evicted after SWR window
            frozen_time.tick(delta=61)
            result = await cache.get("key1")
            assert result is None

    async def test_lru_eviction(self, cache):
        """Test LRU eviction when maxsize is reached"""
        # Fill cache to maxsize
        for i in range(10):
            await cache.set(f"key{i}", f"value{i}")
        
        # All should be present
        for i in range(10):
            result = await cache.get(f"key{i}")
            assert result == f"value{i}"
        
        # Adding one more should evict the LRU (key0)
        await cache.set("key10", "value10")
        
        # key0 should be evicted
        result = await cache.get("key0")
        assert result is None
        
        # Others should still be present
        for i in range(1, 11):
            result = await cache.get(f"key{i}")
            assert result == f"value{i}"

    async def test_access_order_update(self, cache):
        """Test that access updates LRU order"""
        # Fill cache
        for i in range(10):
            await cache.set(f"key{i}", f"value{i}")
        
        # Access key0 to make it most recent
        await cache.get("key0")
        
        # Add new item, should evict key1 (now LRU) instead of key0
        await cache.set("key10", "value10")
        
        # key0 should still be present
        result = await cache.get("key0")
        assert result == "value0"
        
        # key1 should be evicted
        result = await cache.get("key1")
        assert result is None

    async def test_get_or_set_cache_hit(self, cache):
        """Test get_or_set with cache hit"""
        factory = Mock(return_value="computed_value")
        
        # Set initial value
        await cache.set("key1", "cached_value")
        
        # get_or_set should return cached value without calling factory
        result = await cache.get_or_set("key1", factory)
        assert result == "cached_value"
        factory.assert_not_called()

    async def test_get_or_set_cache_miss(self, cache):
        """Test get_or_set with cache miss"""
        factory = Mock(return_value="computed_value")
        
        # get_or_set should call factory and cache result
        result = await cache.get_or_set("key1", factory)
        assert result == "computed_value"
        factory.assert_called_once()
        
        # Subsequent call should use cached value
        factory.reset_mock()
        result = await cache.get_or_set("key1", factory)
        assert result == "computed_value"
        factory.assert_not_called()

    async def test_get_or_set_async_factory(self, cache):
        """Test get_or_set with async factory"""
        async_factory = AsyncMock(return_value="async_computed_value")
        
        result = await cache.get_or_set("key1", async_factory)
        assert result == "async_computed_value"
        async_factory.assert_called_once()

    async def test_swr_background_refresh(self, cache):
        """Test background refresh during SWR window"""
        call_count = 0
        
        def factory():
            nonlocal call_count
            call_count += 1
            return f"value_{call_count}"
        
        with freeze_time("2025-01-01 12:00:00") as frozen_time:
            # Initial cache
            result = await cache.get_or_set("key1", factory, ttl=300, swr=60)
            assert result == "value_1"
            assert call_count == 1
            
            # Move to SWR window
            frozen_time.tick(delta=310)
            
            # Should return stale value and trigger background refresh
            result = await cache.get_or_set("key1", factory, ttl=300, swr=60)
            assert result == "value_1"  # Stale value returned immediately
            
            # Wait for background refresh to complete (poll up to 1s)
            # Wait for background refresh to complete deterministically via helper
            await cache.wait_for_bg_refresh("key1", timeout=1.0)

            # Factory should have been called again
            assert call_count >= 2
            
            # Fresh value should now be available
            result = await cache.get("key1")
            assert result == "value_2"

    async def test_single_flight_protection(self, cache):
        """Test that concurrent requests for same key don't duplicate work"""
        call_count = 0
        
        async def slow_factory():
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.1)  # Simulate slow operation
            return f"value_{call_count}"
        
        # Start multiple concurrent requests
        tasks = [
            asyncio.create_task(cache.get_or_set("key1", slow_factory))
            for _ in range(5)
        ]
        
        results = await asyncio.gather(*tasks)
        
        # All should return same value
        assert all(result == "value_1" for result in results)
        
        # Factory should only be called once
        assert call_count == 1

    async def test_clear(self, cache):
        """Test cache clear"""
        # Add some items
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        
        # Verify they're cached
        assert await cache.get("key1") == "value1"
        assert await cache.get("key2") == "value2"
        
        # Clear cache
        cache.clear()
        
        # Should be empty
        assert await cache.get("key1") is None
        assert await cache.get("key2") is None

    async def test_stats(self, cache):
        """Test cache statistics"""
        with freeze_time("2025-01-01 12:00:00") as frozen_time:
            # Create one stale entry first, advance time so it becomes stale,
            # then add two fresh entries so stats reflect 2 fresh + 1 stale.
            await cache.set("stale1", "value3", ttl=300, swr=60)
            frozen_time.tick(delta=310)  # Move to SWR window for stale1

            # Add fresh entries (created at later time)
            await cache.set("fresh1", "value1", ttl=300, swr=60)
            await cache.set("fresh2", "value2", ttl=300, swr=60)

            stats = cache.stats()

            assert stats["total_entries"] == 3
            assert stats["fresh_entries"] == 2
            assert stats["stale_entries"] == 1
            assert stats["active_refreshes"] == 0
            assert stats["maxsize"] == 10

    async def test_exception_handling_in_factory(self, cache):
        """Test that factory exceptions are properly handled"""
        def failing_factory():
            raise ValueError("Factory failed")
        
        # Should raise the exception
        with pytest.raises(ValueError, match="Factory failed"):
            await cache.get_or_set("key1", failing_factory)
        
        # Key should not be cached
        result = await cache.get("key1")
        assert result is None

    async def test_background_refresh_exception_handling(self, cache):
        """Test that background refresh exceptions don't break cache"""
        call_count = 0
        
        def factory():
            nonlocal call_count
            call_count += 1
            if call_count == 2:  # Fail on background refresh
                raise ValueError("Background refresh failed")
            return f"value_{call_count}"
        
        with freeze_time("2025-01-01 12:00:00") as frozen_time:
            # Initial cache
            result = await cache.get_or_set("key1", factory, ttl=300, swr=60)
            assert result == "value_1"
            
            # Move to SWR window
            frozen_time.tick(delta=310)
            
            # Should still return stale value even if background refresh fails
            result = await cache.get_or_set("key1", factory, ttl=300, swr=60)
            assert result == "value_1"
            
            # Wait for background refresh to complete (ignore background exception)
            await cache.wait_for_bg_refresh("key1", timeout=1.0, swallow_exceptions=True)
            
            # Stale value should still be available
            result = await cache.get("key1")
            assert result == "value_1"
