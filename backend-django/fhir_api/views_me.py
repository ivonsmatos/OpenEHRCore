"""
Perfil do usuário autenticado, persistido como FHIR Practitioner.

GET/PUT /api/v1/me/profile/ — salva nome, e-mail, telefone, endereço,
especialidade, CRM/COREN e foto do profissional logado. Um Practitioner por
usuário, chaveado por um identifier = `sub` do Keycloak.
"""

import logging

from rest_framework import status
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .authentication import KeycloakAuthentication
from .services.fhir_core import FHIRService, FHIRServiceException

logger = logging.getLogger(__name__)

KC_SUB_SYSTEM = "http://interophealth.com.br/fhir/NamingSystem/keycloak-sub"
CONSELHO_SYSTEM = "http://interophealth.com.br/fhir/NamingSystem/conselho"


def _find_practitioner(svc, sub):
    try:
        results = svc.search_resources(
            "Practitioner", {"identifier": f"{KC_SUB_SYSTEM}|{sub}"}, use_cache=False
        )
        return results[0] if results else None
    except Exception as e:  # noqa: BLE001
        logger.warning("Falha ao buscar Practitioner do usuário: %s", e)
        return None


def _to_profile(p):
    """FHIR Practitioner -> dict do formulário do frontend."""
    if not p:
        return {}
    name = ""
    if p.get("name"):
        n = p["name"][0]
        name = n.get("text") or " ".join(
            (n.get("given") or []) + ([n["family"]] if n.get("family") else [])
        )
    tel = {t.get("system"): t.get("value") for t in p.get("telecom", [])}
    address = p["address"][0].get("text", "") if p.get("address") else ""
    specialty = ""
    if p.get("qualification"):
        specialty = (p["qualification"][0].get("code") or {}).get("text", "")
    crm = ""
    for ident in p.get("identifier", []):
        if ident.get("system") == CONSELHO_SYSTEM:
            crm = ident.get("value", "")
    photo = ""
    if p.get("photo") and p["photo"][0].get("data"):
        ph = p["photo"][0]
        photo = f"data:{ph.get('contentType', 'image/jpeg')};base64,{ph['data']}"
    return {
        "name": name,
        "email": tel.get("email", ""),
        "phone": tel.get("phone", ""),
        "address": address,
        "specialty": specialty,
        "crm": crm,
        "photo": photo,
    }


def _build_practitioner(sub, data, existing=None):
    p = dict(existing) if existing else {}
    p["resourceType"] = "Practitioner"

    idents = [{"system": KC_SUB_SYSTEM, "value": sub}]
    if data.get("crm"):
        idents.append({"system": CONSELHO_SYSTEM, "value": data["crm"]})
    p["identifier"] = idents

    if data.get("name"):
        p["name"] = [{"text": data["name"]}]

    telecom = []
    if data.get("email"):
        telecom.append({"system": "email", "value": data["email"]})
    if data.get("phone"):
        telecom.append({"system": "phone", "value": data["phone"]})
    p["telecom"] = telecom

    if data.get("address"):
        p["address"] = [{"text": data["address"]}]
    else:
        p.pop("address", None)

    if data.get("specialty"):
        p["qualification"] = [{"code": {"text": data["specialty"]}}]
    else:
        p.pop("qualification", None)

    photo = data.get("photo")
    if photo and isinstance(photo, str) and photo.startswith("data:"):
        try:
            header, b64 = photo.split(",", 1)
            ctype = header.split(":", 1)[1].split(";", 1)[0]
            p["photo"] = [{"contentType": ctype, "data": b64}]
        except (ValueError, IndexError):
            pass
    else:
        p.pop("photo", None)
    return p


@api_view(["GET", "PUT"])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def me_profile(request):
    """Lê (GET) ou salva (PUT) o perfil do usuário logado como Practitioner."""
    sub = request.user.get("sub") if hasattr(request.user, "get") else None
    if not sub:
        return Response(
            {"error": "Usuário sem identificador (sub)."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    svc = FHIRService(request.user)

    if request.method == "GET":
        prof = _to_profile(_find_practitioner(svc, sub))
        # Defaults vindos do token quando o perfil ainda não foi salvo.
        if not prof.get("name"):
            prof["name"] = request.user.get("name") or request.user.get("preferred_username") or ""
        if not prof.get("email"):
            prof["email"] = request.user.get("email") or ""
        return Response(prof)

    # PUT
    data = request.data or {}
    existing = _find_practitioner(svc, sub)
    resource = _build_practitioner(sub, data, existing)
    try:
        if existing and existing.get("id"):
            saved = svc.update_resource("Practitioner", existing["id"], resource)
        else:
            saved = svc.create_resource("Practitioner", resource)
        return Response(_to_profile(saved), status=status.HTTP_200_OK)
    except FHIRServiceException as e:
        logger.error("Falha ao salvar perfil: %s", e)
        return Response(
            {"error": "Falha ao salvar perfil."},
            status=status.HTTP_502_BAD_GATEWAY,
        )
