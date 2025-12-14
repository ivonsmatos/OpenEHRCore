"""
FHIR DocumentReference - Serializers

Sprint 33: Document Management
"""

from rest_framework import serializers
from .models_document import DocumentReference, DocumentAttachment
import hashlib
import base64


class DocumentAttachmentSerializer(serializers.ModelSerializer):
    """Serializer para anexos de documentos"""
    
    class Meta:
        model = DocumentAttachment
        fields = ['id', 'file', 'content_type', 'size', 'title', 'url', 'hash_sha256', 'created_at']
        read_only_fields = ['id', 'size', 'hash_sha256', 'created_at']
    
    def create(self, validated_data):
        file_obj = validated_data.get('file')
        
        # Calcula hash SHA-256
        file_content = file_obj.read()
        hash_sha256 = hashlib.sha256(file_content).hexdigest()
        file_obj.seek(0)  # Reset file pointer
        
        validated_data['size'] = file_obj.size
        validated_data['hash_sha256'] = hash_sha256
        
        if not validated_data.get('content_type'):
            validated_data['content_type'] = file_obj.content_type
        
        return super().create(validated_data)


class DocumentReferenceSerializer(serializers.ModelSerializer):
    """Serializer para DocumentReference"""
    
    attachments = DocumentAttachmentSerializer(many=True, read_only=True)
    patient_name = serializers.CharField(source='patient.name', read_only=True)
    author_name = serializers.CharField(source='author.name', read_only=True, allow_null=True)
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    
    class Meta:
        model = DocumentReference
        fields = [
            'id', 'status', 'doc_status', 'type', 'type_code', 'type_display',
            'category', 'patient', 'patient_name', 'date', 'author', 'author_name',
            'authenticator', 'encounter', 'description', 'security_label',
            'content', 'attachments', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'date', 'created_at', 'updated_at']
    
    def validate_security_label(self, value):
        """Valida security labels"""
        allowed_labels = ['N', 'R', 'V', 'U']  # Normal, Restricted, Very Restricted, Unrestricted
        for label in value:
            if label not in allowed_labels:
                raise serializers.ValidationError(
                    f"Invalid security label: {label}. Allowed: {', '.join(allowed_labels)}"
                )
        return value


class DocumentReferenceFHIRSerializer(serializers.Serializer):
    """
    Serializer para formato FHIR completo
    """
    resourceType = serializers.CharField(default='DocumentReference', read_only=True)
    id = serializers.UUIDField(read_only=True)
    status = serializers.ChoiceField(choices=DocumentReference.STATUS_CHOICES)
    docStatus = serializers.CharField(required=False, allow_null=True)
    type = serializers.DictField()
    category = serializers.ListField(required=False)
    subject = serializers.DictField()
    date = serializers.DateTimeField(read_only=True)
    author = serializers.ListField(required=False)
    authenticator = serializers.DictField(required=False, allow_null=True)
    context = serializers.DictField(required=False)
    description = serializers.CharField(required=False, allow_blank=True)
    securityLabel = serializers.ListField(required=False)
    content = serializers.ListField()
    
    def to_representation(self, instance):
        """Converte model para FHIR JSON"""
        return instance.to_fhir()
    
    def create(self, validated_data):
        """Cria DocumentReference a partir de payload FHIR"""
        # Extrai patient reference
        subject = validated_data.get('subject', {})
        patient_id = subject.get('reference', '').replace('Patient/', '')
        
        # Extrai author
        authors = validated_data.get('author', [])
        author_id = None
        if authors:
            author_ref = authors[0].get('reference', '')
            author_id = author_ref.replace('Practitioner/', '') if author_ref else None
        
        # Extrai tipo
        type_data = validated_data.get('type', {})
        type_coding = type_data.get('coding', [{}])[0]
        type_code = type_coding.get('code')
        
        # Cria o documento
        document = DocumentReference.objects.create(
            status=validated_data.get('status', 'current'),
            doc_status=validated_data.get('docStatus'),
            type=type_code,
            type_code=type_code,
            patient_id=patient_id,
            author_id=author_id,
            description=validated_data.get('description', ''),
            content=validated_data.get('content', [])
        )
        
        return document


class DocumentUploadSerializer(serializers.Serializer):
    """
    Serializer para upload simplificado de documentos
    """
    patient_id = serializers.UUIDField()
    type = serializers.ChoiceField(choices=DocumentReference.TYPE_CHOICES)
    file = serializers.FileField()
    title = serializers.CharField(max_length=255, required=False)
    description = serializers.CharField(required=False, allow_blank=True)
    encounter_id = serializers.UUIDField(required=False, allow_null=True)
    security_label = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=['N']
    )
    
    def validate_file(self, value):
        """Valida tamanho e tipo do arquivo"""
        # Máximo 50MB
        max_size = 50 * 1024 * 1024
        if value.size > max_size:
            raise serializers.ValidationError(
                f"Arquivo muito grande. Máximo permitido: 50MB"
            )
        
        # Valida extensão
        allowed_extensions = DocumentAttachment.ALLOWED_EXTENSIONS
        file_extension = value.name.split('.')[-1].lower()
        if file_extension not in allowed_extensions:
            raise serializers.ValidationError(
                f"Tipo de arquivo não permitido. Permitidos: {', '.join(allowed_extensions)}"
            )
        
        return value
    
    def create(self, validated_data):
        """Cria DocumentReference + Attachment"""
        file_obj = validated_data.pop('file')
        title = validated_data.pop('title', file_obj.name)
        
        # Cria DocumentReference
        document = DocumentReference.objects.create(**validated_data)
        
        # Cria Attachment
        attachment = DocumentAttachment.objects.create(
            document_reference=document,
            file=file_obj,
            title=title,
            content_type=file_obj.content_type
        )
        
        # Atualiza content field com attachment info
        document.content = [{
            'attachment': attachment.to_fhir_attachment()
        }]
        document.save()
        
        return document
