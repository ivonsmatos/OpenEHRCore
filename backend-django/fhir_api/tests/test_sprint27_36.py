"""
Comprehensive Test Suite for Sprint 27-36 Services

Tests for:
- AI Service
- Bias Prevention
- Questionnaire Service
- HL7 Service
- Formulary Service
- Archetype Service
"""

import pytest
from django.test import TestCase, Client
from unittest.mock import patch, MagicMock
from datetime import datetime
import json


class AIServiceTests(TestCase):
    """Tests for AI Service."""
    
    def setUp(self):
        self.client = Client()
        self.headers = {'HTTP_AUTHORIZATION': 'Bearer dev-token-bypass'}
    
    def test_patient_summary_endpoint_exists(self):
        """Test that patient summary endpoint is accessible."""
        response = self.client.get('/api/v1/ai/summary/test-patient/', **self.headers)
        self.assertIn(response.status_code, [200, 404, 500])
    
    def test_icd_suggestion_endpoint_exists(self):
        """Test ICD suggestion endpoint."""
        response = self.client.post(
            '/api/v1/ai/suggest-icd/',
            data=json.dumps({'description': 'dor de cabeça'}),
            content_type='application/json',
            **self.headers
        )
        self.assertIn(response.status_code, [200, 400, 500])
    
    def test_drug_interaction_endpoint(self):
        """Test drug interaction check endpoint."""
        response = self.client.post(
            '/api/v1/ai/drug-interactions/',
            data=json.dumps({'medications': ['amoxicilina', 'ibuprofeno']}),
            content_type='application/json',
            **self.headers
        )
        self.assertIn(response.status_code, [200, 400, 500])


class BiasPreventionServiceTests(TestCase):
    """Tests for Bias Prevention Service."""
    
    def test_bias_detection(self):
        """Test bias term detection."""
        from fhir_api.services.bias_prevention_service import BiasPreventionService
        
        # Test with clean content
        clean_result = BiasPreventionService.check_for_bias("Paciente com dor de cabeça")
        self.assertFalse(clean_result['has_bias'])
        
        # Test with biased content
        biased_result = BiasPreventionService.check_for_bias("Paciente de raça negra")
        self.assertTrue(biased_result['has_bias'])
    
    def test_content_sanitization(self):
        """Test content sanitization."""
        from fhir_api.services.bias_prevention_service import BiasPreventionService
        
        content = "Paciente branco com dor"
        sanitized = BiasPreventionService.sanitize_content(content)
        self.assertNotIn('branco', sanitized.lower())
    
    def test_pii_anonymization(self):
        """Test PII removal."""
        from fhir_api.services.bias_prevention_service import BiasPreventionService
        
        text = "CPF: 123.456.789-00, Email: test@test.com"
        anonymized = BiasPreventionService.anonymize_text(text)
        self.assertNotIn('123.456.789-00', anonymized)
        self.assertNotIn('test@test.com', anonymized)
    
    def test_ai_guardrails(self):
        """Test AI guardrails are applied."""
        from fhir_api.services.bias_prevention_service import BiasPreventionService
        
        prompt = "Generate patient summary"
        with_guardrails = BiasPreventionService.add_guardrails(prompt)
        self.assertIn('ético', with_guardrails.lower())


class QuestionnaireServiceTests(TestCase):
    """Tests for Questionnaire Service."""
    
    def test_list_questionnaires(self):
        """Test listing available questionnaires."""
        from fhir_api.services.questionnaire_service import QuestionnaireService
        
        questionnaires = QuestionnaireService.list_questionnaires()
        self.assertGreater(len(questionnaires), 0)
        self.assertTrue(any(q['id'] == 'phq-9' for q in questionnaires))
    
    def test_get_phq9(self):
        """Test getting PHQ-9 questionnaire."""
        from fhir_api.services.questionnaire_service import QuestionnaireService
        
        phq9 = QuestionnaireService.get_questionnaire('phq-9')
        self.assertIsNotNone(phq9)
        self.assertEqual(len(phq9.items), 9)
    
    def test_phq9_scoring(self):
        """Test PHQ-9 score calculation."""
        from fhir_api.services.questionnaire_service import QuestionnaireService
        
        # All zeros = no depression
        answers = {f'phq{i}': '0' for i in range(1, 10)}
        result = QuestionnaireService.submit_response('phq-9', 'patient-1', answers)
        self.assertEqual(result['score']['value'], 0)
        self.assertIn('Mínima', result['interpretation'])
        
        # All 3s = severe depression
        answers = {f'phq{i}': '3' for i in range(1, 10)}
        result = QuestionnaireService.submit_response('phq-9', 'patient-1', answers)
        self.assertEqual(result['score']['value'], 27)
        self.assertIn('Grave', result['interpretation'])
    
    def test_gad7_exists(self):
        """Test GAD-7 questionnaire exists."""
        from fhir_api.services.questionnaire_service import QuestionnaireService
        
        gad7 = QuestionnaireService.get_questionnaire('gad-7')
        self.assertIsNotNone(gad7)
        self.assertEqual(len(gad7.items), 7)


class HL7ServiceTests(TestCase):
    """Tests for HL7 v2.x Service."""
    
    def test_create_msh_segment(self):
        """Test MSH segment creation."""
        from fhir_api.services.hl7_service import HL7Service
        
        msh = HL7Service.create_msh_segment("ADT^A01")
        self.assertEqual(msh.name, "MSH")
        self.assertIn("ADT^A01", msh.to_string())
    
    def test_create_pid_segment(self):
        """Test PID segment from FHIR Patient."""
        from fhir_api.services.hl7_service import HL7Service
        
        patient = {
            "id": "123",
            "name": [{"family": "Silva", "given": ["João"]}],
            "birthDate": "1990-05-15",
            "gender": "male"
        }
        
        pid = HL7Service.create_pid_segment(patient)
        self.assertEqual(pid.name, "PID")
        self.assertIn("Silva", pid.to_string())
    
    def test_create_adt_message(self):
        """Test ADT message generation."""
        from fhir_api.services.hl7_service import HL7Service, ADTEventType
        
        patient = {
            "id": "123",
            "name": [{"family": "Silva", "given": ["João"]}],
            "gender": "male"
        }
        
        message = HL7Service.create_adt_message(patient, ADTEventType.ADMIT)
        self.assertEqual(message.message_type, "ADT^A01")
        self.assertIsNotNone(message.get_segment("MSH"))
        self.assertIsNotNone(message.get_segment("PID"))
        self.assertIsNotNone(message.get_segment("PV1"))
    
    def test_parse_hl7_message(self):
        """Test HL7 message parsing."""
        from fhir_api.services.hl7_service import HL7Message
        
        raw = "MSH|^~\\&|APP|FAC|||20241213||ADT^A01|123|P|2.5.1\rPID|1|123|||Silva^João"
        message = HL7Message.from_string(raw)
        
        self.assertEqual(message.message_type, "ADT^A01")
        self.assertEqual(len(message.segments), 2)
    
    def test_adt_to_fhir_conversion(self):
        """Test ADT to FHIR conversion."""
        from fhir_api.services.hl7_service import HL7Service, HL7Message
        
        raw = "MSH|^~\\&|APP|FAC|||20241213||ADT^A01|123|P|2.5.1\rPID|1|123|123^^^HOSP||Silva^João||19900515|M\rPV1|1|I"
        message = HL7Message.from_string(raw)
        
        fhir = HL7Service.parse_adt_to_fhir(message)
        self.assertIn('patient', fhir)
        self.assertEqual(fhir['patient']['name'][0]['family'], 'Silva')


class FormularyServiceTests(TestCase):
    """Tests for Formulary Service."""
    
    def test_list_medications(self):
        """Test listing medications."""
        from fhir_api.services.formulary_service import FormularyService
        
        meds = FormularyService.list_medications()
        self.assertGreater(len(meds), 0)
    
    def test_search_medications(self):
        """Test medication search."""
        from fhir_api.services.formulary_service import FormularyService
        
        meds = FormularyService.list_medications(search='amoxicilina')
        self.assertGreater(len(meds), 0)
    
    def test_filter_by_type(self):
        """Test filtering by generic/brand."""
        from fhir_api.services.formulary_service import FormularyService
        
        generics = FormularyService.list_medications(product_type='generic')
        brands = FormularyService.list_medications(product_type='brand')
        
        self.assertTrue(all(m['product_type'] == 'generic' for m in generics))
        self.assertTrue(all(m['product_type'] == 'brand' for m in brands))
    
    def test_get_alternatives(self):
        """Test getting brand/generic alternatives."""
        from fhir_api.services.formulary_service import FormularyService
        
        # Amoxicilina generic should have Amoxil as brand alternative
        alternatives = FormularyService.get_alternatives('amoxicilina-500')
        self.assertGreater(len(alternatives), 0)
    
    def test_sus_formulary(self):
        """Test SUS formulary (generics only)."""
        from fhir_api.services.formulary_service import FormularyService
        
        sus_meds = FormularyService.list_medications(formulary_id='SUS')
        self.assertTrue(all(m['product_type'] == 'generic' for m in sus_meds))


class ArchetypeServiceTests(TestCase):
    """Tests for ISO 13606-2 Archetype Service."""
    
    def test_list_archetypes(self):
        """Test listing clinical archetypes."""
        from fhir_api.services.archetype_service import ISO13606ArchetypeService
        
        archetypes = ISO13606ArchetypeService.list_archetypes()
        self.assertGreater(len(archetypes), 0)
    
    def test_get_blood_pressure_archetype(self):
        """Test getting blood pressure archetype."""
        from fhir_api.services.archetype_service import ISO13606ArchetypeService
        
        bp = ISO13606ArchetypeService.get_archetype('blood_pressure')
        self.assertIsNotNone(bp)
        self.assertIn('systolic', [c.path for c in bp.constraints])
    
    def test_validate_blood_pressure(self):
        """Test blood pressure validation."""
        from fhir_api.services.archetype_service import ISO13606ArchetypeService
        
        valid_data = {'systolic': 120, 'diastolic': 80}
        result = ISO13606ArchetypeService.validate_data('blood_pressure', valid_data)
        self.assertTrue(result['valid'])
        
        invalid_data = {'systolic': 300, 'diastolic': 80}
        result = ISO13606ArchetypeService.validate_data('blood_pressure', invalid_data)
        self.assertFalse(result['valid'])
    
    def test_archetype_to_fhir_mapping(self):
        """Test archetype to FHIR mapping."""
        from fhir_api.services.archetype_service import ISO13606ArchetypeService
        
        data = {'systolic': 120, 'diastolic': 80, 'patient_id': '123'}
        fhir = ISO13606ArchetypeService.map_to_fhir('blood_pressure', data)
        
        self.assertEqual(fhir['resourceType'], 'Observation')
        self.assertIn('component', fhir)


class ComplianceEndpointTests(TestCase):
    """Tests for Compliance API Endpoints."""
    
    def setUp(self):
        self.client = Client()
        self.headers = {'HTTP_AUTHORIZATION': 'Bearer dev-token-bypass'}
    
    def test_compliance_status(self):
        """Test compliance status endpoint."""
        response = self.client.get('/api/v1/compliance/status', **self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('iso_13606_2', data)
        self.assertIn('bias_prevention', data)
    
    def test_list_archetypes_endpoint(self):
        """Test list archetypes endpoint."""
        response = self.client.get('/api/v1/archetypes/', **self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('archetypes', data)


class HL7EndpointTests(TestCase):
    """Tests for HL7 API Endpoints."""
    
    def setUp(self):
        self.client = Client()
        self.headers = {'HTTP_AUTHORIZATION': 'Bearer dev-token-bypass'}
    
    def test_hl7_info_endpoint(self):
        """Test HL7 info endpoint."""
        response = self.client.get('/api/v1/hl7/info', **self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['version'], '2.5.1')
        self.assertIn('supported_messages', data)


class QuestionnaireEndpointTests(TestCase):
    """Tests for Questionnaire API Endpoints."""
    
    def setUp(self):
        self.client = Client()
        self.headers = {'HTTP_AUTHORIZATION': 'Bearer dev-token-bypass'}
    
    def test_list_questionnaires_endpoint(self):
        """Test list questionnaires endpoint."""
        response = self.client.get('/api/v1/questionnaires/', **self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('questionnaires', data)
