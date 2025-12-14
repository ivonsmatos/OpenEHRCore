"""
Permissions para DocumentReference

Sprint 33: Controle de acesso granular para documentos médicos
"""

from rest_framework import permissions


class CanViewPatientDocuments(permissions.BasePermission):
    """
    Permissão para visualizar documentos de pacientes
    - Médico pode ver documentos de seus pacientes
    - Enfermeiro pode ver documentos de pacientes na sua unidade
    - Admin pode ver tudo
    """
    
    message = "Você não tem permissão para acessar documentos deste paciente"
    
    def has_permission(self, request, view):
        """Verifica se usuário tem permissão básica"""
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        """Verifica permissão específica para o documento"""
        user = request.user
        
        # Admin tem acesso total
        if user.is_staff or user.is_superuser:
            return True
        
        # Verifica se usuário tem role de médico/enfermeiro
        if hasattr(user, 'practitioner'):
            practitioner = user.practitioner
            
            # Autor do documento pode acessar
            if obj.author == practitioner:
                return True
            
            # Médico responsável pelo paciente
            if hasattr(obj.patient, 'responsible_practitioner'):
                if obj.patient.responsible_practitioner == practitioner:
                    return True
        
        # Paciente pode ver seus próprios documentos
        if hasattr(user, 'patient'):
            if obj.patient == user.patient:
                # Verifica security label
                if 'V' in obj.security_label:  # Very Restricted
                    return False
                return True
        
        return False


class CanCreateDocuments(permissions.BasePermission):
    """
    Permissão para criar/upload de documentos
    Apenas profissionais de saúde e staff
    """
    
    message = "Apenas profissionais de saúde podem fazer upload de documentos"
    
    def has_permission(self, request, view):
        user = request.user
        
        # Staff e admin podem
        if user.is_staff or user.is_superuser:
            return True
        
        # Profissionais de saúde podem
        if hasattr(user, 'practitioner'):
            return True
        
        return False


class CanDeleteDocument(permissions.BasePermission):
    """
    Permissão para deletar documentos
    Apenas autor ou admin
    """
    
    message = "Você não pode deletar este documento"
    
    def has_object_permission(self, request, view, obj):
        user = request.user
        
        # Admin pode deletar
        if user.is_staff or user.is_superuser:
            return True
        
        # Autor pode deletar (dentro de 24h da criação)
        if hasattr(user, 'practitioner') and obj.author == user.practitioner:
            from django.utils import timezone
            from datetime import timedelta
            
            time_since_creation = timezone.now() - obj.created_at
            if time_since_creation < timedelta(hours=24):
                return True
        
        return False
