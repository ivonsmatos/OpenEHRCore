"""
Subscription and Bot Views - API endpoints for automation

Sprint 28-29: Subscriptions and Bots
"""

import logging
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .authentication import KeycloakAuthentication
from .services.subscription_service import get_subscription_service, SubscriptionChannel
from .services.bot_engine import get_bot_engine, BotTriggerType

logger = logging.getLogger(__name__)


# ========== SUBSCRIPTION ENDPOINTS ==========

@api_view(['GET', 'POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def manage_subscriptions(request):
    """
    List or create subscriptions.
    
    GET /api/v1/subscriptions/
    POST /api/v1/subscriptions/
    """
    service = get_subscription_service()
    
    if request.method == 'GET':
        subscriptions = service.list_subscriptions()
        return Response({
            'count': len(subscriptions),
            'results': subscriptions
        })
    
    elif request.method == 'POST':
        data = request.data
        
        criteria = data.get('criteria', '')
        channel_type = data.get('channel_type', SubscriptionChannel.REST_HOOK)
        endpoint = data.get('endpoint', '')
        
        if not endpoint:
            return Response({
                'error': 'endpoint is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        subscription = service.create_subscription(
            criteria=criteria,
            channel_type=channel_type,
            endpoint=endpoint,
            headers=data.get('headers', {})
        )
        
        return Response(subscription, status=status.HTTP_201_CREATED)


@api_view(['GET', 'DELETE'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def subscription_detail(request, subscription_id):
    """
    Get or delete a subscription.
    
    GET /api/v1/subscriptions/{id}/
    DELETE /api/v1/subscriptions/{id}/
    """
    service = get_subscription_service()
    
    if request.method == 'GET':
        subscription = service.get_subscription(subscription_id)
        if not subscription:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(subscription)
    
    elif request.method == 'DELETE':
        if service.delete_subscription(subscription_id):
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)


# ========== BOT ENDPOINTS ==========

@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def list_bots(request):
    """
    List all registered bots.
    
    GET /api/v1/bots/
    """
    engine = get_bot_engine()
    bots = engine.list_bots()
    
    return Response({
        'count': len(bots),
        'results': bots
    })


@api_view(['GET', 'PUT'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def bot_detail(request, bot_id):
    """
    Get or update a bot.
    
    GET /api/v1/bots/{id}/
    PUT /api/v1/bots/{id}/
    """
    engine = get_bot_engine()
    bot = engine.get_bot(bot_id)
    
    if not bot:
        return Response({'error': 'Bot not found'}, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        return Response({
            'id': bot.id,
            'name': bot.name,
            'description': bot.description,
            'trigger_type': bot.trigger_type.value,
            'trigger_config': bot.trigger_config,
            'enabled': bot.enabled,
            'status': bot.status.value,
            'last_run': bot.last_run.isoformat() if bot.last_run else None,
            'run_count': bot.run_count,
            'error_count': bot.error_count,
            'code': bot.code
        })
    
    elif request.method == 'PUT':
        data = request.data
        
        if 'enabled' in data:
            bot.enabled = data['enabled']
        if 'name' in data:
            bot.name = data['name']
        if 'description' in data:
            bot.description = data['description']
        if 'code' in data:
            bot.code = data['code']
        
        return Response({'success': True, 'bot_id': bot.id})


@api_view(['POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def execute_bot(request, bot_id):
    """
    Manually execute a bot.
    
    POST /api/v1/bots/{id}/execute/
    
    Body:
        {
            "trigger_data": {...}  // Optional custom trigger data
        }
    """
    from .services.fhir_core import FHIRService
    from .services.ai_service import AIService
    
    engine = get_bot_engine()
    bot = engine.get_bot(bot_id)
    
    if not bot:
        return Response({'error': 'Bot not found'}, status=status.HTTP_404_NOT_FOUND)
    
    trigger_data = request.data.get('trigger_data', {})
    
    result = engine.execute_bot(
        bot_id,
        trigger_data,
        fhir_service=FHIRService(request.user),
        ai_service=AIService(request.user)
    )
    
    return Response(result)


@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def bot_history(request, bot_id=None):
    """
    Get bot execution history.
    
    GET /api/v1/bots/history/
    GET /api/v1/bots/{id}/history/
    """
    engine = get_bot_engine()
    limit = int(request.query_params.get('limit', 50))
    
    history = engine.get_execution_history(bot_id=bot_id, limit=limit)
    
    return Response({
        'count': len(history),
        'results': history
    })


# ========== WEBHOOK RECEIVER ==========

@api_view(['POST'])
@permission_classes([])  # Public endpoint for webhooks
def webhook_receiver(request, webhook_id):
    """
    Receive external webhooks and trigger bots.
    
    POST /api/v1/webhooks/{webhook_id}/
    """
    engine = get_bot_engine()
    
    trigger_data = {
        'webhook_id': webhook_id,
        'headers': dict(request.headers),
        'body': request.data,
        'method': request.method
    }
    
    # Trigger bots with webhook trigger type
    results = engine.trigger_bots(
        BotTriggerType.WEBHOOK,
        'Webhook',
        trigger_data
    )
    
    return Response({
        'received': True,
        'bots_triggered': len(results),
        'results': results
    })
