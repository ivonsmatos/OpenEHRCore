"""
Autenticação SOMENTE para a suíte de testes.

Aceita um token fixo (``dev-token-bypass``) para que os testes possam
autenticar sem um servidor Keycloak ativo. Este módulo é referenciado
exclusivamente por ``openehrcore.test_settings`` e NUNCA é incluído nas
configurações de produção.
"""

from rest_framework.authentication import BaseAuthentication

from fhir_api.authentication import KeycloakUser

TEST_BYPASS_TOKEN = "dev-token-bypass"


class TestBypassAuthentication(BaseAuthentication):
    """Autentica como admin de teste quando o token de bypass é apresentado."""

    keyword = "Bearer"

    def authenticate(self, request):
        header = request.META.get("HTTP_AUTHORIZATION", "")
        if not header.startswith(f"{self.keyword} "):
            return None

        token = header.split(" ", 1)[1].strip()
        if token != TEST_BYPASS_TOKEN:
            return None

        user_info = {
            "sub": "test-user",
            "preferred_username": "testuser",
            "email": "test@example.com",
            "name": "Test User",
            "roles": ["admin", "medico"],
        }
        return (KeycloakUser(user_info), token)
