"""
Sprint 25: Performance Monitoring Middleware

Middleware for:
- Request timing
- Query counting
- Rate limiting
- Performance headers
"""

import time
import logging
from django.conf import settings
from django.http import JsonResponse
from django.db import connection, reset_queries

logger = logging.getLogger(__name__)


class PerformanceMiddleware:
    """
    Middleware to track request performance.
    
    Adds headers:
    - X-Request-Time: Total request time in ms
    - X-Query-Count: Number of database queries
    - X-Cache-Status: Cache hit/miss status
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Start timing
        start_time = time.time()
        
        # Reset query log if in debug mode
        if settings.DEBUG:
            reset_queries()
        
        # Process request
        response = self.get_response(request)
        
        # Calculate elapsed time
        elapsed_ms = (time.time() - start_time) * 1000
        
        # Add performance headers
        response['X-Request-Time'] = f"{elapsed_ms:.2f}ms"
        
        if settings.DEBUG:
            query_count = len(connection.queries)
            response['X-Query-Count'] = str(query_count)
            
            if query_count > 10:
                logger.warning(
                    f"High query count ({query_count}) for {request.method} {request.path}"
                )
        
        # Log slow requests
        if elapsed_ms > 1000:  # > 1 second
            logger.warning(
                f"Slow request: {request.method} {request.path} took {elapsed_ms:.2f}ms"
            )
        
        return response


class RateLimitMiddleware:
    """
    Simple rate limiting middleware.
    
    Limits requests per IP address within a time window.
    """
    
    # In-memory store (use Redis in production)
    _requests = {}
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.limit = getattr(settings, 'RATE_LIMIT_REQUESTS', 100)
        self.window = getattr(settings, 'RATE_LIMIT_WINDOW', 60)  # seconds
    
    def __call__(self, request):
        # Skip rate limiting for certain paths
        if request.path.startswith('/admin/'):
            return self.get_response(request)
        
        # Get client IP
        ip = self._get_client_ip(request)
        
        # Check rate limit
        if not self._check_rate_limit(ip):
            return JsonResponse(
                {
                    "error": "Rate limit exceeded",
                    "retry_after": self.window
                },
                status=429
            )
        
        response = self.get_response(request)
        
        # Add rate limit headers
        remaining = self.limit - self._get_request_count(ip)
        response['X-RateLimit-Limit'] = str(self.limit)
        response['X-RateLimit-Remaining'] = str(max(0, remaining))
        response['X-RateLimit-Reset'] = str(int(time.time()) + self.window)
        
        return response
    
    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR', 'unknown')
    
    def _check_rate_limit(self, ip: str) -> bool:
        current_time = time.time()
        
        # Initialize or clean up old entries
        if ip not in self._requests:
            self._requests[ip] = []
        
        # Remove old requests outside the window
        self._requests[ip] = [
            t for t in self._requests[ip]
            if current_time - t < self.window
        ]
        
        # Check if under limit
        if len(self._requests[ip]) >= self.limit:
            return False
        
        # Record this request
        self._requests[ip].append(current_time)
        return True
    
    def _get_request_count(self, ip: str) -> int:
        return len(self._requests.get(ip, []))


class CompressionMiddleware:
    """
    Middleware to ensure proper compression headers.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Add Vary header for proper caching
        if 'Vary' not in response:
            response['Vary'] = 'Accept-Encoding'
        
        return response


class CacheControlMiddleware:
    """
    Adds Cache-Control headers based on response type.
    """
    
    # Cache durations by path prefix
    CACHE_RULES = {
        '/api/v1/terminology/': 86400,      # 24 hours
        '/api/v1/patients/': 0,             # No cache
        '/api/v1/observations/': 60,        # 1 minute
        '/static/': 604800,                 # 1 week
    }
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Don't cache errors
        if response.status_code >= 400:
            response['Cache-Control'] = 'no-store'
            return response
        
        # Apply cache rules
        for path_prefix, max_age in self.CACHE_RULES.items():
            if request.path.startswith(path_prefix):
                if max_age > 0:
                    response['Cache-Control'] = f'public, max-age={max_age}'
                else:
                    response['Cache-Control'] = 'no-store'
                break
        
        return response


class ETaggerMiddleware:
    """
    Adds ETag headers for conditional requests.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Only for successful GET requests
        if request.method != 'GET' or response.status_code != 200:
            return response
        
        # Generate ETag from content
        if hasattr(response, 'content'):
            import hashlib
            content_hash = hashlib.md5(response.content).hexdigest()
            etag = f'"{content_hash}"'
            
            response['ETag'] = etag
            
            # Check If-None-Match
            if_none_match = request.META.get('HTTP_IF_NONE_MATCH')
            if if_none_match == etag:
                response.status_code = 304
                response.content = b''
        
        return response
