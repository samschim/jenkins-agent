"""Rate limiting utilities."""
import time
import asyncio
import logging
from typing import Dict, Optional, Callable, Any
from dataclasses import dataclass
import redis.asyncio as redis
from ..config.config import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class RateLimitConfig:
    """Rate limit configuration."""
    requests: int  # Number of requests
    period: int   # Time period in seconds
    burst: Optional[int] = None  # Burst size (optional)

class RateLimiter:
    """Rate limiter using Redis."""
    
    def __init__(self):
        """Initialize rate limiter."""
        self.redis = redis.from_url(config.redis_url)
        self.default_config = RateLimitConfig(
            requests=60,    # 60 requests
            period=60,      # per minute
            burst=10        # allow 10 extra requests
        )
    
    async def check_rate_limit(
        self,
        key: str,
        config: Optional[RateLimitConfig] = None
    ) -> bool:
        """Check if rate limit is exceeded.
        
        Args:
            key: Rate limit key
            config: Rate limit configuration
            
        Returns:
            True if rate limit is not exceeded, False otherwise
        """
        config = config or self.default_config
        now = time.time()
        
        # Create a pipeline
        pipe = self.redis.pipeline()
        
        # Remove old entries
        pipe.zremrangebyscore(
            f"ratelimit:{key}",
            "-inf",
            now - config.period
        )
        
        # Count recent requests
        pipe.zcard(f"ratelimit:{key}")
        
        # Add current request
        pipe.zadd(f"ratelimit:{key}", {str(now): now})
        
        # Execute pipeline
        results = await pipe.execute()
        count = results[1]
        
        # Check if limit is exceeded
        limit = config.requests
        if config.burst:
            limit += config.burst
        
        return count <= limit
    
    async def get_retry_after(
        self,
        key: str,
        config: Optional[RateLimitConfig] = None
    ) -> float:
        """Get time until rate limit resets.
        
        Args:
            key: Rate limit key
            config: Rate limit configuration
            
        Returns:
            Seconds until rate limit resets
        """
        config = config or self.default_config
        now = time.time()
        
        # Get oldest request timestamp
        oldest = await self.redis.zrange(
            f"ratelimit:{key}",
            0,
            0,
            withscores=True
        )
        
        if not oldest:
            return 0
        
        oldest_time = oldest[0][1]
        return max(0, config.period - (now - oldest_time))
    
    def rate_limit(
        self,
        key: str,
        config: Optional[RateLimitConfig] = None
    ) -> Callable:
        """Decorator for rate limiting functions.
        
        Args:
            key: Rate limit key
            config: Rate limit configuration
            
        Returns:
            Decorated function
        """
        def decorator(func: Callable) -> Callable:
            async def wrapper(*args: Any, **kwargs: Any) -> Any:
                # Check rate limit
                if not await self.check_rate_limit(key, config):
                    retry_after = await self.get_retry_after(key, config)
                    logger.warning(
                        "Rate limit exceeded for %s. Retry after %.1f seconds",
                        key,
                        retry_after
                    )
                    
                    # Wait if burst is allowed
                    if config and config.burst:
                        await asyncio.sleep(retry_after)
                    else:
                        raise Exception(
                            f"Rate limit exceeded. Retry after {retry_after:.1f} seconds"
                        )
                
                return await func(*args, **kwargs)
            return wrapper
        return decorator

# Global rate limiter instance
rate_limiter = RateLimiter()

class APIRateLimiter:
    """Rate limiter for API endpoints."""
    
    def __init__(self):
        """Initialize API rate limiter."""
        self.limiters: Dict[str, RateLimitConfig] = {
            "default": RateLimitConfig(
                requests=60,
                period=60,
                burst=10
            ),
            "builds": RateLimitConfig(
                requests=10,
                period=60,
                burst=5
            ),
            "plugins": RateLimitConfig(
                requests=30,
                period=60,
                burst=5
            ),
            "users": RateLimitConfig(
                requests=20,
                period=60,
                burst=5
            )
        }
    
    def get_limiter(self, endpoint: str) -> RateLimitConfig:
        """Get rate limit configuration for endpoint.
        
        Args:
            endpoint: API endpoint
            
        Returns:
            Rate limit configuration
        """
        # Find matching limiter
        for key, config in self.limiters.items():
            if key in endpoint:
                return config
        
        # Return default limiter
        return self.limiters["default"]
    
    def limit_api(self, endpoint: str) -> Callable:
        """Decorator for rate limiting API endpoints.
        
        Args:
            endpoint: API endpoint
            
        Returns:
            Decorated function
        """
        config = self.get_limiter(endpoint)
        return rate_limiter.rate_limit(f"api:{endpoint}", config)

# Global API rate limiter instance
api_rate_limiter = APIRateLimiter()