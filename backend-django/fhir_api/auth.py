"""
Autenticação e autorização com Keycloak + JWT

Este módulo integra Keycloak (OAuth2/OIDC) com Django REST Framework.
Todos os endpoints protegidos validam tokens JWT contra o servidor Keycloak.
"""

import requests
import json
import jwt
from functools import wraps
from datetime import datetime, timedelta
from typing import Dict, Optional, Any

from django.conf import settings
from django.core.cache import cache
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed

import logging

logger = logging.getLogger(__name__)


from .authentication import KeycloakAuthentication, KeycloakUser

# Re-export keycloak logic if needed or just keep require_role below.
# For backward compatibility within this module if used elsewhere.



def require_role(*allowed_roles):
    """
    Decorator para validar roles do usuário.
    
    Uso:
        @require_role('medico', 'admin')
        def minha_view(request):
            pass
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            try:
                # Obter usuário autenticado (já validado por KeycloakAuthentication)
                user_info = getattr(request, 'user', None)
                
                if not user_info:
                    return Response(
                        {'error': 'Não autenticado'},
                        status=status.HTTP_401_UNAUTHORIZED
                    )
                
                # Verificar roles
                user_roles = []
                if isinstance(user_info, dict):
                    user_roles = user_info.get('roles', [])
                elif hasattr(user_info, 'get'):
                    user_roles = user_info.get('roles', [])
                elif hasattr(user_info, 'roles'):
                    user_roles = user_info.roles
                
                # Verificar se tem role permitida
                if not any(role in user_roles for role in allowed_roles):
                    logger.warning(f"Acesso negado: roles {user_roles} não permitidas")
                    return Response(
                        {'error': f'Acesso negado. Roles necessárias: {allowed_roles}'},
                        status=status.HTTP_403_FORBIDDEN
                    )
                
                return view_func(request, *args, **kwargs)
            except Exception as e:
                logger.error(f"Error in require_role decorator: {str(e)}")
                import traceback
                traceback.print_exc()
                from django.http import JsonResponse
                return JsonResponse({"error": "Erro interno de permissão", "detail": str(e)}, status=500)
        
        return wrapper
    
    return decorator


def get_keycloak_token(username: str, password: str) -> Optional[str]:
    """
    Obtém token JWT do Keycloak usando username + password (Resource Owner Password Flow).
    
    Usado para testes e login direto (não recomendado em produção).
    """
    try:
        keycloak_url = settings.KEYCLOAK_URL
        realm = settings.KEYCLOAK_REALM
        client_id = settings.KEYCLOAK_CLIENT_ID
        client_secret = settings.KEYCLOAK_CLIENT_SECRET
        
        url = f"{keycloak_url}/realms/{realm}/protocol/openid-connect/token"
        
        data = {
            'client_id': client_id,
            'username': username,
            'password': password,
            'grant_type': 'password',
            'scope': 'openid profile email'
        }
        
        if client_secret:
            data['client_secret'] = client_secret
        
        response = requests.post(
            url,
            data=data,
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json().get('access_token')
        else:
            logger.warning(f"Keycloak login failed: {response.status_code}")
            return None
    
    except Exception as e:
        logger.error(f"Erro ao obter token Keycloak: {str(e)}")
        return None
