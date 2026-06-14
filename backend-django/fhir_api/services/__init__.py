"""
FHIR API Services

Módulos de serviços para integrações e funcionalidades avançadas.
"""

from .crm_validation_service import (
    CRMValidationService,
    CRMValidationResult,
    ConselhoTipo,
    ValidationStatus,
)

__all__ = [
    'CRMValidationService',
    'CRMValidationResult',
    'ConselhoTipo',
    'ValidationStatus',
]
