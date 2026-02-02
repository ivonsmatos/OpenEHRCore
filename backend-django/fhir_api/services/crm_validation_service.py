"""
CRM Validation Service - Validação de Registros em Conselhos Profissionais

Sprint 37+: Validação de CRM/COREN/CRO seguindo padrões LGPD, FHIR, GDPR.

Funcionalidades:
- Validação de formato de número de conselho
- Consulta opcional à API do CFM (quando disponível)
- Registro de AuditEvent para cada validação (LGPD compliance)
- Armazenamento em FHIR Practitioner.identifier

Referências:
- CFM Web Service: https://crmvirtual.cfm.org.br
- LGPD: Lei nº 13.709/2018 (Art. 6, 7, 18)
- FHIR R4: Practitioner.identifier
- GDPR: Art. 5, 6
"""

import re
import uuid
import logging
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

import requests
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class ConselhoTipo(Enum):
    """Tipos de conselhos profissionais de saúde no Brasil"""
    CRM = "CRM"      # Conselho Regional de Medicina
    COREN = "COREN"  # Conselho Regional de Enfermagem
    CRO = "CRO"      # Conselho Regional de Odontologia
    CRF = "CRF"      # Conselho Regional de Farmácia
    CREFITO = "CREFITO"  # Conselho Regional de Fisioterapia
    CRN = "CRN"      # Conselho Regional de Nutrição
    CRFa = "CRFa"    # Conselho Regional de Fonoaudiologia
    CRP = "CRP"      # Conselho Regional de Psicologia
    CRBM = "CRBM"    # Conselho Regional de Biomedicina
    CRESS = "CRESS"  # Conselho Regional de Serviço Social


class ValidationStatus(Enum):
    """Status da validação do registro profissional"""
    VALID = "valid"                # Registro válido e ativo
    INVALID_FORMAT = "invalid_format"  # Formato do número inválido
    NOT_FOUND = "not_found"        # Não encontrado no conselho
    SUSPENDED = "suspended"        # Registro suspenso
    CANCELLED = "cancelled"        # Registro cancelado
    EXPIRED = "expired"            # Registro expirado
    PENDING = "pending"            # Validação pendente (API indisponível)
    ERROR = "error"                # Erro na validação


@dataclass
class CRMValidationResult:
    """Resultado da validação de CRM/conselho profissional"""
    status: ValidationStatus
    conselho: str
    numero: str
    uf: str
    # Dados públicos (quando disponíveis via API)
    nome_profissional: Optional[str] = None
    especialidades: Optional[List[str]] = None
    situacao_registro: Optional[str] = None
    data_inscricao: Optional[str] = None
    # Metadados da validação
    validation_id: str = ""
    validated_at: str = ""
    validation_source: str = "local"  # "local" ou "api"
    message: str = ""
    # Hash para auditoria (não expõe dados sensíveis)
    identifier_hash: str = ""

    def __post_init__(self):
        if not self.validation_id:
            self.validation_id = str(uuid.uuid4())
        if not self.validated_at:
            self.validated_at = datetime.now().isoformat()
        if not self.identifier_hash:
            # Hash do identificador para auditoria LGPD
            raw = f"{self.conselho}-{self.numero}-{self.uf}"
            self.identifier_hash = hashlib.sha256(raw.encode()).hexdigest()[:16]

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "status": self.status.value,
            "conselho": self.conselho,
            "numero": self.numero,
            "uf": self.uf,
            "validation_id": self.validation_id,
            "validated_at": self.validated_at,
            "validation_source": self.validation_source,
            "message": self.message,
        }
        # Incluir dados públicos apenas se disponíveis
        if self.nome_profissional:
            result["nome_profissional"] = self.nome_profissional
        if self.especialidades:
            result["especialidades"] = self.especialidades
        if self.situacao_registro:
            result["situacao_registro"] = self.situacao_registro
        return result

    def to_fhir_identifier(self) -> Dict[str, Any]:
        """
        Converte resultado para FHIR Identifier (Practitioner.identifier)
        Seguindo perfil RNDS BR-Core
        """
        system_map = {
            "CRM": "http://www.saude.gov.br/fhir/r4/NamingSystem/cpf-crm",
            "COREN": "http://www.saude.gov.br/fhir/r4/NamingSystem/cpf-coren",
            "CRO": "http://www.saude.gov.br/fhir/r4/NamingSystem/cpf-cro",
            "CRF": "http://www.saude.gov.br/fhir/r4/NamingSystem/cpf-crf",
            "CREFITO": "http://www.saude.gov.br/fhir/r4/NamingSystem/cpf-crefito",
            "CRN": "http://www.saude.gov.br/fhir/r4/NamingSystem/cpf-crn",
            "CRFa": "http://www.saude.gov.br/fhir/r4/NamingSystem/cpf-crfa",
            "CRP": "http://www.saude.gov.br/fhir/r4/NamingSystem/cpf-crp",
            "CRBM": "http://www.saude.gov.br/fhir/r4/NamingSystem/cpf-crbm",
            "CRESS": "http://www.saude.gov.br/fhir/r4/NamingSystem/cpf-cress",
        }

        identifier = {
            "use": "official",
            "type": {
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                    "code": "MD" if self.conselho == "CRM" else "RN" if self.conselho == "COREN" else "LN",
                    "display": f"Registro {self.conselho}"
                }]
            },
            "system": system_map.get(self.conselho, f"http://www.saude.gov.br/fhir/r4/NamingSystem/{self.conselho.lower()}"),
            "value": f"{self.numero}-{self.uf}",
            "period": {
                "start": self.data_inscricao or datetime.now().strftime("%Y-%m-%d")
            }
        }

        # Adicionar extensão com status de validação
        identifier["extension"] = [{
            "url": "http://openehrcore.com.br/fhir/StructureDefinition/validation-status",
            "valueCode": self.status.value
        }, {
            "url": "http://openehrcore.com.br/fhir/StructureDefinition/validation-date",
            "valueDateTime": self.validated_at
        }]

        return identifier


class CRMValidationService:
    """
    Serviço de validação de registros em conselhos profissionais.

    Implementa:
    - Validação de formato local
    - Integração opcional com API do CFM
    - Cache de validações
    - Registro de auditoria LGPD-compliant
    """

    # UFs válidas do Brasil
    UF_VALIDAS = [
        'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA',
        'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN',
        'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'
    ]

    # Padrões de validação de formato por conselho
    FORMATO_PATTERNS = {
        ConselhoTipo.CRM: r'^\d{4,7}$',      # 4-7 dígitos
        ConselhoTipo.COREN: r'^\d{4,9}$',    # 4-9 dígitos
        ConselhoTipo.CRO: r'^\d{4,7}$',      # 4-7 dígitos
        ConselhoTipo.CRF: r'^\d{4,6}$',      # 4-6 dígitos
        ConselhoTipo.CREFITO: r'^\d{4,7}$',  # 4-7 dígitos
        ConselhoTipo.CRN: r'^\d{4,6}$',      # 4-6 dígitos
        ConselhoTipo.CRFa: r'^\d{4,6}$',     # 4-6 dígitos
        ConselhoTipo.CRP: r'^\d{2}/\d{4,6}$|^\d{4,6}$',  # Região/número ou só número
        ConselhoTipo.CRBM: r'^\d{4,6}$',     # 4-6 dígitos
        ConselhoTipo.CRESS: r'^\d{4,6}$',    # 4-6 dígitos
    }

    # Cache TTL em segundos (24 horas por padrão)
    CACHE_TTL = 86400

    # Configuração da API CFM (se disponível)
    CFM_API_URL = getattr(settings, 'CFM_API_URL', None)
    CFM_API_KEY = getattr(settings, 'CFM_API_KEY', None)

    @classmethod
    def validate(
        cls,
        conselho: str,
        numero: str,
        uf: str,
        use_api: bool = True,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> CRMValidationResult:
        """
        Valida um registro de conselho profissional.

        Args:
            conselho: Tipo do conselho (CRM, COREN, etc.)
            numero: Número do registro
            uf: UF do conselho
            use_api: Se True, tenta validar via API (se disponível)
            user_id: ID do usuário solicitante (para auditoria)
            ip_address: IP do solicitante (para auditoria)

        Returns:
            CRMValidationResult com o resultado da validação
        """
        # Normalizar entrada
        conselho = conselho.upper().strip()
        numero = re.sub(r'\D', '', numero)  # Remove não-dígitos
        uf = uf.upper().strip()

        # Log de início da validação (auditoria)
        logger.info(f"Iniciando validação de registro: {conselho}/{uf} (hash: {hashlib.sha256(numero.encode()).hexdigest()[:8]})")

        # 1. Validação de formato local
        format_result = cls._validate_format(conselho, numero, uf)
        if format_result.status != ValidationStatus.VALID:
            cls._log_validation_audit(format_result, user_id, ip_address)
            return format_result

        # 2. Verificar cache
        cache_key = f"crm_validation:{conselho}:{numero}:{uf}"
        cached = cache.get(cache_key)
        if cached:
            logger.info(f"Retornando validação do cache: {cache_key}")
            cached['validation_source'] = 'cache'
            return CRMValidationResult(**cached)

        # 3. Validação via API (se habilitada e disponível)
        if use_api and cls.CFM_API_URL and conselho == "CRM":
            api_result = cls._validate_via_cfm_api(numero, uf)
            if api_result:
                cls._log_validation_audit(api_result, user_id, ip_address)
                # Cachear resultado
                cache.set(cache_key, asdict(api_result), cls.CACHE_TTL)
                return api_result

        # 4. Se API não disponível, retornar validação de formato como sucesso
        result = CRMValidationResult(
            status=ValidationStatus.VALID,
            conselho=conselho,
            numero=numero,
            uf=uf,
            validation_source="local",
            message="Formato válido. Validação de registro pendente (API não disponível)."
        )

        # Cachear resultado local
        cache.set(cache_key, asdict(result), cls.CACHE_TTL // 2)  # Metade do TTL para local

        cls._log_validation_audit(result, user_id, ip_address)
        return result

    @classmethod
    def _validate_format(cls, conselho: str, numero: str, uf: str) -> CRMValidationResult:
        """Valida apenas o formato do registro (validação local)"""

        # Validar UF
        if uf not in cls.UF_VALIDAS:
            return CRMValidationResult(
                status=ValidationStatus.INVALID_FORMAT,
                conselho=conselho,
                numero=numero,
                uf=uf,
                validation_source="local",
                message=f"UF inválida: {uf}. UFs válidas: {', '.join(cls.UF_VALIDAS)}"
            )

        # Validar tipo de conselho
        try:
            conselho_tipo = ConselhoTipo[conselho]
        except KeyError:
            return CRMValidationResult(
                status=ValidationStatus.INVALID_FORMAT,
                conselho=conselho,
                numero=numero,
                uf=uf,
                validation_source="local",
                message=f"Tipo de conselho inválido: {conselho}. Tipos válidos: {', '.join([c.value for c in ConselhoTipo])}"
            )

        # Validar formato do número
        pattern = cls.FORMATO_PATTERNS.get(conselho_tipo)
        if pattern and not re.match(pattern, numero):
            return CRMValidationResult(
                status=ValidationStatus.INVALID_FORMAT,
                conselho=conselho,
                numero=numero,
                uf=uf,
                validation_source="local",
                message=f"Formato de número inválido para {conselho}. Esperado: apenas dígitos (4-7 dígitos para CRM)"
            )

        # Validar número mínimo
        if len(numero) < 4:
            return CRMValidationResult(
                status=ValidationStatus.INVALID_FORMAT,
                conselho=conselho,
                numero=numero,
                uf=uf,
                validation_source="local",
                message="Número do registro deve ter pelo menos 4 dígitos"
            )

        return CRMValidationResult(
            status=ValidationStatus.VALID,
            conselho=conselho,
            numero=numero,
            uf=uf,
            validation_source="local",
            message="Formato válido"
        )

    @classmethod
    def _validate_via_cfm_api(cls, numero: str, uf: str) -> Optional[CRMValidationResult]:
        """
        Valida CRM via API oficial do CFM.

        Nota: Requer registro prévio no CFM e chave de API.
        API: https://siem-servicos-api.cfm.org.br

        A API retorna apenas dados públicos:
        - Nome do médico
        - Situação do registro
        - Especialidades
        - Data de inscrição

        NÃO retorna dados pessoais (CPF, endereço, telefone, email) - LGPD compliant.
        """
        if not cls.CFM_API_URL or not cls.CFM_API_KEY:
            logger.debug("API CFM não configurada")
            return None

        try:
            headers = {
                'Authorization': f'Bearer {cls.CFM_API_KEY}',
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }

            # Endpoint de consulta CFM
            url = f"{cls.CFM_API_URL}/medicos/buscar"
            params = {
                'crm': numero,
                'uf': uf
            }

            response = requests.get(
                url,
                headers=headers,
                params=params,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()

                if not data or not data.get('encontrado'):
                    return CRMValidationResult(
                        status=ValidationStatus.NOT_FOUND,
                        conselho="CRM",
                        numero=numero,
                        uf=uf,
                        validation_source="api",
                        message="Registro não encontrado no CFM"
                    )

                # Mapear situação para status
                situacao = data.get('situacao', '').upper()
                status = ValidationStatus.VALID
                if 'CANCELADO' in situacao:
                    status = ValidationStatus.CANCELLED
                elif 'SUSPENSO' in situacao:
                    status = ValidationStatus.SUSPENDED
                elif 'INATIVO' in situacao or 'EXPIRADO' in situacao:
                    status = ValidationStatus.EXPIRED

                return CRMValidationResult(
                    status=status,
                    conselho="CRM",
                    numero=numero,
                    uf=uf,
                    nome_profissional=data.get('nome'),
                    especialidades=data.get('especialidades', []),
                    situacao_registro=data.get('situacao'),
                    data_inscricao=data.get('dataInscricao'),
                    validation_source="api",
                    message=f"Validado via CFM. Situação: {situacao}"
                )

            elif response.status_code == 404:
                return CRMValidationResult(
                    status=ValidationStatus.NOT_FOUND,
                    conselho="CRM",
                    numero=numero,
                    uf=uf,
                    validation_source="api",
                    message="Registro não encontrado no CFM"
                )

            else:
                logger.warning(f"Erro na API CFM: {response.status_code}")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Erro de conexão com API CFM: {e}")
            return None
        except Exception as e:
            logger.error(f"Erro inesperado na validação CFM: {e}")
            return None

    @classmethod
    def _log_validation_audit(
        cls,
        result: CRMValidationResult,
        user_id: Optional[str],
        ip_address: Optional[str]
    ):
        """
        Registra evento de auditoria para a validação (LGPD Art. 6, VII).

        Não armazena o número do registro, apenas o hash para rastreabilidade.
        """
        from .lgpd_service import LGPDService

        # Log para fins de auditoria (sem dados sensíveis)
        audit_data = {
            "action": "crm_validation",
            "validation_id": result.validation_id,
            "conselho": result.conselho,
            "uf": result.uf,
            "identifier_hash": result.identifier_hash,
            "status": result.status.value,
            "source": result.validation_source,
            "user_id": user_id or "anonymous",
            "ip_address": ip_address or "unknown",
            "timestamp": result.validated_at
        }

        logger.info(f"CRM Validation Audit: {audit_data}")

        # Se o serviço LGPD estiver disponível, registrar acesso
        try:
            LGPDService.log_data_access(
                patient_id="system",  # Validação não é específica de paciente
                resource_type="Practitioner",
                resource_id=f"validation:{result.validation_id}",
                action="validate",
                user=user_id,
                ip_address=ip_address,
                reason=f"Validação de {result.conselho}/{result.uf}"
            )
        except Exception as e:
            logger.warning(f"Não foi possível registrar auditoria LGPD: {e}")

    @classmethod
    def batch_validate(
        cls,
        registros: List[Dict[str, str]],
        use_api: bool = True,
        user_id: Optional[str] = None
    ) -> List[CRMValidationResult]:
        """
        Valida múltiplos registros em lote.

        Args:
            registros: Lista de dicts com {conselho, numero, uf}
            use_api: Se True, tenta validar via API
            user_id: ID do usuário para auditoria

        Returns:
            Lista de CRMValidationResult
        """
        results = []
        for reg in registros:
            result = cls.validate(
                conselho=reg.get('conselho', ''),
                numero=reg.get('numero', ''),
                uf=reg.get('uf', ''),
                use_api=use_api,
                user_id=user_id
            )
            results.append(result)
        return results

    @classmethod
    def invalidate_cache(cls, conselho: str, numero: str, uf: str):
        """Remove uma entrada específica do cache de validação"""
        cache_key = f"crm_validation:{conselho}:{numero}:{uf}"
        cache.delete(cache_key)
        logger.info(f"Cache invalidado: {cache_key}")

    @classmethod
    def get_validation_stats(cls) -> Dict[str, Any]:
        """
        Retorna estatísticas de validação (para dashboard admin).

        Nota: Não expõe dados individuais, apenas métricas agregadas.
        """
        # Em produção, buscar do banco de dados de auditoria
        return {
            "total_validations": 0,
            "valid_count": 0,
            "invalid_format_count": 0,
            "not_found_count": 0,
            "api_validated_count": 0,
            "local_validated_count": 0,
            "last_24h_count": 0,
            "cache_hit_rate": 0.0
        }
