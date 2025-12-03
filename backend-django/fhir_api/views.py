"""
Django REST Views para a API FHIR.

Expõe endpoints que manipulam recursos FHIR através do FHIRService.
"""

import logging
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from .services.fhir_core import FHIRService, FHIRServiceException


logger = logging.getLogger(__name__)


@api_view(['GET'])
def health_check(request):
    """
    Verifica se toda a stack está saudável.
    
    GET /api/v1/health/
    
    Returns:
        {
            "status": "ok",
            "fhir_server": "healthy",
            "timestamp": "2024-01-01T00:00:00Z"
        }
    """
    try:
        fhir_service = FHIRService()
        fhir_service.health_check()
        
        return Response({
            "status": "ok",
            "fhir_server": "healthy",
            "message": "HAPI FHIR and infrastructure are operational"
        }, status=status.HTTP_200_OK)
    except FHIRServiceException as e:
        return Response({
            "status": "error",
            "fhir_server": "unhealthy",
            "error": str(e)
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)


@api_view(['POST'])
def create_patient(request):
    """
    Cria um novo paciente no sistema.
    
    POST /api/v1/patients/
    
    Body:
    {
        "first_name": "João",
        "last_name": "Silva",
        "birth_date": "1990-05-15",
        "cpf": "12345678901",
        "gender": "male",
        "telecom": [
            {"system": "phone", "value": "(11) 99999-9999"},
            {"system": "email", "value": "joao@example.com"}
        ]
    }
    
    Returns:
        {
            "resourceType": "Patient",
            "id": "patient-123",
            "name": "João Silva",
            "cpf": "12345678901",
            "birthDate": "1990-05-15",
            "gender": "male",
            "created_at": "2024-01-01T00:00:00Z"
        }
    """
    try:
        data = request.data
        
        # Validar campos obrigatórios
        required_fields = ['first_name', 'last_name', 'birth_date']
        for field in required_fields:
            if field not in data:
                return Response({
                    "error": f"Campo obrigatório ausente: {field}"
                }, status=status.HTTP_400_BAD_REQUEST)
        
        fhir_service = FHIRService()
        
        result = fhir_service.create_patient_resource(
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            birth_date=data.get('birth_date'),
            cpf=data.get('cpf'),
            gender=data.get('gender'),
            telecom=data.get('telecom'),
        )
        
        return Response(result, status=status.HTTP_201_CREATED)
    
    except FHIRServiceException as e:
        logger.error(f"FHIR error creating patient: {str(e)}")
        return Response({
            "error": str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Unexpected error creating patient: {str(e)}")
        return Response({
            "error": "Erro interno ao criar paciente"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_patient(request, patient_id):
    """
    Recupera um paciente pelo ID.
    
    GET /api/v1/patients/{patient_id}/
    
    Returns:
        {
            "resourceType": "Patient",
            "id": "patient-123",
            "name": [...],
            "birthDate": "1990-05-15",
            ...
        }
    """
    try:
        fhir_service = FHIRService()
        patient = fhir_service.get_patient_by_id(patient_id)
        
        return Response(patient, status=status.HTTP_200_OK)
    
    except FHIRServiceException as e:
        return Response({
            "error": str(e)
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error retrieving patient: {str(e)}")
        return Response({
            "error": "Erro ao recuperar paciente"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def create_encounter(request):
    """
    Cria um novo encontro (consulta/internação) para um paciente.
    
    POST /api/v1/encounters/
    
    Body:
    {
        "patient_id": "patient-123",
        "encounter_type": "consultation",
        "status": "finished",
        "period_start": "2024-01-01T10:00:00Z",
        "period_end": "2024-01-01T11:00:00Z",
        "reason_code": "fever"
    }
    """
    try:
        data = request.data
        
        if 'patient_id' not in data:
            return Response({
                "error": "Campo obrigatório ausente: patient_id"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        fhir_service = FHIRService()
        
        result = fhir_service.create_encounter_resource(
            patient_id=data.get('patient_id'),
            encounter_type=data.get('encounter_type', 'unknown'),
            status=data.get('status', 'finished'),
            period_start=data.get('period_start'),
            period_end=data.get('period_end'),
            reason_code=data.get('reason_code'),
        )
        
        return Response(result, status=status.HTTP_201_CREATED)
    
    except FHIRServiceException as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Error creating encounter: {str(e)}")
        return Response({"error": "Erro ao criar encontro"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def create_observation(request):
    """
    Cria uma nova observação (resultado de teste) para um paciente.
    
    POST /api/v1/observations/
    
    Body:
    {
        "patient_id": "patient-123",
        "code": "8480-6",  # LOINC code para pressão sistólica
        "value": "120",
        "status": "final"
    }
    """
    try:
        data = request.data
        
        required_fields = ['patient_id', 'code', 'value']
        for field in required_fields:
            if field not in data:
                return Response({
                    "error": f"Campo obrigatório ausente: {field}"
                }, status=status.HTTP_400_BAD_REQUEST)
        
        fhir_service = FHIRService()
        
        result = fhir_service.create_observation_resource(
            patient_id=data.get('patient_id'),
            code=data.get('code'),
            value=data.get('value'),
            status=data.get('status', 'final'),
        )
        
        return Response(result, status=status.HTTP_201_CREATED)
    
    except FHIRServiceException as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Error creating observation: {str(e)}")
        return Response({"error": "Erro ao criar observação"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
