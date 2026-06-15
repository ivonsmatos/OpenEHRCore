"""
Disponibilidade (horários de atendimento) do profissional.

GET/PUT /api/v1/practitioners/<id>/availability/ — persiste os slots como um
recurso FHIR Basic (code=availability-config) com os slots em uma extensão JSON.
"""

import json
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

AVAIL_SYSTEM = "http://interophealth.com.br/fhir/NamingSystem/availability"
SLOTS_EXT = "http://interophealth.com.br/fhir/StructureDefinition/availability-slots"


def _find(svc, pid):
    # FHIR Basic NÃO tem search param 'identifier' (só 'subject'/'code'). Buscamos
    # por subject=Practitioner/<id> e filtramos pelo nosso code.
    try:
        results = svc.search_resources("Basic", {"subject": f"Practitioner/{pid}"})
        for res in results:
            for c in (res.get("code") or {}).get("coding", []):
                if c.get("code") == "availability-config":
                    return res
        return None
    except Exception as e:  # noqa: BLE001
        logger.warning("Falha ao buscar disponibilidade: %s", e)
        return None


def _slots_of(resource):
    for ext in (resource or {}).get("extension", []):
        if ext.get("url") == SLOTS_EXT and ext.get("valueString"):
            try:
                return json.loads(ext["valueString"])
            except (ValueError, TypeError):
                return []
    return []


@api_view(["GET", "PUT"])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def practitioner_availability(request, practitioner_id):
    svc = FHIRService(request.user)
    existing = _find(svc, practitioner_id)

    if request.method == "GET":
        return Response({"practitionerId": practitioner_id, "slots": _slots_of(existing)})

    # PUT
    slots = (request.data or {}).get("slots", [])
    resource = dict(existing) if existing else {}
    resource["resourceType"] = "Basic"
    resource["identifier"] = [{"system": AVAIL_SYSTEM, "value": str(practitioner_id)}]
    resource["code"] = {"coding": [{
        "system": "http://interophealth.com.br/fhir/CodeSystem/basic-type",
        "code": "availability-config",
    }]}
    resource["subject"] = {"reference": f"Practitioner/{practitioner_id}"}
    resource["extension"] = [{"url": SLOTS_EXT, "valueString": json.dumps(slots)}]
    try:
        if existing and existing.get("id"):
            svc.update_resource("Basic", existing["id"], resource)
        else:
            svc.create_resource("Basic", resource)
        return Response({"practitionerId": practitioner_id, "slots": slots, "saved": True})
    except FHIRServiceException as e:
        logger.error("Falha ao salvar disponibilidade: %s", e)
        return Response(
            {"error": "BadGateway", "detail": "Falha ao salvar disponibilidade.", "status": 502},
            status=status.HTTP_502_BAD_GATEWAY,
        )
