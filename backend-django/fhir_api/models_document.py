"""
FHIR DocumentReference Resource - Backend Implementation

Sprint 33: Document Management (FHIR R4 Compliance)
Permite anexar documentos médicos (PDFs, imagens, laudos) aos pacientes
"""

from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.core.validators import FileExtensionValidator
from django.conf import settings
import uuid


class DocumentReference(models.Model):
    """
    FHIR DocumentReference Resource
    Anexos médicos: exames, laudos, imagens, PDFs
    
    Spec: https://hl7.org/fhir/R4/documentreference.html
    """
    
    # Status do documento
    STATUS_CHOICES = [
        ('current', 'Current'),
        ('superseded', 'Superseded'),
        ('entered-in-error', 'Entered in Error'),
    ]
    
    # Tipo de documento
    TYPE_CHOICES = [
        ('lab-report', 'Resultado Laboratorial'),
        ('imaging-report', 'Laudo de Imagem'),
        ('prescription', 'Prescrição'),
        ('discharge-summary', 'Sumário de Alta'),
        ('progress-note', 'Evolução'),
        ('consent-form', 'Termo de Consentimento'),
        ('identification', 'Documento de Identificação'),
        ('insurance-card', 'Carteirinha do Convênio'),
        ('other', 'Outro'),
    ]
    
    # FHIR Resource Fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='current')
    doc_status = models.CharField(max_length=20, blank=True, null=True,
                                   help_text='Status do documento: preliminary, final, amended')
    
    # Tipo do documento (LOINC preferred)
    type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    type_code = models.CharField(max_length=50, blank=True, null=True,
                                  help_text='Código LOINC do tipo de documento')
    
    # Categoria
    category = models.CharField(max_length=100, blank=True, null=True,
                                 help_text='Categoria: Clinical Note, Imaging, etc')
    
    # Paciente (subject)
    patient = models.ForeignKey(
        'Patient',
        on_delete=models.CASCADE,
        related_name='documents'
    )
    
    # Data do documento
    date = models.DateTimeField(auto_now_add=True)
    
    # Autor/Criador
    author = models.ForeignKey(
        'Practitioner',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='authored_documents'
    )
    
    # Autenticador (quem validou)
    authenticator = models.ForeignKey(
        'Practitioner',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='authenticated_documents'
    )
    
    # Contexto clínico
    encounter = models.ForeignKey(
        'Encounter',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documents'
    )
    
    # Descrição
    description = models.TextField(blank=True, null=True)
    
    # Security labels (confidencialidade)
    security_label = ArrayField(
        models.CharField(max_length=50),
        default=list,
        blank=True,
        help_text='Níveis de confidencialidade: N (normal), R (restricted), V (very restricted)'
    )
    
    # Content (attachments)
    # Usando JSON para armazenar múltiplos attachments
    content = models.JSONField(default=list)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_documents'
    )
    
    class Meta:
        db_table = 'fhir_document_reference'
        ordering = ['-date']
        indexes = [
            models.Index(fields=['patient', '-date']),
            models.Index(fields=['type', '-date']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.get_type_display()} - {self.patient} ({self.date.strftime('%Y-%m-%d')})"
    
    def to_fhir(self):
        """Converte para formato FHIR JSON"""
        return {
            'resourceType': 'DocumentReference',
            'id': str(self.id),
            'status': self.status,
            'docStatus': self.doc_status,
            'type': {
                'coding': [{
                    'system': 'http://loinc.org' if self.type_code else 'http://terminology.hl7.org/CodeSystem/doc-typecodes',
                    'code': self.type_code or self.type,
                    'display': self.get_type_display()
                }],
                'text': self.get_type_display()
            },
            'category': [{
                'text': self.category
            }] if self.category else [],
            'subject': {
                'reference': f'Patient/{self.patient.id}',
                'display': self.patient.name
            },
            'date': self.date.isoformat(),
            'author': [{
                'reference': f'Practitioner/{self.author.id}',
                'display': self.author.name
            }] if self.author else [],
            'authenticator': {
                'reference': f'Practitioner/{self.authenticator.id}',
                'display': self.authenticator.name
            } if self.authenticator else None,
            'context': {
                'encounter': [{
                    'reference': f'Encounter/{self.encounter.id}'
                }] if self.encounter else []
            },
            'description': self.description,
            'securityLabel': [
                {'text': label} for label in self.security_label
            ] if self.security_label else [],
            'content': self.content
        }


class DocumentAttachment(models.Model):
    """
    Model para armazenar arquivos físicos dos documentos
    Separado para melhor gerenciamento de storage
    """
    
    ALLOWED_EXTENSIONS = ['pdf', 'jpg', 'jpeg', 'png', 'tiff', 'dcm', 'doc', 'docx']
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document_reference = models.ForeignKey(
        DocumentReference,
        on_delete=models.CASCADE,
        related_name='attachments'
    )
    
    # Arquivo
    file = models.FileField(
        upload_to='documents/%Y/%m/%d/',
        validators=[FileExtensionValidator(allowed_extensions=ALLOWED_EXTENSIONS)]
    )
    
    # Metadata do arquivo
    content_type = models.CharField(max_length=100)
    size = models.BigIntegerField(help_text='Tamanho em bytes')
    title = models.CharField(max_length=255, blank=True, null=True)
    creation_date = models.DateTimeField(blank=True, null=True)
    
    # Hash para integridade
    hash_sha256 = models.CharField(max_length=64, blank=True, null=True)
    
    # URL pública (se aplicável)
    url = models.URLField(max_length=500, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'fhir_document_attachment'
    
    def __str__(self):
        return f"{self.title or self.file.name}"
    
    def to_fhir_attachment(self):
        """Formato FHIR Attachment"""
        return {
            'contentType': self.content_type,
            'url': self.url or self.file.url,
            'size': self.size,
            'hash': self.hash_sha256,
            'title': self.title,
            'creation': self.creation_date.isoformat() if self.creation_date else None
        }
