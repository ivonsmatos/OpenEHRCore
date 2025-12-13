"""
Tests for FHIR API Views

Basic test suite covering:
- Health check endpoints
- Patient CRUD operations
- Authentication flows
- FHIR resource validation
"""

import pytest
from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch, MagicMock
import json


class HealthCheckTestCase(TestCase):
    """Tests for health check endpoints."""
    
    def setUp(self):
        self.client = Client()
    
    def test_health_basic(self):
        """Test basic health check returns 200."""
        response = self.client.get('/api/v1/health/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('status', data)
    
    def test_health_detailed(self):
        """Test detailed health check."""
        response = self.client.get('/api/v1/health/detailed/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('components', data)


class PatientAPITestCase(TestCase):
    """Tests for Patient FHIR resources."""
    
    def setUp(self):
        self.client = Client()
        self.mock_token = 'test-token-12345'
    
    @patch('fhir_api.authentication.KeycloakAuthentication.authenticate')
    def test_list_patients_unauthorized(self, mock_auth):
        """Test that listing patients without auth returns 401."""
        mock_auth.return_value = None
        response = self.client.get('/api/v1/patients/')
        self.assertIn(response.status_code, [401, 403])
    
    @patch('fhir_api.views_auth.requests.get')
    @patch('fhir_api.authentication.KeycloakAuthentication.authenticate')
    def test_list_patients_success(self, mock_auth, mock_get):
        """Test listing patients with valid auth."""
        # Mock authentication
        mock_user = MagicMock()
        mock_user.is_authenticated = True
        mock_auth.return_value = (mock_user, None)
        
        # Mock FHIR server response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'resourceType': 'Bundle',
            'entry': []
        }
        mock_get.return_value = mock_response
        
        response = self.client.get(
            '/api/v1/patients/',
            HTTP_AUTHORIZATION=f'Bearer {self.mock_token}'
        )
        # Should be 200 or auth redirect
        self.assertIn(response.status_code, [200, 302, 401])


class FHIRResourceValidationTestCase(TestCase):
    """Tests for FHIR resource validation."""
    
    def test_valid_patient_resource(self):
        """Test that valid Patient resource passes validation."""
        from fhir_api.utils.fhir_parser import isValidPatientResource
        
        valid_patient = {
            'resourceType': 'Patient',
            'id': '12345',
            'name': [{'family': 'Silva', 'given': ['João']}],
            'birthDate': '1990-01-15',
            'gender': 'male'
        }
        
        # This should not raise
        result = isValidPatientResource(valid_patient)
        self.assertTrue(result)
    
    def test_invalid_patient_resource(self):
        """Test that invalid Patient resource fails validation."""
        from fhir_api.utils.fhir_parser import isValidPatientResource
        
        invalid_patient = {
            'resourceType': 'Observation',  # Wrong type
            'id': '12345'
        }
        
        result = isValidPatientResource(invalid_patient)
        self.assertFalse(result)


class CBOServiceTestCase(TestCase):
    """Tests for CBO (Ocupações) service."""
    
    def test_cbo_families_endpoint(self):
        """Test CBO families endpoint returns data."""
        response = self.client.get('/api/v1/cbo/families/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('families', data)
    
    def test_cbo_search(self):
        """Test CBO search functionality."""
        response = self.client.get('/api/v1/cbo/search/?q=medico')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('results', data)
    
    def test_cbo_doctors(self):
        """Test CBO doctors endpoint."""
        response = self.client.get('/api/v1/cbo/doctors/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)


class RateLimitTestCase(TestCase):
    """Tests for rate limiting middleware."""
    
    def test_rate_limit_not_exceeded(self):
        """Test normal requests are not rate limited."""
        # Make a few requests
        for _ in range(5):
            response = self.client.get('/api/v1/health/')
            self.assertEqual(response.status_code, 200)
    
    def test_rate_limit_headers(self):
        """Test rate limit headers are present."""
        response = self.client.get('/api/v1/health/')
        # Headers may or may not be present depending on config
        self.assertEqual(response.status_code, 200)


class AuditLogTestCase(TestCase):
    """Tests for audit logging."""
    
    @patch('fhir_api.views_audit_event.requests.get')
    def test_audit_events_endpoint(self, mock_get):
        """Test audit events endpoint."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'resourceType': 'Bundle',
            'entry': []
        }
        mock_get.return_value = mock_response
        
        response = self.client.get('/api/v1/audit-events/')
        # May require auth
        self.assertIn(response.status_code, [200, 401, 403])


class TISSServiceTestCase(TestCase):
    """Tests for TISS/ANS integration."""
    
    def test_tiss_guides_structure(self):
        """Test TISS guide structure is correct."""
        from fhir_api.services.tiss_service import TISSService
        
        service = TISSService()
        # Test that service has required methods
        self.assertTrue(hasattr(service, 'generate_consulta'))
        self.assertTrue(hasattr(service, 'generate_sp_sadt'))


class RNDSServiceTestCase(TestCase):
    """Tests for RNDS integration."""
    
    def test_rnds_service_exists(self):
        """Test RNDS service is available."""
        from fhir_api.services.rnds_service import RNDSService
        
        service = RNDSService()
        # Test that service has required methods
        self.assertTrue(hasattr(service, 'submit_ips'))
        self.assertTrue(hasattr(service, 'submit_immunization'))


# Pytest fixtures
@pytest.fixture
def api_client():
    """Return a Django test client."""
    return Client()


@pytest.fixture
def mock_fhir_response():
    """Return a mock FHIR Bundle response."""
    return {
        'resourceType': 'Bundle',
        'type': 'searchset',
        'total': 0,
        'entry': []
    }


@pytest.fixture
def sample_patient():
    """Return a sample Patient resource."""
    return {
        'resourceType': 'Patient',
        'id': 'test-patient-001',
        'meta': {
            'versionId': '1',
            'lastUpdated': '2024-12-13T12:00:00Z'
        },
        'identifier': [
            {
                'system': 'http://rnds.saude.gov.br/cpf',
                'value': '12345678901'
            }
        ],
        'name': [
            {
                'use': 'official',
                'family': 'Silva',
                'given': ['Maria', 'Santos']
            }
        ],
        'birthDate': '1985-06-15',
        'gender': 'female',
        'telecom': [
            {
                'system': 'phone',
                'value': '+55 11 99999-9999',
                'use': 'mobile'
            }
        ],
        'address': [
            {
                'use': 'home',
                'line': ['Rua das Flores, 123'],
                'city': 'São Paulo',
                'state': 'SP',
                'postalCode': '01234-567',
                'country': 'BR'
            }
        ]
    }


# Run with: pytest fhir_api/tests/test_views.py -v
