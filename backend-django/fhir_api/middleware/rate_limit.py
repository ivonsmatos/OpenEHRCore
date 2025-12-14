"""
Rate Limiting Middleware for HealthStack

Implements request rate limiting to prevent API abuse.
Supports different limits for different endpoint types.

ISO 27001 / OWASP Security Best Practice
"""

import time
import logging
from collections import defaultdict
from threading import Lock
from typing import Dict, Optional, Tuple
from django.http import JsonResponse
from django.conf import settings

logger = logging.getLogger(__name__)


class RateLimitConfig:
    """Rate limit configuration for different endpoint types."""
    
    # Requests per minute limits
    LIMITS = {
        'default': 60,           # 60 requests/minute for general endpoints
        'auth': 10,              # 10 requests/minute for auth endpoints (login, etc.)
        'bulk': 5,               # 5 requests/minute for bulk operations
        'export': 3,             # 3 requests/minute for export operations
        'ai': 20,                # 20 requests/minute for AI endpoints
        'search': 30,            # 30 requests/minute for search
        'webhook': 100,          # 100 requests/minute for webhooks
        'agent': 120,            # 120 requests/minute for agent communication
    }
    
    # Endpoint patterns to category mapping
    PATTERNS = {
        '/auth/': 'auth',
        '/login': 'auth',
        '/register': 'auth',
        '/token': 'auth',
        '/bulk-data/': 'bulk',
        '/export': 'export',
        '/ai/': 'ai',
        '/search': 'search',
        '/webhook': 'webhook',
        '/agent/': 'agent',
    }


class TokenBucket:
    """Token bucket algorithm for rate limiting."""
    
    def __init__(self, rate: int, capacity: int):
        self.rate = rate  # tokens per minute
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = time.time()
        self.lock = Lock()
    
    def consume(self, tokens: int = 1) -> bool:
        """Try to consume tokens. Returns True if successful."""
        with self.lock:
            now = time.time()
            elapsed = now - self.last_update
            
            # Add tokens based on elapsed time
            self.tokens = min(
                self.capacity,
                self.tokens + (elapsed * self.rate / 60)
            )
            self.last_update = now
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False
    
    def get_wait_time(self) -> float:
        """Get time to wait until next token available."""
        if self.tokens >= 1:
            return 0
        return ((1 - self.tokens) / self.rate) * 60


class RateLimiter:
    """Rate limiter using token bucket algorithm per client."""
    
    def __init__(self):
        self.buckets: Dict[str, Dict[str, TokenBucket]] = defaultdict(dict)
        self.lock = Lock()
    
    def get_bucket(self, client_id: str, category: str) -> TokenBucket:
        """Get or create a token bucket for a client/category combo."""
        with self.lock:
            if category not in self.buckets[client_id]:
                rate = RateLimitConfig.LIMITS.get(category, RateLimitConfig.LIMITS['default'])
                self.buckets[client_id][category] = TokenBucket(rate=rate, capacity=rate)
            return self.buckets[client_id][category]
    
    def is_allowed(self, client_id: str, category: str) -> Tuple[bool, float]:
        """Check if request is allowed. Returns (allowed, retry_after)."""
        bucket = self.get_bucket(client_id, category)
        if bucket.consume():
            return True, 0
        return False, bucket.get_wait_time()
    
    def cleanup_old_buckets(self, max_age: int = 3600):
        """Remove buckets that haven't been used in max_age seconds."""
        with self.lock:
            now = time.time()
            expired_clients = []
            
            for client_id, categories in self.buckets.items():
                all_expired = True
                for bucket in categories.values():
                    if now - bucket.last_update < max_age:
                        all_expired = False
                        break
                
                if all_expired:
                    expired_clients.append(client_id)
            
            for client_id in expired_clients:
                del self.buckets[client_id]


# Global rate limiter instance
_rate_limiter = RateLimiter()


class RateLimitMiddleware:
    """
    Django middleware for request rate limiting.
    
    Features:
    - Per-client rate limiting using IP or user ID
    - Different limits for different endpoint types
    - Token bucket algorithm for smooth rate limiting
    - Retry-After header in 429 responses
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.enabled = getattr(settings, 'RATE_LIMIT_ENABLED', True)
    
    def __call__(self, request):
        if not self.enabled:
            return self.get_response(request)
        
        # Skip rate limiting for certain paths
        if self._should_skip(request.path):
            return self.get_response(request)
        
        # Get client identifier
        client_id = self._get_client_id(request)
        
        # Get rate limit category
        category = self._get_category(request.path)
        
        # Check rate limit
        allowed, retry_after = _rate_limiter.is_allowed(client_id, category)
        
        if not allowed:
            logger.warning(
                f"Rate limit exceeded for client {client_id} on category {category}",
                extra={
                    'client_id': client_id,
                    'category': category,
                    'path': request.path,
                    'retry_after': retry_after
                }
            )
            
            return JsonResponse(
                {
                    'error': 'rate_limit_exceeded',
                    'message': 'Too many requests. Please try again later.',
                    'retry_after': round(retry_after, 1)
                },
                status=429,
                headers={'Retry-After': str(int(retry_after) + 1)}
            )
        
        # Add rate limit headers to response
        response = self.get_response(request)
        
        bucket = _rate_limiter.get_bucket(client_id, category)
        response['X-RateLimit-Limit'] = str(RateLimitConfig.LIMITS.get(category, 60))
        response['X-RateLimit-Remaining'] = str(int(bucket.tokens))
        response['X-RateLimit-Reset'] = str(int(time.time()) + 60)
        
        return response
    
    def _should_skip(self, path: str) -> bool:
        """Check if path should skip rate limiting."""
        skip_paths = [
            '/health',
            '/ready',
            '/metrics',
            '/static/',
            '/admin/',
        ]
        return any(path.startswith(p) for p in skip_paths)
    
    def _get_client_id(self, request) -> str:
        """Get unique client identifier."""
        # Try to get user ID first
        if hasattr(request, 'user') and request.user.is_authenticated:
            return f"user:{request.user.id}"
        
        # Fall back to IP address
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', 'unknown')
        
        return f"ip:{ip}"
    
    def _get_category(self, path: str) -> str:
        """Get rate limit category for a path."""
        for pattern, category in RateLimitConfig.PATTERNS.items():
            if pattern in path:
                return category
        return 'default'


def get_rate_limiter() -> RateLimiter:
    """Get the global rate limiter instance."""
    return _rate_limiter
