"""
FHIR Validation API Endpoints

Sprint 38: FHIR-Native Architecture
"""

import logging
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .authentication import KeycloakAuthentication
from .services.fhir_validation_service import FHIRValidationService

logger = logging.getLogger(__name__)


@api_view(['POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def validate_resource(request):
    """
    Validate a FHIR resource.
    
    POST /api/v1/fhir/validate
    
    Body: Any FHIR resource
    
    Query params:
        profile: Optional profile URL to validate against
        mode: create, update, or delete (default: create)
    
    Returns:
        {
            "valid": true/false,
            "resource_type": "Patient",
            "issues": [...],
            "error_count": 0,
            "warning_count": 1
        }
    """
    try:
        resource = request.data
        
        if not isinstance(resource, dict) or "resourceType" not in resource:
            return Response({
                "valid": False,
                "error": "Invalid FHIR resource - must have resourceType"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        profile = request.query_params.get('profile')
        mode = request.query_params.get('mode', 'create')
        
        result = FHIRValidationService.validate(resource, profile=profile, mode=mode)
        
        return Response(result.to_dict())
        
    except Exception as e:
        logger.error(f"Validation error: {e}")
        return Response({
            "valid": False,
            "error": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def validate_bundle(request):
    """
    Validate a FHIR Bundle and all contained resources.
    
    POST /api/v1/fhir/validate-bundle
    """
    try:
        bundle = request.data
        
        if not isinstance(bundle, dict) or bundle.get("resourceType") != "Bundle":
            return Response({
                "valid": False,
                "error": "Resource must be a FHIR Bundle"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        result = FHIRValidationService.validate_bundle(bundle)
        
        return Response(result.to_dict())
        
    except Exception as e:
        logger.error(f"Bundle validation error: {e}")
        return Response({
            "valid": False,
            "error": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def check_reference(request):
    """
    Check if a FHIR reference exists.
    
    GET /api/v1/fhir/check-reference?ref=Patient/123
    """
    reference = request.query_params.get('ref')
    
    if not reference:
        return Response({
            "error": "Missing 'ref' query parameter"
        }, status=status.HTTP_400_BAD_REQUEST)
    
    exists, error = FHIRValidationService.validate_reference(reference)
    
    return Response({
        "reference": reference,
        "exists": exists,
        "error": error
    })


@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def list_profiles(request, resource_type):
    """
    List available profiles for a resource type.
    
    GET /api/v1/fhir/profiles/Patient
    """
    profiles = FHIRValidationService.get_profiles(resource_type)
    
    return Response({
        "resource_type": resource_type,
        "profiles": profiles
    })


@api_view(['POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def quick_validate(request):
    """
    Quick validation without calling HAPI (local checks only).
    
    POST /api/v1/fhir/quick-validate
    
    Faster but less thorough than full validation.
    """
    try:
        resource = request.data
        
        if not isinstance(resource, dict):
            return Response({
                "valid": False,
                "error": "Invalid resource format"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        result = FHIRValidationService.validate_with_quick_check(
            resource,
            full_validation=False
        )
        
        return Response(result.to_dict())
        
    except Exception as e:
        return Response({
            "valid": False,
            "error": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def validation_info(request):
    """
    Get validation service info.
    
    GET /api/v1/fhir/validation-info
    """
    return Response({
        'service': 'FHIR Validation',
        'version': '1.0',
        'fhir_version': 'R4 (4.0.1)',
        'features': [
            '$validate operation integration',
            'Profile validation',
            'Bundle validation',
            'Reference checking',
            'Quick local validation'
        ],
        'endpoints': [
            'POST /api/v1/fhir/validate',
            'POST /api/v1/fhir/validate-bundle',
            'POST /api/v1/fhir/quick-validate',
            'GET /api/v1/fhir/check-reference',
            'GET /api/v1/fhir/profiles/{resourceType}'
        ]
    })
