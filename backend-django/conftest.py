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

@pytest.fixture(autouse=True)
def _mock_external_health_checks(monkeypatch):
    """HAPI FHIR e Keycloak não rodam no ambiente de teste/CI. O endpoint
    /api/v1/health/ faz checagem real de conectividade e retornaria 503
    (CONNECTION_REFUSED), quebrando os testes que esperam 200. Mockamos as duas
    checagens externas como 'healthy' para os testes do endpoint serem
    herméticos. NÃO afeta produção (só vale ao carregar a conftest de testes)."""
    import fhir_api.views_health as vh
    monkeypatch.setattr(vh, "check_fhir_server", lambda: {"status": "healthy", "message": "mock (test)"})
    monkeypatch.setattr(vh, "check_keycloak", lambda: {"status": "healthy", "message": "mock (test)"})


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
