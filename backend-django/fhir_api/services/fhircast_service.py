"""
FHIRcast Service - Real-time Clinical Context Synchronization

Sprint 34: FHIRcast Implementation

Features:
- WebSocket hub for event distribution
- EHR context synchronization
- User-facing events (open patient, switch context)
"""

import logging
import asyncio
from typing import Dict, List, Optional, Set, Any
from datetime import datetime
import json
import uuid

logger = logging.getLogger(__name__)


class FHIRcastHub:
    """
    FHIRcast hub for managing subscriptions and events.
    
    Implements FHIRcast 2.0 specification for:
    - Patient-open
    - Patient-close
    - ImagingStudy-open
    - DiagnosticReport-open
    - Encounter-open
    - UserLogout
    - SyncError
    """
    
    # Supported event types
    EVENT_TYPES = {
        'Patient-open': 'Patient context opened',
        'Patient-close': 'Patient context closed',
        'Encounter-open': 'Encounter context opened',
        'Encounter-close': 'Encounter context closed',
        'ImagingStudy-open': 'Imaging study opened',
        'DiagnosticReport-open': 'Diagnostic report opened',
        'DiagnosticReport-select': 'Diagnostic report selected',
        'UserLogout': 'User logged out',
        'SyncError': 'Synchronization error',
    }
    
    def __init__(self):
        # Active subscriptions: {topic: {subscriber_id: callback}}
        self.subscriptions: Dict[str, Dict[str, Any]] = {}
        # Active sessions: {session_id: session_data}
        self.sessions: Dict[str, Dict] = {}
        # Event history for each topic: {topic: [events]}
        self.event_history: Dict[str, List[Dict]] = {}
        # WebSocket connections: {session_id: websocket}
        self.websockets: Dict[str, Any] = {}
    
    def create_session(self, user_id: str, context: Optional[Dict] = None) -> Dict:
        """
        Create a new FHIRcast session.
        
        Returns:
            Session details with hub URL and topic
        """
        session_id = str(uuid.uuid4())
        topic = f"fhircast/{session_id}"
        
        self.sessions[session_id] = {
            'id': session_id,
            'user_id': user_id,
            'topic': topic,
            'context': context or {},
            'created_at': datetime.utcnow().isoformat(),
            'subscribers': set()
        }
        
        self.subscriptions[topic] = {}
        self.event_history[topic] = []
        
        logger.info(f"Created FHIRcast session {session_id} for user {user_id}")
        
        return {
            'session_id': session_id,
            'hub.url': '/api/v1/fhircast/hub',
            'hub.topic': topic,
            'context': context
        }
    
    def subscribe(
        self,
        topic: str,
        subscriber_id: str,
        callback_url: Optional[str] = None,
        events: Optional[List[str]] = None
    ) -> Dict:
        """
        Subscribe to FHIRcast events on a topic.
        
        Args:
            topic: Topic to subscribe to
            subscriber_id: Unique subscriber identifier
            callback_url: Webhook URL for event delivery
            events: List of event types to subscribe to
        
        Returns:
            Subscription confirmation
        """
        if topic not in self.subscriptions:
            self.subscriptions[topic] = {}
        
        self.subscriptions[topic][subscriber_id] = {
            'subscriber_id': subscriber_id,
            'callback_url': callback_url,
            'events': events or list(self.EVENT_TYPES.keys()),
            'subscribed_at': datetime.utcnow().isoformat()
        }
        
        # Add to session if exists
        for session in self.sessions.values():
            if session['topic'] == topic:
                session['subscribers'].add(subscriber_id)
        
        logger.info(f"Subscriber {subscriber_id} subscribed to {topic}")
        
        return {
            'hub.topic': topic,
            'hub.mode': 'subscribe',
            'hub.events': events or list(self.EVENT_TYPES.keys()),
            'subscriber_id': subscriber_id
        }
    
    def unsubscribe(self, topic: str, subscriber_id: str) -> bool:
        """
        Unsubscribe from a topic.
        """
        if topic in self.subscriptions and subscriber_id in self.subscriptions[topic]:
            del self.subscriptions[topic][subscriber_id]
            logger.info(f"Subscriber {subscriber_id} unsubscribed from {topic}")
            return True
        return False
    
    def publish_event(
        self,
        topic: str,
        event_type: str,
        context: Dict,
        version_id: Optional[str] = None
    ) -> Dict:
        """
        Publish a FHIRcast event to all subscribers.
        
        Args:
            topic: Topic to publish to
            event_type: Type of event (e.g., 'Patient-open')
            context: Event context (resource data)
            version_id: Optional anchor context version
        
        Returns:
            Event details
        """
        if event_type not in self.EVENT_TYPES:
            raise ValueError(f"Unknown event type: {event_type}")
        
        event_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        event = {
            'id': event_id,
            'timestamp': timestamp,
            'event': {
                'hub.topic': topic,
                'hub.event': event_type,
                'context': [context]
            }
        }
        
        if version_id:
            event['event']['context.versionId'] = version_id
        
        # Store in history
        if topic not in self.event_history:
            self.event_history[topic] = []
        self.event_history[topic].append(event)
        
        # Keep only last 100 events
        if len(self.event_history[topic]) > 100:
            self.event_history[topic] = self.event_history[topic][-100:]
        
        # Update session context for Patient-open/Encounter-open
        for session in self.sessions.values():
            if session['topic'] == topic:
                if event_type == 'Patient-open':
                    session['context']['patient'] = context
                elif event_type == 'Encounter-open':
                    session['context']['encounter'] = context
                elif event_type == 'Patient-close':
                    session['context'].pop('patient', None)
        
        # Notify subscribers
        self._notify_subscribers(topic, event_type, event)
        
        logger.info(f"Published {event_type} event to {topic}")
        
        return event
    
    def _notify_subscribers(self, topic: str, event_type: str, event: Dict):
        """
        Notify all subscribers of an event.
        
        In production, this would:
        - Send WebSocket messages to connected clients
        - Make HTTP webhooks to callback URLs
        """
        if topic not in self.subscriptions:
            return
        
        import requests
        
        for subscriber_id, sub_data in self.subscriptions[topic].items():
            # Check if subscriber wants this event type
            if sub_data['events'] and event_type not in sub_data['events']:
                continue
            
            # Send webhook if callback URL configured
            if sub_data.get('callback_url'):
                try:
                    requests.post(
                        sub_data['callback_url'],
                        json=event,
                        timeout=5
                    )
                except Exception as e:
                    logger.warning(f"Failed to notify subscriber {subscriber_id}: {e}")
            
            # WebSocket notification would go here
            if subscriber_id in self.websockets:
                # await websocket.send_json(event)
                pass
    
    def get_current_context(self, topic: str) -> Dict:
        """
        Get current context for a topic.
        """
        for session in self.sessions.values():
            if session['topic'] == topic:
                return session['context']
        return {}
    
    def get_event_history(self, topic: str, limit: int = 50) -> List[Dict]:
        """
        Get event history for a topic.
        """
        return self.event_history.get(topic, [])[-limit:]
    
    def get_subscribers(self, topic: str) -> List[Dict]:
        """
        Get all subscribers for a topic.
        """
        return list(self.subscriptions.get(topic, {}).values())


# Singleton instance
_fhircast_hub = None


def get_fhircast_hub() -> FHIRcastHub:
    """Get FHIRcast hub singleton."""
    global _fhircast_hub
    if _fhircast_hub is None:
        _fhircast_hub = FHIRcastHub()
    return _fhircast_hub
