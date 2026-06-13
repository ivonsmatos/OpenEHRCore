from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .services.fhir_core import FHIRService, FHIRServiceException
from .services.ai_service import AIService
from .utils.validators import validate_patient_id, calculate_age
from .utils.logging_utils import sanitize_for_log
import logging
from datetime import datetime
import requests

logger = logging.getLogger(__name__)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_patient_summary(request, patient_id):
    """
    Gera um resumo clínico SEMPRE FRESCO usando IA (SEM CACHE).
    
    GET /api/v1/ai/summary/{patient_id}/
    
    Returns:
        200: {"summary": "...", "using_ai": bool, "timestamp": "..."}
        400: Validation error
        404: Patient not found
        500: Internal server error
    """
    
    logger.info(f"🔥 Gerando NOVO resumo para paciente {patient_id}")
    
    # VALIDAÇÃO
    if not validate_patient_id(patient_id):
        return Response(
            {"error": "Invalid patient ID format"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # BUSCAR DADOS DO FHIR
    fhir_service = FHIRService(request.user)
    
    try:
        patient = fhir_service.get_patient_by_id(patient_id)
    except FHIRServiceException as e:
        error_str = str(e).lower()
        if "not found" in error_str or "404" in error_str:
            return Response(
                {"error": "Patient not found", "patient_id": patient_id},
                status=status.HTTP_404_NOT_FOUND
            )
        return Response(
            {"error": "Failed to retrieve patient data"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    # CALCULAR IDADE
    birth_date = patient.get("birthDate")
    age = calculate_age(birth_date)
    age_display = str(age) if age is not None else "Desconhecida"
    
    # BUSCAR RECURSOS FHIR
    def fetch_safe(resource_type: str, params: dict) -> list:
        try:
            return fhir_service.search_resources(resource_type, params)
        except Exception as e:
            logger.warning(f"Falha ao buscar {resource_type} para {patient_id}: {e}")
            return []
    
    conditions = fetch_safe("Condition", {"patient": patient_id})
    medications = fetch_safe("MedicationRequest", {"patient": patient_id, "status": "active"})
    observations = fetch_safe("Observation", {"patient": patient_id, "category": "vital-signs", "_count": "15", "_sort": "-date"})
    immunizations = fetch_safe("Immunization", {"patient": patient_id, "_count": "20", "_sort": "-date"})
    diagnostic_reports = fetch_safe("DiagnosticReport", {"patient": patient_id, "_count": "10", "_sort": "-date"})
    appointments = fetch_safe("Appointment", {"patient": patient_id, "_count": "10", "_sort": "-date"})
    
    # MONTAR DADOS
    patient_names = patient.get('name', [{}])
    first_name = patient_names[0].get('given', [''])[0] if patient_names else ''
    family_name = patient_names[0].get('family', '') if patient_names else ''
    full_name = f"{first_name} {family_name}".strip() or "Nome não disponível"
    
    patient_data = {
        "name": full_name,
        "age": age_display,
        "gender": patient.get("gender", "unknown"),
        "conditions": conditions,
        "medications": medications,
        "vital_signs": observations,
        "immunizations": immunizations,
        "diagnostic_reports": diagnostic_reports,
        "appointments": appointments
    }
    
    # GERAR RESUMO COM IA
    ai_service = AIService(request.user)
    
    try:
        result = ai_service.generate_patient_summary(patient_data)
        summary = result['summary']
        using_ai = result['using_ai']
        
        logger.info(f"✅ Resumo gerado: {len(summary)} chars | AI={using_ai}")
        
        return Response({
            "summary": summary,
            "using_ai": using_ai,
            "timestamp": datetime.now().isoformat()
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Erro ao gerar resumo: {e}")
        return Response({
            "summary": f"Erro: {str(e)}",
            "using_ai": False,
            "timestamp": datetime.now().isoformat()
        }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def check_interactions(request):
    """Verifica interações medicamentosas."""
    try:
        new_medication = request.data.get('new_medication')
        if not new_medication:
            return Response({"error": "new_medication is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        patient_id = request.data.get('patient_id')
        current_medications = request.data.get('current_medications', [])
        
        if patient_id:
            if not validate_patient_id(patient_id):
                return Response({"error": "Invalid patient_id"}, status=status.HTTP_400_BAD_REQUEST)
            
            fhir_service = FHIRService(request.user)
            try:
                current_medications = fhir_service.search_resources("MedicationRequest", {"patient": patient_id, "status": "active"})
            except Exception as e:
                logger.warning(f"Falha ao buscar medicações de {patient_id}: {e}")
                current_medications = []
        
        ai_service = AIService(request.user)
        alerts = ai_service.check_drug_interactions(new_medication, current_medications)
        
        return Response({"alerts": alerts}, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Erro ao checar interações: {e}")
        return Response({"error": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def clinical_assistant(request):
    """
    Assistente clínico (RAG sobre os manuais). APOIO À DECISÃO — o médico decide.

    POST /api/v1/ai/assistant/  { "question": "..." }
    Retorna: { "answer": str, "sources": [...], "grounded": bool }
    """
    question = (request.data.get('question') or '').strip()
    if not question:
        return Response({"error": "question is required"}, status=status.HTTP_400_BAD_REQUEST)

    from .services import rag_service
    try:
        result = rag_service.answer(question)
        return Response(result, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Erro no assistente clínico: {e}")
        return Response({"error": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
