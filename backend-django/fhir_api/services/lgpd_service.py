"""
Sprint 24: LGPD Privacy Service

Implements LGPD (Lei Geral de Proteção de Dados) compliance features:
- Data Access Logging (Art. 19)
- Data Portability / Download (Art. 18, II)
- Data Deletion Request (Art. 18, VI)
- Data Anonymization
- Consent Verification

LGPD Reference: Lei nº 13.709/2018
"""

import os
import json
import logging
import zipfile
import tempfile
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict
from enum import Enum
from io import BytesIO

from .fhir_core import FHIRService, FHIRServiceException

logger = logging.getLogger(__name__)


class LGPDRequestType(Enum):
    """LGPD request types based on Art. 18"""
    CONFIRMATION = "confirmation"           # I - confirmação da existência
    ACCESS = "access"                       # II - acesso aos dados
    CORRECTION = "correction"               # III - correção de dados
    ANONYMIZATION = "anonymization"         # IV - anonimização
    BLOCKING = "blocking"                   # IV - bloqueio
    DELETION = "deletion"                   # VI - eliminação
    PORTABILITY = "portability"             # V - portabilidade
    INFO_SHARING = "info_sharing"           # VII - informação sobre compartilhamento
    CONSENT_REVOCATION = "consent_revocation"  # IX - revogação do consentimento


class LGPDRequestStatus(Enum):
    """Status of LGPD request"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REJECTED = "rejected"
    EXPIRED = "expired"


@dataclass
class LGPDRequest:
    """LGPD data subject request"""
    request_id: str
    request_type: LGPDRequestType
    patient_id: str
    requester_name: str
    requester_email: str
    status: LGPDRequestStatus
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    reason: Optional[str] = None
    notes: Optional[str] = None
    output_file: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "request_type": self.request_type.value,
            "patient_id": self.patient_id,
            "requester_name": self.requester_name,
            "requester_email": self.requester_email,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "reason": self.reason,
            "notes": self.notes,
            "output_file": self.output_file
        }


@dataclass
class DataAccessLog:
    """Log of data access for audit purposes"""
    log_id: str
    patient_id: str
    resource_type: str
    resource_id: str
    action: str  # read, update, delete, export
    user_id: str
    user_name: str
    timestamp: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    reason: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "log_id": self.log_id,
            "patient_id": self.patient_id,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "action": self.action,
            "user_id": self.user_id,
            "user_name": self.user_name,
            "timestamp": self.timestamp.isoformat(),
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "reason": self.reason
        }


class LGPDService:
    """
    LGPD Compliance Service
    
    Handles all LGPD-related operations including:
    - Data access logging
    - Data portability (export)
    - Data deletion requests
    - Consent management integration
    """
    
    # In-memory storage (use database in production)
    _requests: Dict[str, LGPDRequest] = {}
    _access_logs: List[DataAccessLog] = []
    
    # Resource types to include in data export
    EXPORTABLE_RESOURCES = [
        "Patient",
        "Observation",
        "Condition",
        "Procedure",
        "MedicationRequest",
        "MedicationStatement",
        "AllergyIntolerance",
        "Immunization",
        "Encounter",
        "DiagnosticReport",
        "Consent",
        "DocumentReference"
    ]
    
    # Sensitive fields to anonymize
    SENSITIVE_FIELDS = [
        "name", "telecom", "address", "birthDate",
        "identifier", "photo", "contact"
    ]
    
    @classmethod
    def log_data_access(
        cls,
        patient_id: str,
        resource_type: str,
        resource_id: str,
        action: str,
        user,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        reason: Optional[str] = None
    ) -> DataAccessLog:
        """
        Log a data access event for LGPD compliance.
        
        Args:
            patient_id: ID of the patient whose data was accessed
            resource_type: FHIR resource type
            resource_id: Resource ID
            action: Type of action (read, update, delete, export)
            user: The user who accessed the data
            ip_address: Client IP address
            user_agent: Client user agent
            reason: Reason for access
        """
        import uuid
        
        log = DataAccessLog(
            log_id=str(uuid.uuid4()),
            patient_id=patient_id,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            user_id=str(user) if user else "anonymous",
            user_name=getattr(user, 'username', str(user)) if user else "Anonymous",
            timestamp=datetime.now(),
            ip_address=ip_address,
            user_agent=user_agent,
            reason=reason
        )
        
        cls._access_logs.append(log)
        logger.info(f"Data access logged: {log.log_id} - {action} on {resource_type}/{resource_id}")
        
        return log
    
    @classmethod
    def get_access_logs(
        cls,
        patient_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        action: Optional[str] = None
    ) -> List[DataAccessLog]:
        """
        Get data access logs for a patient.
        
        LGPD Art. 19 - The data subject has the right to obtain information
        about their personal data processing activities.
        """
        logs = [log for log in cls._access_logs if log.patient_id == patient_id]
        
        if start_date:
            logs = [log for log in logs if log.timestamp >= start_date]
        if end_date:
            logs = [log for log in logs if log.timestamp <= end_date]
        if action:
            logs = [log for log in logs if log.action == action]
        
        return sorted(logs, key=lambda x: x.timestamp, reverse=True)
    
    @classmethod
    def create_lgpd_request(
        cls,
        request_type: LGPDRequestType,
        patient_id: str,
        requester_name: str,
        requester_email: str,
        reason: Optional[str] = None
    ) -> LGPDRequest:
        """
        Create a new LGPD request.
        
        Args:
            request_type: Type of LGPD request
            patient_id: ID of the patient
            requester_name: Name of the requester (usually the patient)
            requester_email: Email for communication
            reason: Reason for the request
        """
        import uuid
        
        request = LGPDRequest(
            request_id=str(uuid.uuid4()),
            request_type=request_type,
            patient_id=patient_id,
            requester_name=requester_name,
            requester_email=requester_email,
            status=LGPDRequestStatus.PENDING,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            reason=reason
        )
        
        cls._requests[request.request_id] = request
        logger.info(f"LGPD request created: {request.request_id} - {request_type.value}")
        
        return request
    
    @classmethod
    def get_lgpd_request(cls, request_id: str) -> Optional[LGPDRequest]:
        """Get a specific LGPD request."""
        return cls._requests.get(request_id)
    
    @classmethod
    def list_lgpd_requests(
        cls,
        patient_id: Optional[str] = None,
        status: Optional[LGPDRequestStatus] = None
    ) -> List[LGPDRequest]:
        """List LGPD requests with optional filtering."""
        requests = list(cls._requests.values())
        
        if patient_id:
            requests = [r for r in requests if r.patient_id == patient_id]
        if status:
            requests = [r for r in requests if r.status == status]
        
        return sorted(requests, key=lambda x: x.created_at, reverse=True)
    
    @classmethod
    def update_request_status(
        cls,
        request_id: str,
        status: LGPDRequestStatus,
        notes: Optional[str] = None
    ) -> Optional[LGPDRequest]:
        """Update the status of an LGPD request."""
        request = cls._requests.get(request_id)
        if not request:
            return None
        
        request.status = status
        request.updated_at = datetime.now()
        if notes:
            request.notes = notes
        if status == LGPDRequestStatus.COMPLETED:
            request.completed_at = datetime.now()
        
        return request
    
    @classmethod
    def export_patient_data(
        cls,
        patient_id: str,
        fhir_service: FHIRService,
        format: str = "json"
    ) -> Dict[str, Any]:
        """
        Export all patient data for portability (LGPD Art. 18, II and V).
        
        Returns a dictionary with all patient resources.
        """
        logger.info(f"Starting data export for patient {patient_id}")
        
        export_data = {
            "exportDate": datetime.now().isoformat(),
            "patientId": patient_id,
            "format": format,
            "resources": {}
        }
        
        # Get patient demographics
        try:
            patient = fhir_service.get_patient_by_id(patient_id)
            export_data["resources"]["Patient"] = [patient]
        except FHIRServiceException:
            export_data["resources"]["Patient"] = []
        
        # Get related resources
        for resource_type in cls.EXPORTABLE_RESOURCES[1:]:  # Skip Patient
            try:
                params = {"patient": patient_id, "_count": 1000}
                # Some resources use 'subject' instead of 'patient'
                if resource_type in ["Consent", "DocumentReference"]:
                    params = {"patient": f"Patient/{patient_id}", "_count": 1000}
                
                resources = fhir_service.search_resources(resource_type, params, use_cache=False)
                if resources:
                    export_data["resources"][resource_type] = resources
            except Exception as e:
                logger.warning(f"Error exporting {resource_type}: {e}")
                export_data["resources"][resource_type] = []
        
        # Calculate statistics
        total_resources = sum(len(r) for r in export_data["resources"].values())
        export_data["statistics"] = {
            "totalResources": total_resources,
            "resourceCounts": {
                rt: len(resources) 
                for rt, resources in export_data["resources"].items()
            }
        }
        
        logger.info(f"Data export completed for patient {patient_id}: {total_resources} resources")
        
        return export_data
    
    @classmethod
    def create_export_file(
        cls,
        export_data: Dict[str, Any],
        file_format: str = "json"
    ) -> bytes:
        """
        Create a downloadable file from export data.
        
        Returns bytes of the file (JSON or ZIP).
        """
        if file_format == "json":
            return json.dumps(export_data, indent=2, ensure_ascii=False).encode("utf-8")
        
        elif file_format == "zip":
            # Create ZIP with separate files per resource type
            buffer = BytesIO()
            with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
                # Write metadata
                metadata = {
                    "exportDate": export_data["exportDate"],
                    "patientId": export_data["patientId"],
                    "statistics": export_data["statistics"]
                }
                zf.writestr("metadata.json", json.dumps(metadata, indent=2))
                
                # Write each resource type to separate file
                for resource_type, resources in export_data["resources"].items():
                    if resources:
                        content = json.dumps(resources, indent=2, ensure_ascii=False)
                        zf.writestr(f"{resource_type.lower()}.json", content)
            
            return buffer.getvalue()
        
        else:
            raise ValueError(f"Unsupported format: {file_format}")
    
    @classmethod
    def process_deletion_request(
        cls,
        patient_id: str,
        fhir_service: FHIRService,
        soft_delete: bool = True
    ) -> Dict[str, Any]:
        """
        Process a data deletion request (LGPD Art. 18, VI).
        
        By default, performs a soft delete (anonymization + status change)
        rather than hard delete to maintain audit trail.
        
        Args:
            patient_id: ID of the patient
            fhir_service: FHIR service instance
            soft_delete: If True, anonymize data. If False, actually delete.
        """
        logger.info(f"Processing deletion request for patient {patient_id}")
        
        result = {
            "patient_id": patient_id,
            "deletion_type": "soft" if soft_delete else "hard",
            "processed_at": datetime.now().isoformat(),
            "deleted_resources": {},
            "errors": []
        }
        
        if soft_delete:
            # Anonymize patient data
            try:
                patient = fhir_service.get_patient_by_id(patient_id)
                anonymized = cls._anonymize_patient(patient)
                fhir_service.update_resource("Patient", patient_id, anonymized)
                result["deleted_resources"]["Patient"] = 1
            except Exception as e:
                result["errors"].append(f"Patient: {str(e)}")
            
            # Update related consents to rejected
            try:
                consents = fhir_service.search_resources("Consent", {
                    "patient": patient_id,
                    "status": "active"
                }, use_cache=False)
                
                for consent in consents:
                    consent["status"] = "rejected"
                    fhir_service.update_resource("Consent", consent["id"], consent)
                
                result["deleted_resources"]["Consent"] = len(consents)
            except Exception as e:
                result["errors"].append(f"Consent: {str(e)}")
        
        else:
            # Hard delete - only if really needed
            # Note: This might fail due to referential integrity
            for resource_type in cls.EXPORTABLE_RESOURCES:
                try:
                    if resource_type == "Patient":
                        # Patient is deleted last
                        continue
                    
                    resources = fhir_service.search_resources(resource_type, {
                        "patient": patient_id
                    }, use_cache=False)
                    
                    for resource in resources:
                        fhir_service.delete_resource(resource_type, resource["id"])
                    
                    result["deleted_resources"][resource_type] = len(resources)
                except Exception as e:
                    result["errors"].append(f"{resource_type}: {str(e)}")
            
            # Finally delete patient
            try:
                fhir_service.delete_patient_resource(patient_id)
                result["deleted_resources"]["Patient"] = 1
            except Exception as e:
                result["errors"].append(f"Patient deletion: {str(e)}")
        
        result["success"] = len(result["errors"]) == 0
        logger.info(f"Deletion request completed for {patient_id}: {result['success']}")
        
        return result
    
    @classmethod
    def _anonymize_patient(cls, patient: Dict[str, Any]) -> Dict[str, Any]:
        """
        Anonymize patient data by removing PII.
        
        Preserves non-identifying data for statistical purposes.
        """
        anonymized = patient.copy()
        
        # Remove name
        if "name" in anonymized:
            anonymized["name"] = [{
                "use": "anonymous",
                "family": "ANONIMIZADO",
                "given": ["PACIENTE"]
            }]
        
        # Remove identifiers (CPF, etc)
        if "identifier" in anonymized:
            anonymized["identifier"] = [{
                "system": "urn:oid:2.16.840.1.113883.13.236",
                "value": f"ANON-{datetime.now().strftime('%Y%m%d')}"
            }]
        
        # Remove contact info
        if "telecom" in anonymized:
            anonymized["telecom"] = []
        
        # Remove address
        if "address" in anonymized:
            # Keep only city/state for statistics
            for addr in anonymized.get("address", []):
                addr.pop("line", None)
                addr.pop("postalCode", None)
        
        # Remove photo
        anonymized.pop("photo", None)
        
        # Remove contact persons
        anonymized.pop("contact", None)
        
        # Mark as anonymized with extension
        anonymized["extension"] = anonymized.get("extension", []) + [{
            "url": "http://openehrcore.com.br/fhir/StructureDefinition/anonymized",
            "valueBoolean": True
        }]
        
        return anonymized
    
    @classmethod
    def check_consent(
        cls,
        patient_id: str,
        fhir_service: FHIRService,
        purpose: str = "treatment"
    ) -> Dict[str, Any]:
        """
        Check if patient has given consent for a specific purpose.
        
        Args:
            patient_id: Patient ID
            fhir_service: FHIR service
            purpose: Purpose to check (treatment, research, sharing, marketing)
        """
        try:
            consents = fhir_service.search_resources("Consent", {
                "patient": patient_id,
                "status": "active",
                "_count": 50
            }, use_cache=False)
            
            # Map category codes to purposes
            purpose_codes = {
                "treatment": "TREAT",
                "research": "RESEARCH",
                "sharing": "HPROVRD",
                "marketing": "HMARKT",
                "emergency": "ETREAT"
            }
            
            target_code = purpose_codes.get(purpose)
            if not target_code:
                return {"has_consent": False, "error": "Unknown purpose"}
            
            for consent in consents:
                categories = consent.get("category", [])
                for cat in categories:
                    codings = cat.get("coding", [])
                    for coding in codings:
                        if coding.get("code") == target_code:
                            # Check if consent is still valid
                            provision = consent.get("provision", {})
                            period = provision.get("period", {})
                            
                            end_date = period.get("end")
                            if end_date:
                                if datetime.fromisoformat(end_date.replace("Z", "+00:00")) < datetime.now():
                                    continue  # Expired
                            
                            return {
                                "has_consent": True,
                                "consent_id": consent.get("id"),
                                "purpose": purpose,
                                "valid_until": end_date
                            }
            
            return {"has_consent": False, "purpose": purpose}
            
        except Exception as e:
            logger.error(f"Error checking consent: {e}")
            return {"has_consent": False, "error": str(e)}
    
    @classmethod
    def generate_lgpd_report(
        cls,
        patient_id: str,
        fhir_service: FHIRService
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive LGPD report for a patient.
        
        Includes: data inventory, consents, access logs, processing activities.
        """
        report = {
            "generated_at": datetime.now().isoformat(),
            "patient_id": patient_id,
            "report_type": "LGPD Compliance Report",
            "sections": {}
        }
        
        # 1. Data Inventory
        data_inventory = {"resources": {}}
        for resource_type in cls.EXPORTABLE_RESOURCES:
            try:
                resources = fhir_service.search_resources(resource_type, {
                    "patient": patient_id,
                    "_count": 1000
                }, use_cache=False)
                data_inventory["resources"][resource_type] = {
                    "count": len(resources),
                    "oldest": min([r.get("meta", {}).get("lastUpdated", "") for r in resources]) if resources else None,
                    "newest": max([r.get("meta", {}).get("lastUpdated", "") for r in resources]) if resources else None
                }
            except:
                pass
        
        data_inventory["total_records"] = sum(
            d["count"] for d in data_inventory["resources"].values()
        )
        report["sections"]["data_inventory"] = data_inventory
        
        # 2. Active Consents
        try:
            consents = fhir_service.search_resources("Consent", {
                "patient": patient_id,
                "_count": 50
            }, use_cache=False)
            
            report["sections"]["consents"] = {
                "total": len(consents),
                "active": len([c for c in consents if c.get("status") == "active"]),
                "rejected": len([c for c in consents if c.get("status") == "rejected"]),
                "details": [
                    {
                        "id": c.get("id"),
                        "status": c.get("status"),
                        "category": c.get("category", [{}])[0].get("coding", [{}])[0].get("display"),
                        "date": c.get("dateTime")
                    }
                    for c in consents
                ]
            }
        except:
            report["sections"]["consents"] = {"error": "Could not fetch consents"}
        
        # 3. Access Logs (last 90 days)
        access_logs = cls.get_access_logs(
            patient_id,
            start_date=datetime.now() - timedelta(days=90)
        )
        report["sections"]["access_logs"] = {
            "period": "Last 90 days",
            "total_accesses": len(access_logs),
            "by_action": {},
            "by_user": {},
            "recent": [log.to_dict() for log in access_logs[:20]]
        }
        
        for log in access_logs:
            action = log.action
            report["sections"]["access_logs"]["by_action"][action] = \
                report["sections"]["access_logs"]["by_action"].get(action, 0) + 1
            
            user = log.user_name
            report["sections"]["access_logs"]["by_user"][user] = \
                report["sections"]["access_logs"]["by_user"].get(user, 0) + 1
        
        # 4. LGPD Requests
        lgpd_requests = cls.list_lgpd_requests(patient_id=patient_id)
        report["sections"]["lgpd_requests"] = {
            "total": len(lgpd_requests),
            "pending": len([r for r in lgpd_requests if r.status == LGPDRequestStatus.PENDING]),
            "completed": len([r for r in lgpd_requests if r.status == LGPDRequestStatus.COMPLETED]),
            "details": [r.to_dict() for r in lgpd_requests]
        }
        
        # 5. Compliance Status
        report["sections"]["compliance_status"] = {
            "has_active_consent": any(
                c.get("status") == "active" 
                for c in report["sections"].get("consents", {}).get("details", [])
            ),
            "data_access_logged": len(access_logs) > 0,
            "pending_requests": len([r for r in lgpd_requests if r.status == LGPDRequestStatus.PENDING]),
            "last_access": access_logs[0].timestamp.isoformat() if access_logs else None
        }
        
        return report
