"""
Sprint 23: API Integration Tests for Bulk Data Endpoints

Tests for FHIR Bulk Export/Import REST API endpoints.
"""

import pytest
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock


@pytest.mark.django_db
class TestBulkExportAPI:
    """Integration tests for bulk export API endpoints."""
    
    @pytest.fixture
    def auth_client(self):
        """Authenticated API client."""
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Bearer dev-token-bypass')
        return client
    
    def test_export_patient_level(self, auth_client):
        """Test initiating patient-level export."""
        response = auth_client.post('/api/v1/export/Patient/', {
            "patient_ids": ["patient-1", "patient-2"]
        }, format='json')
        
        assert response.status_code == status.HTTP_202_ACCEPTED
        assert "job_id" in response.data
        assert response.data["status"] == "pending"
        assert "Content-Location" in response
    
    def test_export_patient_level_with_types(self, auth_client):
        """Test patient export with custom resource types."""
        response = auth_client.post('/api/v1/export/Patient/', {
            "resource_types": ["Patient", "Observation"]
        }, format='json')
        
        assert response.status_code == status.HTTP_202_ACCEPTED
    
    def test_export_system_level(self, auth_client):
        """Test initiating system-level export."""
        response = auth_client.post('/api/v1/export/System/', {}, format='json')
        
        assert response.status_code == status.HTTP_202_ACCEPTED
        assert "job_id" in response.data
    
    def test_export_group_level(self, auth_client):
        """Test initiating group-level export."""
        response = auth_client.post('/api/v1/export/Group/group-123/', {}, format='json')
        
        assert response.status_code == status.HTTP_202_ACCEPTED
    
    def test_get_export_status(self, auth_client):
        """Test getting export job status."""
        # First create a job
        create_response = auth_client.post('/api/v1/export/Patient/', {}, format='json')
        job_id = create_response.data["job_id"]
        
        # Then get status
        response = auth_client.get(f'/api/v1/export/status/{job_id}/')
        
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_202_ACCEPTED]
        assert "status" in response.data
    
    def test_get_nonexistent_export_status(self, auth_client):
        """Test getting status of non-existent job."""
        response = auth_client.get('/api/v1/export/status/nonexistent-id/')
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_cancel_export(self, auth_client):
        """Test cancelling an export job."""
        # Create a job
        create_response = auth_client.post('/api/v1/export/Patient/', {}, format='json')
        job_id = create_response.data["job_id"]
        
        # Cancel it
        response = auth_client.delete(f'/api/v1/export/status/{job_id}/')
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_list_exports(self, auth_client):
        """Test listing export jobs."""
        # Create a job first
        auth_client.post('/api/v1/export/Patient/', {}, format='json')
        
        response = auth_client.get('/api/v1/export/jobs/')
        
        assert response.status_code == status.HTTP_200_OK
        assert "jobs" in response.data
        assert isinstance(response.data["jobs"], list)
    
    def test_export_with_since_filter(self, auth_client):
        """Test export with _since parameter."""
        response = auth_client.post('/api/v1/export/Patient/', {
            "_since": "2024-01-01T00:00:00Z"
        }, format='json')
        
        assert response.status_code == status.HTTP_202_ACCEPTED
    
    def test_export_with_invalid_types(self, auth_client):
        """Test export with invalid resource types."""
        response = auth_client.post('/api/v1/export/Patient/', {
            "resource_types": ["InvalidType"]
        }, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestBulkImportAPI:
    """Integration tests for bulk import API endpoints."""
    
    @pytest.fixture
    def auth_client(self):
        """Authenticated API client."""
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Bearer dev-token-bypass')
        return client
    
    def test_import_bulk(self, auth_client):
        """Test initiating bulk import."""
        response = auth_client.post('/api/v1/import/', {
            "files": [
                {
                    "resource_type": "Patient",
                    "content": '{"resourceType":"Patient","name":[{"family":"Test"}]}'
                }
            ]
        }, format='json')
        
        assert response.status_code == status.HTTP_202_ACCEPTED
        assert "job_id" in response.data
    
    def test_import_without_files(self, auth_client):
        """Test import without files should fail."""
        response = auth_client.post('/api/v1/import/', {
            "files": []
        }, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_get_import_status(self, auth_client):
        """Test getting import job status."""
        # Create import job
        create_response = auth_client.post('/api/v1/import/', {
            "files": [{"resource_type": "Patient", "content": "{}"}]
        }, format='json')
        job_id = create_response.data["job_id"]
        
        # Get status
        response = auth_client.get(f'/api/v1/import/status/{job_id}/')
        
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_202_ACCEPTED]


@pytest.mark.django_db
class TestSMARTScopesAPI:
    """Integration tests for SMART on FHIR scope endpoints."""
    
    @pytest.fixture
    def auth_client(self):
        """Authenticated API client."""
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Bearer dev-token-bypass')
        return client
    
    def test_list_smart_scopes(self, auth_client):
        """Test listing all SMART scopes."""
        response = auth_client.get('/api/v1/smart/scopes/')
        
        assert response.status_code == status.HTTP_200_OK
        assert "scopes" in response.data
        assert len(response.data["scopes"]) > 0
    
    def test_validate_smart_scopes_valid(self, auth_client):
        """Test validating valid scopes."""
        response = auth_client.post('/api/v1/smart/scopes/validate/', {
            "scopes": ["patient/*.read", "user/Patient.write"]
        }, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data["all_valid"] is True
    
    def test_validate_smart_scopes_invalid(self, auth_client):
        """Test validating with invalid scopes."""
        response = auth_client.post('/api/v1/smart/scopes/validate/', {
            "scopes": ["invalid_scope"]
        }, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data["all_valid"] is False
    
    def test_validate_smart_scopes_empty(self, auth_client):
        """Test validating with no scopes."""
        response = auth_client.post('/api/v1/smart/scopes/validate/', {
            "scopes": []
        }, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_check_smart_access_granted(self, auth_client):
        """Test access check when granted."""
        response = auth_client.post('/api/v1/smart/access/check/', {
            "granted_scopes": ["patient/*.read"],
            "resource_type": "Observation",
            "action": "read",
            "context": "patient"
        }, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data["granted"] is True
    
    def test_check_smart_access_denied(self, auth_client):
        """Test access check when denied."""
        response = auth_client.post('/api/v1/smart/access/check/', {
            "granted_scopes": ["patient/*.read"],
            "resource_type": "Patient",
            "action": "write",
            "context": "patient"
        }, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data["granted"] is False
    
    def test_check_smart_access_missing_params(self, auth_client):
        """Test access check with missing parameters."""
        response = auth_client.post('/api/v1/smart/access/check/', {
            "granted_scopes": ["patient/*.read"]
        }, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestTerminologyAPI:
    """Integration tests for terminology API endpoints."""
    
    @pytest.fixture
    def auth_client(self):
        """Authenticated API client."""
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Bearer dev-token-bypass')
        return client
    
    def test_search_icd10(self, auth_client):
        """Test searching ICD-10 codes."""
        response = auth_client.get('/api/v1/terminology/icd10/search/', {'q': 'diabetes'})
        
        assert response.status_code == status.HTTP_200_OK
        assert "results" in response.data
    
    def test_search_icd10_missing_query(self, auth_client):
        """Test ICD-10 search without query."""
        response = auth_client.get('/api/v1/terminology/icd10/search/')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_validate_icd10(self, auth_client):
        """Test validating ICD-10 code."""
        response = auth_client.get('/api/v1/terminology/icd10/I10/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data["valid"] is True
    
    def test_validate_icd10_invalid(self, auth_client):
        """Test validating invalid ICD-10 code."""
        response = auth_client.get('/api/v1/terminology/icd10/INVALID/')
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_search_tuss(self, auth_client):
        """Test searching TUSS codes."""
        response = auth_client.get('/api/v1/terminology/tuss/search/', {'q': 'consulta'})
        
        assert response.status_code == status.HTTP_200_OK
        assert "results" in response.data
    
    def test_list_tuss_by_type(self, auth_client):
        """Test listing TUSS by type."""
        response = auth_client.get('/api/v1/terminology/tuss/type/exame/')
        
        assert response.status_code == status.HTTP_200_OK
        assert "results" in response.data
    
    def test_list_tuss_invalid_type(self, auth_client):
        """Test listing TUSS with invalid type."""
        response = auth_client.get('/api/v1/terminology/tuss/type/invalid/')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_map_icd10_to_snomed(self, auth_client):
        """Test mapping ICD-10 to SNOMED."""
        response = auth_client.get('/api/v1/terminology/map/icd10-to-snomed/I10/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data["mapped"] is True
    
    def test_map_snomed_to_icd10(self, auth_client):
        """Test mapping SNOMED to ICD-10."""
        response = auth_client.get('/api/v1/terminology/map/snomed-to-icd10/38341003/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data["mapped"] is True
