from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .auth import KeycloakAuthentication
from .services.fhir_core import FHIRService

import logging

logger = logging.getLogger(__name__)

@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def list_visitors(request):
    """
    Listar visitantes (RelatedPerson).
    Pode filtrar por paciente: ?patient_id=UUID
    """
    patient_id = request.query_params.get('patient_id')
    
    try:
        fhir = FHIRService()
        if patient_id:
            # Search by patient reference
            # Note: FHIR param for RelatedPerson patient is 'patient'
            resources = fhir.search_resources('RelatedPerson', {'patient': patient_id})
        else:
            # Search recent
            resources = fhir.search_resources('RelatedPerson', {'_count': 50})
            
        visitors = []
        for res in resources:
            # Parse human readable format
            name = "Unknown"
            if res.get('name'):
                name_obj = res['name'][0]
                given = " ".join(name_obj.get('given', []))
                family = name_obj.get('family', '')
                name = f"{given} {family}".strip()
                
            relationship = "Visitante"
            if res.get('relationship'):
                relationship = res['relationship'][0].get('text') or res['relationship'][0]['coding'][0]['display']
                
            contact = ""
            if res.get('telecom'):
                contact = res['telecom'][0].get('value', '')

            patient_ref = res.get('patient', {}).get('reference', '')
            pid = patient_ref.split('/')[-1] if patient_ref else None

            visitors.append({
                "id": res.get('id'),
                "name": name,
                "relationship": relationship,
                "contact": contact,
                "patient_id": pid
            })
            
        return Response(visitors, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error listing visitors: {e}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def create_visitor(request):
    """
    Registrar novo visitante.
    Payload: { name, relationship, phone, patient_id }
    """
    data = request.data
    patient_id = data.get('patient_id')
    name = data.get('name')
    relationship = data.get('relationship', 'Visitor')
    phone = data.get('phone')
    
    if not patient_id or not name:
        return Response({"error": "patient_id and name are required"}, status=status.HTTP_400_BAD_REQUEST)
        
    try:
        fhir = FHIRService()
        
        # Build RelatedPerson resource
        related_person = {
            "resourceType": "RelatedPerson",
            "active": True,
            "patient": {
                "reference": f"Patient/{patient_id}"
            },
            "name": [{
                "use": "official",
                "text": name,
                "family": name.split()[-1] if ' ' in name else name,
                "given": name.split()[:-1] if ' ' in name else [name]
            }],
            "relationship": [{
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/v3-RoleCode",
                    "code": "V", # Generic Visitor
                    "display": relationship
                }],
                "text": relationship
            }],
            "telecom": []
        }
        
        if phone:
            related_person["telecom"].append({
                "system": "phone",
                "value": phone,
                "use": "mobile"
            })
            
        result = fhir.create_resource("RelatedPerson", related_person)
        if result:
            return Response(result, status=status.HTTP_201_CREATED)
        else:
            return Response({"error": "Failed to create resource"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    except Exception as e:
        logger.error(f"Error creating visitor: {e}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
