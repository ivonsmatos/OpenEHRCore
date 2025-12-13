"""
FHIR Validation Service

Provides automatic validation of FHIR resources using HAPI FHIR $validate operation.

Features:
- Resource validation before save
- Profile validation
- OperationOutcome parsing
- Validation caching
"""

import logging
import requests
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from functools import lru_cache
from django.conf import settings

logger = logging.getLogger(__name__)


@dataclass
class ValidationIssue:
    """Represents a single validation issue."""
    severity: str  # fatal, error, warning, information
    code: str
    diagnostics: str
    location: Optional[str] = None
    expression: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "severity": self.severity,
            "code": self.code,
            "diagnostics": self.diagnostics,
            "location": self.location,
            "expression": self.expression
        }


@dataclass
class ValidationResult:
    """Result of FHIR resource validation."""
    valid: bool
    issues: List[ValidationIssue]
    resource_type: str
    profile: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "valid": self.valid,
            "resource_type": self.resource_type,
            "profile": self.profile,
            "issues": [i.to_dict() for i in self.issues],
            "error_count": len([i for i in self.issues if i.severity in ("fatal", "error")]),
            "warning_count": len([i for i in self.issues if i.severity == "warning"])
        }


class FHIRValidationService:
    """
    FHIR Resource Validation Service.
    
    Uses HAPI FHIR's $validate operation to validate resources
    against FHIR R4 specification and optionally custom profiles.
    """
    
    FHIR_BASE_URL = getattr(settings, 'FHIR_SERVER_URL', 'http://localhost:8080/fhir')
    
    # Cache for profiles
    _profile_cache: Dict[str, bool] = {}
    
    @classmethod
    def validate(
        cls,
        resource: Dict[str, Any],
        profile: Optional[str] = None,
        mode: str = "create"
    ) -> ValidationResult:
        """
        Validate a FHIR resource.
        
        Args:
            resource: FHIR resource as dict
            profile: Optional profile URL to validate against
            mode: Validation mode (create, update, delete)
            
        Returns:
            ValidationResult with issues
        """
        resource_type = resource.get("resourceType", "Unknown")
        
        try:
            # Build validation URL
            url = f"{cls.FHIR_BASE_URL}/{resource_type}/$validate"
            
            params = {"mode": mode}
            if profile:
                params["profile"] = profile
            
            # Call HAPI $validate
            response = requests.post(
                url,
                json=resource,
                params=params,
                headers={
                    "Content-Type": "application/fhir+json",
                    "Accept": "application/fhir+json"
                },
                timeout=10
            )
            
            # Parse OperationOutcome
            if response.status_code == 200:
                outcome = response.json()
                return cls._parse_operation_outcome(outcome, resource_type, profile)
            else:
                # Validation request itself failed
                logger.error(f"Validation request failed: {response.status_code}")
                return ValidationResult(
                    valid=False,
                    issues=[ValidationIssue(
                        severity="error",
                        code="exception",
                        diagnostics=f"Validation service returned {response.status_code}"
                    )],
                    resource_type=resource_type,
                    profile=profile
                )
                
        except requests.exceptions.ConnectionError:
            logger.warning("FHIR server not available for validation")
            # Return valid if server is down (don't block operations)
            return ValidationResult(
                valid=True,
                issues=[ValidationIssue(
                    severity="information",
                    code="informational",
                    diagnostics="Validation skipped - FHIR server not available"
                )],
                resource_type=resource_type,
                profile=profile
            )
        except Exception as e:
            logger.error(f"Validation error: {e}")
            return ValidationResult(
                valid=False,
                issues=[ValidationIssue(
                    severity="error",
                    code="exception",
                    diagnostics=str(e)
                )],
                resource_type=resource_type,
                profile=profile
            )
    
    @classmethod
    def _parse_operation_outcome(
        cls,
        outcome: Dict,
        resource_type: str,
        profile: Optional[str]
    ) -> ValidationResult:
        """Parse FHIR OperationOutcome into ValidationResult."""
        issues = []
        has_errors = False
        
        for issue_data in outcome.get("issue", []):
            severity = issue_data.get("severity", "information")
            
            if severity in ("fatal", "error"):
                has_errors = True
            
            issue = ValidationIssue(
                severity=severity,
                code=issue_data.get("code", "unknown"),
                diagnostics=issue_data.get("diagnostics", ""),
                location=issue_data.get("location", [None])[0] if issue_data.get("location") else None,
                expression=issue_data.get("expression", [None])[0] if issue_data.get("expression") else None
            )
            issues.append(issue)
        
        return ValidationResult(
            valid=not has_errors,
            issues=issues,
            resource_type=resource_type,
            profile=profile
        )
    
    @classmethod
    def validate_bundle(cls, bundle: Dict[str, Any]) -> ValidationResult:
        """Validate a FHIR Bundle and all contained resources."""
        if bundle.get("resourceType") != "Bundle":
            return ValidationResult(
                valid=False,
                issues=[ValidationIssue(
                    severity="error",
                    code="invalid",
                    diagnostics="Resource is not a Bundle"
                )],
                resource_type="Bundle"
            )
        
        all_issues = []
        has_errors = False
        
        # Validate the bundle itself
        bundle_result = cls.validate(bundle)
        all_issues.extend(bundle_result.issues)
        if not bundle_result.valid:
            has_errors = True
        
        # Validate each entry
        for i, entry in enumerate(bundle.get("entry", [])):
            resource = entry.get("resource")
            if resource:
                result = cls.validate(resource)
                for issue in result.issues:
                    issue.location = f"Bundle.entry[{i}].{issue.location or 'resource'}"
                all_issues.extend(result.issues)
                if not result.valid:
                    has_errors = True
        
        return ValidationResult(
            valid=not has_errors,
            issues=all_issues,
            resource_type="Bundle"
        )
    
    @classmethod
    def validate_reference(cls, reference: str) -> Tuple[bool, Optional[str]]:
        """
        Validate that a FHIR reference exists.
        
        Args:
            reference: Reference string (e.g., "Patient/123")
            
        Returns:
            Tuple of (exists, error_message)
        """
        try:
            url = f"{cls.FHIR_BASE_URL}/{reference}"
            response = requests.head(url, timeout=5)
            
            if response.status_code == 200:
                return True, None
            elif response.status_code == 404:
                return False, f"Referenced resource not found: {reference}"
            else:
                return False, f"Error checking reference: {response.status_code}"
                
        except Exception as e:
            logger.warning(f"Reference validation failed: {e}")
            return True, None  # Don't block if we can't check
    
    @classmethod
    def get_profiles(cls, resource_type: str) -> List[str]:
        """Get available profiles for a resource type."""
        # This could be extended to fetch from a profile registry
        profiles = {
            "Patient": [
                "http://hl7.org/fhir/us/core/StructureDefinition/us-core-patient",
                "http://hl7.org/fhir/br/core/StructureDefinition/br-core-patient"
            ],
            "Observation": [
                "http://hl7.org/fhir/us/core/StructureDefinition/us-core-vital-signs",
                "http://hl7.org/fhir/StructureDefinition/vitalsigns"
            ],
            "Condition": [
                "http://hl7.org/fhir/us/core/StructureDefinition/us-core-condition"
            ]
        }
        return profiles.get(resource_type, [])
    
    @classmethod
    def check_required_fields(cls, resource: Dict[str, Any]) -> List[ValidationIssue]:
        """
        Quick local check for commonly required fields.
        
        This is faster than calling $validate for obvious errors.
        """
        issues = []
        resource_type = resource.get("resourceType")
        
        if not resource_type:
            issues.append(ValidationIssue(
                severity="error",
                code="required",
                diagnostics="Missing required field: resourceType"
            ))
            return issues
        
        # Resource-specific required fields
        required_fields = {
            "Patient": ["name"],
            "Observation": ["status", "code", "subject"],
            "Condition": ["subject", "code"],
            "Encounter": ["status", "class", "subject"],
            "MedicationRequest": ["status", "intent", "medication", "subject"],
            "DiagnosticReport": ["status", "code"],
            "Procedure": ["status", "subject"],
            "AllergyIntolerance": ["patient"],
            "Immunization": ["status", "vaccineCode", "patient"],
            "CarePlan": ["status", "intent", "subject"],
            "ServiceRequest": ["status", "intent", "subject"],
            "Communication": ["status"],
        }
        
        for field in required_fields.get(resource_type, []):
            if field not in resource or resource[field] is None:
                issues.append(ValidationIssue(
                    severity="error",
                    code="required",
                    diagnostics=f"Missing required field: {field}",
                    expression=f"{resource_type}.{field}"
                ))
        
        return issues
    
    @classmethod
    def validate_with_quick_check(
        cls,
        resource: Dict[str, Any],
        full_validation: bool = True
    ) -> ValidationResult:
        """
        Validate resource with quick local check first.
        
        Args:
            resource: FHIR resource
            full_validation: If True, also call HAPI $validate
            
        Returns:
            ValidationResult
        """
        resource_type = resource.get("resourceType", "Unknown")
        
        # Quick local check
        quick_issues = cls.check_required_fields(resource)
        
        if quick_issues:
            # Has obvious errors, return immediately
            return ValidationResult(
                valid=False,
                issues=quick_issues,
                resource_type=resource_type
            )
        
        if full_validation:
            # Do full HAPI validation
            return cls.validate(resource)
        
        # Quick check passed, skip full validation
        return ValidationResult(
            valid=True,
            issues=[],
            resource_type=resource_type
        )


# Decorator for automatic validation
def validate_fhir_resource(profile: str = None, strict: bool = True):
    """
    Decorator to automatically validate FHIR resources in views.
    
    Usage:
        @validate_fhir_resource(strict=True)
        def create_patient(request):
            resource = request.data
            # ... create patient
    """
    def decorator(func):
        def wrapper(request, *args, **kwargs):
            from rest_framework.response import Response
            from rest_framework import status
            
            resource = request.data
            
            if not isinstance(resource, dict):
                return Response(
                    {"error": "Invalid resource format"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            result = FHIRValidationService.validate_with_quick_check(
                resource,
                full_validation=strict
            )
            
            if not result.valid:
                return Response({
                    "resourceType": "OperationOutcome",
                    "issue": [i.to_dict() for i in result.issues]
                }, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
            
            # Add validation result to request for logging
            request.fhir_validation = result
            
            return func(request, *args, **kwargs)
        
        return wrapper
    return decorator


# Singleton
_validation_service = None


def get_validation_service() -> FHIRValidationService:
    """Get validation service singleton."""
    global _validation_service
    if _validation_service is None:
        _validation_service = FHIRValidationService()
    return _validation_service
