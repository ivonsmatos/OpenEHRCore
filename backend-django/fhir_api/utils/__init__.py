"""
Utilitários compartilhados para o módulo fhir_api.
"""

from .validators import (
    validate_cpf,
    validate_uuid,
    validate_patient_id,
    sanitize_cpf,
    format_cpf,
    validate_email,
    sanitize_fhir_search_param,
    validate_date_not_future,
    calculate_age
)

from .logging_utils import (
    sanitize_for_log,
    sanitize_url,
    mask_cpf,
    create_audit_log_entry
)

__all__ = [
    'validate_cpf',
    'validate_uuid',
    'validate_patient_id',
    'sanitize_cpf',
    'format_cpf',
    'validate_email',
    'sanitize_fhir_search_param',
    'validate_date_not_future',
    'calculate_age',
    'sanitize_for_log',
    'sanitize_url',
    'mask_cpf',
    'create_audit_log_entry',
]
