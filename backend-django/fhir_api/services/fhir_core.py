"""
FHIR Core Service - Manipulação segura de recursos FHIR.

Este serviço atua como o guardião da comunicação com o HAPI FHIR Server.
Ele utiliza a biblioteca fhirclient para garantir que todos os recursos
sejam criados e manipulados de acordo com a especificação FHIR R4.

Princípio: O HAPI FHIR é a autoridade absoluta dos dados clínicos.
"""

import requests
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
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
from fhirclient.models.fhirreference import FHIRReference
from fhirclient.models.condition import Condition
from fhirclient.models.allergyintolerance import AllergyIntolerance
from fhirclient.models.appointment import Appointment


logger = logging.getLogger(__name__)


class FHIRServiceException(Exception):
    """Exceção customizada para erros de integração FHIR."""
    pass


class FHIRService:
    """
    Serviço centralizado para comunicação com HAPI FHIR Server.
    
    Garante:
    - Tipagem FHIR correta (usa objetos da lib fhirclient)
    - Validação de dados antes de enviar
    - Tratamento de erros padronizado
    - Logging de todas as operações
    """

    def __init__(self):
        self.base_url = settings.FHIR_SERVER_URL
        self.timeout = settings.FHIR_SERVER_TIMEOUT
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/fhir+json',
            'Accept': 'application/fhir+json',
        })

    def health_check(self) -> bool:
        """
        Verifica se o servidor FHIR está respondendo.
        
        Returns:
            bool: True se o servidor está saudável
            
        Raises:
            FHIRServiceException: Se o servidor não responde
        """
        try:
            response = self.session.get(
                f"{self.base_url}/metadata",
                timeout=self.timeout
            )
            response.raise_for_status()
            logger.info("FHIR Server health check: OK")
            return True
        except requests.RequestException as e:
            logger.error(f"FHIR Server health check failed: {str(e)}")
            raise FHIRServiceException(f"FHIR Server unreachable: {str(e)}")

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
                identifier.system = "http://openehrcore.com.br/cpf"
                identifier.value = cpf
                identifier.type = CodeableConcept()
                identifier.type.coding = [Coding()]
                identifier.type.coding[0].system = "http://terminology.hl7.org/CodeSystem/v2-0203"
                identifier.type.coding[0].code = "CPF"
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
            FHIRServiceException: Se o recurso não for encontrado
        """
        try:
            response = self.session.get(
                f"{self.base_url}/Patient/{patient_id}",
                timeout=self.timeout
            )
            
            if response.status_code == 404:
                raise FHIRServiceException(f"Patient not found: {patient_id}")
            
            response.raise_for_status()
            
            logger.info(f"Patient retrieved: ID={patient_id}")
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"Error retrieving Patient {patient_id}: {str(e)}")
            raise FHIRServiceException(f"Failed to retrieve Patient: {str(e)}")

    def search_patients(self, name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Busca pacientes no servidor FHIR.
        
        Args:
            name: Nome para busca parcial (opcional)
            
        Returns:
            Lista de recursos Patient
        """
        try:
            params = {"_sort": "-_lastUpdated"}
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
                        
            logger.info(f"Search patients (name={name}): found {len(patients)}")
            return patients
            
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
            
            # Tipo de encontro
            type_coding = CodeableConcept()
            type_coding.coding = [Coding()]
            type_coding.coding[0].system = "http://terminology.hl7.org/CodeSystem/encounter-type"
            type_coding.coding[0].code = encounter_type
            encounter.type = [type_coding]
            
            # Relacionar ao paciente
            from fhirclient.models.fhirreference import FHIRReference
            encounter.subject = FHIRReference(json={"reference": f"Patient/{patient_id}"})
            
            # Período (quando aconteceu)
            if period_start or period_end:
                period = Period()
                if period_start:
                    period.start = FHIRDate(period_start)
                if period_end:
                    period.end = FHIRDate(period_end)
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
        value: str,
        status: str = "final",  # preliminary, final, amended, corrected, cancelled
    ) -> Dict[str, Any]:
        """
        Cria um novo recurso Observation (resultado de teste/medição) no FHIR.
        
        Args:
            patient_id: ID do paciente
            code: LOINC code da observação
            value: Valor da observação
            status: Status da observação
        
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
            observation.subject = FHIRReference(json={"reference": f"Patient/{patient_id}"})
            
            # Valor da observação
            quantity = Quantity()
            quantity.value = float(value)
            observation.value = quantity
            
            # Data da observação
            observation.effectiveDateTime = FHIRDate(datetime.utcnow().isoformat())
            
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
                "code": code,
                "value": value,
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
            
            # Code
            condition.code = CodeableConcept()
            condition.code.coding = [Coding()]
            condition.code.coding[0].system = "http://snomed.info/sct"
            condition.code.coding[0].code = code
            condition.code.coding[0].display = display
            condition.code.text = display
            
            # Subject
            from fhirclient.models.fhirreference import FHIRReference
            condition.subject = FHIRReference(json={"reference": f"Patient/{patient_id}"})
            
            condition.recordedDate = FHIRDate(datetime.utcnow().isoformat())
            
            response = self.session.post(
                f"{self.base_url}/Condition",
                json=condition.as_json(),
                timeout=self.timeout
            )
            
            if response.status_code not in [200, 201]:
                raise FHIRServiceException(f"Failed to create Condition: {response.text}")
                
            return response.json()
            
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
            allergy.patient = FHIRReference(json={"reference": f"Patient/{patient_id}"})
            
            allergy.recordedDate = FHIRDate(datetime.utcnow().isoformat())
            
            response = self.session.post(
                f"{self.base_url}/AllergyIntolerance",
                json=allergy.as_json(),
                timeout=self.timeout
            )
            
            if response.status_code not in [200, 201]:
                raise FHIRServiceException(f"Failed to create Allergy: {response.text}")
                
            return response.json()
            
        except Exception as e:
            logger.error(f"Error creating Allergy: {str(e)}")
            raise FHIRServiceException(f"Failed to create Allergy: {str(e)}")

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
                appointment.start = FHIRDate(start)
            if end:
                appointment.end = FHIRDate(end)
            
            # Participant (Patient)
            from fhirclient.models.appointment import AppointmentParticipant
            participant = AppointmentParticipant()
            participant.actor = FHIRReference(json={"reference": f"Patient/{patient_id}"})
            participant.status = "accepted"
            appointment.participant = [participant]
            
            appointment.created = FHIRDate(datetime.utcnow().isoformat())
            
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
