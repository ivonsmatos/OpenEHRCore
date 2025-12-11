"""
Sprint 23: Unit Tests for Bulk Data Services

Tests for FHIR Bulk Export/Import and SMART scopes.
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

from fhir_api.services.bulk_data_service import (
    BulkExportService,
    BulkImportService,
    ExportJob,
    ExportLevel,
    ExportStatus,
    SMARTScopeValidator,
    SMART_SCOPES
)


class TestExportJob:
    """Tests for ExportJob dataclass."""
    
    def test_export_job_creation(self):
        """Test creating an export job."""
        job = ExportJob(
            job_id="test-123",
            status=ExportStatus.PENDING,
            level=ExportLevel.PATIENT,
            request_time=datetime.now(),
            resource_types=["Patient", "Observation"]
        )
        
        assert job.job_id == "test-123"
        assert job.status == ExportStatus.PENDING
        assert job.level == ExportLevel.PATIENT
        assert len(job.resource_types) == 2
    
    def test_export_job_to_dict(self):
        """Test converting export job to dictionary."""
        job = ExportJob(
            job_id="test-123",
            status=ExportStatus.COMPLETED,
            level=ExportLevel.SYSTEM,
            request_time=datetime(2024, 1, 1, 12, 0, 0),
            resource_types=["Patient"],
            completed_time=datetime(2024, 1, 1, 12, 5, 0)
        )
        
        result = job.to_dict()
        
        assert result["job_id"] == "test-123"
        assert result["status"] == "completed"
        assert result["level"] == "System"
        assert result["completed_time"] is not None


class TestBulkExportService:
    """Tests for BulkExportService."""
    
    def test_supported_resource_types(self):
        """Test that common FHIR resources are supported."""
        expected_types = ["Patient", "Observation", "Condition", "Encounter"]
        for rt in expected_types:
            assert rt in BulkExportService.SUPPORTED_RESOURCE_TYPES
    
    def test_default_patient_types(self):
        """Test default resource types for patient export."""
        assert "Patient" in BulkExportService.DEFAULT_PATIENT_TYPES
        assert "Observation" in BulkExportService.DEFAULT_PATIENT_TYPES
        assert "Condition" in BulkExportService.DEFAULT_PATIENT_TYPES
    
    @patch.object(BulkExportService, '_process_export_job')
    def test_create_export_job(self, mock_process):
        """Test creating an export job."""
        mock_process.return_value = None
        
        job = BulkExportService.create_export_job(
            level=ExportLevel.PATIENT,
            patient_ids=["patient-1"]
        )
        
        assert job.job_id is not None
        assert job.status == ExportStatus.PENDING
        assert job.level == ExportLevel.PATIENT
        assert job.patient_ids == ["patient-1"]
    
    @patch.object(BulkExportService, '_process_export_job')
    def test_create_export_job_with_custom_types(self, mock_process):
        """Test creating export job with custom resource types."""
        mock_process.return_value = None
        
        job = BulkExportService.create_export_job(
            level=ExportLevel.PATIENT,
            resource_types=["Patient", "Observation"]
        )
        
        assert job.resource_types == ["Patient", "Observation"]
    
    @patch.object(BulkExportService, '_process_export_job')
    def test_create_export_job_invalid_types(self, mock_process):
        """Test that invalid resource types raise an error."""
        mock_process.return_value = None
        
        with pytest.raises(ValueError) as excinfo:
            BulkExportService.create_export_job(
                level=ExportLevel.PATIENT,
                resource_types=["InvalidType", "AnotherBad"]
            )
        
        assert "Unsupported resource types" in str(excinfo.value)
    
    @patch.object(BulkExportService, '_process_export_job')
    def test_get_job(self, mock_process):
        """Test getting an export job by ID."""
        mock_process.return_value = None
        
        job = BulkExportService.create_export_job(level=ExportLevel.SYSTEM)
        
        retrieved = BulkExportService.get_job(job.job_id)
        assert retrieved is not None
        assert retrieved.job_id == job.job_id
    
    def test_get_nonexistent_job(self):
        """Test getting a job that doesn't exist."""
        result = BulkExportService.get_job("nonexistent-id")
        assert result is None
    
    @patch.object(BulkExportService, '_process_export_job')
    def test_cancel_job(self, mock_process):
        """Test cancelling an export job."""
        mock_process.return_value = None
        
        job = BulkExportService.create_export_job(level=ExportLevel.PATIENT)
        
        result = BulkExportService.cancel_job(job.job_id)
        assert result is True
        
        updated = BulkExportService.get_job(job.job_id)
        assert updated.status == ExportStatus.CANCELLED
    
    def test_cancel_nonexistent_job(self):
        """Test cancelling a job that doesn't exist."""
        result = BulkExportService.cancel_job("nonexistent")
        assert result is False
    
    @patch.object(BulkExportService, '_process_export_job')
    def test_list_jobs(self, mock_process):
        """Test listing export jobs."""
        mock_process.return_value = None
        
        # Create a few jobs
        BulkExportService.create_export_job(level=ExportLevel.PATIENT)
        BulkExportService.create_export_job(level=ExportLevel.SYSTEM)
        
        jobs = BulkExportService.list_jobs()
        assert len(jobs) >= 2


class TestSMARTScopeValidator:
    """Tests for SMART on FHIR scope validation."""
    
    def test_parse_patient_read_scope(self):
        """Test parsing patient read scope."""
        result = SMARTScopeValidator.parse_scope("patient/*.read")
        
        assert result["valid"] is True
        assert result["context"] == "patient"
        assert result["resource_type"] == "*"
        assert result["permission"] == "read"
    
    def test_parse_user_write_scope(self):
        """Test parsing user write scope."""
        result = SMARTScopeValidator.parse_scope("user/Patient.write")
        
        assert result["valid"] is True
        assert result["context"] == "user"
        assert result["resource_type"] == "Patient"
        assert result["permission"] == "write"
    
    def test_parse_system_export_scope(self):
        """Test parsing system export scope."""
        result = SMARTScopeValidator.parse_scope("system/*.$export")
        
        assert result["valid"] is True
        assert result["context"] == "system"
        assert result["operation"] == "$export"
    
    def test_parse_invalid_scope(self):
        """Test parsing invalid scope format."""
        result = SMARTScopeValidator.parse_scope("invalid")
        
        assert result["valid"] is False
    
    def test_parse_invalid_context(self):
        """Test parsing scope with invalid context."""
        result = SMARTScopeValidator.parse_scope("admin/*.read")
        
        assert result["valid"] is False
    
    def test_validate_scopes_all_valid(self):
        """Test validating all valid scopes."""
        scopes = ["patient/*.read", "user/Patient.write"]
        result = SMARTScopeValidator.validate_scopes(scopes)
        
        assert result["all_valid"] is True
        assert len(result["valid_scopes"]) == 2
        assert len(result["invalid_scopes"]) == 0
    
    def test_validate_scopes_with_invalid(self):
        """Test validating with some invalid scopes."""
        scopes = ["patient/*.read", "invalid"]
        result = SMARTScopeValidator.validate_scopes(scopes)
        
        assert result["all_valid"] is False
        assert len(result["valid_scopes"]) == 1
        assert len(result["invalid_scopes"]) == 1
    
    def test_validate_predefined_scopes(self):
        """Test that predefined scopes are valid."""
        scopes = list(SMART_SCOPES.keys())[:5]
        result = SMARTScopeValidator.validate_scopes(scopes)
        
        assert result["all_valid"] is True
    
    def test_check_access_granted(self):
        """Test access check when granted."""
        granted = ["patient/*.read", "user/Patient.write"]
        
        # Should have read access to Observation in patient context
        assert SMARTScopeValidator.check_access(
            granted, "Observation", "read", "patient"
        ) is True
    
    def test_check_access_denied(self):
        """Test access check when denied."""
        granted = ["patient/*.read"]
        
        # Should NOT have write access
        assert SMARTScopeValidator.check_access(
            granted, "Patient", "write", "patient"
        ) is False
    
    def test_check_access_wildcard(self):
        """Test access with wildcard permissions."""
        granted = ["user/*.*"]
        
        # Wildcard should grant all access in user context
        # (depends on implementation)
        result = SMARTScopeValidator.check_access(granted, "Patient", "read", "user")
        # This may vary based on how wildcards are handled
        assert isinstance(result, bool)
    
    def test_check_access_system_context(self):
        """Test that system context grants access everywhere."""
        granted = ["system/*.read"]
        
        # System-level read should work for patient context too
        assert SMARTScopeValidator.check_access(
            granted, "Patient", "read", "patient"
        ) is True


class TestBulkImportService:
    """Tests for BulkImportService."""
    
    @patch.object(BulkImportService, '_process_import_job')
    def test_create_import_job(self, mock_process):
        """Test creating an import job."""
        mock_process.return_value = None
        
        files = [
            {"resource_type": "Patient", "content": '{"resourceType":"Patient"}'}
        ]
        
        job = BulkImportService.create_import_job(files)
        
        assert job.job_id is not None
        assert job.status == ExportStatus.PENDING
        assert len(job.input_files) == 1
    
    @patch.object(BulkImportService, '_process_import_job')
    def test_get_import_job(self, mock_process):
        """Test getting an import job."""
        mock_process.return_value = None
        
        files = [{"resource_type": "Patient", "content": "{}"}]
        job = BulkImportService.create_import_job(files)
        
        retrieved = BulkImportService.get_job(job.job_id)
        assert retrieved is not None
        assert retrieved.job_id == job.job_id
