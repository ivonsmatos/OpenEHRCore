"""
Sprint 20: FHIR Search Endpoints - Automated Tests

Tests for:
- Encounter search (patient, date, status)
- Observation search (patient, code, date)
- Condition search (patient, code, clinical-status)
- Practitioner search (name, identifier, specialty)
"""

import pytest
from unittest.mock import patch, MagicMock
from rest_framework.test import APIRequestFactory
from rest_framework import status

# Import views
from fhir_api.views_search import search_encounters, search_observations, search_conditions
from fhir_api.views_practitioners import list_practitioners


@pytest.fixture
def api_factory():
    return APIRequestFactory()


@pytest.fixture
def mock_user():
    user = MagicMock()
    user.is_authenticated = True
    return user


@pytest.fixture
def mock_fhir_service():
    with patch('fhir_api.views_search.FHIRService') as mock_fhir, \
         patch('fhir_api.views_search.KeycloakAuthentication.authenticate', return_value=(MagicMock(), None)), \
         patch('fhir_api.views_search.IsAuthenticated.has_permission', return_value=True):
        yield mock_fhir


@pytest.fixture
def mock_practitioner_fhir_service():
    with patch('fhir_api.views_practitioners.FHIRService') as mock_fhir, \
         patch('fhir_api.views_practitioners.KeycloakAuthentication.authenticate', return_value=(MagicMock(), None)), \
         patch('fhir_api.views_practitioners.IsAuthenticated.has_permission', return_value=True):
        yield mock_fhir


class TestEncounterSearch:
    """Test cases for Encounter search endpoint"""
    
    def test_search_encounters_by_patient(self, api_factory, mock_user, mock_fhir_service):
        """Test searching encounters by patient ID"""
        # Setup mock
        mock_instance = mock_fhir_service.return_value
        mock_instance.search_resources.return_value = [
            {"id": "enc-1", "resourceType": "Encounter", "status": "finished"},
            {"id": "enc-2", "resourceType": "Encounter", "status": "in-progress"}
        ]
        
        # Create request
        request = api_factory.get('/api/v1/encounters/search/', {'patient': 'patient-123'})
        request.user = mock_user
        
        # Execute
        response = search_encounters(request)
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data['total'] == 2
        mock_instance.search_resources.assert_called_once()
        call_args = mock_instance.search_resources.call_args
        assert call_args[0][0] == 'Encounter'
        assert 'patient' in call_args[0][1]
    
    def test_search_encounters_by_status(self, api_factory, mock_user, mock_fhir_service):
        """Test searching encounters by status"""
        mock_instance = mock_fhir_service.return_value
        mock_instance.search_resources.return_value = [
            {"id": "enc-1", "resourceType": "Encounter", "status": "in-progress"}
        ]
        
        request = api_factory.get('/api/v1/encounters/search/', {'status': 'in-progress'})
        request.user = mock_user
        
        response = search_encounters(request)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['total'] == 1
    
    def test_search_encounters_invalid_status(self, api_factory, mock_user, mock_fhir_service):
        """Test that invalid status returns 400"""
        request = api_factory.get('/api/v1/encounters/search/', {'status': 'invalid-status'})
        request.user = mock_user
        
        response = search_encounters(request)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data
    
    def test_search_encounters_by_date_range(self, api_factory, mock_user, mock_fhir_service):
        """Test searching encounters by date range"""
        mock_instance = mock_fhir_service.return_value
        mock_instance.search_resources.return_value = []
        
        request = api_factory.get('/api/v1/encounters/search/', {'date': 'ge2024-01-01'})
        request.user = mock_user
        
        response = search_encounters(request)
        
        assert response.status_code == status.HTTP_200_OK
        call_args = mock_instance.search_resources.call_args
        assert 'date' in call_args[0][1]
    
    def test_search_encounters_pagination(self, api_factory, mock_user, mock_fhir_service):
        """Test pagination parameters"""
        mock_instance = mock_fhir_service.return_value
        mock_instance.search_resources.return_value = []
        
        request = api_factory.get('/api/v1/encounters/search/', {'_count': '10', '_getpagesoffset': '20'})
        request.user = mock_user
        
        response = search_encounters(request)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 10
        assert response.data['offset'] == 20


class TestObservationSearch:
    """Test cases for Observation search endpoint"""
    
    def test_search_observations_by_patient(self, api_factory, mock_user, mock_fhir_service):
        """Test searching observations by patient ID"""
        mock_instance = mock_fhir_service.return_value
        mock_instance.search_resources.return_value = [
            {"id": "obs-1", "resourceType": "Observation", "code": {"text": "Blood Pressure"}}
        ]
        
        request = api_factory.get('/api/v1/observations/search/', {'patient': 'patient-123'})
        request.user = mock_user
        
        response = search_observations(request)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['total'] == 1
    
    def test_search_observations_by_code(self, api_factory, mock_user, mock_fhir_service):
        """Test searching observations by LOINC code"""
        mock_instance = mock_fhir_service.return_value
        mock_instance.search_resources.return_value = []
        
        request = api_factory.get('/api/v1/observations/search/', {'code': '8480-6'})
        request.user = mock_user
        
        response = search_observations(request)
        
        assert response.status_code == status.HTTP_200_OK
        call_args = mock_instance.search_resources.call_args
        assert call_args[0][1]['code'] == '8480-6'
    
    def test_search_observations_by_category(self, api_factory, mock_user, mock_fhir_service):
        """Test searching observations by category"""
        mock_instance = mock_fhir_service.return_value
        mock_instance.search_resources.return_value = []
        
        request = api_factory.get('/api/v1/observations/search/', {'category': 'vital-signs'})
        request.user = mock_user
        
        response = search_observations(request)
        
        assert response.status_code == status.HTTP_200_OK
        call_args = mock_instance.search_resources.call_args
        assert call_args[0][1]['category'] == 'vital-signs'


class TestConditionSearch:
    """Test cases for Condition search endpoint"""
    
    def test_search_conditions_by_patient(self, api_factory, mock_user, mock_fhir_service):
        """Test searching conditions by patient ID"""
        mock_instance = mock_fhir_service.return_value
        mock_instance.search_resources.return_value = [
            {"id": "cond-1", "resourceType": "Condition", "clinicalStatus": {"coding": [{"code": "active"}]}}
        ]
        
        request = api_factory.get('/api/v1/conditions/search/', {'patient': 'patient-123'})
        request.user = mock_user
        
        response = search_conditions(request)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['total'] == 1
    
    def test_search_conditions_by_clinical_status(self, api_factory, mock_user, mock_fhir_service):
        """Test searching conditions by clinical status"""
        mock_instance = mock_fhir_service.return_value
        mock_instance.search_resources.return_value = []
        
        request = api_factory.get('/api/v1/conditions/search/', {'clinical-status': 'active'})
        request.user = mock_user
        
        response = search_conditions(request)
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_search_conditions_invalid_clinical_status(self, api_factory, mock_user, mock_fhir_service):
        """Test that invalid clinical-status returns 400"""
        request = api_factory.get('/api/v1/conditions/search/', {'clinical-status': 'invalid'})
        request.user = mock_user
        
        response = search_conditions(request)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_search_conditions_by_code(self, api_factory, mock_user, mock_fhir_service):
        """Test searching conditions by SNOMED CT code"""
        mock_instance = mock_fhir_service.return_value
        mock_instance.search_resources.return_value = []
        
        request = api_factory.get('/api/v1/conditions/search/', {'code': '38341003'})
        request.user = mock_user
        
        response = search_conditions(request)
        
        assert response.status_code == status.HTTP_200_OK
        call_args = mock_instance.search_resources.call_args
        assert call_args[0][1]['code'] == '38341003'


class TestPractitionerSearch:
    """Test cases for Practitioner search endpoint"""
    
    def test_search_practitioners_by_name(self, api_factory, mock_user, mock_practitioner_fhir_service):
        """Test searching practitioners by name"""
        mock_instance = mock_practitioner_fhir_service.return_value
        mock_instance.search_resources.return_value = [
            {"id": "prac-1", "resourceType": "Practitioner", "name": [{"family": "Silva"}]}
        ]
        
        request = api_factory.get('/api/v1/practitioners/list/', {'name': 'Silva'})
        request.user = mock_user
        
        response = list_practitioners(request)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['total'] == 1
    
    def test_search_practitioners_by_identifier(self, api_factory, mock_user, mock_practitioner_fhir_service):
        """Test searching practitioners by CRM identifier"""
        mock_instance = mock_practitioner_fhir_service.return_value
        mock_instance.search_resources.return_value = [
            {"id": "prac-1", "resourceType": "Practitioner", "identifier": [{"value": "CRM-SP-123456"}]}
        ]
        
        request = api_factory.get('/api/v1/practitioners/list/', {'identifier': 'CRM-SP-123456'})
        request.user = mock_user
        
        response = list_practitioners(request)
        
        assert response.status_code == status.HTTP_200_OK
        call_args = mock_instance.search_resources.call_args
        assert 'identifier' in call_args[0][1]
    
    def test_search_practitioners_by_specialty(self, api_factory, mock_user, mock_practitioner_fhir_service):
        """Test searching practitioners by specialty (via PractitionerRole)"""
        mock_instance = mock_practitioner_fhir_service.return_value
        
        # First call returns practitioners, second call returns roles
        mock_instance.search_resources.side_effect = [
            [{"id": "prac-1", "resourceType": "Practitioner"}, {"id": "prac-2", "resourceType": "Practitioner"}],
            [{"id": "role-1", "practitioner": {"reference": "Practitioner/prac-1"}}]
        ]
        
        request = api_factory.get('/api/v1/practitioners/list/', {'specialty': '394579002'})
        request.user = mock_user
        
        response = list_practitioners(request)
        
        assert response.status_code == status.HTTP_200_OK
        # Should only return prac-1 which has matching role
        assert response.data['total'] == 1
    
    def test_search_practitioners_pagination(self, api_factory, mock_user, mock_practitioner_fhir_service):
        """Test pagination parameters"""
        mock_instance = mock_practitioner_fhir_service.return_value
        mock_instance.search_resources.return_value = []
        
        request = api_factory.get('/api/v1/practitioners/list/', {'_count': '50', '_getpagesoffset': '100'})
        request.user = mock_user
        
        response = list_practitioners(request)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 50
        assert response.data['offset'] == 100
