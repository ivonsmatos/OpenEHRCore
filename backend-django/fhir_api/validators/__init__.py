# Brazilian healthcare validators package
from .brazilian_validators import (
    validate_crm,
    validate_crf,
    validate_coren,
    validate_cro,
    validate_professional_identifier,
    format_identifier,
    get_all_specialties,
    get_specialty_by_code,
    VALID_UF_CODES,
    MEDICAL_SPECIALTIES,
)

__all__ = [
    'validate_crm',
    'validate_crf',
    'validate_coren',
    'validate_cro',
    'validate_professional_identifier',
    'format_identifier',
    'get_all_specialties',
    'get_specialty_by_code',
    'VALID_UF_CODES',
    'MEDICAL_SPECIALTIES',
]
