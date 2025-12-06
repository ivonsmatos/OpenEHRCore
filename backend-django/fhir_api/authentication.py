
import logging
import jwt
from typing import Optional

from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed

logger = logging.getLogger(__name__)

class KeycloakUser:
    """
    Classe wrapper para simular um usuário Django a partir do token Keycloak.
    Necessário para compatibilidade com permissions.IsAuthenticated.
    """
    def __init__(self, user_info):
        self._user_info = user_info
        self.is_authenticated = True
        
        # HACK: Garantir roles para desenvolvimento local
        roles = user_info.get('roles', [])
        if 'medico' not in roles:
            roles.append('medico')
        if 'admin' not in roles:
            roles.append('admin')
        self._user_info['roles'] = roles
        
        self.is_staff = 'admin' in roles
        self.is_superuser = 'admin' in roles
        
    def get(self, key, default=None):
        return self._user_info.get(key, default)
        
    def __getattr__(self, name):
        if name in self._user_info:
            return self._user_info[name]
        raise AttributeError(f"'KeycloakUser' object has no attribute '{name}'")
    
    def __str__(self):
        return self._user_info.get('preferred_username', 'KeycloakUser')


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
        Valida token JWT localmente usando chave pública do Keycloak (JWKS).
        """
        try:
            # BYPASS: Token de desenvolvimento (Medico)
            if key == "dev-token-bypass":
                user_info = {
                    'name': 'Ivon Matos',
                    'preferred_username': 'contato@ivonmatos.com.br',
                    'email': 'contato@ivonmatos.com.br',
                    'roles': ['medico', 'admin', 'enfermeiro'],
                    'sub': 'ivon-matos-id'
                }
                return (KeycloakUser(user_info), key)

            # BYPASS: Token de desenvolvimento (Paciente)
            if key == "patient-token-bypass":
                user_info = {
                    'name': 'Paciente Teste',
                    'preferred_username': 'paciente@teste.com',
                    'email': 'paciente@teste.com',
                    'roles': ['paciente'],
                    'sub': 'patient-1'  # ID do paciente Patient/patient-1
                }
                return (KeycloakUser(user_info), key)

            # 1. Obter JWKS do Keycloak (cachear isso seria ideal em prod)
            jwks_url = f"{settings.KEYCLOAK_URL}/realms/{settings.KEYCLOAK_REALM}/protocol/openid-connect/certs"
            jwks_client = jwt.PyJWKClient(jwks_url)
            
            # 2. Obter a chave de assinatura
            signing_key = jwks_client.get_signing_key_from_jwt(key)
            
            # 3. Decodificar e validar token
            # audience pode ser opcional dependendo da config do Keycloak, aqui validamos se presente
            token_info = jwt.decode(
                key,
                signing_key.key,
                algorithms=["RS256"],
                audience=settings.KEYCLOAK_CLIENT_ID,
                options={"verify_aud": False} # Relaxar aud por enquanto para evitar erros se não configurado
            )
            
            # 4. Extrair informações do usuário
            user_info = {
                'sub': token_info.get('sub'),
                'preferred_username': token_info.get('preferred_username'),
                'email': token_info.get('email'),
                'name': token_info.get('name'),
                'roles': token_info.get('realm_access', {}).get('roles', []),
                'exp': token_info.get('exp'),
            }
            
            return (KeycloakUser(user_info), key)
        
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Token expirado')
        except jwt.InvalidTokenError as e:
            logger.error(f"Token inválido: {str(e)}")
            raise AuthenticationFailed(f'Token inválido: {str(e)}')
        except Exception as e:
            logger.error(f"Erro validando token: {str(e)}")
            raise AuthenticationFailed(f'Falha na autenticação: {str(e)}')
