"""
Permissions para API FHIR

Controle de acesso baseado em roles (RBAC). As roles são lidas do token
Keycloak via ``KeycloakUser.roles``. Convenção de roles:

- ``admin``        : acesso total
- ``medico`` / ``practitioner`` : profissionais de saúde
- ``patient``      : paciente (acesso apenas aos próprios dados)
"""

from rest_framework.permissions import BasePermission

PRACTITIONER_ROLES = {"admin", "medico", "practitioner", "enfermeiro", "nurse"}
ADMIN_ROLES = {"admin"}


def _roles(user) -> set:
    """Retorna o conjunto de roles do usuário (vazio se não autenticado)."""
    return set(getattr(user, "roles", []) or [])


def _is_admin(user) -> bool:
    return getattr(user, "is_staff", False) or getattr(user, "is_superuser", False) \
        or bool(_roles(user) & ADMIN_ROLES)


def _is_practitioner(user) -> bool:
    return _is_admin(user) or bool(_roles(user) & PRACTITIONER_ROLES)


def _owns_resource(user, obj) -> bool:
    """
    Best-effort: verifica se o objeto pertence ao paciente autenticado.

    Compara o ``sub`` do token com identificadores comuns no objeto. Quando o
    vínculo não pode ser determinado, retorna False (nega por padrão).
    """
    sub = getattr(user, "sub", None) or (user.get("sub") if hasattr(user, "get") else None)
    if not sub:
        return False
    for attr in ("patient_id", "subject_id", "owner_id", "created_by"):
        value = getattr(obj, attr, None)
        if value is not None and str(value) == str(sub):
            return True
    return False


class CanViewPatientDocuments(BasePermission):
    """Visualizar documentos: admin/practitioner veem; paciente vê só os seus."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if _is_practitioner(request.user):
            return True
        return _owns_resource(request.user, obj)


class CanCreateDocuments(BasePermission):
    """Criar documentos clínicos: apenas profissionais de saúde."""

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        return _is_practitioner(request.user)


class CanEditDocuments(BasePermission):
    """Editar documentos: admin tudo; practitioner apenas o que criou."""

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        return _is_practitioner(request.user)

    def has_object_permission(self, request, view, obj):
        if _is_admin(request.user):
            return True
        created_by = getattr(obj, "created_by", None)
        return created_by is not None and created_by == request.user


class CanDeleteDocuments(BasePermission):
    """Deletar documentos: apenas admins."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and _is_admin(request.user))


class IsPractitioner(BasePermission):
    """Usuário é profissional de saúde (ou admin)."""

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        return _is_practitioner(request.user)


class IsPatient(BasePermission):
    """Usuário possui a role 'patient' (ou é admin)."""

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        return _is_admin(request.user) or "patient" in _roles(request.user)
