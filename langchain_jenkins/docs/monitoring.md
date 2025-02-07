# Monitoring System Documentation

## Overview
The monitoring system provides comprehensive monitoring and metrics collection for the LangChain Jenkins Agent system.

## Components

### 1. Performance Monitoring
- Response time tracking
- Error rate monitoring
- System metrics (CPU, memory)
- Historical data storage

### 2. Prometheus Integration
- Metrics exposition
- Time series data
- Alerting support
- Grafana compatibility

### 3. Redis Storage
- Metric persistence
- Time-based cleanup
- Fast retrieval
- Data aggregation

## Metrics

### Performance Metrics
1. **Response Time**
   ```python
   RESPONSE_TIME = Histogram(
       'jenkins_agent_response_time_seconds',
       'Response time in seconds',
       ['endpoint']
   )
   ```

2. **Request Count**
   ```python
   REQUESTS_TOTAL = Counter(
       'jenkins_agent_requests_total',
       'Total number of requests',
       ['endpoint', 'method', 'status']
   )
   ```

### System Metrics
1. **Memory Usage**
   ```python
   MEMORY_USAGE = Gauge(
       'jenkins_agent_memory_usage_bytes',
       'Memory usage in bytes'
   )
   ```

2. **CPU Usage**
   ```python
   CPU_USAGE = Gauge(
       'jenkins_agent_cpu_usage_percent',
       'CPU usage percentage'
   )
   ```

### Task Metrics
```python
ACTIVE_TASKS = Gauge(
    'jenkins_agent_active_tasks',
    'Number of active tasks'
)
```

## Usage

### Recording Metrics
```python
# Record response time
await monitor.record_metric(
    "response_time",
    duration,
    {"function": "my_function"}
)

# Record error
await monitor.record_metric(
    "error_rate",
    1.0,
    {
        "function": "my_function",
        "error_type": "ValueError"
    }
)
```

### Monitoring Decorator
```python
@monitor.monitor_performance()
async def my_function():
    # Function is automatically monitored
    pass
```

### Getting Metrics
```python
# Get performance summary
summary = await monitor.get_performance_summary()

# Get specific metrics
metrics = await monitor.get_metrics(
    "response_time",
    start_time=datetime.now() - timedelta(hours=1)
)
```

## Prometheus Integration

### Metrics Server
The Prometheus metrics server starts automatically on port 8000. You can access metrics at:
```
http://localhost:8000/metrics
```

### Metric Types
1. **Counter**: Cumulative values (e.g., total requests)
2. **Gauge**: Current values (e.g., memory usage)
3. **Histogram**: Distribution of values (e.g., response times)

### Labels
Metrics include labels for better categorization:
- endpoint: Function or API endpoint
- method: HTTP method
- status: Success/error status

## Redis Storage

### Data Structure
- Sorted sets for time-series data
- Key format: `metrics:{metric_type}`
- Value format: `{timestamp}:{value}`

### Retention
- 24-hour retention period
- Automatic cleanup of old metrics
- Configurable retention period

## Configuration

### Environment Variables
```bash
# Redis configuration
REDIS_URL=redis://localhost:6379

# Prometheus configuration
PROMETHEUS_PORT=8000
```

### Logging
```python
# Log level
LOG_LEVEL=INFO

# Log format
LOG_FORMAT='%(asctime)s [%(levelname)s] %(message)s'
```

## Monitoring Dashboard

### Grafana Setup
1. Add Prometheus data source:
   ```
   URL: http://localhost:8000
   Access: Browser
   ```

2. Import dashboard:
   - Response times panel
   - Error rates panel
   - System metrics panel
   - Active tasks panel

### Alerting
1. **Response Time Alerts**
   - Threshold: > 5s
   - Window: 5m

2. **Error Rate Alerts**
   - Threshold: > 5%
   - Window: 15m

3. **System Alerts**
   - Memory: > 80%
   - CPU: > 90%

## Best Practices

### Metric Naming
- Use snake_case
- Include unit in name
- Use descriptive prefixes

### Label Usage
- Keep cardinality low
- Use meaningful labels
- Avoid high-churn labels

### Performance
- Use batching for high-frequency metrics
- Set appropriate retention periods
- Monitor metric volume

## Next Steps
1. Add more system metrics
2. Implement metric aggregation
3. Create custom dashboards
4. Set up alerting rules
5. Add tracing support