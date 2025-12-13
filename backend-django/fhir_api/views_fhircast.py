"""
FHIRcast Views - Real-time Context Synchronization

Sprint 34: FHIRcast endpoints
"""

import logging
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny

from .authentication import KeycloakAuthentication
from .services.fhircast_service import get_fhircast_hub

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([AllowAny])
def fhircast_well_known(request):
    """
    FHIRcast .well-known endpoint.
    
    GET /api/v1/.well-known/fhircast-configuration
    """
    base_url = request.build_absolute_uri('/api/v1').rstrip('/')
    
    return Response({
        'eventsSupported': list(get_fhircast_hub().EVENT_TYPES.keys()),
        'websocketSupport': True,
        'webhookSupport': True,
        'fhircastVersion': '2.0',
        'hubUrl': f'{base_url}/fhircast/hub',
        'subscriberUrl': f'{base_url}/fhircast/subscribe'
    })


@api_view(['POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def create_session(request):
    """
    Create a new FHIRcast session.
    
    POST /api/v1/fhircast/session
    
    Body:
        {
            "context": {"patient": "123"}
        }
    """
    user_id = getattr(request.user, 'user_id', 'anonymous')
    context = request.data.get('context', {})
    
    hub = get_fhircast_hub()
    session = hub.create_session(user_id, context)
    
    return Response(session, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def subscribe(request):
    """
    Subscribe to FHIRcast events.
    
    POST /api/v1/fhircast/subscribe
    
    Body:
        {
            "hub.topic": "fhircast/session-id",
            "hub.callback": "https://app.example.com/callback",
            "hub.events": ["Patient-open", "Encounter-open"]
        }
    """
    topic = request.data.get('hub.topic')
    callback = request.data.get('hub.callback')
    events = request.data.get('hub.events')
    
    if not topic:
        return Response({
            'error': 'hub.topic is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    subscriber_id = str(request.data.get('subscriber_id', request.user.user_id if hasattr(request.user, 'user_id') else 'subscriber'))
    
    hub = get_fhircast_hub()
    result = hub.subscribe(
        topic=topic,
        subscriber_id=subscriber_id,
        callback_url=callback,
        events=events
    )
    
    return Response(result)


@api_view(['POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def unsubscribe(request):
    """
    Unsubscribe from FHIRcast events.
    
    POST /api/v1/fhircast/unsubscribe
    """
    topic = request.data.get('hub.topic')
    subscriber_id = request.data.get('subscriber_id')
    
    if not topic or not subscriber_id:
        return Response({
            'error': 'hub.topic and subscriber_id are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    hub = get_fhircast_hub()
    success = hub.unsubscribe(topic, subscriber_id)
    
    return Response({'success': success})


@api_view(['POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def publish_event(request, topic):
    """
    Publish a FHIRcast event.
    
    POST /api/v1/fhircast/{topic}
    
    Body:
        {
            "hub.event": "Patient-open",
            "context": {
                "resourceType": "Patient",
                "id": "123",
                "name": [{"family": "Silva"}]
            }
        }
    """
    event_type = request.data.get('hub.event')
    context = request.data.get('context', {})
    version_id = request.data.get('context.versionId')
    
    if not event_type:
        return Response({
            'error': 'hub.event is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    hub = get_fhircast_hub()
    
    try:
        event = hub.publish_event(
            topic=f"fhircast/{topic}",
            event_type=event_type,
            context=context,
            version_id=version_id
        )
        return Response(event, status=status.HTTP_201_CREATED)
    except ValueError as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def get_context(request, topic):
    """
    Get current context for a FHIRcast topic.
    
    GET /api/v1/fhircast/{topic}
    """
    hub = get_fhircast_hub()
    context = hub.get_current_context(f"fhircast/{topic}")
    
    return Response({
        'hub.topic': f"fhircast/{topic}",
        'context': context
    })


@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def get_history(request, topic):
    """
    Get event history for a FHIRcast topic.
    
    GET /api/v1/fhircast/{topic}/history
    """
    limit = int(request.query_params.get('limit', 50))
    
    hub = get_fhircast_hub()
    history = hub.get_event_history(f"fhircast/{topic}", limit)
    
    return Response({
        'hub.topic': f"fhircast/{topic}",
        'events': history,
        'count': len(history)
    })


@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def get_subscribers(request, topic):
    """
    Get subscribers for a FHIRcast topic.
    
    GET /api/v1/fhircast/{topic}/subscribers
    """
    hub = get_fhircast_hub()
    subscribers = hub.get_subscribers(f"fhircast/{topic}")
    
    return Response({
        'hub.topic': f"fhircast/{topic}",
        'subscribers': subscribers,
        'count': len(subscribers)
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def event_types(request):
    """
    List supported FHIRcast event types.
    
    GET /api/v1/fhircast/events
    """
    hub = get_fhircast_hub()
    
    return Response({
        'events': [
            {'type': event, 'description': desc}
            for event, desc in hub.EVENT_TYPES.items()
        ]
    })
