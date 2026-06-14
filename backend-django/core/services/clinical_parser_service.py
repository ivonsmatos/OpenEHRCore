import logging
import requests
import json
from decouple import config
from datetime import datetime
from core.services import llm_client

logger = logging.getLogger(__name__)


class ClinicalParserService:
    """
    Extração de dados clínicos estruturados de texto livre (apoio à decisão),
    usando LLM open-source self-hosted (vLLM/Ollama) e criando recursos FHIR.
    """
    _instance = None

    # FHIR server
    FHIR_BASE_URL = config('FHIR_SERVER_URL', default='http://localhost:8080/fhir')

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ClinicalParserService, cls).__new__(cls)
        return cls._instance

    def parse_clinical_note(self, text: str, patient_id: str, encounter_id: str = None) -> dict:
        """
        Parses clinical note text and extracts structured data.
        Creates FHIR resources for: medications, diagnoses, exams, vitals.
        
        Returns:
            dict with extracted data and created resource IDs
        """
        if not llm_client.available():
            return {"error": "LLM não configurado (LLM_BASE_URL)", "resources_created": []}
        
        if not text or len(text.strip()) < 10:
            return {"error": "Text too short", "resources_created": []}
        
        # Parse text with LLM
        parsed_data = self._extract_clinical_entities(text)
        
        if "error" in parsed_data:
            return parsed_data
        
        # Create FHIR resources
        created_resources = []
        
        # Create MedicationRequests
        for med in parsed_data.get("medications", []):
            try:
                resource_id = self._create_medication_request(patient_id, encounter_id, med)
                if resource_id:
                    created_resources.append({"type": "MedicationRequest", "id": resource_id, "display": med.get("name")})
            except Exception as e:
                logger.error(f"Error creating MedicationRequest: {e}")
        
        # Create Conditions (diagnoses)
        for dx in parsed_data.get("diagnoses", []):
            try:
                resource_id = self._create_condition(patient_id, encounter_id, dx)
                if resource_id:
                    created_resources.append({"type": "Condition", "id": resource_id, "display": dx.get("name")})
            except Exception as e:
                logger.error(f"Error creating Condition: {e}")
        
        # Create ServiceRequests (exams)
        for exam in parsed_data.get("exams", []):
            try:
                resource_id = self._create_service_request(patient_id, encounter_id, exam)
                if resource_id:
                    created_resources.append({"type": "ServiceRequest", "id": resource_id, "display": exam.get("name")})
            except Exception as e:
                logger.error(f"Error creating ServiceRequest: {e}")
        
        # Create Observations (vitals)
        for vital in parsed_data.get("vitals", []):
            try:
                resource_id = self._create_observation(patient_id, encounter_id, vital)
                if resource_id:
                    created_resources.append({"type": "Observation", "id": resource_id, "display": vital.get("name")})
            except Exception as e:
                logger.error(f"Error creating Observation: {e}")
        
        return {
            "parsed_data": parsed_data,
            "resources_created": created_resources,
            "summary": f"Created {len(created_resources)} FHIR resources"
        }

    def _extract_clinical_entities(self, text: str) -> dict:
        """
        Uses Llama to extract clinical entities from text.
        """
        system_prompt = """Você é um sistema de NLP clínico especializado em extrair informações estruturadas de notas médicas.
Analise o texto e extraia as seguintes entidades em formato JSON:

{
    "medications": [
        {"name": "Nome do medicamento", "dose": "dose", "route": "via", "frequency": "frequência", "duration": "duração"}
    ],
    "diagnoses": [
        {"name": "Nome do diagnóstico/condição", "status": "active/resolved/provisional", "severity": "mild/moderate/severe"}
    ],
    "exams": [
        {"name": "Nome do exame", "type": "laboratory/imaging/procedure", "urgency": "routine/urgent/stat"}
    ],
    "vitals": [
        {"name": "Nome do sinal vital", "value": "valor numérico", "unit": "unidade"}
    ],
    "allergies": [
        {"substance": "substância", "reaction": "tipo de reação"}
    ]
}

Regras:
- Se um campo não for mencionado, use array vazio []
- Para medicamentos, extraia dose, via de administração (VO, IV, IM, SC, etc) e frequência
- Para diagnósticos, classifique como "provisional" se for hipótese, "active" se confirmado
- Para exames, identifique se é laboratorial, imagem ou procedimento
- Para sinais vitais, extraia o valor numérico e unidade (PAS/PAD em mmHg, FC em bpm, etc)
- Responda APENAS com JSON válido, sem explicações"""

        user_prompt = f"""Extraia as entidades clínicas do seguinte texto:

{text}

Responda APENAS com o JSON estruturado."""

        try:
            content = llm_client.chat(
                [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": llm_client.redact_pii(user_prompt)},
                ],
                max_tokens=2000,
                temperature=0.1,
                json_mode=True,
            )
            if not content:
                return {"error": "IA indisponível"}
            return json.loads(content)
        except Exception as e:
            logger.error(f"Entity extraction failed: {e}")
            return {"error": str(e)}

    def _create_medication_request(self, patient_id: str, encounter_id: str, med: dict) -> str:
        """Creates a FHIR MedicationRequest resource."""
        resource = {
            "resourceType": "MedicationRequest",
            "status": "active",
            "intent": "order",
            "subject": {"reference": f"Patient/{patient_id}"},
            "authoredOn": datetime.now().isoformat(),
            "medicationCodeableConcept": {
                "text": med.get("name", "Medicamento não especificado")
            },
            "dosageInstruction": [{
                "text": f"{med.get('dose', '')} {med.get('route', '')} {med.get('frequency', '')}".strip(),
                "route": {"text": med.get("route", "")},
                "timing": {"code": {"text": med.get("frequency", "")}}
            }]
        }
        
        if encounter_id:
            resource["encounter"] = {"reference": f"Encounter/{encounter_id}"}
        
        return self._post_fhir_resource("MedicationRequest", resource)

    def _create_condition(self, patient_id: str, encounter_id: str, dx: dict) -> str:
        """Creates a FHIR Condition resource."""
        status_map = {
            "active": "active",
            "resolved": "resolved",
            "provisional": "provisional"
        }
        
        resource = {
            "resourceType": "Condition",
            "clinicalStatus": {
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                    "code": status_map.get(dx.get("status", "active"), "active")
                }]
            },
            "verificationStatus": {
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
                    "code": "provisional" if dx.get("status") == "provisional" else "confirmed"
                }]
            },
            "subject": {"reference": f"Patient/{patient_id}"},
            "recordedDate": datetime.now().date().isoformat(),
            "code": {
                "text": dx.get("name", "Diagnóstico não especificado")
            }
        }
        
        if dx.get("severity"):
            resource["severity"] = {"text": dx.get("severity")}
        
        if encounter_id:
            resource["encounter"] = {"reference": f"Encounter/{encounter_id}"}
        
        return self._post_fhir_resource("Condition", resource)

    def _create_service_request(self, patient_id: str, encounter_id: str, exam: dict) -> str:
        """Creates a FHIR ServiceRequest resource for exams."""
        priority_map = {
            "routine": "routine",
            "urgent": "urgent",
            "stat": "stat"
        }
        
        category_map = {
            "laboratory": ("108252007", "Laboratory procedure"),
            "imaging": ("363679005", "Imaging"),
            "procedure": ("387713003", "Surgical procedure")
        }
        
        cat_code, cat_display = category_map.get(exam.get("type", "laboratory"), ("108252007", "Laboratory procedure"))
        
        resource = {
            "resourceType": "ServiceRequest",
            "status": "active",
            "intent": "order",
            "priority": priority_map.get(exam.get("urgency", "routine"), "routine"),
            "subject": {"reference": f"Patient/{patient_id}"},
            "authoredOn": datetime.now().isoformat(),
            "code": {
                "text": exam.get("name", "Exame não especificado")
            },
            "category": [{
                "coding": [{
                    "system": "http://snomed.info/sct",
                    "code": cat_code,
                    "display": cat_display
                }]
            }]
        }
        
        if encounter_id:
            resource["encounter"] = {"reference": f"Encounter/{encounter_id}"}
        
        return self._post_fhir_resource("ServiceRequest", resource)

    def _create_observation(self, patient_id: str, encounter_id: str, vital: dict) -> str:
        """Creates a FHIR Observation resource for vitals."""
        # Map common vital signs to LOINC codes
        loinc_map = {
            "pressão arterial": ("85354-9", "Blood pressure"),
            "pas": ("8480-6", "Systolic blood pressure"),
            "pad": ("8462-4", "Diastolic blood pressure"),
            "frequência cardíaca": ("8867-4", "Heart rate"),
            "fc": ("8867-4", "Heart rate"),
            "temperatura": ("8310-5", "Body temperature"),
            "saturação": ("2708-6", "Oxygen saturation"),
            "sato2": ("2708-6", "Oxygen saturation"),
            "frequência respiratória": ("9279-1", "Respiratory rate"),
            "glicemia": ("2345-7", "Glucose"),
            "peso": ("29463-7", "Body weight"),
            "altura": ("8302-2", "Body height")
        }
        
        vital_name = vital.get("name", "").lower()
        loinc_code, loinc_display = None, None
        
        for key, (code, display) in loinc_map.items():
            if key in vital_name:
                loinc_code, loinc_display = code, display
                break
        
        resource = {
            "resourceType": "Observation",
            "status": "final",
            "category": [{
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                    "code": "vital-signs",
                    "display": "Vital Signs"
                }]
            }],
            "code": {
                "text": vital.get("name", "Sinal vital")
            },
            "subject": {"reference": f"Patient/{patient_id}"},
            "effectiveDateTime": datetime.now().isoformat()
        }
        
        if loinc_code:
            resource["code"]["coding"] = [{
                "system": "http://loinc.org",
                "code": loinc_code,
                "display": loinc_display
            }]
        
        # Add value
        try:
            value = float(vital.get("value", 0))
            resource["valueQuantity"] = {
                "value": value,
                "unit": vital.get("unit", ""),
                "system": "http://unitsofmeasure.org"
            }
        except (ValueError, TypeError):
            resource["valueString"] = str(vital.get("value", ""))
        
        if encounter_id:
            resource["encounter"] = {"reference": f"Encounter/{encounter_id}"}
        
        return self._post_fhir_resource("Observation", resource)

    def _post_fhir_resource(self, resource_type: str, resource: dict) -> str:
        """Posts a FHIR resource and returns the created ID."""
        try:
            response = requests.post(
                f"{self.FHIR_BASE_URL}/{resource_type}",
                json=resource,
                headers={"Content-Type": "application/fhir+json"},
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                result = response.json()
                resource_id = result.get("id")
                logger.info(f"Created {resource_type}/{resource_id}")
                return resource_id
            else:
                logger.error(f"Failed to create {resource_type}: {response.status_code} - {response.text[:200]}")
                return None
                
        except Exception as e:
            logger.error(f"FHIR POST error: {e}")
            return None
