
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_audit_logs(request):
    """
    Lista logs de auditoria (Provenance).
    Query param: target (ex: Patient/123)
    """
    target = request.query_params.get('target')
    if not target:
        return Response({"error": "Target parameter is required"}, status=status.HTTP_400_BAD_REQUEST)
        
    try:
        # Busca direta no HAPI FHIR via Service ou Request simples
        # Como Provenance é read-only para o frontend, podemos fazer um proxy simples
        
        fhir_url = settings.FHIR_SERVER_URL
        response = requests.get(
            f"{fhir_url}/Provenance",
            params={"target": target, "_sort": "-_lastUpdated"},
            headers={'Accept': 'application/fhir+json'},
            timeout=10
        )
        
        if response.status_code == 200:
            bundle = response.json()
            logs = []
            if "entry" in bundle:
                for entry in bundle["entry"]:
                    if "resource" in entry:
                        logs.append(entry["resource"])
            return Response(logs, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Failed to fetch audit logs"}, status=response.status_code)
            
    except Exception as e:
        logger.error(f"Error fetching audit logs: {str(e)}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
