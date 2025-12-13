"""
HL7 Integration Views

Sprint 36: HL7 ADT and Orders/Results Integration
"""

import logging
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .authentication import KeycloakAuthentication
from .services.hl7_service import HL7Service, HL7Message, ADTEventType

logger = logging.getLogger(__name__)


@api_view(['POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def generate_adt(request):
    """
    Generate an ADT message from FHIR resources.
    
    POST /api/v1/hl7/adt/generate
    
    Body:
        {
            "patient": {...},
            "event_type": "A01",
            "encounter": {...}  # optional
        }
    """
    patient = request.data.get('patient', {})
    event_type_str = request.data.get('event_type', 'A04')
    encounter = request.data.get('encounter')
    
    if not patient:
        return Response({
            'error': 'patient is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        event_type = ADTEventType(event_type_str)
    except ValueError:
        return Response({
            'error': f'Invalid event type: {event_type_str}',
            'valid_types': [e.value for e in ADTEventType]
        }, status=status.HTTP_400_BAD_REQUEST)
    
    message = HL7Service.create_adt_message(patient, event_type, encounter)
    
    return Response({
        'message_type': message.message_type,
        'hl7_message': message.to_string(),
        'segments': [seg.to_string() for seg in message.segments]
    })


@api_view(['POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def parse_adt(request):
    """
    Parse an ADT message to FHIR resources.
    
    POST /api/v1/hl7/adt/parse
    
    Body:
        {
            "message": "MSH|^~\\&|..."
        }
    """
    message_str = request.data.get('message', '')
    
    if not message_str:
        return Response({
            'error': 'message is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        message = HL7Message.from_string(message_str)
        fhir_resources = HL7Service.parse_adt_to_fhir(message)
        
        return Response({
            'message_type': message.message_type,
            'resources': fhir_resources
        })
    except Exception as e:
        return Response({
            'error': f'Failed to parse message: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def generate_orm(request):
    """
    Generate an ORM^O01 order message.
    
    POST /api/v1/hl7/orm/generate
    
    Body:
        {
            "service_request": {...},
            "patient": {...}
        }
    """
    service_request = request.data.get('service_request', {})
    patient = request.data.get('patient', {})
    
    if not service_request or not patient:
        return Response({
            'error': 'service_request and patient are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    message = HL7Service.create_orm_message(service_request, patient)
    
    return Response({
        'message_type': message.message_type,
        'hl7_message': message.to_string(),
        'segments': [seg.to_string() for seg in message.segments]
    })


@api_view(['POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def parse_oru(request):
    """
    Parse an ORU^R01 result message to FHIR Observations.
    
    POST /api/v1/hl7/oru/parse
    
    Body:
        {
            "message": "MSH|^~\\&|..."
        }
    """
    message_str = request.data.get('message', '')
    
    if not message_str:
        return Response({
            'error': 'message is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        message = HL7Message.from_string(message_str)
        observations = HL7Service.parse_oru_to_fhir(message)
        
        return Response({
            'message_type': message.message_type,
            'observation_count': len(observations),
            'observations': observations
        })
    except Exception as e:
        return Response({
            'error': f'Failed to parse message: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def hl7_info(request):
    """
    Get HL7 integration info and supported message types.
    
    GET /api/v1/hl7/info
    """
    return Response({
        'version': '2.5.1',
        'supported_messages': {
            'ADT': {
                'description': 'Admit, Discharge, Transfer',
                'events': [
                    {'code': 'A01', 'name': 'Admit'},
                    {'code': 'A02', 'name': 'Transfer'},
                    {'code': 'A03', 'name': 'Discharge'},
                    {'code': 'A04', 'name': 'Register'},
                    {'code': 'A08', 'name': 'Update Patient'},
                    {'code': 'A11', 'name': 'Cancel Admit'},
                ]
            },
            'ORM': {
                'description': 'Order Entry',
                'events': [
                    {'code': 'O01', 'name': 'Order'}
                ]
            },
            'ORU': {
                'description': 'Observation Result',
                'events': [
                    {'code': 'R01', 'name': 'Result'}
                ]
            }
        },
        'endpoints': {
            'generate_adt': 'POST /api/v1/hl7/adt/generate',
            'parse_adt': 'POST /api/v1/hl7/adt/parse',
            'generate_orm': 'POST /api/v1/hl7/orm/generate',
            'parse_oru': 'POST /api/v1/hl7/oru/parse',
        }
    })
