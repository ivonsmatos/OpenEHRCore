"""
Views for Compliance Features

Sprint 35: Compliance endpoints for:
- Bias Prevention
- ISO 13606-2 Archetypes
- Data Anonymization
"""

import logging
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny

from .authentication import KeycloakAuthentication
from .services.bias_prevention_service import BiasPreventionService
from .services.archetype_service import ISO13606ArchetypeService, TerminologySystem

logger = logging.getLogger(__name__)


# ============================================================================
# BIAS PREVENTION ENDPOINTS
# ============================================================================

@api_view(['POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def validate_content(request):
    """
    Validate content for potential bias.
    
    POST /api/v1/compliance/bias/validate
    
    Body:
        {
            "content": "Clinical recommendation text...",
            "context": "clinical"
        }
    """
    content = request.data.get('content', '')
    context = request.data.get('context', 'general')
    
    if not content:
        return Response({
            'error': 'Content is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    has_bias, terms = BiasPreventionService.check_content_for_bias(content, context)
    
    return Response({
        'has_bias': has_bias,
        'detected_terms': terms,
        'original_content': content,
        'sanitized_content': BiasPreventionService.sanitize_content(content) if has_bias else content
    })


@api_view(['POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def validate_recommendation(request):
    """
    Validate a clinical recommendation for bias.
    
    POST /api/v1/compliance/bias/validate-recommendation
    
    Body:
        {
            "recommendation": "AI-generated recommendation..."
        }
    """
    recommendation = request.data.get('recommendation', '')
    patient_data = request.data.get('patient_data')
    
    if not recommendation:
        return Response({
            'error': 'Recommendation is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    result = BiasPreventionService.validate_clinical_recommendation(
        recommendation, 
        patient_data
    )
    
    return Response(result)


@api_view(['POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def anonymize_data(request):
    """
    Anonymize data for analytics export.
    
    POST /api/v1/compliance/anonymize
    
    Body:
        {
            "data": {...},
            "preserve_fields": ["gender", "birthDate"]
        }
    """
    data = request.data.get('data', {})
    preserve = request.data.get('preserve_fields')
    
    if not data:
        return Response({
            'error': 'Data is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    anonymized = BiasPreventionService.anonymize_for_analytics(data, preserve)
    
    return Response({
        'original_fields': list(data.keys()),
        'anonymized_fields': list(anonymized.keys()),
        'anonymized_data': anonymized
    })


@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def bias_audit_report(request):
    """
    Get bias detection audit report.
    
    GET /api/v1/compliance/bias/report
    """
    report = BiasPreventionService.generate_bias_report()
    return Response(report)


# ============================================================================
# ISO 13606-2 ARCHETYPE ENDPOINTS
# ============================================================================

@api_view(['GET'])
@permission_classes([AllowAny])
def list_archetypes(request):
    """
    List available clinical archetypes.
    
    GET /api/v1/archetypes/
    GET /api/v1/archetypes/?rm_type=OBSERVATION
    """
    rm_type = request.query_params.get('rm_type')
    
    archetypes = ISO13606ArchetypeService.list_archetypes(rm_type)
    
    return Response({
        'count': len(archetypes),
        'archetypes': archetypes
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def get_archetype(request, archetype_name):
    """
    Get a specific archetype definition.
    
    GET /api/v1/archetypes/{name}/
    """
    archetype = ISO13606ArchetypeService.get_archetype(archetype_name)
    
    if not archetype:
        return Response({
            'error': f'Archetype not found: {archetype_name}'
        }, status=status.HTTP_404_NOT_FOUND)
    
    return Response(archetype.to_dict())


@api_view(['POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def validate_archetype_data(request, archetype_name):
    """
    Validate data against an archetype.
    
    POST /api/v1/archetypes/{name}/validate/
    
    Body:
        {
            "data": {...}
        }
    """
    data = request.data.get('data', {})
    
    result = ISO13606ArchetypeService.validate_data(archetype_name, data)
    
    http_status = status.HTTP_200_OK if result['valid'] else status.HTTP_422_UNPROCESSABLE_ENTITY
    return Response(result, status=http_status)


@api_view(['POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def map_to_fhir(request, archetype_name):
    """
    Map archetype data to FHIR resource.
    
    POST /api/v1/archetypes/{name}/to-fhir/
    
    Body:
        {
            "data": {...},
            "patient_id": "patient-123"
        }
    """
    data = request.data.get('data', {})
    patient_id = request.data.get('patient_id')
    
    if not patient_id:
        return Response({
            'error': 'patient_id is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        fhir_resource = ISO13606ArchetypeService.map_to_fhir(
            archetype_name, 
            data, 
            patient_id
        )
        return Response(fhir_resource, status=status.HTTP_201_CREATED)
    except ValueError as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_terminology_codes(request):
    """
    Get terminology codes from a system.
    
    GET /api/v1/terminology/codes/?system=LOINC&q=blood
    """
    system_name = request.query_params.get('system', 'LOINC')
    search_term = request.query_params.get('q')
    
    try:
        system = TerminologySystem[system_name]
    except KeyError:
        return Response({
            'error': f'Unknown terminology system: {system_name}',
            'available_systems': [s.name for s in TerminologySystem]
        }, status=status.HTTP_400_BAD_REQUEST)
    
    codes = ISO13606ArchetypeService.get_terminology_codes(system, search_term)
    
    return Response({
        'system': system.value,
        'count': len(codes),
        'codes': codes
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def compliance_status(request):
    """
    Get overall compliance status.
    
    GET /api/v1/compliance/status
    """
    # Count archetypes
    archetypes = ISO13606ArchetypeService.list_archetypes()
    
    # Get bias audit summary
    bias_report = BiasPreventionService.generate_bias_report()
    
    return Response({
        'compliance': {
            'iso_13606_2': {
                'status': 'implemented',
                'archetypes_count': len(archetypes),
                'supported_rm_types': ['OBSERVATION', 'EVALUATION', 'INSTRUCTION', 'ACTION']
            },
            'bias_prevention': {
                'status': 'active',
                'guardrails_enabled': True,
                'total_detections': bias_report.get('total_detections', 0)
            },
            'data_anonymization': {
                'status': 'active',
                'lgpd_compliant': True,
                'pii_patterns_detected': list(BiasPreventionService.PII_PATTERNS.keys())
            },
            'terminology_bindings': {
                'status': 'active',
                'supported_systems': [s.name for s in TerminologySystem]
            }
        },
        'certifications': [
            'LGPD (Lei 13.709/2018)',
            'ISO 13606-2:2019 (Clinical Archetypes)',
            'HL7 FHIR R4'
        ]
    })
