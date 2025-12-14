"""
FHIR R4 Schema Validation
=========================

Valida respostas da API contra schemas oficiais FHIR R4.
Garante conformidade com o padrão HL7 FHIR.

Requisitos:
    pip install fhir.resources

Schemas Validados:
    - Patient
    - Observation
    - Condition
    - MedicationRequest
    - Encounter
    - Practitioner
    - Organization

Uso:
    # Validar endpoint único
    python tests/test_fhir_schema_validation.py TestPatientSchema

    # Validar todos os schemas
    pytest tests/test_fhir_schema_validation.py -v

    # Gerar relatório
    pytest tests/test_fhir_schema_validation.py --html=fhir_validation_report.html
"""

import json
import logging
import unittest
from typing import Dict, Any, Optional

import requests
from pydantic import ValidationError

# FHIR Resources models
try:
    from fhir.resources.patient import Patient
    from fhir.resources.observation import Observation
    from fhir.resources.condition import Condition
    from fhir.resources.medicationrequest import MedicationRequest
    from fhir.resources.encounter import Encounter
    from fhir.resources.practitioner import Practitioner
    from fhir.resources.organization import Organization
    from fhir.resources.bundle import Bundle
except ImportError:
    print("❌ ERRO: Instale fhir.resources")
    print("   pip install fhir.resources")
    exit(1)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FHIRSchemaValidator:
    """
    Valida recursos FHIR contra schemas oficiais.
    """
    
    BASE_URL = "http://localhost:8000/api/v1"
    
    # Mapeamento de recursos para modelos Pydantic
    RESOURCE_MODELS = {
        'Patient': Patient,
        'Observation': Observation,
        'Condition': Condition,
        'MedicationRequest': MedicationRequest,
        'Encounter': Encounter,
        'Practitioner': Practitioner,
        'Organization': Organization,
        'Bundle': Bundle
    }
    
    def __init__(self, base_url: Optional[str] = None):
        """
        Inicializa validador.
        
        Args:
            base_url: URL base da API FHIR
        """
        self.base_url = base_url or self.BASE_URL
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/fhir+json',
            'Accept': 'application/fhir+json'
        })
    
    def validate_resource(
        self,
        resource_data: Dict[str, Any],
        resource_type: str
    ) -> tuple[bool, Optional[str]]:
        """
        Valida um recurso FHIR.
        
        Args:
            resource_data: Dados do recurso (dict)
            resource_type: Tipo do recurso ('Patient', 'Observation', etc.)
            
        Returns:
            (is_valid, error_message)
        """
        if resource_type not in self.RESOURCE_MODELS:
            return False, f"Tipo de recurso '{resource_type}' não suportado"
        
        model_class = self.RESOURCE_MODELS[resource_type]
        
        try:
            # Valida usando Pydantic model
            validated = model_class(**resource_data)
            
            # Verifica campos obrigatórios
            if not validated.resourceType:
                return False, "Campo 'resourceType' ausente"
            
            if validated.resourceType != resource_type:
                return False, f"resourceType esperado '{resource_type}', encontrado '{validated.resourceType}'"
            
            logger.info(f"✅ {resource_type} válido: {validated.id}")
            return True, None
        
        except ValidationError as e:
            error_msg = self._format_validation_error(e)
            logger.error(f"❌ {resource_type} inválido: {error_msg}")
            return False, error_msg
        
        except Exception as e:
            error_msg = f"Erro inesperado: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return False, error_msg
    
    def _format_validation_error(self, error: ValidationError) -> str:
        """Formata erro de validação Pydantic"""
        errors = []
        for err in error.errors():
            loc = ' -> '.join(str(l) for l in err['loc'])
            msg = err['msg']
            errors.append(f"{loc}: {msg}")
        return "; ".join(errors)
    
    def validate_endpoint(
        self,
        endpoint: str,
        expected_resource_type: str
    ) -> tuple[bool, Optional[str], Optional[Dict]]:
        """
        Busca e valida recurso de um endpoint.
        
        Args:
            endpoint: Endpoint relativo (ex: '/patients/123')
            expected_resource_type: Tipo esperado do recurso
            
        Returns:
            (is_valid, error_message, resource_data)
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.get(url, timeout=10)
            
            if response.status_code != 200:
                return False, f"HTTP {response.status_code}", None
            
            resource_data = response.json()
            
            is_valid, error = self.validate_resource(
                resource_data,
                expected_resource_type
            )
            
            return is_valid, error, resource_data
        
        except requests.exceptions.RequestException as e:
            return False, f"Request error: {str(e)}", None
        
        except json.JSONDecodeError as e:
            return False, f"JSON inválido: {str(e)}", None
    
    def validate_bundle(self, bundle_data: Dict[str, Any]) -> tuple[bool, list]:
        """
        Valida um Bundle FHIR.
        
        Args:
            bundle_data: Dados do Bundle
            
        Returns:
            (is_valid, errors_list)
        """
        errors = []
        
        # Valida Bundle em si
        is_valid, error = self.validate_resource(bundle_data, 'Bundle')
        if not is_valid:
            errors.append(f"Bundle inválido: {error}")
            return False, errors
        
        # Valida cada entry
        entries = bundle_data.get('entry', [])
        for idx, entry in enumerate(entries):
            resource = entry.get('resource', {})
            resource_type = resource.get('resourceType')
            
            if not resource_type:
                errors.append(f"Entry {idx}: resourceType ausente")
                continue
            
            is_valid, error = self.validate_resource(resource, resource_type)
            if not is_valid:
                errors.append(f"Entry {idx} ({resource_type}): {error}")
        
        return len(errors) == 0, errors


class TestPatientSchema(unittest.TestCase):
    """Testes de validação de schema para Patient"""
    
    @classmethod
    def setUpClass(cls):
        cls.validator = FHIRSchemaValidator()
    
    def test_patient_minimal_valid(self):
        """Patient mínimo válido"""
        patient = {
            "resourceType": "Patient",
            "id": "test-123",
            "name": [{
                "family": "Silva",
                "given": ["João"]
            }]
        }
        
        is_valid, error = self.validator.validate_resource(patient, 'Patient')
        self.assertTrue(is_valid, f"Falhou: {error}")
    
    def test_patient_with_cpf_identifier(self):
        """Patient com identificador CPF (extensão brasileira)"""
        patient = {
            "resourceType": "Patient",
            "id": "test-456",
            "identifier": [{
                "system": "http://rnds.saude.gov.br/fhir/r4/NamingSystem/cpf",
                "value": "123.456.789-09"
            }],
            "name": [{
                "family": "Santos",
                "given": ["Maria"]
            }],
            "gender": "female",
            "birthDate": "1990-05-15"
        }
        
        is_valid, error = self.validator.validate_resource(patient, 'Patient')
        self.assertTrue(is_valid, f"Falhou: {error}")
    
    def test_patient_missing_resourceType(self):
        """Patient sem resourceType deve falhar"""
        patient = {
            "id": "test-789",
            "name": [{
                "family": "Costa"
            }]
        }
        
        is_valid, error = self.validator.validate_resource(patient, 'Patient')
        self.assertFalse(is_valid)
        self.assertIn("resourceType", error.lower())
    
    def test_patient_invalid_gender(self):
        """Patient com gender inválido"""
        patient = {
            "resourceType": "Patient",
            "id": "test-999",
            "name": [{"family": "Silva"}],
            "gender": "invalid_gender"  # Deve ser: male, female, other, unknown
        }
        
        is_valid, error = self.validator.validate_resource(patient, 'Patient')
        self.assertFalse(is_valid)
    
    def test_patient_from_api_endpoint(self):
        """Busca e valida Patient de endpoint real"""
        # Este teste pode falhar se API não estiver rodando
        is_valid, error, data = self.validator.validate_endpoint(
            '/patients/patient-123',
            'Patient'
        )
        
        if error and "404" in error:
            self.skipTest("Paciente não existe")
        
        self.assertTrue(is_valid, f"Falhou: {error}")


class TestObservationSchema(unittest.TestCase):
    """Testes de validação de schema para Observation"""
    
    @classmethod
    def setUpClass(cls):
        cls.validator = FHIRSchemaValidator()
    
    def test_observation_vital_signs(self):
        """Observation de sinais vitais"""
        observation = {
            "resourceType": "Observation",
            "id": "vitals-123",
            "status": "final",
            "category": [{
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                    "code": "vital-signs",
                    "display": "Vital Signs"
                }]
            }],
            "code": {
                "coding": [{
                    "system": "http://loinc.org",
                    "code": "85354-9",
                    "display": "Blood pressure"
                }]
            },
            "subject": {
                "reference": "Patient/patient-123"
            },
            "effectiveDateTime": "2024-01-15T10:00:00Z",
            "component": [
                {
                    "code": {
                        "coding": [{
                            "system": "http://loinc.org",
                            "code": "8480-6",
                            "display": "Systolic blood pressure"
                        }]
                    },
                    "valueQuantity": {
                        "value": 120,
                        "unit": "mmHg",
                        "system": "http://unitsofmeasure.org",
                        "code": "mm[Hg]"
                    }
                },
                {
                    "code": {
                        "coding": [{
                            "system": "http://loinc.org",
                            "code": "8462-4",
                            "display": "Diastolic blood pressure"
                        }]
                    },
                    "valueQuantity": {
                        "value": 80,
                        "unit": "mmHg",
                        "system": "http://unitsofmeasure.org",
                        "code": "mm[Hg]"
                    }
                }
            ]
        }
        
        is_valid, error = self.validator.validate_resource(observation, 'Observation')
        self.assertTrue(is_valid, f"Falhou: {error}")
    
    def test_observation_missing_status(self):
        """Observation sem status obrigatório"""
        observation = {
            "resourceType": "Observation",
            "id": "obs-invalid",
            "code": {
                "coding": [{
                    "system": "http://loinc.org",
                    "code": "15074-8"
                }]
            },
            "subject": {
                "reference": "Patient/123"
            }
            # Falta 'status' obrigatório
        }
        
        is_valid, error = self.validator.validate_resource(observation, 'Observation')
        self.assertFalse(is_valid)


class TestConditionSchema(unittest.TestCase):
    """Testes de validação de schema para Condition"""
    
    @classmethod
    def setUpClass(cls):
        cls.validator = FHIRSchemaValidator()
    
    def test_condition_valid(self):
        """Condition (diagnóstico) válido"""
        condition = {
            "resourceType": "Condition",
            "id": "condition-123",
            "clinicalStatus": {
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                    "code": "active"
                }]
            },
            "verificationStatus": {
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
                    "code": "confirmed"
                }]
            },
            "code": {
                "coding": [{
                    "system": "http://snomed.info/sct",
                    "code": "38341003",
                    "display": "Hypertension"
                }]
            },
            "subject": {
                "reference": "Patient/patient-123"
            },
            "onsetDateTime": "2023-01-01"
        }
        
        is_valid, error = self.validator.validate_resource(condition, 'Condition')
        self.assertTrue(is_valid, f"Falhou: {error}")


class TestBundleValidation(unittest.TestCase):
    """Testes de validação de Bundle (coleção de recursos)"""
    
    @classmethod
    def setUpClass(cls):
        cls.validator = FHIRSchemaValidator()
    
    def test_bundle_searchset(self):
        """Bundle de resultados de busca"""
        bundle = {
            "resourceType": "Bundle",
            "type": "searchset",
            "total": 2,
            "entry": [
                {
                    "resource": {
                        "resourceType": "Patient",
                        "id": "patient-1",
                        "name": [{"family": "Silva"}]
                    }
                },
                {
                    "resource": {
                        "resourceType": "Patient",
                        "id": "patient-2",
                        "name": [{"family": "Santos"}]
                    }
                }
            ]
        }
        
        is_valid, errors = self.validator.validate_bundle(bundle)
        self.assertTrue(is_valid, f"Erros: {errors}")
    
    def test_bundle_with_invalid_entry(self):
        """Bundle com entry inválido"""
        bundle = {
            "resourceType": "Bundle",
            "type": "searchset",
            "entry": [
                {
                    "resource": {
                        "resourceType": "Patient",
                        "id": "valid-patient",
                        "name": [{"family": "Valid"}]
                    }
                },
                {
                    "resource": {
                        # resourceType faltando
                        "id": "invalid",
                        "name": [{"family": "Invalid"}]
                    }
                }
            ]
        }
        
        is_valid, errors = self.validator.validate_bundle(bundle)
        self.assertFalse(is_valid)
        self.assertTrue(len(errors) > 0)


def run_validation_report():
    """Gera relatório de validação completo"""
    print("\n" + "="*80)
    print("🔍 FHIR R4 SCHEMA VALIDATION REPORT")
    print("="*80)
    
    validator = FHIRSchemaValidator()
    
    # Testa endpoints comuns
    endpoints = [
        ('/patients/patient-123', 'Patient'),
        ('/observations/obs-123', 'Observation'),
        ('/conditions/cond-123', 'Condition')
    ]
    
    results = []
    for endpoint, resource_type in endpoints:
        is_valid, error, data = validator.validate_endpoint(endpoint, resource_type)
        results.append({
            'endpoint': endpoint,
            'resource_type': resource_type,
            'valid': is_valid,
            'error': error
        })
    
    # Mostra resultados
    print(f"\n📊 Validados {len(results)} endpoints:\n")
    for r in results:
        status = "✅" if r['valid'] else "❌"
        print(f"{status} {r['endpoint']} ({r['resource_type']})")
        if not r['valid']:
            print(f"   Erro: {r['error']}")
    
    print("\n" + "="*80)
    
    # Resumo
    valid_count = sum(1 for r in results if r['valid'])
    print(f"\n✅ Válidos: {valid_count}/{len(results)}")
    print(f"❌ Inválidos: {len(results) - valid_count}/{len(results)}")
    print("\n" + "="*80 + "\n")


if __name__ == '__main__':
    # Modo CLI
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--report':
        run_validation_report()
    else:
        # Roda testes unitários
        unittest.main()
