"""
Task Views

Sprint 34: Endpoints para gerenciamento genérico de workflow
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

from .models_task import Task
from .serializers_task import (
    TaskSerializer,
    TaskDetailSerializer,
    TaskFHIRSerializer,
    TaskCreateSerializer,
    TaskUpdateSerializer,
    TaskTransitionSerializer
)
from .authentication import KeycloakAuthentication
from .permissions import CanViewPatientDocuments

logger = logging.getLogger(__name__)


class TaskViewSet(viewsets.ModelViewSet):
    """
    ViewSet para Task genérico
    
    Endpoints:
    - GET /api/v1/tasks/ - Listar tarefas
    - POST /api/v1/tasks/ - Criar tarefa
    - GET /api/v1/tasks/{id}/ - Detalhes
    - PUT/PATCH /api/v1/tasks/{id}/ - Atualizar
    - DELETE /api/v1/tasks/{id}/ - Deletar
    - GET /api/v1/tasks/my-tasks/ - Tarefas do usuário atual
    - GET /api/v1/tasks/patient/{patient_id}/ - Tarefas do paciente
    - POST /api/v1/tasks/{id}/accept/ - Aceitar tarefa
    - POST /api/v1/tasks/{id}/start/ - Iniciar tarefa
    - POST /api/v1/tasks/{id}/complete/ - Completar tarefa
    - POST /api/v1/tasks/{id}/reject/ - Rejeitar tarefa
    - POST /api/v1/tasks/{id}/cancel/ - Cancelar tarefa
    - POST /api/v1/tasks/{id}/assign/ - Atribuir tarefa
    - GET /api/v1/tasks/statistics/ - Estatísticas
    """
    
    queryset = Task.objects.all()
    permission_classes = [IsAuthenticated, CanViewPatientDocuments]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    
    filterset_fields = ['status', 'priority', 'intent', 'owner_id', 'requester_id', 'for_patient_id', 'focus']
    search_fields = ['identifier', 'description', 'note']
    ordering_fields = ['authored_on', 'last_modified', 'priority', 'status']
    ordering = ['-priority', '-authored_on']
    
    def get_serializer_class(self):
        """Retorna serializer apropriado"""
        if self.action == 'create':
            return TaskCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return TaskUpdateSerializer
        elif self.action == 'retrieve':
            if self.request.query_params.get('format') == 'fhir':
                return TaskFHIRSerializer
            return TaskDetailSerializer
        return TaskSerializer
    
    def get_queryset(self):
        """Filtra conforme permissões"""
        queryset = super().get_queryset()
        user = self.request.user
        
        # Admin vê tudo
        if user.is_staff or user.is_superuser:
            return queryset
        
        # Outros usuários veem apenas tarefas relevantes
        # TODO: Implementar lógica de permissões específica
        
        return queryset
    
    def create(self, request, *args, **kwargs):
        """Cria nova tarefa"""
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        task = serializer.save()
        
        logger.info(f"Task {task.identifier} created by {request.user}")
        
        # Retornar com serializer de detalhes
        detail_serializer = TaskDetailSerializer(task)
        return Response(detail_serializer.data, status=status.HTTP_201_CREATED)
    
    def update(self, request, *args, **kwargs):
        """Atualiza tarefa"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        # Update fields
        for key, value in serializer.validated_data.items():
            setattr(instance, key, value)
        
        instance.save()
        
        logger.info(f"Task {instance.identifier} updated by {request.user}")
        
        detail_serializer = TaskDetailSerializer(instance)
        return Response(detail_serializer.data)
    
    @action(detail=False, methods=['get'], url_path='my-tasks')
    def my_tasks(self, request):
        """
        Tarefas do usuário atual (como owner)
        
        GET /api/v1/tasks/my-tasks/
        Query params: ?status=requested&priority=urgent
        """
        # Tentar encontrar Practitioner para o user
        # TODO: Implementar mapeamento User -> Practitioner
        practitioner_id = f"Practitioner/{request.user.id}"
        
        queryset = self.get_queryset().filter(owner_id=practitioner_id)
        
        # Filter by status
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by priority
        priority_filter = request.query_params.get('priority')
        if priority_filter:
            queryset = queryset.filter(priority=priority_filter)
        
        # Pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='patient/(?P<patient_id>[^/.]+)')
    def patient_tasks(self, request, patient_id=None):
        """
        Tarefas de um paciente específico
        
        GET /api/v1/tasks/patient/{patient_id}/
        Query params: ?status=in-progress
        """
        queryset = self.get_queryset().filter(for_patient_id=patient_id)
        
        # Filter by status
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        """
        Aceitar tarefa
        
        POST /api/v1/tasks/{id}/accept/
        Body: {"note": "Aceitando a solicitação"}
        """
        task = self.get_object()
        
        if task.status not in ['requested', 'received']:
            return Response(
                {'error': f'Cannot accept task with status {task.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        task.status = 'accepted'
        
        # Set owner if not set
        if not task.owner_id:
            # TODO: Get practitioner ID from user
            task.owner_id = f"Practitioner/{request.user.id}"
            task.owner_display = request.user.get_full_name() or request.user.username
        
        # Add note if provided
        note = request.data.get('note')
        if note:
            existing = task.note or ''
            task.note = f"{existing}\n\n[{timezone.now().strftime('%Y-%m-%d %H:%M')}] ACCEPTED: {note}"
        
        task.save()
        
        logger.info(f"Task {task.identifier} accepted by {request.user}")
        
        serializer = TaskDetailSerializer(task)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """
        Iniciar tarefa
        
        POST /api/v1/tasks/{id}/start/
        """
        task = self.get_object()
        
        if task.status not in ['accepted', 'ready', 'on-hold']:
            return Response(
                {'error': f'Cannot start task with status {task.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        task.status = 'in-progress'
        
        # Set execution start if not set
        if not task.execution_period_start:
            task.execution_period_start = timezone.now()
        
        # Add note
        note = request.data.get('note', 'Tarefa iniciada')
        existing = task.note or ''
        task.note = f"{existing}\n\n[{timezone.now().strftime('%Y-%m-%d %H:%M')}] STARTED: {note}"
        
        task.save()
        
        logger.info(f"Task {task.identifier} started by {request.user}")
        
        serializer = TaskDetailSerializer(task)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """
        Completar tarefa
        
        POST /api/v1/tasks/{id}/complete/
        Body: {"output": [{...}], "note": "Concluído com sucesso"}
        """
        task = self.get_object()
        
        if task.status not in ['in-progress', 'on-hold']:
            return Response(
                {'error': f'Cannot complete task with status {task.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        task.status = 'completed'
        
        # Set execution end
        if not task.execution_period_end:
            task.execution_period_end = timezone.now()
        
        # Add output if provided
        output = request.data.get('output')
        if output:
            task.output = output if isinstance(output, list) else [output]
        
        # Add note
        note = request.data.get('note', 'Tarefa concluída')
        existing = task.note or ''
        task.note = f"{existing}\n\n[{timezone.now().strftime('%Y-%m-%d %H:%M')}] COMPLETED: {note}"
        
        task.save()
        
        logger.info(f"Task {task.identifier} completed by {request.user}")
        
        serializer = TaskDetailSerializer(task)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """
        Rejeitar tarefa
        
        POST /api/v1/tasks/{id}/reject/
        Body: {"reason": "Não tenho capacidade"}
        """
        task = self.get_object()
        
        if task.status not in ['requested', 'received']:
            return Response(
                {'error': f'Cannot reject task with status {task.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        task.status = 'rejected'
        
        # Add reason
        reason = request.data.get('reason', 'Rejeitado')
        task.status_reason = [{
            'text': reason
        }]
        
        # Add note
        existing = task.note or ''
        task.note = f"{existing}\n\n[{timezone.now().strftime('%Y-%m-%d %H:%M')}] REJECTED: {reason}"
        
        task.save()
        
        logger.warning(f"Task {task.identifier} rejected by {request.user}: {reason}")
        
        serializer = TaskDetailSerializer(task)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Cancelar tarefa
        
        POST /api/v1/tasks/{id}/cancel/
        Body: {"reason": "Não é mais necessário"}
        """
        task = self.get_object()
        
        if task.status in ['completed', 'failed', 'entered-in-error']:
            return Response(
                {'error': f'Cannot cancel task with status {task.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        task.status = 'cancelled'
        
        # Add reason
        reason = request.data.get('reason', 'Cancelado')
        task.status_reason = [{
            'text': reason
        }]
        
        # Add note
        existing = task.note or ''
        task.note = f"{existing}\n\n[{timezone.now().strftime('%Y-%m-%d %H:%M')}] CANCELLED: {reason}"
        
        task.save()
        
        logger.info(f"Task {task.identifier} cancelled by {request.user}: {reason}")
        
        serializer = TaskDetailSerializer(task)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        """
        Atribuir tarefa a novo owner
        
        POST /api/v1/tasks/{id}/assign/
        Body: {"owner_id": "Practitioner/123", "owner_display": "Dr. Silva"}
        """
        task = self.get_object()
        
        owner_id = request.data.get('owner_id')
        if not owner_id:
            return Response(
                {'error': 'owner_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        old_owner = task.owner_display or task.owner_id
        
        task.owner_id = owner_id
        task.owner_display = request.data.get('owner_display', '')
        
        # Add note
        note = f"Reatribuído de {old_owner} para {task.owner_display or owner_id}"
        existing = task.note or ''
        task.note = f"{existing}\n\n[{timezone.now().strftime('%Y-%m-%d %H:%M')}] {note}"
        
        # If task was requested, move to received
        if task.status == 'requested':
            task.status = 'received'
        
        task.save()
        
        logger.info(f"Task {task.identifier} assigned to {owner_id} by {request.user}")
        
        serializer = TaskDetailSerializer(task)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Estatísticas de tarefas
        
        GET /api/v1/tasks/statistics/
        """
        cache_key = 'task_statistics'
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return Response(cached_data)
        
        queryset = self.get_queryset()
        
        total = queryset.count()
        
        by_status = {}
        for status_choice, _ in Task.STATUS_CHOICES:
            by_status[status_choice] = queryset.filter(status=status_choice).count()
        
        by_priority = {}
        for priority_choice, _ in Task.PRIORITY_CHOICES:
            by_priority[priority_choice] = queryset.filter(priority=priority_choice).count()
        
        # Active tasks (not terminal states)
        active = queryset.exclude(status__in=['completed', 'failed', 'rejected', 'cancelled', 'entered-in-error']).count()
        
        # Overdue tasks (execution_period_end passed but not completed)
        overdue = queryset.filter(
            execution_period_end__lt=timezone.now(),
            status__in=['requested', 'received', 'accepted', 'in-progress', 'on-hold']
        ).count()
        
        stats = {
            'total_tasks': total,
            'active_tasks': active,
            'overdue_tasks': overdue,
            'by_status': by_status,
            'by_priority': by_priority,
            'completion_rate': round((by_status.get('completed', 0) / total * 100) if total > 0 else 0, 2),
            'cached_at': timezone.now().isoformat()
        }
        
        cache.set(cache_key, stats, 60 * 5)  # 5 minutes
        
        return Response(stats)
