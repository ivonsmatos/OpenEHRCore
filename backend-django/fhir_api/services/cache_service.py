"""
Sprint 25: Redis Cache Service

High-performance caching layer for FHIR resources and API responses.
Uses Redis for distributed caching with support for:
- Resource caching
- Query result caching
- Session caching
- Rate limiting
"""

import json
import hashlib
import logging
from datetime import timedelta
from typing import Any, Dict, List, Optional, Callable, TypeVar
from functools import wraps
from django.conf import settings

logger = logging.getLogger(__name__)

# Try to import redis, fall back to in-memory cache
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not available, using in-memory cache fallback")


T = TypeVar('T')


class CacheBackend:
    """Abstract cache backend interface."""
    
    def get(self, key: str) -> Optional[str]:
        raise NotImplementedError
    
    def set(self, key: str, value: str, ttl: Optional[int] = None) -> bool:
        raise NotImplementedError
    
    def delete(self, key: str) -> bool:
        raise NotImplementedError
    
    def exists(self, key: str) -> bool:
        raise NotImplementedError
    
    def clear_pattern(self, pattern: str) -> int:
        raise NotImplementedError
    
    def incr(self, key: str) -> int:
        raise NotImplementedError


class InMemoryCache(CacheBackend):
    """In-memory cache fallback when Redis is not available."""
    
    _cache: Dict[str, tuple] = {}  # key -> (value, expiry_time)
    
    def __init__(self):
        import time
        self._time = time
    
    def _cleanup(self):
        """Remove expired entries."""
        now = self._time.time()
        expired = [k for k, (_, exp) in self._cache.items() if exp and exp < now]
        for k in expired:
            del self._cache[k]
    
    def get(self, key: str) -> Optional[str]:
        self._cleanup()
        if key in self._cache:
            value, expiry = self._cache[key]
            if expiry is None or expiry > self._time.time():
                return value
            del self._cache[key]
        return None
    
    def set(self, key: str, value: str, ttl: Optional[int] = None) -> bool:
        expiry = self._time.time() + ttl if ttl else None
        self._cache[key] = (value, expiry)
        return True
    
    def delete(self, key: str) -> bool:
        if key in self._cache:
            del self._cache[key]
            return True
        return False
    
    def exists(self, key: str) -> bool:
        return self.get(key) is not None
    
    def clear_pattern(self, pattern: str) -> int:
        import fnmatch
        keys = [k for k in self._cache.keys() if fnmatch.fnmatch(k, pattern)]
        for k in keys:
            del self._cache[k]
        return len(keys)
    
    def incr(self, key: str) -> int:
        value = self.get(key)
        new_value = int(value or 0) + 1
        self.set(key, str(new_value), ttl=60)
        return new_value


class RedisCache(CacheBackend):
    """Redis-based cache backend."""
    
    def __init__(self, url: str = None, **kwargs):
        self.url = url or getattr(settings, 'REDIS_URL', 'redis://localhost:6379/0')
        self.client = redis.from_url(self.url, decode_responses=True, **kwargs)
        logger.info(f"Redis cache connected: {self.url}")
    
    def get(self, key: str) -> Optional[str]:
        try:
            return self.client.get(key)
        except redis.RedisError as e:
            logger.error(f"Redis GET error: {e}")
            return None
    
    def set(self, key: str, value: str, ttl: Optional[int] = None) -> bool:
        try:
            if ttl:
                return self.client.setex(key, ttl, value)
            return self.client.set(key, value)
        except redis.RedisError as e:
            logger.error(f"Redis SET error: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        try:
            return self.client.delete(key) > 0
        except redis.RedisError as e:
            logger.error(f"Redis DELETE error: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        try:
            return self.client.exists(key) > 0
        except redis.RedisError as e:
            logger.error(f"Redis EXISTS error: {e}")
            return False
    
    def clear_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern."""
        try:
            keys = list(self.client.scan_iter(pattern))
            if keys:
                return self.client.delete(*keys)
            return 0
        except redis.RedisError as e:
            logger.error(f"Redis CLEAR_PATTERN error: {e}")
            return 0
    
    def incr(self, key: str) -> int:
        try:
            return self.client.incr(key)
        except redis.RedisError as e:
            logger.error(f"Redis INCR error: {e}")
            return 0
    
    def pipeline(self):
        """Get a pipeline for batch operations."""
        return self.client.pipeline()


class CacheService:
    """
    High-level caching service for FHIR resources.
    
    Provides:
    - Resource caching with automatic invalidation
    - Query result caching
    - Cache key generation
    - TTL management
    """
    
    # Default TTL values (in seconds)
    TTL_SHORT = 60          # 1 minute
    TTL_MEDIUM = 300        # 5 minutes
    TTL_LONG = 3600         # 1 hour
    TTL_VERY_LONG = 86400   # 24 hours
    
    # Cache key prefixes
    PREFIX_RESOURCE = "fhir:resource"
    PREFIX_SEARCH = "fhir:search"
    PREFIX_PATIENT = "fhir:patient"
    PREFIX_TERMINOLOGY = "term"
    PREFIX_RATE_LIMIT = "rate"
    
    _instance: Optional['CacheService'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        if REDIS_AVAILABLE and getattr(settings, 'USE_REDIS_CACHE', False):
            try:
                self.backend = RedisCache()
            except Exception as e:
                logger.warning(f"Failed to connect to Redis: {e}, using in-memory cache")
                self.backend = InMemoryCache()
        else:
            self.backend = InMemoryCache()
        
        self._initialized = True
    
    @staticmethod
    def generate_key(*args, **kwargs) -> str:
        """Generate a cache key from arguments."""
        key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True)
        return hashlib.md5(key_data.encode()).hexdigest()[:16]
    
    # =========================================================================
    # Resource Caching
    # =========================================================================
    
    def get_resource(self, resource_type: str, resource_id: str) -> Optional[Dict]:
        """Get a cached FHIR resource."""
        key = f"{self.PREFIX_RESOURCE}:{resource_type}:{resource_id}"
        data = self.backend.get(key)
        if data:
            logger.debug(f"Cache HIT: {key}")
            return json.loads(data)
        logger.debug(f"Cache MISS: {key}")
        return None
    
    def set_resource(self, resource_type: str, resource_id: str, resource: Dict, ttl: int = None) -> bool:
        """Cache a FHIR resource."""
        key = f"{self.PREFIX_RESOURCE}:{resource_type}:{resource_id}"
        ttl = ttl or self.TTL_MEDIUM
        return self.backend.set(key, json.dumps(resource), ttl)
    
    def invalidate_resource(self, resource_type: str, resource_id: str) -> bool:
        """Invalidate a cached resource."""
        key = f"{self.PREFIX_RESOURCE}:{resource_type}:{resource_id}"
        # Also invalidate related search results
        self.invalidate_search(resource_type)
        return self.backend.delete(key)
    
    # =========================================================================
    # Search Result Caching
    # =========================================================================
    
    def get_search(self, resource_type: str, params: Dict) -> Optional[List]:
        """Get cached search results."""
        params_hash = self.generate_key(**params)
        key = f"{self.PREFIX_SEARCH}:{resource_type}:{params_hash}"
        data = self.backend.get(key)
        if data:
            logger.debug(f"Search cache HIT: {resource_type}")
            return json.loads(data)
        return None
    
    def set_search(self, resource_type: str, params: Dict, results: List, ttl: int = None) -> bool:
        """Cache search results."""
        params_hash = self.generate_key(**params)
        key = f"{self.PREFIX_SEARCH}:{resource_type}:{params_hash}"
        ttl = ttl or self.TTL_SHORT
        return self.backend.set(key, json.dumps(results), ttl)
    
    def invalidate_search(self, resource_type: str) -> int:
        """Invalidate all cached searches for a resource type."""
        pattern = f"{self.PREFIX_SEARCH}:{resource_type}:*"
        return self.backend.clear_pattern(pattern)
    
    # =========================================================================
    # Patient-Centric Caching
    # =========================================================================
    
    def get_patient_data(self, patient_id: str, data_type: str) -> Optional[Any]:
        """Get cached patient-related data."""
        key = f"{self.PREFIX_PATIENT}:{patient_id}:{data_type}"
        data = self.backend.get(key)
        return json.loads(data) if data else None
    
    def set_patient_data(self, patient_id: str, data_type: str, data: Any, ttl: int = None) -> bool:
        """Cache patient-related data."""
        key = f"{self.PREFIX_PATIENT}:{patient_id}:{data_type}"
        ttl = ttl or self.TTL_MEDIUM
        return self.backend.set(key, json.dumps(data), ttl)
    
    def invalidate_patient(self, patient_id: str) -> int:
        """Invalidate all cached data for a patient."""
        pattern = f"{self.PREFIX_PATIENT}:{patient_id}:*"
        count = self.backend.clear_pattern(pattern)
        # Also invalidate patient resource
        self.invalidate_resource("Patient", patient_id)
        return count
    
    # =========================================================================
    # Terminology Caching
    # =========================================================================
    
    def get_terminology(self, system: str, code: str) -> Optional[Dict]:
        """Get cached terminology lookup."""
        key = f"{self.PREFIX_TERMINOLOGY}:{system}:{code}"
        data = self.backend.get(key)
        return json.loads(data) if data else None
    
    def set_terminology(self, system: str, code: str, data: Dict, ttl: int = None) -> bool:
        """Cache terminology lookup result."""
        key = f"{self.PREFIX_TERMINOLOGY}:{system}:{code}"
        ttl = ttl or self.TTL_VERY_LONG  # Terminology is stable
        return self.backend.set(key, json.dumps(data), ttl)
    
    # =========================================================================
    # Rate Limiting
    # =========================================================================
    
    def check_rate_limit(self, key_id: str, limit: int, window_seconds: int = 60) -> bool:
        """
        Check if request is within rate limit.
        
        Returns True if request is allowed, False if rate limited.
        """
        key = f"{self.PREFIX_RATE_LIMIT}:{key_id}"
        count = self.backend.incr(key)
        
        if count == 1:
            # First request, set expiry
            if isinstance(self.backend, RedisCache):
                self.backend.client.expire(key, window_seconds)
        
        return count <= limit
    
    # =========================================================================
    # Cache Decorator
    # =========================================================================
    
    def cached(self, ttl: int = None, key_prefix: str = "cache"):
        """
        Decorator to cache function results.
        
        Usage:
            @cache_service.cached(ttl=300, key_prefix="my_func")
            def my_expensive_function(arg1, arg2):
                ...
        """
        def decorator(func: Callable[..., T]) -> Callable[..., T]:
            @wraps(func)
            def wrapper(*args, **kwargs) -> T:
                cache_key = f"{key_prefix}:{func.__name__}:{self.generate_key(*args, **kwargs)}"
                
                # Try to get from cache
                cached = self.backend.get(cache_key)
                if cached:
                    return json.loads(cached)
                
                # Execute function
                result = func(*args, **kwargs)
                
                # Store in cache
                self.backend.set(cache_key, json.dumps(result), ttl or self.TTL_MEDIUM)
                
                return result
            return wrapper
        return decorator
    
    # =========================================================================
    # Statistics
    # =========================================================================
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics (Redis only)."""
        if isinstance(self.backend, RedisCache):
            try:
                info = self.backend.client.info()
                return {
                    "backend": "redis",
                    "connected": True,
                    "memory_used": info.get("used_memory_human"),
                    "total_keys": self.backend.client.dbsize(),
                    "hits": info.get("keyspace_hits", 0),
                    "misses": info.get("keyspace_misses", 0),
                    "hit_rate": round(
                        info.get("keyspace_hits", 0) / 
                        max(info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0), 1) * 100,
                        2
                    )
                }
            except Exception as e:
                return {"backend": "redis", "connected": False, "error": str(e)}
        else:
            return {
                "backend": "in-memory",
                "total_keys": len(self.backend._cache)
            }


# Singleton instance
cache_service = CacheService()


# Convenience functions
def get_cache() -> CacheService:
    """Get the cache service instance."""
    return cache_service


def cached(ttl: int = None, key_prefix: str = "cache"):
    """Decorator shortcut for caching."""
    return cache_service.cached(ttl, key_prefix)
