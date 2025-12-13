"""
Rate Limiter Middleware - Proteção contra DDoS e abuso
Implementa throttling configurável por endpoint e usuário
"""

import time
import logging
from collections import defaultdict
from threading import Lock
from functools import wraps
from django.conf import settings
from django.http import JsonResponse
from rest_framework import status

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Rate limiter em memória com sliding window.
    Para produção, considerar Redis para distribuído.
    """
    
    def __init__(self):
        self.requests = defaultdict(list)
        self.lock = Lock()
        
        # Configurações padrão (requests por minuto)
        self.limits = {
            'default': 60,           # 60 req/min para usuários autenticados
            'anonymous': 20,         # 20 req/min para anônimos
            'auth': 10,              # 10 req/min para login (previne brute force)
            'bulk': 5,               # 5 req/min para operações bulk
            'ai': 10,                # 10 req/min para IA
            'export': 3,             # 3 req/min para exports
        }
        
        # Permite override via settings
        if hasattr(settings, 'RATE_LIMITS'):
            self.limits.update(settings.RATE_LIMITS)
    
    def get_client_id(self, request):
        """Identifica o cliente por IP ou usuário autenticado"""
        if hasattr(request, 'user') and request.user.is_authenticated:
            return f"user:{request.user.id}"
        
        # Usar X-Forwarded-For se existir (proxy reverso)
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', 'unknown')
        
        return f"ip:{ip}"
    
    def get_limit_category(self, path):
        """Determina categoria de limite baseado no path"""
        if '/auth/' in path or '/login' in path:
            return 'auth'
        elif '/bulk/' in path or '/export/' in path:
            return 'bulk'
        elif '/ai/' in path:
            return 'ai'
        elif '/export/' in path:
            return 'export'
        return 'default'
    
    def is_rate_limited(self, request):
        """
        Verifica se o request deve ser limitado.
        Retorna (is_limited, retry_after_seconds, limit_info)
        """
        client_id = self.get_client_id(request)
        category = self.get_limit_category(request.path)
        
        # Usar limite anônimo se não autenticado
        if client_id.startswith('ip:') and category == 'default':
            category = 'anonymous'
        
        limit = self.limits.get(category, self.limits['default'])
        window = 60  # 1 minuto
        
        key = f"{client_id}:{category}"
        now = time.time()
        
        with self.lock:
            # Limpar requests antigos
            self.requests[key] = [
                ts for ts in self.requests[key]
                if now - ts < window
            ]
            
            current_count = len(self.requests[key])
            
            if current_count >= limit:
                # Calcular tempo até próximo slot
                oldest = min(self.requests[key]) if self.requests[key] else now
                retry_after = int(window - (now - oldest)) + 1
                
                logger.warning(
                    f"Rate limit exceeded for {client_id} on {category}",
                    extra={
                        'client_id': client_id,
                        'category': category,
                        'limit': limit,
                        'current': current_count,
                        'path': request.path
                    }
                )
                
                return True, retry_after, {
                    'limit': limit,
                    'remaining': 0,
                    'reset': int(oldest + window)
                }
            
            # Registrar request
            self.requests[key].append(now)
            
            return False, 0, {
                'limit': limit,
                'remaining': limit - current_count - 1,
                'reset': int(now + window)
            }


# Instância global
rate_limiter = RateLimiter()


class RateLimitMiddleware:
    """
    Middleware Django para rate limiting.
    Adiciona headers X-RateLimit-* nas respostas.
    """
    
    # Paths que não devem ter rate limiting
    EXEMPT_PATHS = [
        '/api/v1/health/',
        '/api/v1/health/live/',
        '/api/v1/health/ready/',
        '/static/',
        '/media/',
    ]
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Verificar se path está isento
        if any(request.path.startswith(path) for path in self.EXEMPT_PATHS):
            return self.get_response(request)
        
        # Verificar rate limit
        is_limited, retry_after, limit_info = rate_limiter.is_rate_limited(request)
        
        if is_limited:
            response = JsonResponse({
                'error': 'Rate limit exceeded',
                'message': 'Muitas requisições. Tente novamente em alguns segundos.',
                'retry_after': retry_after
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)
            response['Retry-After'] = str(retry_after)
        else:
            response = self.get_response(request)
        
        # Adicionar headers de rate limit
        response['X-RateLimit-Limit'] = str(limit_info['limit'])
        response['X-RateLimit-Remaining'] = str(limit_info['remaining'])
        response['X-RateLimit-Reset'] = str(limit_info['reset'])
        
        return response


def rate_limit(category='default', limit=None):
    """
    Decorator para rate limiting em views específicas.
    
    @rate_limit(category='auth', limit=5)
    def login_view(request):
        ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Override temporário do limite se especificado
            original_limit = None
            if limit is not None:
                original_limit = rate_limiter.limits.get(category)
                rate_limiter.limits[category] = limit
            
            try:
                is_limited, retry_after, limit_info = rate_limiter.is_rate_limited(request)
                
                if is_limited:
                    return JsonResponse({
                        'error': 'Rate limit exceeded',
                        'message': 'Limite de requisições atingido.',
                        'retry_after': retry_after
                    }, status=status.HTTP_429_TOO_MANY_REQUESTS)
                
                return view_func(request, *args, **kwargs)
            finally:
                # Restaurar limite original
                if original_limit is not None:
                    rate_limiter.limits[category] = original_limit
        
        return wrapper
    return decorator
