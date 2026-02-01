"""
FHIR Terminology Operations

Sprint 36: Conformidade FHIR R4 - Terminology Operations

Implementa operações de terminologia FHIR:
- $expand: Expande um ValueSet
- $validate-code: Valida código contra ValueSet/CodeSystem
- $lookup: Busca informações sobre um código
- $translate: Traduz código entre sistemas
- $subsumes: Verifica relação hierárquica
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from django.conf import settings
from django.core.cache import cache
import requests

logger = logging.getLogger(__name__)


@dataclass
class ExpandedConcept:
    """Conceito expandido de um ValueSet"""
    code: str
    display: str
    system: str
    version: Optional[str] = None
    abstract: bool = False
    inactive: bool = False
    designation: List[Dict[str, str]] = None


@dataclass
class TranslationMatch:
    """Match de tradução de código"""
    equivalence: str  # equivalent, relatedto, broader, narrower, etc
    concept: Dict[str, Any]
    source: Optional[str] = None


class TerminologyOperations:
    """
    Implementação das operações de terminologia FHIR

    Suporta CodeSystems locais e delegação para servidor FHIR externo
    """

    # Cache TTL (1 hora para expansões)
    CACHE_TTL = 3600

    # ValueSets locais disponíveis
    LOCAL_VALUESETS = {
        'http://openehrcore.com.br/fhir/ValueSet/BRRacaCor': {
            'name': 'BRRacaCor',
            'title': 'Raça/Cor - Brasil',
            'status': 'active',
            'concepts': [
                {'code': '01', 'display': 'Branca', 'system': 'http://www.saude.gov.br/fhir/r4/CodeSystem/BRRacaCor'},
                {'code': '02', 'display': 'Preta', 'system': 'http://www.saude.gov.br/fhir/r4/CodeSystem/BRRacaCor'},
                {'code': '03', 'display': 'Parda', 'system': 'http://www.saude.gov.br/fhir/r4/CodeSystem/BRRacaCor'},
                {'code': '04', 'display': 'Amarela', 'system': 'http://www.saude.gov.br/fhir/r4/CodeSystem/BRRacaCor'},
                {'code': '05', 'display': 'Indígena', 'system': 'http://www.saude.gov.br/fhir/r4/CodeSystem/BRRacaCor'},
                {'code': '99', 'display': 'Sem informação', 'system': 'http://www.saude.gov.br/fhir/r4/CodeSystem/BRRacaCor'},
            ]
        },
        'http://hl7.org/fhir/ValueSet/administrative-gender': {
            'name': 'AdministrativeGender',
            'title': 'Administrative Gender',
            'status': 'active',
            'concepts': [
                {'code': 'male', 'display': 'Male', 'system': 'http://hl7.org/fhir/administrative-gender'},
                {'code': 'female', 'display': 'Female', 'system': 'http://hl7.org/fhir/administrative-gender'},
                {'code': 'other', 'display': 'Other', 'system': 'http://hl7.org/fhir/administrative-gender'},
                {'code': 'unknown', 'display': 'Unknown', 'system': 'http://hl7.org/fhir/administrative-gender'},
            ]
        },
        'http://hl7.org/fhir/ValueSet/observation-status': {
            'name': 'ObservationStatus',
            'title': 'Observation Status',
            'status': 'active',
            'concepts': [
                {'code': 'registered', 'display': 'Registered', 'system': 'http://hl7.org/fhir/observation-status'},
                {'code': 'preliminary', 'display': 'Preliminary', 'system': 'http://hl7.org/fhir/observation-status'},
                {'code': 'final', 'display': 'Final', 'system': 'http://hl7.org/fhir/observation-status'},
                {'code': 'amended', 'display': 'Amended', 'system': 'http://hl7.org/fhir/observation-status'},
                {'code': 'corrected', 'display': 'Corrected', 'system': 'http://hl7.org/fhir/observation-status'},
                {'code': 'cancelled', 'display': 'Cancelled', 'system': 'http://hl7.org/fhir/observation-status'},
                {'code': 'entered-in-error', 'display': 'Entered in Error', 'system': 'http://hl7.org/fhir/observation-status'},
                {'code': 'unknown', 'display': 'Unknown', 'system': 'http://hl7.org/fhir/observation-status'},
            ]
        },
        'http://hl7.org/fhir/ValueSet/goal-status': {
            'name': 'GoalLifecycleStatus',
            'title': 'Goal Lifecycle Status',
            'status': 'active',
            'concepts': [
                {'code': 'proposed', 'display': 'Proposed', 'system': 'http://hl7.org/fhir/goal-status'},
                {'code': 'planned', 'display': 'Planned', 'system': 'http://hl7.org/fhir/goal-status'},
                {'code': 'accepted', 'display': 'Accepted', 'system': 'http://hl7.org/fhir/goal-status'},
                {'code': 'active', 'display': 'Active', 'system': 'http://hl7.org/fhir/goal-status'},
                {'code': 'on-hold', 'display': 'On Hold', 'system': 'http://hl7.org/fhir/goal-status'},
                {'code': 'completed', 'display': 'Completed', 'system': 'http://hl7.org/fhir/goal-status'},
                {'code': 'cancelled', 'display': 'Cancelled', 'system': 'http://hl7.org/fhir/goal-status'},
                {'code': 'entered-in-error', 'display': 'Entered in Error', 'system': 'http://hl7.org/fhir/goal-status'},
                {'code': 'rejected', 'display': 'Rejected', 'system': 'http://hl7.org/fhir/goal-status'},
            ]
        },
    }

    # Mapeamentos de tradução (source_system -> target_system -> code mappings)
    CONCEPT_MAPS = {
        # ICD-10 para SNOMED CT (exemplos)
        ('http://hl7.org/fhir/sid/icd-10', 'http://snomed.info/sct'): {
            'E11': {'code': '44054006', 'display': 'Type 2 diabetes mellitus', 'equivalence': 'equivalent'},
            'I10': {'code': '38341003', 'display': 'Hypertensive disorder', 'equivalence': 'equivalent'},
            'J06': {'code': '54150009', 'display': 'Upper respiratory infection', 'equivalence': 'broader'},
        },
        # LOINC para SNOMED (exemplos)
        ('http://loinc.org', 'http://snomed.info/sct'): {
            '8310-5': {'code': '386725007', 'display': 'Body temperature', 'equivalence': 'equivalent'},
            '8867-4': {'code': '364075005', 'display': 'Heart rate', 'equivalence': 'equivalent'},
            '85354-9': {'code': '75367002', 'display': 'Blood pressure', 'equivalence': 'equivalent'},
        },
    }

    def __init__(self, fhir_server_url: Optional[str] = None):
        self.fhir_server_url = fhir_server_url or getattr(
            settings, 'FHIR_SERVER_URL', 'http://localhost:8080/fhir'
        )

    def expand(
        self,
        url: Optional[str] = None,
        valueset: Optional[Dict[str, Any]] = None,
        filter: Optional[str] = None,
        offset: int = 0,
        count: int = 100,
        include_designations: bool = False
    ) -> Dict[str, Any]:
        """
        $expand - Expande um ValueSet

        Args:
            url: URL canônica do ValueSet
            valueset: ValueSet inline (se não usar url)
            filter: Filtro de texto para conceitos
            offset: Offset para paginação
            count: Número máximo de conceitos
            include_designations: Incluir designações alternativas

        Returns:
            ValueSet expandido como dict FHIR
        """
        # Tenta cache primeiro
        cache_key = f"valueset_expand:{url}:{filter}:{offset}:{count}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        # Tenta expansão local
        if url and url in self.LOCAL_VALUESETS:
            result = self._expand_local(url, filter, offset, count)
            cache.set(cache_key, result, self.CACHE_TTL)
            return result

        # Tenta servidor FHIR externo
        result = self._expand_remote(url, valueset, filter, offset, count)
        if result:
            cache.set(cache_key, result, self.CACHE_TTL)
            return result

        # Retorna erro
        return self._create_operation_outcome(
            'error',
            'not-found',
            f"ValueSet not found: {url}"
        )

    def _expand_local(
        self,
        url: str,
        filter: Optional[str],
        offset: int,
        count: int
    ) -> Dict[str, Any]:
        """Expande ValueSet local"""
        vs_data = self.LOCAL_VALUESETS[url]
        concepts = vs_data['concepts']

        # Aplica filtro
        if filter:
            filter_lower = filter.lower()
            concepts = [
                c for c in concepts
                if filter_lower in c['display'].lower() or filter_lower in c['code'].lower()
            ]

        total = len(concepts)

        # Aplica paginação
        concepts = concepts[offset:offset + count]

        # Constrói expansion
        expansion = {
            'identifier': f"urn:uuid:{url.split('/')[-1]}-expansion",
            'timestamp': '2024-12-01T00:00:00Z',
            'total': total,
            'offset': offset,
            'contains': [
                {
                    'system': c['system'],
                    'code': c['code'],
                    'display': c['display']
                }
                for c in concepts
            ]
        }

        return {
            'resourceType': 'ValueSet',
            'url': url,
            'name': vs_data['name'],
            'title': vs_data['title'],
            'status': vs_data['status'],
            'expansion': expansion
        }

    def _expand_remote(
        self,
        url: Optional[str],
        valueset: Optional[Dict[str, Any]],
        filter: Optional[str],
        offset: int,
        count: int
    ) -> Optional[Dict[str, Any]]:
        """Expande via servidor FHIR externo"""
        try:
            params = {
                'offset': offset,
                'count': count
            }
            if url:
                params['url'] = url
            if filter:
                params['filter'] = filter

            response = requests.get(
                f"{self.fhir_server_url}/ValueSet/$expand",
                params=params,
                timeout=10
            )

            if response.status_code == 200:
                return response.json()

        except Exception as e:
            logger.warning(f"Remote $expand failed: {e}")

        return None

    def lookup(
        self,
        code: str,
        system: str,
        version: Optional[str] = None,
        coding: Optional[Dict[str, Any]] = None,
        display_language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        $lookup - Busca informações sobre um código

        Args:
            code: Código a buscar
            system: URI do CodeSystem
            version: Versão do CodeSystem
            coding: Coding completo (alternativa a code/system)
            display_language: Idioma preferido para display

        Returns:
            Parameters resource com informações do código
        """
        # Busca em ValueSets locais
        for vs_url, vs_data in self.LOCAL_VALUESETS.items():
            for concept in vs_data['concepts']:
                if concept['code'] == code and concept['system'] == system:
                    return {
                        'resourceType': 'Parameters',
                        'parameter': [
                            {'name': 'name', 'valueString': vs_data['name']},
                            {'name': 'display', 'valueString': concept['display']},
                            {'name': 'abstract', 'valueBoolean': False},
                        ]
                    }

        # Tenta servidor externo
        try:
            params = {'code': code, 'system': system}
            if version:
                params['version'] = version

            response = requests.get(
                f"{self.fhir_server_url}/CodeSystem/$lookup",
                params=params,
                timeout=10
            )

            if response.status_code == 200:
                return response.json()

        except Exception as e:
            logger.warning(f"Remote $lookup failed: {e}")

        return self._create_operation_outcome(
            'error',
            'not-found',
            f"Code not found: {code} in system {system}"
        )

    def translate(
        self,
        code: str,
        system: str,
        source: Optional[str] = None,
        target: Optional[str] = None,
        target_system: Optional[str] = None,
        concept_map_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        $translate - Traduz código entre sistemas

        Args:
            code: Código a traduzir
            system: Sistema de origem
            source: ValueSet de origem
            target: ValueSet de destino
            target_system: CodeSystem de destino
            concept_map_url: URL do ConceptMap a usar

        Returns:
            Parameters resource com traduções
        """
        matches = []

        # Busca em mapeamentos locais
        map_key = (system, target_system) if target_system else None
        if map_key and map_key in self.CONCEPT_MAPS:
            mapping = self.CONCEPT_MAPS[map_key].get(code)
            if mapping:
                matches.append({
                    'equivalence': mapping['equivalence'],
                    'concept': {
                        'system': target_system,
                        'code': mapping['code'],
                        'display': mapping['display']
                    }
                })

        # Tenta servidor externo se não encontrou
        if not matches:
            remote_result = self._translate_remote(
                code, system, source, target, target_system, concept_map_url
            )
            if remote_result:
                return remote_result

        # Constrói resposta
        if matches:
            return {
                'resourceType': 'Parameters',
                'parameter': [
                    {'name': 'result', 'valueBoolean': True},
                    *[
                        {
                            'name': 'match',
                            'part': [
                                {'name': 'equivalence', 'valueCode': m['equivalence']},
                                {'name': 'concept', 'valueCoding': m['concept']}
                            ]
                        }
                        for m in matches
                    ]
                ]
            }
        else:
            return {
                'resourceType': 'Parameters',
                'parameter': [
                    {'name': 'result', 'valueBoolean': False},
                    {'name': 'message', 'valueString': f"No translation found for {code} from {system}"}
                ]
            }

    def _translate_remote(
        self,
        code: str,
        system: str,
        source: Optional[str],
        target: Optional[str],
        target_system: Optional[str],
        concept_map_url: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        """Traduz via servidor FHIR externo"""
        try:
            params = {'code': code, 'system': system}
            if source:
                params['source'] = source
            if target:
                params['target'] = target
            if target_system:
                params['targetsystem'] = target_system
            if concept_map_url:
                params['url'] = concept_map_url

            response = requests.get(
                f"{self.fhir_server_url}/ConceptMap/$translate",
                params=params,
                timeout=10
            )

            if response.status_code == 200:
                return response.json()

        except Exception as e:
            logger.warning(f"Remote $translate failed: {e}")

        return None

    def validate_code(
        self,
        url: Optional[str] = None,
        code: Optional[str] = None,
        system: Optional[str] = None,
        display: Optional[str] = None,
        coding: Optional[Dict[str, Any]] = None,
        codeable_concept: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        $validate-code - Valida código contra ValueSet

        Returns:
            Parameters resource com resultado
        """
        # Extrai code/system de coding se fornecido
        if coding:
            code = coding.get('code', code)
            system = coding.get('system', system)
            display = coding.get('display', display)

        # Extrai de codeableConcept se fornecido
        if codeable_concept:
            codings = codeable_concept.get('coding', [])
            if codings:
                code = codings[0].get('code', code)
                system = codings[0].get('system', system)
                display = codings[0].get('display', display)

        # Valida localmente
        if url and url in self.LOCAL_VALUESETS:
            vs_data = self.LOCAL_VALUESETS[url]
            for concept in vs_data['concepts']:
                if concept['code'] == code:
                    if system and concept['system'] != system:
                        continue

                    display_valid = True
                    if display and concept['display'] != display:
                        display_valid = False

                    return {
                        'resourceType': 'Parameters',
                        'parameter': [
                            {'name': 'result', 'valueBoolean': True},
                            {'name': 'display', 'valueString': concept['display']},
                            *([{'name': 'message', 'valueString': f"Display mismatch: expected '{concept['display']}'"}]
                              if not display_valid else [])
                        ]
                    }

            return {
                'resourceType': 'Parameters',
                'parameter': [
                    {'name': 'result', 'valueBoolean': False},
                    {'name': 'message', 'valueString': f"Code '{code}' not found in ValueSet"}
                ]
            }

        # Tenta servidor externo
        try:
            params = {}
            if url:
                params['url'] = url
            if code:
                params['code'] = code
            if system:
                params['system'] = system
            if display:
                params['display'] = display

            response = requests.get(
                f"{self.fhir_server_url}/ValueSet/$validate-code",
                params=params,
                timeout=10
            )

            if response.status_code == 200:
                return response.json()

        except Exception as e:
            logger.warning(f"Remote $validate-code failed: {e}")

        return self._create_operation_outcome(
            'error',
            'not-supported',
            f"Unable to validate code against ValueSet: {url}"
        )

    def subsumes(
        self,
        code_a: str,
        code_b: str,
        system: str,
        version: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        $subsumes - Verifica relação hierárquica entre códigos

        Returns:
            Parameters com outcome: equivalent, subsumes, subsumed-by, not-subsumed
        """
        # Por padrão, só verifica igualdade
        # Implementação completa requer hierarquia de CodeSystem
        if code_a == code_b:
            outcome = 'equivalent'
        else:
            outcome = 'not-subsumed'

        return {
            'resourceType': 'Parameters',
            'parameter': [
                {'name': 'outcome', 'valueCode': outcome}
            ]
        }

    def _create_operation_outcome(
        self,
        severity: str,
        code: str,
        diagnostics: str
    ) -> Dict[str, Any]:
        """Cria OperationOutcome para erros"""
        return {
            'resourceType': 'OperationOutcome',
            'issue': [
                {
                    'severity': severity,
                    'code': code,
                    'diagnostics': diagnostics
                }
            ]
        }


# Instância global
_operations = None


def get_terminology_operations() -> TerminologyOperations:
    """Retorna instância singleton"""
    global _operations
    if _operations is None:
        _operations = TerminologyOperations()
    return _operations
