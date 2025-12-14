"""
FHIR DocumentReference - Views

Sprint 33: Document Management
Endpoints seguros para gerenciamento de documentos médicos
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.http import FileResponse, Http404
from django.db import transaction
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django_filters.rest_framework import DjangoFilterBackend

from .models_document import DocumentReference, DocumentAttachment
from .serializers_document import (
    DocumentReferenceSerializer,
    DocumentReferenceFHIRSerializer,
    DocumentUploadSerializer,
    DocumentAttachmentSerializer
)
from .permissions import CanViewPatientDocuments, CanCreateDocuments
from .audit_logging import log_document_access, log_document_upload
import logging

logger = logging.getLogger(__name__)


class DocumentReferenceViewSet(viewsets.ModelViewSet):
    """
    ViewSet para DocumentReference (FHIR R4)
    
    Endpoints:
    - GET /api/v1/documents/ - Lista documentos
    - POST /api/v1/documents/ - Cria documento (FHIR)
    - GET /api/v1/documents/{id}/ - Busca documento
    - PUT /api/v1/documents/{id}/ - Atualiza documento
    - DELETE /api/v1/documents/{id}/ - Remove documento
    
    - POST /api/v1/documents/upload/ - Upload simplificado
    - GET /api/v1/documents/{id}/download/ - Download de arquivo
    - GET /api/v1/documents/patient/{patient_id}/ - Docs do paciente
    """
    
    queryset = DocumentReference.objects.select_related(
        'patient', 'author', 'authenticator', 'encounter'
    ).prefetch_related('attachments')
    
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'type', 'patient', 'author', 'encounter']
    search_fields = ['description', 'patient__name', 'type']
    ordering_fields = ['date', 'created_at', 'type']
    ordering = ['-date']
    
    def get_serializer_class(self):
        """Retorna serializer baseado na action"""
        if self.action == 'upload':
            return DocumentUploadSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            # Se payload é FHIR completo
            if self.request.data.get('resourceType') == 'DocumentReference':
                return DocumentReferenceFHIRSerializer
        return DocumentReferenceSerializer
    
    def get_permissions(self):
        """Permissões baseadas na action"""
        if self.action in ['list', 'retrieve', 'download', 'by_patient']:
            permission_classes = [IsAuthenticated, CanViewPatientDocuments]
        elif self.action in ['create', 'upload']:
            permission_classes = [IsAuthenticated, CanCreateDocuments]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def perform_create(self, serializer):
        """Adiciona user na criação"""
        serializer.save(created_by=self.request.user)
        log_document_upload(self.request.user, serializer.instance)
    
    def retrieve(self, request, *args, **kwargs):
        """
        Busca documento e registra acesso no audit log
        """
        instance = self.get_object()
        log_document_access(request.user, instance, action='view')
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'], url_path='upload')
    def upload(self, request):
        """
        Upload simplificado de documento
        
        POST /api/v1/documents/upload/
        
        Form Data:
        - patient_id: UUID
        - type: lab-report, imaging-report, etc
        - file: arquivo (PDF, imagem)
        - title: título opcional
        - description: descrição opcional
        """
        serializer = DocumentUploadSerializer(data=request.data)
        
        if serializer.is_valid():
            with transaction.atomic():
                document = serializer.save(created_by=request.user)
                log_document_upload(request.user, document)
                
                # Retorna com attachments incluídos
                output_serializer = DocumentReferenceSerializer(document)
                return Response(
                    output_serializer.data,
                    status=status.HTTP_201_CREATED
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'], url_path='download')
    def download(self, request, pk=None):
        """
        Download de arquivo do documento
        
        GET /api/v1/documents/{id}/download/?attachment_id={uuid}
        
        Query Params:
        - attachment_id: ID do attachment (opcional, pega o primeiro se omitido)
        """
        document = self.get_object()
        attachment_id = request.query_params.get('attachment_id')
        
        try:
            if attachment_id:
                attachment = document.attachments.get(id=attachment_id)
            else:
                attachment = document.attachments.first()
            
            if not attachment:
                return Response(
                    {'error': 'Nenhum arquivo encontrado'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Log de acesso
            log_document_access(request.user, document, action='download')
            
            # Retorna arquivo
            file_handle = attachment.file.open()
            response = FileResponse(
                file_handle,
                content_type=attachment.content_type
            )
            response['Content-Disposition'] = f'attachment; filename="{attachment.title or attachment.file.name}"'
            response['Content-Length'] = attachment.size
            
            return response
            
        except DocumentAttachment.DoesNotExist:
            return Response(
                {'error': 'Arquivo não encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['get'], url_path='patient/(?P<patient_id>[^/.]+)')
    def by_patient(self, request, patient_id=None):
        """
        Lista todos os documentos de um paciente
        
        GET /api/v1/documents/patient/{patient_id}/
        
        Query Params:
        - type: filtrar por tipo
        - status: filtrar por status
        """
        queryset = self.get_queryset().filter(patient_id=patient_id)
        
        # Filtros opcionais
        doc_type = request.query_params.get('type')
        if doc_type:
            queryset = queryset.filter(type=doc_type)
        
        doc_status = request.query_params.get('status')
        if doc_status:
            queryset = queryset.filter(status=doc_status)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], url_path='supersede')
    def supersede(self, request, pk=None):
        """
        Marca documento como superseded e cria nova versão
        
        POST /api/v1/documents/{id}/supersede/
        Body: novo documento FHIR ou upload
        """
        old_document = self.get_object()
        
        # Marca como superseded
        old_document.status = 'superseded'
        old_document.save()
        
        # Cria novo documento
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            new_document = serializer.save(
                created_by=request.user,
                patient=old_document.patient
            )
            
            log_document_upload(
                request.user,
                new_document,
                notes=f"Supersedes document {old_document.id}"
            )
            
            return Response(
                DocumentReferenceSerializer(new_document).data,
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'], url_path='statistics')
    @method_decorator(cache_page(60 * 5))  # Cache 5 minutos
    def statistics(self, request):
        """
        Estatísticas de documentos
        
        GET /api/v1/documents/statistics/
        """
        from django.db.models import Count
        
        stats = {
            'total_documents': self.get_queryset().count(),
            'by_type': dict(
                self.get_queryset().values('type').annotate(
                    count=Count('id')
                ).values_list('type', 'count')
            ),
            'by_status': dict(
                self.get_queryset().values('status').annotate(
                    count=Count('id')
                ).values_list('status', 'count')
            ),
            'recent_uploads': self.get_queryset().order_by('-created_at')[:10].values(
                'id', 'type', 'patient__name', 'created_at'
            )
        }
        
        return Response(stats)


class DocumentAttachmentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet somente leitura para attachments
    Upload é feito via DocumentReference
    """
    queryset = DocumentAttachment.objects.all()
    serializer_class = DocumentAttachmentSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=True, methods=['get'], url_path='download')
    def download(self, request, pk=None):
        """Download direto do attachment"""
        attachment = self.get_object()
        
        file_handle = attachment.file.open()
        response = FileResponse(file_handle, content_type=attachment.content_type)
        response['Content-Disposition'] = f'attachment; filename="{attachment.title or attachment.file.name}"'
        
        return response
