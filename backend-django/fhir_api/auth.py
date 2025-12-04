"""
Autenticação e autorização com Keycloak + JWT

Este módulo integra Keycloak (OAuth2/OIDC) com Django REST Framework.
Todos os endpoints protegidos validam tokens JWT contra o servidor Keycloak.
"""

import requests
import json
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


class KeycloakAuthentication(TokenAuthentication):
    """
    Autenticação customizada que valida tokens JWT do Keycloak.
    
    Espera header: Authorization: Bearer <token_jwt>
    """
    
    keyword = "Bearer"
    
    def get_model(self):
        # Não usa modelo de token do Django
        return None
    
    def authenticate_credentials(self, key):
        """
        Valida token JWT contra Keycloak.
        
        Retorna (user_info, validated_token) ou lança AuthenticationFailed
        """
        try:
            # 1. Validar token no Keycloak (introspect endpoint)
            token_info = self._introspect_token(key)
            
            if not token_info.get('active'):
                raise AuthenticationFailed('Token inválido ou expirado')
            
            # 2. Extrair informações do usuário
            user_info = {
                'sub': token_info.get('sub'),
                'preferred_username': token_info.get('preferred_username'),
                'email': token_info.get('email'),
                'name': token_info.get('name'),
                'roles': token_info.get('realm_access', {}).get('roles', []),
                'exp': token_info.get('exp'),
            }
            
            # 3. Retornar como usuário autenticado
            # Nota: Não criamos usuário Django, apenas usamos info do Keycloak
            return (user_info, key)
        
        except Exception as e:
            logger.error(f"Erro validando token Keycloak: {str(e)}")
            raise AuthenticationFailed(f'Falha na autenticação: {str(e)}')
    
    def _introspect_token(self, token: str) -> Dict[str, Any]:
        """
        Valida token contra endpoint /protocol/openid-connect/token/introspect
        """
        try:
            keycloak_url = settings.KEYCLOAK_URL
            realm = settings.KEYCLOAK_REALM
            client_id = settings.KEYCLOAK_CLIENT_ID
            client_secret = settings.KEYCLOAK_CLIENT_SECRET
            
            url = f"{keycloak_url}/realms/{realm}/protocol/openid-connect/token/introspect"
            
            response = requests.post(
                url,
                data={
                    'client_id': client_id,
                    'client_secret': client_secret,
                    'token': token,
                },
                timeout=10
            )
            
            if response.status_code != 200:
                logger.warning(f"Keycloak introspect failed: {response.status_code} - {response.text}")
                return {'active': False}
            
            data = response.json()
            logger.info(f"Introspect response: {data}")
            return data
        
        except Exception as e:
            logger.error(f"Erro ao chamar Keycloak introspect: {str(e)}")
            return {'active': False}


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
            # Obter usuário autenticado (já validado por KeycloakAuthentication)
            user_info = getattr(request, 'user', None)
            
            if not user_info:
                return Response(
                    {'error': 'Não autenticado'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            user_roles = user_info.get('roles', []) if isinstance(user_info, dict) else []
            
            # Verificar se tem role permitida
            if not any(role in user_roles for role in allowed_roles):
                logger.warning(f"Acesso negado: roles {user_roles} não permitidas")
                return Response(
                    {'error': f'Acesso negado. Roles necessárias: {allowed_roles}'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            return view_func(request, *args, **kwargs)
        
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
        
        response = requests.post(
            url,
            data={
                'client_id': client_id,
                'client_secret': client_secret,
                'username': username,
                'password': password,
                'grant_type': 'password',
                'scope': 'openid profile email'
            },
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
