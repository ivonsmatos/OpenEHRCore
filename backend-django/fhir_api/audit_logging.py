"""
Audit Logging Utilities

Funções auxiliares para registrar auditoria de acessos e operações
"""

import logging

logger = logging.getLogger(__name__)


def log_document_access(user, document_id, action='view'):
    """
    Registra acesso a documento
    
    Args:
        user: Usuario que acessou
        document_id: ID do documento
        action: Ação realizada (view, download, etc)
    """
    logger.info(f"Document access: user={user.username} document={document_id} action={action}")
    # TODO: Salvar em AuditEvent FHIR ou tabela de auditoria


def log_document_upload(user, document_id, document_type=None):
    """
    Registra upload de documento
    
    Args:
        user: Usuario que fez upload
        document_id: ID do documento
        document_type: Tipo do documento
    """
    logger.info(f"Document upload: user={user.username} document={document_id} type={document_type}")
    # TODO: Salvar em AuditEvent FHIR ou tabela de auditoria


def log_resource_access(user, resource_type, resource_id, action='read'):
    """
    Registra acesso a recurso FHIR genérico
    
    Args:
        user: Usuario que acessou
        resource_type: Tipo do recurso FHIR
        resource_id: ID do recurso
        action: Ação realizada (read, create, update, delete)
    """
    logger.info(f"Resource access: user={user.username} resource={resource_type}/{resource_id} action={action}")
    # TODO: Salvar em AuditEvent FHIR


def log_authentication(user, success=True, method='password'):
    """
    Registra tentativa de autenticação
    
    Args:
        user: Usuario (ou username se falhou)
        success: Se autenticação foi bem sucedida
        method: Método de autenticação (password, token, oauth, etc)
    """
    status = 'SUCCESS' if success else 'FAILED'
    username = user.username if hasattr(user, 'username') else str(user)
    logger.info(f"Authentication {status}: user={username} method={method}")
    # TODO: Salvar em AuditEvent FHIR
