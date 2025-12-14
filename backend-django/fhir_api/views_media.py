"""
Media Views

Sprint 35: Endpoints para recursos multimídia
"""

import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.core.cache import cache
from django.http import HttpResponse, FileResponse
from django.db.models import Count, Q, Sum
from django.utils import timezone

from .models_media import Media
from .serializers_media import (
    MediaSerializer,
    MediaDetailSerializer,
    MediaFHIRSerializer,
    MediaUploadSerializer,
    MediaUpdateSerializer
)
from .authentication import KeycloakAuthentication
from .permissions import CanViewPatientDocuments

logger = logging.getLogger(__name__)


class MediaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para Media
    
    Endpoints:
    - GET /api/v1/media/ - Listar mídias
    - POST /api/v1/media/ - Upload de mídia
    - GET /api/v1/media/{id}/ - Detalhes
    - PUT/PATCH /api/v1/media/{id}/ - Atualizar metadata
    - DELETE /api/v1/media/{id}/ - Deletar (remove arquivo)
    - GET /api/v1/media/patient/{patient_id}/ - Mídias do paciente
    - GET /api/v1/media/{id}/download/ - Download do arquivo
    - GET /api/v1/media/{id}/thumbnail/ - Download do thumbnail
    - GET /api/v1/media/{id}/preview/ - Preview inline (imagens)
    - GET /api/v1/media/statistics/ - Estatísticas
    """
    
    queryset = Media.objects.all()
    permission_classes = [IsAuthenticated, CanViewPatientDocuments]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    
    filterset_fields = ['status', 'type', 'subject_id', 'encounter_id', 'content_type']
    search_fields = ['identifier', 'content_title', 'note']
    ordering_fields = ['created_datetime', 'file_size']
    ordering = ['-created_datetime']
    
    def get_serializer_class(self):
        """Retorna serializer apropriado"""
        if self.action == 'create':
            return MediaUploadSerializer
        elif self.action in ['update', 'partial_update']:
            return MediaUpdateSerializer
        elif self.action == 'retrieve':
            if self.request.query_params.get('format') == 'fhir':
                return MediaFHIRSerializer
            return MediaDetailSerializer
        return MediaSerializer
    
    def get_queryset(self):
        """Filtra conforme permissões"""
        queryset = super().get_queryset()
        user = self.request.user
        
        # Admin vê tudo
        if user.is_staff or user.is_superuser:
            return queryset
        
        # TODO: Implementar lógica de permissões específica
        
        return queryset
    
    def create(self, request, *args, **kwargs):
        """Upload de mídia"""
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        media = serializer.save()
        
        logger.info(f"Media {media.identifier} uploaded by {request.user} ({media.file_size} bytes)")
        
        # Retornar com serializer de detalhes
        detail_serializer = MediaDetailSerializer(media)
        return Response(detail_serializer.data, status=status.HTTP_201_CREATED)
    
    def update(self, request, *args, **kwargs):
        """Atualiza metadata (não o arquivo)"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        # Update fields
        for key, value in serializer.validated_data.items():
            setattr(instance, key, value)
        
        instance.save()
        
        logger.info(f"Media {instance.identifier} metadata updated by {request.user}")
        
        detail_serializer = MediaDetailSerializer(instance)
        return Response(detail_serializer.data)
    
    def destroy(self, request, *args, **kwargs):
        """Deleta mídia e arquivo"""
        instance = self.get_object()
        identifier = instance.identifier
        
        # Delete irá remover os arquivos também (override no model)
        instance.delete()
        
        logger.info(f"Media {identifier} deleted by {request.user}")
        
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=['get'], url_path='patient/(?P<patient_id>[^/.]+)')
    def patient_media(self, request, patient_id=None):
        """
        Mídias de um paciente específico
        
        GET /api/v1/media/patient/{patient_id}/
        Query params: ?type=image&days=30
        """
        queryset = self.get_queryset().filter(subject_id=patient_id)
        
        # Filter by type
        type_filter = request.query_params.get('type')
        if type_filter:
            queryset = queryset.filter(type=type_filter)
        
        # Filter by days
        days = request.query_params.get('days')
        if days:
            from datetime import timedelta
            cutoff = timezone.now() - timedelta(days=int(days))
            queryset = queryset.filter(created_datetime__gte=cutoff)
        
        # Pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """
        Download do arquivo original
        
        GET /api/v1/media/{id}/download/
        """
        media = self.get_object()
        
        file_data = media.get_file_data()
        
        if not file_data:
            return Response(
                {'error': 'File not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Determinar filename
        filename = media.content_title or media.identifier
        # Adicionar extensão se não tiver
        if '.' not in filename:
            ext_map = {
                'image/jpeg': '.jpg',
                'image/png': '.png',
                'video/mp4': '.mp4',
                'audio/mp3': '.mp3',
            }
            ext = ext_map.get(media.content_type, '')
            filename = f"{filename}{ext}"
        
        response = HttpResponse(file_data, content_type=media.content_type)
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        response['Content-Length'] = len(file_data)
        
        logger.info(f"Media {media.identifier} downloaded by {request.user}")
        
        return response
    
    @action(detail=True, methods=['get'])
    def thumbnail(self, request, pk=None):
        """
        Download do thumbnail
        
        GET /api/v1/media/{id}/thumbnail/
        """
        media = self.get_object()
        
        thumb_data = media.get_thumbnail_data()
        
        if not thumb_data:
            return Response(
                {'error': 'Thumbnail not available'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        response = HttpResponse(thumb_data, content_type='image/jpeg')
        response['Content-Length'] = len(thumb_data)
        
        return response
    
    @action(detail=True, methods=['get'])
    def preview(self, request, pk=None):
        """
        Preview inline (para imagens)
        
        GET /api/v1/media/{id}/preview/
        """
        media = self.get_object()
        
        # Apenas para imagens
        if media.type != 'image':
            return Response(
                {'error': 'Preview only available for images'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        file_data = media.get_file_data()
        
        if not file_data:
            return Response(
                {'error': 'File not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        response = HttpResponse(file_data, content_type=media.content_type)
        response['Content-Disposition'] = 'inline'
        response['Content-Length'] = len(file_data)
        
        return response
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Estatísticas de mídias
        
        GET /api/v1/media/statistics/
        """
        cache_key = 'media_statistics'
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return Response(cached_data)
        
        queryset = self.get_queryset()
        
        total = queryset.count()
        
        by_type = {}
        for type_choice, _ in Media.TYPE_CHOICES:
            by_type[type_choice] = queryset.filter(type=type_choice).count()
        
        by_status = {}
        for status_choice, _ in Media.STATUS_CHOICES:
            by_status[status_choice] = queryset.filter(status=status_choice).count()
        
        # Total storage used
        total_size = queryset.aggregate(total=Sum('file_size'))['total'] or 0
        total_size_mb = round(total_size / (1024 * 1024), 2)
        
        # Average file size
        avg_size = round(total_size / total if total > 0 else 0, 2)
        avg_size_kb = round(avg_size / 1024, 2)
        
        # Images with thumbnails
        with_thumbnails = queryset.filter(thumbnail_path__isnull=False).count()
        
        # Recent uploads (last 7 days)
        from datetime import timedelta
        week_ago = timezone.now() - timedelta(days=7)
        recent_uploads = queryset.filter(created_datetime__gte=week_ago).count()
        
        stats = {
            'total_media': total,
            'by_type': by_type,
            'by_status': by_status,
            'total_storage_mb': total_size_mb,
            'average_file_size_kb': avg_size_kb,
            'media_with_thumbnails': with_thumbnails,
            'recent_uploads_7d': recent_uploads,
            'cached_at': timezone.now().isoformat()
        }
        
        cache.set(cache_key, stats, 60 * 5)  # 5 minutes
        
        return Response(stats)
