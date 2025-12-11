"""
Sprint 20: FHIR Advanced Search Endpoints

This module provides advanced search capabilities for FHIR resources
with R4-compliant search parameters.
"""

import logging
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .services.fhir_core import FHIRService, FHIRServiceException
from .authentication import KeycloakAuthentication

logger = logging.getLogger(__name__)


@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def search_encounters(request):
    """
    Advanced encounter search with FHIR R4 compliant parameters.
    
    GET /api/v1/encounters/search/
    
    Query Parameters:
        - patient: Filter by patient ID
        - date: Filter by encounter date (exact: YYYY-MM-DD, or range: ge2024-01-01, le2024-12-31)
        - status: Filter by status (planned, arrived, in-progress, finished, cancelled)
        - class: Filter by encounter class (inpatient, outpatient, emergency, etc.)
        - _count: Number of results per page (default: 20, max: 100)
        - _getpagesoffset: Pagination offset
    
    Examples:
        /api/v1/encounters/search/?patient=patient-123
        /api/v1/encounters/search/?status=in-progress
        /api/v1/encounters/search/?date=ge2024-01-01&date=le2024-12-31
    """
    try:
        fhir_service = FHIRService(request.user)
        params = {}
        
        # Patient filter
        if request.query_params.get('patient'):
            params['patient'] = request.query_params['patient']
        
        # Date filter (supports range)
        if request.query_params.get('date'):
            params['date'] = request.query_params['date']
        
        # Status filter
        if request.query_params.get('status'):
            valid_statuses = ['planned', 'arrived', 'triaged', 'in-progress', 'onleave', 'finished', 'cancelled']
            status_val = request.query_params['status'].lower()
            if status_val in valid_statuses:
                params['status'] = status_val
            else:
                return Response({
                    "error": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Class filter
        if request.query_params.get('class'):
            params['class'] = request.query_params['class']
        
        # Pagination
        count = min(int(request.query_params.get('_count', 20)), 100)
        offset = int(request.query_params.get('_getpagesoffset', 0))
        params['_count'] = str(count)
        if offset > 0:
            params['_getpagesoffset'] = str(offset)
        
        # Execute search
        results = fhir_service.search_resources('Encounter', params)
        
        return Response({
            "total": len(results),
            "count": count,
            "offset": offset,
            "results": results
        }, status=status.HTTP_200_OK)
        
    except ValueError as e:
        return Response({"error": f"Invalid parameter: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
    except FHIRServiceException as e:
        logger.error(f"FHIR error searching encounters: {str(e)}")
        return Response({"error": str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    except Exception as e:
        logger.error(f"Error searching encounters: {str(e)}")
        return Response({"error": "Erro ao buscar encontros"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def search_observations(request):
    """
    Advanced observation search with FHIR R4 compliant parameters.
    
    GET /api/v1/observations/search/
    
    Query Parameters:
        - patient: Filter by patient ID
        - code: Filter by LOINC code
        - date: Filter by observation date (exact or range)
        - category: Filter by category (vital-signs, laboratory, imaging, etc.)
        - _count: Number of results per page (default: 20, max: 100)
        - _getpagesoffset: Pagination offset
    
    Examples:
        /api/v1/observations/search/?patient=patient-123&category=vital-signs
        /api/v1/observations/search/?code=8480-6
        /api/v1/observations/search/?date=ge2024-01-01
    """
    try:
        fhir_service = FHIRService(request.user)
        params = {}
        
        # Patient filter
        if request.query_params.get('patient'):
            params['patient'] = request.query_params['patient']
        
        # LOINC code filter
        if request.query_params.get('code'):
            params['code'] = request.query_params['code']
        
        # Date filter
        if request.query_params.get('date'):
            params['date'] = request.query_params['date']
        
        # Category filter
        if request.query_params.get('category'):
            params['category'] = request.query_params['category']
        
        # Pagination
        count = min(int(request.query_params.get('_count', 20)), 100)
        offset = int(request.query_params.get('_getpagesoffset', 0))
        params['_count'] = str(count)
        if offset > 0:
            params['_getpagesoffset'] = str(offset)
        
        # Execute search
        results = fhir_service.search_resources('Observation', params)
        
        return Response({
            "total": len(results),
            "count": count,
            "offset": offset,
            "results": results
        }, status=status.HTTP_200_OK)
        
    except ValueError as e:
        return Response({"error": f"Invalid parameter: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
    except FHIRServiceException as e:
        logger.error(f"FHIR error searching observations: {str(e)}")
        return Response({"error": str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    except Exception as e:
        logger.error(f"Error searching observations: {str(e)}")
        return Response({"error": "Erro ao buscar observações"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def search_conditions(request):
    """
    Advanced condition search with FHIR R4 compliant parameters.
    
    GET /api/v1/conditions/search/
    
    Query Parameters:
        - patient: Filter by patient ID
        - code: Filter by SNOMED CT code
        - clinical-status: Filter by clinical status (active, inactive, resolved)
        - _count: Number of results per page (default: 20, max: 100)
        - _getpagesoffset: Pagination offset
    
    Examples:
        /api/v1/conditions/search/?patient=patient-123
        /api/v1/conditions/search/?clinical-status=active
        /api/v1/conditions/search/?code=38341003
    """
    try:
        fhir_service = FHIRService(request.user)
        params = {}
        
        # Patient filter
        if request.query_params.get('patient'):
            params['patient'] = request.query_params['patient']
        
        # SNOMED CT code filter
        if request.query_params.get('code'):
            params['code'] = request.query_params['code']
        
        # Clinical status filter
        if request.query_params.get('clinical-status'):
            valid_statuses = ['active', 'recurrence', 'relapse', 'inactive', 'remission', 'resolved']
            clinical_status = request.query_params['clinical-status'].lower()
            if clinical_status in valid_statuses:
                params['clinical-status'] = clinical_status
            else:
                return Response({
                    "error": f"Invalid clinical-status. Must be one of: {', '.join(valid_statuses)}"
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Pagination
        count = min(int(request.query_params.get('_count', 20)), 100)
        offset = int(request.query_params.get('_getpagesoffset', 0))
        params['_count'] = str(count)
        if offset > 0:
            params['_getpagesoffset'] = str(offset)
        
        # Execute search
        results = fhir_service.search_resources('Condition', params)
        
        return Response({
            "total": len(results),
            "count": count,
            "offset": offset,
            "results": results
        }, status=status.HTTP_200_OK)
        
    except ValueError as e:
        return Response({"error": f"Invalid parameter: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
    except FHIRServiceException as e:
        logger.error(f"FHIR error searching conditions: {str(e)}")
        return Response({"error": str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    except Exception as e:
        logger.error(f"Error searching conditions: {str(e)}")
        return Response({"error": "Erro ao buscar condições"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def search_practitioners(request):
    """
    Advanced practitioner search with FHIR R4 compliant parameters.
    
    GET /api/v1/practitioners/search/
    
    Query Parameters:
        - name: Filter by practitioner name (partial match)
        - identifier: Filter by identifier (e.g., CRM number)
        - specialty: Filter by specialty code
        - active: Filter by active status (true/false)
        - organization: Filter by organization ID
        - _count: Number of results per page (default: 20, max: 100)
        - _getpagesoffset: Pagination offset
    
    Examples:
        /api/v1/practitioners/search/?name=Silva
        /api/v1/practitioners/search/?identifier=CRM12345
        /api/v1/practitioners/search/?specialty=cardiology
        /api/v1/practitioners/search/?active=true
    """
    try:
        fhir_service = FHIRService(request.user)
        params = {}
        
        # Name filter (partial match)
        if request.query_params.get('name'):
            params['name'] = request.query_params['name']
        
        # Identifier filter (CRM, CPF, etc.)
        if request.query_params.get('identifier'):
            params['identifier'] = request.query_params['identifier']
        
        # Specialty filter (searches in PractitionerRole)
        if request.query_params.get('specialty'):
            params['specialty'] = request.query_params['specialty']
        
        # Active status filter
        if request.query_params.get('active'):
            active_val = request.query_params['active'].lower()
            if active_val in ['true', 'false']:
                params['active'] = active_val
            else:
                return Response({
                    "error": "Invalid active value. Must be 'true' or 'false'"
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Organization filter
        if request.query_params.get('organization'):
            params['organization'] = request.query_params['organization']
        
        # Pagination
        count = min(int(request.query_params.get('_count', 20)), 100)
        offset = int(request.query_params.get('_getpagesoffset', 0))
        params['_count'] = str(count)
        if offset > 0:
            params['_getpagesoffset'] = str(offset)
        
        # Execute search
        results = fhir_service.search_resources('Practitioner', params)
        
        return Response({
            "total": len(results),
            "count": count,
            "offset": offset,
            "results": results
        }, status=status.HTTP_200_OK)
        
    except ValueError as e:
        return Response({"error": f"Invalid parameter: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
    except FHIRServiceException as e:
        logger.error(f"FHIR error searching practitioners: {str(e)}")
        return Response({"error": str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    except Exception as e:
        logger.error(f"Error searching practitioners: {str(e)}")
        return Response({"error": "Erro ao buscar profissionais"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
