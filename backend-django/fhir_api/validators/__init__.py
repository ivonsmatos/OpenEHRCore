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

# Sprint 36: FHIR Terminology Validation
from .terminology_validator import (
    TerminologyValidator,
    BindingStrength,
    ValidationResult,
    validate_code,
    validate_codeable_concept,
    get_terminology_validator,
)

__all__ = [
    # Brazilian validators
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
    # Terminology validators
    'TerminologyValidator',
    'BindingStrength',
    'ValidationResult',
    'validate_code',
    'validate_codeable_concept',
    'get_terminology_validator',
]
