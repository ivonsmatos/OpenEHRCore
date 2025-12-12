"""
Prometheus Metrics Endpoint
Sprint 28: DevOps Improvement

Provides /metrics endpoint for Prometheus scraping.
"""

import time
import functools
import logging
from typing import Dict, Any, Callable
from django.http import HttpResponse
from django.conf import settings

logger = logging.getLogger(__name__)

# Metrics storage (in production, use prometheus_client library)
_metrics: Dict[str, Any] = {
    'requests_total': 0,
    'requests_by_method': {},
    'requests_by_status': {},
    'requests_by_endpoint': {},
    'request_duration_seconds': [],
    'active_requests': 0,
    'fhir_operations': {},
    'cache_hits': 0,
    'cache_misses': 0,
    'db_queries': 0,
    'errors_total': 0,
}


def increment_counter(name: str, labels: Dict[str, str] = None) -> None:
    """Increment a counter metric."""
    if labels:
        key = f"{name}_{labels}"
        _metrics.setdefault(name, {})
        _metrics[name][str(labels)] = _metrics[name].get(str(labels), 0) + 1
    else:
        _metrics[name] = _metrics.get(name, 0) + 1


def observe_duration(name: str, duration: float) -> None:
    """Record a duration observation."""
    _metrics.setdefault(f'{name}_seconds', [])
    _metrics[f'{name}_seconds'].append(duration)
    # Keep only last 1000 observations
    if len(_metrics[f'{name}_seconds']) > 1000:
        _metrics[f'{name}_seconds'] = _metrics[f'{name}_seconds'][-1000:]


def set_gauge(name: str, value: float) -> None:
    """Set a gauge metric value."""
    _metrics[name] = value


def track_request(func: Callable) -> Callable:
    """Decorator to track request metrics."""
    @functools.wraps(func)
    def wrapper(request, *args, **kwargs):
        _metrics['active_requests'] = _metrics.get('active_requests', 0) + 1
        start_time = time.time()
        
        try:
            response = func(request, *args, **kwargs)
            status_code = response.status_code
        except Exception as e:
            _metrics['errors_total'] = _metrics.get('errors_total', 0) + 1
            raise
        finally:
            duration = time.time() - start_time
            _metrics['active_requests'] = max(0, _metrics.get('active_requests', 1) - 1)
            
            # Record metrics
            increment_counter('requests_total')
            increment_counter('requests_by_method', {'method': request.method})
            observe_duration('request_duration', duration)
            
            if 'status_code' in dir():
                increment_counter('requests_by_status', {'status': str(status_code)})
        
        return response
    return wrapper


def format_prometheus_metrics() -> str:
    """Format metrics in Prometheus exposition format."""
    lines = []
    
    # Help and type declarations
    lines.append('# HELP openehrcore_requests_total Total number of HTTP requests')
    lines.append('# TYPE openehrcore_requests_total counter')
    lines.append(f'openehrcore_requests_total {_metrics.get("requests_total", 0)}')
    
    lines.append('')
    lines.append('# HELP openehrcore_active_requests Current number of active requests')
    lines.append('# TYPE openehrcore_active_requests gauge')
    lines.append(f'openehrcore_active_requests {_metrics.get("active_requests", 0)}')
    
    lines.append('')
    lines.append('# HELP openehrcore_errors_total Total number of errors')
    lines.append('# TYPE openehrcore_errors_total counter')
    lines.append(f'openehrcore_errors_total {_metrics.get("errors_total", 0)}')
    
    lines.append('')
    lines.append('# HELP openehrcore_cache_hits_total Total cache hits')
    lines.append('# TYPE openehrcore_cache_hits_total counter')
    lines.append(f'openehrcore_cache_hits_total {_metrics.get("cache_hits", 0)}')
    
    lines.append('')
    lines.append('# HELP openehrcore_cache_misses_total Total cache misses')
    lines.append('# TYPE openehrcore_cache_misses_total counter')
    lines.append(f'openehrcore_cache_misses_total {_metrics.get("cache_misses", 0)}')
    
    # Request duration histogram (simplified)
    durations = _metrics.get('request_duration_seconds', [])
    if durations:
        avg_duration = sum(durations) / len(durations)
        max_duration = max(durations)
        lines.append('')
        lines.append('# HELP openehrcore_request_duration_seconds Request duration in seconds')
        lines.append('# TYPE openehrcore_request_duration_seconds summary')
        lines.append(f'openehrcore_request_duration_seconds_avg {avg_duration:.6f}')
        lines.append(f'openehrcore_request_duration_seconds_max {max_duration:.6f}')
        lines.append(f'openehrcore_request_duration_seconds_count {len(durations)}')
    
    # Requests by method
    methods = _metrics.get('requests_by_method', {})
    if methods:
        lines.append('')
        lines.append('# HELP openehrcore_requests_by_method Requests by HTTP method')
        lines.append('# TYPE openehrcore_requests_by_method counter')
        for method_labels, count in methods.items():
            lines.append(f'openehrcore_requests_by_method{{{method_labels.replace("'", '"')}}} {count}')
    
    # Requests by status
    statuses = _metrics.get('requests_by_status', {})
    if statuses:
        lines.append('')
        lines.append('# HELP openehrcore_requests_by_status Requests by HTTP status')
        lines.append('# TYPE openehrcore_requests_by_status counter')
        for status_labels, count in statuses.items():
            lines.append(f'openehrcore_requests_by_status{{{status_labels.replace("'", '"')}}} {count}')
    
    # FHIR operations
    fhir_ops = _metrics.get('fhir_operations', {})
    if fhir_ops:
        lines.append('')
        lines.append('# HELP openehrcore_fhir_operations FHIR operations by type')
        lines.append('# TYPE openehrcore_fhir_operations counter')
        for op_labels, count in fhir_ops.items():
            lines.append(f'openehrcore_fhir_operations{{{op_labels}}} {count}')
    
    return '\n'.join(lines) + '\n'


def metrics_view(request):
    """
    Prometheus metrics endpoint.
    
    GET /metrics
    
    Returns metrics in Prometheus exposition format.
    """
    content = format_prometheus_metrics()
    return HttpResponse(
        content,
        content_type='text/plain; version=0.0.4; charset=utf-8'
    )


# Utility functions for tracking specific operations
def track_fhir_operation(operation: str, resource_type: str) -> None:
    """Track a FHIR operation."""
    key = f'operation="{operation}",resource="{resource_type}"'
    _metrics.setdefault('fhir_operations', {})
    _metrics['fhir_operations'][key] = _metrics['fhir_operations'].get(key, 0) + 1


def track_cache_hit() -> None:
    """Track a cache hit."""
    _metrics['cache_hits'] = _metrics.get('cache_hits', 0) + 1


def track_cache_miss() -> None:
    """Track a cache miss."""
    _metrics['cache_misses'] = _metrics.get('cache_misses', 0) + 1


def get_metrics_summary() -> Dict[str, Any]:
    """Get a summary of current metrics (for health check)."""
    durations = _metrics.get('request_duration_seconds', [])
    return {
        'requests_total': _metrics.get('requests_total', 0),
        'errors_total': _metrics.get('errors_total', 0),
        'active_requests': _metrics.get('active_requests', 0),
        'avg_response_time': sum(durations) / len(durations) if durations else 0,
        'cache_hit_rate': (
            _metrics.get('cache_hits', 0) / 
            max(1, _metrics.get('cache_hits', 0) + _metrics.get('cache_misses', 0))
        )
    }
