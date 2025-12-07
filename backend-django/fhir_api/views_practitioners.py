"""
Views for Practitioner (Healthcare Professional) management
FHIR R4 Compliant
"""
import logging
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .services.fhir_core import FHIRService
from .auth import KeycloakAuthentication, IsAuthenticated

logger = logging.getLogger(__name__)


@api_view(['POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def create_practitioner(request):
    """
    Create a new Practitioner (Healthcare Professional)
    
    FHIR R4 Compliant - Creates Practitioner resource
    
    POST /api/v1/practitioners/
    
    Body:
    {
        "family_name": "Santos",
        "given_names": ["Maria", "da", "Silva"],
        "prefix": "Dra.",
        "gender": "female",
        "birthDate": "1985-03-20",
        "phone": "(11) 3456-7890",
        "email": "maria.santos@hospital.com",
        "crm": "CRM-SP-123456",  # Brazilian medical license
        "qualification_code": "MD",
        "qualification_display": "Médica Cardiologista"
    }
    
    Returns:
    {
        "id": "practitioner-123",
        "resourceType": "Practitioner",
        "name": "Dra. Maria Santos",
        ...
    }
    """
    try:
        data = request.data
        
        # Validate required fields
        required = ['family_name', 'given_names']
        for field in required:
            if field not in data:
                return Response(
                    {"error": f"Campo obrigatório ausente: {field}"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        fhir = FHIRService()
        
        # Build FHIR Practitioner resource
        practitioner = {
            "resourceType": "Practitioner",
            "active": True,
            "name": [{
                "use": "official",
                "family": data['family_name'],
                "given": data['given_names'] if isinstance(data['given_names'], list) else [data['given_names']]
            }],
            "gender": data.get('gender', 'unknown'),
        }
        
        # Add prefix if provided
        if data.get('prefix'):
            practitioner['name'][0]['prefix'] = [data['prefix']]
        
        # Add birthDate if provided
        if data.get('birthDate'):
            practitioner['birthDate'] = data['birthDate']
        
        # Add telecom
        telecom = []
        if data.get('phone'):
            telecom.append({
                "system": "phone",
                "value": data['phone'],
                "use": "work"
            })
        if data.get('email'):
            telecom.append({
                "system": "email",
                "value": data['email'],
                "use": "work"
            })
        if telecom:
            practitioner['telecom'] = telecom
        
        # Add Brazilian CRM identifier
        if data.get('crm'):
            practitioner['identifier'] = [{
                "system": "http://hl7.org.br/fhir/r4/NamingSystem/crm",
                "value": data['crm']
            }]
        
        # Add qualification
        if data.get('qualification_code'):
            practitioner['qualification'] = [{
                "code": {
                    "coding": [{
                        "system": "http://terminology.hl7.org/CodeSystem/v2-0360",
                        "code": data.get('qualification_code', 'MD'),
                        "display": data.get('qualification_display', 'Doctor')
                    }],
                    "text": data.get('qualification_display', 'Médico')
                }
            }]
            
            # Add CRM to qualification if provided
            if data.get('crm'):
                practitioner['qualification'][0]['identifier'] = [{
                    "system": "http://hl7.org.br/fhir/r4/NamingSystem/crm",
                    "value": data['crm']
                }]
        
        # Create in FHIR server
        result = fhir.create_resource('Practitioner', practitioner)
        
        return Response(result, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Error creating practitioner: {e}")
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def list_practitioners(request):
    """
    List all practitioners
    
    GET /api/v1/practitioners/
    
    Query params:
    - name: Filter by name
    - active: Filter by active status (true/false)
    """
    try:
        fhir = FHIRService()
        
        # Build search parameters
        params = {}
        if request.GET.get('name'):
            params['name'] = request.GET['name']
        if request.GET.get('active'):
            params['active'] = request.GET['active']
        
        practitioners = fhir.search_resources('Practitioner', params)
        
        return Response({
            "count": len(practitioners),
            "practitioners": practitioners
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error listing practitioners: {e}")
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def get_practitioner(request, practitioner_id):
    """
    Get practitioner by ID
    
    GET /api/v1/practitioners/{id}/
    """
    try:
        fhir = FHIRService()
        practitioner = fhir.get_resource('Practitioner', practitioner_id)
        
        if not practitioner:
            return Response(
                {"error": "Practitioner not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response(practitioner, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error getting practitioner: {e}")
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def create_practitioner_role(request):
    """
    Create PractitionerRole (links practitioner to organization/specialty)
    
    POST /api/v1/practitioner-roles/
    
    Body:
    {
        "practitioner_id": "practitioner-123",
        "organization_id": "organization-1",
        "specialty_code": "394579002",  # SNOMED CT code
        "specialty_display": "Cardiology",
        "location_ids": ["location-1"],
        "available_days": ["mon", "tue", "wed", "thu", "fri"],
        "available_start": "08:00:00",
        "available_end": "17:00:00"
    }
    """
    try:
        data = request.data
        
        if 'practitioner_id' not in data:
            return Response(
                {"error": "practitioner_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        fhir = FHIRService()
        
        # Build PractitionerRole resource
        role = {
            "resourceType": "PractitionerRole",
            "active": True,
            "practitioner": {
                "reference": f"Practitioner/{data['practitioner_id']}"
            }
        }
        
        # Add organization
        if data.get('organization_id'):
            role['organization'] = {
                "reference": f"Organization/{data['organization_id']}"
            }
        
        # Add code (role type)
        role['code'] = [{
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/practitioner-role",
                "code": "doctor",
                "display": "Doctor"
            }]
        }]
        
        # Add specialty
        if data.get('specialty_code'):
            role['specialty'] = [{
                "coding": [{
                    "system": "http://snomed.info/sct",
                    "code": data['specialty_code'],
                    "display": data.get('specialty_display', 'Specialist')
                }]
            }]
        
        # Add locations
        if data.get('location_ids'):
            role['location'] = [
                {"reference": f"Location/{loc_id}"}
                for loc_id in data['location_ids']
            ]
        
        # Add available time
        if data.get('available_days'):
            role['availableTime'] = [{
                "daysOfWeek": data['available_days'],
                "availableStartTime": data.get('available_start', '08:00:00'),
                "availableEndTime": data.get('available_end', '17:00:00')
            }]
        
        # Create in FHIR server
        result = fhir.create_resource('PractitionerRole', role)
        
        return Response(result, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Error creating practitioner role: {e}")
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
