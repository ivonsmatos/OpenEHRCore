"""
FHIR Search Parameters Implementation

Sprint 36: Conformidade FHIR R4 - Search Parameters

Implementa parâmetros de busca FHIR R4:
- _include: Inclui recursos referenciados
- _revinclude: Inclui recursos que referenciam
- _has: Busca reversa por referência
- Modifiers: :exact, :contains, :missing, etc
- Chaining: patient.name, subject:Patient.name
"""

import re
import logging
from typing import Dict, Any, List, Optional, Tuple, Set, Type
from dataclasses import dataclass, field
from enum import Enum
from django.db.models import QuerySet, Q
from rest_framework.request import Request

logger = logging.getLogger(__name__)


class SearchParamType(Enum):
    """Tipos de parâmetros de busca FHIR"""
    NUMBER = 'number'
    DATE = 'date'
    STRING = 'string'
    TOKEN = 'token'
    REFERENCE = 'reference'
    COMPOSITE = 'composite'
    QUANTITY = 'quantity'
    URI = 'uri'
    SPECIAL = 'special'


class SearchModifier(Enum):
    """Modificadores de busca FHIR"""
    EXACT = 'exact'
    CONTAINS = 'contains'
    TEXT = 'text'
    IN = 'in'
    NOT_IN = 'not-in'
    BELOW = 'below'
    ABOVE = 'above'
    MISSING = 'missing'
    IDENTIFIER = 'identifier'
    OF_TYPE = 'of-type'


class SearchPrefix(Enum):
    """Prefixos de comparação FHIR"""
    EQ = 'eq'  # Equal
    NE = 'ne'  # Not Equal
    GT = 'gt'  # Greater Than
    LT = 'lt'  # Less Than
    GE = 'ge'  # Greater or Equal
    LE = 'le'  # Less or Equal
    SA = 'sa'  # Starts After
    EB = 'eb'  # Ends Before
    AP = 'ap'  # Approximately


@dataclass
class SearchParameter:
    """Definição de um parâmetro de busca"""
    name: str
    type: SearchParamType
    path: str  # FHIRPath ou campo Django
    django_field: Optional[str] = None  # Campo no model Django
    target_resources: List[str] = field(default_factory=list)  # Para references
    modifiers: List[SearchModifier] = field(default_factory=list)
    description: str = ""


@dataclass
class IncludeSpec:
    """Especificação de _include ou _revinclude"""
    source_type: str
    search_param: str
    target_type: Optional[str] = None
    iterate: bool = False  # :iterate modifier


@dataclass
class SearchResult:
    """Resultado de uma busca FHIR"""
    resources: List[Dict[str, Any]]
    total: int
    included: List[Dict[str, Any]] = field(default_factory=list)
    link: List[Dict[str, str]] = field(default_factory=list)


class FHIRSearchParser:
    """
    Parser para parâmetros de busca FHIR

    Processa query strings FHIR e converte para filtros Django
    """

    # Padrão para parâmetros com modifier
    PARAM_PATTERN = re.compile(r'^([a-zA-Z_][a-zA-Z0-9_-]*)(?::([a-zA-Z-]+))?$')

    # Padrão para valores com prefixo
    PREFIX_PATTERN = re.compile(r'^(eq|ne|gt|lt|ge|le|sa|eb|ap)?(.+)$')

    # Padrão para _include/_revinclude
    INCLUDE_PATTERN = re.compile(r'^([A-Z][a-zA-Z]+):([a-zA-Z]+)(?::([A-Z][a-zA-Z]+))?$')

    # Padrão para _has
    HAS_PATTERN = re.compile(r'^([A-Z][a-zA-Z]+):([a-zA-Z]+)(?::(.+))?$')

    def parse_param(self, param_name: str) -> Tuple[str, Optional[SearchModifier]]:
        """
        Parse nome do parâmetro e extrai modifier

        Returns:
            Tuple de (nome_base, modifier ou None)
        """
        match = self.PARAM_PATTERN.match(param_name)
        if not match:
            return param_name, None

        name = match.group(1)
        modifier_str = match.group(2)

        modifier = None
        if modifier_str:
            try:
                modifier = SearchModifier(modifier_str)
            except ValueError:
                logger.warning(f"Unknown search modifier: {modifier_str}")

        return name, modifier

    def parse_value(self, value: str, param_type: SearchParamType) -> Tuple[Optional[SearchPrefix], str]:
        """
        Parse valor do parâmetro e extrai prefixo

        Returns:
            Tuple de (prefixo ou None, valor)
        """
        if param_type not in [SearchParamType.NUMBER, SearchParamType.DATE, SearchParamType.QUANTITY]:
            return None, value

        match = self.PREFIX_PATTERN.match(value)
        if not match:
            return None, value

        prefix_str = match.group(1)
        actual_value = match.group(2)

        prefix = None
        if prefix_str:
            try:
                prefix = SearchPrefix(prefix_str)
            except ValueError:
                return None, value

        return prefix, actual_value

    def parse_include(self, value: str) -> Optional[IncludeSpec]:
        """
        Parse valor de _include ou _revinclude

        Formato: SourceType:searchParam[:TargetType]
        Exemplo: Patient:organization, Observation:subject:Patient

        Returns:
            IncludeSpec ou None se inválido
        """
        match = self.INCLUDE_PATTERN.match(value)
        if not match:
            logger.warning(f"Invalid _include format: {value}")
            return None

        return IncludeSpec(
            source_type=match.group(1),
            search_param=match.group(2),
            target_type=match.group(3)
        )

    def parse_token(self, value: str) -> Tuple[Optional[str], str]:
        """
        Parse valor de token (system|code)

        Returns:
            Tuple de (system ou None, code)
        """
        if '|' in value:
            parts = value.split('|', 1)
            system = parts[0] if parts[0] else None
            code = parts[1]
            return system, code
        return None, value


class FHIRSearchMixin:
    """
    Mixin para ViewSets com suporte a busca FHIR

    Adiciona suporte a:
    - _include: Inclui recursos referenciados
    - _revinclude: Inclui recursos que referenciam este
    - _has: Busca reversa por referência
    - Modifiers padrão FHIR
    - Paginação FHIR (_count, _offset)
    """

    # Configuração de parâmetros de busca por resource type
    # Override nas subclasses
    search_parameters: Dict[str, SearchParameter] = {}

    # Mapeamento de referências para _include
    # Formato: {search_param: (model_class, foreign_key_field)}
    include_references: Dict[str, Tuple[Any, str]] = {}

    # Mapeamento para _revinclude
    # Formato: {ResourceType:param: (model_class, field_to_this)}
    revinclude_references: Dict[str, Tuple[Any, str]] = {}

    # Parser compartilhado
    _parser = FHIRSearchParser()

    def apply_fhir_search(self, request: Request, queryset: QuerySet) -> Tuple[QuerySet, Dict[str, Any]]:
        """
        Aplica parâmetros de busca FHIR ao queryset

        Returns:
            Tuple de (queryset filtrado, metadata com includes)
        """
        metadata = {
            'includes': [],
            'total': 0,
            'links': []
        }

        # Processa parâmetros de busca normais
        for param_name, values in request.query_params.lists():
            # Ignora parâmetros especiais
            if param_name.startswith('_'):
                continue

            base_name, modifier = self._parser.parse_param(param_name)

            if base_name in self.search_parameters:
                param_def = self.search_parameters[base_name]
                for value in values:
                    queryset = self._apply_search_param(
                        queryset, param_def, value, modifier
                    )

        # Aplica _has
        has_params = request.query_params.getlist('_has')
        for has_value in has_params:
            queryset = self._apply_has(queryset, has_value)

        # Conta total antes de paginação
        metadata['total'] = queryset.count()

        # Aplica paginação FHIR
        count = int(request.query_params.get('_count', 20))
        offset = int(request.query_params.get('_offset', 0))

        # Limita _count a máximo de 100
        count = min(count, 100)
        queryset = queryset[offset:offset + count]

        # Processa _include
        include_params = request.query_params.getlist('_include')
        for include_value in include_params:
            included = self._process_include(queryset, include_value)
            metadata['includes'].extend(included)

        # Processa _revinclude
        revinclude_params = request.query_params.getlist('_revinclude')
        for revinclude_value in revinclude_params:
            included = self._process_revinclude(queryset, revinclude_value)
            metadata['includes'].extend(included)

        # Gera links de paginação
        metadata['links'] = self._generate_pagination_links(
            request, metadata['total'], count, offset
        )

        return queryset, metadata

    def _apply_search_param(
        self,
        queryset: QuerySet,
        param: SearchParameter,
        value: str,
        modifier: Optional[SearchModifier]
    ) -> QuerySet:
        """Aplica um parâmetro de busca individual"""
        django_field = param.django_field or param.path

        # Processa por tipo
        if param.type == SearchParamType.STRING:
            return self._apply_string_search(queryset, django_field, value, modifier)

        elif param.type == SearchParamType.TOKEN:
            return self._apply_token_search(queryset, django_field, value, modifier)

        elif param.type == SearchParamType.REFERENCE:
            return self._apply_reference_search(queryset, django_field, value, modifier)

        elif param.type == SearchParamType.DATE:
            prefix, actual_value = self._parser.parse_value(value, param.type)
            return self._apply_date_search(queryset, django_field, actual_value, prefix)

        elif param.type == SearchParamType.NUMBER:
            prefix, actual_value = self._parser.parse_value(value, param.type)
            return self._apply_number_search(queryset, django_field, actual_value, prefix)

        return queryset

    def _apply_string_search(
        self,
        queryset: QuerySet,
        field: str,
        value: str,
        modifier: Optional[SearchModifier]
    ) -> QuerySet:
        """Aplica busca de string com modifiers"""
        if modifier == SearchModifier.EXACT:
            return queryset.filter(**{field: value})

        elif modifier == SearchModifier.CONTAINS:
            return queryset.filter(**{f"{field}__icontains": value})

        elif modifier == SearchModifier.MISSING:
            is_missing = value.lower() == 'true'
            if is_missing:
                return queryset.filter(**{f"{field}__isnull": True})
            else:
                return queryset.filter(**{f"{field}__isnull": False})

        else:
            # Default: starts with (case insensitive)
            return queryset.filter(**{f"{field}__istartswith": value})

    def _apply_token_search(
        self,
        queryset: QuerySet,
        field: str,
        value: str,
        modifier: Optional[SearchModifier]
    ) -> QuerySet:
        """Aplica busca de token (code|system)"""
        system, code = self._parser.parse_token(value)

        if system and code:
            # Busca com system e code
            # Assume campo JSONField com estrutura coding
            return queryset.filter(
                **{f"{field}__coding__contains": [{'system': system, 'code': code}]}
            )
        elif code:
            # Busca apenas por code
            return queryset.filter(
                Q(**{f"{field}__coding__contains": [{'code': code}]}) |
                Q(**{f"{field}__code": code}) |
                Q(**{field: code})
            )

        return queryset

    def _apply_reference_search(
        self,
        queryset: QuerySet,
        field: str,
        value: str,
        modifier: Optional[SearchModifier]
    ) -> QuerySet:
        """Aplica busca de referência"""
        # Valor pode ser: ResourceType/id ou apenas id
        if '/' in value:
            # Full reference
            return queryset.filter(**{f"{field}__reference": value})
        else:
            # Apenas ID
            return queryset.filter(
                Q(**{f"{field}__reference__endswith": f"/{value}"}) |
                Q(**{f"{field}__id": value})
            )

    def _apply_date_search(
        self,
        queryset: QuerySet,
        field: str,
        value: str,
        prefix: Optional[SearchPrefix]
    ) -> QuerySet:
        """Aplica busca de data com prefixos"""
        if prefix == SearchPrefix.EQ or prefix is None:
            return queryset.filter(**{f"{field}__date": value})
        elif prefix == SearchPrefix.NE:
            return queryset.exclude(**{f"{field}__date": value})
        elif prefix == SearchPrefix.GT:
            return queryset.filter(**{f"{field}__gt": value})
        elif prefix == SearchPrefix.LT:
            return queryset.filter(**{f"{field}__lt": value})
        elif prefix == SearchPrefix.GE:
            return queryset.filter(**{f"{field}__gte": value})
        elif prefix == SearchPrefix.LE:
            return queryset.filter(**{f"{field}__lte": value})

        return queryset

    def _apply_number_search(
        self,
        queryset: QuerySet,
        field: str,
        value: str,
        prefix: Optional[SearchPrefix]
    ) -> QuerySet:
        """Aplica busca numérica com prefixos"""
        try:
            num_value = float(value)
        except ValueError:
            return queryset

        if prefix == SearchPrefix.EQ or prefix is None:
            return queryset.filter(**{field: num_value})
        elif prefix == SearchPrefix.NE:
            return queryset.exclude(**{field: num_value})
        elif prefix == SearchPrefix.GT:
            return queryset.filter(**{f"{field}__gt": num_value})
        elif prefix == SearchPrefix.LT:
            return queryset.filter(**{f"{field}__lt": num_value})
        elif prefix == SearchPrefix.GE:
            return queryset.filter(**{f"{field}__gte": num_value})
        elif prefix == SearchPrefix.LE:
            return queryset.filter(**{f"{field}__lte": num_value})

        return queryset

    def _apply_has(self, queryset: QuerySet, has_value: str) -> QuerySet:
        """
        Aplica _has para busca reversa

        Formato: _has:Observation:subject:code=vital-signs
        """
        # TODO: Implementar _has completo
        logger.info(f"_has not fully implemented: {has_value}")
        return queryset

    def _process_include(self, queryset: QuerySet, include_value: str) -> List[Dict[str, Any]]:
        """
        Processa _include e retorna recursos incluídos

        Formato: Patient:organization
        """
        spec = self._parser.parse_include(include_value)
        if not spec:
            return []

        if spec.search_param not in self.include_references:
            logger.warning(f"Unknown _include param: {spec.search_param}")
            return []

        model_class, fk_field = self.include_references[spec.search_param]

        # Coleta IDs referenciados
        referenced_ids = set()
        for obj in queryset:
            ref_value = getattr(obj, fk_field, None)
            if ref_value:
                # Extrai ID da referência
                if isinstance(ref_value, dict):
                    ref = ref_value.get('reference', '')
                    if '/' in ref:
                        referenced_ids.add(ref.split('/')[-1])
                elif isinstance(ref_value, str):
                    if '/' in ref_value:
                        referenced_ids.add(ref_value.split('/')[-1])
                    else:
                        referenced_ids.add(ref_value)

        if not referenced_ids:
            return []

        # Busca recursos referenciados
        included_resources = []
        try:
            included_objects = model_class.objects.filter(id__in=referenced_ids)
            for obj in included_objects:
                if hasattr(obj, 'to_fhir'):
                    included_resources.append(obj.to_fhir())
        except Exception as e:
            logger.error(f"Error processing _include: {e}")

        return included_resources

    def _process_revinclude(self, queryset: QuerySet, revinclude_value: str) -> List[Dict[str, Any]]:
        """
        Processa _revinclude e retorna recursos que referenciam

        Formato: Observation:subject
        """
        if revinclude_value not in self.revinclude_references:
            logger.warning(f"Unknown _revinclude: {revinclude_value}")
            return []

        model_class, ref_field = self.revinclude_references[revinclude_value]

        # Coleta IDs dos recursos principais
        main_ids = [str(obj.id) for obj in queryset]
        if not main_ids:
            return []

        # Busca recursos que referenciam
        included_resources = []
        try:
            # Cria filtro para referências
            q_filter = Q()
            for main_id in main_ids:
                q_filter |= Q(**{f"{ref_field}__contains": main_id})

            included_objects = model_class.objects.filter(q_filter)
            for obj in included_objects:
                if hasattr(obj, 'to_fhir'):
                    included_resources.append(obj.to_fhir())
        except Exception as e:
            logger.error(f"Error processing _revinclude: {e}")

        return included_resources

    def _generate_pagination_links(
        self,
        request: Request,
        total: int,
        count: int,
        offset: int
    ) -> List[Dict[str, str]]:
        """Gera links de paginação FHIR"""
        links = []
        base_url = request.build_absolute_uri(request.path)

        # Self
        links.append({
            'relation': 'self',
            'url': f"{base_url}?_count={count}&_offset={offset}"
        })

        # First
        links.append({
            'relation': 'first',
            'url': f"{base_url}?_count={count}&_offset=0"
        })

        # Previous
        if offset > 0:
            prev_offset = max(0, offset - count)
            links.append({
                'relation': 'previous',
                'url': f"{base_url}?_count={count}&_offset={prev_offset}"
            })

        # Next
        if offset + count < total:
            next_offset = offset + count
            links.append({
                'relation': 'next',
                'url': f"{base_url}?_count={count}&_offset={next_offset}"
            })

        # Last
        if total > count:
            last_offset = ((total - 1) // count) * count
            links.append({
                'relation': 'last',
                'url': f"{base_url}?_count={count}&_offset={last_offset}"
            })

        return links

    def build_search_bundle(
        self,
        resources: List[Dict[str, Any]],
        metadata: Dict[str, Any],
        request: Request
    ) -> Dict[str, Any]:
        """
        Constrói Bundle de busca FHIR

        Returns:
            Bundle FHIR com resultados e includes
        """
        entries = []

        # Adiciona recursos principais
        for resource in resources:
            entries.append({
                'fullUrl': f"{request.build_absolute_uri('/')}{resource['resourceType']}/{resource['id']}",
                'resource': resource,
                'search': {
                    'mode': 'match'
                }
            })

        # Adiciona recursos incluídos
        for included in metadata.get('includes', []):
            entries.append({
                'fullUrl': f"{request.build_absolute_uri('/')}{included['resourceType']}/{included['id']}",
                'resource': included,
                'search': {
                    'mode': 'include'
                }
            })

        bundle = {
            'resourceType': 'Bundle',
            'type': 'searchset',
            'total': metadata.get('total', len(resources)),
            'link': metadata.get('links', []),
            'entry': entries
        }

        return bundle
