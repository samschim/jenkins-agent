"""Unit tests for cache module."""
import pytest
import json
from unittest.mock import AsyncMock, patch
from langchain_jenkins.utils.cache import CacheManager

@pytest.fixture
async def cache_manager():
    """Create a cache manager instance for testing."""
    with patch('redis.asyncio.Redis.from_url') as mock_redis:
        manager = CacheManager()
        manager.redis = AsyncMock()
        yield manager

@pytest.mark.asyncio
async def test_generate_key(cache_manager):
    """Test cache key generation."""
    key = cache_manager._generate_key("test", "arg1", "arg2", kwarg1="value1")
    assert key.startswith("jenkins:test:")
    assert len(key) > len("jenkins:test:")

@pytest.mark.asyncio
async def test_get_cached_value(cache_manager):
    """Test getting a cached value."""
    test_data = {"key": "value"}
    cache_manager.redis.get.return_value = json.dumps(test_data)
    
    result = await cache_manager.get("test_key")
    assert result == test_data
    cache_manager.redis.get.assert_called_once_with("test_key")

@pytest.mark.asyncio
async def test_get_missing_value(cache_manager):
    """Test getting a non-existent cached value."""
    cache_manager.redis.get.return_value = None
    
    result = await cache_manager.get("test_key")
    assert result is None
    cache_manager.redis.get.assert_called_once_with("test_key")

@pytest.mark.asyncio
async def test_set_value(cache_manager):
    """Test setting a cache value."""
    test_data = {"key": "value"}
    await cache_manager.set("test_key", test_data)
    
    cache_manager.redis.set.assert_called_once_with(
        "test_key",
        json.dumps(test_data),
        ex=300
    )

@pytest.mark.asyncio
async def test_delete_value(cache_manager):
    """Test deleting a cache value."""
    await cache_manager.delete("test_key")
    cache_manager.redis.delete.assert_called_once_with("test_key")

@pytest.mark.asyncio
async def test_clear_pattern(cache_manager):
    """Test clearing cache by pattern."""
    cache_manager.redis.keys.return_value = ["key1", "key2"]
    
    await cache_manager.clear_pattern("test")
    
    cache_manager.redis.keys.assert_called_once_with("jenkins:test:*")
    cache_manager.redis.delete.assert_called_once_with("key1", "key2")

@pytest.mark.asyncio
async def test_cached_decorator(cache_manager):
    """Test the cached decorator."""
    test_data = {"result": "value"}
    
    @cache_manager.cached("test")
    async def test_func():
        return test_data
    
    # First call - should cache
    cache_manager.redis.get.return_value = None
    result1 = await test_func()
    assert result1 == test_data
    
    # Second call - should use cache
    cache_manager.redis.get.return_value = json.dumps(test_data)
    result2 = await test_func()
    assert result2 == test_data