import pytest
from rest_framework.test import APIClient
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth.models import User

# ---------------------------------------------------------------------------
# Em testes, fazemos o KeycloakAuthentication aceitar um token de bypass fixo,
# para não depender de um servidor Keycloak ativo. Isso cobre inclusive as
# views que declaram explicitamente @authentication_classes([KeycloakAuthentication]).
# NUNCA afeta produção: o patch só é aplicado ao carregar a conftest de testes.
# ---------------------------------------------------------------------------
from fhir_api.authentication import KeycloakAuthentication, KeycloakUser  # noqa: E402
from openehrcore.test_auth import TEST_BYPASS_TOKEN  # noqa: E402


def _bypass_authenticate_credentials(self, key):
    if key == TEST_BYPASS_TOKEN:
        return (
            KeycloakUser({
                'sub': 'test-user',
                'preferred_username': 'testuser',
                'email': 'test@example.com',
                'name': 'Test User',
                'roles': ['admin', 'medico'],
            }),
            key,
        )
    raise AuthenticationFailed('Token inválido (teste)')


KeycloakAuthentication.authenticate_credentials = _bypass_authenticate_credentials

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def create_user():
    def _create_user(username='testuser', email='test@example.com', password='password123', is_staff=False):
        user = User.objects.create_user(username=username, email=email, password=password)
        user.is_staff = is_staff
        user.save()
        return user
    return _create_user

@pytest.fixture
def auth_client():
    client = APIClient()
    # Usa o token de dev definido em KeycloakAuthentication
    client.credentials(HTTP_AUTHORIZATION='Bearer dev-token-bypass')
    return client
