"""
Rate Limiting Middleware for OpenEHRCore API

Implements rate limiting to protect against abuse and ensure fair usage.
Uses in-memory storage (for development) or Redis (for production).
"""
import time
import logging
from collections import defaultdict
from functools import wraps
from django.http import JsonResponse
from django.conf import settings

logger = logging.getLogger(__name__)


class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded"""
    pass


class InMemoryRateLimiter:
    """
    Simple in-memory rate limiter for development.
    For production, use Redis-based implementation.
    """
    def __init__(self):
        self.requests = defaultdict(list)
        self.cleanup_interval = 60  # seconds
        self.last_cleanup = time.time()
    
    def _cleanup(self):
        """Remove expired entries"""
        now = time.time()
        if now - self.last_cleanup < self.cleanup_interval:
            return
        
        cutoff = now - 3600  # Keep last hour
        for key in list(self.requests.keys()):
            self.requests[key] = [t for t in self.requests[key] if t > cutoff]
            if not self.requests[key]:
                del self.requests[key]
        
        self.last_cleanup = now
    
    def is_rate_limited(self, key: str, limit: int, period: int) -> tuple:
        """
        Check if request should be rate limited
        
        Args:
            key: Unique identifier (user_id, IP, etc)
            limit: Max requests allowed
            period: Time window in seconds
        
        Returns:
            (is_limited, remaining, reset_time)
        """
        self._cleanup()
        
        now = time.time()
        window_start = now - period
        
        # Get requests in current window
        self.requests[key] = [t for t in self.requests[key] if t > window_start]
        current_count = len(self.requests[key])
        
        if current_count >= limit:
            # Calculate reset time
            oldest = min(self.requests[key]) if self.requests[key] else now
            reset_time = int(oldest + period - now)
            return True, 0, reset_time
        
        # Record this request
        self.requests[key].append(now)
        remaining = limit - current_count - 1
        reset_time = int(period)
        
        return False, remaining, reset_time


# Global rate limiter instance
_rate_limiter = InMemoryRateLimiter()


# Rate limit configurations per endpoint type
RATE_LIMITS = {
    'default': {'limit': 100, 'period': 60},      # 100 req/min
    'auth': {'limit': 10, 'period': 60},          # 10 req/min for auth
    'search': {'limit': 30, 'period': 60},        # 30 req/min for searches
    'export': {'limit': 5, 'period': 300},        # 5 req/5min for exports
    'ai': {'limit': 10, 'period': 60},            # 10 req/min for AI
    'write': {'limit': 50, 'period': 60},         # 50 req/min for writes
}


def get_client_key(request):
    """Get unique identifier for rate limiting"""
    # Try to get user ID first
    if hasattr(request, 'user') and hasattr(request.user, 'id'):
        return f"user:{request.user.id}"
    
    # Fall back to IP address
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', 'unknown')
    
    return f"ip:{ip}"


def get_endpoint_type(request):
    """Determine endpoint type for rate limit selection"""
    path = request.path.lower()
    method = request.method
    
    if '/auth/' in path or '/login' in path:
        return 'auth'
    if '/search' in path or method == 'GET' and '_search' in path:
        return 'search'
    if '/export' in path or '/download' in path:
        return 'export'
    if '/ai/' in path or '/summary' in path:
        return 'ai'
    if method in ('POST', 'PUT', 'PATCH', 'DELETE'):
        return 'write'
    
    return 'default'


class RateLimitMiddleware:
    """
    Django middleware for rate limiting
    
    Add to MIDDLEWARE in settings.py:
    'fhir_api.middleware.rate_limit.RateLimitMiddleware'
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.enabled = getattr(settings, 'RATE_LIMIT_ENABLED', True)
    
    def __call__(self, request):
        # Skip if disabled
        if not self.enabled:
            return self.get_response(request)
        
        # Skip for health checks
        if '/health' in request.path:
            return self.get_response(request)
        
        # Get rate limit config
        endpoint_type = get_endpoint_type(request)
        config = RATE_LIMITS.get(endpoint_type, RATE_LIMITS['default'])
        
        # Check rate limit
        client_key = get_client_key(request)
        rate_key = f"{client_key}:{endpoint_type}"
        
        is_limited, remaining, reset_time = _rate_limiter.is_rate_limited(
            rate_key, config['limit'], config['period']
        )
        
        if is_limited:
            logger.warning(f"Rate limit exceeded for {client_key} on {endpoint_type}")
            return JsonResponse({
                'error': 'Rate limit exceeded',
                'message': 'Muitas requisições. Tente novamente em alguns segundos.',
                'retry_after': reset_time
            }, status=429)
        
        # Add rate limit headers to response
        response = self.get_response(request)
        response['X-RateLimit-Limit'] = config['limit']
        response['X-RateLimit-Remaining'] = remaining
        response['X-RateLimit-Reset'] = reset_time
        
        return response


def rate_limit(limit: int = None, period: int = None, endpoint_type: str = 'default'):
    """
    Decorator for rate limiting specific views
    
    @rate_limit(limit=5, period=60)
    def my_view(request):
        ...
    
    Or use predefined type:
    @rate_limit(endpoint_type='export')
    def export_view(request):
        ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Get config
            if limit and period:
                config = {'limit': limit, 'period': period}
            else:
                config = RATE_LIMITS.get(endpoint_type, RATE_LIMITS['default'])
            
            # Check rate limit
            client_key = get_client_key(request)
            rate_key = f"{client_key}:{view_func.__name__}"
            
            is_limited, remaining, reset_time = _rate_limiter.is_rate_limited(
                rate_key, config['limit'], config['period']
            )
            
            if is_limited:
                return JsonResponse({
                    'error': 'Rate limit exceeded',
                    'message': 'Limite de requisições excedido',
                    'retry_after': reset_time
                }, status=429)
            
            response = view_func(request, *args, **kwargs)
            
            # Add headers if it's a Django response
            if hasattr(response, '__setitem__'):
                response['X-RateLimit-Limit'] = config['limit']
                response['X-RateLimit-Remaining'] = remaining
                response['X-RateLimit-Reset'] = reset_time
            
            return response
        return wrapper
    return decorator


# Utility to manually check/reset rate limits
def check_rate_limit(key: str, endpoint_type: str = 'default') -> dict:
    """Check current rate limit status for a key"""
    config = RATE_LIMITS.get(endpoint_type, RATE_LIMITS['default'])
    is_limited, remaining, reset_time = _rate_limiter.is_rate_limited(
        f"{key}:{endpoint_type}",
        config['limit'],
        config['period']
    )
    return {
        'is_limited': is_limited,
        'remaining': remaining,
        'reset_in_seconds': reset_time,
        'limit': config['limit'],
        'period': config['period']
    }


def reset_rate_limit(key: str):
    """Reset rate limit for a specific key"""
    keys_to_remove = [k for k in _rate_limiter.requests.keys() if key in k]
    for k in keys_to_remove:
        del _rate_limiter.requests[k]
    logger.info(f"Rate limit reset for key: {key}")
