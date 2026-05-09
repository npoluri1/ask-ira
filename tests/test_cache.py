import pytest

from src.cache import MemoryCache, ResponseCache, get_cache


@pytest.fixture
def cache():
    return MemoryCache(default_ttl=60)


@pytest.mark.asyncio
async def test_memory_cache_set_get(cache):
    await cache.set("test-key", "test-value", 60)
    result = await cache.get("test-key")
    assert result == "test-value"


@pytest.mark.asyncio
async def test_memory_cache_expiry(cache):
    await cache.set("expire-key", "value", -1)
    result = await cache.get("expire-key")
    assert result is None


@pytest.mark.asyncio
async def test_memory_cache_missing(cache):
    result = await cache.get("non-existent")
    assert result is None


@pytest.mark.asyncio
async def test_memory_cache_clear(cache):
    await cache.set("a", "1", 60)
    await cache.set("b", "2", 60)
    await cache.clear()
    assert await cache.get("a") is None
    assert await cache.get("b") is None


@pytest.mark.asyncio
async def test_response_cache_mcp_result():
    resp_cache = ResponseCache()
    await resp_cache.set_mcp_result("market_data", "AAPL", "AAPL at $150", 60)
    result = await resp_cache.get_mcp_result("market_data", "AAPL")
    assert result == "AAPL at $150"


@pytest.mark.asyncio
async def test_response_cache_miss():
    resp_cache = ResponseCache()
    result = await resp_cache.get_mcp_result("macro", "GDP")
    assert result is None


@pytest.mark.asyncio
async def test_get_cache_singleton():
    c1 = get_cache()
    c2 = get_cache()
    assert c1 is c2
