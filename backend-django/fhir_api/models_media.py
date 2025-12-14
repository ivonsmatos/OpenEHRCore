"""
Media Models - FHIR R4

Sprint 35: Media Resource para imagens/vídeos/áudio clínico
Resource para fotos de feridas, raio-X, vídeos de procedimentos, etc
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.utils import timezone
import uuid
import base64
import os


class Media(models.Model):
    """
    FHIR Media Resource
    
    Registro de fotos, vídeos, áudio ou outros dados multimídia.
    Usado para:
    - Fotos de feridas/lesões
    - Imagens de raio-X (simples, não DICOM completo)
    - Vídeos de procedimentos
    - Gravações de áudio (ausculta, etc)
    - Fotos de documentos
    
    Campos principais:
    - status: preparation | in-progress | not-done | on-hold | stopped | completed | entered-in-error | unknown
    - type: image | video | audio
    - modality: Modalidade (XR, CT, MR, US, foto, etc)
    - view: Código da view (PA, lateral, etc)
    - subject: Patient (required)
    - content: Attachment com data binário
    """
    
    STATUS_CHOICES = [
        ('preparation', 'Preparation'),
        ('in-progress', 'In Progress'),
        ('not-done', 'Not Done'),
        ('on-hold', 'On Hold'),
        ('stopped', 'Stopped'),
        ('completed', 'Completed'),
        ('entered-in-error', 'Entered in Error'),
        ('unknown', 'Unknown'),
    ]
    
    TYPE_CHOICES = [
        ('image', 'Image'),
        ('video', 'Video'),
        ('audio', 'Audio'),
    ]
    
    # Identificação
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    identifier = models.CharField(max_length=100, unique=True, db_index=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='completed', db_index=True)
    
    # Tipo
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, db_index=True)
    
    # Modalidade (XR, CT, MR, US, foto digital, vídeo, etc)
    modality = models.JSONField(null=True, blank=True)  # CodeableConcept
    
    # View/projeção (PA, lateral, oblíqua, etc)
    view = models.JSONField(null=True, blank=True)  # CodeableConcept
    
    # Contexto
    subject_id = models.CharField(max_length=100, db_index=True)  # Reference Patient (required)
    encounter_id = models.CharField(max_length=100, null=True, blank=True, db_index=True)  # Reference Encounter
    
    # Quando foi criado/capturado
    created_datetime = models.DateTimeField(default=timezone.now, db_index=True)
    issued = models.DateTimeField(null=True, blank=True)  # Quando foi publicado
    
    # Operador/performer
    operator_id = models.CharField(max_length=100, null=True, blank=True)  # Reference Practitioner
    operator_display = models.CharField(max_length=200, null=True, blank=True)
    
    # Razão
    reason_code = models.JSONField(null=True, blank=True)  # CodeableConcept
    
    # Body site (parte do corpo)
    body_site = models.JSONField(null=True, blank=True)  # CodeableConcept
    
    # Device usado (câmera, scanner, etc)
    device_name = models.CharField(max_length=200, null=True, blank=True)
    
    # Dimensões (para imagem/vídeo)
    width = models.IntegerField(null=True, blank=True)
    height = models.IntegerField(null=True, blank=True)
    frames = models.IntegerField(null=True, blank=True)  # Número de frames
    duration = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # Duração em segundos
    
    # Content - attachment
    content_type = models.CharField(max_length=100, db_index=True)  # MIME type
    content_title = models.CharField(max_length=200, null=True, blank=True)
    content_creation = models.DateTimeField(null=True, blank=True)
    
    # Storage
    file_path = models.CharField(max_length=500, null=True, blank=True)  # Path no storage
    file_size = models.IntegerField(null=True, blank=True)  # Tamanho em bytes
    file_hash = models.CharField(max_length=64, null=True, blank=True)  # SHA-256 hash
    
    # Thumbnail
    thumbnail_path = models.CharField(max_length=500, null=True, blank=True)
    thumbnail_size = models.IntegerField(null=True, blank=True)
    
    # Notas
    note = models.TextField(null=True, blank=True)
    
    # Auditoria
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_media')
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'fhir_media'
        verbose_name_plural = 'Media'
        ordering = ['-created_datetime']
        indexes = [
            models.Index(fields=['subject_id', 'created_datetime']),
            models.Index(fields=['type', 'status']),
            models.Index(fields=['encounter_id']),
        ]
    
    def __str__(self):
        title = self.content_title or f"{self.type} media"
        return f"Media {self.identifier}: {title} ({self.status})"
    
    def clean(self):
        """Validações customizadas"""
        # Content type validation
        if self.content_type:
            if self.type == 'image' and not self.content_type.startswith('image/'):
                raise ValidationError("Content type must be image/* for type=image")
            elif self.type == 'video' and not self.content_type.startswith('video/'):
                raise ValidationError("Content type must be video/* for type=video")
            elif self.type == 'audio' and not self.content_type.startswith('audio/'):
                raise ValidationError("Content type must be audio/* for type=audio")
    
    def save(self, *args, **kwargs):
        # Gerar identifier se não existir
        if not self.identifier:
            self.identifier = f"MEDIA-{self.id}"
        
        self.full_clean()
        super().save(*args, **kwargs)
    
    def get_file_data(self):
        """Retorna dados do arquivo como bytes"""
        if self.file_path and default_storage.exists(self.file_path):
            with default_storage.open(self.file_path, 'rb') as f:
                return f.read()
        return None
    
    def get_thumbnail_data(self):
        """Retorna dados do thumbnail como bytes"""
        if self.thumbnail_path and default_storage.exists(self.thumbnail_path):
            with default_storage.open(self.thumbnail_path, 'rb') as f:
                return f.read()
        return None
    
    def to_fhir(self, include_data=False):
        """
        Converte para FHIR Media R4
        
        Args:
            include_data: Se True, inclui dados binários inline (base64)
        """
        resource = {
            'resourceType': 'Media',
            'id': str(self.id),
            'identifier': [{
                'system': 'http://openehrcore.com.br/fhir/media',
                'value': self.identifier
            }],
            'status': self.status,
            'type': {
                'coding': [{
                    'system': 'http://terminology.hl7.org/CodeSystem/media-type',
                    'code': self.type,
                    'display': dict(self.TYPE_CHOICES)[self.type]
                }]
            },
            'subject': {
                'reference': f'Patient/{self.subject_id}'
            },
            'createdDateTime': self.created_datetime.isoformat()
        }
        
        # Modality
        if self.modality:
            resource['modality'] = self.modality
        
        # View
        if self.view:
            resource['view'] = self.view
        
        # Encounter
        if self.encounter_id:
            resource['encounter'] = {
                'reference': f'Encounter/{self.encounter_id}'
            }
        
        # Issued
        if self.issued:
            resource['issued'] = self.issued.isoformat()
        
        # Operator
        if self.operator_id:
            resource['operator'] = {'reference': self.operator_id}
            if self.operator_display:
                resource['operator']['display'] = self.operator_display
        
        # Reason
        if self.reason_code:
            resource['reasonCode'] = self.reason_code if isinstance(self.reason_code, list) else [self.reason_code]
        
        # Body site
        if self.body_site:
            resource['bodySite'] = self.body_site
        
        # Device
        if self.device_name:
            resource['deviceName'] = self.device_name
        
        # Dimensions
        if self.width:
            resource['width'] = self.width
        if self.height:
            resource['height'] = self.height
        if self.frames:
            resource['frames'] = self.frames
        if self.duration:
            resource['duration'] = float(self.duration)
        
        # Content (Attachment)
        content = {
            'contentType': self.content_type
        }
        
        if self.content_title:
            content['title'] = self.content_title
        
        if self.content_creation:
            content['creation'] = self.content_creation.isoformat()
        
        if self.file_size:
            content['size'] = self.file_size
        
        if self.file_hash:
            content['hash'] = self.file_hash
        
        # URL para download
        content['url'] = f'/api/v1/media/{self.id}/download/'
        
        # Include binary data if requested (WARNING: pode ser muito grande!)
        if include_data:
            file_data = self.get_file_data()
            if file_data:
                content['data'] = base64.b64encode(file_data).decode('utf-8')
        
        resource['content'] = content
        
        # Note
        if self.note:
            resource['note'] = [{
                'text': self.note,
                'time': self.updated_at.isoformat()
            }]
        
        return resource
    
    def delete(self, *args, **kwargs):
        """Override delete para remover arquivos do storage"""
        # Delete file
        if self.file_path and default_storage.exists(self.file_path):
            default_storage.delete(self.file_path)
        
        # Delete thumbnail
        if self.thumbnail_path and default_storage.exists(self.thumbnail_path):
            default_storage.delete(self.thumbnail_path)
        
        super().delete(*args, **kwargs)
