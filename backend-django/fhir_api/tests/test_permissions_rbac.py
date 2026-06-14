"""
Testes de RBAC: validam a lógica de roles do KeycloakUser e das permission
classes. São testes unitários puros (sem DB nem rede).
"""

from rest_framework.test import APIRequestFactory

from fhir_api.authentication import KeycloakUser
from fhir_api.permissions import (
    IsPractitioner,
    IsPatient,
    CanCreateDocuments,
    CanDeleteDocuments,
)


def _user(roles):
    return KeycloakUser({
        "sub": "u1",
        "preferred_username": "u",
        "roles": list(roles),
    })


def _request(user):
    request = APIRequestFactory().get("/")
    request.user = user
    return request


# --------------------------------------------------------------------------
# KeycloakUser
# --------------------------------------------------------------------------

def test_admin_role_grants_staff_and_superuser():
    user = _user(["admin"])
    assert user.is_staff is True
    assert user.is_superuser is True
    assert user.has_role("admin")


def test_non_admin_is_not_staff():
    # Regressão do HACK que concedia admin a todos os usuários autenticados.
    user = _user(["medico"])
    assert user.is_staff is False
    assert user.is_superuser is False


def test_user_without_roles_has_no_privileges():
    user = _user([])
    assert user.is_staff is False
    assert user.roles == []


# --------------------------------------------------------------------------
# Permission classes
# --------------------------------------------------------------------------

def test_practitioner_permission():
    assert IsPractitioner().has_permission(_request(_user(["medico"])), None) is True
    assert IsPractitioner().has_permission(_request(_user(["admin"])), None) is True
    assert IsPractitioner().has_permission(_request(_user(["patient"])), None) is False


def test_patient_permission():
    assert IsPatient().has_permission(_request(_user(["patient"])), None) is True
    assert IsPatient().has_permission(_request(_user(["admin"])), None) is True
    assert IsPatient().has_permission(_request(_user(["medico"])), None) is False


def test_create_documents_requires_practitioner():
    assert CanCreateDocuments().has_permission(_request(_user(["medico"])), None) is True
    assert CanCreateDocuments().has_permission(_request(_user(["patient"])), None) is False


def test_delete_documents_requires_admin():
    assert CanDeleteDocuments().has_permission(_request(_user(["admin"])), None) is True
    assert CanDeleteDocuments().has_permission(_request(_user(["medico"])), None) is False
