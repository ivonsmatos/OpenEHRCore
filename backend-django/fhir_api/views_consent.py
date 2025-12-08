from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime
from .services.fhir_core import FHIRService
import logging

logger = logging.getLogger(__name__)

@api_view(['POST'])
# @permission_classes([IsAuthenticated]) 
def create_consent(request):
    try:
        service = FHIRService()
        data = request.data
        
        patient_id = data.get('patient_id')
        if not patient_id:
            return Response({"error": "patient_id is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        resource = {
            "resourceType": "Consent",
            "status": "active",
            "scope": {
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/consentscope",
                    "code": "patient-privacy",
                    "display": "Privacy Consent"
                }]
            },
            "category": [{
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                    "code": "INFA",
                    "display": "information access"
                }]
            }],
            "patient": {"reference": f"Patient/{patient_id}"},
            "dateTime": datetime.now().isoformat(),
            "organization": [{"display": "OpenEHRCore Hospital"}],
            "policyRule": {
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/consentpolicycodes",
                    "code": "openehr-lgpd-v1",
                    "display": "General Data Protection Consent"
                }]
            },
            "provision": {
                "type": "permit",
                "period": {
                    "start": datetime.now().isoformat()
                }
            }
        }
        
        result = service.create_resource("Consent", resource)
        return Response(result, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Error creating consent: {str(e)}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def list_consents(request):
    try:
        service = FHIRService()
        params = {}
        
        patient_id = request.query_params.get('patient')
        if patient_id:
            params['patient'] = f"Patient/{patient_id}" if not patient_id.startswith('Patient/') else patient_id
            
        results = service.search_resources("Consent", params)
        return Response(results, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error listing consents: {str(e)}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
