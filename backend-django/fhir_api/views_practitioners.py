"""
Views for Practitioner (Healthcare Professional) management
FHIR R4 Compliant - Integrated with CBO (Classificação Brasileira de Ocupações)
"""
import logging
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response

from .services.fhir_core import FHIRService
from .services.cbo_service import cbo_service
from .auth import KeycloakAuthentication, IsAuthenticated

logger = logging.getLogger(__name__)


@api_view(['POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def create_practitioner(request):
    """
    Create a new Practitioner (Healthcare Professional)
    
    FHIR R4 Compliant - Creates Practitioner resource with CBO integration
    
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
        "conselho": "CRM",              # CRM, COREN, CRO, CRF, etc.
        "numero_conselho": "123456",
        "uf_conselho": "SP",
        "codigo_cbo": "2251-25"          # CBO code (optional if qualification_code provided)
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
        
        # Build identifier from conselho (CRM, COREN, CRO, etc.)
        conselho = data.get('conselho', '').upper()
        numero_conselho = data.get('numero_conselho', '') or data.get('crm', '')
        uf_conselho = data.get('uf_conselho', 'SP').upper()
        
        if numero_conselho:
            # Format identifier based on council type
            practitioner['identifier'] = [{
                "use": "official",
                "system": f"http://www.saude.gov.br/fhir/r4/NamingSystem/BR{conselho or 'CRM'}",
                "value": f"{numero_conselho}/{uf_conselho}"
            }]
            
            # Add CPF if provided
            if data.get('cpf'):
                practitioner['identifier'].append({
                    "use": "official",
                    "system": "http://www.saude.gov.br/fhir/r4/NamingSystem/cpf",
                    "value": data['cpf']
                })
        
        # Build qualification using CBO service
        codigo_cbo = data.get('codigo_cbo', '')
        
        if codigo_cbo:
            # Use CBO service to generate proper qualification
            if cbo_service.validar_codigo(codigo_cbo):
                qualification = cbo_service.gerar_practitioner_qualification(
                    codigo_cbo=codigo_cbo,
                    numero_conselho=numero_conselho,
                    conselho=conselho or 'CRM',
                    uf=uf_conselho
                )
                practitioner['qualification'] = [qualification]
                
                # Log CBO usage
                ocupacao = cbo_service.buscar_por_codigo(codigo_cbo)
                if ocupacao:
                    logger.info(f"Practitioner created with CBO {codigo_cbo}: {ocupacao.nome}")
            else:
                return Response(
                    {"error": f"Código CBO inválido: {codigo_cbo}. Use /api/v1/cbo/search/ para buscar códigos válidos."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        elif data.get('qualification_code'):
            # Fallback to legacy qualification format
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
            
            if numero_conselho:
                practitioner['qualification'][0]['identifier'] = [{
                    "system": f"http://www.saude.gov.br/fhir/r4/NamingSystem/BR{conselho or 'CRM'}",
                    "value": f"{numero_conselho}/{uf_conselho}"
                }]
        
        # Create in FHIR server
        result = fhir.create_resource('Practitioner', practitioner)
        
        # Add CBO info to response
        if codigo_cbo and cbo_service.validar_codigo(codigo_cbo):
            ocupacao = cbo_service.buscar_por_codigo(codigo_cbo)
            if ocupacao:
                result['_cbo'] = {
                    'codigo': ocupacao.codigo,
                    'nome': ocupacao.nome,
                    'familia': ocupacao.familia_nome
                }
        
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
    List/search practitioners with FHIR R4 compliant parameters
    
    GET /api/v1/practitioners/list/
    
    Query params:
    - name: Filter by name (partial match)
    - identifier: Filter by CRM or other identifier
    - specialty: Filter by specialty code (SNOMED CT)
    - active: Filter by active status (true/false)
    - _count: Number of results per page (default: 20, max: 100)
    - _getpagesoffset: Pagination offset
    """
    try:
        fhir = FHIRService()
        
        # Build search parameters
        params = {}
        if request.GET.get('name'):
            params['name'] = request.GET['name']
        if request.GET.get('identifier'):
            params['identifier'] = request.GET['identifier']
        if request.GET.get('active'):
            params['active'] = request.GET['active']
        
        # Pagination
        count = min(int(request.GET.get('_count', 20)), 100)
        offset = int(request.GET.get('_getpagesoffset', 0))
        params['_count'] = str(count)
        if offset > 0:
            params['_getpagesoffset'] = str(offset)
        
        practitioners = fhir.search_resources('Practitioner', params)
        
        # If specialty filter provided, we need to search PractitionerRole
        specialty = request.GET.get('specialty')
        if specialty:
            # Get PractitionerRoles with this specialty
            role_params = {'specialty': specialty}
            roles = fhir.search_resources('PractitionerRole', role_params)
            
            # Extract practitioner IDs from roles
            practitioner_ids = set()
            for role in roles:
                if role.get('practitioner', {}).get('reference'):
                    ref = role['practitioner']['reference']
                    prac_id = ref.split('/')[-1] if '/' in ref else ref
                    practitioner_ids.add(prac_id)
            
            # Filter practitioners by matching IDs
            practitioners = [p for p in practitioners if p.get('id') in practitioner_ids]
        
        return Response({
            "total": len(practitioners),
            "count": count,
            "offset": offset,
            "results": practitioners
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


@api_view(['PUT'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def update_practitioner(request, practitioner_id):
    """
    Update practitioner by ID
    
    PUT /api/v1/practitioners/{id}/
    
    Body: Same as create_practitioner
    """
    try:
        data = request.data
        fhir = FHIRService()
        
        # Get existing practitioner
        existing = fhir.get_resource('Practitioner', practitioner_id)
        if not existing:
            return Response(
                {"error": "Practitioner not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Validate required fields
        required = ['family_name', 'given_names']
        for field in required:
            if field not in data:
                return Response(
                    {"error": f"Campo obrigatório ausente: {field}"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Build updated FHIR Practitioner resource
        practitioner = {
            "resourceType": "Practitioner",
            "id": practitioner_id,
            "active": data.get('active', True),
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
        
        # Add telecom (phone and email)
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
        
        # Add identifier (CRM or similar)
        conselho = data.get('conselho', 'CRM')
        numero_conselho = data.get('numero_conselho')
        uf_conselho = data.get('uf_conselho', 'SP')
        
        if numero_conselho:
            practitioner['identifier'] = [{
                "system": f"http://www.saude.gov.br/fhir/r4/NamingSystem/BR{conselho}",
                "value": f"{numero_conselho}",
                "type": {
                    "coding": [{
                        "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                        "code": "MD",
                        "display": conselho
                    }]
                },
                "_value": {
                    "extension": [{
                        "url": "http://www.saude.gov.br/fhir/r4/StructureDefinition/BREstado",
                        "valueCode": uf_conselho
                    }]
                }
            }]
        
        # Add qualification
        codigo_cbo = data.get('codigo_cbo')
        if codigo_cbo:
            # Validate CBO code
            if cbo_service.validar_codigo(codigo_cbo):
                ocupacao = cbo_service.buscar_por_codigo(codigo_cbo)
                
                practitioner['qualification'] = [{
                    "code": {
                        "coding": [{
                            "system": "http://www.saude.gov.br/fhir/r4/CodeSystem/BRClassificacaoBrasileiradeOcupacoes",
                            "code": codigo_cbo,
                            "display": ocupacao.nome if ocupacao else codigo_cbo
                        }, {
                            "system": "http://terminology.hl7.org/CodeSystem/v2-0360",
                            "code": data.get('qualification_code', 'MD'),
                            "display": data.get('qualification_display', ocupacao.nome if ocupacao else 'Doctor')
                        }],
                        "text": ocupacao.nome if ocupacao else data.get('qualification_display', 'Médico')
                    }
                }]
            else:
                # No CBO but has qualification
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
        else:
            # No CBO provided, use qualification_code and display
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
            
            if numero_conselho:
                practitioner['qualification'][0]['identifier'] = [{
                    "system": f"http://www.saude.gov.br/fhir/r4/NamingSystem/BR{conselho or 'CRM'}",
                    "value": f"{numero_conselho}/{uf_conselho}"
                }]
        
        # Update in FHIR server
        result = fhir.update_resource('Practitioner', practitioner_id, practitioner)
        
        # Add CBO info to response
        if codigo_cbo and cbo_service.validar_codigo(codigo_cbo):
            ocupacao = cbo_service.buscar_por_codigo(codigo_cbo)
            if ocupacao:
                result['_cbo'] = {
                    'codigo': ocupacao.codigo,
                    'nome': ocupacao.nome,
                    'familia': ocupacao.familia_nome
                }
        
        return Response(result, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error updating practitioner: {e}")
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


@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def list_specialties(request):
    """
    List all medical specialties for practitioners
    
    GET /api/v1/practitioners/specialties/
    
    Returns SNOMED CT coded specialties with Brazilian CBO codes
    
    Response:
    {
        "specialties": [
            {
                "code": "394579002",
                "display": "Cardiologia",
                "display_en": "Cardiology",
                "cbo": "225120"
            },
            ...
        ]
    }
    """
    try:
        from .validators import get_all_specialties
        
        specialties = get_all_specialties()
        
        # Sort by display name
        specialties.sort(key=lambda x: x['display'])
        
        return Response({
            "specialties": specialties,
            "total": len(specialties)
        })
        
    except Exception as e:
        logger.error(f"Error listing specialties: {e}")
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def validate_identifier(request):
    """
    Validate a Brazilian professional identifier (CRM, CRF, COREN, CRO)
    
    POST /api/v1/practitioners/validate-identifier/
    
    Body:
    {
        "identifier": "CRM-SP-123456"
    }
    
    Response:
    {
        "valid": true,
        "type": "CRM",
        "formatted": "CRM-SP-123456",
        "error": null
    }
    """
    try:
        from .validators import validate_professional_identifier, format_identifier
        
        identifier = request.data.get('identifier', '')
        
        if not identifier:
            return Response(
                {"error": "Campo 'identifier' é obrigatório"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        is_valid, id_type, error = validate_professional_identifier(identifier)
        
        return Response({
            "valid": is_valid,
            "type": id_type,
            "formatted": format_identifier(identifier) if is_valid else None,
            "error": error
        })
        
    except Exception as e:
        logger.error(f"Error validating identifier: {e}")
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
