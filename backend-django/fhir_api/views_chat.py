
from rest_framework.decorators import api_view, authentication_classes, permission_classes # type: ignore
from rest_framework.response import Response # type: ignore
from rest_framework import status # type: ignore
from .auth import KeycloakAuthentication
from rest_framework.permissions import IsAuthenticated # type: ignore
from .services.fhir_core import FHIRService
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def list_channels(request):
    """
    List available channels (Groups + System) and practitioners for DM.
    """
    try:
        fhir = FHIRService()
        
        # 1. System Channels (Public)
        channels = [
            {"id": "general", "name": "# Geral", "type": "channel"},
            {"id": "clinical", "name": "# Clínico", "type": "channel"},
            {"id": "admin", "name": "# Admin", "type": "channel"},
            {"id": "emergency", "name": "# Emergência", "type": "channel"},
        ]
        
        # 1.5 Fetch Created Teams (Groups)
        # Search for Groups with type=practitioner or no type
        groups = fhir.search_resources('Group', {'type': 'practitioner', '_count': 50})
        for g in groups:
             channels.append({
                 "id": g.get('id'),
                 "name": f"# {g.get('name', 'Unnamed Team')}",
                 "type": "channel"
             })
        
        # 2. Practitioners (for DM)
        practitioners = fhir.search_resources('Practitioner', {'_count': 50})
        users = []
        for p in practitioners:
            name = "Unknown"
            if p.get('name'):
                name_parts = p['name'][0]
                given = " ".join(name_parts.get('given', []))
                family = name_parts.get('family', '')
                name = f"{given} {family}".strip()
            
            role = "Staff"
            if p.get('qualification'):
                role = p['qualification'][0].get('code', {}).get('text', 'Staff')
                
            users.append({
                "id": p.get('id'),
                "name": name,
                "role": role,
                "type": "user"
            })
            
        return Response({
            "channels": channels,
            "users": users
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error listing chat channels: {e}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def create_channel(request):
    """
    Create a new Team/Channel (FHIR Group).
    """
    name = request.data.get('name')
    if not name:
        return Response({"error": "Name required"}, status=status.HTTP_400_BAD_REQUEST)
        
    try:
        fhir = FHIRService()
        group = {
            "resourceType": "Group",
            "active": True,
            "type": "practitioner",
            "actual": True,
            "name": name,
            "code": {
                "coding": [{
                    "system": "http://openehrcore/chat-teams",
                    "code": name.lower().replace(" ", "-"),
                    "display": name
                }]
            }
        }
        result = fhir.create_resource("Group", group)
        return Response(result, status=status.HTTP_201_CREATED)
    except Exception as e:
        logger.error(f"Error creating channel: {e}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def list_messages(request):
    """
    Get messages for a channel or DM.
    Params: channel_id (e.g. 'general', '123' (Group ID), or 'Practitioner/123')
    """
    channel_id = request.query_params.get('channel_id')
    if not channel_id:
        return Response({"error": "channel_id required"}, status=status.HTTP_400_BAD_REQUEST)
        
    try:
        fhir = FHIRService()
        messages = []
        
        search_params = {'_sort': 'sent', '_count': 50}
        
        # Format the channel_id for searching
        # Store it in category with system|code format
        # Handle dm- prefix for direct messages
        channel_code = channel_id
        
        # Use a token search with system|code format for HAPI FHIR
        search_params['category'] = f"http://openehrcore/chat-channels|{channel_code}"
              
        resources = fhir.search_resources('Communication', search_params)
        
        for r in resources:
            content = ""
            attachment = None
            
            if r.get('payload'):
                for payload_item in r['payload']:
                    if 'contentString' in payload_item:
                        content = payload_item.get('contentString', '')
                    if 'contentAttachment' in payload_item:
                        att = payload_item['contentAttachment']
                        attachment = {
                            'name': att.get('title', 'attachment'),
                            'type': att.get('contentType', 'application/octet-stream'),
                            'size': att.get('size', 0),
                            'data': att.get('data')  # base64
                        }
                
            sender_ref = r.get('sender', {}).get('reference', '')
            sender_id = sender_ref.split('/')[-1] if '/' in sender_ref else sender_ref
            
            msg = {
                "id": r.get('id'),
                "content": content,
                "sender_id": sender_id,
                "sent": r.get('sent'),
                "category": r.get('category', [{}])[0].get('coding', [{}])[0].get('code')
            }
            
            if attachment:
                msg['attachment'] = attachment
                
            messages.append(msg)
            
        return Response(messages, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error listing messages: {e}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def send_message(request):
    data = request.data
    channel_id = data.get('channel_id')
    content = data.get('content')
    sender_id = data.get('sender_id')
    attachment = data.get('attachment')  # {name, type, size, data}
    
    if not channel_id or (not content and not attachment):
         return Response({"error": "channel_id and content or attachment required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        fhir = FHIRService()
        
        # Build payload
        payload = []
        
        # Add text content if present
        if content:
            payload.append({
                "contentString": content
            })
        
        # Add attachment if present
        if attachment:
            attachment_payload = {
                "contentAttachment": {
                    "contentType": attachment.get('type', 'application/octet-stream'),
                    "title": attachment.get('name', 'attachment'),
                    "size": attachment.get('size', 0)
                }
            }
            
            # Include data if provided (base64 encoded)
            if attachment.get('data'):
                # Remove the data:mime;base64, prefix if present
                data_str = attachment.get('data')
                if ';base64,' in data_str:
                    data_str = data_str.split(';base64,')[1]
                attachment_payload["contentAttachment"]["data"] = data_str
            
            payload.append(attachment_payload)
        
        resource = {
            "resourceType": "Communication",
            "status": "completed",
            "sent": datetime.utcnow().isoformat() + "Z",
            "payload": payload
        }
        
        # Check validity of sender_id
        if sender_id and sender_id != 'undefined':
             # Try to ensure it's a valid reference format or just ID
             # If just ID, prepend Practitioner/
             ref = sender_id if '/' in sender_id else f"Practitioner/{sender_id}"
             resource['sender'] = {"reference": ref}
        else:
             resource['sender'] = {"display": "Anonymous User"}
        
        # CATEGORY LOGIC
        # Store the channel_id as the category code. Use a generic system.
        resource['category'] = [{
            "coding": [{
                "system": "http://openehrcore/chat-channels",
                "code": channel_id,
                "display": channel_id # Name might be unknown, use ID
            }]
        }]
            
        result = fhir.create_resource("Communication", resource)
        return Response(result, status=status.HTTP_201_CREATED)

    except Exception as e:
        logger.error(f"Error sending message: {e}")
        # Return the exception details for debugging
        return Response({"error": f"Internal Error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
