"""
FHIR R4 Data Types - Conformidade 100%

Módulo com tipos de dados FHIR R4 para garantir conformidade total.
Baseado em: https://hl7.org/fhir/R4/datatypes.html

Sprint 36: Correções de conformidade FHIR R4
"""

from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, date
from decimal import Decimal
import re
import uuid


# =============================================================================
# FHIR Primitive Types
# =============================================================================

class FHIRInstant:
    """
    FHIR instant - timestamp with timezone (millisecond precision)
    Format: YYYY-MM-DDThh:mm:ss.sss+zz:zz
    """
    PATTERN = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,3})?(Z|[+-]\d{2}:\d{2})$'

    @staticmethod
    def from_datetime(dt: datetime) -> str:
        """Converte datetime para FHIR instant"""
        if dt.tzinfo is None:
            # Assume UTC se não tiver timezone
            return dt.strftime('%Y-%m-%dT%H:%M:%S.') + f'{dt.microsecond // 1000:03d}Z'
        return dt.strftime('%Y-%m-%dT%H:%M:%S.') + f'{dt.microsecond // 1000:03d}' + dt.strftime('%z')[:3] + ':' + dt.strftime('%z')[3:]

    @staticmethod
    def validate(value: str) -> bool:
        """Valida formato FHIR instant"""
        return bool(re.match(FHIRInstant.PATTERN, value))


class FHIRDateTime:
    """
    FHIR dateTime - date/time with variable precision
    Formats: YYYY, YYYY-MM, YYYY-MM-DD, YYYY-MM-DDThh:mm:ss+zz:zz
    """
    PATTERN = r'^(\d{4})(-\d{2})?(-\d{2})?(T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2}))?$'

    @staticmethod
    def from_datetime(dt: datetime, precision: str = 'full') -> str:
        """
        Converte datetime para FHIR dateTime
        precision: 'year', 'month', 'day', 'full'
        """
        if precision == 'year':
            return dt.strftime('%Y')
        elif precision == 'month':
            return dt.strftime('%Y-%m')
        elif precision == 'day':
            return dt.strftime('%Y-%m-%d')
        else:
            return FHIRInstant.from_datetime(dt)

    @staticmethod
    def validate(value: str) -> bool:
        """Valida formato FHIR dateTime"""
        return bool(re.match(FHIRDateTime.PATTERN, value))


# =============================================================================
# FHIR Complex Types
# =============================================================================

@dataclass
class Identifier:
    """
    FHIR Identifier - identificador único
    https://hl7.org/fhir/R4/datatypes.html#Identifier
    """
    value: str
    system: Optional[str] = None
    use: Optional[str] = None  # usual | official | temp | secondary | old
    type: Optional[Dict[str, Any]] = None  # CodeableConcept
    period: Optional[Dict[str, str]] = None  # Period
    assigner: Optional[Dict[str, str]] = None  # Reference(Organization)

    def to_fhir(self) -> Dict[str, Any]:
        """Converte para dict FHIR"""
        result = {'value': self.value}
        if self.system:
            result['system'] = self.system
        if self.use:
            result['use'] = self.use
        if self.type:
            result['type'] = self.type
        if self.period:
            result['period'] = self.period
        if self.assigner:
            result['assigner'] = self.assigner
        return result

    @classmethod
    def from_fhir(cls, data: Dict[str, Any]) -> 'Identifier':
        """Cria Identifier a partir de dict FHIR"""
        return cls(
            value=data.get('value', ''),
            system=data.get('system'),
            use=data.get('use'),
            type=data.get('type'),
            period=data.get('period'),
            assigner=data.get('assigner')
        )


@dataclass
class Coding:
    """
    FHIR Coding - código de terminologia
    https://hl7.org/fhir/R4/datatypes.html#Coding
    """
    code: str
    system: Optional[str] = None
    version: Optional[str] = None
    display: Optional[str] = None
    userSelected: Optional[bool] = None

    def to_fhir(self) -> Dict[str, Any]:
        result = {'code': self.code}
        if self.system:
            result['system'] = self.system
        if self.version:
            result['version'] = self.version
        if self.display:
            result['display'] = self.display
        if self.userSelected is not None:
            result['userSelected'] = self.userSelected
        return result

    @classmethod
    def from_fhir(cls, data: Dict[str, Any]) -> 'Coding':
        return cls(
            code=data.get('code', ''),
            system=data.get('system'),
            version=data.get('version'),
            display=data.get('display'),
            userSelected=data.get('userSelected')
        )


@dataclass
class CodeableConcept:
    """
    FHIR CodeableConcept - conceito com múltiplos códigos
    https://hl7.org/fhir/R4/datatypes.html#CodeableConcept
    """
    coding: List[Coding] = field(default_factory=list)
    text: Optional[str] = None

    def to_fhir(self) -> Dict[str, Any]:
        result = {}
        if self.coding:
            result['coding'] = [c.to_fhir() for c in self.coding]
        if self.text:
            result['text'] = self.text
        return result

    @classmethod
    def from_fhir(cls, data: Dict[str, Any]) -> 'CodeableConcept':
        coding = [Coding.from_fhir(c) for c in data.get('coding', [])]
        return cls(coding=coding, text=data.get('text'))

    @classmethod
    def simple(cls, code: str, system: str, display: str, text: Optional[str] = None) -> 'CodeableConcept':
        """Cria CodeableConcept simples com um código"""
        return cls(
            coding=[Coding(code=code, system=system, display=display)],
            text=text or display
        )


@dataclass
class Reference:
    """
    FHIR Reference - referência a outro recurso
    https://hl7.org/fhir/R4/references.html
    """
    reference: Optional[str] = None  # Literal reference
    type: Optional[str] = None  # Resource type
    identifier: Optional[Identifier] = None  # Logical reference
    display: Optional[str] = None  # Text alternative

    def to_fhir(self) -> Dict[str, Any]:
        result = {}
        if self.reference:
            result['reference'] = self.reference
        if self.type:
            result['type'] = self.type
        if self.identifier:
            result['identifier'] = self.identifier.to_fhir()
        if self.display:
            result['display'] = self.display
        return result

    @classmethod
    def from_fhir(cls, data: Dict[str, Any]) -> 'Reference':
        identifier = None
        if 'identifier' in data:
            identifier = Identifier.from_fhir(data['identifier'])
        return cls(
            reference=data.get('reference'),
            type=data.get('type'),
            identifier=identifier,
            display=data.get('display')
        )

    @classmethod
    def to_resource(cls, resource_type: str, resource_id: str, display: Optional[str] = None) -> 'Reference':
        """Cria referência para recurso"""
        return cls(
            reference=f'{resource_type}/{resource_id}',
            type=resource_type,
            display=display
        )


@dataclass
class Period:
    """
    FHIR Period - intervalo de tempo
    https://hl7.org/fhir/R4/datatypes.html#Period
    """
    start: Optional[str] = None  # dateTime
    end: Optional[str] = None  # dateTime

    def to_fhir(self) -> Dict[str, str]:
        result = {}
        if self.start:
            result['start'] = self.start
        if self.end:
            result['end'] = self.end
        return result

    @classmethod
    def from_datetime(cls, start: Optional[datetime] = None, end: Optional[datetime] = None) -> 'Period':
        return cls(
            start=FHIRDateTime.from_datetime(start) if start else None,
            end=FHIRDateTime.from_datetime(end) if end else None
        )


@dataclass
class Quantity:
    """
    FHIR Quantity - valor com unidade
    https://hl7.org/fhir/R4/datatypes.html#Quantity
    """
    value: Optional[Decimal] = None
    comparator: Optional[str] = None  # < | <= | >= | >
    unit: Optional[str] = None
    system: Optional[str] = None  # http://unitsofmeasure.org
    code: Optional[str] = None

    def to_fhir(self) -> Dict[str, Any]:
        result = {}
        if self.value is not None:
            result['value'] = float(self.value)
        if self.comparator:
            result['comparator'] = self.comparator
        if self.unit:
            result['unit'] = self.unit
        if self.system:
            result['system'] = self.system
        if self.code:
            result['code'] = self.code
        return result

    @classmethod
    def ucum(cls, value: Decimal, unit: str, code: Optional[str] = None) -> 'Quantity':
        """Cria Quantity com sistema UCUM"""
        return cls(
            value=value,
            unit=unit,
            system='http://unitsofmeasure.org',
            code=code or unit
        )


@dataclass
class HumanName:
    """
    FHIR HumanName - nome de pessoa
    https://hl7.org/fhir/R4/datatypes.html#HumanName
    """
    use: Optional[str] = None  # usual | official | temp | nickname | anonymous | old | maiden
    text: Optional[str] = None
    family: Optional[str] = None
    given: List[str] = field(default_factory=list)
    prefix: List[str] = field(default_factory=list)
    suffix: List[str] = field(default_factory=list)
    period: Optional[Period] = None

    def to_fhir(self) -> Dict[str, Any]:
        result = {}
        if self.use:
            result['use'] = self.use
        if self.text:
            result['text'] = self.text
        if self.family:
            result['family'] = self.family
        if self.given:
            result['given'] = self.given
        if self.prefix:
            result['prefix'] = self.prefix
        if self.suffix:
            result['suffix'] = self.suffix
        if self.period:
            result['period'] = self.period.to_fhir()
        return result


@dataclass
class ContactPoint:
    """
    FHIR ContactPoint - telefone, email, etc
    https://hl7.org/fhir/R4/datatypes.html#ContactPoint
    """
    system: Optional[str] = None  # phone | fax | email | pager | url | sms | other
    value: Optional[str] = None
    use: Optional[str] = None  # home | work | temp | old | mobile
    rank: Optional[int] = None
    period: Optional[Period] = None

    def to_fhir(self) -> Dict[str, Any]:
        result = {}
        if self.system:
            result['system'] = self.system
        if self.value:
            result['value'] = self.value
        if self.use:
            result['use'] = self.use
        if self.rank is not None:
            result['rank'] = self.rank
        if self.period:
            result['period'] = self.period.to_fhir()
        return result


@dataclass
class Address:
    """
    FHIR Address - endereço
    https://hl7.org/fhir/R4/datatypes.html#Address
    """
    use: Optional[str] = None  # home | work | temp | old | billing
    type: Optional[str] = None  # postal | physical | both
    text: Optional[str] = None
    line: List[str] = field(default_factory=list)
    city: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    postalCode: Optional[str] = None
    country: Optional[str] = None
    period: Optional[Period] = None

    def to_fhir(self) -> Dict[str, Any]:
        result = {}
        if self.use:
            result['use'] = self.use
        if self.type:
            result['type'] = self.type
        if self.text:
            result['text'] = self.text
        if self.line:
            result['line'] = self.line
        if self.city:
            result['city'] = self.city
        if self.district:
            result['district'] = self.district
        if self.state:
            result['state'] = self.state
        if self.postalCode:
            result['postalCode'] = self.postalCode
        if self.country:
            result['country'] = self.country
        if self.period:
            result['period'] = self.period.to_fhir()
        return result


# =============================================================================
# Brazilian Extensions / Identifiers
# =============================================================================

class BrazilianIdentifiers:
    """
    Sistemas de identificação brasileiros para FHIR
    Baseado em: https://rnds-fhir.saude.gov.br/
    """

    # Sistemas de identificação
    CPF_SYSTEM = 'http://rnds.saude.gov.br/fhir/r4/NamingSystem/cpf'
    CNS_SYSTEM = 'http://rnds.saude.gov.br/fhir/r4/NamingSystem/cns'
    CNES_SYSTEM = 'http://rnds.saude.gov.br/fhir/r4/NamingSystem/cnes'
    CRM_SYSTEM = 'http://rnds.saude.gov.br/fhir/r4/NamingSystem/crm'
    COREN_SYSTEM = 'http://rnds.saude.gov.br/fhir/r4/NamingSystem/coren'
    RG_SYSTEM = 'http://rnds.saude.gov.br/fhir/r4/NamingSystem/rg'

    # Terminologias
    TUSS_SYSTEM = 'http://www.ans.gov.br/tuss'
    CIAP2_SYSTEM = 'http://hl7.org/fhir/sid/icpc-2'
    CID10_SYSTEM = 'http://hl7.org/fhir/sid/icd-10'
    CBH_SYSTEM = 'http://www.saude.gov.br/fhir/r4/CodeSystem/BRCBHPM'

    @staticmethod
    def cpf_identifier(cpf: str) -> Identifier:
        """Cria identificador CPF"""
        return Identifier(
            system=BrazilianIdentifiers.CPF_SYSTEM,
            value=cpf.replace('.', '').replace('-', ''),
            use='official',
            type=CodeableConcept.simple(
                code='TAX',
                system='http://terminology.hl7.org/CodeSystem/v2-0203',
                display='Tax ID number'
            ).to_fhir()
        )

    @staticmethod
    def cns_identifier(cns: str) -> Identifier:
        """Cria identificador CNS (Cartão Nacional de Saúde)"""
        return Identifier(
            system=BrazilianIdentifiers.CNS_SYSTEM,
            value=cns.replace(' ', ''),
            use='official',
            type=CodeableConcept.simple(
                code='HC',
                system='http://terminology.hl7.org/CodeSystem/v2-0203',
                display='Health Card Number'
            ).to_fhir()
        )

    @staticmethod
    def cnes_identifier(cnes: str) -> Identifier:
        """Cria identificador CNES (estabelecimento de saúde)"""
        return Identifier(
            system=BrazilianIdentifiers.CNES_SYSTEM,
            value=cnes,
            use='official'
        )

    @staticmethod
    def crm_identifier(crm: str, uf: str) -> Identifier:
        """Cria identificador CRM (médico)"""
        return Identifier(
            system=BrazilianIdentifiers.CRM_SYSTEM,
            value=f'{crm}/{uf}',
            use='official',
            type=CodeableConcept.simple(
                code='MD',
                system='http://terminology.hl7.org/CodeSystem/v2-0203',
                display='Medical License number'
            ).to_fhir()
        )


# =============================================================================
# Identifier List Helper
# =============================================================================

class IdentifierList:
    """
    Helper para gerenciar lista de Identifiers (padrão FHIR)
    """

    def __init__(self, identifiers: Optional[List[Dict[str, Any]]] = None):
        self._identifiers: List[Identifier] = []
        if identifiers:
            for id_dict in identifiers:
                self._identifiers.append(Identifier.from_fhir(id_dict))

    def add(self, identifier: Identifier) -> 'IdentifierList':
        """Adiciona identificador"""
        self._identifiers.append(identifier)
        return self

    def add_simple(self, system: str, value: str, use: str = 'official') -> 'IdentifierList':
        """Adiciona identificador simples"""
        self._identifiers.append(Identifier(system=system, value=value, use=use))
        return self

    def get_by_system(self, system: str) -> Optional[Identifier]:
        """Busca identificador por sistema"""
        for identifier in self._identifiers:
            if identifier.system == system:
                return identifier
        return None

    def get_cpf(self) -> Optional[str]:
        """Extrai CPF se existir"""
        identifier = self.get_by_system(BrazilianIdentifiers.CPF_SYSTEM)
        return identifier.value if identifier else None

    def get_cns(self) -> Optional[str]:
        """Extrai CNS se existir"""
        identifier = self.get_by_system(BrazilianIdentifiers.CNS_SYSTEM)
        return identifier.value if identifier else None

    def to_fhir(self) -> List[Dict[str, Any]]:
        """Converte para lista FHIR"""
        return [i.to_fhir() for i in self._identifiers]

    def __len__(self) -> int:
        return len(self._identifiers)

    def __iter__(self):
        return iter(self._identifiers)


# =============================================================================
# Meta Resource Element
# =============================================================================

@dataclass
class Meta:
    """
    FHIR Meta - metadados do recurso
    https://hl7.org/fhir/R4/resource.html#Meta
    """
    versionId: Optional[str] = None
    lastUpdated: Optional[str] = None  # instant
    source: Optional[str] = None  # uri
    profile: List[str] = field(default_factory=list)
    security: List[Coding] = field(default_factory=list)
    tag: List[Coding] = field(default_factory=list)

    def to_fhir(self) -> Dict[str, Any]:
        result = {}
        if self.versionId:
            result['versionId'] = self.versionId
        if self.lastUpdated:
            result['lastUpdated'] = self.lastUpdated
        if self.source:
            result['source'] = self.source
        if self.profile:
            result['profile'] = self.profile
        if self.security:
            result['security'] = [s.to_fhir() for s in self.security]
        if self.tag:
            result['tag'] = [t.to_fhir() for t in self.tag]
        return result


# =============================================================================
# Extension Support
# =============================================================================

@dataclass
class Extension:
    """
    FHIR Extension - extensão de recurso
    https://hl7.org/fhir/R4/extensibility.html
    """
    url: str
    valueString: Optional[str] = None
    valueCode: Optional[str] = None
    valueBoolean: Optional[bool] = None
    valueInteger: Optional[int] = None
    valueDecimal: Optional[Decimal] = None
    valueDateTime: Optional[str] = None
    valueCoding: Optional[Coding] = None
    valueCodeableConcept: Optional[CodeableConcept] = None
    valueReference: Optional[Reference] = None
    valueQuantity: Optional[Quantity] = None
    valueIdentifier: Optional[Identifier] = None
    extension: List['Extension'] = field(default_factory=list)  # Nested extensions

    def to_fhir(self) -> Dict[str, Any]:
        result = {'url': self.url}

        # Apenas um value[x] deve estar presente
        if self.valueString is not None:
            result['valueString'] = self.valueString
        elif self.valueCode is not None:
            result['valueCode'] = self.valueCode
        elif self.valueBoolean is not None:
            result['valueBoolean'] = self.valueBoolean
        elif self.valueInteger is not None:
            result['valueInteger'] = self.valueInteger
        elif self.valueDecimal is not None:
            result['valueDecimal'] = float(self.valueDecimal)
        elif self.valueDateTime is not None:
            result['valueDateTime'] = self.valueDateTime
        elif self.valueCoding is not None:
            result['valueCoding'] = self.valueCoding.to_fhir()
        elif self.valueCodeableConcept is not None:
            result['valueCodeableConcept'] = self.valueCodeableConcept.to_fhir()
        elif self.valueReference is not None:
            result['valueReference'] = self.valueReference.to_fhir()
        elif self.valueQuantity is not None:
            result['valueQuantity'] = self.valueQuantity.to_fhir()
        elif self.valueIdentifier is not None:
            result['valueIdentifier'] = self.valueIdentifier.to_fhir()
        elif self.extension:
            result['extension'] = [e.to_fhir() for e in self.extension]

        return result


# =============================================================================
# Brazilian Extensions (RNDS)
# =============================================================================

class BrazilianExtensions:
    """
    Extensões brasileiras para FHIR (RNDS)
    """

    # URLs de extensões
    RACE_URL = 'http://rnds.saude.gov.br/fhir/r4/StructureDefinition/BRRacaCorEtnia-1.0'
    NATIONALITY_URL = 'http://rnds.saude.gov.br/fhir/r4/StructureDefinition/BRNacionalidade'
    NATURALIZATION_URL = 'http://rnds.saude.gov.br/fhir/r4/StructureDefinition/BRNaturalizacao'
    PARENTS_URL = 'http://rnds.saude.gov.br/fhir/r4/StructureDefinition/BRParentesIndividuo-1.0'
    BIRTH_CITY_URL = 'http://rnds.saude.gov.br/fhir/r4/StructureDefinition/BRMunicipioNascimento'

    @staticmethod
    def race_extension(race_code: str, race_display: str) -> Extension:
        """Extensão de raça/cor/etnia"""
        return Extension(
            url=BrazilianExtensions.RACE_URL,
            valueCoding=Coding(
                system='http://www.saude.gov.br/fhir/r4/CodeSystem/BRRacaCor',
                code=race_code,
                display=race_display
            )
        )

    @staticmethod
    def nationality_extension(country_code: str = 'BR') -> Extension:
        """Extensão de nacionalidade"""
        return Extension(
            url=BrazilianExtensions.NATIONALITY_URL,
            valueCode=country_code
        )
