"""Unit tests for rate limiting."""
import pytest
import time
from unittest.mock import AsyncMock, patch
from langchain_jenkins.utils.rate_limit import (
    RateLimiter,
    APIRateLimiter,
    RateLimitConfig
)

@pytest.fixture
async def rate_limiter():
    """Create a rate limiter for testing."""
    with patch('redis.asyncio.Redis.from_url') as mock_redis:
        limiter = RateLimiter()
        limiter.redis = AsyncMock()
        yield limiter

@pytest.mark.asyncio
async def test_check_rate_limit_not_exceeded(rate_limiter):
    """Test rate limit not exceeded."""
    rate_limiter.redis.pipeline.return_value.execute.return_value = [
        1,  # zremrangebyscore result
        5,  # zcard result
        1   # zadd result
    ]
    
    result = await rate_limiter.check_rate_limit(
        "test",
        RateLimitConfig(requests=10, period=60)
    )
    
    assert result is True

@pytest.mark.asyncio
async def test_check_rate_limit_exceeded(rate_limiter):
    """Test rate limit exceeded."""
    rate_limiter.redis.pipeline.return_value.execute.return_value = [
        1,    # zremrangebyscore result
        15,   # zcard result
        1     # zadd result
    ]
    
    result = await rate_limiter.check_rate_limit(
        "test",
        RateLimitConfig(requests=10, period=60)
    )
    
    assert result is False

@pytest.mark.asyncio
async def test_get_retry_after(rate_limiter):
    """Test getting retry after time."""
    now = time.time()
    rate_limiter.redis.zrange.return_value = [
        ("test", now - 30)  # 30 seconds ago
    ]
    
    retry_after = await rate_limiter.get_retry_after(
        "test",
        RateLimitConfig(requests=10, period=60)
    )
    
    assert retry_after == pytest.approx(30, rel=1)

@pytest.mark.asyncio
async def test_rate_limit_decorator(rate_limiter):
    """Test rate limit decorator."""
    @rate_limiter.rate_limit("test")
    async def test_func():
        return "success"
    
    rate_limiter.check_rate_limit = AsyncMock(return_value=True)
    result = await test_func()
    
    assert result == "success"
    rate_limiter.check_rate_limit.assert_called_once()

@pytest.mark.asyncio
async def test_rate_limit_decorator_exceeded(rate_limiter):
    """Test rate limit decorator when limit exceeded."""
    @rate_limiter.rate_limit("test")
    async def test_func():
        return "success"
    
    rate_limiter.check_rate_limit = AsyncMock(return_value=False)
    rate_limiter.get_retry_after = AsyncMock(return_value=30)
    
    with pytest.raises(Exception) as exc:
        await test_func()
    assert "Rate limit exceeded" in str(exc.value)

def test_api_rate_limiter_get_limiter():
    """Test getting API rate limiter config."""
    limiter = APIRateLimiter()
    
    # Test default limiter
    config = limiter.get_limiter("unknown")
    assert config.requests == 60
    
    # Test specific limiters
    config = limiter.get_limiter("builds")
    assert config.requests == 10
    
    config = limiter.get_limiter("plugins")
    assert config.requests == 30

@pytest.mark.asyncio
async def test_api_rate_limiter_decorator(rate_limiter):
    """Test API rate limiter decorator."""
    api_limiter = APIRateLimiter()
    
    @api_limiter.limit_api("builds")
    async def test_func():
        return "success"
    
    rate_limiter.check_rate_limit = AsyncMock(return_value=True)
    with patch('langchain_jenkins.utils.rate_limit.rate_limiter', rate_limiter):
        result = await test_func()
    
    assert result == "success"
    rate_limiter.check_rate_limit.assert_called_once()