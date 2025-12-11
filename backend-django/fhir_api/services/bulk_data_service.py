"""
Sprint 22: FHIR Bulk Data Export Service

Implements the FHIR Bulk Data Access (Flat FHIR) specification:
- $export operation at Patient, Group, and System levels
- NDJSON (Newline Delimited JSON) format
- Async processing with job status tracking
- $import operation for bulk data loading

Reference: https://hl7.org/fhir/uv/bulkdata/
"""

import json
import logging
import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass, field, asdict
import threading
from concurrent.futures import ThreadPoolExecutor

from .fhir_core import FHIRService, FHIRServiceException

logger = logging.getLogger(__name__)

# Directory for storing export files
EXPORT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'exports')
os.makedirs(EXPORT_DIR, exist_ok=True)


class ExportStatus(Enum):
    """Status of an export job."""
    PENDING = "pending"
    IN_PROGRESS = "in-progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExportLevel(Enum):
    """Level of the export operation."""
    PATIENT = "Patient"  # Single patient or group of patients
    GROUP = "Group"      # Pre-defined group
    SYSTEM = "System"    # All data in the system


@dataclass
class ExportJob:
    """Represents a bulk export job."""
    job_id: str
    status: ExportStatus
    level: ExportLevel
    request_time: datetime
    resource_types: List[str]
    patient_ids: Optional[List[str]] = None
    group_id: Optional[str] = None
    since: Optional[datetime] = None
    type_filter: Optional[str] = None
    output_files: List[Dict[str, str]] = field(default_factory=list)
    error_message: Optional[str] = None
    completed_time: Optional[datetime] = None
    progress: int = 0
    total_resources: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "job_id": self.job_id,
            "status": self.status.value,
            "level": self.level.value,
            "request_time": self.request_time.isoformat(),
            "resource_types": self.resource_types,
            "patient_ids": self.patient_ids,
            "group_id": self.group_id,
            "since": self.since.isoformat() if self.since else None,
            "type_filter": self.type_filter,
            "output_files": self.output_files,
            "error_message": self.error_message,
            "completed_time": self.completed_time.isoformat() if self.completed_time else None,
            "progress": self.progress,
            "total_resources": self.total_resources
        }


class BulkExportService:
    """
    Service for FHIR Bulk Data Export operations.
    
    Implements the FHIR Bulk Data Access specification for exporting
    large amounts of data in NDJSON format.
    """
    
    # In-memory job storage (in production, use Redis or database)
    _jobs: Dict[str, ExportJob] = {}
    _lock = threading.Lock()
    _executor = ThreadPoolExecutor(max_workers=3)
    
    # Supported resource types for export
    SUPPORTED_RESOURCE_TYPES = [
        "Patient", "Practitioner", "PractitionerRole", "Organization",
        "Encounter", "Observation", "Condition", "Procedure",
        "MedicationRequest", "AllergyIntolerance", "Immunization",
        "DiagnosticReport", "DocumentReference", "Composition",
        "Appointment", "Schedule", "Slot", "Location", "RelatedPerson",
        "Consent", "AuditEvent", "Provenance"
    ]
    
    # Default resource types for each export level
    DEFAULT_PATIENT_TYPES = [
        "Patient", "Encounter", "Observation", "Condition", "Procedure",
        "MedicationRequest", "AllergyIntolerance", "Immunization",
        "DiagnosticReport", "DocumentReference", "Appointment", "Consent"
    ]
    
    DEFAULT_GROUP_TYPES = DEFAULT_PATIENT_TYPES + ["RelatedPerson"]
    
    DEFAULT_SYSTEM_TYPES = SUPPORTED_RESOURCE_TYPES
    
    @classmethod
    def create_export_job(
        cls,
        level: ExportLevel,
        resource_types: Optional[List[str]] = None,
        patient_ids: Optional[List[str]] = None,
        group_id: Optional[str] = None,
        since: Optional[datetime] = None,
        type_filter: Optional[str] = None,
        user: Optional[Any] = None
    ) -> ExportJob:
        """
        Create a new bulk export job.
        
        Args:
            level: Export level (Patient, Group, System)
            resource_types: List of resource types to export (optional)
            patient_ids: List of patient IDs for Patient-level export
            group_id: Group ID for Group-level export
            since: Only export resources updated since this time
            type_filter: Additional filter expression
            user: Requesting user (for audit)
            
        Returns:
            The created ExportJob
        """
        # Determine resource types based on level
        if not resource_types:
            if level == ExportLevel.PATIENT:
                resource_types = cls.DEFAULT_PATIENT_TYPES
            elif level == ExportLevel.GROUP:
                resource_types = cls.DEFAULT_GROUP_TYPES
            else:
                resource_types = cls.DEFAULT_SYSTEM_TYPES
        
        # Validate resource types
        invalid_types = [t for t in resource_types if t not in cls.SUPPORTED_RESOURCE_TYPES]
        if invalid_types:
            raise ValueError(f"Unsupported resource types: {invalid_types}")
        
        # Create job
        job = ExportJob(
            job_id=str(uuid.uuid4()),
            status=ExportStatus.PENDING,
            level=level,
            request_time=datetime.now(),
            resource_types=resource_types,
            patient_ids=patient_ids,
            group_id=group_id,
            since=since,
            type_filter=type_filter
        )
        
        with cls._lock:
            cls._jobs[job.job_id] = job
        
        logger.info(f"Created export job {job.job_id} at level {level.value}")
        
        # Start async processing
        cls._executor.submit(cls._process_export_job, job.job_id, user)
        
        return job
    
    @classmethod
    def get_job(cls, job_id: str) -> Optional[ExportJob]:
        """Get an export job by ID."""
        with cls._lock:
            return cls._jobs.get(job_id)
    
    @classmethod
    def cancel_job(cls, job_id: str) -> bool:
        """Cancel an export job."""
        with cls._lock:
            job = cls._jobs.get(job_id)
            if job and job.status in [ExportStatus.PENDING, ExportStatus.IN_PROGRESS]:
                job.status = ExportStatus.CANCELLED
                logger.info(f"Cancelled export job {job_id}")
                return True
            return False
    
    @classmethod
    def delete_job(cls, job_id: str) -> bool:
        """Delete an export job and its files."""
        with cls._lock:
            job = cls._jobs.get(job_id)
            if not job:
                return False
            
            # Delete output files
            for output in job.output_files:
                file_path = output.get("file_path")
                if file_path and os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except Exception as e:
                        logger.error(f"Error deleting file {file_path}: {e}")
            
            del cls._jobs[job_id]
            logger.info(f"Deleted export job {job_id}")
            return True
    
    @classmethod
    def list_jobs(cls, status: Optional[ExportStatus] = None) -> List[ExportJob]:
        """List all export jobs, optionally filtered by status."""
        with cls._lock:
            jobs = list(cls._jobs.values())
            if status:
                jobs = [j for j in jobs if j.status == status]
            return sorted(jobs, key=lambda j: j.request_time, reverse=True)
    
    @classmethod
    def _process_export_job(cls, job_id: str, user: Optional[Any] = None):
        """Background task to process an export job."""
        job = cls.get_job(job_id)
        if not job:
            return
        
        try:
            with cls._lock:
                job.status = ExportStatus.IN_PROGRESS
            
            logger.info(f"Processing export job {job_id}")
            
            fhir_service = FHIRService(user)
            job_dir = os.path.join(EXPORT_DIR, job_id)
            os.makedirs(job_dir, exist_ok=True)
            
            total_resources = 0
            
            for i, resource_type in enumerate(job.resource_types):
                # Check if cancelled
                if job.status == ExportStatus.CANCELLED:
                    return
                
                # Update progress
                job.progress = int((i / len(job.resource_types)) * 100)
                
                # Build search parameters
                params = {"_count": "1000"}  # Max per request
                
                if job.since:
                    params["_lastUpdated"] = f"ge{job.since.isoformat()}"
                
                if job.level == ExportLevel.PATIENT and job.patient_ids:
                    if resource_type == "Patient":
                        params["_id"] = ",".join(job.patient_ids)
                    else:
                        params["patient"] = ",".join(job.patient_ids)
                
                # Fetch resources
                try:
                    resources = fhir_service.search_resources(resource_type, params)
                except FHIRServiceException as e:
                    logger.warning(f"Error fetching {resource_type}: {e}")
                    resources = []
                
                if not resources:
                    continue
                
                # Write to NDJSON file
                file_name = f"{resource_type}.ndjson"
                file_path = os.path.join(job_dir, file_name)
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    for resource in resources:
                        f.write(json.dumps(resource, ensure_ascii=False) + '\n')
                        total_resources += 1
                
                job.output_files.append({
                    "type": resource_type,
                    "url": f"/api/v1/export/files/{job_id}/{file_name}",
                    "file_path": file_path,
                    "count": len(resources)
                })
                
                job.total_resources = total_resources
            
            # Mark as completed
            with cls._lock:
                job.status = ExportStatus.COMPLETED
                job.completed_time = datetime.now()
                job.progress = 100
            
            logger.info(f"Export job {job_id} completed with {total_resources} resources")
            
        except Exception as e:
            logger.error(f"Export job {job_id} failed: {e}")
            with cls._lock:
                job.status = ExportStatus.FAILED
                job.error_message = str(e)
    
    @classmethod
    def get_export_file(cls, job_id: str, file_name: str) -> Optional[str]:
        """Get the path to an export file."""
        job = cls.get_job(job_id)
        if not job or job.status != ExportStatus.COMPLETED:
            return None
        
        file_path = os.path.join(EXPORT_DIR, job_id, file_name)
        if os.path.exists(file_path):
            return file_path
        return None


@dataclass
class ImportJob:
    """Represents a bulk import job."""
    job_id: str
    status: ExportStatus  # Reusing ExportStatus
    request_time: datetime
    input_files: List[Dict[str, str]] = field(default_factory=list)
    imported_resources: Dict[str, int] = field(default_factory=dict)
    error_message: Optional[str] = None
    completed_time: Optional[datetime] = None
    progress: int = 0
    total_resources: int = 0
    errors: List[Dict[str, str]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "job_id": self.job_id,
            "status": self.status.value,
            "request_time": self.request_time.isoformat(),
            "input_files": self.input_files,
            "imported_resources": self.imported_resources,
            "error_message": self.error_message,
            "completed_time": self.completed_time.isoformat() if self.completed_time else None,
            "progress": self.progress,
            "total_resources": self.total_resources,
            "errors": self.errors
        }


class BulkImportService:
    """
    Service for FHIR Bulk Data Import operations.
    
    Processes NDJSON files to import resources into the FHIR server.
    """
    
    _jobs: Dict[str, ImportJob] = {}
    _lock = threading.Lock()
    _executor = ThreadPoolExecutor(max_workers=2)
    
    @classmethod
    def create_import_job(
        cls,
        ndjson_files: List[Dict[str, Any]],
        user: Optional[Any] = None
    ) -> ImportJob:
        """
        Create a new bulk import job.
        
        Args:
            ndjson_files: List of dicts with 'resource_type' and 'content' or 'file_path'
            user: Requesting user
            
        Returns:
            The created ImportJob
        """
        job = ImportJob(
            job_id=str(uuid.uuid4()),
            status=ExportStatus.PENDING,
            request_time=datetime.now(),
            input_files=ndjson_files
        )
        
        with cls._lock:
            cls._jobs[job.job_id] = job
        
        logger.info(f"Created import job {job.job_id}")
        
        # Start async processing
        cls._executor.submit(cls._process_import_job, job.job_id, user)
        
        return job
    
    @classmethod
    def get_job(cls, job_id: str) -> Optional[ImportJob]:
        """Get an import job by ID."""
        with cls._lock:
            return cls._jobs.get(job_id)
    
    @classmethod
    def _process_import_job(cls, job_id: str, user: Optional[Any] = None):
        """Background task to process an import job."""
        job = cls.get_job(job_id)
        if not job:
            return
        
        try:
            with cls._lock:
                job.status = ExportStatus.IN_PROGRESS
            
            logger.info(f"Processing import job {job_id}")
            
            fhir_service = FHIRService(user)
            total_imported = 0
            
            for i, file_info in enumerate(job.input_files):
                resource_type = file_info.get("resource_type", "Unknown")
                content = file_info.get("content", "")
                file_path = file_info.get("file_path")
                
                # Update progress
                job.progress = int((i / len(job.input_files)) * 100)
                
                # Read content from file if path provided
                if file_path and os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                
                if not content:
                    continue
                
                # Parse NDJSON and import each resource
                lines = content.strip().split('\n')
                imported_count = 0
                
                for line in lines:
                    if not line.strip():
                        continue
                    
                    try:
                        resource = json.loads(line)
                        
                        # Create or update resource
                        if "id" in resource:
                            # Update existing
                            fhir_service.update_resource(
                                resource_type,
                                resource["id"],
                                resource
                            )
                        else:
                            # Create new
                            fhir_service.create_resource(resource_type, resource)
                        
                        imported_count += 1
                        total_imported += 1
                        
                    except json.JSONDecodeError as e:
                        job.errors.append({
                            "resource_type": resource_type,
                            "error": f"JSON parse error: {str(e)}",
                            "line": line[:100]
                        })
                    except Exception as e:
                        job.errors.append({
                            "resource_type": resource_type,
                            "error": str(e),
                            "line": line[:100]
                        })
                
                job.imported_resources[resource_type] = imported_count
                job.total_resources = total_imported
            
            # Mark as completed
            with cls._lock:
                job.status = ExportStatus.COMPLETED
                job.completed_time = datetime.now()
                job.progress = 100
            
            logger.info(f"Import job {job_id} completed: {total_imported} resources imported")
            
        except Exception as e:
            logger.error(f"Import job {job_id} failed: {e}")
            with cls._lock:
                job.status = ExportStatus.FAILED
                job.error_message = str(e)


# SMART on FHIR OAuth2 Scopes
SMART_SCOPES = {
    # Patient-level scopes
    "patient/*.read": "Read all patient data",
    "patient/*.write": "Write all patient data",
    "patient/Patient.read": "Read Patient resources",
    "patient/Observation.read": "Read Observation resources",
    "patient/Condition.read": "Read Condition resources",
    "patient/MedicationRequest.read": "Read MedicationRequest resources",
    "patient/Encounter.read": "Read Encounter resources",
    
    # User-level scopes
    "user/*.read": "Read all data the user has access to",
    "user/*.write": "Write all data the user has access to",
    "user/Patient.read": "Read Patient resources",
    "user/Practitioner.read": "Read Practitioner resources",
    
    # System-level scopes
    "system/*.read": "System-level read access",
    "system/*.write": "System-level write access",
    "system/Patient.read": "System read Patient resources",
    "system/Observation.write": "System write Observation resources",
    
    # Launch scopes
    "launch": "Permission to obtain launch context",
    "launch/patient": "Need patient context at launch",
    "launch/encounter": "Need encounter context at launch",
    
    # Identity scopes
    "openid": "OpenID Connect scope",
    "profile": "Permission to access user profile",
    "fhirUser": "Permission to access FHIR user identity",
    
    # Bulk data scopes
    "system/Patient.$export": "Bulk export Patient data",
    "system/Group.$export": "Bulk export Group data",
    "system/*.$export": "Bulk export all data",
}


class SMARTScopeValidator:
    """Validator for SMART on FHIR OAuth2 scopes."""
    
    @classmethod
    def parse_scope(cls, scope: str) -> Dict[str, Any]:
        """
        Parse a SMART scope string.
        
        Returns dict with:
            - context: 'patient', 'user', or 'system'
            - resource_type: '*' or specific type
            - permission: 'read', 'write', or '*'
            - operation: Optional, e.g., '$export'
        """
        parts = scope.split("/")
        if len(parts) != 2:
            return {"valid": False, "error": "Invalid scope format"}
        
        context = parts[0]
        if context not in ["patient", "user", "system"]:
            return {"valid": False, "error": f"Invalid context: {context}"}
        
        resource_permission = parts[1]
        
        # Check for operation
        if ".$" in resource_permission:
            resource_part, operation = resource_permission.split(".$", 1)
            operation = f"${operation}"
        else:
            resource_part = resource_permission
            operation = None
        
        # Parse resource.permission
        if "." in resource_part:
            resource_type, permission = resource_part.rsplit(".", 1)
        else:
            resource_type = resource_part
            permission = "*"
        
        return {
            "valid": True,
            "context": context,
            "resource_type": resource_type,
            "permission": permission,
            "operation": operation
        }
    
    @classmethod
    def validate_scopes(cls, requested_scopes: List[str]) -> Dict[str, Any]:
        """
        Validate a list of requested scopes.
        
        Returns dict with valid and invalid scopes.
        """
        valid = []
        invalid = []
        
        for scope in requested_scopes:
            if scope in SMART_SCOPES:
                valid.append({
                    "scope": scope,
                    "description": SMART_SCOPES[scope]
                })
            else:
                # Try to parse as a valid pattern
                parsed = cls.parse_scope(scope)
                if parsed.get("valid"):
                    valid.append({
                        "scope": scope,
                        "description": f"Access to {parsed['resource_type']} ({parsed['permission']})"
                    })
                else:
                    invalid.append({
                        "scope": scope,
                        "error": parsed.get("error", "Unknown scope")
                    })
        
        return {
            "valid_scopes": valid,
            "invalid_scopes": invalid,
            "all_valid": len(invalid) == 0
        }
    
    @classmethod
    def check_access(
        cls,
        granted_scopes: List[str],
        resource_type: str,
        action: str,  # 'read' or 'write'
        context: str = "user"  # 'patient', 'user', or 'system'
    ) -> bool:
        """
        Check if access is granted for a specific resource and action.
        """
        for scope in granted_scopes:
            parsed = cls.parse_scope(scope)
            if not parsed.get("valid"):
                continue
            
            # Check context
            if parsed["context"] != context and parsed["context"] != "system":
                continue
            
            # Check resource type
            if parsed["resource_type"] != "*" and parsed["resource_type"] != resource_type:
                continue
            
            # Check permission
            if parsed["permission"] == "*" or parsed["permission"] == action:
                return True
        
        return False
