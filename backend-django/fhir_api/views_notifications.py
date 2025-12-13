"""
Views Notifications - Notificações Compulsórias (Vigilância Epidemiológica)
Notificações de doenças para SINAN (Sistema de Informação de Agravos de Notificação)
"""

import logging
from datetime import datetime
from typing import Dict, List
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework import status
from .auth import KeycloakAuthentication
from rest_framework.permissions import IsAuthenticated
from .services.fhir_core import FHIRService

logger = logging.getLogger(__name__)


# Lista de CIDs de notificação compulsória imediata (24h)
NOTIFICACAO_IMEDIATA = {
    'U07.1': 'COVID-19',
    'A00': 'Cólera',
    'A20': 'Peste',
    'A22': 'Antraz',
    'A75': 'Tifo epidêmico',
    'A78': 'Febre Q',
    'A80': 'Poliomielite',
    'A82': 'Raiva humana',
    'A90': 'Dengue',
    'A91': 'Febre hemorrágica da dengue',
    'A92.0': 'Febre Chikungunya',
    'A92.8': 'Febre do Zika vírus',
    'A95': 'Febre amarela',
    'A96.2': 'Febre de Lassa',
    'A98.4': 'Ebola',
    'B05': 'Sarampo',
    'B06': 'Rubéola',
    'B15': 'Hepatite A aguda',
    'J09': 'Influenza (H1N1, H5N1)',
    'P35.0': 'Síndrome da rubéola congênita',
}

# Lista de CIDs de notificação compulsória semanal
NOTIFICACAO_SEMANAL = {
    'A15': 'Tuberculose pulmonar',
    'A16': 'Tuberculose respiratória',
    'A17': 'Tuberculose do sistema nervoso',
    'A30': 'Hanseníase',
    'A50': 'Sífilis congênita',
    'A51': 'Sífilis precoce',
    'A52': 'Sífilis tardia',
    'A53': 'Outras formas de sífilis',
    'B16': 'Hepatite B aguda',
    'B17': 'Hepatite C aguda',
    'B20': 'HIV resultando em doenças infecciosas',
    'B24': 'HIV não especificado',
    'J10': 'Influenza',
    'O98.7': 'HIV complicando gravidez',
}


@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def list_notifiable_conditions(request):
    """
    Lista condições de notificação compulsória
    GET /api/v1/notifications/conditions/
    """
    return Response({
        'immediate': [
            {'cid': k, 'name': v, 'prazo': '24 horas'}
            for k, v in NOTIFICACAO_IMEDIATA.items()
        ],
        'weekly': [
            {'cid': k, 'name': v, 'prazo': '7 dias'}
            for k, v in NOTIFICACAO_SEMANAL.items()
        ]
    })


@api_view(['GET', 'POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def manage_notifications(request):
    """
    Lista ou cria notificações compulsórias
    GET /api/v1/notifications/
    POST /api/v1/notifications/
    """
    fhir_service = FHIRService(request.user)
    
    if request.method == 'GET':
        try:
            params = {
                '_tag': 'compulsory-notification',
                '_sort': '-date',
                '_count': request.query_params.get('limit', 50)
            }
            
            if request.query_params.get('status'):
                params['verification-status'] = request.query_params['status']
            
            result = fhir_service.search_resources('Condition', params)
            
            notifications = []
            for entry in result.get('entry', []):
                condition = entry.get('resource', {})
                notifications.append(_format_notification(condition))
            
            return Response({
                'count': len(notifications),
                'results': notifications
            })
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'POST':
        try:
            data = request.data
            
            cid_code = data['cid_code']
            
            # Determinar urgência
            is_immediate = cid_code in NOTIFICACAO_IMEDIATA or cid_code[:3] in NOTIFICACAO_IMEDIATA
            disease_name = NOTIFICACAO_IMEDIATA.get(cid_code) or NOTIFICACAO_SEMANAL.get(cid_code) or data.get('disease_name', 'Agravo')
            
            # Criar Condition com tag de notificação
            condition = {
                'resourceType': 'Condition',
                'meta': {
                    'tag': [{
                        'system': 'http://openehrcore.com/tags',
                        'code': 'compulsory-notification'
                    }]
                },
                'clinicalStatus': {
                    'coding': [{
                        'system': 'http://terminology.hl7.org/CodeSystem/condition-clinical',
                        'code': 'active'
                    }]
                },
                'verificationStatus': {
                    'coding': [{
                        'system': 'http://terminology.hl7.org/CodeSystem/condition-ver-status',
                        'code': data.get('verification_status', 'confirmed')
                    }]
                },
                'category': [{
                    'coding': [{
                        'system': 'http://terminology.hl7.org/CodeSystem/condition-category',
                        'code': 'encounter-diagnosis'
                    }]
                }],
                'severity': {
                    'coding': [{
                        'system': 'http://snomed.info/sct',
                        'code': '24484000' if is_immediate else '255604002',
                        'display': 'Severe' if is_immediate else 'Mild'
                    }]
                },
                'code': {
                    'coding': [{
                        'system': 'http://hl7.org/fhir/sid/icd-10',
                        'code': cid_code,
                        'display': disease_name
                    }]
                },
                'subject': {
                    'reference': f"Patient/{data['patient_id']}"
                },
                'onsetDateTime': data.get('onset_date', datetime.now().isoformat()),
                'recordedDate': datetime.now().isoformat(),
                'recorder': {
                    'reference': f"Practitioner/{data['practitioner_id']}"
                },
                'note': [{
                    'text': data.get('notes', '')
                }] if data.get('notes') else [],
                'extension': [
                    {
                        'url': 'http://openehrcore.com/fhir/StructureDefinition/notification-status',
                        'valueString': 'pending'
                    },
                    {
                        'url': 'http://openehrcore.com/fhir/StructureDefinition/notification-urgency',
                        'valueString': 'immediate' if is_immediate else 'weekly'
                    }
                ]
            }
            
            if data.get('encounter_id'):
                condition['encounter'] = {
                    'reference': f"Encounter/{data['encounter_id']}"
                }
            
            result = fhir_service.create_resource('Condition', condition)
            
            # Criar alerta automático se imediato
            alert_message = None
            if is_immediate:
                alert_message = f"⚠️ NOTIFICAÇÃO IMEDIATA: {disease_name} ({cid_code}) - Prazo: 24 horas"
            
            return Response({
                'id': result.get('id'),
                'message': 'Notificação criada',
                'notification': _format_notification(result),
                'alert': alert_message,
                'urgency': 'immediate' if is_immediate else 'weekly',
                'deadline': '24 horas' if is_immediate else '7 dias'
            }, status=status.HTTP_201_CREATED)
            
        except KeyError as e:
            return Response({'error': f'Campo obrigatório: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Erro ao criar notificação: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def pending_notifications(request):
    """
    Lista notificações pendentes de envio ao SINAN
    GET /api/v1/notifications/pending/
    """
    fhir_service = FHIRService(request.user)
    
    try:
        # Buscar conditions com tag de notificação e status pendente
        params = {
            '_tag': 'compulsory-notification',
            '_sort': '-date'
        }
        
        result = fhir_service.search_resources('Condition', params)
        
        pending = []
        for entry in result.get('entry', []):
            condition = entry.get('resource', {})
            
            # Verificar se está pendente
            extensions = condition.get('extension', [])
            status_ext = next((e for e in extensions if 'notification-status' in e.get('url', '')), None)
            
            if status_ext and status_ext.get('valueString') == 'pending':
                pending.append(_format_notification(condition))
        
        return Response({
            'count': len(pending),
            'results': pending
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def send_to_sinan(request, notification_id):
    """
    Envia notificação ao SINAN
    POST /api/v1/notifications/{notification_id}/send/
    """
    fhir_service = FHIRService(request.user)
    
    try:
        condition = fhir_service.get_resource('Condition', notification_id)
        if not condition:
            return Response({'error': 'Notificação não encontrada'}, status=status.HTTP_404_NOT_FOUND)
        
        # Simular envio ao SINAN (em produção, integrar com API do SINAN)
        # Atualizar status para "sent"
        extensions = condition.get('extension', [])
        for ext in extensions:
            if 'notification-status' in ext.get('url', ''):
                ext['valueString'] = 'sent'
        
        # Adicionar dados do envio
        extensions.append({
            'url': 'http://openehrcore.com/fhir/StructureDefinition/notification-sent-date',
            'valueDateTime': datetime.now().isoformat()
        })
        
        condition['extension'] = extensions
        fhir_service.update_resource('Condition', notification_id, condition)
        
        # Em produção: enviar para API SINAN
        sinan_protocol = f"SINAN-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        return Response({
            'message': 'Notificação enviada ao SINAN',
            'notification_id': notification_id,
            'sinan_protocol': sinan_protocol,
            'sent_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erro ao enviar ao SINAN: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def notification_stats(request):
    """
    Estatísticas de notificações
    GET /api/v1/notifications/stats/
    """
    fhir_service = FHIRService(request.user)
    
    try:
        result = fhir_service.search_resources('Condition', {
            '_tag': 'compulsory-notification'
        })
        
        stats = {
            'total': 0,
            'pending': 0,
            'sent': 0,
            'by_disease': {},
            'by_urgency': {'immediate': 0, 'weekly': 0}
        }
        
        for entry in result.get('entry', []):
            condition = entry.get('resource', {})
            stats['total'] += 1
            
            # Status
            extensions = condition.get('extension', [])
            status_ext = next((e for e in extensions if 'notification-status' in e.get('url', '')), None)
            if status_ext:
                if status_ext.get('valueString') == 'pending':
                    stats['pending'] += 1
                elif status_ext.get('valueString') == 'sent':
                    stats['sent'] += 1
            
            # Urgência
            urgency_ext = next((e for e in extensions if 'notification-urgency' in e.get('url', '')), None)
            if urgency_ext:
                urgency = urgency_ext.get('valueString', 'weekly')
                stats['by_urgency'][urgency] = stats['by_urgency'].get(urgency, 0) + 1
            
            # Por doença
            code = condition.get('code', {}).get('coding', [{}])[0]
            disease = code.get('display', code.get('code', 'Unknown'))
            stats['by_disease'][disease] = stats['by_disease'].get(disease, 0) + 1
        
        return Response(stats)
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def check_notifiable(request):
    """
    Verifica se um CID é de notificação compulsória
    POST /api/v1/notifications/check/
    
    Body: {"cid_code": "A90"}
    """
    cid_code = request.data.get('cid_code', '')
    
    # Verificar código exato ou prefixo
    is_immediate = cid_code in NOTIFICACAO_IMEDIATA or cid_code[:3] in NOTIFICACAO_IMEDIATA
    is_weekly = cid_code in NOTIFICACAO_SEMANAL or cid_code[:3] in NOTIFICACAO_SEMANAL
    
    if is_immediate:
        disease = NOTIFICACAO_IMEDIATA.get(cid_code) or NOTIFICACAO_IMEDIATA.get(cid_code[:3])
        return Response({
            'is_notifiable': True,
            'urgency': 'immediate',
            'deadline': '24 horas',
            'disease': disease,
            'cid': cid_code,
            'alert': f'⚠️ Notificação IMEDIATA obrigatória: {disease}'
        })
    elif is_weekly:
        disease = NOTIFICACAO_SEMANAL.get(cid_code) or NOTIFICACAO_SEMANAL.get(cid_code[:3])
        return Response({
            'is_notifiable': True,
            'urgency': 'weekly',
            'deadline': '7 dias',
            'disease': disease,
            'cid': cid_code,
            'alert': f'ℹ️ Notificação semanal obrigatória: {disease}'
        })
    else:
        return Response({
            'is_notifiable': False,
            'cid': cid_code,
            'message': 'Este CID não é de notificação compulsória'
        })


def _format_notification(condition: dict) -> dict:
    """Formata Condition como notificação"""
    code = condition.get('code', {}).get('coding', [{}])[0]
    extensions = condition.get('extension', [])
    
    status_ext = next((e for e in extensions if 'notification-status' in e.get('url', '')), {})
    urgency_ext = next((e for e in extensions if 'notification-urgency' in e.get('url', '')), {})
    sent_ext = next((e for e in extensions if 'notification-sent-date' in e.get('url', '')), {})
    
    return {
        'id': condition.get('id'),
        'cid_code': code.get('code'),
        'disease': code.get('display'),
        'patient': condition.get('subject', {}).get('reference', '').replace('Patient/', ''),
        'practitioner': condition.get('recorder', {}).get('reference', '').replace('Practitioner/', ''),
        'onset_date': condition.get('onsetDateTime'),
        'recorded_date': condition.get('recordedDate'),
        'verification_status': condition.get('verificationStatus', {}).get('coding', [{}])[0].get('code'),
        'notification_status': status_ext.get('valueString', 'pending'),
        'urgency': urgency_ext.get('valueString', 'weekly'),
        'sent_date': sent_ext.get('valueDateTime'),
        'notes': condition.get('note', [{}])[0].get('text') if condition.get('note') else None
    }
