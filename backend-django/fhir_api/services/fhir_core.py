"""
FHIR Core Service - Manipulação segura de recursos FHIR.

Este serviço atua como o guardião da comunicação com o HAPI FHIR Server.
Ele utiliza a biblioteca fhirclient para garantir que todos os recursos
sejam criados e manipulados de acordo com a especificação FHIR R4.

Princípio: O HAPI FHIR é a autoridade absoluta dos dados clínicos.
"""

import requests
import logging
import threading
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from django.conf import settings

from fhirclient.models.patient import Patient
from fhirclient.models.humanname import HumanName
from fhirclient.models.identifier import Identifier
from fhirclient.models.contactpoint import ContactPoint
from fhirclient.models.codeableconcept import CodeableConcept
from fhirclient.models.coding import Coding
from fhirclient.models.encounter import Encounter
from fhirclient.models.period import Period
from fhirclient.models.observation import Observation
from fhirclient.models.quantity import Quantity
from fhirclient.models.fhirdate import FHIRDate
from fhirclient.models.fhirdatetime import FHIRDateTime
from fhirclient.models.fhirinstant import FHIRInstant
from fhirclient.models.fhirreference import FHIRReference
from fhirclient.models.condition import Condition
from fhirclient.models.allergyintolerance import AllergyIntolerance
from fhirclient.models.appointment import Appointment
from fhirclient.models.coverage import Coverage
from fhirclient.models.invoice import Invoice
from fhirclient.models.account import Account
from fhirclient.models.account import Account
from fhirclient.models.money import Money
from fhirclient.models.provenance import Provenance
from fhirclient.models.provenance import ProvenanceAgent



logger = logging.getLogger(__name__)


class FHIRServiceException(Exception):
    """Exceção customizada para erros de integração FHIR."""
    pass


class CircuitBreakerOpen(FHIRServiceException):
    """Exceção lançada quando circuit breaker está aberto."""
    pass


class FHIRService:
    """
    Serviço centralizado para comunicação com HAPI FHIR Server.
    
    Garante:
    - Tipagem FHIR correta (usa objetos da lib fhirclient)
    - Validação de dados antes de enviar
    - Tratamento de erros padronizado
    - Logging de todas as operações
    - Cache para buscas frequentes (TTL 5 minutos)
    - Circuit Breaker para resiliência
    """
    
    # Cache class-level para buscas (shared entre instâncias)
    _cache: Dict[str, tuple] = {}
    _cache_ttl_seconds = 300  # 5 minutos
    
    # Circuit Breaker state (shared entre instâncias)
    _circuit_open = False
    _circuit_open_until: Optional[datetime] = None
    _failure_count = 0
    _lock = threading.Lock()
    
    # Circuit Breaker configuração
    FAILURE_THRESHOLD = getattr(settings, 'FHIR_CIRCUIT_BREAKER_THRESHOLD', 5)
    CIRCUIT_OPEN_DURATION = getattr(settings, 'FHIR_CIRCUIT_BREAKER_DURATION', 60)

    def __init__(self, user: Optional[Any] = None):
        self.base_url = settings.FHIR_SERVER_URL
        self.timeout = settings.FHIR_SERVER_TIMEOUT
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/fhir+json',
            'Accept': 'application/fhir+json',
        })
        self.user = user # Contexto do usuário para auditoria (Provenance)
    
    @classmethod
    def _check_circuit(cls):
        """
        Verifica se circuit breaker está aberto.
        
        Raises:
            CircuitBreakerOpen: Se circuito está aberto
        """
        with cls._lock:
            if cls._circuit_open:
                if datetime.now() > cls._circuit_open_until:
                    logger.info("Circuit breaker: Attempting to close (half-open state)")
                    cls._circuit_open = False
                    cls._failure_count = 0
                else:
                    seconds_remaining = int((cls._circuit_open_until - datetime.now()).total_seconds())
                    raise CircuitBreakerOpen(
                        f"FHIR Server circuit breaker OPEN. "
                        f"Retry after {seconds_remaining}s"
                    )
    
    @classmethod
    def _record_success(cls):
        """Registra sucesso na chamada FHIR."""
        with cls._lock:
            if cls._failure_count > 0:
                logger.info(f"FHIR call succeeded - resetting failure count from {cls._failure_count} to 0")
            cls._failure_count = 0
    
    @classmethod
    def _record_failure(cls):
        """Registra falha e abre circuito se necessário."""
        with cls._lock:
            cls._failure_count += 1
            logger.warning(f"FHIR call failed - failure count: {cls._failure_count}/{cls.FAILURE_THRESHOLD}")
            
            if cls._failure_count >= cls.FAILURE_THRESHOLD:
                cls._circuit_open = True
                cls._circuit_open_until = datetime.now() + timedelta(seconds=cls.CIRCUIT_OPEN_DURATION)
                logger.error(
                    f"Circuit breaker OPENED after {cls._failure_count} failures. "
                    f"Will retry at {cls._circuit_open_until.strftime('%H:%M:%S')}"
                )
    
    @classmethod
    def get_circuit_state(cls) -> Dict[str, Any]:
        """
        Retorna estado atual do circuit breaker.
        
        Returns:
            Dict com estado do circuito
        """
        with cls._lock:
            return {
                "open": cls._circuit_open,
                "failure_count": cls._failure_count,
                "threshold": cls.FAILURE_THRESHOLD,
                "retry_at": cls._circuit_open_until.isoformat() if cls._circuit_open_until else None,
                "seconds_until_retry": int((cls._circuit_open_until - datetime.now()).total_seconds()) 
                    if cls._circuit_open and cls._circuit_open_until else 0
            }
    
    @classmethod
    def reset_circuit(cls):
        """Reset manual do circuit breaker (para testes/admin)."""
        with cls._lock:
            cls._circuit_open = False
            cls._circuit_open_until = None
            cls._failure_count = 0
            logger.info("Circuit breaker manually reset")

    @classmethod
    def _get_cache_key(cls, resource_type: str, params: Dict[str, Any]) -> str:
        """Gera chave única para cache baseada no tipo e parâmetros."""
        sorted_params = sorted((params or {}).items())
        return f"{resource_type}:{str(sorted_params)}"
    
    @classmethod
    def _is_cache_valid(cls, cache_key: str) -> bool:
        """Verifica se o cache ainda é válido (não expirou)."""
        if cache_key not in cls._cache:
            return False
        cached_time, _ = cls._cache[cache_key]
        return (datetime.now() - cached_time).total_seconds() < cls._cache_ttl_seconds
    
    @classmethod
    def _get_from_cache(cls, cache_key: str) -> Optional[List[Dict[str, Any]]]:
        """Retorna dados do cache se válido."""
        if cls._is_cache_valid(cache_key):
            _, data = cls._cache[cache_key]
            logger.debug(f"Cache HIT: {cache_key}")
            return data
        return None
    
    @classmethod
    def _set_cache(cls, cache_key: str, data: List[Dict[str, Any]]) -> None:
        """Armazena dados no cache."""
        cls._cache[cache_key] = (datetime.now(), data)
        logger.debug(f"Cache SET: {cache_key}")
    
    @classmethod
    def clear_cache(cls, resource_type: Optional[str] = None) -> int:
        """
        Limpa o cache. Se resource_type for especificado, limpa apenas desse tipo.
        
        Returns:
            int: Número de entradas removidas
        """
        if resource_type:
            keys_to_remove = [k for k in cls._cache if k.startswith(f"{resource_type}:")]
            for key in keys_to_remove:
                del cls._cache[key]
            logger.info(f"Cache cleared for {resource_type}: {len(keys_to_remove)} entries removed")
            return len(keys_to_remove)
        else:
            count = len(cls._cache)
            cls._cache.clear()
            logger.info(f"Cache fully cleared: {count} entries removed")
            return count

    def health_check(self) -> bool:
        """
        Verifica se o servidor FHIR está respondendo.
        
        Returns:
            bool: True se o servidor está saudável
            
        Raises:
            CircuitBreakerOpen: Se circuit breaker está aberto
            FHIRServiceException: Se o servidor não responde
        """
        # Verificar circuit breaker antes de tentar
        self._check_circuit()
        
        try:
            response = self.session.get(
                f"{self.base_url}/metadata",
                timeout=self.timeout
            )
            response.raise_for_status()
            
            # Sucesso - resetar contadores
            self._record_success()
            logger.info("FHIR Server health check: OK")
            return True
            
        except requests.exceptions.Timeout as e:
            self._record_failure()
            logger.error(f"FHIR Server health check timeout: {str(e)}")
            raise FHIRServiceException(f"FHIR Server timeout: {str(e)}")
            
        except requests.exceptions.ConnectionError as e:
            self._record_failure()
            logger.error(f"FHIR Server connection error: {str(e)}")
            raise FHIRServiceException(f"FHIR Server unreachable: {str(e)}")
            
        except requests.RequestException as e:
            self._record_failure()
            logger.error(f"FHIR Server health check failed: {str(e)}")
            raise FHIRServiceException(f"FHIR Server error: {str(e)}")

    def create_resource(self, resource_type: str, resource_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Cria qualquer recurso FHIR genericamente.
        
        Args:
            resource_type: Tipo do recurso (Ex: 'RelatedPerson')
            resource_data: Dict com os dados do recurso
            
        Returns:
            Dict com o recurso criado (incluindo ID)
            
        Raises:
            CircuitBreakerOpen: Se circuit breaker está aberto
            FHIRServiceException: Se criação falhar
        """
        # Verificar circuit breaker antes de tentar
        self._check_circuit()
        
        try:
            logger.info(f"Creating generic {resource_type}")
            response = self.session.post(
                f"{self.base_url}/{resource_type}",
                json=resource_data,
                timeout=self.timeout
            )
            
            if response.status_code not in [200, 201]:
                self._record_failure()
                logger.error(f"Failed to create {resource_type}: {response.text}")
                raise FHIRServiceException(f"Failed to create {resource_type}: {response.status_code}")
            
            # Sucesso - resetar contadores
            self._record_success()
            
            result = response.json()
            logger.info(f"{resource_type} created successfully: ID={result.get('id')}")
            return result
        
        except requests.exceptions.Timeout as e:
            self._record_failure()
            logger.error(f"Timeout creating {resource_type}: {str(e)}")
            raise FHIRServiceException(f"Timeout creating {resource_type}: {str(e)}")
            
        except requests.exceptions.ConnectionError as e:
            self._record_failure()
            logger.error(f"Connection error creating {resource_type}: {str(e)}")
            raise FHIRServiceException(f"Connection failed: {str(e)}")
            
        except FHIRServiceException:
            # Já logou e registrou falha
            raise
            
        except Exception as e:
            self._record_failure()
            logger.error(f"Error creating {resource_type}: {str(e)}", exc_info=True)
            raise FHIRServiceException(f"Error creating {resource_type}: {str(e)}")

    def update_resource(self, resource_type: str, resource_id: str, resource_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Atualiza qualquer recurso FHIR genericamente.
        
        Args:
            resource_type: Tipo do recurso (Ex: 'Patient')
            resource_id: ID do recurso a atualizar
            resource_data: Dict com os dados do recurso
            
        Returns:
            Dict com o recurso atualizado
        """
        try:
            # Garantir que o ID está no payload
            resource_data['id'] = resource_id
            
            logger.info(f"Updating {resource_type}/{resource_id}")
            response = self.session.put(
                f"{self.base_url}/{resource_type}/{resource_id}",
                json=resource_data,
                timeout=self.timeout
            )
            
            if response.status_code not in [200, 201]:
                logger.error(f"Failed to update {resource_type}/{resource_id}: {response.text}")
                raise FHIRServiceException(f"Failed to update {resource_type}: {response.status_code}")
                
            result = response.json()
            logger.info(f"{resource_type}/{resource_id} updated successfully")
            return result
            
        except Exception as e:
            logger.error(f"Error updating {resource_type}/{resource_id}: {str(e)}")
            raise FHIRServiceException(f"Error updating {resource_type}: {str(e)}")

    def search_resources(self, resource_type: str, params: Dict[str, Any] = None, use_cache: bool = True) -> List[Dict[str, Any]]:
        """
        Busca genérica de recursos FHIR com suporte a cache.
        
        Args:
            resource_type: Tipo do recurso (Ex: 'RelatedPerson')
            params: Dicionário de parâmetros de busca
            use_cache: Se True, usa cache (padrão). Se False, força busca no servidor.
            
        Returns:
            Lista de recursos encontrados
        """
        # Verificar cache primeiro
        if use_cache:
            cache_key = self._get_cache_key(resource_type, params)
            cached_data = self._get_from_cache(cache_key)
            if cached_data is not None:
                return cached_data
        
        try:
            response = self.session.get(
                f"{self.base_url}/{resource_type}",
                params=params,
                timeout=self.timeout
            )
            
            if response.status_code != 200:
                logger.error(f"Search failed for {resource_type}: {response.status_code}")
                return []
                
            bundle = response.json()
            results = []
            if 'entry' in bundle:
                for entry in bundle['entry']:
                    if 'resource' in entry:
                        results.append(entry['resource'])
            
            # Armazenar no cache
            if use_cache:
                cache_key = self._get_cache_key(resource_type, params)
                self._set_cache(cache_key, results)
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching {resource_type}: {e}")
            return []
    
    def search_resources_no_cache(self, resource_type: str, params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Busca de recursos FHIR sem cache. Útil para dados que precisam estar sempre atualizados.
        """
        return self.search_resources(resource_type, params, use_cache=False)

    def get_resource(self, resource_type: str, resource_id: str) -> Optional[Dict[str, Any]]:
        """
        Recupera um único recurso FHIR pelo ID.
        
        Args:
            resource_type: Tipo do recurso (Ex: 'Practitioner', 'Patient')
            resource_id: ID do recurso no FHIR
        
        Returns:
            Dict com o recurso completo, ou None se não encontrado
        """
        try:
            response = self.session.get(
                f"{self.base_url}/{resource_type}/{resource_id}",
                timeout=self.timeout
            )
            
            if response.status_code == 404:
                logger.warning(f"{resource_type}/{resource_id} not found")
                return None
            
            if response.status_code != 200:
                logger.error(f"Failed to get {resource_type}/{resource_id}: {response.status_code}")
                return None
                
            logger.info(f"{resource_type} retrieved: ID={resource_id}")
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"Error retrieving {resource_type}/{resource_id}: {str(e)}")
            return None

    def create_patient_resource(
        self,
        first_name: str,
        last_name: str,
        birth_date: str,  # Format: YYYY-MM-DD
        cpf: Optional[str] = None,
        gender: Optional[str] = None,  # male, female, other, unknown
        telecom: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """
        Cria um novo recurso Patient no FHIR.
        
        Args:
            first_name: Nome(s) do paciente
            last_name: Sobrenome do paciente
            birth_date: Data de nascimento (YYYY-MM-DD)
            cpf: CPF do paciente (opcional, único identificador)
            gender: Gênero (male, female, other, unknown)
            telecom: Lista de contatos [{"system": "phone", "value": "..."}]
        
        Returns:
            Dict com resourceType, id e metadados da criação
            
        Raises:
            FHIRServiceException: Se falhar na validação ou criação
        """
        try:
            # Criar objeto Patient FHIR R4
            patient = Patient()
            
            # 1. Nome (obrigatório, estrutura FHIR)
            human_name = HumanName()
            human_name.given = [first_name]
            human_name.family = last_name
            human_name.use = "official"
            patient.name = [human_name]
            
            # 2. Identificador (CPF como identificador único)
            if cpf:
                identifier = Identifier()
                # Use canonical project CPF system for consistency across services
                identifier.system = "http://openehrcore.com.br/cpf"
                identifier.value = cpf
                identifier.type = CodeableConcept()
                # Provide multiple codings so clients can detect CPF regardless of code used
                coding_cpf = Coding()
                coding_cpf.system = "http://terminology.hl7.org/CodeSystem/v2-0203"
                coding_cpf.code = "CPF"
                coding_tax = Coding()
                coding_tax.system = "http://terminology.hl7.org/CodeSystem/v2-0203"
                coding_tax.code = "TAX"
                # Keep both codings (CPF and TAX) so external clients can detect either code
                identifier.type.coding = [coding_cpf, coding_tax]
                patient.identifier = [identifier]
            
            # 3. Data de nascimento
            if birth_date:
                patient.birthDate = FHIRDate(birth_date)
            
            # 4. Gênero
            if gender:
                patient.gender = gender
            
            # 5. Contatos (telefone, email)
            if telecom:
                contact_points = []
                for contact in telecom:
                    cp = ContactPoint()
                    cp.system = contact.get("system", "phone")  # phone, email, etc
                    cp.value = contact.get("value")
                    contact_points.append(cp)
                patient.telecom = contact_points
            
            # Validar estrutura antes de enviar
            logger.info(f"Creating Patient: {last_name}, {first_name} (CPF: {cpf})")
            
            # Serializar para JSON FHIR
            patient_json = patient.as_json()
            
            # Enviar POST para HAPI FHIR
            response = self.session.post(
                f"{self.base_url}/Patient",
                json=patient_json,
                timeout=self.timeout
            )
            
            if response.status_code not in [200, 201]:
                logger.error(f"FHIR Server error: {response.status_code} - {response.text}")
                raise FHIRServiceException(
                    f"Failed to create Patient: {response.status_code} - {response.text}"
                )
            
            result = response.json()
            patient_id = result.get("id")
            logger.info(f"Patient created successfully: ID={patient_id}")
            
            # --- AUDITORIA (PROVENANCE) ---
            if self.user:
                self.create_provenance_resource(
                    target_reference=f"Patient/{patient_id}",
                    activity="CREATE",
                    agent_name=str(self.user)
                )

            return {
                "resourceType": "Patient",
                "id": patient_id,
                "name": f"{first_name} {last_name}",
                "cpf": cpf,
                "birthDate": birth_date,
                "gender": gender,
                "created_at": datetime.utcnow().isoformat(),
            }
            
        except Exception as e:
            logger.error(f"Error creating Patient resource: {str(e)}")
            raise FHIRServiceException(f"Failed to create Patient: {str(e)}")

    def get_patient_by_id(self, patient_id: str) -> Dict[str, Any]:
        """
        Recupera um recurso Patient pelo ID do FHIR.
        
        Args:
            patient_id: ID do paciente no FHIR
        
        Returns:
            Dict com o recurso Patient completo
            
        Raises:
            CircuitBreakerOpen: Se circuit breaker está aberto
            FHIRServiceException: Se o recurso não for encontrado
        """
        # Verificar circuit breaker antes de tentar
        self._check_circuit()
        
        try:
            response = self.session.get(
                f"{self.base_url}/Patient/{patient_id}",
                timeout=self.timeout
            )
            
            if response.status_code == 404:
                # 404 não é falha de servidor, não registrar no circuit breaker
                raise FHIRServiceException(f"Patient not found: {patient_id}")
            
            response.raise_for_status()
            
            # Tentar parsear JSON
            try:
                result = response.json()
            except ValueError as e:
                # JSON malformado - registrar falha
                self._record_failure()
                logger.error(f"Invalid JSON from FHIR server for Patient {patient_id}: {str(e)}")
                raise FHIRServiceException(f"Invalid JSON response from FHIR server: {str(e)}")
            
            # Sucesso - resetar contadores
            self._record_success()
            logger.info(f"Patient retrieved: ID={patient_id}")
            return result
        
        except FHIRServiceException:
            # 404 ou erro específico - não registrar como falha de infraestrutura
            raise
            
        except requests.exceptions.Timeout as e:
            self._record_failure()
            logger.error(f"Timeout retrieving Patient {patient_id}: {str(e)}")
            raise FHIRServiceException(f"FHIR Server timeout: {str(e)}")
            
        except requests.exceptions.ConnectionError as e:
            self._record_failure()
            logger.error(f"Connection error retrieving Patient {patient_id}: {str(e)}")
            raise FHIRServiceException(f"FHIR Server connection failed: {str(e)}")
            
        except requests.RequestException as e:
            self._record_failure()
            logger.error(f"Error retrieving Patient {patient_id}: {str(e)}")
            raise FHIRServiceException(f"Failed to retrieve Patient: {str(e)}")

    def update_patient_resource(self, patient_id: str, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Atualiza um recurso Patient existente.
        """
        try:
            # Primeiro, buscar o paciente atual para preservar ID e outros campos se necessário
            # Mas idealmente construímos um novo objeto com os dados novos e o mesmo ID
            
            from fhirclient.models.patient import Patient
            from fhirclient.models.humanname import HumanName
            from fhirclient.models.identifier import Identifier
            from fhirclient.models.codeableconcept import CodeableConcept
            from fhirclient.models.coding import Coding
            from fhirclient.models.contactpoint import ContactPoint
            from fhirclient.models.fhirdate import FHIRDate
            
            patient = Patient()
            patient.id = patient_id
            
            # 1. Nome
            if 'first_name' in patient_data or 'last_name' in patient_data:
                human_name = HumanName()
                human_name.given = [patient_data.get('first_name', '')] 
                human_name.family = patient_data.get('last_name', '')
                human_name.use = "official"
                patient.name = [human_name]
            
            # 2. Identificador (CPF)
            if 'cpf' in patient_data and patient_data['cpf']:
                identifier = Identifier()
                identifier.system = "http://openehrcore.com.br/cpf"
                identifier.value = patient_data['cpf']
                identifier.type = CodeableConcept()
                identifier.type.coding = [Coding()]
                identifier.type.coding[0].system = "http://terminology.hl7.org/CodeSystem/v2-0203"
                identifier.type.coding[0].code = "CPF"
                patient.identifier = [identifier]
            
            # 3. Data de nascimento
            if 'birth_date' in patient_data:
                patient.birthDate = FHIRDate(patient_data['birth_date'])
            
            # 4. Gênero
            if 'gender' in patient_data:
                patient.gender = patient_data['gender']
            
            # 5. Contatos
            if 'telecom' in patient_data:
                contact_points = []
                for contact in patient_data['telecom']:
                    cp = ContactPoint()
                    cp.system = contact.get("system", "phone")
                    cp.value = contact.get("value")
                    contact_points.append(cp)
                patient.telecom = contact_points
                
            # Serializar
            patient_json = patient.as_json()
            
            response = self.session.put(
                f"{self.base_url}/Patient/{patient_id}",
                json=patient_json,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            logger.info(f"Patient updated: ID={patient_id}")
            return response.json()
            
        except Exception as e:
            logger.error(f"Error updating Patient {patient_id}: {str(e)}")
            raise FHIRServiceException(f"Failed to update Patient: {str(e)}")

    def delete_patient_resource(self, patient_id: str) -> bool:
        """
        Remove um recurso Patient.
        """
        try:
            response = self.session.delete(
                f"{self.base_url}/Patient/{patient_id}",
                timeout=self.timeout
            )
            
            if response.status_code == 404:
                return False # Já não existia
                
            response.raise_for_status()
            logger.info(f"Patient deleted: ID={patient_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting Patient {patient_id}: {str(e)}")
            raise FHIRServiceException(f"Failed to delete Patient: {str(e)}")

    def search_patients(self, name: Optional[str] = None, offset: int = 0, count: int = 20) -> Dict[str, Any]:
        """
        Busca pacientes no servidor FHIR com paginação.
        
        Args:
            name: Nome para busca parcial
            offset: Deslocamento inicial (pular N registros)
            count: Número máximo de registros para retornar
            
        Returns:
            Dict com total, links e lista de resultados
        """
        try:
            params = {
                "_sort": "-_lastUpdated",
                "_count": count,
                "_offset": offset
            }
            if name:
                params["name"] = name
                
            response = self.session.get(
                f"{self.base_url}/Patient",
                params=params,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            bundle = response.json()
            
            patients = []
            if "entry" in bundle:
                for entry in bundle["entry"]:
                    if "resource" in entry:
                        patients.append(entry["resource"])
                        
            return {
                "total": bundle.get("total", 0),
                "results": patients
            }
            
        except requests.RequestException as e:
            logger.error(f"Error searching patients: {str(e)}")
            raise FHIRServiceException(f"Failed to search patients: {str(e)}")

    def create_encounter_resource(
        self,
        patient_id: str,
        encounter_type: str,  # "consultation", "hospitalization", etc
        status: str = "finished",  # planned, arrived, triaged, in-progress, finished, cancelled
        period_start: Optional[str] = None,  # ISO datetime
        period_end: Optional[str] = None,
        reason_code: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Cria um novo recurso Encounter (consulta/internação) no FHIR.
        
        Args:
            patient_id: ID do paciente relacionado
            encounter_type: Tipo de encontro
            status: Status do encontro
            period_start: Data/hora de início (ISO format)
            period_end: Data/hora de término
            reason_code: Motivo da consulta
        
        Returns:
            Dict com resourceType, id e metadados
            
        Raises:
            FHIRServiceException: Se falhar na criação
        """
        try:
            encounter = Encounter()
            
            # Status (obrigatório)
            encounter.status = status

            # Class (obrigatório) - usando AMB (ambulatory)
            class_coding = Coding()
            class_coding.system = "http://terminology.hl7.org/CodeSystem/v3-ActCode"
            class_coding.code = "AMB"
            class_coding.display = "ambulatory"
            encounter.class_fhir = class_coding
            
            # Tipo de encontro
            type_coding = CodeableConcept()
            type_coding.coding = [Coding()]
            type_coding.coding[0].system = "http://terminology.hl7.org/CodeSystem/encounter-type"
            type_coding.coding[0].code = encounter_type
            encounter.type = [type_coding]
            
            # Relacionar ao paciente
            from fhirclient.models.fhirreference import FHIRReference
            encounter.subject = FHIRReference(jsondict={"reference": f"Patient/{patient_id}"})
            
            # Período (quando aconteceu)
            if period_start or period_end:
                period = Period()
                if period_start:
                    period.start = FHIRDateTime(period_start)
                if period_end:
                    period.end = FHIRDateTime(period_end)
                encounter.period = period
            
            logger.info(f"Creating Encounter for Patient {patient_id}, type: {encounter_type}")
            
            response = self.session.post(
                f"{self.base_url}/Encounter",
                json=encounter.as_json(),
                timeout=self.timeout
            )
            
            if response.status_code not in [200, 201]:
                raise FHIRServiceException(
                    f"Failed to create Encounter: {response.status_code} - {response.text}"
                )
            
            result = response.json()
            encounter_id = result.get("id")
            logger.info(f"Encounter created successfully: ID={encounter_id}")
            
            return {
                "resourceType": "Encounter",
                "id": encounter_id,
                "patientId": patient_id,
                "type": encounter_type,
                "status": status,
                "created_at": datetime.utcnow().isoformat(),
            }
            
        except Exception as e:
            logger.error(f"Error creating Encounter: {str(e)}")
            raise FHIRServiceException(f"Failed to create Encounter: {str(e)}")

    def create_observation_resource(
        self,
        patient_id: str,
        code: str,  # LOINC code para a observação
        value: Optional[str] = None,
        status: str = "final",  # preliminary, final, amended, corrected, cancelled
        components: Optional[List[Dict[str, Any]]] = None, # [{"code": "...", "value": "..."}]
        encounter_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Cria um novo recurso Observation (resultado de teste/medição) no FHIR.
        Suporta observações simples (value) ou complexas (components).
        
        Args:
            patient_id: ID do paciente
            code: LOINC code da observação
            value: Valor da observação (para simples)
            status: Status da observação
            components: Lista de componentes (para complexas, ex: BP)
            encounter_id: ID do encontro relacionado (opcional)
        
        Returns:
            Dict com resourceType, id e metadados
            
        Raises:
            FHIRServiceException: Se falhar na criação
        """
        try:
            observation = Observation()
            
            # Status (obrigatório)
            observation.status = status
            
            # Código LOINC (o que está sendo observado)
            code_concept = CodeableConcept()
            code_concept.coding = [Coding()]
            code_concept.coding[0].system = "http://loinc.org"
            code_concept.coding[0].code = code
            observation.code = code_concept
            
            # Relacionar ao paciente
            from fhirclient.models.fhirreference import FHIRReference
            observation.subject = FHIRReference(jsondict={"reference": f"Patient/{patient_id}"})
            
            # Relacionar ao encontro (Encounter)
            if encounter_id:
                observation.encounter = FHIRReference(jsondict={"reference": f"Encounter/{encounter_id}"})

            # Valor da observação (Simples)
            if value is not None:
                quantity = Quantity()
                quantity.value = float(value)
                observation.valueQuantity = quantity

            # Componentes (Complexa - ex: BP)
            if components:
                observation.component = []
                for comp in components:
                    from fhirclient.models.observation import ObservationComponent
                    obs_comp = ObservationComponent()
                    
                    # Component Code
                    comp_code = CodeableConcept()
                    comp_code.coding = [Coding()]
                    comp_code.coding[0].system = "http://loinc.org"
                    comp_code.coding[0].code = comp.get("code")
                    obs_comp.code = comp_code
                    
                    # Component Value
                    comp_val = Quantity()
                    comp_val.value = float(comp.get("value"))
                    if comp.get("unit"):
                        comp_val.unit = comp.get("unit")
                    obs_comp.valueQuantity = comp_val
                    
                    observation.component.append(obs_comp)
            
            # Data da observação
            # Fix: Remover microsegundos e adicionar Z para compatibilidade FHIR strict
            observation.effectiveDateTime = FHIRDateTime(datetime.utcnow().replace(microsecond=0).isoformat() + "Z")
            
            logger.info(f"Creating Observation for Patient {patient_id}, code: {code}")
            
            response = self.session.post(
                f"{self.base_url}/Observation",
                json=observation.as_json(),
                timeout=self.timeout
            )
            
            if response.status_code not in [200, 201]:
                raise FHIRServiceException(
                    f"Failed to create Observation: {response.status_code} - {response.text}"
                )
            
            result = response.json()
            obs_id = result.get("id")
            logger.info(f"Observation created successfully: ID={obs_id}")
            
            return {
                "resourceType": "Observation",
                "id": obs_id,
                "patientId": patient_id,
                "encounterId": encounter_id,
                "code": code,
                "value": value,
                "components": components,
                "status": status,
                "created_at": datetime.utcnow().isoformat(),
            }
            
        except Exception as e:
            logger.error(f"Error creating Observation: {str(e)}")
            raise FHIRServiceException(f"Failed to create Observation: {str(e)}")

    def get_observations_by_patient_id(self, patient_id: str) -> List[Dict[str, Any]]:
        """
        Recupera todas as observações de um paciente.
        
        Args:
            patient_id: ID do paciente
            
        Returns:
            Lista de recursos Observation
        """
        try:
            # Busca por observações onde subject = Patient/{id}
            # Ordenado por data decrescente (_sort=-date)
            response = self.session.get(
                f"{self.base_url}/Observation",
                params={
                    "subject": f"Patient/{patient_id}",
                    "_sort": "-date"
                },
                timeout=self.timeout
            )
            
            response.raise_for_status()
            
            bundle = response.json()
            
            # Extrair recursos do Bundle
            observations = []
            if "entry" in bundle:
                for entry in bundle["entry"]:
                    if "resource" in entry:
                        observations.append(entry["resource"])
            
            logger.info(f"Retrieved {len(observations)} observations for Patient {patient_id}")
            return observations
            
        except requests.RequestException as e:
            logger.error(f"Error retrieving observations for Patient {patient_id}: {str(e)}")
            raise FHIRServiceException(f"Failed to retrieve observations: {str(e)}")

    def create_condition_resource(
        self,
        patient_id: str,
        code: str,
        display: str,
        clinical_status: str = "active",
        verification_status: str = "confirmed",
        encounter_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        try:
            condition = Condition()
            
            # Clinical Status
            condition.clinicalStatus = CodeableConcept()
            condition.clinicalStatus.coding = [Coding()]
            condition.clinicalStatus.coding[0].system = "http://terminology.hl7.org/CodeSystem/condition-clinical"
            condition.clinicalStatus.coding[0].code = clinical_status
            
            # Verification Status
            condition.verificationStatus = CodeableConcept()
            condition.verificationStatus.coding = [Coding()]
            condition.verificationStatus.coding[0].system = "http://terminology.hl7.org/CodeSystem/condition-ver-status"
            condition.verificationStatus.coding[0].code = verification_status
            condition.verificationStatus.coding[0].display = verification_status
            
            # Code
            condition.code = CodeableConcept()
            condition.code.coding = [Coding()]
            condition.code.coding[0].system = "http://snomed.info/sct"
            condition.code.coding[0].code = code
            condition.code.coding[0].display = display
            condition.code.text = display
            
            # Subject
            from fhirclient.models.fhirreference import FHIRReference
            condition.subject = FHIRReference(jsondict={"reference": f"Patient/{patient_id}"})

            # Encounter
            if encounter_id:
                condition.encounter = FHIRReference(jsondict={"reference": f"Encounter/{encounter_id}"})
            
            condition.recordedDate = FHIRDateTime(datetime.utcnow().isoformat())
            
            response = self.session.post(
                f"{self.base_url}/Condition",
                json=condition.as_json(),
                timeout=self.timeout
            )
            
            if response.status_code not in [200, 201]:
                raise FHIRServiceException(f"Failed to create Condition: {response.text}")
            
            result = response.json()
            condition_id = result.get("id")
            
            return {
                "resourceType": "Condition",
                "id": condition_id,
                "patientId": patient_id,
                "encounterId": encounter_id,
                "code": code,
                "display": display,
                "clinicalStatus": clinical_status,
                "verificationStatus": verification_status,
                "created_at": datetime.utcnow().isoformat(),
            }
            
        except Exception as e:
            logger.error(f"Error creating Condition: {str(e)}")
            raise FHIRServiceException(f"Failed to create Condition: {str(e)}")

    def get_conditions_by_patient_id(self, patient_id: str) -> List[Dict[str, Any]]:
        try:
            response = self.session.get(
                f"{self.base_url}/Condition",
                params={"subject": f"Patient/{patient_id}"},
                timeout=self.timeout
            )
            response.raise_for_status()
            bundle = response.json()
            return [entry["resource"] for entry in bundle.get("entry", []) if "resource" in entry]
        except Exception as e:
            logger.error(f"Error getting conditions: {str(e)}")
            raise FHIRServiceException(f"Failed to get conditions: {str(e)}")

    def create_allergy_resource(
        self,
        patient_id: str,
        code: str,
        display: str,
        clinical_status: str = "active",
        criticality: str = "low",
        encounter_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        try:
            allergy = AllergyIntolerance()
            
            # Clinical Status
            allergy.clinicalStatus = CodeableConcept()
            allergy.clinicalStatus.coding = [Coding()]
            allergy.clinicalStatus.coding[0].system = "http://terminology.hl7.org/CodeSystem/allergyintolerance-clinical"
            allergy.clinicalStatus.coding[0].code = clinical_status
            
            # Criticality
            allergy.criticality = criticality
            
            # Code
            allergy.code = CodeableConcept()
            allergy.code.coding = [Coding()]
            allergy.code.coding[0].system = "http://snomed.info/sct"
            allergy.code.coding[0].code = code
            allergy.code.coding[0].display = display
            allergy.code.text = display
            
            # Patient
            from fhirclient.models.fhirreference import FHIRReference
            allergy.patient = FHIRReference(jsondict={"reference": f"Patient/{patient_id}"})

            # Encounter
            if encounter_id:
                allergy.encounter = FHIRReference(jsondict={"reference": f"Encounter/{encounter_id}"})
            
            allergy.recordedDate = FHIRDateTime(datetime.utcnow().isoformat())
            
            response = self.session.post(
                f"{self.base_url}/AllergyIntolerance",
                json=allergy.as_json(),
                timeout=self.timeout
            )
            
            if response.status_code not in [200, 201]:
                raise FHIRServiceException(f"Failed to create Allergy: {response.text}")
            
            result = response.json()
            allergy_id = result.get("id")
            
            return {
                "resourceType": "AllergyIntolerance",
                "id": allergy_id,
                "patientId": patient_id,
                "encounterId": encounter_id,
                "code": code,
                "display": display,
                "clinicalStatus": clinical_status,
                "criticality": criticality,
                "created_at": datetime.utcnow().isoformat(),
            }
            
        except Exception as e:
            logger.error(f"Error creating Allergy: {str(e)}")
            raise FHIRServiceException(f"Failed to create Allergy: {str(e)}")

    def create_medication_request_resource(
        self,
        patient_id: str,
        medication_code: str,
        medication_display: str,
        status: str = "active",
        intent: str = "order",
        dosage_instruction: str = None,
        encounter_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        try:
            from fhirclient.models.medicationrequest import MedicationRequest
            
            med_req = MedicationRequest()
            med_req.status = status
            med_req.intent = intent
            
            # MedicationCodeableConcept
            med_req.medicationCodeableConcept = CodeableConcept()
            med_req.medicationCodeableConcept.coding = [Coding()]
            med_req.medicationCodeableConcept.coding[0].system = "http://www.nlm.nih.gov/research/umls/rxnorm"
            med_req.medicationCodeableConcept.coding[0].code = medication_code
            med_req.medicationCodeableConcept.coding[0].display = medication_display
            med_req.medicationCodeableConcept.text = medication_display
            
            # Subject
            from fhirclient.models.fhirreference import FHIRReference
            med_req.subject = FHIRReference(jsondict={"reference": f"Patient/{patient_id}"})
            
            # Encounter
            if encounter_id:
                med_req.encounter = FHIRReference(jsondict={"reference": f"Encounter/{encounter_id}"})
            
            # DosageInstruction
            if dosage_instruction:
                from fhirclient.models.dosage import Dosage
                dosage = Dosage()
                dosage.text = dosage_instruction
                med_req.dosageInstruction = [dosage]
            
            med_req.authoredOn = FHIRDateTime(datetime.utcnow().isoformat())
            
            response = self.session.post(
                f"{self.base_url}/MedicationRequest",
                json=med_req.as_json(),
                timeout=self.timeout
            )
            
            if response.status_code not in [200, 201]:
                raise FHIRServiceException(f"Failed to create MedicationRequest: {response.text}")
            
            result = response.json()
            med_req_id = result.get("id")
            
            return {
                "resourceType": "MedicationRequest",
                "id": med_req_id,
                "patientId": patient_id,
                "encounterId": encounter_id,
                "medicationCode": medication_code,
                "medicationDisplay": medication_display,
                "status": status,
                "intent": intent,
                "dosageInstruction": dosage_instruction,
                "created_at": datetime.utcnow().isoformat(),
            }
            
        except Exception as e:
            logger.error(f"Error creating MedicationRequest: {str(e)}")
            raise FHIRServiceException(f"Failed to create MedicationRequest: {str(e)}")

    def create_service_request_resource(
        self,
        patient_id: str,
        code: str,
        display: str,
        status: str = "active",
        intent: str = "order",
        encounter_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        try:
            from fhirclient.models.servicerequest import ServiceRequest
            
            req = ServiceRequest()
            req.status = status
            req.intent = intent
            
            # Code
            req.code = CodeableConcept()
            req.code.coding = [Coding()]
            req.code.coding[0].system = "http://snomed.info/sct"
            req.code.coding[0].code = code
            req.code.coding[0].display = display
            req.code.text = display
            
            # Subject
            from fhirclient.models.fhirreference import FHIRReference
            req.subject = FHIRReference(jsondict={"reference": f"Patient/{patient_id}"})
            
            # Encounter
            if encounter_id:
                req.encounter = FHIRReference(jsondict={"reference": f"Encounter/{encounter_id}"})
            
            req.authoredOn = FHIRDateTime(datetime.utcnow().isoformat())
            
            response = self.session.post(
                f"{self.base_url}/ServiceRequest",
                json=req.as_json(),
                timeout=self.timeout
            )
            
            if response.status_code not in [200, 201]:
                raise FHIRServiceException(f"Failed to create ServiceRequest: {response.text}")
            
            result = response.json()
            req_id = result.get("id")
            
            return {
                "resourceType": "ServiceRequest",
                "id": req_id,
                "patientId": patient_id,
                "encounterId": encounter_id,
                "code": code,
                "display": display,
                "status": status,
                "intent": intent,
                "created_at": datetime.utcnow().isoformat(),
            }
            
        except Exception as e:
            logger.error(f"Error creating ServiceRequest: {str(e)}")
            raise FHIRServiceException(f"Failed to create ServiceRequest: {str(e)}")

    def create_clinical_impression_resource(
        self,
        patient_id: str,
        summary: str,
        status: str = "completed",
        encounter_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        try:
            from fhirclient.models.clinicalimpression import ClinicalImpression
            
            impression = ClinicalImpression()
            impression.status = status
            impression.summary = summary
            
            # Subject
            from fhirclient.models.fhirreference import FHIRReference
            impression.subject = FHIRReference(jsondict={"reference": f"Patient/{patient_id}"})
            
            # Encounter
            if encounter_id:
                impression.encounter = FHIRReference(jsondict={"reference": f"Encounter/{encounter_id}"})
            
            impression.effectiveDateTime = FHIRDateTime(datetime.utcnow().isoformat())
            
            response = self.session.post(
                f"{self.base_url}/ClinicalImpression",
                json=impression.as_json(),
                timeout=self.timeout
            )
            
            if response.status_code not in [200, 201]:
                raise FHIRServiceException(f"Failed to create ClinicalImpression: {response.text}")
            
            result = response.json()
            impression_id = result.get("id")
            
            return {
                "resourceType": "ClinicalImpression",
                "id": impression_id,
                "patientId": patient_id,
                "encounterId": encounter_id,
                "summary": summary,
                "status": status,
                "created_at": datetime.utcnow().isoformat(),
            }
            
        except Exception as e:
            logger.error(f"Error creating ClinicalImpression: {str(e)}")
            raise FHIRServiceException(f"Failed to create ClinicalImpression: {str(e)}")

    def get_allergies_by_patient_id(self, patient_id: str) -> List[Dict[str, Any]]:
        try:
            response = self.session.get(
                f"{self.base_url}/AllergyIntolerance",
                params={"patient": f"Patient/{patient_id}"},
                timeout=self.timeout
            )
            response.raise_for_status()
            bundle = response.json()
            return [entry["resource"] for entry in bundle.get("entry", []) if "resource" in entry]
        except Exception as e:
            logger.error(f"Error getting allergies: {str(e)}")
            raise FHIRServiceException(f"Failed to get allergies: {str(e)}")

    def create_appointment_resource(
        self,
        patient_id: str,
        status: str,
        description: str,
        start: str,
        end: str,
    ) -> Dict[str, Any]:
        try:
            appointment = Appointment()
            
            appointment.status = status
            appointment.description = description
            
            if start:
                appointment.start = FHIRDateTime(start)
            if end:
                appointment.end = FHIRDateTime(end)
            
            # Participant (Patient)
            from fhirclient.models.appointment import AppointmentParticipant
            participant = AppointmentParticipant()
            participant.actor = FHIRReference(jsondict={"reference": f"Patient/{patient_id}"})
            participant.status = "accepted"
            appointment.participant = [participant]
            
            appointment.created = FHIRDateTime(datetime.utcnow().isoformat())
            
            response = self.session.post(
                f"{self.base_url}/Appointment",
                json=appointment.as_json(),
                timeout=self.timeout
            )
            
            if response.status_code not in [200, 201]:
                raise FHIRServiceException(f"Failed to create Appointment: {response.text}")
                
            return response.json()
            
        except Exception as e:
            logger.error(f"Error creating Appointment: {str(e)}")
            raise FHIRServiceException(f"Failed to create Appointment: {str(e)}")

    def get_appointments_by_patient_id(self, patient_id: str) -> List[Dict[str, Any]]:
        try:
            response = self.session.get(
                f"{self.base_url}/Appointment",
                params={
                    "actor": f"Patient/{patient_id}",
                    "_sort": "date"
                },
                timeout=self.timeout
            )
            response.raise_for_status()
            bundle = response.json()
            return [entry["resource"] for entry in bundle.get("entry", []) if "resource" in entry]
        except Exception as e:
            logger.error(f"Error getting appointments: {str(e)}")
            raise FHIRServiceException(f"Failed to get appointments: {str(e)}")

    def get_encounters_by_patient_id(self, patient_id: str) -> List[Dict[str, Any]]:
        try:
            response = self.session.get(
                f"{self.base_url}/Encounter",
                params={"subject": f"Patient/{patient_id}", "_sort": "-date"},
                timeout=self.timeout
            )
            response.raise_for_status()
            bundle = response.json()
            return [entry["resource"] for entry in bundle.get("entry", []) if "resource" in entry]
        except Exception as e:
            logger.error(f"Error getting encounters: {str(e)}")
            raise FHIRServiceException(f"Failed to get encounters: {str(e)}")

    def create_schedule_resource(
        self,
        practitioner_id: str,
        actor_display: str,
        comment: str = "Horário de Atendimento",
    ) -> Dict[str, Any]:
        try:
            from fhirclient.models.schedule import Schedule
            
            schedule = Schedule()
            schedule.active = True
            schedule.comment = comment
            
            # Actor (Practitioner)
            from fhirclient.models.fhirreference import FHIRReference
            actor = FHIRReference(jsondict={"reference": f"Practitioner/{practitioner_id}", "display": actor_display})
            schedule.actor = [actor]
            
            response = self.session.post(
                f"{self.base_url}/Schedule",
                json=schedule.as_json(),
                timeout=self.timeout
            )
            
            if response.status_code not in [200, 201]:
                raise FHIRServiceException(f"Failed to create Schedule: {response.text}")
                
            result = response.json()
            return {
                "resourceType": "Schedule",
                "id": result.get("id"),
                "actor": actor_display,
                "comment": comment
            }
        except Exception as e:
            logger.error(f"Error creating Schedule: {str(e)}")
            raise FHIRServiceException(f"Failed to create Schedule: {str(e)}")

    def create_slot_resource(
        self,
        schedule_id: str,
        start: str,
        end: str,
        status: str = "free",
    ) -> Dict[str, Any]:
        try:
            from fhirclient.models.slot import Slot
            from fhirclient.models.fhirinstant import FHIRInstant
            
            slot = Slot()
            slot.status = status
            slot.start = FHIRInstant(start)
            slot.end = FHIRInstant(end)
            
            # Schedule Reference
            from fhirclient.models.fhirreference import FHIRReference
            slot.schedule = FHIRReference(jsondict={"reference": f"Schedule/{schedule_id}"})
            
            response = self.session.post(
                f"{self.base_url}/Slot",
                json=slot.as_json(),
                timeout=self.timeout
            )
            
            if response.status_code not in [200, 201]:
                raise FHIRServiceException(f"Failed to create Slot: {response.text}")
                
            result = response.json()
            return {
                "resourceType": "Slot",
                "id": result.get("id"),
                "scheduleId": schedule_id,
                "start": start,
                "end": end,
                "status": status
            }
        except Exception as e:
            logger.error(f"Error creating Slot: {str(e)}")
            raise FHIRServiceException(f"Failed to create Slot: {str(e)}")

    def search_slots(self, start: str = None, end: str = None, status: str = "free") -> List[Dict[str, Any]]:
        try:
            params = {"status": status}
            if start:
                params["start"] = f"ge{start}"
            if end:
                params["start"] = [f"ge{start}", f"lt{end}"] # HAPI FHIR supports multiple params with same name for range

            response = self.session.get(
                f"{self.base_url}/Slot",
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            bundle = response.json()
            return [entry["resource"] for entry in bundle.get("entry", []) if "resource" in entry]
        except Exception as e:
            logger.error(f"Error searching Slots: {str(e)}")
            raise FHIRServiceException(f"Failed to search Slots: {str(e)}")

    def create_questionnaire(
        self,
        title: str,
        items: List[Dict[str, Any]],
        status: str = "active"
    ) -> Dict[str, Any]:
        try:
            from fhirclient.models.questionnaire import Questionnaire, QuestionnaireItem
            
            q = Questionnaire()
            q.title = title
            q.status = status
            
            q_items = []
            for item_data in items:
                item = QuestionnaireItem()
                item.linkId = item_data.get("linkId")
                item.text = item_data.get("text")
                item.type = item_data.get("type")
                q_items.append(item)
            
            q.item = q_items
            
            response = self.session.post(
                f"{self.base_url}/Questionnaire",
                json=q.as_json(),
                timeout=self.timeout
            )
            
            if response.status_code not in [200, 201]:
                raise FHIRServiceException(f"Failed to create Questionnaire: {response.text}")
                
            return response.json()
        except Exception as e:
            logger.error(f"Error creating Questionnaire: {str(e)}")
            raise FHIRServiceException(f"Failed to create Questionnaire: {str(e)}")

    def create_questionnaire_response(
        self,
        questionnaire_id: str,
        patient_id: str,
        answers: List[Dict[str, Any]],
        status: str = "completed"
    ) -> Dict[str, Any]:
        try:
            from fhirclient.models.questionnaireresponse import QuestionnaireResponse, QuestionnaireResponseItem, QuestionnaireResponseItemAnswer
            from fhirclient.models.fhirreference import FHIRReference
            
            qr = QuestionnaireResponse()
            qr.status = status
            qr.questionnaire = f"Questionnaire/{questionnaire_id}"
            qr.subject = FHIRReference(jsondict={"reference": f"Patient/{patient_id}"})
            
            qr_items = []
            for ans_data in answers:
                item = QuestionnaireResponseItem()
                item.linkId = ans_data.get("linkId")
                item.text = ans_data.get("text")
                
                # Simple string answer support for now
                if "valueString" in ans_data:
                    ans = QuestionnaireResponseItemAnswer()
                    ans.valueString = ans_data["valueString"]
                    item.answer = [ans]
                
                qr_items.append(item)
            
            qr.item = qr_items
            
            response = self.session.post(
                f"{self.base_url}/QuestionnaireResponse",
                json=qr.as_json(),
                timeout=self.timeout
            )
            
        except Exception as e:
            logger.error(f"Error creating QuestionnaireResponse: {str(e)}")
            raise FHIRServiceException(f"Failed to create QuestionnaireResponse: {str(e)}")

    # -------------------------------------------------------------------------
    # Módulo Financeiro (Sprint 6)
    # -------------------------------------------------------------------------

    def create_coverage_resource(
        self,
        patient_id: str,
        payor_name: str,
        subscriber_id: str,
        status: str = "active",
        type_text: str = "health insurance"
    ) -> Dict[str, Any]:
        """
        Cria um recurso Coverage (Plano de Saúde/Convênio).
        """
        try:
            cov = Coverage()
            cov.status = status
            cov.subscriberId = subscriber_id
            
            # Relacionar ao paciente (Subscriber & Beneficiary)
            from fhirclient.models.fhirreference import FHIRReference
            ref = FHIRReference(jsondict={"reference": f"Patient/{patient_id}"})
            cov.subscriber = ref
            cov.beneficiary = ref
            
            # Payor (Pagador) - Simplificado como Organization text only por enquanto
            # Em prod real, seria uma Reference(Organization/id)
            payor_ref = FHIRReference()
            payor_ref.display = payor_name
            cov.payor = [payor_ref]
            
            # Tipo
            type_concept = CodeableConcept()
            type_concept.text = type_text
            cov.type = type_concept
            
            logger.info(f"Creating Coverage for Patient {patient_id}, Payor: {payor_name}")
            
            response = self.session.post(
                f"{self.base_url}/Coverage",
                json=cov.as_json(),
                timeout=self.timeout
            )
            
            if response.status_code not in [200, 201]:
                raise FHIRServiceException(f"Failed to create Coverage: {response.text}")
                
            return response.json()
        except Exception as e:
            logger.error(f"Error creating Coverage: {str(e)}")
            raise FHIRServiceException(f"Failed to create Coverage: {str(e)}")

    def create_account_resource(
        self,
        patient_id: str,
        name: str = "Conta Paciente",
        status: str = "active",
        currency: str = "BRL"
    ) -> Dict[str, Any]:
        """
        Cria um recurso Account (Conta Financeira do Paciente).
        """
        try:
            acc = Account()
            acc.status = status
            acc.name = name
            
            # Subject (Paciente)
            from fhirclient.models.fhirreference import FHIRReference
            acc.subject = [FHIRReference(jsondict={"reference": f"Patient/{patient_id}"})]
            
            # Mock currency/balance extension if needed, but standard Account lacks 'balance' field in R4 direct root.
            # Usually calculated from Invoices/Payments.
            # We'll rely on listing Invoices linked to this Account for balance.
            
            logger.info(f"Creating Account for Patient {patient_id}")
            
            response = self.session.post(
                f"{self.base_url}/Account",
                json=acc.as_json(),
                timeout=self.timeout
            )
            
            if response.status_code not in [200, 201]:
                raise FHIRServiceException(f"Failed to create Account: {response.text}")
                
            return response.json()
        except Exception as e:
            logger.error(f"Error creating Account: {str(e)}")
            raise FHIRServiceException(f"Failed to create Account: {str(e)}")

    def create_invoice_resource(
        self,
        patient_id: str,
        account_id: str,
        total_gross: float,
        status: str = "issued"
    ) -> Dict[str, Any]:
        """
        Cria um recurso Invoice (Fatura/Cobrança).
        """
        try:
            inv = Invoice()
            inv.status = status
            inv.date = FHIRDateTime(datetime.utcnow().replace(microsecond=0).isoformat() + "Z")
            
            # Subject
            from fhirclient.models.fhirreference import FHIRReference
            inv.subject = FHIRReference(jsondict={"reference": f"Patient/{patient_id}"})
            
            # Account
            if account_id:
                inv.account = FHIRReference(jsondict={"reference": f"Account/{account_id}"})
            
            # Total Gross
            m = Money()
            m.value = float(total_gross)
            m.currency = "BRL"
            inv.totalGross = m
            # totalNet required sometimes, reusing gross for simplicity
            inv.totalNet = m 

            logger.info(f"Creating Invoice for Patient {patient_id}: {total_gross} BRL")
            
            response = self.session.post(
                f"{self.base_url}/Invoice",
                json=inv.as_json(),
                timeout=self.timeout
            )
            
            if response.status_code not in [200, 201]:
                raise FHIRServiceException(f"Failed to create Invoice: {response.text}")
                
            return response.json()
        except Exception as e:
            logger.error(f"Error creating Invoice: {str(e)}")
            raise FHIRServiceException(f"Failed to create Invoice: {str(e)}")
    # --------------------------------------------------------------------------
    # COMPOSITION (Documentos Clínicos)
    # --------------------------------------------------------------------------
    
    def create_composition_resource(self,
                                  patient_id: str,
                                  practitioner_id: str,
                                  date_time: str,
                                  doc_type: str,
                                  title: str,
                                  text_content: str,
                                  status: str = "final") -> Dict[str, Any]:
        """
        Cria um recurso Composition (Documento Clínico).
        """
        try:
            from fhirclient.models.composition import Composition, CompositionSection
            from fhirclient.models.codeableconcept import CodeableConcept
            from fhirclient.models.coding import Coding
            from fhirclient.models.fhirdatetime import FHIRDateTime
            from fhirclient.models.fhirreference import FHIRReference
            from fhirclient.models.narrative import Narrative
            
            comp = Composition()
            comp.status = status
            
            # Data do documento
            comp.date = FHIRDateTime(date_time)
            
            # Título
            comp.title = title
            
            # Tipo de documento (LOINC codes simplificados para exemplo)
            # 11488-4: Consultation note
            # 18842-5: Discharge summary
            # 34117-2: History and physical note
            loinc_map = {
                "anamnese": ("34117-2", "History and physical note"),
                "evolucao": ("11506-3", "Progress note"),
                "receita": ("57833-6", "Prescription for medication"),
                "atestado": ("34105-7", "Hospital discharge summary") # Aproximação
            }
            
            code_val, display_val = loinc_map.get(doc_type, ("11506-3", "Progress note"))
            
            doc_type_concept = CodeableConcept()
            doc_type_concept.coding = [Coding()]
            doc_type_concept.coding[0].system = "http://loinc.org"
            doc_type_concept.coding[0].code = code_val
            doc_type_concept.coding[0].display = display_val
            comp.type = doc_type_concept
            
            # Sujeito (Paciente)
            subject_ref = FHIRReference()
            subject_ref.reference = f"Patient/{patient_id}"
            comp.subject = subject_ref
            
            # Autor (Médico)
            # Na prática seria um Practitioner, mas para simplificar usamos string ou referência dummy se não existir
            # Ideal: Practitioner/practitioner_id
            author_ref = FHIRReference()
            author_ref.reference = f"Practitioner/{practitioner_id}" if practitioner_id else "Practitioner/example"
            comp.author = [author_ref]
            
            # Seção Principal (Conteúdo de texto)
            section = CompositionSection()
            section.title = "Conteúdo Principal"
            
            # Narrativa HTML
            div_content = f"<div xmlns=\"http://www.w3.org/1999/xhtml\">{text_content}</div>"
            narrative = Narrative()
            narrative.status = "generated"
            narrative.div = div_content
            section.text = narrative
            
            comp.section = [section]
            
            # Serializar e Enviar
            comp_json = comp.as_json()
            
            response = self.session.post(
                f"{self.base_url}/Composition",
                json=comp_json,
                timeout=self.timeout
            )
            
            try:
                response.raise_for_status()
            except requests.exceptions.HTTPError as e:
                error_body = response.text
                logger.error(f"FHIR Server Error: {error_body}")
                raise FHIRServiceException(f"FHIR Server rejected: {error_body}")
            
            logger.info(f"Composition created for Patient {patient_id}")
            return response.json()

        except Exception as e:
            logger.error(f"Error creating Composition: {str(e)}")
            raise FHIRServiceException(f"Failed to create Composition: {str(e)}")


    def get_composition_by_id(self, composition_id: str) -> Dict[str, Any]:
        """
        Recupera um documento (Composition) pelo ID.
        """
        try:
            response = self.session.get(
                f"{self.base_url}/Composition/{composition_id}",
                timeout=self.timeout
            )
            if response.status_code == 404:
                raise FHIRServiceException(f"Document not found: {composition_id}")
            
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Error retrieving Composition {composition_id}: {str(e)}")
            raise FHIRServiceException(f"Failed to retrieve document: {str(e)}")

    def delete_composition_resource(self, composition_id: str) -> bool:
        """
        Remove um documento (Composition) pelo ID.
        """
        try:
            response = self.session.delete(
                f"{self.base_url}/Composition/{composition_id}",
                timeout=self.timeout
            )
            response.raise_for_status()
            logger.info(f"Composition deleted: ID={composition_id}")
            return True
        except requests.RequestException as e:
            logger.error(f"Error deleting Composition {composition_id}: {str(e)}")
            raise FHIRServiceException(f"Failed to delete document: {str(e)}")

    def get_total_count(self, resource_type: str, search_params: Optional[Dict[str, Any]] = None) -> int:
        """
        Retorna a contagem total de recursos usando _summary=count.
        """
        params = search_params or {}
        params['_summary'] = 'count'
        try:
            response = self.session.get(
                f"{self.base_url}/{resource_type}",
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json().get('total', 0)
        except requests.RequestException as e:
            logger.error(f"Error counting {resource_type}: {str(e)}")
            return 0

    def search_resources(self, resource_type: str, search_params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Busca recursos no servidor FHIR usando parâmetros de consulta.
        """
        try:
            response = self.session.get(
                f"{self.base_url}/{resource_type}",
                params=search_params,
                timeout=self.timeout
            )
            response.raise_for_status()
            bundle = response.json()
            
            # Extrair os recursos do Bundle
            if 'entry' in bundle:
                return [entry['resource'] for entry in bundle['entry']]
            return []
            
        except requests.RequestException as e:
            logger.error(f"Error searching {resource_type}: {str(e)}")
            raise FHIRServiceException(f"Failed to search {resource_type}: {str(e)}")

    def get_observations_by_patient_id(self, patient_id: str, category: Optional[str] = None) -> List[Dict[str, Any]]:
        params = {"patient": f"Patient/{patient_id}"}
        if category:
            params["category"] = category
        return self.search_resources("Observation", params)

    def get_allergies_by_patient_id(self, patient_id: str) -> List[Dict[str, Any]]:
        return self.search_resources("AllergyIntolerance", {"patient": f"Patient/{patient_id}"})

    def get_medications_by_patient_id(self, patient_id: str) -> List[Dict[str, Any]]:
        return self.search_resources("MedicationRequest", {"subject": f"Patient/{patient_id}"})

    def get_encounters_by_patient_id(self, patient_id: str) -> List[Dict[str, Any]]:
        return self.search_resources("Encounter", {"subject": f"Patient/{patient_id}"})

    def get_appointments_by_patient_id(self, patient_id: str) -> List[Dict[str, Any]]:
        return self.search_resources("Appointment", {"actor": f"Patient/{patient_id}"})




    def create_provenance_resource(
        self,
        target_reference: str, # "Patient/123"
        activity: str, # "CREATE", "UPDATE", "DELETE"
        agent_name: str,
    ) -> None:
        """
        Cria registro de auditoria (Provenance).
        """
        try:
            provenance = Provenance()
            
            # Target (o que foi modificado)
            provenance.target = [FHIRReference(jsondict={"reference": target_reference})]
            
            # Recorded
            # Provenance.recorded is (instant), requires FHIRInstant
            provenance.recorded = FHIRInstant(datetime.utcnow().isoformat() + "Z")
            
            # Activity (Reason)
            # Simplificação: Usar text para descrever a ação por enquanto
            code_concept = CodeableConcept()
            code_concept.text = activity
            provenance.reason = [code_concept]
            
            # Agent (Quem fez)
            agent = ProvenanceAgent()
            agent.who = FHIRReference(jsondict={"display": agent_name})
            # Se tivéssemos Practitioner ID, usaríamos aqui: {"reference": f"Practitioner/{id}"}
            provenance.agent = [agent]
            
            # Enviar
            logger.info(f"Auditing {activity} on {target_reference} by {agent_name}")
            self.session.post(
                f"{self.base_url}/Provenance",
                json=provenance.as_json(),
                timeout=self.timeout
            )
        except Exception as e:
            # Auditoria não deve bloquear a operação principal, mas deve ser logada
            logger.error(f"Failed to create Provenance for {target_reference}: {str(e)}")

    def export_patient_data(self, patient_id: str) -> Dict[str, Any]:
        """
        Gera um Bundle contendo todos os dados clínicos do paciente.
        Simula a operação $everything.
        """
        try:
            logger.info(f"Starting Data Export for Patient {patient_id}...")
            
            # 1. Patient
            patient = self.get_patient_by_id(patient_id)
            
            # 2. Encounters
            encounters = self.get_encounters_by_patient_id(patient_id)
            
            # 3. Observations
            observations = self.get_observations_by_patient_id(patient_id)
            
            # 4. Conditions
            conditions = self.get_conditions_by_patient_id(patient_id)
            
            # 5. Allergies
            allergies = self.get_allergies_by_patient_id(patient_id)
            
            # 6. Medications
            medications = self.get_medications_by_patient_id(patient_id)

            # 7. Appointments (Extra)
            appointments = self.get_appointments_by_patient_id(patient_id)

            # Montar Bundle
            bundle = {
                "resourceType": "Bundle",
                "type": "collection",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "entry": []
            }
            
            def add_entry(resource):
                bundle["entry"].append({"resource": resource})
                
            add_entry(patient)
            for enc in encounters: add_entry(enc)
            for obs in observations: add_entry(obs)
            for cond in conditions: add_entry(cond)
            for alg in allergies: add_entry(alg)
            for med in medications: add_entry(med)
            for app in appointments: add_entry(app)
            
            logger.info(f"Export Bundle created with {len(bundle['entry'])} resources.")
            
            # Audit Export action
            if self.user:
                self.create_provenance_resource(
                    target_reference=f"Patient/{patient_id}",
                    activity="EXPORT",
                    agent_name=str(self.user)
                )
                
            return bundle
            
        except Exception as e:
            logger.error(f"Error exporting patient data: {str(e)}")
            raise FHIRServiceException(f"Failed to export data: {str(e)}")
