"""
RNDS Service - Rede Nacional de Dados em Saúde
Integração com a plataforma nacional de saúde do Ministério da Saúde (Brasil)

Recursos suportados:
- Sumário de Paciente (IPS - International Patient Summary)
- Resultados de Exames Laboratoriais
- Registro de Imunização
- Notificações (COVID-19, etc.)
"""

import logging
import requests
import jwt
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from dataclasses import dataclass
from enum import Enum
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class RNDSAmbiente(Enum):
    """Ambientes RNDS disponíveis"""
    HOMOLOGACAO = 'homologacao'
    PRODUCAO = 'producao'


class TipoDocumentoRNDS(Enum):
    """Tipos de documentos que podem ser enviados à RNDS"""
    SUMARIO_PACIENTE = 'sumario-paciente'
    RESULTADO_EXAME = 'resultado-exame'
    IMUNIZACAO = 'imunizacao'
    NOTIFICACAO_COVID = 'notificacao-covid'
    PRESCRICAO = 'prescricao'


@dataclass
class ConfiguracaoRNDS:
    """Configurações de conexão com a RNDS"""
    ambiente: RNDSAmbiente
    client_id: str  # Identificador do certificado digital
    client_secret: str  # Chave do certificado
    cnes: str  # CNES do estabelecimento
    uf: str  # UF do estabelecimento
    certificado_path: Optional[str] = None  # Caminho do certificado .pfx
    certificado_senha: Optional[str] = None


class RNDSService:
    """
    Serviço de integração com a RNDS (Rede Nacional de Dados em Saúde).
    
    A RNDS é a plataforma nacional de interoperabilidade em saúde do Brasil,
    baseada em FHIR R4 e gerenciada pelo DATASUS/Ministério da Saúde.
    """
    
    # URLs base da RNDS
    URLS = {
        RNDSAmbiente.HOMOLOGACAO: {
            'auth': 'https://ehr-auth-hmg.saude.gov.br/api/token',
            'fhir': 'https://ehr-services-hmg.saude.gov.br/api/fhir/r4'
        },
        RNDSAmbiente.PRODUCAO: {
            'auth': 'https://ehr-auth.saude.gov.br/api/token',
            'fhir': 'https://ehr-services.saude.gov.br/api/fhir/r4'
        }
    }
    
    def __init__(self, config: ConfiguracaoRNDS):
        self.config = config
        self.access_token = None
        self.token_expiry = None
        
        # Definir URLs baseado no ambiente
        self.auth_url = self.URLS[config.ambiente]['auth']
        self.fhir_url = self.URLS[config.ambiente]['fhir']
    
    def _obter_token(self) -> str:
        """
        Obtém token de acesso OAuth2 da RNDS usando certificado digital ICP-Brasil.
        
        O token é cacheado até expirar.
        """
        cache_key = f"rnds_token_{self.config.cnes}"
        cached_token = cache.get(cache_key)
        
        if cached_token:
            return cached_token
        
        try:
            # Autenticação via certificado digital
            # Em produção, usar biblioteca cryptography para carregar certificado
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            data = {
                'grant_type': 'client_credentials',
                'client_id': self.config.client_id,
                'client_secret': self.config.client_secret
            }
            
            # Se certificado disponível, usar autenticação mTLS
            cert = None
            if self.config.certificado_path:
                cert = (self.config.certificado_path, self.config.certificado_senha)
            
            response = requests.post(
                self.auth_url,
                headers=headers,
                data=data,
                cert=cert,
                timeout=30
            )
            
            if response.status_code == 200:
                token_data = response.json()
                access_token = token_data.get('access_token')
                expires_in = token_data.get('expires_in', 3600)
                
                # Cachear token (com margem de 60 segundos)
                cache.set(cache_key, access_token, expires_in - 60)
                
                self.access_token = access_token
                self.token_expiry = datetime.now() + timedelta(seconds=expires_in)
                
                logger.info(f"Token RNDS obtido com sucesso, expira em {expires_in}s")
                return access_token
            else:
                logger.error(f"Erro ao obter token RNDS: {response.status_code} - {response.text}")
                raise Exception(f"Falha na autenticação RNDS: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro de conexão com RNDS: {str(e)}")
            raise
    
    def _fazer_requisicao(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict:
        """Executa requisição autenticada para a RNDS"""
        token = self._obter_token()
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/fhir+json',
            'Accept': 'application/fhir+json',
            'X-Authorization-Server': f'oauth2-{self.config.ambiente.value}'
        }
        
        url = f"{self.fhir_url}/{endpoint}"
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=data,
                params=params,
                timeout=60
            )
            
            if response.status_code in (200, 201):
                return response.json()
            elif response.status_code == 401:
                # Token expirado, limpar cache e tentar novamente
                cache.delete(f"rnds_token_{self.config.cnes}")
                return self._fazer_requisicao(method, endpoint, data, params)
            else:
                logger.error(f"Erro RNDS: {response.status_code} - {response.text}")
                raise Exception(f"Erro RNDS: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro de conexão RNDS: {str(e)}")
            raise
    
    def consultar_paciente(self, cpf: str) -> Dict:
        """
        Consulta dados do paciente na RNDS pelo CPF.
        
        Args:
            cpf: CPF do paciente (apenas números)
        
        Returns:
            Bundle FHIR com dados do paciente
        """
        endpoint = f"Patient?identifier=http://rnds.saude.gov.br/fhir/r4/NamingSystem/cpf|{cpf}"
        return self._fazer_requisicao('GET', endpoint)
    
    def consultar_cns(self, cns: str) -> Dict:
        """
        Consulta dados do paciente pelo CNS (Cartão Nacional de Saúde).
        
        Args:
            cns: Número do CNS
        
        Returns:
            Recurso Patient FHIR
        """
        endpoint = f"Patient?identifier=http://rnds.saude.gov.br/fhir/r4/NamingSystem/cns|{cns}"
        return self._fazer_requisicao('GET', endpoint)
    
    def enviar_sumario_paciente(
        self,
        patient_cpf: str,
        conditions: List[Dict],
        allergies: List[Dict],
        medications: List[Dict],
        immunizations: List[Dict],
        practitioner_cns: str,
        encounter_id: Optional[str] = None
    ) -> Dict:
        """
        Envia Sumário de Paciente (IPS) para a RNDS.
        
        O IPS é um resumo estruturado dos dados clínicos essenciais do paciente,
        seguindo o padrão International Patient Summary.
        
        Args:
            patient_cpf: CPF do paciente
            conditions: Lista de condições/diagnósticos
            allergies: Lista de alergias
            medications: Lista de medicamentos em uso
            immunizations: Lista de vacinas
            practitioner_cns: CNS do profissional responsável
            encounter_id: ID do atendimento (opcional)
        
        Returns:
            Resposta da RNDS com ID do documento
        """
        # Construir Composition IPS
        composition = {
            'resourceType': 'Composition',
            'meta': {
                'profile': ['http://www.saude.gov.br/fhir/r4/StructureDefinition/BRSumarioAlta']
            },
            'status': 'final',
            'type': {
                'coding': [{
                    'system': 'http://loinc.org',
                    'code': '60591-5',
                    'display': 'Patient summary Document'
                }]
            },
            'subject': {
                'identifier': {
                    'system': 'http://rnds.saude.gov.br/fhir/r4/NamingSystem/cpf',
                    'value': patient_cpf
                }
            },
            'date': datetime.now().strftime('%Y-%m-%dT%H:%M:%S-03:00'),
            'author': [{
                'identifier': {
                    'system': 'http://rnds.saude.gov.br/fhir/r4/NamingSystem/cns',
                    'value': practitioner_cns
                }
            }],
            'title': 'Sumário de Paciente',
            'section': []
        }
        
        # Seção de problemas/condições
        if conditions:
            composition['section'].append({
                'title': 'Problemas',
                'code': {
                    'coding': [{
                        'system': 'http://loinc.org',
                        'code': '11450-4',
                        'display': 'Problem list'
                    }]
                },
                'entry': [{'reference': f"Condition/{c.get('id')}"} for c in conditions]
            })
        
        # Seção de alergias
        if allergies:
            composition['section'].append({
                'title': 'Alergias',
                'code': {
                    'coding': [{
                        'system': 'http://loinc.org',
                        'code': '48765-2',
                        'display': 'Allergies and adverse reactions'
                    }]
                },
                'entry': [{'reference': f"AllergyIntolerance/{a.get('id')}"} for a in allergies]
            })
        
        # Seção de medicamentos
        if medications:
            composition['section'].append({
                'title': 'Medicamentos',
                'code': {
                    'coding': [{
                        'system': 'http://loinc.org',
                        'code': '10160-0',
                        'display': 'Medication use'
                    }]
                },
                'entry': [{'reference': f"MedicationStatement/{m.get('id')}"} for m in medications]
            })
        
        # Seção de imunizações
        if immunizations:
            composition['section'].append({
                'title': 'Imunizações',
                'code': {
                    'coding': [{
                        'system': 'http://loinc.org',
                        'code': '11369-6',
                        'display': 'Immunizations'
                    }]
                },
                'entry': [{'reference': f"Immunization/{i.get('id')}"} for i in immunizations]
            })
        
        # Construir Bundle
        bundle = {
            'resourceType': 'Bundle',
            'type': 'document',
            'timestamp': datetime.now().strftime('%Y-%m-%dT%H:%M:%S-03:00'),
            'entry': [
                {'fullUrl': 'urn:uuid:composition', 'resource': composition}
            ]
        }
        
        # Adicionar recursos referenciados
        for condition in conditions:
            bundle['entry'].append({
                'fullUrl': f"urn:uuid:condition-{condition.get('id')}",
                'resource': self._converter_para_rnds(condition, 'Condition')
            })
        
        logger.info(f"Enviando Sumário de Paciente para RNDS - CPF: {patient_cpf[:3]}***")
        
        return self._fazer_requisicao('POST', 'Bundle', bundle)
    
    def enviar_resultado_exame(
        self,
        patient_cpf: str,
        exam_type: str,
        result_value: str,
        result_unit: str,
        exam_date: str,
        practitioner_cns: str,
        loinc_code: str,
        interpretation: Optional[str] = None
    ) -> Dict:
        """
        Envia resultado de exame laboratorial para a RNDS.
        
        Args:
            patient_cpf: CPF do paciente
            exam_type: Tipo do exame
            result_value: Valor do resultado
            result_unit: Unidade de medida
            exam_date: Data do exame
            practitioner_cns: CNS do profissional
            loinc_code: Código LOINC do exame
            interpretation: Interpretação (N=Normal, A=Abnormal, etc)
        
        Returns:
            Resposta da RNDS
        """
        observation = {
            'resourceType': 'Observation',
            'meta': {
                'profile': ['http://www.saude.gov.br/fhir/r4/StructureDefinition/BRDiagnosticoLaboratorioClinico']
            },
            'status': 'final',
            'category': [{
                'coding': [{
                    'system': 'http://terminology.hl7.org/CodeSystem/observation-category',
                    'code': 'laboratory'
                }]
            }],
            'code': {
                'coding': [{
                    'system': 'http://loinc.org',
                    'code': loinc_code,
                    'display': exam_type
                }]
            },
            'subject': {
                'identifier': {
                    'system': 'http://rnds.saude.gov.br/fhir/r4/NamingSystem/cpf',
                    'value': patient_cpf
                }
            },
            'effectiveDateTime': exam_date,
            'issued': datetime.now().strftime('%Y-%m-%dT%H:%M:%S-03:00'),
            'performer': [{
                'identifier': {
                    'system': 'http://rnds.saude.gov.br/fhir/r4/NamingSystem/cnes',
                    'value': self.config.cnes
                }
            }],
            'valueQuantity': {
                'value': float(result_value) if result_value.replace('.', '').isdigit() else None,
                'unit': result_unit,
                'system': 'http://unitsofmeasure.org'
            }
        }
        
        if interpretation:
            observation['interpretation'] = [{
                'coding': [{
                    'system': 'http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation',
                    'code': interpretation
                }]
            }]
        
        logger.info(f"Enviando resultado de exame para RNDS - Tipo: {exam_type}")
        
        return self._fazer_requisicao('POST', 'Observation', observation)
    
    def enviar_imunizacao(
        self,
        patient_cpf: str,
        vaccine_code: str,
        vaccine_name: str,
        dose_number: int,
        vaccination_date: str,
        lot_number: str,
        practitioner_cns: str,
        manufacturer: Optional[str] = None
    ) -> Dict:
        """
        Registra imunização na RNDS.
        
        Args:
            patient_cpf: CPF do paciente
            vaccine_code: Código da vacina (CVX ou SBIM)
            vaccine_name: Nome da vacina
            dose_number: Número da dose
            vaccination_date: Data da vacinação
            lot_number: Número do lote
            practitioner_cns: CNS do vacinador
            manufacturer: Fabricante
        
        Returns:
            Resposta da RNDS
        """
        immunization = {
            'resourceType': 'Immunization',
            'meta': {
                'profile': ['http://www.saude.gov.br/fhir/r4/StructureDefinition/BRImunobiologicoAdministrado']
            },
            'status': 'completed',
            'vaccineCode': {
                'coding': [{
                    'system': 'http://www.saude.gov.br/fhir/r4/CodeSystem/BRImunobiologico',
                    'code': vaccine_code,
                    'display': vaccine_name
                }]
            },
            'patient': {
                'identifier': {
                    'system': 'http://rnds.saude.gov.br/fhir/r4/NamingSystem/cpf',
                    'value': patient_cpf
                }
            },
            'occurrenceDateTime': vaccination_date,
            'lotNumber': lot_number,
            'performer': [{
                'actor': {
                    'identifier': {
                        'system': 'http://rnds.saude.gov.br/fhir/r4/NamingSystem/cns',
                        'value': practitioner_cns
                    }
                }
            }],
            'protocolApplied': [{
                'doseNumberPositiveInt': dose_number
            }]
        }
        
        if manufacturer:
            immunization['manufacturer'] = {'display': manufacturer}
        
        logger.info(f"Enviando imunização para RNDS - Vacina: {vaccine_name}, Dose: {dose_number}")
        
        return self._fazer_requisicao('POST', 'Immunization', immunization)
    
    def consultar_historico_vacinal(self, cpf: str) -> Dict:
        """
        Consulta histórico de vacinação do paciente na RNDS.
        
        Args:
            cpf: CPF do paciente
        
        Returns:
            Bundle com imunizações registradas
        """
        endpoint = f"Immunization?patient.identifier=http://rnds.saude.gov.br/fhir/r4/NamingSystem/cpf|{cpf}"
        return self._fazer_requisicao('GET', endpoint)
    
    def verificar_status_conexao(self) -> Dict:
        """
        Verifica status da conexão com a RNDS.
        
        Returns:
            Dict com status da conexão
        """
        try:
            token = self._obter_token()
            return {
                'status': 'conectado',
                'ambiente': self.config.ambiente.value,
                'cnes': self.config.cnes,
                'token_valido': bool(token),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'status': 'erro',
                'ambiente': self.config.ambiente.value,
                'cnes': self.config.cnes,
                'erro': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _converter_para_rnds(self, resource: Dict, resource_type: str) -> Dict:
        """
        Converte recurso FHIR local para formato RNDS.
        Adiciona profiles e identificadores necessários.
        """
        # Adicionar profile RNDS
        profiles = {
            'Condition': 'http://www.saude.gov.br/fhir/r4/StructureDefinition/BRProblemaDiagnostico',
            'Observation': 'http://www.saude.gov.br/fhir/r4/StructureDefinition/BRObservacaoDescritiva',
            'MedicationRequest': 'http://www.saude.gov.br/fhir/r4/StructureDefinition/BRPrescricaoMedicamento',
            'AllergyIntolerance': 'http://hl7.org/fhir/StructureDefinition/AllergyIntolerance'
        }
        
        if 'meta' not in resource:
            resource['meta'] = {}
        
        resource['meta']['profile'] = [profiles.get(resource_type, '')]
        
        return resource
