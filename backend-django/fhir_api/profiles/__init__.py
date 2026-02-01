"""
FHIR Profiles - StructureDefinitions brasileiros (RNDS)

Sprint 36: Perfis FHIR para conformidade RNDS
"""

from .patient_br import PATIENT_BR_PROFILE
from .practitioner_br import PRACTITIONER_BR_PROFILE
from .organization_br import ORGANIZATION_BR_PROFILE

__all__ = [
    'PATIENT_BR_PROFILE',
    'PRACTITIONER_BR_PROFILE',
    'ORGANIZATION_BR_PROFILE',
]
