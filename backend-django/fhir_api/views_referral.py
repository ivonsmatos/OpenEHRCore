"""
Views Referral - Encaminhamentos e Referências (ServiceRequest + Task)
Gestão de encaminhamentos entre profissionais e especialidades
"""

import logging
from datetime import datetime
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework import status
from .auth import KeycloakAuthentication
from rest_framework.permissions import IsAuthenticated
from .services.fhir_core import FHIRService

logger = logging.getLogger(__name__)


# =============================================================================
# ServiceRequest (Encaminhamentos)
# =============================================================================

@api_view(['GET', 'POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def manage_referrals(request):
    """
    Lista ou cria encaminhamentos
    GET /api/v1/referrals/
    POST /api/v1/referrals/
    """
    fhir_service = FHIRService(request.user)
    
    if request.method == 'GET':
        try:
            params = {
                '_sort': '-authored-on',
                '_count': request.query_params.get('limit', 50)
            }
            
            # Filtros opcionais
            if request.query_params.get('status'):
                params['status'] = request.query_params['status']
            if request.query_params.get('patient'):
                params['subject'] = f"Patient/{request.query_params['patient']}"
            if request.query_params.get('requester'):
                params['requester'] = request.query_params['requester']
            if request.query_params.get('specialty'):
                params['performer-type'] = request.query_params['specialty']
            
            result = fhir_service.search_resources('ServiceRequest', params)
            
            referrals = []
            for entry in result.get('entry', []):
                sr = entry.get('resource', {})
                referrals.append(_format_referral(sr))
            
            return Response({
                'count': len(referrals),
                'results': referrals
            })
            
        except Exception as e:
            logger.error(f"Erro ao listar encaminhamentos: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'POST':
        try:
            data = request.data
            
            service_request = {
                'resourceType': 'ServiceRequest',
                'status': 'active',
                'intent': 'order',
                'priority': data.get('priority', 'routine'),
                'category': [{
                    'coding': [{
                        'system': 'http://terminology.hl7.org/CodeSystem/servicerequest-category',
                        'code': 'consultation',
                        'display': 'Consultation'
                    }]
                }],
                'code': {
                    'coding': [{
                        'system': 'http://loinc.org',
                        'code': '11488-4',
                        'display': 'Consultation note'
                    }],
                    'text': data.get('reason', 'Encaminhamento')
                },
                'subject': {
                    'reference': f"Patient/{data['patient_id']}"
                },
                'requester': {
                    'reference': f"Practitioner/{data['requester_id']}"
                },
                'authoredOn': datetime.now().isoformat(),
                'reasonCode': [{
                    'text': data.get('clinical_indication', '')
                }],
                'note': [{
                    'text': data.get('notes', '')
                }] if data.get('notes') else []
            }
            
            # Especialidade destino
            if data.get('specialty'):
                service_request['performerType'] = {
                    'coding': [{
                        'system': 'http://snomed.info/sct',
                        'code': data['specialty']['code'],
                        'display': data['specialty']['display']
                    }]
                }
            
            # Profissional/organização destino específico
            if data.get('performer_id'):
                service_request['performer'] = [{
                    'reference': f"Practitioner/{data['performer_id']}"
                }]
            elif data.get('organization_id'):
                service_request['performer'] = [{
                    'reference': f"Organization/{data['organization_id']}"
                }]
            
            # Encounter relacionado
            if data.get('encounter_id'):
                service_request['encounter'] = {
                    'reference': f"Encounter/{data['encounter_id']}"
                }
            
            result = fhir_service.create_resource('ServiceRequest', service_request)
            
            # Criar Task para rastreamento
            if result.get('id'):
                _create_referral_task(fhir_service, result['id'], data)
            
            return Response({
                'id': result.get('id'),
                'message': 'Encaminhamento criado com sucesso',
                'referral': _format_referral(result)
            }, status=status.HTTP_201_CREATED)
            
        except KeyError as e:
            return Response({'error': f'Campo obrigatório: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Erro ao criar encaminhamento: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'PUT', 'DELETE'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def referral_detail(request, referral_id):
    """
    Detalhes, atualização ou cancelamento de encaminhamento
    GET/PUT/DELETE /api/v1/referrals/{referral_id}/
    """
    fhir_service = FHIRService(request.user)
    
    if request.method == 'GET':
        try:
            sr = fhir_service.get_resource('ServiceRequest', referral_id)
            if not sr:
                return Response({'error': 'Encaminhamento não encontrado'}, status=status.HTTP_404_NOT_FOUND)
            
            # Buscar Task associada
            tasks = fhir_service.search_resources('Task', {'based-on': f'ServiceRequest/{referral_id}'})
            task = tasks.get('entry', [{}])[0].get('resource') if tasks.get('entry') else None
            
            result = _format_referral(sr)
            if task:
                result['task'] = _format_task(task)
            
            return Response(result)
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'PUT':
        try:
            data = request.data
            sr = fhir_service.get_resource('ServiceRequest', referral_id)
            if not sr:
                return Response({'error': 'Encaminhamento não encontrado'}, status=status.HTTP_404_NOT_FOUND)
            
            # Atualizar campos permitidos
            if 'status' in data:
                sr['status'] = data['status']
            if 'priority' in data:
                sr['priority'] = data['priority']
            if 'notes' in data:
                sr['note'] = [{'text': data['notes']}]
            
            result = fhir_service.update_resource('ServiceRequest', referral_id, sr)
            
            return Response({
                'message': 'Encaminhamento atualizado',
                'referral': _format_referral(result)
            })
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'DELETE':
        try:
            # Não deletar, apenas cancelar
            sr = fhir_service.get_resource('ServiceRequest', referral_id)
            if not sr:
                return Response({'error': 'Encaminhamento não encontrado'}, status=status.HTTP_404_NOT_FOUND)
            
            sr['status'] = 'revoked'
            fhir_service.update_resource('ServiceRequest', referral_id, sr)
            
            return Response({'message': 'Encaminhamento cancelado'})
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def pending_referrals(request):
    """
    Lista encaminhamentos pendentes de aceite
    GET /api/v1/referrals/pending/
    """
    fhir_service = FHIRService(request.user)
    
    try:
        # Buscar ServiceRequests ativos
        params = {
            'status': 'active',
            '_sort': '-authored-on'
        }
        
        # Se for um profissional específico
        if request.query_params.get('performer'):
            params['performer'] = request.query_params['performer']
        
        result = fhir_service.search_resources('ServiceRequest', params)
        
        referrals = []
        for entry in result.get('entry', []):
            sr = entry.get('resource', {})
            referrals.append(_format_referral(sr))
        
        return Response({
            'count': len(referrals),
            'results': referrals
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def accept_referral(request, referral_id):
    """
    Aceita um encaminhamento
    POST /api/v1/referrals/{referral_id}/accept/
    """
    fhir_service = FHIRService(request.user)
    
    try:
        data = request.data
        
        # Buscar e atualizar Task
        tasks = fhir_service.search_resources('Task', {'based-on': f'ServiceRequest/{referral_id}'})
        
        if tasks.get('entry'):
            task = tasks['entry'][0]['resource']
            task['status'] = 'accepted'
            task['lastModified'] = datetime.now().isoformat()
            
            if data.get('scheduled_date'):
                task['executionPeriod'] = {
                    'start': data['scheduled_date']
                }
            
            fhir_service.update_resource('Task', task['id'], task)
        
        return Response({
            'message': 'Encaminhamento aceito',
            'referral_id': referral_id
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def complete_referral(request, referral_id):
    """
    Marca encaminhamento como concluído
    POST /api/v1/referrals/{referral_id}/complete/
    """
    fhir_service = FHIRService(request.user)
    
    try:
        data = request.data
        
        # Atualizar ServiceRequest
        sr = fhir_service.get_resource('ServiceRequest', referral_id)
        if sr:
            sr['status'] = 'completed'
            fhir_service.update_resource('ServiceRequest', referral_id, sr)
        
        # Atualizar Task
        tasks = fhir_service.search_resources('Task', {'based-on': f'ServiceRequest/{referral_id}'})
        
        if tasks.get('entry'):
            task = tasks['entry'][0]['resource']
            task['status'] = 'completed'
            task['lastModified'] = datetime.now().isoformat()
            task['executionPeriod'] = task.get('executionPeriod', {})
            task['executionPeriod']['end'] = datetime.now().isoformat()
            
            # Adicionar output (resultado da consulta)
            if data.get('outcome'):
                task['output'] = [{
                    'type': {'text': 'Resultado'},
                    'valueString': data['outcome']
                }]
            
            fhir_service.update_resource('Task', task['id'], task)
        
        return Response({
            'message': 'Encaminhamento concluído',
            'referral_id': referral_id
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def patient_referrals(request, patient_id):
    """
    Lista encaminhamentos de um paciente
    GET /api/v1/patients/{patient_id}/referrals/
    """
    fhir_service = FHIRService(request.user)
    
    try:
        params = {
            'subject': f'Patient/{patient_id}',
            '_sort': '-authored-on'
        }
        
        result = fhir_service.search_resources('ServiceRequest', params)
        
        referrals = []
        for entry in result.get('entry', []):
            sr = entry.get('resource', {})
            referrals.append(_format_referral(sr))
        
        return Response({
            'patient_id': patient_id,
            'count': len(referrals),
            'results': referrals
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# =============================================================================
# Helpers
# =============================================================================

def _format_referral(sr: dict) -> dict:
    """Formata ServiceRequest para resposta"""
    return {
        'id': sr.get('id'),
        'status': sr.get('status'),
        'intent': sr.get('intent'),
        'priority': sr.get('priority'),
        'reason': sr.get('code', {}).get('text'),
        'clinical_indication': sr.get('reasonCode', [{}])[0].get('text') if sr.get('reasonCode') else None,
        'patient': sr.get('subject', {}).get('reference', '').replace('Patient/', ''),
        'requester': sr.get('requester', {}).get('reference', '').replace('Practitioner/', ''),
        'performer': sr.get('performer', [{}])[0].get('reference', '') if sr.get('performer') else None,
        'specialty': sr.get('performerType', {}).get('coding', [{}])[0].get('display') if sr.get('performerType') else None,
        'authored_on': sr.get('authoredOn'),
        'notes': sr.get('note', [{}])[0].get('text') if sr.get('note') else None
    }


def _format_task(task: dict) -> dict:
    """Formata Task para resposta"""
    return {
        'id': task.get('id'),
        'status': task.get('status'),
        'last_modified': task.get('lastModified'),
        'scheduled_start': task.get('executionPeriod', {}).get('start'),
        'completed_at': task.get('executionPeriod', {}).get('end'),
        'outcome': task.get('output', [{}])[0].get('valueString') if task.get('output') else None
    }


def _create_referral_task(fhir_service, service_request_id: str, data: dict):
    """Cria Task para rastrear o encaminhamento"""
    task = {
        'resourceType': 'Task',
        'status': 'requested',
        'intent': 'order',
        'priority': data.get('priority', 'routine'),
        'description': f"Encaminhamento: {data.get('reason', 'Consulta')}",
        'basedOn': [{
            'reference': f'ServiceRequest/{service_request_id}'
        }],
        'for': {
            'reference': f"Patient/{data['patient_id']}"
        },
        'authoredOn': datetime.now().isoformat(),
        'lastModified': datetime.now().isoformat()
    }
    
    if data.get('performer_id'):
        task['owner'] = {'reference': f"Practitioner/{data['performer_id']}"}
    
    try:
        fhir_service.create_resource('Task', task)
    except Exception as e:
        logger.warning(f"Erro ao criar Task para encaminhamento: {str(e)}")
