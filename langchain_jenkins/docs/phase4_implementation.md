# Phase 4: Performance Monitoring and Rate Limiting

## Overview
Phase 4 adds performance monitoring, rate limiting, and optimizations to the LangChain Jenkins Agent system.

## New Components

### 1. Performance Monitoring
#### Monitoring Module (`monitoring.py`)
- Response time tracking
- Error rate monitoring
- System metrics collection
- Performance analysis

#### Features
- Metric collection
- Performance analysis
- System monitoring
- Historical data

### 2. Rate Limiting
#### Rate Limit Module (`rate_limit.py`)
- Redis-based rate limiting
- API endpoint limits
- Burst handling
- Retry mechanisms

#### Features
- Request throttling
- Burst allowance
- Rate limit configuration
- API endpoint limits

## Implementation Details

### Performance Monitoring
1. **Metric Collection**
   ```python
   @monitor.monitor_performance()
   async def monitored_function():
       # Function is monitored for:
       # - Response time
       # - Error rate
       # - Memory usage
       # - CPU usage
       pass
   ```

2. **Performance Analysis**
   ```python
   # Get performance summary
   summary = await monitor.get_performance_summary()
   print(f"Average response time: {summary['requests']['avg_response_time']}")
   print(f"Error rate: {summary['requests']['error_rate']}")
   ```

3. **System Metrics**
   ```python
   # Record system metrics
   await monitor.record_metric(
       "memory_usage",
       process.memory_info().rss / 1024 / 1024
   )
   ```

### Rate Limiting
1. **Basic Rate Limiting**
   ```python
   @rate_limiter.rate_limit("api", RateLimitConfig(
       requests=60,
       period=60,
       burst=10
   ))
   async def rate_limited_function():
       pass
   ```

2. **API Rate Limiting**
   ```python
   @api_rate_limiter.limit_api("builds")
   async def build_function():
       # Limited to 10 requests per minute
       pass
   ```

3. **Burst Handling**
   ```python
   # Configure burst allowance
   config = RateLimitConfig(
       requests=60,
       period=60,
       burst=10  # Allow 10 extra requests
   )
   ```

## Usage Examples

### Performance Monitoring
```python
from langchain_jenkins.utils.monitoring import monitor

# Monitor a function
@monitor.monitor_performance()
async def my_function():
    pass

# Get performance metrics
metrics = await monitor.get_metrics("response_time")
summary = await monitor.get_performance_summary()
```

### Rate Limiting
```python
from langchain_jenkins.utils.rate_limit import rate_limiter, api_rate_limiter

# Basic rate limiting
@rate_limiter.rate_limit("my_function")
async def my_function():
    pass

# API rate limiting
@api_rate_limiter.limit_api("builds")
async def build_function():
    pass
```

## Configuration

### Performance Monitoring
```python
# Metric retention
METRIC_RETENTION = 24 * 60 * 60  # 24 hours

# System metrics
SYSTEM_METRIC_INTERVAL = 60  # 1 minute
```

### Rate Limiting
```python
# Default rate limits
DEFAULT_RATE_LIMIT = RateLimitConfig(
    requests=60,
    period=60,
    burst=10
)

# API endpoint limits
API_RATE_LIMITS = {
    "builds": RateLimitConfig(requests=10, period=60),
    "plugins": RateLimitConfig(requests=30, period=60),
    "users": RateLimitConfig(requests=20, period=60)
}
```

## Testing
```python
# Test monitoring
@pytest.mark.asyncio
async def test_monitor_performance():
    @monitor.monitor_performance()
    async def test_func():
        return "success"
    
    result = await test_func()
    assert result == "success"

# Test rate limiting
@pytest.mark.asyncio
async def test_rate_limit():
    @rate_limiter.rate_limit("test")
    async def test_func():
        return "success"
    
    result = await test_func()
    assert result == "success"
```

## Next Steps
1. Add more performance metrics
2. Implement adaptive rate limiting
3. Add metric visualization
4. Enhance monitoring alerts
5. Improve burst handling