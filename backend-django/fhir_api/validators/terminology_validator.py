"""
Terminology Validator - Validação de códigos contra ValueSets

Sprint 36: Conformidade FHIR R4 - Terminology Binding

Este módulo valida se códigos pertencem aos ValueSets especificados,
garantindo conformidade com terminologias FHIR.
"""

import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum
import requests
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class BindingStrength(Enum):
    """Força do binding de terminologia FHIR"""
    REQUIRED = 'required'      # Código DEVE estar no ValueSet
    EXTENSIBLE = 'extensible'  # Código DEVE estar no ValueSet, exceto se não existir
    PREFERRED = 'preferred'    # Código DEVERIA estar no ValueSet
    EXAMPLE = 'example'        # Código pode ser qualquer coisa


@dataclass
class ValidationResult:
    """Resultado da validação de terminologia"""
    valid: bool
    code: str
    system: Optional[str]
    display: Optional[str]
    message: Optional[str] = None
    severity: str = 'error'  # error, warning, information


class TerminologyValidator:
    """
    Validador de terminologias FHIR

    Suporta:
    - Validação local (CodeSystems embarcados)
    - Validação via FHIR $validate-code operation
    - Cache de resultados para performance
    """

    # Cache TTL em segundos (1 hora)
    CACHE_TTL = 3600

    # CodeSystems locais (embutidos)
    LOCAL_CODESYSTEMS = {
        # Raça/Cor Brasil
        'http://www.saude.gov.br/fhir/r4/CodeSystem/BRRacaCor': {
            '01': 'Branca',
            '02': 'Preta',
            '03': 'Parda',
            '04': 'Amarela',
            '05': 'Indígena',
            '99': 'Sem informação'
        },
        # Gênero administrativo
        'http://hl7.org/fhir/administrative-gender': {
            'male': 'Male',
            'female': 'Female',
            'other': 'Other',
            'unknown': 'Unknown'
        },
        # Status de recursos
        'http://hl7.org/fhir/observation-status': {
            'registered': 'Registered',
            'preliminary': 'Preliminary',
            'final': 'Final',
            'amended': 'Amended',
            'corrected': 'Corrected',
            'cancelled': 'Cancelled',
            'entered-in-error': 'Entered in Error',
            'unknown': 'Unknown'
        },
        # CarePlan status
        'http://hl7.org/fhir/request-status': {
            'draft': 'Draft',
            'active': 'Active',
            'on-hold': 'On Hold',
            'revoked': 'Revoked',
            'completed': 'Completed',
            'entered-in-error': 'Entered in Error',
            'unknown': 'Unknown'
        },
        # Goal lifecycle status
        'http://hl7.org/fhir/goal-status': {
            'proposed': 'Proposed',
            'planned': 'Planned',
            'accepted': 'Accepted',
            'active': 'Active',
            'on-hold': 'On Hold',
            'completed': 'Completed',
            'cancelled': 'Cancelled',
            'entered-in-error': 'Entered in Error',
            'rejected': 'Rejected'
        },
        # Goal achievement status
        'http://terminology.hl7.org/CodeSystem/goal-achievement': {
            'in-progress': 'In Progress',
            'improving': 'Improving',
            'worsening': 'Worsening',
            'no-change': 'No Change',
            'achieved': 'Achieved',
            'sustaining': 'Sustaining',
            'not-achieved': 'Not Achieved',
            'no-progress': 'No Progress',
            'not-attainable': 'Not Attainable'
        },
        # Task status
        'http://hl7.org/fhir/task-status': {
            'draft': 'Draft',
            'requested': 'Requested',
            'received': 'Received',
            'accepted': 'Accepted',
            'rejected': 'Rejected',
            'ready': 'Ready',
            'cancelled': 'Cancelled',
            'in-progress': 'In Progress',
            'on-hold': 'On Hold',
            'failed': 'Failed',
            'completed': 'Completed',
            'entered-in-error': 'Entered in Error'
        },
        # Prioridade
        'http://hl7.org/fhir/request-priority': {
            'routine': 'Routine',
            'urgent': 'Urgent',
            'asap': 'ASAP',
            'stat': 'Stat'
        },
        # Identifier use
        'http://hl7.org/fhir/identifier-use': {
            'usual': 'Usual',
            'official': 'Official',
            'temp': 'Temp',
            'secondary': 'Secondary',
            'old': 'Old'
        },
        # Name use
        'http://hl7.org/fhir/name-use': {
            'usual': 'Usual',
            'official': 'Official',
            'temp': 'Temp',
            'nickname': 'Nickname',
            'anonymous': 'Anonymous',
            'old': 'Old',
            'maiden': 'Maiden'
        },
        # Contact point system
        'http://hl7.org/fhir/contact-point-system': {
            'phone': 'Phone',
            'fax': 'Fax',
            'email': 'Email',
            'pager': 'Pager',
            'url': 'URL',
            'sms': 'SMS',
            'other': 'Other'
        },
        # Contact point use
        'http://hl7.org/fhir/contact-point-use': {
            'home': 'Home',
            'work': 'Work',
            'temp': 'Temp',
            'old': 'Old',
            'mobile': 'Mobile'
        },
        # MedicationAdministration status
        'http://hl7.org/fhir/medication-admin-status': {
            'in-progress': 'In Progress',
            'not-done': 'Not Done',
            'on-hold': 'On Hold',
            'completed': 'Completed',
            'entered-in-error': 'Entered in Error',
            'stopped': 'Stopped',
            'unknown': 'Unknown'
        }
    }

    def __init__(self, fhir_server_url: Optional[str] = None):
        """
        Inicializa o validador

        Args:
            fhir_server_url: URL do servidor FHIR para validação remota
        """
        self.fhir_server_url = fhir_server_url or getattr(
            settings, 'FHIR_SERVER_URL', 'http://localhost:8080/fhir'
        )

    def validate_code(
        self,
        code: str,
        system: str,
        display: Optional[str] = None,
        valueset_url: Optional[str] = None,
        binding_strength: BindingStrength = BindingStrength.REQUIRED
    ) -> ValidationResult:
        """
        Valida um código contra um sistema de terminologia

        Args:
            code: Código a validar
            system: URI do CodeSystem
            display: Display text (opcional)
            valueset_url: URL do ValueSet (opcional, usa CodeSystem se não fornecido)
            binding_strength: Força do binding

        Returns:
            ValidationResult com resultado da validação
        """
        # Tenta validação local primeiro
        local_result = self._validate_local(code, system, display)
        if local_result is not None:
            return local_result

        # Tenta validação remota
        remote_result = self._validate_remote(code, system, display, valueset_url)
        if remote_result is not None:
            return remote_result

        # Se não conseguiu validar e binding não é required, aceita
        if binding_strength in [BindingStrength.PREFERRED, BindingStrength.EXAMPLE]:
            return ValidationResult(
                valid=True,
                code=code,
                system=system,
                display=display,
                message=f"Code not validated (binding: {binding_strength.value})",
                severity='information'
            )

        # Se extensible e não encontrou, pode ainda ser válido
        if binding_strength == BindingStrength.EXTENSIBLE:
            return ValidationResult(
                valid=True,
                code=code,
                system=system,
                display=display,
                message="Code not in standard ValueSet but accepted (extensible binding)",
                severity='warning'
            )

        # Required mas não validou
        return ValidationResult(
            valid=False,
            code=code,
            system=system,
            display=display,
            message=f"Unable to validate code '{code}' against system '{system}'",
            severity='error'
        )

    def _validate_local(
        self,
        code: str,
        system: str,
        display: Optional[str] = None
    ) -> Optional[ValidationResult]:
        """Valida código contra CodeSystems locais"""
        if system not in self.LOCAL_CODESYSTEMS:
            return None

        codesystem = self.LOCAL_CODESYSTEMS[system]
        if code not in codesystem:
            return ValidationResult(
                valid=False,
                code=code,
                system=system,
                display=display,
                message=f"Code '{code}' not found in CodeSystem '{system}'",
                severity='error'
            )

        expected_display = codesystem[code]
        if display and display != expected_display:
            return ValidationResult(
                valid=True,
                code=code,
                system=system,
                display=display,
                message=f"Display mismatch: expected '{expected_display}', got '{display}'",
                severity='warning'
            )

        return ValidationResult(
            valid=True,
            code=code,
            system=system,
            display=expected_display
        )

    def _validate_remote(
        self,
        code: str,
        system: str,
        display: Optional[str] = None,
        valueset_url: Optional[str] = None
    ) -> Optional[ValidationResult]:
        """Valida código via FHIR $validate-code operation"""
        cache_key = f"terminology_validate:{system}:{code}"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        try:
            params = {
                'code': code,
                'system': system
            }
            if display:
                params['display'] = display
            if valueset_url:
                params['url'] = valueset_url

            # Usa CodeSystem/$validate-code ou ValueSet/$validate-code
            endpoint = 'ValueSet' if valueset_url else 'CodeSystem'
            url = f"{self.fhir_server_url}/{endpoint}/$validate-code"

            response = requests.get(url, params=params, timeout=5)

            if response.status_code == 200:
                data = response.json()
                result_param = next(
                    (p for p in data.get('parameter', []) if p.get('name') == 'result'),
                    None
                )
                valid = result_param.get('valueBoolean', False) if result_param else False

                result = ValidationResult(
                    valid=valid,
                    code=code,
                    system=system,
                    display=display,
                    message=None if valid else f"Code '{code}' not valid in system '{system}'"
                )
                cache.set(cache_key, result, self.CACHE_TTL)
                return result

        except Exception as e:
            logger.warning(f"Remote terminology validation failed: {e}")

        return None

    def validate_codeable_concept(
        self,
        codeable_concept: Dict[str, Any],
        valueset_url: Optional[str] = None,
        binding_strength: BindingStrength = BindingStrength.REQUIRED
    ) -> List[ValidationResult]:
        """
        Valida um CodeableConcept inteiro

        Args:
            codeable_concept: Dict com estrutura FHIR CodeableConcept
            valueset_url: URL do ValueSet esperado
            binding_strength: Força do binding

        Returns:
            Lista de ValidationResults (um por coding)
        """
        results = []
        codings = codeable_concept.get('coding', [])

        if not codings and binding_strength == BindingStrength.REQUIRED:
            results.append(ValidationResult(
                valid=False,
                code='',
                system=None,
                display=None,
                message="CodeableConcept must have at least one coding",
                severity='error'
            ))
            return results

        for coding in codings:
            code = coding.get('code', '')
            system = coding.get('system', '')
            display = coding.get('display')

            result = self.validate_code(
                code=code,
                system=system,
                display=display,
                valueset_url=valueset_url,
                binding_strength=binding_strength
            )
            results.append(result)

        return results

    def validate_identifier(
        self,
        identifier: Dict[str, Any]
    ) -> ValidationResult:
        """
        Valida estrutura de Identifier FHIR

        Args:
            identifier: Dict com estrutura FHIR Identifier

        Returns:
            ValidationResult
        """
        value = identifier.get('value')
        system = identifier.get('system')
        use = identifier.get('use')

        if not value:
            return ValidationResult(
                valid=False,
                code='',
                system=system,
                display=None,
                message="Identifier must have a value",
                severity='error'
            )

        # Valida 'use' se presente
        if use:
            use_result = self.validate_code(
                code=use,
                system='http://hl7.org/fhir/identifier-use',
                binding_strength=BindingStrength.REQUIRED
            )
            if not use_result.valid:
                return use_result

        # Validações específicas por sistema brasileiro
        if system == 'http://rnds.saude.gov.br/fhir/r4/NamingSystem/cpf':
            if not self._validate_cpf(value):
                return ValidationResult(
                    valid=False,
                    code=value,
                    system=system,
                    display=None,
                    message="Invalid CPF format or check digits",
                    severity='error'
                )

        elif system == 'http://rnds.saude.gov.br/fhir/r4/NamingSystem/cns':
            if not self._validate_cns(value):
                return ValidationResult(
                    valid=False,
                    code=value,
                    system=system,
                    display=None,
                    message="Invalid CNS format",
                    severity='error'
                )

        elif system == 'http://rnds.saude.gov.br/fhir/r4/NamingSystem/cnes':
            if not self._validate_cnes(value):
                return ValidationResult(
                    valid=False,
                    code=value,
                    system=system,
                    display=None,
                    message="Invalid CNES format (must be 7 digits)",
                    severity='error'
                )

        return ValidationResult(
            valid=True,
            code=value,
            system=system,
            display=None
        )

    def _validate_cpf(self, cpf: str) -> bool:
        """Valida CPF brasileiro"""
        cpf = cpf.replace('.', '').replace('-', '')

        if len(cpf) != 11 or not cpf.isdigit():
            return False

        # CPFs conhecidos como inválidos
        if cpf == cpf[0] * 11:
            return False

        # Validação dos dígitos verificadores
        def calc_digit(cpf_partial: str, weights: List[int]) -> int:
            total = sum(int(d) * w for d, w in zip(cpf_partial, weights))
            remainder = total % 11
            return 0 if remainder < 2 else 11 - remainder

        weights1 = [10, 9, 8, 7, 6, 5, 4, 3, 2]
        weights2 = [11, 10, 9, 8, 7, 6, 5, 4, 3, 2]

        digit1 = calc_digit(cpf[:9], weights1)
        digit2 = calc_digit(cpf[:10], weights2)

        return cpf[-2:] == f"{digit1}{digit2}"

    def _validate_cns(self, cns: str) -> bool:
        """Valida CNS (Cartão Nacional de Saúde)"""
        cns = cns.replace(' ', '')

        if len(cns) != 15 or not cns.isdigit():
            return False

        # CNS deve começar com 1, 2, 7, 8 ou 9
        if cns[0] not in '12789':
            return False

        return True

    def _validate_cnes(self, cnes: str) -> bool:
        """Valida CNES (Cadastro Nacional de Estabelecimentos de Saúde)"""
        if len(cnes) != 7 or not cnes.isdigit():
            return False
        return True


# Instância global para uso simplificado
_validator = None


def get_terminology_validator() -> TerminologyValidator:
    """Retorna instância singleton do validador"""
    global _validator
    if _validator is None:
        _validator = TerminologyValidator()
    return _validator


def validate_code(
    code: str,
    system: str,
    display: Optional[str] = None,
    binding_strength: BindingStrength = BindingStrength.REQUIRED
) -> ValidationResult:
    """Função de conveniência para validar código"""
    return get_terminology_validator().validate_code(
        code=code,
        system=system,
        display=display,
        binding_strength=binding_strength
    )


def validate_codeable_concept(
    codeable_concept: Dict[str, Any],
    valueset_url: Optional[str] = None,
    binding_strength: BindingStrength = BindingStrength.REQUIRED
) -> List[ValidationResult]:
    """Função de conveniência para validar CodeableConcept"""
    return get_terminology_validator().validate_codeable_concept(
        codeable_concept=codeable_concept,
        valueset_url=valueset_url,
        binding_strength=binding_strength
    )
