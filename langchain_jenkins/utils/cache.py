"""Caching utilities for Jenkins API responses."""
import json
import hashlib
import asyncio
from typing import Any, Dict, Optional, Callable
from datetime import datetime, timedelta
import redis.asyncio as redis
from ..config.config import config

class CacheManager:
    """Manages caching of API responses using Redis."""
    
    def __init__(self):
        """Initialize cache manager with Redis connection."""
        self.redis = redis.from_url(config.redis_url)
        self.default_ttl = 300  # 5 minutes default TTL
    
    def _generate_key(self, prefix: str, *args: Any, **kwargs: Any) -> str:
        """Generate a cache key from prefix and arguments.
        
        Args:
            prefix: Key prefix (e.g., 'jenkins:job')
            *args: Positional arguments to include in key
            **kwargs: Keyword arguments to include in key
            
        Returns:
            Cache key string
        """
        # Create a string representation of args and kwargs
        key_parts = [prefix]
        if args:
            key_parts.append(":".join(str(arg) for arg in args))
        if kwargs:
            key_parts.append(
                ":".join(f"{k}={v}" for k, v in sorted(kwargs.items()))
            )
        
        # Create a hash of the key parts
        key_str = ":".join(key_parts)
        key_hash = hashlib.md5(key_str.encode()).hexdigest()
        
        return f"jenkins:{prefix}:{key_hash}"
    
    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get a value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        value = await self.redis.get(key)
        if value:
            return json.loads(value)
        return None
    
    async def set(
        self,
        key: str,
        value: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> None:
        """Set a value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (optional)
        """
        await self.redis.set(
            key,
            json.dumps(value),
            ex=ttl or self.default_ttl
        )
    
    async def delete(self, key: str) -> None:
        """Delete a value from cache.
        
        Args:
            key: Cache key to delete
        """
        await self.redis.delete(key)
    
    async def clear_pattern(self, pattern: str) -> None:
        """Clear all keys matching a pattern.
        
        Args:
            pattern: Key pattern to match
        """
        keys = await self.redis.keys(f"jenkins:{pattern}:*")
        if keys:
            await self.redis.delete(*keys)
    
    def cached(
        self,
        prefix: str,
        ttl: Optional[int] = None
    ) -> Callable:
        """Decorator for caching function results.
        
        Args:
            prefix: Cache key prefix
            ttl: Time to live in seconds (optional)
            
        Returns:
            Decorated function
        """
        def decorator(func: Callable) -> Callable:
            async def wrapper(*args: Any, **kwargs: Any) -> Any:
                # Generate cache key
                cache_key = self._generate_key(prefix, *args, **kwargs)
                
                # Try to get from cache
                cached_value = await self.get(cache_key)
                if cached_value is not None:
                    return cached_value
                
                # Call the function
                result = await func(*args, **kwargs)
                
                # Cache the result
                await self.set(cache_key, result, ttl)
                
                return result
            return wrapper
        return decorator

# Global cache instance
cache = CacheManager()