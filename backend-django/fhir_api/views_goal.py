"""
Goal Views

Sprint 35: Endpoints para objetivos terapêuticos
"""

import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.core.cache import cache
from django.db.models import Count, Q
from django.utils import timezone

from .models_goal import Goal, GoalTarget
from .serializers_goal import (
    GoalSerializer,
    GoalDetailSerializer,
    GoalFHIRSerializer,
    GoalCreateSerializer,
    GoalUpdateSerializer,
    GoalTargetCreateSerializer,
    GoalTargetSerializer
)
from .authentication import KeycloakAuthentication
from .permissions import CanViewPatientDocuments

logger = logging.getLogger(__name__)


class GoalViewSet(viewsets.ModelViewSet):
    """
    ViewSet para Goal
    
    Endpoints:
    - GET /api/v1/goals/ - Listar objetivos
    - POST /api/v1/goals/ - Criar objetivo
    - GET /api/v1/goals/{id}/ - Detalhes
    - PUT/PATCH /api/v1/goals/{id}/ - Atualizar
    - DELETE /api/v1/goals/{id}/ - Deletar
    - GET /api/v1/goals/patient/{patient_id}/ - Objetivos do paciente
    - POST /api/v1/goals/{id}/activate/ - Ativar objetivo
    - POST /api/v1/goals/{id}/achieve/ - Marcar como alcançado
    - POST /api/v1/goals/{id}/cancel/ - Cancelar objetivo
    - POST /api/v1/goals/{id}/add-target/ - Adicionar target
    - DELETE /api/v1/goals/{id}/targets/{target_id}/ - Remover target
    - GET /api/v1/goals/statistics/ - Estatísticas
    """
    
    queryset = Goal.objects.all()
    permission_classes = [IsAuthenticated, CanViewPatientDocuments]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    
    filterset_fields = ['lifecycle_status', 'achievement_status', 'priority', 'subject_id']
    search_fields = ['identifier', 'note', 'status_reason']
    ordering_fields = ['start_date', 'status_date', 'created_at']
    ordering = ['-start_date', '-created_at']
    
    def get_serializer_class(self):
        """Retorna serializer apropriado"""
        if self.action == 'create':
            return GoalCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return GoalUpdateSerializer
        elif self.action == 'retrieve':
            if self.request.query_params.get('format') == 'fhir':
                return GoalFHIRSerializer
            return GoalDetailSerializer
        return GoalSerializer
    
    def get_queryset(self):
        """Filtra conforme permissões"""
        queryset = super().get_queryset().prefetch_related('targets')
        user = self.request.user
        
        # Admin vê tudo
        if user.is_staff or user.is_superuser:
            return queryset
        
        # TODO: Implementar lógica de permissões específica
        
        return queryset
    
    def create(self, request, *args, **kwargs):
        """Cria novo objetivo"""
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        goal = serializer.save()
        
        logger.info(f"Goal {goal.identifier} created by {request.user}")
        
        # Retornar com serializer de detalhes
        detail_serializer = GoalDetailSerializer(goal)
        return Response(detail_serializer.data, status=status.HTTP_201_CREATED)
    
    def update(self, request, *args, **kwargs):
        """Atualiza objetivo"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        # Update fields (exceto add_targets)
        add_targets = serializer.validated_data.pop('add_targets', None)
        
        for key, value in serializer.validated_data.items():
            setattr(instance, key, value)
        
        instance.save()
        
        # Add new targets
        if add_targets:
            for target_data in add_targets:
                GoalTarget.objects.create(goal=instance, **target_data)
        
        logger.info(f"Goal {instance.identifier} updated by {request.user}")
        
        detail_serializer = GoalDetailSerializer(instance)
        return Response(detail_serializer.data)
    
    @action(detail=False, methods=['get'], url_path='patient/(?P<patient_id>[^/.]+)')
    def patient_goals(self, request, patient_id=None):
        """
        Objetivos de um paciente específico
        
        GET /api/v1/goals/patient/{patient_id}/
        Query params: ?lifecycle_status=active&achievement_status=in-progress
        """
        queryset = self.get_queryset().filter(subject_id=patient_id)
        
        # Filter by lifecycle_status
        lifecycle_status = request.query_params.get('lifecycle_status')
        if lifecycle_status:
            queryset = queryset.filter(lifecycle_status=lifecycle_status)
        
        # Filter by achievement_status
        achievement_status = request.query_params.get('achievement_status')
        if achievement_status:
            queryset = queryset.filter(achievement_status=achievement_status)
        
        # Filter active (não completed/cancelled/rejected)
        active_only = request.query_params.get('active_only')
        if active_only == 'true':
            queryset = queryset.exclude(
                lifecycle_status__in=['completed', 'cancelled', 'rejected', 'entered-in-error']
            )
        
        # Pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """
        Ativar objetivo (mover de proposed/planned para active)
        
        POST /api/v1/goals/{id}/activate/
        Body: {"note": "Paciente concordou com o objetivo"}
        """
        goal = self.get_object()
        
        if goal.lifecycle_status not in ['proposed', 'planned', 'accepted']:
            return Response(
                {'error': f'Cannot activate goal with status {goal.lifecycle_status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        goal.lifecycle_status = 'active'
        
        # Set start_date if not set
        if not goal.start_date:
            goal.start_date = timezone.now().date()
        
        # Set achievement_status
        if not goal.achievement_status:
            goal.achievement_status = 'in-progress'
        
        # Add note if provided
        note = request.data.get('note')
        if note:
            existing = goal.note or ''
            goal.note = f"{existing}\n\n[{timezone.now().strftime('%Y-%m-%d %H:%M')}] ACTIVATED: {note}"
        
        goal.save()
        
        logger.info(f"Goal {goal.identifier} activated by {request.user}")
        
        serializer = GoalDetailSerializer(goal)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def achieve(self, request, pk=None):
        """
        Marcar objetivo como alcançado
        
        POST /api/v1/goals/{id}/achieve/
        Body: {"note": "Paciente atingiu peso alvo", "achievement_status": "achieved"}
        """
        goal = self.get_object()
        
        if goal.lifecycle_status not in ['active', 'on-hold']:
            return Response(
                {'error': f'Cannot complete goal with status {goal.lifecycle_status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        goal.lifecycle_status = 'completed'
        
        # Set achievement_status from request or default to achieved
        achievement_status = request.data.get('achievement_status', 'achieved')
        if achievement_status not in ['achieved', 'not-achieved', 'sustaining']:
            return Response(
                {'error': f'Invalid achievement_status for completed goal: {achievement_status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        goal.achievement_status = achievement_status
        
        # Add note
        note = request.data.get('note', f'Objetivo marcado como {achievement_status}')
        existing = goal.note or ''
        goal.note = f"{existing}\n\n[{timezone.now().strftime('%Y-%m-%d %H:%M')}] COMPLETED: {note}"
        
        goal.save()
        
        logger.info(f"Goal {goal.identifier} achieved ({achievement_status}) by {request.user}")
        
        serializer = GoalDetailSerializer(goal)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Cancelar objetivo
        
        POST /api/v1/goals/{id}/cancel/
        Body: {"reason": "Paciente desistiu"}
        """
        goal = self.get_object()
        
        if goal.lifecycle_status in ['completed', 'entered-in-error']:
            return Response(
                {'error': f'Cannot cancel goal with status {goal.lifecycle_status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        goal.lifecycle_status = 'cancelled'
        
        # Add reason
        reason = request.data.get('reason', 'Cancelado')
        goal.status_reason = reason
        
        # Add note
        existing = goal.note or ''
        goal.note = f"{existing}\n\n[{timezone.now().strftime('%Y-%m-%d %H:%M')}] CANCELLED: {reason}"
        
        goal.save()
        
        logger.info(f"Goal {goal.identifier} cancelled by {request.user}: {reason}")
        
        serializer = GoalDetailSerializer(goal)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], url_path='add-target')
    def add_target(self, request, pk=None):
        """
        Adicionar target ao objetivo
        
        POST /api/v1/goals/{id}/add-target/
        Body: {
            "detail_quantity_value": 75,
            "detail_quantity_unit": "kg",
            "detail_quantity_comparator": "<=",
            "due_date": "2025-06-30"
        }
        """
        goal = self.get_object()
        
        serializer = GoalTargetCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        target = GoalTarget.objects.create(goal=goal, **serializer.validated_data)
        
        logger.info(f"Target added to Goal {goal.identifier} by {request.user}")
        
        target_serializer = GoalTargetSerializer(target)
        return Response(target_serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['delete'], url_path='targets/(?P<target_id>[^/.]+)')
    def remove_target(self, request, pk=None, target_id=None):
        """
        Remover target do objetivo
        
        DELETE /api/v1/goals/{id}/targets/{target_id}/
        """
        goal = self.get_object()
        
        try:
            target = goal.targets.get(id=target_id)
        except GoalTarget.DoesNotExist:
            return Response(
                {'error': 'Target not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        target.delete()
        
        logger.info(f"Target {target_id} removed from Goal {goal.identifier} by {request.user}")
        
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Estatísticas de objetivos
        
        GET /api/v1/goals/statistics/
        """
        cache_key = 'goal_statistics'
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return Response(cached_data)
        
        queryset = self.get_queryset()
        
        total = queryset.count()
        
        by_lifecycle_status = {}
        for status_choice, _ in Goal.LIFECYCLE_STATUS_CHOICES:
            by_lifecycle_status[status_choice] = queryset.filter(lifecycle_status=status_choice).count()
        
        by_achievement_status = {}
        for status_choice, _ in Goal.ACHIEVEMENT_STATUS_CHOICES:
            by_achievement_status[status_choice] = queryset.filter(achievement_status=status_choice).count()
        
        # Active goals
        active = queryset.filter(lifecycle_status='active').count()
        
        # Achieved goals
        achieved = queryset.filter(
            lifecycle_status='completed',
            achievement_status='achieved'
        ).count()
        
        # Achievement rate
        completed = by_lifecycle_status.get('completed', 0)
        achievement_rate = round((achieved / completed * 100) if completed > 0 else 0, 2)
        
        stats = {
            'total_goals': total,
            'active_goals': active,
            'achieved_goals': achieved,
            'by_lifecycle_status': by_lifecycle_status,
            'by_achievement_status': by_achievement_status,
            'achievement_rate': achievement_rate,
            'cached_at': timezone.now().isoformat()
        }
        
        cache.set(cache_key, stats, 60 * 5)  # 5 minutes
        
        return Response(stats)
