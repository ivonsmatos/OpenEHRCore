"""
Sprint 25: Database Query Optimization Service

Provides query optimization utilities for Django and FHIR operations:
- Query analysis and logging
- Batch operations
- Prefetch optimization
- Query profiling
"""

import time
import logging
from typing import Any, Dict, List, Optional, Callable, TypeVar
from functools import wraps
from contextlib import contextmanager
from django.db import connection, reset_queries
from django.conf import settings

logger = logging.getLogger(__name__)

T = TypeVar('T')


class QueryProfiler:
    """
    Profiles database queries to identify performance issues.
    """
    
    def __init__(self):
        self.queries: List[Dict] = []
        self.slow_query_threshold = 0.1  # 100ms
    
    @contextmanager
    def profile(self, label: str = "Query"):
        """
        Context manager to profile queries within a block.
        
        Usage:
            with profiler.profile("Patient search"):
                results = Patient.objects.filter(...)
        """
        reset_queries()
        start_time = time.time()
        
        yield
        
        elapsed = time.time() - start_time
        queries = connection.queries.copy()
        
        profile = {
            "label": label,
            "elapsed_total": round(elapsed * 1000, 2),  # ms
            "query_count": len(queries),
            "queries": []
        }
        
        for q in queries:
            query_time = float(q.get("time", 0))
            is_slow = query_time > self.slow_query_threshold
            
            profile["queries"].append({
                "sql": q.get("sql", "")[:200],  # Truncate long queries
                "time": query_time,
                "is_slow": is_slow
            })
            
            if is_slow:
                logger.warning(f"Slow query ({query_time}s): {q.get('sql', '')[:100]}...")
        
        self.queries.append(profile)
        
        if settings.DEBUG:
            logger.info(
                f"[{label}] {len(queries)} queries in {profile['elapsed_total']}ms"
            )
    
    def get_summary(self) -> Dict[str, Any]:
        """Get profiling summary."""
        if not self.queries:
            return {"total_profiles": 0}
        
        total_queries = sum(p["query_count"] for p in self.queries)
        total_time = sum(p["elapsed_total"] for p in self.queries)
        slow_queries = sum(
            1 for p in self.queries 
            for q in p["queries"] 
            if q.get("is_slow")
        )
        
        return {
            "total_profiles": len(self.queries),
            "total_queries": total_queries,
            "total_time_ms": round(total_time, 2),
            "avg_queries_per_profile": round(total_queries / len(self.queries), 2),
            "slow_queries": slow_queries,
            "profiles": self.queries
        }
    
    def clear(self):
        """Clear profiling data."""
        self.queries = []


class BatchProcessor:
    """
    Handles batch operations efficiently.
    """
    
    @staticmethod
    def batch_create(model_class, items: List[Dict], batch_size: int = 100) -> List:
        """
        Create multiple model instances in batches.
        
        Args:
            model_class: Django model class
            items: List of dictionaries with field values
            batch_size: Number of items per batch
        """
        instances = [model_class(**item) for item in items]
        return model_class.objects.bulk_create(instances, batch_size=batch_size)
    
    @staticmethod
    def batch_update(queryset, updates: Dict, batch_size: int = 100) -> int:
        """
        Update multiple records in batches.
        
        Args:
            queryset: Django queryset to update
            updates: Dictionary of field updates
            batch_size: Number of items per batch
        """
        total = 0
        pks = list(queryset.values_list('pk', flat=True))
        
        for i in range(0, len(pks), batch_size):
            batch_pks = pks[i:i + batch_size]
            updated = queryset.model.objects.filter(pk__in=batch_pks).update(**updates)
            total += updated
        
        return total
    
    @staticmethod
    def batch_delete(queryset, batch_size: int = 100) -> int:
        """Delete records in batches to avoid locking."""
        total = 0
        
        while True:
            pks = list(queryset.values_list('pk', flat=True)[:batch_size])
            if not pks:
                break
            
            deleted, _ = queryset.model.objects.filter(pk__in=pks).delete()
            total += deleted
        
        return total
    
    @staticmethod
    def chunk_list(items: List, chunk_size: int):
        """Yield chunks of a list."""
        for i in range(0, len(items), chunk_size):
            yield items[i:i + chunk_size]


class QueryOptimizer:
    """
    Utilities for optimizing Django ORM queries.
    """
    
    @staticmethod
    def select_related_fields(model_class) -> List[str]:
        """
        Get list of ForeignKey fields for select_related.
        """
        return [
            field.name
            for field in model_class._meta.get_fields()
            if field.is_relation and field.many_to_one
        ]
    
    @staticmethod
    def prefetch_related_fields(model_class) -> List[str]:
        """
        Get list of reverse relations for prefetch_related.
        """
        return [
            field.name
            for field in model_class._meta.get_fields()
            if field.is_relation and (field.one_to_many or field.many_to_many)
        ]
    
    @staticmethod
    def optimize_queryset(queryset, include_related: bool = True):
        """
        Automatically optimize a queryset with select_related and prefetch_related.
        """
        if not include_related:
            return queryset
        
        model = queryset.model
        
        # Add select_related for ForeignKey
        fk_fields = [
            field.name
            for field in model._meta.get_fields()
            if field.is_relation and field.many_to_one
        ]
        if fk_fields:
            queryset = queryset.select_related(*fk_fields)
        
        return queryset
    
    @staticmethod
    def defer_large_fields(queryset, fields: List[str]):
        """
        Defer loading of large fields until accessed.
        """
        return queryset.defer(*fields)
    
    @staticmethod
    def only_required_fields(queryset, fields: List[str]):
        """
        Only load specified fields.
        """
        return queryset.only(*fields)


def profile_queries(label: str = ""):
    """
    Decorator to profile queries in a function.
    
    Usage:
        @profile_queries("Patient list")
        def list_patients():
            ...
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            profiler = QueryProfiler()
            with profiler.profile(label or func.__name__):
                result = func(*args, **kwargs)
            
            summary = profiler.get_summary()
            if summary.get("slow_queries", 0) > 0:
                logger.warning(
                    f"Function {func.__name__} had {summary['slow_queries']} slow queries"
                )
            
            return result
        return wrapper
    return decorator


def timed(label: str = ""):
    """
    Decorator to time function execution.
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            start = time.time()
            result = func(*args, **kwargs)
            elapsed = (time.time() - start) * 1000
            
            logger.info(f"[{label or func.__name__}] executed in {elapsed:.2f}ms")
            
            return result
        return wrapper
    return decorator


class FHIRQueryOptimizer:
    """
    Optimizes FHIR API queries to HAPI FHIR server.
    """
    
    @staticmethod
    def optimize_search_params(params: Dict) -> Dict:
        """
        Optimize FHIR search parameters.
        """
        optimized = params.copy()
        
        # Add _elements to limit returned fields if not present
        if "_elements" not in optimized and "_summary" not in optimized:
            # Don't add by default, but could be configured
            pass
        
        # Ensure count is reasonable
        if "_count" in optimized:
            count = int(optimized["_count"])
            if count > 1000:
                logger.warning(f"Large _count ({count}) may impact performance")
                optimized["_count"] = 1000
        else:
            optimized["_count"] = 50  # Default limit
        
        return optimized
    
    @staticmethod
    def build_bundle_request(requests: List[Dict]) -> Dict:
        """
        Build a FHIR Bundle for batch requests.
        
        More efficient than multiple individual requests.
        """
        return {
            "resourceType": "Bundle",
            "type": "batch",
            "entry": [
                {
                    "request": {
                        "method": req.get("method", "GET"),
                        "url": req.get("url")
                    }
                }
                for req in requests
            ]
        }
    
    @staticmethod
    def parse_bundle_response(bundle: Dict) -> List[Dict]:
        """
        Parse a FHIR Bundle response into individual results.
        """
        results = []
        for entry in bundle.get("entry", []):
            response = entry.get("response", {})
            resource = entry.get("resource")
            
            results.append({
                "status": response.get("status"),
                "resource": resource,
                "location": response.get("location")
            })
        
        return results


# Global instances
query_profiler = QueryProfiler()
batch_processor = BatchProcessor()
query_optimizer = QueryOptimizer()
fhir_optimizer = FHIRQueryOptimizer()
