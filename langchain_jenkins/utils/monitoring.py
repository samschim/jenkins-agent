"""Performance monitoring utilities."""
import time
import asyncio
import logging
import functools
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import psutil
import redis.asyncio as redis
from ..config.config import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class MetricPoint:
    """Single metric measurement point."""
    timestamp: datetime
    value: float
    labels: Dict[str, str] = field(default_factory=dict)

@dataclass
class PerformanceMetrics:
    """Collection of performance metrics."""
    response_times: List[MetricPoint] = field(default_factory=list)
    error_rates: List[MetricPoint] = field(default_factory=list)
    throughput: List[MetricPoint] = field(default_factory=list)
    memory_usage: List[MetricPoint] = field(default_factory=list)
    cpu_usage: List[MetricPoint] = field(default_factory=list)

class PerformanceMonitor:
    """Monitors and tracks performance metrics."""
    
    def __init__(self):
        """Initialize performance monitor."""
        self.redis = redis.from_url(config.redis_url)
        self.metrics = PerformanceMetrics()
        self.start_time = datetime.now()
    
    async def record_metric(
        self,
        metric_type: str,
        value: float,
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Record a metric measurement.
        
        Args:
            metric_type: Type of metric (e.g., 'response_time')
            value: Metric value
            labels: Additional metric labels
        """
        point = MetricPoint(
            timestamp=datetime.now(),
            value=value,
            labels=labels or {}
        )
        
        # Store in memory
        metric_list = getattr(self.metrics, f"{metric_type}s")
        metric_list.append(point)
        
        # Store in Redis
        await self.redis.zadd(
            f"metrics:{metric_type}",
            {
                f"{point.timestamp.isoformat()}:{value}": time.time()
            }
        )
        
        # Cleanup old metrics (keep last 24 hours)
        cleanup_threshold = time.time() - (24 * 60 * 60)
        await self.redis.zremrangebyscore(
            f"metrics:{metric_type}",
            "-inf",
            cleanup_threshold
        )
    
    async def get_metrics(
        self,
        metric_type: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[MetricPoint]:
        """Get metrics for a specific time range.
        
        Args:
            metric_type: Type of metric to retrieve
            start_time: Start of time range
            end_time: End of time range
            
        Returns:
            List of metric points
        """
        start_time = start_time or (datetime.now() - timedelta(hours=24))
        end_time = end_time or datetime.now()
        
        # Get from Redis
        metrics = await self.redis.zrangebyscore(
            f"metrics:{metric_type}",
            time.mktime(start_time.timetuple()),
            time.mktime(end_time.timetuple())
        )
        
        return [
            MetricPoint(
                timestamp=datetime.fromisoformat(m.split(":")[0]),
                value=float(m.split(":")[1])
            )
            for m in metrics
        ]
    
    def monitor_performance(self) -> Callable:
        """Decorator for monitoring function performance.
        
        Returns:
            Decorated function
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            async def wrapper(*args: Any, **kwargs: Any) -> Any:
                start_time = time.time()
                error = None
                
                try:
                    result = await func(*args, **kwargs)
                    return result
                except Exception as e:
                    error = e
                    raise
                finally:
                    end_time = time.time()
                    duration = end_time - start_time
                    
                    # Record response time
                    await self.record_metric(
                        "response_time",
                        duration,
                        {
                            "function": func.__name__,
                            "success": str(error is None)
                        }
                    )
                    
                    # Record error if any
                    if error:
                        await self.record_metric(
                            "error_rate",
                            1.0,
                            {
                                "function": func.__name__,
                                "error_type": type(error).__name__
                            }
                        )
                    
                    # Record system metrics
                    process = psutil.Process()
                    await self.record_metric(
                        "memory_usage",
                        process.memory_info().rss / 1024 / 1024,  # MB
                        {"function": func.__name__}
                    )
                    await self.record_metric(
                        "cpu_usage",
                        process.cpu_percent(),
                        {"function": func.__name__}
                    )
            return wrapper
        return decorator
    
    async def get_performance_summary(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get performance summary for a time range.
        
        Args:
            start_time: Start of time range
            end_time: End of time range
            
        Returns:
            Performance summary
        """
        start_time = start_time or (datetime.now() - timedelta(hours=24))
        end_time = end_time or datetime.now()
        
        # Get metrics
        response_times = await self.get_metrics(
            "response_time",
            start_time,
            end_time
        )
        error_rates = await self.get_metrics(
            "error_rate",
            start_time,
            end_time
        )
        memory_usage = await self.get_metrics(
            "memory_usage",
            start_time,
            end_time
        )
        cpu_usage = await self.get_metrics(
            "cpu_usage",
            start_time,
            end_time
        )
        
        # Calculate statistics
        total_requests = len(response_times)
        total_errors = len(error_rates)
        
        if total_requests > 0:
            avg_response_time = sum(m.value for m in response_times) / total_requests
            error_rate = total_errors / total_requests
        else:
            avg_response_time = 0.0
            error_rate = 0.0
        
        if memory_usage:
            avg_memory = sum(m.value for m in memory_usage) / len(memory_usage)
        else:
            avg_memory = 0.0
        
        if cpu_usage:
            avg_cpu = sum(m.value for m in cpu_usage) / len(cpu_usage)
        else:
            avg_cpu = 0.0
        
        return {
            "time_range": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat()
            },
            "requests": {
                "total": total_requests,
                "avg_response_time": avg_response_time,
                "error_rate": error_rate
            },
            "system": {
                "avg_memory_mb": avg_memory,
                "avg_cpu_percent": avg_cpu
            }
        }

# Global monitor instance
monitor = PerformanceMonitor()