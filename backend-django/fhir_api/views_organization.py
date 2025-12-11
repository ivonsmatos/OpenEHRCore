"""
Views for Organization management
FHIR R4 Compliant

Organization representa instituições de saúde: hospitais, clínicas, laboratórios, etc.
Suporta hierarquia (partOf) e identificadores brasileiros (CNPJ, CNES).
"""
import logging
import re
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response

from .services.fhir_core import FHIRService, FHIRServiceException
from .auth import KeycloakAuthentication, IsAuthenticated

logger = logging.getLogger(__name__)


def validate_cnpj(cnpj: str) -> bool:
    """
    Valida CNPJ brasileiro.
    
    Args:
        cnpj: String com CNPJ (pode conter pontuação)
        
    Returns:
        True se válido, False caso contrário
    """
    # Remove caracteres não numéricos
    cnpj = re.sub(r'[^0-9]', '', cnpj)
    
    if len(cnpj) != 14:
        return False
    
    # Elimina CNPJs inválidos conhecidos
    if cnpj == cnpj[0] * 14:
        return False
    
    # Validação primeiro dígito
    soma = 0
    peso = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    for i, digito in enumerate(cnpj[:12]):
        soma += int(digito) * peso[i]
    resto = soma % 11
    digito1 = 0 if resto < 2 else 11 - resto
    
    if int(cnpj[12]) != digito1:
        return False
    
    # Validação segundo dígito
    soma = 0
    peso = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    for i, digito in enumerate(cnpj[:13]):
        soma += int(digito) * peso[i]
    resto = soma % 11
    digito2 = 0 if resto < 2 else 11 - resto
    
    return int(cnpj[13]) == digito2


def format_cnpj(cnpj: str) -> str:
    """Formata CNPJ para exibição: XX.XXX.XXX/XXXX-XX"""
    cnpj = re.sub(r'[^0-9]', '', cnpj)
    return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:14]}"


@api_view(['GET', 'POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def manage_organizations(request):
    """
    GET: Lista todas as organizações
    POST: Cria nova organização
    
    FHIR R4 Organization Resource
    
    Tipos suportados:
    - prov (Healthcare Provider) - Hospital, clínica
    - dept (Hospital Department) - Departamento
    - team (Clinical Team) - Equipe
    - govt (Government) - Órgão governamental
    - ins (Insurance Company) - Operadora de saúde
    
    Body (POST):
    {
        "name": "Hospital São Paulo",
        "alias": ["HSP", "Hospital Central"],
        "type": "prov",
        "cnpj": "12.345.678/0001-90",
        "cnes": "1234567",
        "phone": "(11) 3456-7890",
        "email": "contato@hospitalsaopaulo.com.br",
        "address": {
            "line": ["Rua das Flores, 123"],
            "city": "São Paulo",
            "state": "SP",
            "postalCode": "01234-567",
            "country": "BR"
        },
        "partOf": "organization-parent-id"  # Opcional: ID da org pai
    }
    """
    fhir = FHIRService(request.user)
    
    if request.method == 'GET':
        try:
            # Parâmetros de busca
            params = {}
            if request.query_params.get('name'):
                params['name'] = request.query_params['name']
            if request.query_params.get('type'):
                params['type'] = request.query_params['type']
            if request.query_params.get('identifier'):
                params['identifier'] = request.query_params['identifier']
            if request.query_params.get('active'):
                params['active'] = request.query_params['active']
            
            # Paginação
            count = int(request.query_params.get('_count', 50))
            offset = int(request.query_params.get('_getpagesoffset', 0))
            params['_count'] = count
            if offset > 0:
                params['_getpagesoffset'] = offset
            
            results = fhir.search_resources('Organization', params)
            
            return Response({
                'total': len(results),
                'count': count,
                'offset': offset,
                'results': results
            })
            
        except Exception as e:
            logger.error(f"Error listing organizations: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    elif request.method == 'POST':
        try:
            data = request.data
            
            # Validar campos obrigatórios
            if not data.get('name'):
                return Response(
                    {'error': 'Campo obrigatório ausente: name'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validar CNPJ se fornecido
            if data.get('cnpj'):
                if not validate_cnpj(data['cnpj']):
                    return Response(
                        {'error': 'CNPJ inválido'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Construir recurso Organization FHIR
            organization = {
                'resourceType': 'Organization',
                'active': True,
                'name': data['name']
            }
            
            # Alias (nomes alternativos)
            if data.get('alias'):
                organization['alias'] = data['alias'] if isinstance(data['alias'], list) else [data['alias']]
            
            # Tipo de organização
            if data.get('type'):
                type_mapping = {
                    'prov': ('prov', 'Healthcare Provider'),
                    'dept': ('dept', 'Hospital Department'),
                    'team': ('team', 'Organizational team'),
                    'govt': ('govt', 'Government'),
                    'ins': ('ins', 'Insurance Company'),
                    'edu': ('edu', 'Educational Institute'),
                    'reli': ('reli', 'Religious Institution'),
                    'crs': ('crs', 'Clinical Research Sponsor'),
                    'cg': ('cg', 'Community Group'),
                    'bus': ('bus', 'Non-Healthcare Business'),
                    'other': ('other', 'Other'),
                }
                type_code, type_display = type_mapping.get(data['type'], ('other', 'Other'))
                organization['type'] = [{
                    'coding': [{
                        'system': 'http://terminology.hl7.org/CodeSystem/organization-type',
                        'code': type_code,
                        'display': type_display
                    }]
                }]
            
            # Identificadores (CNPJ, CNES)
            identifiers = []
            if data.get('cnpj'):
                cnpj_clean = re.sub(r'[^0-9]', '', data['cnpj'])
                identifiers.append({
                    'system': 'http://www.receita.fazenda.gov.br/cnpj',
                    'value': cnpj_clean,
                    'type': {
                        'coding': [{
                            'system': 'http://terminology.hl7.org/CodeSystem/v2-0203',
                            'code': 'TAX',
                            'display': 'Tax ID number'
                        }],
                        'text': 'CNPJ'
                    }
                })
            if data.get('cnes'):
                identifiers.append({
                    'system': 'http://cnes.datasus.gov.br',
                    'value': data['cnes'],
                    'type': {
                        'coding': [{
                            'system': 'http://terminology.hl7.org/CodeSystem/v2-0203',
                            'code': 'PRN',
                            'display': 'Provider number'
                        }],
                        'text': 'CNES'
                    }
                })
            if identifiers:
                organization['identifier'] = identifiers
            
            # Contato (telefone, email)
            telecom = []
            if data.get('phone'):
                telecom.append({
                    'system': 'phone',
                    'value': data['phone'],
                    'use': 'work'
                })
            if data.get('email'):
                telecom.append({
                    'system': 'email',
                    'value': data['email'],
                    'use': 'work'
                })
            if telecom:
                organization['telecom'] = telecom
            
            # Endereço
            if data.get('address'):
                addr = data['address']
                organization['address'] = [{
                    'use': 'work',
                    'type': 'physical',
                    'line': addr.get('line', []),
                    'city': addr.get('city'),
                    'state': addr.get('state'),
                    'postalCode': addr.get('postalCode'),
                    'country': addr.get('country', 'BR')
                }]
            
            # Hierarquia (organização pai)
            if data.get('partOf'):
                organization['partOf'] = {
                    'reference': f"Organization/{data['partOf']}"
                }
            
            # Criar no HAPI FHIR
            result = fhir.create_resource('Organization', organization)
            
            logger.info(f"Organization created: {result.get('id')} - {data['name']}")
            
            return Response({
                'id': result.get('id'),
                'resourceType': 'Organization',
                'name': data['name'],
                'cnpj': format_cnpj(data['cnpj']) if data.get('cnpj') else None,
                'message': 'Organização criada com sucesso'
            }, status=status.HTTP_201_CREATED)
            
        except FHIRServiceException as e:
            logger.error(f"FHIR error creating organization: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            logger.error(f"Error creating organization: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@api_view(['GET', 'PUT', 'DELETE'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def organization_detail(request, organization_id):
    """
    GET: Busca organização por ID
    PUT: Atualiza organização
    DELETE: Desativa organização (soft delete)
    """
    fhir = FHIRService(request.user)
    
    if request.method == 'GET':
        try:
            # Buscar organização
            results = fhir.search_resources('Organization', {'_id': organization_id})
            
            if not results:
                return Response(
                    {'error': 'Organização não encontrada'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            return Response(results[0])
            
        except Exception as e:
            logger.error(f"Error getting organization {organization_id}: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    elif request.method == 'PUT':
        try:
            data = request.data
            
            # Buscar organização existente
            results = fhir.search_resources('Organization', {'_id': organization_id}, use_cache=False)
            
            if not results:
                return Response(
                    {'error': 'Organização não encontrada'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            existing = results[0]
            
            # Atualizar campos
            if data.get('name'):
                existing['name'] = data['name']
            if data.get('alias'):
                existing['alias'] = data['alias'] if isinstance(data['alias'], list) else [data['alias']]
            if 'active' in data:
                existing['active'] = data['active']
            
            # Atualizar contato
            if data.get('phone') or data.get('email'):
                telecom = []
                if data.get('phone'):
                    telecom.append({'system': 'phone', 'value': data['phone'], 'use': 'work'})
                if data.get('email'):
                    telecom.append({'system': 'email', 'value': data['email'], 'use': 'work'})
                existing['telecom'] = telecom
            
            # Atualizar via PUT
            response = fhir.session.put(
                f"{fhir.base_url}/Organization/{organization_id}",
                json=existing,
                timeout=fhir.timeout
            )
            
            if response.status_code not in [200, 201]:
                raise FHIRServiceException(f"Failed to update: {response.text}")
            
            # Limpar cache
            fhir.clear_cache('Organization')
            
            return Response(response.json())
            
        except Exception as e:
            logger.error(f"Error updating organization {organization_id}: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    elif request.method == 'DELETE':
        try:
            # Soft delete: apenas desativar
            results = fhir.search_resources('Organization', {'_id': organization_id}, use_cache=False)
            
            if not results:
                return Response(
                    {'error': 'Organização não encontrada'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            existing = results[0]
            existing['active'] = False
            
            response = fhir.session.put(
                f"{fhir.base_url}/Organization/{organization_id}",
                json=existing,
                timeout=fhir.timeout
            )
            
            if response.status_code not in [200, 201]:
                raise FHIRServiceException(f"Failed to deactivate: {response.text}")
            
            # Limpar cache
            fhir.clear_cache('Organization')
            
            return Response({
                'message': 'Organização desativada com sucesso',
                'id': organization_id
            })
            
        except Exception as e:
            logger.error(f"Error deleting organization {organization_id}: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def organization_hierarchy(request, organization_id):
    """
    Retorna a hierarquia completa de uma organização (pai e filhos).
    
    GET /api/v1/organizations/<id>/hierarchy/
    
    Returns:
    {
        "organization": {...},
        "parent": {...} or null,
        "children": [...]
    }
    """
    fhir = FHIRService(request.user)
    
    try:
        # Buscar organização
        results = fhir.search_resources('Organization', {'_id': organization_id})
        
        if not results:
            return Response(
                {'error': 'Organização não encontrada'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        org = results[0]
        
        # Buscar organização pai (se existir)
        parent = None
        if org.get('partOf') and org['partOf'].get('reference'):
            parent_ref = org['partOf']['reference']
            parent_id = parent_ref.split('/')[-1]
            parent_results = fhir.search_resources('Organization', {'_id': parent_id})
            if parent_results:
                parent = parent_results[0]
        
        # Buscar organizações filhas
        children = fhir.search_resources('Organization', {'partof': organization_id})
        
        return Response({
            'organization': org,
            'parent': parent,
            'children': children
        })
        
    except Exception as e:
        logger.error(f"Error getting organization hierarchy: {e}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
