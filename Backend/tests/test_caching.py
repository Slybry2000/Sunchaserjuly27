import pytest
import asyncio
from utils.cache import get_or_set

@pytest.mark.asyncio
async def test_cache_hit_and_miss():
    calls = []
    async def producer():
        calls.append(1)
        await asyncio.sleep(0.01)
        return "value"
    val1, status1 = await get_or_set("key1", producer, ttl=1, stale_reval=1)
    val2, status2 = await get_or_set("key1", producer, ttl=1, stale_reval=1)
    assert val1 == val2 == "value"
    assert status1 == "miss"
    assert status2 == "hit_fresh"
    assert len(calls) == 1

@pytest.mark.asyncio
async def test_cache_stale_while_revalidate(monkeypatch):
    calls = []
    async def producer():
        calls.append(1)
        return len(calls)
    # Insert value, then simulate time passing
    val1, status1 = await get_or_set("key2", producer, ttl=0, stale_reval=1)
    val2, status2 = await get_or_set("key2", producer, ttl=0, stale_reval=1)
    assert status2 == "hit_stale"
    assert val2 == val1

@pytest.mark.asyncio
async def test_cache_single_flight():
    calls = []
    async def producer():
        calls.append(1)
        await asyncio.sleep(0.05)
        return "v"
    results = await asyncio.gather(
        get_or_set("key3", producer, ttl=1, stale_reval=1),
        get_or_set("key3", producer, ttl=1, stale_reval=1),
    )
    assert len(calls) == 1
    assert results[0][0] == results[1][0] == "v"
