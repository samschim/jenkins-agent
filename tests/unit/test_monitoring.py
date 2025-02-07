"""Unit tests for performance monitoring."""
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch
from langchain_jenkins.utils.monitoring import (
    PerformanceMonitor,
    MetricPoint,
    PerformanceMetrics
)

@pytest.fixture
async def monitor():
    """Create a performance monitor for testing."""
    with patch('redis.asyncio.Redis.from_url') as mock_redis:
        monitor = PerformanceMonitor()
        monitor.redis = AsyncMock()
        yield monitor

@pytest.mark.asyncio
async def test_record_metric(monitor):
    """Test recording a metric."""
    await monitor.record_metric(
        "response_time",
        0.5,
        {"function": "test_func"}
    )
    
    monitor.redis.zadd.assert_called_once()
    assert len(monitor.metrics.response_times) == 1
    assert monitor.metrics.response_times[0].value == 0.5

@pytest.mark.asyncio
async def test_get_metrics(monitor):
    """Test getting metrics."""
    # Add some test metrics
    start_time = datetime.now() - timedelta(hours=1)
    end_time = datetime.now()
    
    monitor.redis.zrangebyscore.return_value = [
        f"{start_time.isoformat()}:0.5",
        f"{end_time.isoformat()}:0.7"
    ]
    
    metrics = await monitor.get_metrics(
        "response_time",
        start_time,
        end_time
    )
    
    assert len(metrics) == 2
    assert metrics[0].value == 0.5
    assert metrics[1].value == 0.7

@pytest.mark.asyncio
async def test_monitor_performance_decorator(monitor):
    """Test performance monitoring decorator."""
    @monitor.monitor_performance()
    async def test_func():
        return "success"
    
    result = await test_func()
    
    assert result == "success"
    assert monitor.redis.zadd.call_count >= 3  # response_time, memory, cpu

@pytest.mark.asyncio
async def test_monitor_performance_with_error(monitor):
    """Test performance monitoring with error."""
    @monitor.monitor_performance()
    async def test_func():
        raise ValueError("Test error")
    
    with pytest.raises(ValueError):
        await test_func()
    
    assert monitor.redis.zadd.call_count >= 4  # response_time, error, memory, cpu

@pytest.mark.asyncio
async def test_get_performance_summary(monitor):
    """Test getting performance summary."""
    # Mock metrics
    monitor.get_metrics = AsyncMock(return_value=[
        MetricPoint(datetime.now(), 0.5),
        MetricPoint(datetime.now(), 0.7)
    ])
    
    summary = await monitor.get_performance_summary()
    
    assert "requests" in summary
    assert "system" in summary
    assert summary["requests"]["avg_response_time"] == 0.6