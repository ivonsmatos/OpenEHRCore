"""
SMART on FHIR Views

Sprint 32: SMART App Launch Protocol endpoints
"""

import logging
from urllib.parse import urlencode

from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated

from .authentication import KeycloakAuthentication
from .services.smart_service import get_smart_service

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([AllowAny])
def smart_configuration(request):
    """
    SMART configuration endpoint.
    
    GET /.well-known/smart-configuration
    """
    base_url = request.build_absolute_uri('/api/v1').rstrip('/')
    
    smart = get_smart_service()
    config = smart.get_well_known_config(base_url)
    
    return Response(config)


@api_view(['GET'])
@permission_classes([AllowAny])
def capability_statement(request):
    """
    FHIR CapabilityStatement with SMART security extensions.
    
    GET /api/v1/metadata
    """
    base_url = request.build_absolute_uri('/api/v1').rstrip('/')
    
    smart = get_smart_service()
    capability = smart.get_capability_statement(base_url)
    
    return Response(capability)


@api_view(['GET'])
@permission_classes([AllowAny])
def available_scopes(request):
    """
    List available SMART scopes.
    
    GET /api/v1/smart/scopes/
    """
    smart = get_smart_service()
    
    scopes_list = [
        {'scope': scope, 'description': desc}
        for scope, desc in smart.SCOPES.items()
    ]
    
    return Response({
        'count': len(scopes_list),
        'scopes': scopes_list
    })


@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def authorize(request):
    """
    OAuth2 authorization endpoint.
    
    GET/POST /api/v1/smart/authorize
    
    Query params:
        - response_type: 'code'
        - client_id: App client ID
        - redirect_uri: Callback URL
        - scope: Space-separated scopes
        - state: Anti-CSRF token
        - aud: FHIR server URL
        - launch: EHR launch context (optional)
        - code_challenge: PKCE challenge (optional)
        - code_challenge_method: 'S256' (optional)
    """
    params = request.GET if request.method == 'GET' else request.data
    
    response_type = params.get('response_type')
    client_id = params.get('client_id')
    redirect_uri = params.get('redirect_uri')
    scope = params.get('scope', '')
    state = params.get('state', '')
    code_challenge = params.get('code_challenge')
    code_challenge_method = params.get('code_challenge_method', 'S256')
    launch = params.get('launch')  # EHR launch context ID
    
    # Validate required params
    if response_type != 'code':
        return Response({
            'error': 'unsupported_response_type',
            'error_description': 'Only code response type is supported'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if not client_id or not redirect_uri:
        return Response({
            'error': 'invalid_request',
            'error_description': 'client_id and redirect_uri are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Parse and validate scopes
    scopes = scope.split() if scope else []
    smart = get_smart_service()
    scope_validation = smart.validate_scopes(scopes)
    
    if not scope_validation['valid']:
        return Response({
            'error': 'invalid_scope',
            'error_description': f"Invalid scopes: {', '.join(scope_validation['invalid_scopes'])}"
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Get launch context if provided
    launch_context = {}
    if launch:
        # In production, would look up launch context from session/database
        # For demo, we use a mock
        if 'launch/patient' in scopes:
            launch_context['patient'] = 'patient-123'
        if 'launch/encounter' in scopes:
            launch_context['encounter'] = 'encounter-456'
    
    # Create authorization code
    result = smart.create_authorization(
        client_id=client_id,
        redirect_uri=redirect_uri,
        scopes=scope_validation['scopes'],
        state=state,
        code_challenge=code_challenge,
        code_challenge_method=code_challenge_method,
        launch_context=launch_context
    )
    
    # Build redirect URL
    redirect_params = {
        'code': result['code'],
        'state': state
    }
    
    redirect_url = f"{redirect_uri}?{urlencode(redirect_params)}"
    
    return Response({
        'redirect_url': redirect_url,
        'code': result['code'],
        'state': state
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def token(request):
    """
    OAuth2 token endpoint.
    
    POST /api/v1/smart/token
    
    Body (x-www-form-urlencoded or JSON):
        - grant_type: 'authorization_code' or 'refresh_token'
        - code: Authorization code (for authorization_code grant)
        - refresh_token: Refresh token (for refresh_token grant)
        - client_id: App client ID
        - client_secret: App client secret (optional for public clients)
        - redirect_uri: Must match original redirect_uri
        - code_verifier: PKCE verifier (if PKCE was used)
    """
    data = request.data
    grant_type = data.get('grant_type')
    
    if grant_type == 'authorization_code':
        code = data.get('code')
        client_id = data.get('client_id')
        client_secret = data.get('client_secret')
        redirect_uri = data.get('redirect_uri')
        code_verifier = data.get('code_verifier')
        
        if not code or not client_id or not redirect_uri:
            return Response({
                'error': 'invalid_request',
                'error_description': 'code, client_id, and redirect_uri are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        smart = get_smart_service()
        result = smart.exchange_code(
            code=code,
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            code_verifier=code_verifier
        )
        
        if 'error' in result:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(result)
    
    elif grant_type == 'refresh_token':
        # TODO: Implement refresh token grant
        return Response({
            'error': 'unsupported_grant_type',
            'error_description': 'refresh_token grant not yet implemented'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    else:
        return Response({
            'error': 'unsupported_grant_type',
            'error_description': 'Only authorization_code and refresh_token grants are supported'
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def introspect(request):
    """
    Token introspection endpoint.
    
    POST /api/v1/smart/introspect
    
    Body:
        - token: Access token to introspect
    """
    token_value = request.data.get('token')
    
    if not token_value:
        return Response({
            'error': 'invalid_request',
            'error_description': 'token is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    smart = get_smart_service()
    result = smart.introspect_token(token_value)
    
    return Response(result)


@api_view(['POST'])
@permission_classes([AllowAny])
def revoke(request):
    """
    Token revocation endpoint.
    
    POST /api/v1/smart/revoke
    
    Body:
        - token: Token to revoke
    """
    token_value = request.data.get('token')
    
    if not token_value:
        return Response({
            'error': 'invalid_request',
            'error_description': 'token is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    smart = get_smart_service()
    result = smart.revoke_token(token_value)
    
    return Response(result)


@api_view(['POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def launch(request):
    """
    Create EHR launch context.
    
    POST /api/v1/smart/launch
    
    Body:
        - patient_id: Patient to launch with
        - encounter_id: Encounter to launch with (optional)
        - app_url: SMART app URL
    """
    patient_id = request.data.get('patient_id')
    encounter_id = request.data.get('encounter_id')
    app_url = request.data.get('app_url')
    
    if not patient_id or not app_url:
        return Response({
            'error': 'patient_id and app_url are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Generate launch token
    import uuid
    launch_token = str(uuid.uuid4())
    
    # In production, store this in session/database
    # For demo, we just return the launch URL
    
    launch_params = {
        'launch': launch_token,
        'iss': request.build_absolute_uri('/api/v1/fhir')
    }
    
    launch_url = f"{app_url}?{urlencode(launch_params)}"
    
    return Response({
        'launch_token': launch_token,
        'launch_url': launch_url,
        'context': {
            'patient': patient_id,
            'encounter': encounter_id
        }
    })
