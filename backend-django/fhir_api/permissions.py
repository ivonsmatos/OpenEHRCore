"""
Permissions para API FHIR

Custom permissions para controle de acesso baseado em roles
"""

from rest_framework.permissions import BasePermission


class CanViewPatientDocuments(BasePermission):
    """
    Permissão para visualizar documentos de pacientes
    
    - Admins: podem ver tudo
    - Practitioners: podem ver documentos de seus pacientes
    - Patients: podem ver apenas seus próprios documentos
    """
    
    def has_permission(self, request, view):
        # User deve estar autenticado
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Admin pode tudo
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # TODO: Implementar lógica de permissões específica
        # Por enquanto, permite tudo para usuários autenticados
        return True


class CanCreateDocuments(BasePermission):
    """
    Permissão para criar documentos
    
    - Admins: podem criar
    - Practitioners: podem criar
    - Patients: normalmente não podem criar documentos clínicos
    """
    
    def has_permission(self, request, view):
        # User deve estar autenticado
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admin pode tudo
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # TODO: Verificar se é practitioner
        return True


class CanEditDocuments(BasePermission):
    """
    Permissão para editar documentos
    
    - Admins: podem editar tudo
    - Practitioners: podem editar documentos que criaram
    - Patients: não podem editar
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Admin pode tudo
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # Pode editar se criou o documento
        if hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        
        return False


class CanDeleteDocuments(BasePermission):
    """
    Permissão para deletar documentos
    
    Apenas admins por padrão
    """
    
    def has_permission(self, request, view):
        return request.user and (request.user.is_staff or request.user.is_superuser)


class IsPractitioner(BasePermission):
    """
    Permissão para verificar se é practitioner
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admin sempre é practitioner
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # TODO: Verificar role no Keycloak ou banco
        return True


class IsPatient(BasePermission):
    """
    Permissão para verificar se é patient
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # TODO: Verificar role no Keycloak ou banco
        return True
