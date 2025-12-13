"""
Views Communication - Mensagens entre Profissionais de Saúde
Comunicação estruturada seguindo padrão FHIR Communication
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


@api_view(['GET', 'POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def manage_communications(request):
    """
    Lista ou cria comunicações
    GET /api/v1/communications/
    POST /api/v1/communications/
    """
    fhir_service = FHIRService(request.user)
    
    if request.method == 'GET':
        try:
            params = {
                '_sort': '-sent',
                '_count': request.query_params.get('limit', 50)
            }
            
            # Filtros
            if request.query_params.get('sender'):
                params['sender'] = f"Practitioner/{request.query_params['sender']}"
            if request.query_params.get('recipient'):
                params['recipient'] = f"Practitioner/{request.query_params['recipient']}"
            if request.query_params.get('patient'):
                params['subject'] = f"Patient/{request.query_params['patient']}"
            if request.query_params.get('status'):
                params['status'] = request.query_params['status']
            if request.query_params.get('category'):
                params['category'] = request.query_params['category']
            
            result = fhir_service.search_resources('Communication', params)
            
            messages = []
            for entry in result.get('entry', []):
                comm = entry.get('resource', {})
                messages.append(_format_communication(comm))
            
            return Response({
                'count': len(messages),
                'results': messages
            })
            
        except Exception as e:
            logger.error(f"Erro ao listar comunicações: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'POST':
        try:
            data = request.data
            
            communication = {
                'resourceType': 'Communication',
                'status': 'completed',
                'category': [{
                    'coding': [{
                        'system': 'http://terminology.hl7.org/CodeSystem/communication-category',
                        'code': data.get('category', 'notification'),
                        'display': _get_category_display(data.get('category', 'notification'))
                    }]
                }],
                'priority': data.get('priority', 'routine'),
                'sender': {
                    'reference': f"Practitioner/{data['sender_id']}"
                },
                'recipient': [{
                    'reference': f"Practitioner/{data['recipient_id']}"
                }],
                'sent': datetime.now().isoformat(),
                'payload': [{
                    'contentString': data['message']
                }]
            }
            
            # Paciente relacionado
            if data.get('patient_id'):
                communication['subject'] = {
                    'reference': f"Patient/{data['patient_id']}"
                }
            
            # Encounter relacionado
            if data.get('encounter_id'):
                communication['encounter'] = {
                    'reference': f"Encounter/{data['encounter_id']}"
                }
            
            # Comunicação em resposta a outra
            if data.get('in_response_to'):
                communication['inResponseTo'] = [{
                    'reference': f"Communication/{data['in_response_to']}"
                }]
            
            # Baseado em encaminhamento
            if data.get('service_request_id'):
                communication['basedOn'] = [{
                    'reference': f"ServiceRequest/{data['service_request_id']}"
                }]
            
            # Anexos
            if data.get('attachments'):
                for attachment in data['attachments']:
                    communication['payload'].append({
                        'contentAttachment': {
                            'contentType': attachment.get('content_type', 'application/pdf'),
                            'url': attachment.get('url'),
                            'title': attachment.get('title')
                        }
                    })
            
            result = fhir_service.create_resource('Communication', communication)
            
            return Response({
                'id': result.get('id'),
                'message': 'Mensagem enviada com sucesso',
                'communication': _format_communication(result)
            }, status=status.HTTP_201_CREATED)
            
        except KeyError as e:
            return Response({'error': f'Campo obrigatório: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Erro ao criar comunicação: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def communication_detail(request, communication_id):
    """
    Detalhes de uma comunicação
    GET /api/v1/communications/{communication_id}/
    """
    fhir_service = FHIRService(request.user)
    
    try:
        comm = fhir_service.get_resource('Communication', communication_id)
        if not comm:
            return Response({'error': 'Comunicação não encontrada'}, status=status.HTTP_404_NOT_FOUND)
        
        # Marcar como lida (received)
        if comm.get('status') == 'completed' and not comm.get('received'):
            comm['received'] = datetime.now().isoformat()
            fhir_service.update_resource('Communication', communication_id, comm)
        
        # Buscar respostas
        responses = fhir_service.search_resources('Communication', {
            'in-response-to': f'Communication/{communication_id}'
        })
        
        result = _format_communication(comm)
        result['responses'] = [
            _format_communication(r.get('resource', {}))
            for r in responses.get('entry', [])
        ]
        
        return Response(result)
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def reply_communication(request, communication_id):
    """
    Responde a uma comunicação
    POST /api/v1/communications/{communication_id}/reply/
    """
    fhir_service = FHIRService(request.user)
    
    try:
        data = request.data
        
        # Buscar comunicação original
        original = fhir_service.get_resource('Communication', communication_id)
        if not original:
            return Response({'error': 'Comunicação não encontrada'}, status=status.HTTP_404_NOT_FOUND)
        
        # Criar resposta (invertendo sender/recipient)
        reply = {
            'resourceType': 'Communication',
            'status': 'completed',
            'category': original.get('category', []),
            'priority': data.get('priority', original.get('priority', 'routine')),
            'sender': original.get('recipient', [{}])[0],  # Quem recebeu responde
            'recipient': [original.get('sender', {})],      # Para quem enviou
            'sent': datetime.now().isoformat(),
            'inResponseTo': [{
                'reference': f'Communication/{communication_id}'
            }],
            'payload': [{
                'contentString': data['message']
            }]
        }
        
        # Manter contexto
        if original.get('subject'):
            reply['subject'] = original['subject']
        if original.get('encounter'):
            reply['encounter'] = original['encounter']
        
        result = fhir_service.create_resource('Communication', reply)
        
        return Response({
            'id': result.get('id'),
            'message': 'Resposta enviada',
            'communication': _format_communication(result)
        }, status=status.HTTP_201_CREATED)
        
    except KeyError as e:
        return Response({'error': f'Campo obrigatório: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def inbox(request, practitioner_id):
    """
    Caixa de entrada de um profissional
    GET /api/v1/practitioners/{practitioner_id}/inbox/
    """
    fhir_service = FHIRService(request.user)
    
    try:
        params = {
            'recipient': f'Practitioner/{practitioner_id}',
            '_sort': '-sent',
            '_count': request.query_params.get('limit', 50)
        }
        
        # Filtro de não lidos
        if request.query_params.get('unread') == 'true':
            params['received:missing'] = 'true'
        
        result = fhir_service.search_resources('Communication', params)
        
        messages = []
        unread_count = 0
        
        for entry in result.get('entry', []):
            comm = entry.get('resource', {})
            formatted = _format_communication(comm)
            messages.append(formatted)
            if not comm.get('received'):
                unread_count += 1
        
        return Response({
            'practitioner_id': practitioner_id,
            'total': len(messages),
            'unread': unread_count,
            'messages': messages
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def sent_messages(request, practitioner_id):
    """
    Mensagens enviadas por um profissional
    GET /api/v1/practitioners/{practitioner_id}/sent/
    """
    fhir_service = FHIRService(request.user)
    
    try:
        params = {
            'sender': f'Practitioner/{practitioner_id}',
            '_sort': '-sent'
        }
        
        result = fhir_service.search_resources('Communication', params)
        
        messages = [
            _format_communication(e.get('resource', {}))
            for e in result.get('entry', [])
        ]
        
        return Response({
            'practitioner_id': practitioner_id,
            'total': len(messages),
            'messages': messages
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def patient_communications(request, patient_id):
    """
    Comunicações sobre um paciente
    GET /api/v1/patients/{patient_id}/communications/
    """
    fhir_service = FHIRService(request.user)
    
    try:
        params = {
            'subject': f'Patient/{patient_id}',
            '_sort': '-sent'
        }
        
        result = fhir_service.search_resources('Communication', params)
        
        messages = [
            _format_communication(e.get('resource', {}))
            for e in result.get('entry', [])
        ]
        
        return Response({
            'patient_id': patient_id,
            'total': len(messages),
            'communications': messages
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# =============================================================================
# CommunicationRequest (Pedidos de Parecer)
# =============================================================================

@api_view(['POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def request_opinion(request):
    """
    Solicita parecer de outro profissional
    POST /api/v1/communications/request-opinion/
    """
    fhir_service = FHIRService(request.user)
    
    try:
        data = request.data
        
        comm_request = {
            'resourceType': 'CommunicationRequest',
            'status': 'active',
            'priority': data.get('priority', 'routine'),
            'category': [{
                'coding': [{
                    'system': 'http://terminology.hl7.org/CodeSystem/communication-category',
                    'code': 'instruction',
                    'display': 'Pedido de Parecer'
                }]
            }],
            'subject': {
                'reference': f"Patient/{data['patient_id']}"
            },
            'requester': {
                'reference': f"Practitioner/{data['requester_id']}"
            },
            'recipient': [{
                'reference': f"Practitioner/{data['recipient_id']}"
            }],
            'authoredOn': datetime.now().isoformat(),
            'payload': [{
                'contentString': data['question']
            }],
            'reasonCode': [{
                'text': data.get('clinical_context', '')
            }]
        }
        
        if data.get('encounter_id'):
            comm_request['encounter'] = {
                'reference': f"Encounter/{data['encounter_id']}"
            }
        
        result = fhir_service.create_resource('CommunicationRequest', comm_request)
        
        return Response({
            'id': result.get('id'),
            'message': 'Pedido de parecer enviado',
            'status': 'pending'
        }, status=status.HTTP_201_CREATED)
        
    except KeyError as e:
        return Response({'error': f'Campo obrigatório: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# =============================================================================
# Helpers
# =============================================================================

def _format_communication(comm: dict) -> dict:
    """Formata Communication para resposta"""
    payloads = comm.get('payload', [])
    message = ''
    attachments = []
    
    for payload in payloads:
        if 'contentString' in payload:
            message = payload['contentString']
        elif 'contentAttachment' in payload:
            attachments.append(payload['contentAttachment'])
    
    return {
        'id': comm.get('id'),
        'status': comm.get('status'),
        'category': comm.get('category', [{}])[0].get('coding', [{}])[0].get('display') if comm.get('category') else None,
        'priority': comm.get('priority'),
        'sender': comm.get('sender', {}).get('reference', '').replace('Practitioner/', ''),
        'recipient': comm.get('recipient', [{}])[0].get('reference', '').replace('Practitioner/', '') if comm.get('recipient') else None,
        'patient': comm.get('subject', {}).get('reference', '').replace('Patient/', '') if comm.get('subject') else None,
        'message': message,
        'attachments': attachments,
        'sent': comm.get('sent'),
        'received': comm.get('received'),
        'read': comm.get('received') is not None,
        'in_response_to': comm.get('inResponseTo', [{}])[0].get('reference', '').replace('Communication/', '') if comm.get('inResponseTo') else None
    }


def _get_category_display(code: str) -> str:
    """Retorna display para código de categoria"""
    categories = {
        'alert': 'Alerta',
        'notification': 'Notificação',
        'reminder': 'Lembrete',
        'instruction': 'Instrução'
    }
    return categories.get(code, code)
