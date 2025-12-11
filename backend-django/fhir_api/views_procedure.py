"""
Views for Procedure management
FHIR R4 Compliant

Procedure representa procedimentos médicos realizados em pacientes:
- Cirurgias
- Procedimentos diagnósticos
- Procedimentos terapêuticos
- Biópsias, etc.

Suporta códigos brasileiros TUSS (Terminologia Unificada da Saúde Suplementar).
"""
import logging
from datetime import datetime
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response

from .services.fhir_core import FHIRService, FHIRServiceException
from .auth import KeycloakAuthentication, IsAuthenticated

logger = logging.getLogger(__name__)

# Status válidos para Procedure FHIR R4
VALID_STATUSES = [
    'preparation',      # Em preparação
    'in-progress',      # Em andamento
    'not-done',         # Não realizado
    'on-hold',          # Em espera
    'stopped',          # Parado
    'completed',        # Concluído
    'entered-in-error', # Erro de entrada
    'unknown'           # Desconhecido
]


@api_view(['GET', 'POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def manage_procedures(request):
    """
    GET: Lista procedimentos (com filtros)
    POST: Registra novo procedimento
    
    FHIR R4 Procedure Resource
    
    Parâmetros de busca (GET):
    - patient: ID do paciente
    - status: Status do procedimento
    - code: Código TUSS/SNOMED
    - date: Data do procedimento (ge/le para range)
    - performer: ID do profissional que realizou
    
    Body (POST):
    {
        "patient_id": "patient-123",
        "encounter_id": "encounter-456",  # Opcional
        "status": "completed",
        "code": "30602002",  # Código TUSS ou SNOMED
        "code_system": "tuss",  # "tuss" ou "snomed"
        "display": "Consulta médica em pronto socorro",
        "category": "surgical",  # surgical, diagnostic, therapeutic
        "performed_date": "2024-01-15T10:30:00Z",
        "performer_id": "practitioner-789",
        "body_site": {
            "code": "251007",
            "display": "Joelho esquerdo"
        },
        "outcome": "Procedimento realizado com sucesso",
        "notes": "Paciente tolerou bem o procedimento"
    }
    """
    fhir = FHIRService(request.user)
    
    if request.method == 'GET':
        try:
            params = {}
            
            # Filtro por paciente
            if request.query_params.get('patient'):
                params['subject'] = f"Patient/{request.query_params['patient']}"
            
            # Filtro por status
            if request.query_params.get('status'):
                req_status = request.query_params['status']
                if req_status not in VALID_STATUSES:
                    return Response(
                        {'error': f'Status inválido. Use: {", ".join(VALID_STATUSES)}'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                params['status'] = req_status
            
            # Filtro por código
            if request.query_params.get('code'):
                params['code'] = request.query_params['code']
            
            # Filtro por data
            if request.query_params.get('date'):
                params['date'] = request.query_params['date']
            
            # Filtro por performer
            if request.query_params.get('performer'):
                params['performer'] = f"Practitioner/{request.query_params['performer']}"
            
            # Paginação
            count = int(request.query_params.get('_count', 50))
            offset = int(request.query_params.get('_getpagesoffset', 0))
            params['_count'] = count
            if offset > 0:
                params['_getpagesoffset'] = offset
            params['_sort'] = '-date'
            
            results = fhir.search_resources('Procedure', params)
            
            return Response({
                'total': len(results),
                'count': count,
                'offset': offset,
                'results': results
            })
            
        except Exception as e:
            logger.error(f"Error listing procedures: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    elif request.method == 'POST':
        try:
            data = request.data
            
            # Validar campos obrigatórios
            required = ['patient_id', 'status', 'code', 'display']
            for field in required:
                if not data.get(field):
                    return Response(
                        {'error': f'Campo obrigatório ausente: {field}'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Validar status
            if data['status'] not in VALID_STATUSES:
                return Response(
                    {'error': f'Status inválido. Use: {", ".join(VALID_STATUSES)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Construir recurso Procedure FHIR
            procedure = {
                'resourceType': 'Procedure',
                'status': data['status'],
                'subject': {
                    'reference': f"Patient/{data['patient_id']}"
                }
            }
            
            # Código do procedimento (TUSS ou SNOMED)
            code_system = data.get('code_system', 'tuss')
            if code_system == 'tuss':
                system_url = 'http://www.ans.gov.br/tuss'
            else:
                system_url = 'http://snomed.info/sct'
            
            procedure['code'] = {
                'coding': [{
                    'system': system_url,
                    'code': data['code'],
                    'display': data['display']
                }],
                'text': data['display']
            }
            
            # Categoria
            if data.get('category'):
                category_mapping = {
                    'surgical': ('387713003', 'Surgical procedure'),
                    'diagnostic': ('103693007', 'Diagnostic procedure'),
                    'therapeutic': ('277132007', 'Therapeutic procedure'),
                }
                cat_code, cat_display = category_mapping.get(
                    data['category'], 
                    ('387713003', 'Surgical procedure')
                )
                procedure['category'] = {
                    'coding': [{
                        'system': 'http://snomed.info/sct',
                        'code': cat_code,
                        'display': cat_display
                    }]
                }
            
            # Data/hora do procedimento
            if data.get('performed_date'):
                procedure['performedDateTime'] = data['performed_date']
            else:
                procedure['performedDateTime'] = datetime.utcnow().isoformat() + 'Z'
            
            # Relacionar ao encontro
            if data.get('encounter_id'):
                procedure['encounter'] = {
                    'reference': f"Encounter/{data['encounter_id']}"
                }
            
            # Profissional que realizou
            if data.get('performer_id'):
                procedure['performer'] = [{
                    'actor': {
                        'reference': f"Practitioner/{data['performer_id']}"
                    }
                }]
            
            # Local do corpo
            if data.get('body_site'):
                procedure['bodySite'] = [{
                    'coding': [{
                        'system': 'http://snomed.info/sct',
                        'code': data['body_site']['code'],
                        'display': data['body_site']['display']
                    }]
                }]
            
            # Resultado/Outcome
            if data.get('outcome'):
                procedure['outcome'] = {
                    'text': data['outcome']
                }
            
            # Notas
            if data.get('notes'):
                procedure['note'] = [{
                    'text': data['notes']
                }]
            
            # Criar no HAPI FHIR
            result = fhir.create_resource('Procedure', procedure)
            
            logger.info(f"Procedure created: {result.get('id')} - {data['display']}")
            
            return Response({
                'id': result.get('id'),
                'resourceType': 'Procedure',
                'status': data['status'],
                'code': data['code'],
                'display': data['display'],
                'patient_id': data['patient_id'],
                'message': 'Procedimento registrado com sucesso'
            }, status=status.HTTP_201_CREATED)
            
        except FHIRServiceException as e:
            logger.error(f"FHIR error creating procedure: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            logger.error(f"Error creating procedure: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@api_view(['GET', 'PUT', 'DELETE'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def procedure_detail(request, procedure_id):
    """
    GET: Busca procedimento por ID
    PUT: Atualiza procedimento
    DELETE: Remove procedimento (marca como entered-in-error)
    """
    fhir = FHIRService(request.user)
    
    if request.method == 'GET':
        try:
            results = fhir.search_resources('Procedure', {'_id': procedure_id})
            
            if not results:
                return Response(
                    {'error': 'Procedimento não encontrado'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            return Response(results[0])
            
        except Exception as e:
            logger.error(f"Error getting procedure {procedure_id}: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    elif request.method == 'PUT':
        try:
            data = request.data
            
            # Buscar procedimento existente
            results = fhir.search_resources('Procedure', {'_id': procedure_id}, use_cache=False)
            
            if not results:
                return Response(
                    {'error': 'Procedimento não encontrado'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            existing = results[0]
            
            # Atualizar campos permitidos
            if data.get('status'):
                if data['status'] not in VALID_STATUSES:
                    return Response(
                        {'error': f'Status inválido. Use: {", ".join(VALID_STATUSES)}'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                existing['status'] = data['status']
            
            if data.get('outcome'):
                existing['outcome'] = {'text': data['outcome']}
            
            if data.get('notes'):
                existing['note'] = [{'text': data['notes']}]
            
            # Atualizar via PUT
            response = fhir.session.put(
                f"{fhir.base_url}/Procedure/{procedure_id}",
                json=existing,
                timeout=fhir.timeout
            )
            
            if response.status_code not in [200, 201]:
                raise FHIRServiceException(f"Failed to update: {response.text}")
            
            # Limpar cache
            fhir.clear_cache('Procedure')
            
            return Response(response.json())
            
        except Exception as e:
            logger.error(f"Error updating procedure {procedure_id}: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    elif request.method == 'DELETE':
        try:
            # Soft delete: marcar como entered-in-error
            results = fhir.search_resources('Procedure', {'_id': procedure_id}, use_cache=False)
            
            if not results:
                return Response(
                    {'error': 'Procedimento não encontrado'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            existing = results[0]
            existing['status'] = 'entered-in-error'
            
            response = fhir.session.put(
                f"{fhir.base_url}/Procedure/{procedure_id}",
                json=existing,
                timeout=fhir.timeout
            )
            
            if response.status_code not in [200, 201]:
                raise FHIRServiceException(f"Failed to mark as error: {response.text}")
            
            # Limpar cache
            fhir.clear_cache('Procedure')
            
            return Response({
                'message': 'Procedimento marcado como erro de entrada',
                'id': procedure_id
            })
            
        except Exception as e:
            logger.error(f"Error deleting procedure {procedure_id}: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def patient_procedures(request, patient_id):
    """
    Lista todos os procedimentos de um paciente.
    
    GET /api/v1/patients/<patient_id>/procedures/
    
    Parâmetros:
    - status: Filtrar por status
    - _count: Limite de resultados
    """
    fhir = FHIRService(request.user)
    
    try:
        params = {
            'subject': f"Patient/{patient_id}",
            '_sort': '-date'
        }
        
        if request.query_params.get('status'):
            params['status'] = request.query_params['status']
        
        count = int(request.query_params.get('_count', 50))
        params['_count'] = count
        
        results = fhir.search_resources('Procedure', params)
        
        return Response({
            'patient_id': patient_id,
            'total': len(results),
            'procedures': results
        })
        
    except Exception as e:
        logger.error(f"Error getting procedures for patient {patient_id}: {e}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
