"""
Media Serializers

Sprint 35: Serialização de recursos multimídia
"""

from rest_framework import serializers
from .models_media import Media
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from PIL import Image
import base64
import hashlib
import io
import os


class MediaSerializer(serializers.ModelSerializer):
    """Serializer básico para listagem"""
    
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    operator_name = serializers.CharField(source='operator_display', read_only=True)
    download_url = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Media
        fields = [
            'id', 'identifier', 'status', 'status_display',
            'type', 'type_display', 'content_type', 'content_title',
            'subject_id', 'encounter_id', 'operator_name',
            'created_datetime', 'file_size', 'width', 'height',
            'download_url', 'thumbnail_url'
        ]
    
    def get_download_url(self, obj):
        return f'/api/v1/media/{obj.id}/download/'
    
    def get_thumbnail_url(self, obj):
        if obj.thumbnail_path:
            return f'/api/v1/media/{obj.id}/thumbnail/'
        return None


class MediaDetailSerializer(serializers.ModelSerializer):
    """Serializer completo para visualização detalhada"""
    
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    download_url = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Media
        fields = '__all__'
        read_only_fields = ['id', 'identifier', 'created_datetime', 'updated_at', 'created_by',
                           'file_path', 'file_size', 'file_hash', 'thumbnail_path', 'thumbnail_size']
    
    def get_download_url(self, obj):
        return f'/api/v1/media/{obj.id}/download/'
    
    def get_thumbnail_url(self, obj):
        if obj.thumbnail_path:
            return f'/api/v1/media/{obj.id}/thumbnail/'
        return None


class MediaFHIRSerializer(serializers.ModelSerializer):
    """Serializer que retorna formato FHIR R4"""
    
    class Meta:
        model = Media
        fields = ['id']
    
    def to_representation(self, instance):
        # Não incluir data inline por padrão (muito pesado)
        include_data = self.context.get('include_data', False)
        return instance.to_fhir(include_data=include_data)


class MediaUploadSerializer(serializers.Serializer):
    """Serializer para upload de mídia"""
    
    # Required
    type = serializers.ChoiceField(choices=Media.TYPE_CHOICES)
    subject_id = serializers.CharField(max_length=100)
    content_type = serializers.CharField(max_length=100)
    
    # File data (base64 ou file upload)
    data = serializers.CharField(required=False, allow_null=True, allow_blank=True)  # Base64
    file = serializers.FileField(required=False, allow_null=True)  # File upload
    
    # Optional
    status = serializers.ChoiceField(choices=Media.STATUS_CHOICES, default='completed')
    encounter_id = serializers.CharField(max_length=100, required=False, allow_null=True, allow_blank=True)
    
    modality = serializers.JSONField(required=False, allow_null=True)
    view = serializers.JSONField(required=False, allow_null=True)
    
    operator_id = serializers.CharField(max_length=100, required=False, allow_null=True, allow_blank=True)
    operator_display = serializers.CharField(max_length=200, required=False, allow_null=True, allow_blank=True)
    
    reason_code = serializers.JSONField(required=False, allow_null=True)
    body_site = serializers.JSONField(required=False, allow_null=True)
    
    device_name = serializers.CharField(max_length=200, required=False, allow_null=True, allow_blank=True)
    content_title = serializers.CharField(max_length=200, required=False, allow_null=True, allow_blank=True)
    
    note = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    
    # Gerar thumbnail automaticamente?
    generate_thumbnail = serializers.BooleanField(default=True)
    
    def validate(self, data):
        """Validações customizadas"""
        # Deve ter data OU file
        if not data.get('data') and not data.get('file'):
            raise serializers.ValidationError("Either 'data' (base64) or 'file' is required")
        
        if data.get('data') and data.get('file'):
            raise serializers.ValidationError("Provide either 'data' or 'file', not both")
        
        # Content type validation
        content_type = data.get('content_type')
        media_type = data.get('type')
        
        if media_type == 'image' and not content_type.startswith('image/'):
            raise serializers.ValidationError("Content type must be image/* for type=image")
        elif media_type == 'video' and not content_type.startswith('video/'):
            raise serializers.ValidationError("Content type must be video/* for type=video")
        elif media_type == 'audio' and not content_type.startswith('audio/'):
            raise serializers.ValidationError("Content type must be audio/* for type=audio")
        
        return data
    
    def create(self, validated_data):
        """Cria Media e armazena arquivo"""
        # Extract file data
        data_b64 = validated_data.pop('data', None)
        file_upload = validated_data.pop('file', None)
        generate_thumbnail = validated_data.pop('generate_thumbnail', True)
        
        # Get file bytes
        if data_b64:
            file_bytes = base64.b64decode(data_b64)
        else:
            file_bytes = file_upload.read()
        
        # Set created_by from request user
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['created_by'] = request.user
        
        # Create Media instance (sem file ainda)
        media = Media.objects.create(**validated_data)
        
        # Determinar extensão do arquivo
        content_type = media.content_type
        ext_map = {
            'image/jpeg': '.jpg',
            'image/png': '.png',
            'image/gif': '.gif',
            'image/webp': '.webp',
            'video/mp4': '.mp4',
            'video/webm': '.webm',
            'audio/mpeg': '.mp3',
            'audio/wav': '.wav',
            'audio/ogg': '.ogg',
        }
        ext = ext_map.get(content_type, '')
        
        # Save file
        file_name = f"media/{media.subject_id}/{media.id}{ext}"
        file_path = default_storage.save(file_name, ContentFile(file_bytes))
        
        # Calculate hash
        file_hash = hashlib.sha256(file_bytes).hexdigest()
        
        # Update media with file info
        media.file_path = file_path
        media.file_size = len(file_bytes)
        media.file_hash = file_hash
        
        # Extract dimensions for images
        if media.type == 'image':
            try:
                image = Image.open(io.BytesIO(file_bytes))
                media.width = image.width
                media.height = image.height
                
                # Generate thumbnail
                if generate_thumbnail:
                    thumbnail = image.copy()
                    thumbnail.thumbnail((200, 200))
                    
                    thumb_io = io.BytesIO()
                    # Salvar como JPEG para reduzir tamanho
                    if image.mode in ('RGBA', 'LA', 'P'):
                        thumbnail = thumbnail.convert('RGB')
                    thumbnail.save(thumb_io, format='JPEG', quality=85)
                    thumb_bytes = thumb_io.getvalue()
                    
                    thumb_name = f"media/{media.subject_id}/thumbnails/{media.id}_thumb.jpg"
                    thumb_path = default_storage.save(thumb_name, ContentFile(thumb_bytes))
                    
                    media.thumbnail_path = thumb_path
                    media.thumbnail_size = len(thumb_bytes)
            
            except Exception as e:
                # Se falhar ao processar imagem, não é crítico
                pass
        
        media.save()
        
        return media


class MediaUpdateSerializer(serializers.Serializer):
    """Serializer para atualizar metadata de mídia (não o arquivo em si)"""
    
    status = serializers.ChoiceField(choices=Media.STATUS_CHOICES, required=False)
    content_title = serializers.CharField(max_length=200, required=False, allow_null=True, allow_blank=True)
    note = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    
    modality = serializers.JSONField(required=False, allow_null=True)
    view = serializers.JSONField(required=False, allow_null=True)
    body_site = serializers.JSONField(required=False, allow_null=True)
    reason_code = serializers.JSONField(required=False, allow_null=True)
