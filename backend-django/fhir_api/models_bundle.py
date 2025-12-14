"""
FHIR Bundle Implementation - Sprint 33
HL7 FHIR R4 - Bundle Resource

Features:
- Atomic transactions (rollback on failure)
- Batch operations
- Multiple resource types in single request
- ACID compliance
- Audit logging

Bundle Types:
- transaction: Atomic (all-or-nothing)
- batch: Independent operations
- document: Clinical document with entries
- collection: Search results
"""

from django.db import models, transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
import uuid


class Bundle(models.Model):
    """FHIR R4 Bundle Resource"""
    
    BUNDLE_TYPE_CHOICES = [
        ('document', 'Document'),
        ('message', 'Message'),
        ('transaction', 'Transaction'),
        ('transaction-response', 'Transaction Response'),
        ('batch', 'Batch'),
        ('batch-response', 'Batch Response'),
        ('history', 'History List'),
        ('searchset', 'Search Results'),
        ('collection', 'Collection'),
    ]
    
    # Identificadores
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    identifier = models.CharField(max_length=255, unique=True, blank=True, null=True)
    
    # Tipo do Bundle
    type = models.CharField(max_length=30, choices=BUNDLE_TYPE_CHOICES)
    
    # Timestamp
    timestamp = models.DateTimeField(default=timezone.now)
    
    # Total (para search results)
    total = models.IntegerField(blank=True, null=True, help_text='Total de recursos encontrados')
    
    # Entries (recursos contidos no bundle)
    entries = models.JSONField(
        default=list,
        help_text='Array de BundleEntry (fullUrl, resource, request, response)'
    )
    
    # Metadata
    created_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_bundles'
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pendente'),
            ('processing', 'Processando'),
            ('completed', 'Completo'),
            ('failed', 'Falhou'),
        ],
        default='pending'
    )
    
    # Resultado
    result_message = models.TextField(blank=True, null=True)
    failed_entries = models.JSONField(default=list, help_text='Entradas que falharam')
    
    # Auditoria
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'FHIR Bundle'
        verbose_name_plural = 'FHIR Bundles'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['type', '-timestamp']),
            models.Index(fields=['status']),
            models.Index(fields=['created_by', '-timestamp']),
        ]
    
    def __str__(self):
        return f"Bundle {self.type} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"
    
    def clean(self):
        """Validações customizadas"""
        super().clean()
        
        # Transaction/batch devem ter entries
        if self.type in ['transaction', 'batch']:
            if not self.entries or len(self.entries) == 0:
                raise ValidationError('Bundle do tipo transaction/batch deve ter pelo menos uma entry')
        
        # Document deve ter composition como primeira entrada
        if self.type == 'document':
            if not self.entries or len(self.entries) == 0:
                raise ValidationError('Bundle do tipo document deve ter entries')
            
            first_entry = self.entries[0]
            if 'resource' not in first_entry or first_entry['resource'].get('resourceType') != 'Composition':
                raise ValidationError('Primeira entrada de Bundle document deve ser Composition')
    
    def to_fhir(self):
        """Converte para formato FHIR R4 canônico"""
        fhir_bundle = {
            'resourceType': 'Bundle',
            'id': str(self.id),
            'type': self.type,
            'timestamp': self.timestamp.isoformat(),
        }
        
        # Identifier (opcional)
        if self.identifier:
            fhir_bundle['identifier'] = {
                'system': 'http://openehrcore.com/fhir/Bundle',
                'value': self.identifier
            }
        
        # Total (para searchset)
        if self.total is not None:
            fhir_bundle['total'] = self.total
        
        # Entries
        if self.entries:
            fhir_bundle['entry'] = self.entries
        
        return fhir_bundle
    
    @transaction.atomic
    def process_transaction(self):
        """
        Processa Bundle do tipo transaction (ACID)
        Rollback completo em caso de qualquer falha
        """
        if self.type != 'transaction':
            raise ValidationError('Este método só funciona para bundles do tipo transaction')
        
        self.status = 'processing'
        self.save()
        
        from .bundle_processor import BundleTransactionProcessor
        
        try:
            processor = BundleTransactionProcessor(self)
            result = processor.process()
            
            self.status = 'completed'
            self.result_message = f'Transação completada com sucesso. {len(result["entry"])} recursos processados.'
            self.entries = result['entry']  # Atualizar com responses
            self.save()
            
            return result
            
        except Exception as e:
            self.status = 'failed'
            self.result_message = f'Erro na transação: {str(e)}'
            self.save()
            raise
    
    def process_batch(self):
        """
        Processa Bundle do tipo batch (operações independentes)
        Continua mesmo se algumas operações falharem
        """
        if self.type != 'batch':
            raise ValidationError('Este método só funciona para bundles do tipo batch')
        
        self.status = 'processing'
        self.save()
        
        from .bundle_processor import BundleBatchProcessor
        
        processor = BundleBatchProcessor(self)
        result = processor.process()
        
        # Verificar se houve falhas
        failed_count = sum(
            1 for entry in result['entry']
            if 'response' in entry and entry['response'].get('status', '').startswith(('4', '5'))
        )
        
        if failed_count > 0:
            self.status = 'completed'  # Batch não falha totalmente
            self.result_message = f'Batch processado. {failed_count}/{len(result["entry"])} operações falharam.'
            self.failed_entries = [
                entry for entry in result['entry']
                if 'response' in entry and entry['response'].get('status', '').startswith(('4', '5'))
            ]
        else:
            self.status = 'completed'
            self.result_message = f'Batch completado com sucesso. {len(result["entry"])} operações processadas.'
        
        self.entries = result['entry']
        self.save()
        
        return result


class BundleEntry(models.Model):
    """
    Modelo auxiliar para rastrear entries individuais de um Bundle
    Útil para auditoria e debugging
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bundle = models.ForeignKey(Bundle, on_delete=models.CASCADE, related_name='entry_records')
    
    # URL completa do recurso
    full_url = models.URLField(max_length=500, blank=True, null=True)
    
    # Tipo de recurso (Patient, Observation, etc.)
    resource_type = models.CharField(max_length=50)
    resource_id = models.CharField(max_length=255, blank=True, null=True)
    
    # Request (para transaction/batch)
    request_method = models.CharField(
        max_length=10,
        choices=[
            ('GET', 'GET'),
            ('POST', 'POST'),
            ('PUT', 'PUT'),
            ('PATCH', 'PATCH'),
            ('DELETE', 'DELETE'),
        ],
        blank=True,
        null=True
    )
    request_url = models.CharField(max_length=500, blank=True, null=True)
    
    # Response (após processamento)
    response_status = models.CharField(max_length=10, blank=True, null=True)
    response_location = models.URLField(max_length=500, blank=True, null=True)
    response_etag = models.CharField(max_length=100, blank=True, null=True)
    response_last_modified = models.DateTimeField(blank=True, null=True)
    
    # Conteúdo do recurso (JSON)
    resource_json = models.JSONField()
    
    # Status
    processed = models.BooleanField(default=False)
    error_message = models.TextField(blank=True, null=True)
    
    # Auditoria
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Bundle Entry'
        verbose_name_plural = 'Bundle Entries'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['bundle', 'resource_type']),
            models.Index(fields=['resource_type', 'resource_id']),
        ]
    
    def __str__(self):
        return f"{self.resource_type}/{self.resource_id or 'new'} - {self.request_method or 'N/A'}"
