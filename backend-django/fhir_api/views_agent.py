"""
Agent Endpoint - Receives messages from on-premise agents.

Sprint 37: Agent Integration
"""

import logging
from datetime import datetime
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .authentication import KeycloakAuthentication
from .services.hl7_service import HL7Service, HL7Message

logger = logging.getLogger(__name__)


# In-memory agent registry (use Redis/DB in production)
_registered_agents = {}


@api_view(['POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def receive_hl7_from_agent(request):
    """
    Receive HL7 message from on-premise agent.
    
    POST /api/v1/agent/hl7/receive
    
    Body:
        {
            "type": "hl7_message",
            "timestamp": "2024-12-13T12:00:00",
            "source": "192.168.1.100",
            "payload": "MSH|^~\\&|..."
        }
    """
    try:
        data = request.data
        
        agent_id = request.headers.get('X-Agent-ID', 'unknown')
        hl7_payload = data.get('payload', '')
        source = data.get('source', 'unknown')
        
        logger.info(f"Received HL7 from agent {agent_id}, source {source}")
        
        # Parse HL7 message
        try:
            message = HL7Message.from_string(hl7_payload)
            msg_type = message.message_type
        except Exception as e:
            logger.warning(f"Failed to parse HL7: {e}")
            msg_type = "UNKNOWN"
        
        # Process based on message type
        result = _process_hl7_message(msg_type, hl7_payload, source, agent_id)
        
        return Response({
            'status': 'received',
            'message_type': msg_type,
            'processed': result.get('processed', False),
            'fhir_resources': result.get('resources', [])
        })
        
    except Exception as e:
        logger.error(f"Error processing agent HL7: {e}")
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def _process_hl7_message(msg_type: str, payload: str, source: str, agent_id: str) -> dict:
    """Process HL7 message based on type."""
    
    resources = []
    
    if msg_type.startswith('ADT'):
        # Admission/Discharge/Transfer
        try:
            message = HL7Message.from_string(payload)
            fhir = HL7Service.parse_adt_to_fhir(message)
            resources = list(fhir.keys())
            # TODO: Save to FHIR server
            logger.info(f"Parsed ADT to FHIR: {resources}")
        except Exception as e:
            logger.error(f"ADT processing error: {e}")
    
    elif msg_type.startswith('ORU'):
        # Lab Results
        try:
            message = HL7Message.from_string(payload)
            fhir = HL7Service.parse_oru_to_fhir(message)
            resources = ['observations']
            logger.info(f"Parsed ORU to {len(fhir.get('observations', []))} observations")
        except Exception as e:
            logger.error(f"ORU processing error: {e}")
    
    elif msg_type.startswith('ORM'):
        # Orders
        logger.info(f"Received ORM order message")
        resources = ['service_request']
    
    return {
        'processed': True,
        'resources': resources
    }


@api_view(['POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def register_agent(request):
    """
    Register an on-premise agent.
    
    POST /api/v1/agent/register
    
    Body:
        {
            "agent_name": "Hospital Lab Agent",
            "capabilities": ["hl7", "mllp"],
            "version": "1.0.0"
        }
    """
    try:
        data = request.data
        agent_id = request.headers.get('X-Agent-ID') or str(hash(data.get('agent_name', '') + str(datetime.now())))[:12]
        
        agent_info = {
            'id': agent_id,
            'name': data.get('agent_name', 'Unknown Agent'),
            'capabilities': data.get('capabilities', []),
            'version': data.get('version', '1.0.0'),
            'registered_at': datetime.now().isoformat(),
            'last_seen': datetime.now().isoformat(),
            'status': 'online'
        }
        
        _registered_agents[agent_id] = agent_info
        
        logger.info(f"Agent registered: {agent_id} - {agent_info['name']}")
        
        return Response({
            'status': 'registered',
            'agent_id': agent_id,
            'agent': agent_info
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Agent registration error: {e}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def agent_heartbeat(request):
    """
    Agent heartbeat/status update.
    
    POST /api/v1/agent/heartbeat
    """
    agent_id = request.headers.get('X-Agent-ID')
    
    if agent_id and agent_id in _registered_agents:
        _registered_agents[agent_id]['last_seen'] = datetime.now().isoformat()
        _registered_agents[agent_id]['status'] = 'online'
        
        # Update stats if provided
        stats = request.data.get('stats', {})
        if stats:
            _registered_agents[agent_id]['stats'] = stats
        
        return Response({'status': 'ok'})
    
    return Response({'status': 'unknown_agent'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def list_agents(request):
    """
    List registered agents.
    
    GET /api/v1/agent/list
    """
    # Check for stale agents
    now = datetime.now()
    for agent_id, info in _registered_agents.items():
        last_seen = datetime.fromisoformat(info['last_seen'])
        if (now - last_seen).total_seconds() > 120:  # 2 minutes
            info['status'] = 'offline'
    
    return Response({
        'count': len(_registered_agents),
        'agents': list(_registered_agents.values())
    })


@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def agent_messages(request):
    """
    Get pending messages for agent (polling fallback).
    
    GET /api/v1/agent/messages
    """
    agent_id = request.headers.get('X-Agent-ID')
    
    # TODO: Implement message queue
    # For now, return empty
    return Response({
        'messages': []
    })


@api_view(['POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def push_to_agent(request, agent_id):
    """
    Push message to agent.
    
    POST /api/v1/agent/{agent_id}/push
    
    Body:
        {
            "type": "hl7_send",
            "destination": "192.168.1.50:2575",
            "message": "MSH|..."
        }
    """
    if agent_id not in _registered_agents:
        return Response({
            'error': 'Agent not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # TODO: Implement WebSocket push or queue message
    logger.info(f"Push request to agent {agent_id}: {request.data.get('type')}")
    
    return Response({
        'status': 'queued',
        'agent_id': agent_id
    })
