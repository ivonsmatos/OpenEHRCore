
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.http import HttpResponse
import json
import logging

from .services.fhir_core import FHIRService, FHIRServiceException

logger = logging.getLogger(__name__)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_patient_data_view(request, patient_id):
    """
    Exporta todos os dados do paciente em formato FHIR Bundle (JSON).
    GET /api/v1/patients/{id}/export/
    """
    try:
        logger.info(f"Export requested for Patient {patient_id} by {request.user}")
        
        # Validar acesso (Se for paciente, só pode exportar o dele mesmo)
        # TODO: Implementar essa validação fina se necessário. Por enquanto, IsAuthenticated.
        
        fhir_service = FHIRService(request.user)
        bundle = fhir_service.export_patient_data(patient_id)
        
        # Retornar como arquivo para download
        response = HttpResponse(
            json.dumps(bundle, indent=2), 
            content_type='application/json'
        )
        response['Content-Disposition'] = f'attachment; filename="patient_{patient_id}_export.json"'
        
        return response
        
    except FHIRServiceException as e:
        logger.error(f"Export service error: {str(e)}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        logger.error(f"Unexpected error in export: {str(e)}")
        return Response({"error": "Failed to export data"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
