
import logging
import jwt

from django.conf import settings
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed

logger = logging.getLogger(__name__)

# JWKS client com cache (evita ir ao Keycloak a cada request).
# PyJWKClient cacheia as chaves de assinatura internamente.
_jwks_client = None


def _get_jwks_client():
    """Retorna um PyJWKClient cacheado para o realm configurado."""
    global _jwks_client
    if _jwks_client is None:
        jwks_url = (
            f"{settings.KEYCLOAK_URL}/realms/{settings.KEYCLOAK_REALM}"
            "/protocol/openid-connect/certs"
        )
        _jwks_client = jwt.PyJWKClient(jwks_url, cache_keys=True, lifespan=600)
    return _jwks_client


class KeycloakUser:
    """
    Wrapper que simula um usuário Django a partir das claims do token Keycloak.

    As roles vêm EXCLUSIVAMENTE do token (realm_access.roles). Nenhuma role é
    concedida automaticamente — o controle de acesso depende da configuração de
    roles no Keycloak.
    """

    def __init__(self, user_info):
        self._user_info = user_info
        self.is_authenticated = True

        roles = user_info.get('roles', []) or []
        self._user_info['roles'] = roles
        self.roles = roles

        # Identidade estável (usada por DRF UserRateThrottle, logs de auditoria, etc.)
        self.pk = user_info.get('sub')
        self.id = user_info.get('sub')

        # is_staff / is_superuser derivam APENAS da role 'admin' presente no token.
        self.is_staff = 'admin' in roles
        self.is_superuser = 'admin' in roles

    def has_role(self, *names) -> bool:
        """True se o usuário possui qualquer uma das roles informadas."""
        return any(role in self.roles for role in names)

    def get(self, key, default=None):
        return self._user_info.get(key, default)

    def __getattr__(self, name):
        # __getattr__ só é chamado para atributos não encontrados normalmente.
        try:
            return self._user_info[name]
        except KeyError:
            raise AttributeError(
                f"'KeycloakUser' object has no attribute '{name}'"
            )

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
        Valida token JWT usando a chave pública do Keycloak (JWKS).

        SECURITY: Tokens de bypass removidos — toda autenticação passa pelo
        Keycloak. Verificação de issuer/audience é configurável via settings
        (desabilitada por padrão para compatibilidade com configs de Keycloak
        que usam aud=account no access token).
        """
        try:
            signing_key = _get_jwks_client().get_signing_key_from_jwt(key)

            verify_aud = bool(getattr(settings, 'KEYCLOAK_AUDIENCE', '') )
            verify_iss = bool(getattr(settings, 'KEYCLOAK_VERIFY_ISSUER', False))
            expected_issuer = getattr(settings, 'KEYCLOAK_ISSUER', '') or (
                f"{settings.KEYCLOAK_URL}/realms/{settings.KEYCLOAK_REALM}"
            )

            decode_kwargs = {
                'algorithms': ["RS256"],
                'options': {
                    'verify_signature': True,
                    'verify_exp': True,
                    'verify_aud': verify_aud,
                    'verify_iss': verify_iss,
                },
            }
            if verify_aud:
                decode_kwargs['audience'] = settings.KEYCLOAK_AUDIENCE
            if verify_iss:
                decode_kwargs['issuer'] = expected_issuer

            token_info = jwt.decode(key, signing_key.key, **decode_kwargs)

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
            logger.warning(f"Token inválido: {str(e)}")
            raise AuthenticationFailed('Token inválido')
        except AuthenticationFailed:
            raise
        except Exception as e:
            # Falhas de rede ao buscar o JWKS, etc.
            logger.error(f"Erro validando token: {str(e)}")
            raise AuthenticationFailed('Falha na autenticação')
