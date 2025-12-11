"""
Views for HealthcareService (Serviços de Saúde) management
FHIR R4 Compliant

HealthcareService representa os serviços oferecidos por uma organização de saúde,
como consultas, exames, procedimentos, etc.
"""
import logging
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response

from .services.fhir_core import FHIRService, FHIRServiceException
from .auth import KeycloakAuthentication, IsAuthenticated

logger = logging.getLogger(__name__)


@api_view(['GET', 'POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def manage_healthcare_services(request):
    """
    List or create HealthcareService resources
    
    GET /api/v1/healthcare-services/
    Query params:
    - organization: Filter by organization ID
    - service-type: Filter by service type code
    - specialty: Filter by specialty code
    - active: Filter by active status (true/false)
    - _count: Number of results (default: 20)
    
    POST /api/v1/healthcare-services/
    Body:
    {
        "organization_id": "org-1",
        "name": "Consulta Cardiológica",
        "type_code": "394579002",
        "type_display": "Cardiologia",
        "specialty_code": "394579002",
        "specialty_display": "Cardiologia",
        "active": true,
        "telecom": [{"system": "phone", "value": "(11) 3456-7890"}],
        "availableTime": [{
            "daysOfWeek": ["mon", "tue", "wed", "thu", "fri"],
            "availableStartTime": "08:00:00",
            "availableEndTime": "18:00:00"
        }],
        "comment": "Consultas especializadas em cardiologia"
    }
    """
    fhir = FHIRService(request.user)
    
    if request.method == 'GET':
        try:
            # Build search params
            params = {}
            
            if request.query_params.get('organization'):
                params['organization'] = request.query_params['organization']
            if request.query_params.get('service-type'):
                params['service-type'] = request.query_params['service-type']
            if request.query_params.get('specialty'):
                params['specialty'] = request.query_params['specialty']
            if request.query_params.get('active'):
                params['active'] = request.query_params['active']
            
            count = int(request.query_params.get('_count', 20))
            params['_count'] = min(count, 100)
            
            # Search in FHIR
            results = fhir.search_resources('HealthcareService', params)
            
            # Format response
            services = []
            for svc in results:
                services.append({
                    'id': svc.get('id'),
                    'resourceType': 'HealthcareService',
                    'name': svc.get('name'),
                    'active': svc.get('active', True),
                    'organization': svc.get('providedBy', {}).get('display'),
                    'organizationId': svc.get('providedBy', {}).get('reference', '').replace('Organization/', ''),
                    'type': svc.get('type', [{}])[0].get('coding', [{}])[0].get('display') if svc.get('type') else None,
                    'specialty': svc.get('specialty', [{}])[0].get('coding', [{}])[0].get('display') if svc.get('specialty') else None,
                    'comment': svc.get('comment'),
                    'telecom': svc.get('telecom', [])
                })
            
            return Response({
                'services': services,
                'total': len(services)
            })
            
        except Exception as e:
            logger.error(f"Error listing healthcare services: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'POST':
        try:
            data = request.data
            
            # Validate required
            if not data.get('name'):
                return Response({'error': 'Campo name é obrigatório'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Build FHIR resource
            healthcare_service = {
                'resourceType': 'HealthcareService',
                'active': data.get('active', True),
                'name': data['name']
            }
            
            # Organization reference
            if data.get('organization_id'):
                healthcare_service['providedBy'] = {
                    'reference': f"Organization/{data['organization_id']}",
                    'display': data.get('organization_name', '')
                }
            
            # Service type
            if data.get('type_code'):
                healthcare_service['type'] = [{
                    'coding': [{
                        'system': 'http://snomed.info/sct',
                        'code': data['type_code'],
                        'display': data.get('type_display', '')
                    }]
                }]
            
            # Specialty
            if data.get('specialty_code'):
                healthcare_service['specialty'] = [{
                    'coding': [{
                        'system': 'http://snomed.info/sct',
                        'code': data['specialty_code'],
                        'display': data.get('specialty_display', '')
                    }]
                }]
            
            # Telecom
            if data.get('telecom'):
                healthcare_service['telecom'] = data['telecom']
            
            # Available time
            if data.get('availableTime'):
                healthcare_service['availableTime'] = data['availableTime']
            
            # Comment
            if data.get('comment'):
                healthcare_service['comment'] = data['comment']
            
            # Location(s)
            if data.get('location_ids'):
                healthcare_service['location'] = [
                    {'reference': f"Location/{loc_id}"} for loc_id in data['location_ids']
                ]
            
            # Create in FHIR
            result = fhir.create_resource('HealthcareService', healthcare_service)
            
            return Response(result, status=status.HTTP_201_CREATED)
            
        except FHIRServiceException as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error creating healthcare service: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'PUT', 'DELETE'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def healthcare_service_detail(request, service_id):
    """
    Get, update or delete a HealthcareService
    
    GET /api/v1/healthcare-services/{id}/
    PUT /api/v1/healthcare-services/{id}/
    DELETE /api/v1/healthcare-services/{id}/
    """
    fhir = FHIRService(request.user)
    
    if request.method == 'GET':
        try:
            result = fhir.get_resource('HealthcareService', service_id)
            return Response(result)
        except FHIRServiceException as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error getting healthcare service: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'PUT':
        try:
            data = request.data
            
            # Get existing
            existing = fhir.get_resource('HealthcareService', service_id)
            
            # Update fields
            if 'name' in data:
                existing['name'] = data['name']
            if 'active' in data:
                existing['active'] = data['active']
            if 'comment' in data:
                existing['comment'] = data['comment']
            if 'telecom' in data:
                existing['telecom'] = data['telecom']
            if 'availableTime' in data:
                existing['availableTime'] = data['availableTime']
            
            # Update organization
            if 'organization_id' in data:
                existing['providedBy'] = {
                    'reference': f"Organization/{data['organization_id']}",
                    'display': data.get('organization_name', '')
                }
            
            # Update type
            if 'type_code' in data:
                existing['type'] = [{
                    'coding': [{
                        'system': 'http://snomed.info/sct',
                        'code': data['type_code'],
                        'display': data.get('type_display', '')
                    }]
                }]
            
            # Update specialty
            if 'specialty_code' in data:
                existing['specialty'] = [{
                    'coding': [{
                        'system': 'http://snomed.info/sct',
                        'code': data['specialty_code'],
                        'display': data.get('specialty_display', '')
                    }]
                }]
            
            result = fhir.update_resource('HealthcareService', service_id, existing)
            return Response(result)
            
        except FHIRServiceException as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error updating healthcare service: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'DELETE':
        try:
            fhir.delete_resource('HealthcareService', service_id)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except FHIRServiceException as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error deleting healthcare service: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def organization_services(request, organization_id):
    """
    List services provided by a specific organization
    
    GET /api/v1/organizations/{id}/services/
    """
    try:
        fhir = FHIRService(request.user)
        
        results = fhir.search_resources('HealthcareService', {
            'organization': organization_id,
            '_count': 50
        })
        
        services = []
        for svc in results:
            services.append({
                'id': svc.get('id'),
                'name': svc.get('name'),
                'active': svc.get('active', True),
                'type': svc.get('type', [{}])[0].get('coding', [{}])[0].get('display') if svc.get('type') else None,
                'specialty': svc.get('specialty', [{}])[0].get('coding', [{}])[0].get('display') if svc.get('specialty') else None,
            })
        
        return Response({
            'services': services,
            'organization_id': organization_id,
            'total': len(services)
        })
        
    except Exception as e:
        logger.error(f"Error listing organization services: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
