"""
MedicationAdministration Views

Sprint 34: Endpoints para registro de administração de medicamentos
"""

import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.core.cache import cache
from django.db.models import Count, Q
from django.utils import timezone

from .models_medication_administration import MedicationAdministration
from .serializers_medication_administration import (
    MedicationAdministrationSerializer,
    MedicationAdministrationDetailSerializer,
    MedicationAdministrationFHIRSerializer,
    MedicationAdministrationCreateSerializer,
    MedicationAdministrationUpdateSerializer
)
from .authentication import KeycloakAuthentication
from .permissions import CanViewPatientDocuments

logger = logging.getLogger(__name__)


class MedicationAdministrationViewSet(viewsets.ModelViewSet):
    """
    ViewSet para MedicationAdministration
    
    Endpoints:
    - GET /api/v1/medication-administrations/ - Listar administrações
    - POST /api/v1/medication-administrations/ - Registrar administração
    - GET /api/v1/medication-administrations/{id}/ - Detalhes
    - PUT/PATCH /api/v1/medication-administrations/{id}/ - Atualizar
    - DELETE /api/v1/medication-administrations/{id}/ - Deletar
    - GET /api/v1/medication-administrations/patient/{patient_id}/ - Administrações do paciente
    - POST /api/v1/medication-administrations/{id}/complete/ - Marcar como completado
    - POST /api/v1/medication-administrations/{id}/stop/ - Parar administração
    - GET /api/v1/medication-administrations/statistics/ - Estatísticas
    """
    
    queryset = MedicationAdministration.objects.all()
    permission_classes = [IsAuthenticated, CanViewPatientDocuments]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    
    filterset_fields = ['status', 'patient_id', 'encounter_id', 'medication_request', 'performer_actor_id']
    search_fields = ['identifier', 'patient_id', 'dosage_text', 'note']
    ordering_fields = ['effective_datetime', 'created_at', 'status']
    ordering = ['-effective_datetime', '-created_at']
    
    def get_serializer_class(self):
        """Retorna serializer apropriado"""
        if self.action == 'create':
            return MedicationAdministrationCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return MedicationAdministrationUpdateSerializer
        elif self.action == 'retrieve':
            if self.request.query_params.get('format') == 'fhir':
                return MedicationAdministrationFHIRSerializer
            return MedicationAdministrationDetailSerializer
        return MedicationAdministrationSerializer
    
    def get_queryset(self):
        """Filtra conforme permissões"""
        queryset = super().get_queryset()
        user = self.request.user
        
        # Admin vê tudo
        if user.is_staff or user.is_superuser:
            return queryset
        
        # Practitioner vê administrações que fez + pacientes sob seus cuidados
        # Patient vê apenas suas próprias
        # TODO: Implementar lógica de permissões específica
        
        return queryset
    
    def create(self, request, *args, **kwargs):
        """Registra nova administração de medicamento"""
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        administration = serializer.save()
        
        logger.info(f"MedicationAdministration {administration.identifier} created by {request.user}")
        
        # Retornar com serializer de detalhes
        detail_serializer = MedicationAdministrationDetailSerializer(administration)
        return Response(detail_serializer.data, status=status.HTTP_201_CREATED)
    
    def update(self, request, *args, **kwargs):
        """Atualiza administração"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        # Update fields
        for key, value in serializer.validated_data.items():
            setattr(instance, key, value)
        
        instance.save()
        
        logger.info(f"MedicationAdministration {instance.identifier} updated by {request.user}")
        
        detail_serializer = MedicationAdministrationDetailSerializer(instance)
        return Response(detail_serializer.data)
    
    @action(detail=False, methods=['get'], url_path='patient/(?P<patient_id>[^/.]+)')
    def patient_administrations(self, request, patient_id=None):
        """
        Administrações de um paciente específico
        
        GET /api/v1/medication-administrations/patient/{patient_id}/
        Query params: ?status=completed&days=7
        """
        queryset = self.get_queryset().filter(patient_id=patient_id)
        
        # Filter by status
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by days
        days = request.query_params.get('days')
        if days:
            from datetime import timedelta
            cutoff = timezone.now() - timedelta(days=int(days))
            queryset = queryset.filter(effective_datetime__gte=cutoff)
        
        # Pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """
        Marca administração como completada
        
        POST /api/v1/medication-administrations/{id}/complete/
        Body: {"note": "Paciente tolerou bem"}
        """
        administration = self.get_object()
        
        if administration.status == 'completed':
            return Response(
                {'error': 'Administration is already completed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        administration.status = 'completed'
        
        # Set end time if it was a period
        if administration.effective_period_start and not administration.effective_period_end:
            administration.effective_period_end = timezone.now()
        
        # Add note if provided
        note = request.data.get('note')
        if note:
            existing = administration.note or ''
            administration.note = f"{existing}\n\n[{timezone.now().strftime('%Y-%m-%d %H:%M')}] {note}"
        
        administration.save()
        
        logger.info(f"MedicationAdministration {administration.identifier} completed by {request.user}")
        
        serializer = MedicationAdministrationDetailSerializer(administration)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def stop(self, request, pk=None):
        """
        Para uma administração em progresso
        
        POST /api/v1/medication-administrations/{id}/stop/
        Body: {"reason": "Reação adversa"}
        """
        administration = self.get_object()
        
        if administration.status not in ['in-progress', 'on-hold']:
            return Response(
                {'error': f'Cannot stop administration with status {administration.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        administration.status = 'stopped'
        
        # Set end time
        if administration.effective_period_start and not administration.effective_period_end:
            administration.effective_period_end = timezone.now()
        
        # Add reason
        reason = request.data.get('reason')
        if reason:
            administration.status_reason = [{
                'text': reason
            }]
            
            # Also add to notes
            administration.note = f"{administration.note or ''}\n\n[{timezone.now().strftime('%Y-%m-%d %H:%M')}] STOPPED: {reason}"
        
        administration.save()
        
        logger.warning(f"MedicationAdministration {administration.identifier} stopped by {request.user}: {reason}")
        
        serializer = MedicationAdministrationDetailSerializer(administration)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Estatísticas de administrações
        
        GET /api/v1/medication-administrations/statistics/
        """
        cache_key = 'medication_administration_statistics'
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return Response(cached_data)
        
        queryset = self.get_queryset()
        
        total = queryset.count()
        
        by_status = {}
        for status_choice, _ in MedicationAdministration.STATUS_CHOICES:
            by_status[status_choice] = queryset.filter(status=status_choice).count()
        
        # Today's administrations
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_count = queryset.filter(effective_datetime__gte=today_start).count()
        
        # Completed today
        completed_today = queryset.filter(
            status='completed',
            effective_datetime__gte=today_start
        ).count()
        
        # Not-done count
        not_done = queryset.filter(status='not-done').count()
        
        stats = {
            'total_administrations': total,
            'by_status': by_status,
            'today_administrations': today_count,
            'completed_today': completed_today,
            'not_done_count': not_done,
            'completion_rate': round((by_status.get('completed', 0) / total * 100) if total > 0 else 0, 2),
            'cached_at': timezone.now().isoformat()
        }
        
        cache.set(cache_key, stats, 60 * 5)  # 5 minutes
        
        return Response(stats)
