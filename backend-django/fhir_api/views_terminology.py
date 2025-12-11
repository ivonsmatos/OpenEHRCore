"""
Sprint 21: Terminology API Endpoints

Provides REST API endpoints for:
- RxNorm medication search and interactions
- ICD-10 diagnosis code lookup
- TUSS procedure code lookup
- ICD-10 ↔ SNOMED CT mapping
"""

import logging
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .authentication import KeycloakAuthentication
from .services.terminology_service import (
    TerminologyService,
    ICD10Service,
    TUSSService,
    TerminologyMappingService
)

logger = logging.getLogger(__name__)


# ============================================================================
# RxNorm Endpoints
# ============================================================================

@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def search_rxnorm(request):
    """
    Search RxNorm for medications by name.
    
    GET /api/v1/terminology/rxnorm/search/
    
    Query Parameters:
        - q: Search term (medication name) - REQUIRED
        - max: Maximum results (default: 20, max: 50)
    
    Examples:
        /api/v1/terminology/rxnorm/search/?q=aspirin
        /api/v1/terminology/rxnorm/search/?q=metformin&max=10
    """
    try:
        term = request.query_params.get('q', '').strip()
        if not term:
            return Response({
                "error": "Query parameter 'q' is required"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        max_results = min(int(request.query_params.get('max', 20)), 50)
        
        results = TerminologyService.search_rxnorm(term, max_results)
        
        return Response({
            "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
            "query": term,
            "total": len(results),
            "results": results
        }, status=status.HTTP_200_OK)
        
    except ValueError as e:
        return Response({"error": f"Invalid parameter: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Error searching RxNorm: {str(e)}")
        return Response({"error": "Erro ao buscar medicamentos"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def get_rxnorm_details(request, rxcui):
    """
    Get detailed information for an RxNorm concept.
    
    GET /api/v1/terminology/rxnorm/{rxcui}/
    
    Path Parameters:
        - rxcui: RxNorm Concept Unique Identifier
    
    Example:
        /api/v1/terminology/rxnorm/1191/
    """
    try:
        details = TerminologyService.get_rxnorm_details(rxcui)
        
        if not details:
            return Response({
                "error": f"RxCUI {rxcui} not found"
            }, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
            **details
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error getting RxNorm details: {str(e)}")
        return Response({"error": "Erro ao buscar detalhes do medicamento"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def get_rxnorm_interactions(request, rxcui):
    """
    Get drug interactions for an RxNorm concept.
    
    GET /api/v1/terminology/rxnorm/{rxcui}/interactions/
    
    Path Parameters:
        - rxcui: RxNorm Concept Unique Identifier
    
    Example:
        /api/v1/terminology/rxnorm/1191/interactions/
    """
    try:
        interactions = TerminologyService.get_rxnorm_interactions(rxcui)
        
        return Response({
            "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
            "rxcui": rxcui,
            "total": len(interactions),
            "interactions": interactions
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error getting RxNorm interactions: {str(e)}")
        return Response({"error": "Erro ao buscar interações"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def check_multi_interactions(request):
    """
    Check interactions between multiple drugs.
    
    POST /api/v1/terminology/rxnorm/interactions/check/
    
    Request Body:
        {
            "rxcuis": ["1191", "4917", "8076"]
        }
    
    Returns interactions between the provided drugs.
    """
    try:
        rxcuis = request.data.get('rxcuis', [])
        
        if not rxcuis or len(rxcuis) < 2:
            return Response({
                "error": "At least 2 RxCUIs are required"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if len(rxcuis) > 10:
            return Response({
                "error": "Maximum 10 RxCUIs allowed"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        interactions = TerminologyService.check_multi_drug_interactions(rxcuis)
        
        return Response({
            "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
            "rxcuis": rxcuis,
            "total": len(interactions),
            "has_interactions": len(interactions) > 0,
            "interactions": interactions
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error checking multi-drug interactions: {str(e)}")
        return Response({"error": "Erro ao verificar interações"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================================================
# ICD-10 Endpoints
# ============================================================================

@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def search_icd10(request):
    """
    Search ICD-10 codes by description or code.
    
    GET /api/v1/terminology/icd10/search/
    
    Query Parameters:
        - q: Search term (code or description) - REQUIRED
        - max: Maximum results (default: 20, max: 50)
    
    Examples:
        /api/v1/terminology/icd10/search/?q=diabetes
        /api/v1/terminology/icd10/search/?q=I10
    """
    try:
        term = request.query_params.get('q', '').strip()
        if not term:
            return Response({
                "error": "Query parameter 'q' is required"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        max_results = min(int(request.query_params.get('max', 20)), 50)
        
        results = ICD10Service.search(term, max_results)
        
        return Response({
            "system": "http://hl7.org/fhir/sid/icd-10",
            "query": term,
            "total": len(results),
            "results": results
        }, status=status.HTTP_200_OK)
        
    except ValueError as e:
        return Response({"error": f"Invalid parameter: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Error searching ICD-10: {str(e)}")
        return Response({"error": "Erro ao buscar códigos CID-10"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def validate_icd10(request, code):
    """
    Validate an ICD-10 code and get its details.
    
    GET /api/v1/terminology/icd10/{code}/
    
    Path Parameters:
        - code: ICD-10 code to validate (e.g., I10, E11.9)
    
    Example:
        /api/v1/terminology/icd10/I10/
    """
    try:
        result = ICD10Service.validate(code)
        
        if not result:
            return Response({
                "code": code,
                "valid": False,
                "error": f"ICD-10 code '{code}' not found"
            }, status=status.HTTP_404_NOT_FOUND)
        
        return Response(result, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error validating ICD-10: {str(e)}")
        return Response({"error": "Erro ao validar código CID-10"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================================================
# TUSS Endpoints
# ============================================================================

@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def search_tuss(request):
    """
    Search TUSS codes by description or code.
    
    GET /api/v1/terminology/tuss/search/
    
    Query Parameters:
        - q: Search term (code or description) - REQUIRED
        - type: Filter by type (consulta, exame, imagem, cirurgia, terapia, procedimento)
        - max: Maximum results (default: 20, max: 50)
    
    Examples:
        /api/v1/terminology/tuss/search/?q=hemograma
        /api/v1/terminology/tuss/search/?q=consulta&type=consulta
    """
    try:
        term = request.query_params.get('q', '').strip()
        if not term:
            return Response({
                "error": "Query parameter 'q' is required"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        procedure_type = request.query_params.get('type')
        max_results = min(int(request.query_params.get('max', 20)), 50)
        
        results = TUSSService.search(term, procedure_type, max_results)
        
        return Response({
            "system": "http://www.ans.gov.br/tuss",
            "query": term,
            "type_filter": procedure_type,
            "total": len(results),
            "results": results
        }, status=status.HTTP_200_OK)
        
    except ValueError as e:
        return Response({"error": f"Invalid parameter: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Error searching TUSS: {str(e)}")
        return Response({"error": "Erro ao buscar códigos TUSS"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def validate_tuss(request, code):
    """
    Validate a TUSS code and get its details.
    
    GET /api/v1/terminology/tuss/{code}/
    
    Path Parameters:
        - code: TUSS code to validate
    
    Example:
        /api/v1/terminology/tuss/40301010/
    """
    try:
        result = TUSSService.validate(code)
        
        if not result:
            return Response({
                "code": code,
                "valid": False,
                "error": f"TUSS code '{code}' not found"
            }, status=status.HTTP_404_NOT_FOUND)
        
        return Response(result, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error validating TUSS: {str(e)}")
        return Response({"error": "Erro ao validar código TUSS"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def list_tuss_by_type(request, procedure_type):
    """
    List all TUSS codes of a specific type.
    
    GET /api/v1/terminology/tuss/type/{procedure_type}/
    
    Path Parameters:
        - procedure_type: consulta, exame, imagem, cirurgia, terapia, procedimento
    
    Query Parameters:
        - max: Maximum results (default: 50)
    
    Example:
        /api/v1/terminology/tuss/type/exame/
    """
    try:
        valid_types = ['consulta', 'exame', 'imagem', 'cirurgia', 'terapia', 'procedimento']
        if procedure_type not in valid_types:
            return Response({
                "error": f"Invalid type. Must be one of: {', '.join(valid_types)}"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        max_results = min(int(request.query_params.get('max', 50)), 100)
        
        results = TUSSService.get_by_type(procedure_type, max_results)
        
        return Response({
            "system": "http://www.ans.gov.br/tuss",
            "type": procedure_type,
            "total": len(results),
            "results": results
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error listing TUSS by type: {str(e)}")
        return Response({"error": "Erro ao listar códigos TUSS"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================================================
# Terminology Mapping Endpoints
# ============================================================================

@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def map_icd10_to_snomed(request, icd10_code):
    """
    Map ICD-10 code to SNOMED CT.
    
    GET /api/v1/terminology/map/icd10-to-snomed/{icd10_code}/
    
    Path Parameters:
        - icd10_code: ICD-10 code to map
    
    Example:
        /api/v1/terminology/map/icd10-to-snomed/I10/
    """
    try:
        result = TerminologyMappingService.icd10_to_snomed(icd10_code)
        
        if not result:
            return Response({
                "source_code": icd10_code,
                "mapped": False,
                "error": f"No SNOMED CT mapping found for ICD-10 code '{icd10_code}'"
            }, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            "mapped": True,
            **result
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error mapping ICD-10 to SNOMED: {str(e)}")
        return Response({"error": "Erro ao mapear código"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def map_snomed_to_icd10(request, snomed_code):
    """
    Map SNOMED CT code to ICD-10.
    
    GET /api/v1/terminology/map/snomed-to-icd10/{snomed_code}/
    
    Path Parameters:
        - snomed_code: SNOMED CT code to map
    
    Example:
        /api/v1/terminology/map/snomed-to-icd10/38341003/
    """
    try:
        result = TerminologyMappingService.snomed_to_icd10(snomed_code)
        
        if not result:
            return Response({
                "source_code": snomed_code,
                "mapped": False,
                "error": f"No ICD-10 mapping found for SNOMED CT code '{snomed_code}'"
            }, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            "mapped": True,
            **result
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error mapping SNOMED to ICD-10: {str(e)}")
        return Response({"error": "Erro ao mapear código"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
