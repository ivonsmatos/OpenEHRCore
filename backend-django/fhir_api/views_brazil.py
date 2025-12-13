"""
Views for Brazil Essential Integrations

Sprint 37: PIX, WhatsApp, Telemedicine

Endpoints:
- /api/v1/pix/
- /api/v1/whatsapp/
- /api/v1/telemedicine/
"""

import logging
from datetime import datetime
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .authentication import KeycloakAuthentication
from .services.pix_service import PixService
from .services.whatsapp_service import WhatsAppService, TemplateType
from .services.telemedicine_service import TelemedicineService, SessionStatus

logger = logging.getLogger(__name__)


# ============================================================================
# PIX ENDPOINTS
# ============================================================================

@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def pix_info(request):
    """
    Get PIX configuration info.
    
    GET /api/v1/pix/info
    """
    return Response({
        'service': 'PIX',
        'version': '1.0',
        'features': [
            'QR Code EMV (BR Code)',
            'Payment tracking',
            'Webhook support',
            'FHIR PaymentNotice'
        ],
        'configured': bool(PixService.PIX_KEY)
    })


@api_view(['POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def create_pix_payment(request):
    """
    Create a new PIX payment.
    
    POST /api/v1/pix/payments/
    
    Body:
        {
            "amount": 150.00,
            "description": "Consulta médica",
            "payer_name": "João Silva",
            "payer_cpf": "123.456.789-00",
            "reference_id": "CONS-001",
            "expiration_minutes": 30
        }
    """
    try:
        data = request.data
        
        payment = PixService.create_payment(
            amount=float(data['amount']),
            description=data.get('description', 'Pagamento'),
            payer_name=data.get('payer_name'),
            payer_cpf=data.get('payer_cpf'),
            reference_id=data.get('reference_id'),
            expiration_minutes=data.get('expiration_minutes', 30)
        )
        
        return Response(payment.to_dict(), status=status.HTTP_201_CREATED)
        
    except KeyError as e:
        return Response({
            'error': f'Missing field: {e}'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Error creating PIX payment: {e}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def list_pix_payments(request):
    """
    List PIX payments.
    
    GET /api/v1/pix/payments/
    GET /api/v1/pix/payments/?status=pending
    """
    status_filter = request.query_params.get('status')
    limit = int(request.query_params.get('limit', 50))
    
    payments = PixService.list_payments(status=status_filter, limit=limit)
    
    return Response({
        'count': len(payments),
        'payments': payments
    })


@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def get_pix_payment(request, payment_id):
    """
    Get a specific payment.
    
    GET /api/v1/pix/payments/{id}/
    """
    payment = PixService.get_payment(payment_id)
    
    if not payment:
        return Response({
            'error': 'Payment not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    return Response(payment.to_dict())


@api_view(['POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def pix_webhook(request):
    """
    Handle PIX webhook from bank.
    
    POST /api/v1/pix/webhook/
    """
    try:
        data = request.data
        payment_id = data.get('txid') or data.get('payment_id')
        
        if not payment_id:
            return Response({
                'error': 'Missing payment_id or txid'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        payment = PixService.confirm_payment(payment_id)
        
        if payment:
            return Response({
                'status': 'confirmed',
                'payment': payment.to_dict()
            })
        else:
            return Response({
                'error': 'Payment not found'
            }, status=status.HTTP_404_NOT_FOUND)
            
    except Exception as e:
        logger.error(f"PIX webhook error: {e}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================================================
# WHATSAPP ENDPOINTS
# ============================================================================

@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def whatsapp_info(request):
    """
    Get WhatsApp service info.
    
    GET /api/v1/whatsapp/info
    """
    return Response({
        'service': 'WhatsApp Business',
        'version': '1.0',
        'templates': [t.value for t in TemplateType],
        'configured': bool(WhatsAppService.ACCESS_TOKEN)
    })


@api_view(['POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def send_whatsapp_message(request):
    """
    Send a WhatsApp template message.
    
    POST /api/v1/whatsapp/send/
    
    Body:
        {
            "to": "5511999998888",
            "template": "appointment_reminder",
            "variables": ["João", "15/12/2024", "14:00", "Dr. Silva"],
            "patient_id": "patient-123"
        }
    """
    try:
        data = request.data
        
        template = TemplateType(data['template'])
        
        message = WhatsAppService.send_template_message(
            to=data['to'],
            template=template,
            variables=data['variables'],
            patient_id=data.get('patient_id')
        )
        
        return Response(message.to_dict(), status=status.HTTP_201_CREATED)
        
    except ValueError as e:
        return Response({
            'error': f'Invalid template: {e}'
        }, status=status.HTTP_400_BAD_REQUEST)
    except KeyError as e:
        return Response({
            'error': f'Missing field: {e}'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Error sending WhatsApp: {e}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def send_appointment_reminder(request):
    """
    Send appointment reminder via WhatsApp.
    
    POST /api/v1/whatsapp/appointment-reminder/
    
    Body:
        {
            "patient_name": "João Silva",
            "patient_phone": "5511999998888",
            "appointment_date": "15/12/2024",
            "appointment_time": "14:00",
            "doctor_name": "Dr. Carlos Santos",
            "patient_id": "patient-123"
        }
    """
    try:
        data = request.data
        
        message = WhatsAppService.send_appointment_reminder(
            patient_name=data['patient_name'],
            patient_phone=data['patient_phone'],
            appointment_date=data['appointment_date'],
            appointment_time=data['appointment_time'],
            doctor_name=data['doctor_name'],
            patient_id=data.get('patient_id')
        )
        
        return Response(message.to_dict(), status=status.HTTP_201_CREATED)
        
    except KeyError as e:
        return Response({
            'error': f'Missing field: {e}'
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def list_whatsapp_messages(request):
    """
    List WhatsApp messages.
    
    GET /api/v1/whatsapp/messages/
    GET /api/v1/whatsapp/messages/?patient_id=123
    """
    patient_id = request.query_params.get('patient_id')
    status_filter = request.query_params.get('status')
    
    messages = WhatsAppService.list_messages(
        patient_id=patient_id,
        status=status_filter
    )
    
    return Response({
        'count': len(messages),
        'messages': messages
    })


@api_view(['POST'])
def whatsapp_webhook(request):
    """
    Handle WhatsApp webhook from Meta.
    
    POST /api/v1/whatsapp/webhook/
    """
    # Verify webhook (Meta sends GET for verification)
    if request.method == 'GET':
        mode = request.query_params.get('hub.mode')
        token = request.query_params.get('hub.verify_token')
        challenge = request.query_params.get('hub.challenge')
        
        # Verify token matches
        if mode == 'subscribe':
            return Response(int(challenge) if challenge else '')
    
    # Process webhook payload
    result = WhatsAppService.handle_webhook(request.data)
    return Response(result)


# ============================================================================
# TELEMEDICINE ENDPOINTS
# ============================================================================

@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def telemedicine_info(request):
    """
    Get telemedicine service info.
    
    GET /api/v1/telemedicine/info
    """
    return Response({
        'service': 'Telemedicine',
        'version': '1.0',
        'provider': TelemedicineService.PROVIDER,
        'features': [
            'Video consultation rooms',
            'Session management',
            'FHIR Encounter integration',
            'CFM 2.314/2022 compliant'
        ]
    })


@api_view(['POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def create_telemedicine_session(request):
    """
    Create a telemedicine session.
    
    POST /api/v1/telemedicine/sessions/
    
    Body:
        {
            "patient_id": "patient-123",
            "practitioner_id": "practitioner-456",
            "scheduled_start": "2024-12-15T14:00:00",
            "duration_minutes": 30,
            "patient_name": "João Silva",
            "practitioner_name": "Dr. Carlos Santos"
        }
    """
    try:
        data = request.data
        
        scheduled_start = datetime.fromisoformat(data['scheduled_start'])
        
        session = TelemedicineService.create_session(
            patient_id=data['patient_id'],
            practitioner_id=data['practitioner_id'],
            scheduled_start=scheduled_start,
            duration_minutes=data.get('duration_minutes', 30),
            patient_name=data.get('patient_name', 'Paciente'),
            practitioner_name=data.get('practitioner_name', 'Médico'),
            encounter_id=data.get('encounter_id')
        )
        
        return Response(session.to_dict(), status=status.HTTP_201_CREATED)
        
    except KeyError as e:
        return Response({
            'error': f'Missing field: {e}'
        }, status=status.HTTP_400_BAD_REQUEST)
    except ValueError as e:
        return Response({
            'error': f'Invalid date format: {e}'
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def list_telemedicine_sessions(request):
    """
    List telemedicine sessions.
    
    GET /api/v1/telemedicine/sessions/
    GET /api/v1/telemedicine/sessions/?practitioner_id=123
    GET /api/v1/telemedicine/sessions/?patient_id=456
    """
    patient_id = request.query_params.get('patient_id')
    practitioner_id = request.query_params.get('practitioner_id')
    status_filter = request.query_params.get('status')
    
    session_status = SessionStatus(status_filter) if status_filter else None
    
    sessions = TelemedicineService.list_sessions(
        patient_id=patient_id,
        practitioner_id=practitioner_id,
        status=session_status
    )
    
    return Response({
        'count': len(sessions),
        'sessions': sessions
    })


@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def get_telemedicine_session(request, session_id):
    """
    Get a specific session.
    
    GET /api/v1/telemedicine/sessions/{id}/
    """
    session = TelemedicineService.get_session(session_id)
    
    if not session:
        return Response({
            'error': 'Session not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    return Response(session.to_dict())


@api_view(['POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def start_telemedicine_session(request, session_id):
    """
    Start a telemedicine session.
    
    POST /api/v1/telemedicine/sessions/{id}/start
    """
    try:
        started_by = request.data.get('started_by') or request.user.id
        
        session = TelemedicineService.start_session(session_id, started_by)
        
        if not session:
            return Response({
                'error': 'Session not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        return Response(session.to_dict())
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def end_telemedicine_session(request, session_id):
    """
    End a telemedicine session.
    
    POST /api/v1/telemedicine/sessions/{id}/end
    
    Body:
        {"notes": "Consulta realizada com sucesso"}
    """
    notes = request.data.get('notes')
    
    session = TelemedicineService.end_session(session_id, notes)
    
    if not session:
        return Response({
            'error': 'Session not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    return Response(session.to_dict())


@api_view(['POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def cancel_telemedicine_session(request, session_id):
    """
    Cancel a telemedicine session.
    
    POST /api/v1/telemedicine/sessions/{id}/cancel
    """
    reason = request.data.get('reason')
    
    session = TelemedicineService.cancel_session(session_id, reason)
    
    if not session:
        return Response({
            'error': 'Session not found or cannot be cancelled'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(session.to_dict())


@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def upcoming_sessions(request, practitioner_id):
    """
    Get upcoming sessions for a practitioner.
    
    GET /api/v1/telemedicine/practitioners/{id}/upcoming
    """
    hours = int(request.query_params.get('hours', 24))
    
    sessions = TelemedicineService.get_upcoming_sessions(practitioner_id, hours)
    
    return Response({
        'practitioner_id': practitioner_id,
        'count': len(sessions),
        'sessions': sessions
    })
