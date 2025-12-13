"""
FHIR Subscriptions - Webhook system for FHIR resource events

Sprint 28: FHIR Subscriptions

Based on FHIR R4 Subscription resource:
- Trigger on resource create/update/delete
- Send webhooks to registered endpoints
- Support for REST Hook and WebSocket channels
"""

import logging
import json
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime
from django.db import models
from django.conf import settings

logger = logging.getLogger(__name__)


class SubscriptionChannel:
    """Subscription channel types."""
    REST_HOOK = 'rest-hook'
    WEBSOCKET = 'websocket'
    EMAIL = 'email'
    MESSAGE = 'message'  # Mattermost integration


class SubscriptionStatus:
    """Subscription status values."""
    REQUESTED = 'requested'
    ACTIVE = 'active'
    ERROR = 'error'
    OFF = 'off'


class SubscriptionService:
    """
    Service for managing FHIR Subscriptions.
    
    Subscriptions allow applications to receive notifications when
    resources are created, updated, or deleted.
    """
    
    def __init__(self):
        self.subscriptions: Dict[str, Dict] = {}
        self._load_subscriptions()
    
    def _load_subscriptions(self):
        """Load subscriptions from storage."""
        # In production, load from database
        # For now, use in-memory storage
        self.subscriptions = {}
    
    def create_subscription(
        self,
        criteria: str,
        channel_type: str,
        endpoint: str,
        payload_type: str = 'application/fhir+json',
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Create a new subscription.
        
        Args:
            criteria: FHIR search criteria (e.g., "Patient?name=Smith")
            channel_type: Type of channel (rest-hook, websocket, message)
            endpoint: URL to receive notifications
            payload_type: MIME type of payload
            headers: Additional headers for REST hook
        
        Returns:
            Created subscription resource
        """
        import uuid
        
        subscription_id = str(uuid.uuid4())
        
        subscription = {
            'resourceType': 'Subscription',
            'id': subscription_id,
            'status': SubscriptionStatus.ACTIVE,
            'criteria': criteria,
            'channel': {
                'type': channel_type,
                'endpoint': endpoint,
                'payload': payload_type,
                'header': headers or {}
            },
            'end': None,  # No expiration
            'reason': 'Clinical notification subscription',
            'meta': {
                'created': datetime.utcnow().isoformat()
            }
        }
        
        self.subscriptions[subscription_id] = subscription
        logger.info(f"Created subscription {subscription_id} for criteria: {criteria}")
        
        return subscription
    
    def delete_subscription(self, subscription_id: str) -> bool:
        """Delete a subscription."""
        if subscription_id in self.subscriptions:
            del self.subscriptions[subscription_id]
            logger.info(f"Deleted subscription {subscription_id}")
            return True
        return False
    
    def get_subscription(self, subscription_id: str) -> Optional[Dict]:
        """Get a subscription by ID."""
        return self.subscriptions.get(subscription_id)
    
    def list_subscriptions(self) -> List[Dict]:
        """List all active subscriptions."""
        return list(self.subscriptions.values())
    
    def trigger_subscriptions(
        self,
        resource_type: str,
        resource_id: str,
        action: str,
        resource: Dict
    ) -> List[Dict]:
        """
        Trigger matching subscriptions when a resource changes.
        
        Args:
            resource_type: Type of FHIR resource (Patient, Observation, etc.)
            resource_id: ID of the resource
            action: Action performed (create, update, delete)
            resource: The FHIR resource data
        
        Returns:
            List of notification results
        """
        results = []
        
        for sub_id, subscription in self.subscriptions.items():
            if subscription['status'] != SubscriptionStatus.ACTIVE:
                continue
            
            # Check if criteria matches
            criteria = subscription.get('criteria', '')
            if not self._matches_criteria(criteria, resource_type, resource):
                continue
            
            # Send notification
            channel = subscription.get('channel', {})
            channel_type = channel.get('type')
            
            notification = {
                'subscription_id': sub_id,
                'resource_type': resource_type,
                'resource_id': resource_id,
                'action': action,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            try:
                if channel_type == SubscriptionChannel.REST_HOOK:
                    result = self._send_rest_hook(channel, resource, notification)
                elif channel_type == SubscriptionChannel.MESSAGE:
                    result = self._send_mattermost_message(channel, resource, notification)
                elif channel_type == SubscriptionChannel.WEBSOCKET:
                    result = self._send_websocket(channel, resource, notification)
                else:
                    result = {'success': False, 'error': f'Unknown channel type: {channel_type}'}
                
                results.append({**notification, **result})
                
            except Exception as e:
                logger.error(f"Error triggering subscription {sub_id}: {e}")
                results.append({**notification, 'success': False, 'error': str(e)})
        
        return results
    
    def _matches_criteria(self, criteria: str, resource_type: str, resource: Dict) -> bool:
        """Check if resource matches subscription criteria."""
        if not criteria:
            return True
        
        # Simple criteria matching: ResourceType or ResourceType?params
        parts = criteria.split('?')
        criteria_type = parts[0]
        
        if criteria_type != resource_type:
            return False
        
        # TODO: Implement more complex criteria matching
        return True
    
    def _send_rest_hook(
        self,
        channel: Dict,
        resource: Dict,
        notification: Dict
    ) -> Dict[str, Any]:
        """Send notification via REST Hook."""
        endpoint = channel.get('endpoint')
        headers = channel.get('header', {})
        
        if not endpoint:
            return {'success': False, 'error': 'No endpoint configured'}
        
        payload = {
            'notification': notification,
            'resource': resource
        }
        
        try:
            response = requests.post(
                endpoint,
                json=payload,
                headers={
                    'Content-Type': 'application/json',
                    **headers
                },
                timeout=10
            )
            
            return {
                'success': response.status_code < 400,
                'status_code': response.status_code,
                'channel': 'rest-hook'
            }
        except requests.RequestException as e:
            return {'success': False, 'error': str(e), 'channel': 'rest-hook'}
    
    def _send_mattermost_message(
        self,
        channel: Dict,
        resource: Dict,
        notification: Dict
    ) -> Dict[str, Any]:
        """Send notification to Mattermost."""
        # Mattermost webhook URL
        webhook_url = channel.get('endpoint') or settings.MATTERMOST_WEBHOOK_URL
        
        if not webhook_url:
            # Use default Mattermost instance
            webhook_url = 'http://localhost:8065/hooks/incoming'
        
        # Format message
        resource_type = notification.get('resource_type', 'Resource')
        action = notification.get('action', 'updated')
        resource_id = notification.get('resource_id', 'unknown')
        
        message = f"""### 🔔 FHIR Notification

**{resource_type}** foi **{action}**

- **ID:** `{resource_id}`
- **Timestamp:** {notification.get('timestamp')}

```json
{json.dumps(resource, indent=2, ensure_ascii=False)[:500]}...
```
"""
        
        payload = {
            'text': message,
            'username': 'OpenEHRCore Bot',
            'icon_url': 'https://www.hl7.org/fhir/assets/images/fhir-logo-www.png'
        }
        
        try:
            response = requests.post(webhook_url, json=payload, timeout=5)
            return {
                'success': response.status_code < 400,
                'channel': 'mattermost'
            }
        except Exception as e:
            logger.warning(f"Mattermost notification failed: {e}")
            return {'success': False, 'error': str(e), 'channel': 'mattermost'}
    
    def _send_websocket(
        self,
        channel: Dict,
        resource: Dict,
        notification: Dict
    ) -> Dict[str, Any]:
        """Send notification via WebSocket (placeholder for async channels)."""
        # TODO: Implement WebSocket gateway with Django Channels
        logger.info(f"WebSocket notification queued: {notification}")
        return {'success': True, 'channel': 'websocket', 'queued': True}


# Singleton instance
_subscription_service = None


def get_subscription_service() -> SubscriptionService:
    """Get the subscription service singleton."""
    global _subscription_service
    if _subscription_service is None:
        _subscription_service = SubscriptionService()
    return _subscription_service


# ========== FHIR Resource Hooks ==========

def on_resource_created(resource_type: str, resource_id: str, resource: Dict):
    """Hook called when a FHIR resource is created."""
    service = get_subscription_service()
    results = service.trigger_subscriptions(resource_type, resource_id, 'create', resource)
    logger.debug(f"Subscription triggers for {resource_type} create: {len(results)} notifications")
    return results


def on_resource_updated(resource_type: str, resource_id: str, resource: Dict):
    """Hook called when a FHIR resource is updated."""
    service = get_subscription_service()
    results = service.trigger_subscriptions(resource_type, resource_id, 'update', resource)
    logger.debug(f"Subscription triggers for {resource_type} update: {len(results)} notifications")
    return results


def on_resource_deleted(resource_type: str, resource_id: str, resource: Dict = None):
    """Hook called when a FHIR resource is deleted."""
    service = get_subscription_service()
    results = service.trigger_subscriptions(resource_type, resource_id, 'delete', resource or {})
    logger.debug(f"Subscription triggers for {resource_type} delete: {len(results)} notifications")
    return results
