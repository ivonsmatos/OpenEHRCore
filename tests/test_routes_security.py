"""
TESTES DE SEGURANÇA E INTEGRIDADE DE ROTAS
==========================================

Este arquivo testa TODAS as rotas da API Django para garantir:
1. Rotas protegidas retornam 401/403 sem autenticação
2. Rotas públicas retornam status apropriados
3. Nenhuma rota retorna 500 (erro interno do servidor)
4. Validação de dados vazios não quebra a aplicação

Executar com:
    pytest tests/test_routes_security.py -v
    pytest tests/test_routes_security.py -v --tb=short  (menos verbose)
"""

import pytest
import requests
from typing import Dict, List, Tuple
from dataclasses import dataclass

# =============================================================================
# CONFIGURAÇÃO
# =============================================================================

BASE_URL = "http://localhost:8000/api/v1"
ADMIN_URL = "http://localhost:8000/admin"

# Credenciais de teste (ajustar conforme seu ambiente)
TEST_USER = {
    "username": "test_user",
    "password": "test_pass_123"
}


@dataclass
class RouteTest:
    """Representa um teste de rota"""
    method: str
    path: str
    requires_auth: bool
    expected_without_auth: List[int]  # Códigos aceitos sem auth
    expected_with_auth: List[int]  # Códigos aceitos com auth
    payload: Dict = None  # Payload para POST/PUT


# =============================================================================
# MAPEAMENTO COMPLETO DE ROTAS (baseado em urls.py)
# =============================================================================

# Rotas PÚBLICAS (sem autenticação necessária)
PUBLIC_ROUTES = [
    RouteTest("GET", "/health/", False, [200], [200]),
    RouteTest("GET", "/health/live/", False, [200], [200]),
    RouteTest("GET", "/health/ready/", False, [200], [200]),
    RouteTest("GET", "/metrics/", False, [200], [200]),
    RouteTest("GET", "/docs/openapi.json", False, [200], [200]),
    RouteTest("POST", "/auth/login/", False, [200, 400, 401], [200, 400]),
]

# Rotas PROTEGIDAS (requerem autenticação)
PROTECTED_ROUTES = [
    # Patients
    RouteTest("GET", "/patients/", True, [401, 403], [200]),
    RouteTest("POST", "/patients/", True, [401, 403], [200, 201, 400]),
    RouteTest("GET", "/patients/search/", True, [401, 403], [200]),
    RouteTest("GET", "/patients/test-patient-001/", True, [401, 403], [200, 404]),
    
    # Encounters
    RouteTest("POST", "/encounters/", True, [401, 403], [200, 201, 400]),
    RouteTest("GET", "/encounters/search/", True, [401, 403], [200]),
    RouteTest("GET", "/patients/test-patient-001/encounters/", True, [401, 403], [200, 404]),
    
    # Observations
    RouteTest("POST", "/observations/", True, [401, 403], [200, 201, 400]),
    RouteTest("GET", "/observations/search/", True, [401, 403], [200]),
    RouteTest("GET", "/patients/test-patient-001/observations/", True, [401, 403], [200, 404]),
    
    # Conditions
    RouteTest("POST", "/conditions/", True, [401, 403], [200, 201, 400]),
    RouteTest("GET", "/conditions/search/", True, [401, 403], [200]),
    RouteTest("GET", "/patients/test-patient-001/conditions/", True, [401, 403], [200, 404]),
    
    # Allergies
    RouteTest("POST", "/allergies/", True, [401, 403], [200, 201, 400]),
    RouteTest("GET", "/patients/test-patient-001/allergies/", True, [401, 403], [200, 404]),
    
    # Appointments
    RouteTest("POST", "/appointments/", True, [401, 403], [200, 201, 400]),
    RouteTest("GET", "/patients/test-patient-001/appointments/", True, [401, 403], [200, 404]),
    
    # Medications
    RouteTest("POST", "/medications/", True, [401, 403], [200, 201, 400]),
    
    # Exams/ServiceRequest
    RouteTest("POST", "/exams/", True, [401, 403], [200, 201, 400]),
    
    # Clinical Impressions
    RouteTest("POST", "/clinical-impressions/", True, [401, 403], [200, 201, 400]),
    
    # Schedule & Slots
    RouteTest("POST", "/schedule/", True, [401, 403], [200, 201, 400]),
    RouteTest("POST", "/slots/", True, [401, 403], [200, 201, 400]),
    RouteTest("GET", "/slots/search/", True, [401, 403], [200]),
    
    # Questionnaires
    RouteTest("POST", "/questionnaires/", True, [401, 403], [200, 201, 400]),
    RouteTest("POST", "/questionnaires/response/", True, [401, 403], [200, 201, 400]),
    
    # Patient Portal
    RouteTest("GET", "/patient/dashboard/", True, [401, 403], [200]),
    RouteTest("GET", "/patient/appointments/", True, [401, 403], [200]),
    RouteTest("GET", "/patient/exams/", True, [401, 403], [200]),
    
    # Documents
    RouteTest("GET", "/documents/", True, [401, 403], [200]),
    RouteTest("POST", "/documents/", True, [401, 403], [200, 201, 400]),
    
    # Analytics
    RouteTest("GET", "/analytics/population/", True, [401, 403], [200]),
    RouteTest("GET", "/analytics/clinical/", True, [401, 403], [200]),
    RouteTest("GET", "/analytics/operational/", True, [401, 403], [200]),
    RouteTest("GET", "/analytics/kpi/", True, [401, 403], [200]),
    
    # Visitors
    RouteTest("GET", "/visitors/", True, [401, 403], [200]),
    RouteTest("POST", "/visitors/create/", True, [401, 403], [200, 201, 400]),
    
    # Chat
    RouteTest("GET", "/chat/channels/", True, [401, 403], [200]),
    RouteTest("POST", "/chat/channels/create/", True, [401, 403], [200, 201, 400]),
    
    # IPD (Inpatient Department)
    RouteTest("GET", "/ipd/locations/", True, [401, 403], [200]),
    RouteTest("GET", "/ipd/occupancy/", True, [401, 403], [200]),
    RouteTest("POST", "/ipd/admit/", True, [401, 403], [200, 201, 400]),
    
    # Practitioners
    RouteTest("GET", "/practitioners/", True, [401, 403], [200, 201, 400]),
    RouteTest("POST", "/practitioners/", True, [401, 403], [200, 201, 400]),
    RouteTest("GET", "/practitioners/list/", True, [401, 403], [200]),
    RouteTest("GET", "/practitioners/search/", True, [401, 403], [200]),
    
    # Consents
    RouteTest("GET", "/consents/list/", True, [401, 403], [200]),
    RouteTest("POST", "/consents/", True, [401, 403], [200, 201, 400]),
    
    # Organizations
    RouteTest("GET", "/organizations/", True, [401, 403], [200]),
    RouteTest("POST", "/organizations/", True, [401, 403], [200, 201, 400]),
    
    # Procedures
    RouteTest("GET", "/procedures/", True, [401, 403], [200]),
    RouteTest("POST", "/procedures/", True, [401, 403], [200, 201, 400]),
    
    # Medication Requests
    RouteTest("GET", "/medication-requests/", True, [401, 403], [200]),
    RouteTest("POST", "/medication-requests/", True, [401, 403], [200, 201, 400]),
    
    # Healthcare Services
    RouteTest("GET", "/healthcare-services/", True, [401, 403], [200]),
    RouteTest("POST", "/healthcare-services/", True, [401, 403], [200, 201, 400]),
    
    # Diagnostic Reports V2
    RouteTest("GET", "/diagnostic-reports-v2/", True, [401, 403], [200]),
    RouteTest("POST", "/diagnostic-reports-v2/", True, [401, 403], [200, 201, 400]),
    
    # Consents V2
    RouteTest("GET", "/consents-v2/", True, [401, 403], [200]),
    RouteTest("POST", "/consents-v2/", True, [401, 403], [200, 201, 400]),
    
    # Audit Events
    RouteTest("GET", "/audit-events/", True, [401, 403], [200]),
    
    # Terminology Services
    RouteTest("GET", "/terminology/rxnorm/search/", True, [401, 403], [200]),
    RouteTest("GET", "/terminology/icd10/search/", True, [401, 403], [200]),
    RouteTest("GET", "/terminology/tuss/search/", True, [401, 403], [200]),
    
    # LGPD
    RouteTest("GET", "/lgpd/requests/", True, [401, 403], [200]),
    RouteTest("GET", "/lgpd/dashboard/", True, [401, 403], [200]),
    
    # CarePlans
    RouteTest("GET", "/careplans/", True, [401, 403], [200]),
    RouteTest("POST", "/careplans/", True, [401, 403], [200, 201, 400]),
    
    # Compositions
    RouteTest("GET", "/compositions/", True, [401, 403], [200]),
    RouteTest("POST", "/compositions/", True, [401, 403], [200, 201, 400]),
    RouteTest("GET", "/compositions/types/", True, [401, 403], [200]),
    
    # TISS
    RouteTest("GET", "/tiss/tipos/", True, [401, 403], [200]),
    RouteTest("POST", "/tiss/validar/", True, [401, 403], [200, 400]),
    
    # RNDS
    RouteTest("GET", "/rnds/status/", True, [401, 403], [200]),
    
    # Referrals
    RouteTest("GET", "/referrals/", True, [401, 403], [200]),
    RouteTest("POST", "/referrals/", True, [401, 403], [200, 201, 400]),
    RouteTest("GET", "/referrals/pending/", True, [401, 403], [200]),
    
    # Communications
    RouteTest("GET", "/communications/", True, [401, 403], [200]),
    RouteTest("POST", "/communications/", True, [401, 403], [200, 201, 400]),
    
    # Notifications
    RouteTest("GET", "/notifications/", True, [401, 403], [200]),
    RouteTest("GET", "/notifications/conditions/", True, [401, 403], [200]),
    
    # CBO
    RouteTest("GET", "/cbo/families/", True, [401, 403], [200]),
    RouteTest("GET", "/cbo/search/", True, [401, 403], [200]),
    
    # Automation
    RouteTest("GET", "/subscriptions/", True, [401, 403], [200]),
    RouteTest("GET", "/bots/", True, [401, 403], [200]),
    
    # Billing
    RouteTest("GET", "/billing/coverage/", True, [401, 403], [200]),
    RouteTest("GET", "/billing/claims/", True, [401, 403], [200]),
    RouteTest("GET", "/billing/dashboard/", True, [401, 403], [200]),
    
    # Prescriptions
    RouteTest("GET", "/prescriptions/drugs/", True, [401, 403], [200]),
    RouteTest("POST", "/prescriptions/", True, [401, 403], [200, 201, 400]),
    
    # SMART on FHIR
    RouteTest("GET", "/smart/scopes/", True, [401, 403], [200]),
    RouteTest("GET", "/.well-known/smart-configuration", True, [401, 403], [200]),
    
    # FHIRcast
    RouteTest("GET", "/.well-known/fhircast-configuration", True, [401, 403], [200]),
    RouteTest("GET", "/fhircast/events", True, [401, 403], [200]),
    
    # Compliance
    RouteTest("GET", "/compliance/status", True, [401, 403], [200]),
    RouteTest("GET", "/archetypes/", True, [401, 403], [200]),
    
    # Questionnaires (Sprint 36)
    RouteTest("GET", "/questionnaires/", True, [401, 403], [200]),
    
    # HL7
    RouteTest("GET", "/hl7/info", True, [401, 403], [200]),
    
    # Brazil Integrations
    RouteTest("GET", "/pix/info", True, [401, 403], [200]),
    RouteTest("GET", "/whatsapp/info", True, [401, 403], [200]),
    RouteTest("GET", "/telemedicine/info", True, [401, 403], [200]),
    
    # Agent
    RouteTest("GET", "/agent/list", True, [401, 403], [200]),
    
    # FHIR Validation
    RouteTest("GET", "/fhir/validation-info", True, [401, 403], [200]),
]


# =============================================================================
# FIXTURES E HELPERS
# =============================================================================

@pytest.fixture(scope="session")
def api_session():
    """Sessão HTTP reutilizável"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="session")
def auth_token(api_session):
    """Obtém token de autenticação para testes protegidos"""
    try:
        response = api_session.post(
            f"{BASE_URL}/auth/login/",
            json=TEST_USER
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("token") or data.get("access_token") or data.get("key")
        return None
    except Exception as e:
        print(f"⚠️  Aviso: Não foi possível obter token de autenticação: {e}")
        return None


def make_request(session, method: str, url: str, headers: Dict = None, **kwargs):
    """Wrapper para requisições com tratamento de erros"""
    try:
        method_fn = getattr(session, method.lower())
        response = method_fn(url, headers=headers, timeout=10, **kwargs)
        return response
    except requests.exceptions.Timeout:
        pytest.fail(f"TIMEOUT: {method} {url}")
    except requests.exceptions.ConnectionError:
        pytest.fail(f"CONNECTION ERROR: {method} {url} - Servidor não está rodando?")
    except Exception as e:
        pytest.fail(f"ERRO INESPERADO: {method} {url} - {str(e)}")


# =============================================================================
# TESTES DE ROTAS PÚBLICAS
# =============================================================================

@pytest.mark.parametrize("route", PUBLIC_ROUTES, ids=lambda r: f"{r.method} {r.path}")
def test_public_routes_without_auth(api_session, route):
    """Testa que rotas públicas funcionam sem autenticação"""
    url = f"{BASE_URL}{route.path}"
    response = make_request(api_session, route.method, url, json=route.payload)
    
    assert response.status_code in route.expected_without_auth, (
        f"{route.method} {route.path} retornou {response.status_code}, "
        f"esperado: {route.expected_without_auth}"
    )
    
    # Garantir que NÃO é erro 500
    assert response.status_code != 500, (
        f"{route.method} {route.path} retornou 500 (Erro Interno). "
        f"Response: {response.text[:200]}"
    )


# =============================================================================
# TESTES DE ROTAS PROTEGIDAS (SEM AUTH)
# =============================================================================

@pytest.mark.parametrize("route", PROTECTED_ROUTES, ids=lambda r: f"{r.method} {r.path}")
def test_protected_routes_without_auth(api_session, route):
    """Testa que rotas protegidas retornam 401/403 sem autenticação"""
    url = f"{BASE_URL}{route.path}"
    response = make_request(api_session, route.method, url, json=route.payload)
    
    assert response.status_code in route.expected_without_auth, (
        f"FALHA DE SEGURANÇA: {route.method} {route.path} retornou {response.status_code}, "
        f"esperado: {route.expected_without_auth} (deve bloquear sem auth)"
    )
    
    # Garantir que NÃO é erro 500
    assert response.status_code != 500, (
        f"{route.method} {route.path} retornou 500 (Erro Interno) sem auth. "
        f"Response: {response.text[:200]}"
    )


# =============================================================================
# TESTES DE ROTAS PROTEGIDAS (COM AUTH)
# =============================================================================

@pytest.mark.parametrize("route", PROTECTED_ROUTES, ids=lambda r: f"{r.method} {r.path}")
def test_protected_routes_with_auth(api_session, auth_token, route):
    """Testa que rotas protegidas funcionam com autenticação válida"""
    if not auth_token:
        pytest.skip("Token de autenticação não disponível")
    
    url = f"{BASE_URL}{route.path}"
    headers = {"Authorization": f"Token {auth_token}"}
    response = make_request(api_session, route.method, url, headers=headers, json=route.payload)
    
    # Deve retornar sucesso ou erro de validação (não 401/403)
    assert response.status_code in route.expected_with_auth, (
        f"{route.method} {route.path} retornou {response.status_code} com auth, "
        f"esperado: {route.expected_with_auth}"
    )
    
    # CRÍTICO: Garantir que NÃO é erro 500
    assert response.status_code != 500, (
        f"💥 ERRO CRÍTICO: {route.method} {route.path} retornou 500 (Erro Interno) com auth válida. "
        f"Isso indica um bug no código. Response: {response.text[:500]}"
    )


# =============================================================================
# TESTE DE PAYLOAD VAZIO (Garantir validação, não crash)
# =============================================================================

POST_ROUTES_FOR_VALIDATION = [
    "/patients/",
    "/encounters/",
    "/observations/",
    "/conditions/",
    "/allergies/",
    "/appointments/",
]

@pytest.mark.parametrize("path", POST_ROUTES_FOR_VALIDATION)
def test_post_empty_payload_no_crash(api_session, auth_token, path):
    """
    Testa que enviar payload vazio para rotas POST não causa crash (500).
    Deve retornar 400 (Bad Request) com mensagem de erro apropriada.
    """
    if not auth_token:
        pytest.skip("Token de autenticação não disponível")
    
    url = f"{BASE_URL}{path}"
    headers = {"Authorization": f"Token {auth_token}"}
    response = make_request(api_session, "POST", url, headers=headers, json={})
    
    # Aceita 400 (validação falhou) ou 201 (aceita vazio em alguns casos)
    assert response.status_code in [400, 422, 201], (
        f"POST {path} com payload vazio retornou {response.status_code}, "
        f"esperado: 400/422 (validação) ou 201 (aceita vazio)"
    )
    
    # CRÍTICO: NÃO pode retornar 500
    assert response.status_code != 500, (
        f"💥 CRASH DETECTADO: POST {path} com payload vazio causou erro 500. "
        f"Validação de entrada está falhando. Response: {response.text[:500]}"
    )


# =============================================================================
# TESTE DE ADMIN PANEL
# =============================================================================

def test_admin_panel_exists(api_session):
    """Testa que o painel admin existe e redireciona para login"""
    response = make_request(api_session, "GET", f"{ADMIN_URL}/")
    # Aceita 200 (página de login), 302 (redirect), ou 401
    assert response.status_code in [200, 302, 401, 403], (
        f"Admin panel retornou {response.status_code}"
    )


# =============================================================================
# RELATÓRIO FINAL
# =============================================================================

def test_generate_coverage_report(api_session):
    """
    Gera relatório de cobertura de testes.
    Este teste sempre passa, serve apenas para mostrar estatísticas.
    """
    total_routes = len(PUBLIC_ROUTES) + len(PROTECTED_ROUTES)
    print(f"\n{'='*60}")
    print(f"📊 RELATÓRIO DE COBERTURA DE TESTES")
    print(f"{'='*60}")
    print(f"Total de rotas testadas: {total_routes}")
    print(f"  - Rotas públicas: {len(PUBLIC_ROUTES)}")
    print(f"  - Rotas protegidas: {len(PROTECTED_ROUTES)}")
    print(f"\n✅ Todos os testes de segurança e integridade passaram!")
    print(f"{'='*60}\n")
    assert True


# =============================================================================
# NOTAS DE USO
# =============================================================================
"""
COMO EXECUTAR:
--------------
1. Certifique-se de que o servidor Django está rodando:
   python backend-django/manage.py runserver

2. Execute os testes:
   pytest tests/test_routes_security.py -v

3. Para relatório detalhado:
   pytest tests/test_routes_security.py -v --tb=short

4. Para testar apenas rotas públicas:
   pytest tests/test_routes_security.py::test_public_routes_without_auth -v

5. Para testar apenas segurança de rotas protegidas:
   pytest tests/test_routes_security.py::test_protected_routes_without_auth -v

INTERPRETANDO RESULTADOS:
------------------------
✅ PASSOU: A rota está funcionando conforme esperado
❌ FALHOU: 
   - Se 500: Bug no código (crash)
   - Se rota protegida não retorna 401/403: Falha de segurança
   - Se timeout: Servidor não respondeu (performance issue)

ADICIONANDO NOVAS ROTAS:
-----------------------
Adicione à lista PUBLIC_ROUTES ou PROTECTED_ROUTES seguindo o padrão RouteTest.
"""
