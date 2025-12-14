"""
FHIR Bundle ViewSet - Sprint 33
REST API Endpoints for Bundle Resource
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db import transaction as db_transaction
from django.utils import timezone
from django.core.cache import cache

from .models_bundle import Bundle, BundleEntry
from .serializers_bundle import (
    BundleSerializer,
    BundleFHIRSerializer,
    BundleCreateSerializer,
    BundleProcessSerializer,
    BundleEntrySerializer
)
from .permissions_document import CanCreateDocuments  # Reusar permissões
import logging

logger = logging.getLogger(__name__)


class BundleViewSet(viewsets.ModelViewSet):
    """
    ViewSet para FHIR Bundle Resource
    
    Endpoints:
    - GET /api/v1/bundles/ - Listar bundles
    - POST /api/v1/bundles/ - Criar bundle
    - GET /api/v1/bundles/{id}/ - Buscar bundle
    - DELETE /api/v1/bundles/{id}/ - Deletar bundle
    - POST /api/v1/bundles/{id}/process/ - Processar bundle transaction/batch
    - GET /api/v1/bundles/{id}/entries/ - Listar entries do bundle
    - GET /api/v1/bundles/statistics/ - Estatísticas de bundles
    """
    
    queryset = Bundle.objects.all()
    permission_classes = [IsAuthenticated, CanCreateDocuments]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    
    filterset_fields = ['type', 'status', 'created_by']
    search_fields = ['identifier', 'result_message']
    ordering_fields = ['timestamp', 'created_at', 'updated_at']
    ordering = ['-timestamp']
    
    def get_serializer_class(self):
        """Retorna serializer apropriado para cada ação"""
        if self.action == 'create':
            return BundleCreateSerializer
        elif self.action == 'retrieve' and self.request.query_params.get('format') == 'fhir':
            return BundleFHIRSerializer
        elif self.action == 'process':
            return BundleProcessSerializer
        return BundleSerializer
    
    def get_queryset(self):
        """Filtra bundles por usuário se não for admin"""
        queryset = super().get_queryset()
        
        user = self.request.user
        if not user.is_staff and not user.is_superuser:
            # Usuários normais veem apenas seus próprios bundles
            queryset = queryset.filter(created_by=user)
        
        return queryset.select_related('created_by')
    
    @db_transaction.atomic
    def create(self, request, *args, **kwargs):
        """
        Cria novo Bundle
        
        Body:
        {
            "type": "transaction",
            "entries": [
                {
                    "fullUrl": "urn:uuid:abc-123",
                    "resource": {
                        "resourceType": "Patient",
                        "name": [{"given": ["João"], "family": "Silva"}]
                    },
                    "request": {
                        "method": "POST",
                        "url": "Patient"
                    }
                }
            ]
        }
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        bundle = serializer.save()
        
        # Auto-processar se solicitado
        auto_process = request.data.get('auto_process', True)
        if auto_process and bundle.type in ['transaction', 'batch']:
            try:
                if bundle.type == 'transaction':
                    result = bundle.process_transaction()
                else:
                    result = bundle.process_batch()
                
                return Response(result, status=status.HTTP_201_CREATED)
            
            except Exception as e:
                logger.error(f"Erro ao processar bundle {bundle.id}: {str(e)}")
                return Response(
                    {
                        'error': 'Erro ao processar bundle',
                        'details': str(e),
                        'bundle_id': str(bundle.id)
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Retornar bundle criado sem processar
        return Response(
            BundleSerializer(bundle).data,
            status=status.HTTP_201_CREATED
        )
    
    def retrieve(self, request, *args, **kwargs):
        """
        Busca bundle específico
        
        Query params:
        - format=fhir : Retorna formato FHIR completo
        """
        instance = self.get_object()
        
        # Formato FHIR completo
        if request.query_params.get('format') == 'fhir':
            return Response(instance.to_fhir())
        
        # Formato padrão
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def process(self, request, pk=None):
        """
        Processa bundle transaction ou batch
        
        POST /api/v1/bundles/{id}/process/
        
        Body (opcional):
        {
            "auto_process": true
        }
        """
        bundle = self.get_object()
        
        serializer = BundleProcessSerializer(instance=bundle, data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            if bundle.type == 'transaction':
                logger.info(f"Processing transaction bundle {bundle.id}")
                result = bundle.process_transaction()
            elif bundle.type == 'batch':
                logger.info(f"Processing batch bundle {bundle.id}")
                result = bundle.process_batch()
            else:
                return Response(
                    {'error': f'Bundle type {bundle.type} não pode ser processado'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            return Response(result, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.error(f"Erro ao processar bundle {bundle.id}: {str(e)}")
            return Response(
                {
                    'error': 'Erro ao processar bundle',
                    'details': str(e),
                    'bundle_status': bundle.status
                },
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['get'])
    def entries(self, request, pk=None):
        """
        Lista todas as entries de um bundle
        
        GET /api/v1/bundles/{id}/entries/
        """
        bundle = self.get_object()
        entries = BundleEntry.objects.filter(bundle=bundle)
        serializer = BundleEntrySerializer(entries, many=True)
        
        return Response({
            'bundle_id': str(bundle.id),
            'type': bundle.type,
            'status': bundle.status,
            'entry_count': entries.count(),
            'entries': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Estatísticas de bundles
        
        GET /api/v1/bundles/statistics/
        
        Cache: 5 minutos
        """
        cache_key = 'bundle_statistics'
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return Response(cached_data)
        
        # Calcular estatísticas
        total_bundles = Bundle.objects.count()
        
        by_type = {}
        for bundle_type, _ in Bundle.BUNDLE_TYPE_CHOICES:
            by_type[bundle_type] = Bundle.objects.filter(type=bundle_type).count()
        
        by_status = {}
        for bundle_status in ['pending', 'processing', 'completed', 'failed']:
            by_status[bundle_status] = Bundle.objects.filter(status=bundle_status).count()
        
        # Total de entries processadas
        total_entries = BundleEntry.objects.count()
        processed_entries = BundleEntry.objects.filter(processed=True).count()
        failed_entries = BundleEntry.objects.filter(error_message__isnull=False).count()
        
        # Bundles recentes (últimas 24h)
        last_24h = timezone.now() - timezone.timedelta(hours=24)
        recent_bundles = Bundle.objects.filter(created_at__gte=last_24h).count()
        
        stats = {
            'total_bundles': total_bundles,
            'by_type': by_type,
            'by_status': by_status,
            'total_entries': total_entries,
            'processed_entries': processed_entries,
            'failed_entries': failed_entries,
            'recent_bundles_24h': recent_bundles,
            'success_rate': round((by_status['completed'] / total_bundles * 100), 2) if total_bundles > 0 else 0,
            'cached_at': timezone.now().isoformat()
        }
        
        # Cache por 5 minutos
        cache.set(cache_key, stats, 60 * 5)
        
        return Response(stats)
    
    @action(detail=True, methods=['post'])
    def retry(self, request, pk=None):
        """
        Reprocessa bundle que falhou
        
        POST /api/v1/bundles/{id}/retry/
        """
        bundle = self.get_object()
        
        if bundle.status != 'failed':
            return Response(
                {'error': 'Apenas bundles com status "failed" podem ser reprocessados'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Resetar status
        bundle.status = 'pending'
        bundle.result_message = None
        bundle.failed_entries = []
        bundle.save()
        
        # Reprocessar
        try:
            if bundle.type == 'transaction':
                result = bundle.process_transaction()
            else:
                result = bundle.process_batch()
            
            return Response(result, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
