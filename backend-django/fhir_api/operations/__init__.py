"""
FHIR Operations Module

Sprint 36: Operações FHIR R4
"""

from .terminology_operations import (
    TerminologyOperations,
    get_terminology_operations,
    ExpandedConcept,
    TranslationMatch,
)

__all__ = [
    'TerminologyOperations',
    'get_terminology_operations',
    'ExpandedConcept',
    'TranslationMatch',
]
