"""
View temporária para testar IA sem autenticação
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse
from .services.ai_service import AIService
from datetime import datetime
import requests
import logging

logger = logging.getLogger(__name__)

FHIR_SERVER_URL = 'http://localhost:8080/fhir'

@api_view(['GET'])
@permission_classes([AllowAny])
def test_ai_summary(request, patient_id):
    """
    Endpoint de teste da IA sem autenticação
    GET /api/v1/ai/test-summary/<patient_id>/
    """
    try:
        start_time = datetime.now()
        
        # Buscar dados do FHIR Server diretamente
        patient = requests.get(f'{FHIR_SERVER_URL}/Patient/{patient_id}').json()
        
        def fetch_resource(resource_type, params=None):
            try:
                url = f'{FHIR_SERVER_URL}/{resource_type}'
                response = requests.get(url, params=params or {}, timeout=10)
                if response.status_code == 200:
                    return response.json()
                return {'entry': []}
            except:
                return {'entry': []}
        
        # Coletar todos os dados
        patient_data = {
            "patient": patient,
            "conditions": fetch_resource("Condition", {"patient": patient_id}),
            "medications": fetch_resource("MedicationRequest", {"patient": patient_id}),
            "observations": fetch_resource("Observation", {"patient": patient_id, "_count": "100"}),
            "allergies": fetch_resource("AllergyIntolerance", {"patient": patient_id}),
            "procedures": fetch_resource("Procedure", {"patient": patient_id}),
            "immunizations": fetch_resource("Immunization", {"patient": patient_id}),
            "diagnostic_reports": fetch_resource("DiagnosticReport", {"patient": patient_id}),
            "appointments": fetch_resource("Appointment", {"patient": patient_id})
        }
        
        # Gerar resumo com IA
        ai_service = AIService()
        summary = ai_service.generate_clinical_summary(patient_data)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return Response({
            "summary": summary,
            "model": ai_service.model_name,
            "processing_time": round(processing_time, 2),
            "patient_id": patient_id,
            "data_collected": {
                "conditions": len(patient_data["conditions"].get("entry", [])),
                "medications": len(patient_data["medications"].get("entry", [])),
                "observations": len(patient_data["observations"].get("entry", [])),
                "immunizations": len(patient_data["immunizations"].get("entry", [])),
                "diagnostic_reports": len(patient_data["diagnostic_reports"].get("entry", [])),
                "appointments": len(patient_data["appointments"].get("entry", []))
            }
        })
        
    except Exception as e:
        logger.error(f"Erro ao gerar resumo AI: {e}")
        return JsonResponse(
            {'error': str(e)},
            status=500
        )
