"""
JSON Logging Formatter for OpenEHRCore

Provides structured JSON logging for:
- Request tracking
- Audit trails
- Error reporting
- Performance monitoring
"""

import json
import logging
import traceback
from datetime import datetime
from typing import Any, Dict, Optional


class JsonFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging.
    
    Output format:
    {
        "timestamp": "2024-12-13T15:00:00.000Z",
        "level": "INFO",
        "logger": "fhir_api.views",
        "message": "Request processed",
        "module": "views_auth",
        "function": "create_patient",
        "line": 42,
        "extra": {...}
    }
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.default_fields = {
            'service': 'openehrcore',
            'version': '1.0.0',
        }

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record as JSON."""
        log_data = self._build_log_data(record)
        return json.dumps(log_data, ensure_ascii=False, default=str)

    def _build_log_data(self, record: logging.LogRecord) -> Dict[str, Any]:
        """Build the log data dictionary."""
        log_data = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            **self.default_fields,
        }

        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__ if record.exc_info[0] else None,
                'message': str(record.exc_info[1]) if record.exc_info[1] else None,
                'traceback': traceback.format_exception(*record.exc_info) if record.exc_info[2] else None,
            }

        # Add extra fields from record
        extra_fields = self._get_extra_fields(record)
        if extra_fields:
            log_data['extra'] = extra_fields

        return log_data

    def _get_extra_fields(self, record: logging.LogRecord) -> Dict[str, Any]:
        """Extract extra fields from the log record."""
        # Standard LogRecord attributes to exclude
        standard_attrs = {
            'name', 'msg', 'args', 'created', 'filename', 'funcName',
            'levelname', 'levelno', 'lineno', 'module', 'msecs',
            'pathname', 'process', 'processName', 'relativeCreated',
            'stack_info', 'exc_info', 'exc_text', 'thread', 'threadName',
            'message', 'asctime'
        }

        extra = {}
        for key, value in record.__dict__.items():
            if key not in standard_attrs and not key.startswith('_'):
                extra[key] = value

        return extra


class RequestLogFormatter(JsonFormatter):
    """
    Extended JSON formatter for HTTP request logging.
    Includes request-specific fields.
    """

    def _build_log_data(self, record: logging.LogRecord) -> Dict[str, Any]:
        log_data = super()._build_log_data(record)

        # Add request-specific fields if present
        if hasattr(record, 'request'):
            request = record.request
            log_data['request'] = {
                'method': getattr(request, 'method', None),
                'path': getattr(request, 'path', None),
                'user': str(getattr(request, 'user', 'anonymous')),
                'ip': self._get_client_ip(request),
            }

        # Add response-specific fields if present
        if hasattr(record, 'response'):
            response = record.response
            log_data['response'] = {
                'status_code': getattr(response, 'status_code', None),
            }

        # Add timing info if present
        if hasattr(record, 'duration_ms'):
            log_data['duration_ms'] = record.duration_ms

        return log_data

    def _get_client_ip(self, request) -> Optional[str]:
        """Extract client IP from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')


class AuditLogFormatter(JsonFormatter):
    """
    Extended JSON formatter for audit logging.
    Includes FHIR audit-specific fields.
    """

    def _build_log_data(self, record: logging.LogRecord) -> Dict[str, Any]:
        log_data = super()._build_log_data(record)
        log_data['audit'] = True

        # Add audit-specific fields if present
        audit_fields = ['action', 'resource_type', 'resource_id', 
                        'patient_id', 'practitioner_id', 'outcome']
        
        for field in audit_fields:
            if hasattr(record, field):
                if 'audit_data' not in log_data:
                    log_data['audit_data'] = {}
                log_data['audit_data'][field] = getattr(record, field)

        return log_data


# Convenience function for structured logging
def get_logger(name: str = 'fhir_api') -> logging.Logger:
    """Get a logger instance with the given name."""
    return logging.getLogger(name)


def get_audit_logger() -> logging.Logger:
    """Get the audit logger instance."""
    return logging.getLogger('fhir_api.audit')


def get_security_logger() -> logging.Logger:
    """Get the security logger instance."""
    return logging.getLogger('fhir_api.security')


# Export for use in settings.py
__all__ = [
    'JsonFormatter',
    'RequestLogFormatter', 
    'AuditLogFormatter',
    'get_logger',
    'get_audit_logger',
    'get_security_logger',
]
