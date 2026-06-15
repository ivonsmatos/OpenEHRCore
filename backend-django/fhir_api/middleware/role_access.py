"""
RBAC por papel via middleware (matriz por prefixo de rota) — defesa em profundidade.

Os papéis vêm do JWT do Keycloak (realm_access.roles). A ASSINATURA do token é
validada na view (KeycloakAuthentication); aqui só lemos os papéis para o controle
de acesso por rota — um token forjado é rejeitado depois pela autenticação real.

Matriz: admin acessa tudo. Rotas abertas (auth/health/docs/me/smart) passam livres.
Rotas não mapeadas: liberadas para qualquer autenticado (default seguro/não-bloqueante).
"""

import base64
import json
import logging

from django.http import JsonResponse

logger = logging.getLogger(__name__)

CLINICAL = {"medico", "enfermeiro", "admin"}
AGENDA = {"medico", "enfermeiro", "recepcao", "recepcionista", "admin"}
ADMIN_ONLY = {"admin"}

# Prefixo (1º segmento após /api/v1/) -> papéis permitidos.
ROLE_MATRIX = {
    "patients": CLINICAL, "encounters": CLINICAL, "observations": CLINICAL,
    "conditions": CLINICAL, "allergies": CLINICAL, "medication": CLINICAL,
    "medications": CLINICAL, "careplan": CLINICAL, "care-plans": CLINICAL,
    "clinical": CLINICAL, "documents": CLINICAL, "diagnostic": CLINICAL,
    "immunization": CLINICAL, "immunizations": CLINICAL, "procedures": CLINICAL,
    "ai": CLINICAL, "exams": CLINICAL, "ipd": CLINICAL, "chat": CLINICAL,
    "appointments": AGENDA, "scheduling": AGENDA, "schedule": AGENDA,
    "checkin": AGENDA, "availability": AGENDA, "visitors": AGENDA,
    "financial": ADMIN_ONLY, "invoices": ADMIN_ONLY, "accounts": ADMIN_ONLY,
    "coverage": ADMIN_ONLY, "tiss": ADMIN_ONLY, "billing": ADMIN_ONLY,
    "organizations": ADMIN_ONLY,
}

OPEN_PREFIXES = {
    "auth", "health", "metrics", "docs", "me", "smart", ".well-known", "fhircast",
}
API_PREFIX = "/api/v1/"


def _roles_from_token(request):
    auth = request.META.get("HTTP_AUTHORIZATION", "")
    if not auth.startswith("Bearer "):
        return None
    token = auth.split(" ", 1)[1]
    try:
        payload_b64 = token.split(".")[1]
        payload_b64 += "=" * (-len(payload_b64) % 4)
        data = json.loads(base64.urlsafe_b64decode(payload_b64))
        return set((data.get("realm_access") or {}).get("roles") or [])
    except Exception:  # noqa: BLE001 — token inválido/bypass: deixa a view tratar a auth
        return None


class RoleAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path
        if path.startswith(API_PREFIX):
            seg = path[len(API_PREFIX):].split("/", 1)[0]
            if seg not in OPEN_PREFIXES and seg in ROLE_MATRIX:
                roles = _roles_from_token(request)
                # Sem token -> a view (IsAuthenticated) responde 401. Só barramos
                # quando há token válido com papéis que não cobrem a rota.
                if roles is not None and "admin" not in roles and not (roles & ROLE_MATRIX[seg]):
                    logger.info("RBAC: acesso negado a /%s (papéis: %s)", seg, sorted(roles))
                    return JsonResponse(
                        {"error": "Forbidden", "detail": f"Seu papel não tem acesso a /{seg}.", "status": 403},
                        status=403,
                    )
        return self.get_response(request)
