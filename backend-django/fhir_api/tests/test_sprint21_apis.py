"""
Tests for Sprint 21 APIs: Organization and Procedure

Testes unitários para as novas APIs FHIR R4:
- Organization (validação CNPJ, hierarquia, CNES)
- Procedure (códigos TUSS, categorias, performer)
- MedicationRequest (códigos ANVISA, Timing)
"""
import pytest
from unittest.mock import patch, MagicMock
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status


class TestOrganizationAPI(TestCase):
    """Testes para a API de Organization"""
    
    def setUp(self):
        self.client = APIClient()
        # Mock authentication
        self.client.credentials(HTTP_AUTHORIZATION='Bearer test-token')
    
    @patch('fhir_api.views_organization.FHIRService')
    @patch('fhir_api.auth.KeycloakAuthentication.authenticate')
    def test_list_organizations(self, mock_auth, mock_fhir):
        """Deve listar organizações"""
        mock_auth.return_value = (MagicMock(), None)
        mock_fhir.return_value.search_resources.return_value = [
            {
                'id': 'org-1',
                'resourceType': 'Organization',
                'name': 'Hospital Central',
                'active': True
            }
        ]
        
        response = self.client.get('/api/v1/organizations/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
    
    @patch('fhir_api.views_organization.FHIRService')
    @patch('fhir_api.auth.KeycloakAuthentication.authenticate')
    def test_create_organization_valid_cnpj(self, mock_auth, mock_fhir):
        """Deve criar organização com CNPJ válido"""
        mock_auth.return_value = (MagicMock(), None)
        mock_fhir.return_value.create_resource.return_value = {
            'id': 'org-new',
            'resourceType': 'Organization'
        }
        
        data = {
            'name': 'Clínica Teste',
            'type': 'prov',
            'cnpj': '11222333000181',  # CNPJ válido
            'cnes': '1234567',
            'phone': '11999999999',
            'email': 'contato@clinica.com.br'
        }
        
        response = self.client.post('/api/v1/organizations/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    @patch('fhir_api.views_organization.FHIRService')
    @patch('fhir_api.auth.KeycloakAuthentication.authenticate')
    def test_create_organization_invalid_cnpj(self, mock_auth, mock_fhir):
        """Deve rejeitar organização com CNPJ inválido"""
        mock_auth.return_value = (MagicMock(), None)
        
        data = {
            'name': 'Clínica Teste',
            'cnpj': '12345678901234'  # CNPJ inválido
        }
        
        response = self.client.post('/api/v1/organizations/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('CNPJ', str(response.data))
    
    @patch('fhir_api.views_organization.FHIRService')
    @patch('fhir_api.auth.KeycloakAuthentication.authenticate')
    def test_get_organization_hierarchy(self, mock_auth, mock_fhir):
        """Deve retornar hierarquia organizacional"""
        mock_auth.return_value = (MagicMock(), None)
        mock_fhir.return_value.search_resources.return_value = [
            {
                'id': 'org-1',
                'name': 'Hospital',
                'partOf': None
            }
        ]
        
        response = self.client.get('/api/v1/organizations/org-1/hierarchy/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('organization', response.data)


class TestProcedureAPI(TestCase):
    """Testes para a API de Procedure"""
    
    def setUp(self):
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Bearer test-token')
    
    @patch('fhir_api.views_procedure.FHIRService')
    @patch('fhir_api.auth.KeycloakAuthentication.authenticate')
    def test_create_procedure(self, mock_auth, mock_fhir):
        """Deve criar procedimento com código TUSS"""
        mock_auth.return_value = (MagicMock(), None)
        mock_fhir.return_value.create_resource.return_value = {
            'id': 'proc-1',
            'resourceType': 'Procedure'
        }
        
        data = {
            'patient_id': 'patient-1',
            'code': '10101012',  # Código TUSS
            'display': 'Consulta em consultório',
            'category': 'diagnostic',
            'status': 'completed',
            'performed_date_time': '2024-01-15T10:30:00Z'
        }
        
        response = self.client.post('/api/v1/procedures/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    @patch('fhir_api.views_procedure.FHIRService')
    @patch('fhir_api.auth.KeycloakAuthentication.authenticate')
    def test_create_procedure_invalid_status(self, mock_auth, mock_fhir):
        """Deve rejeitar status inválido"""
        mock_auth.return_value = (MagicMock(), None)
        
        data = {
            'patient_id': 'patient-1',
            'code': '10101012',
            'display': 'Consulta',
            'status': 'invalid-status'  # Status inválido
        }
        
        response = self.client.post('/api/v1/procedures/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    @patch('fhir_api.views_procedure.FHIRService')
    @patch('fhir_api.auth.KeycloakAuthentication.authenticate')
    def test_list_patient_procedures(self, mock_auth, mock_fhir):
        """Deve listar procedimentos de um paciente"""
        mock_auth.return_value = (MagicMock(), None)
        mock_fhir.return_value.search_resources.return_value = [
            {
                'id': 'proc-1',
                'resourceType': 'Procedure',
                'status': 'completed'
            }
        ]
        
        response = self.client.get('/api/v1/patients/patient-1/procedures/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class TestMedicationRequestAPI(TestCase):
    """Testes para a API de MedicationRequest aprimorada"""
    
    def setUp(self):
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Bearer test-token')
    
    @patch('fhir_api.views_medication.FHIRService')
    @patch('fhir_api.auth.KeycloakAuthentication.authenticate')
    def test_create_medication_request_anvisa(self, mock_auth, mock_fhir):
        """Deve criar prescrição com código ANVISA"""
        mock_auth.return_value = (MagicMock(), None)
        mock_fhir.return_value.create_resource.return_value = {
            'id': 'med-1',
            'resourceType': 'MedicationRequest'
        }
        
        data = {
            'patient_id': 'patient-1',
            'medication': {
                'code': '1234567890123',  # Código ANVISA
                'code_system': 'anvisa',
                'display': 'Dipirona 500mg'
            },
            'dosage': {
                'dose_value': 1,
                'dose_unit': 'comprimido',
                'route': 'oral',
                'frequency': {'value': 8, 'unit': 'h'},
                'duration': {'value': 5, 'unit': 'd'},
                'instructions': 'Tomar após as refeições'
            },
            'dispense': {
                'quantity': 15,
                'supply_duration': 5
            },
            'validity_period': 30
        }
        
        response = self.client.post('/api/v1/medication-requests/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    @patch('fhir_api.views_medication.FHIRService')
    @patch('fhir_api.auth.KeycloakAuthentication.authenticate')
    def test_create_medication_request_without_patient(self, mock_auth, mock_fhir):
        """Deve rejeitar prescrição sem paciente"""
        mock_auth.return_value = (MagicMock(), None)
        
        data = {
            'medication': {
                'code': '123456',
                'display': 'Medicamento'
            }
        }
        
        response = self.client.post('/api/v1/medication-requests/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    @patch('fhir_api.views_medication.FHIRService')
    @patch('fhir_api.auth.KeycloakAuthentication.authenticate')
    def test_list_patient_medications(self, mock_auth, mock_fhir):
        """Deve listar medicações de um paciente"""
        mock_auth.return_value = (MagicMock(), None)
        mock_fhir.return_value.search_resources.return_value = [
            {
                'id': 'med-1',
                'resourceType': 'MedicationRequest',
                'status': 'active'
            }
        ]
        
        response = self.client.get('/api/v1/patients/patient-1/medications/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('medications', response.data)


class TestCNPJValidation(TestCase):
    """Testes unitários para validação de CNPJ"""
    
    def test_valid_cnpj(self):
        """Deve validar CNPJ correto"""
        from fhir_api.views_organization import validate_cnpj
        
        # CNPJs válidos conhecidos
        valid_cnpjs = [
            '11222333000181',
            '11.222.333/0001-81'
        ]
        
        for cnpj in valid_cnpjs:
            self.assertTrue(validate_cnpj(cnpj), f"CNPJ {cnpj} deveria ser válido")
    
    def test_invalid_cnpj(self):
        """Deve rejeitar CNPJ inválido"""
        from fhir_api.views_organization import validate_cnpj
        
        invalid_cnpjs = [
            '12345678901234',
            '00000000000000',
            '11111111111111',
            '123',
            ''
        ]
        
        for cnpj in invalid_cnpjs:
            self.assertFalse(validate_cnpj(cnpj), f"CNPJ {cnpj} deveria ser inválido")


class TestCNPJFormatting(TestCase):
    """Testes de formatação de CNPJ"""
    
    def test_format_cnpj(self):
        """Deve formatar CNPJ corretamente"""
        from fhir_api.views_organization import format_cnpj
        
        self.assertEqual(format_cnpj('11222333000181'), '11.222.333/0001-81')
        self.assertEqual(format_cnpj('11.222.333/0001-81'), '11.222.333/0001-81')
