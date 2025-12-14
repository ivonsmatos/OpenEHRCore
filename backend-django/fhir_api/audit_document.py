"""
Audit Logging para DocumentReference

Sprint 33: Rastreabilidade de acessos a documentos (LGPD Compliance)
"""

from .models import AuditEvent
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


def log_document_access(user, document, action='view', notes=None):
    """
    Registra acesso a documento médico
    
    Args:
        user: Usuário que acessou
        document: DocumentReference acessado
        action: 'view', 'download', 'print'
        notes: Observações adicionais
    """
    try:
        audit_event = AuditEvent.objects.create(
            action='R' if action == 'view' else 'E',  # Read ou Execute
            outcome='0',  # Success
            agent_type='user',
            agent_who=f"User/{user.id}",
            agent_name=user.get_full_name() or user.username,
            agent_requestor=True,
            source_site='DocumentReference',
            entity_type='DocumentReference',
            entity_what=f"DocumentReference/{document.id}",
            entity_name=document.description or document.get_type_display(),
            entity_description=f"Patient: {document.patient.name}, Type: {document.get_type_display()}",
            purpose_of_use=action,
            recorded=timezone.now()
        )
        
        logger.info(
            f"Document {action}: User {user.username} {action}ed document {document.id} "
            f"(Patient: {document.patient.id})"
        )
        
        return audit_event
        
    except Exception as e:
        logger.error(f"Failed to log document access: {str(e)}")
        return None


def log_document_upload(user, document, notes=None):
    """
    Registra upload de novo documento
    
    Args:
        user: Usuário que fez upload
        document: DocumentReference criado
        notes: Observações
    """
    try:
        audit_event = AuditEvent.objects.create(
            action='C',  # Create
            outcome='0',  # Success
            agent_type='user',
            agent_who=f"User/{user.id}",
            agent_name=user.get_full_name() or user.username,
            agent_requestor=True,
            source_site='DocumentReference',
            entity_type='DocumentReference',
            entity_what=f"DocumentReference/{document.id}",
            entity_name=document.description or document.get_type_display(),
            entity_description=f"Uploaded: Patient {document.patient.name}, Type: {document.get_type_display()}",
            purpose_of_use='upload',
            recorded=timezone.now()
        )
        
        logger.info(
            f"Document upload: User {user.username} uploaded {document.get_type_display()} "
            f"for patient {document.patient.id}"
        )
        
        return audit_event
        
    except Exception as e:
        logger.error(f"Failed to log document upload: {str(e)}")
        return None


def log_document_deletion(user, document, reason=None):
    """
    Registra exclusão de documento (crítico para auditoria)
    """
    try:
        audit_event = AuditEvent.objects.create(
            action='D',  # Delete
            outcome='0',
            agent_type='user',
            agent_who=f"User/{user.id}",
            agent_name=user.get_full_name() or user.username,
            agent_requestor=True,
            source_site='DocumentReference',
            entity_type='DocumentReference',
            entity_what=f"DocumentReference/{document.id}",
            entity_name=document.description or document.get_type_display(),
            entity_description=f"Deleted: {reason or 'No reason provided'}",
            purpose_of_use='deletion',
            recorded=timezone.now()
        )
        
        logger.warning(
            f"Document deletion: User {user.username} deleted document {document.id}. "
            f"Reason: {reason}"
        )
        
        return audit_event
        
    except Exception as e:
        logger.error(f"Failed to log document deletion: {str(e)}")
        return None
