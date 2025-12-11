
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework import status
from .auth import KeycloakAuthentication
from rest_framework.permissions import IsAuthenticated
from .services.fhir_core import FHIRService
from .services.ai_service import AIService
import logging

logger = logging.getLogger(__name__)

@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def get_patient_summary(request, patient_id):
    """
    Gera um resumo clínico inteligente do paciente usando IA (Simulada).
    GET /api/v1/ai/summary/{patient_id}/
    """
    try:
        # 1. Recuperar dados do paciente via FHIRService
        fhir_service = FHIRService(request.user)
        patient = fhir_service.get_patient_by_id(patient_id)
        
        if not patient:
            return Response({"error": "Paciente não encontrado"}, status=status.HTTP_404_NOT_FOUND)
            
        # 2. Recuperar histórico relevante (simplificado)
        # TODO: Adicionar MedicationRequest, Condition, etc.
        try:
            conditions = fhir_service.search_resources("Condition", {"patient": patient_id})
        except:
            conditions = []
            
        try:
            medications = fhir_service.search_resources("MedicationRequest", {"patient": patient_id, "status": "active"})
        except:
            medications = []

        # Montar objeto de dados para o AIService
        patient_data = {
            "name": f"{patient.get('name', [{}])[0].get('given', [''])[0]} {patient.get('name', [{}])[0].get('family', '')}",
            "age": "Desconhecida", # TODO: Calcular idade real
            "gender": patient.get("gender", "unknown"),
            "conditions": conditions,
            "medications": medications
        }
        
        # 3. Gerar resumo
        ai_service = AIService(request.user)
        summary = ai_service.generate_patient_summary(patient_data)
        
        return Response({"summary": summary}, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Erro ao gerar resumo IA: {str(e)}")
        return Response({"error": f"Erro interno: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def check_interactions(request):
    """
    Verifica interações medicamentosas.
    POST /api/v1/ai/interactions
    Body: { "new_medication": "Aspirina", "current_medications": [...] }
    """
    try:
        new_medication = request.data.get('new_medication')
        # current_medications can be passed directly or fetched from DB if patient_id provided
        # For this endpoint, let's allow passing the list direct or patient_id
        patient_id = request.data.get('patient_id')
        
        fhir_service = FHIRService(request.user)
        current_medications = []
        
        if patient_id:
            try:
                current_medications = fhir_service.search_resources("MedicationRequest", {"patient": patient_id, "status": "active"})
            except:
                pass
        
        ai_service = AIService(request.user)
        alerts = ai_service.check_drug_interactions(new_medication, current_medications)
        
        return Response({"alerts": alerts}, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Erro ao checar interações: {str(e)}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
