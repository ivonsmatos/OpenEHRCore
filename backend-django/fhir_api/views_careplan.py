"""
FHIR CarePlan ViewSet - Sprint 33
REST API for Care Coordination
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Q, Count, Avg
from django.utils import timezone
from django.core.cache import cache

from .models_careplan import CarePlan, CarePlanActivity
from .serializers_careplan import (
    CarePlanSerializer,
    CarePlanDetailSerializer,
    CarePlanFHIRSerializer,
    CarePlanCreateSerializer,
    CarePlanActivitySerializer,
    CarePlanActivityCreateSerializer
)
from .permissions_document import CanViewPatientDocuments, CanCreateDocuments
import logging

logger = logging.getLogger(__name__)


class CarePlanViewSet(viewsets.ModelViewSet):
    """
    ViewSet para FHIR CarePlan Resource
    
    Endpoints:
    - GET /api/v1/careplans/ - Listar planos de cuidado
    - POST /api/v1/careplans/ - Criar plano
    - GET /api/v1/careplans/{id}/ - Buscar plano
    - PUT/PATCH /api/v1/careplans/{id}/ - Atualizar plano
    - DELETE /api/v1/careplans/{id}/ - Deletar plano
    - GET /api/v1/careplans/patient/{patient_id}/ - Planos do paciente
    - POST /api/v1/careplans/{id}/activate/ - Ativar plano
    - POST /api/v1/careplans/{id}/complete/ - Completar plano
    - GET /api/v1/careplans/{id}/activities/ - Listar atividades
    - POST /api/v1/careplans/{id}/activities/ - Adicionar atividade
    """
    
    queryset = CarePlan.objects.all()
    permission_classes = [IsAuthenticated, CanViewPatientDocuments]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    
    filterset_fields = ['status', 'intent', 'patient', 'author', 'care_team']
    search_fields = ['title', 'description', 'patient__name']
    ordering_fields = ['period_start', 'created_at', 'updated_at']
    ordering = ['-period_start']
    
    def get_serializer_class(self):
        """Retorna serializer apropriado"""
        if self.action == 'create':
            return CarePlanCreateSerializer
        elif self.action == 'retrieve':
            if self.request.query_params.get('format') == 'fhir':
                return CarePlanFHIRSerializer
            return CarePlanDetailSerializer
        return CarePlanSerializer
    
    def get_queryset(self):
        """Filtra planos conforme permissões"""
        queryset = super().get_queryset()
        user = self.request.user
        
        if user.is_staff or user.is_superuser:
            return queryset.select_related('patient', 'author', 'care_team')
        
        # Practitioner: planos próprios + pacientes sob cuidado
        if hasattr(user, 'practitioner'):
            queryset = queryset.filter(
                Q(author=user) |
                Q(patient__practitioners=user.practitioner) |
                Q(care_team__members__practitioner=user.practitioner)
            ).distinct()
        
        # Patient: apenas próprios planos
        elif hasattr(user, 'patient'):
            queryset = queryset.filter(patient__user=user)
        
        return queryset.select_related('patient', 'author', 'care_team')
    
    def create(self, request, *args, **kwargs):
        """Cria novo CarePlan"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        care_plan = serializer.save()
        
        logger.info(f"CarePlan {care_plan.id} criado por {request.user}")
        
        # Retornar detalhado
        detail_serializer = CarePlanDetailSerializer(care_plan)
        return Response(detail_serializer.data, status=status.HTTP_201_CREATED)
    
    def retrieve(self, request, *args, **kwargs):
        """Busca plano específico"""
        instance = self.get_object()
        
        # Formato FHIR
        if request.query_params.get('format') == 'fhir':
            return Response(instance.to_fhir())
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='patient/(?P<patient_id>[^/.]+)')
    def by_patient(self, request, patient_id=None):
        """
        Lista todos os planos de cuidado de um paciente
        
        GET /api/v1/careplans/patient/{patient_id}/
        """
        queryset = self.get_queryset().filter(patient_id=patient_id)
        
        # Filtrar por status se fornecido
        status_param = request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = CarePlanSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = CarePlanSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """
        Ativa plano de cuidado (draft → active)
        
        POST /api/v1/careplans/{id}/activate/
        """
        care_plan = self.get_object()
        
        if care_plan.status != 'draft':
            return Response(
                {'error': f'Apenas planos em draft podem ser ativados. Status atual: {care_plan.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        care_plan.status = 'active'
        care_plan.save()
        
        logger.info(f"CarePlan {care_plan.id} ativado por {request.user}")
        
        serializer = CarePlanDetailSerializer(care_plan)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """
        Completa plano de cuidado
        
        POST /api/v1/careplans/{id}/complete/
        
        Body (opcional):
        {
            "notes": "Plano completado com sucesso"
        }
        """
        care_plan = self.get_object()
        
        if care_plan.status not in ['active', 'on-hold']:
            return Response(
                {'error': f'Apenas planos ativos podem ser completados. Status atual: {care_plan.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        care_plan.status = 'completed'
        care_plan.period_end = timezone.now()
        
        # Adicionar notas
        notes = request.data.get('notes')
        if notes:
            existing_notes = care_plan.notes or ''
            care_plan.notes = f"{existing_notes}\n\n[{timezone.now().strftime('%Y-%m-%d %H:%M')}] {notes}"
        
        care_plan.save()
        
        logger.info(f"CarePlan {care_plan.id} completado por {request.user}")
        
        serializer = CarePlanDetailSerializer(care_plan)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get', 'post'])
    def activities(self, request, pk=None):
        """
        GET: Lista atividades do plano
        POST: Adiciona nova atividade
        
        GET /api/v1/careplans/{id}/activities/
        POST /api/v1/careplans/{id}/activities/
        """
        care_plan = self.get_object()
        
        if request.method == 'GET':
            activities = care_plan.activities.all()
            
            # Filtrar por status
            status_param = request.query_params.get('status')
            if status_param:
                activities = activities.filter(status=status_param)
            
            serializer = CarePlanActivitySerializer(activities, many=True)
            return Response({
                'care_plan_id': str(care_plan.id),
                'activity_count': activities.count(),
                'activities': serializer.data
            })
        
        else:  # POST
            data = request.data.copy()
            data['care_plan_id'] = str(care_plan.id)
            
            serializer = CarePlanActivityCreateSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            activity = serializer.save()
            
            logger.info(f"Atividade {activity.id} adicionada ao CarePlan {care_plan.id}")
            
            return Response(
                CarePlanActivitySerializer(activity).data,
                status=status.HTTP_201_CREATED
            )
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Estatísticas de planos de cuidado
        
        GET /api/v1/careplans/statistics/
        """
        cache_key = 'careplan_statistics'
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return Response(cached_data)
        
        queryset = self.get_queryset()
        
        total_plans = queryset.count()
        
        by_status = {}
        for status_choice, _ in CarePlan.STATUS_CHOICES:
            by_status[status_choice] = queryset.filter(status=status_choice).count()
        
        by_intent = {}
        for intent_choice, _ in CarePlan.INTENT_CHOICES:
            by_intent[intent_choice] = queryset.filter(intent=intent_choice).count()
        
        # Planos ativos
        active_plans = queryset.filter(status='active').count()
        
        # Planos com atividades
        plans_with_activities = queryset.annotate(
            activity_count=Count('activities')
        ).filter(activity_count__gt=0).count()
        
        # Média de atividades por plano
        avg_activities = queryset.annotate(
            activity_count=Count('activities')
        ).aggregate(avg=Avg('activity_count'))['avg'] or 0
        
        stats = {
            'total_plans': total_plans,
            'active_plans': active_plans,
            'by_status': by_status,
            'by_intent': by_intent,
            'plans_with_activities': plans_with_activities,
            'avg_activities_per_plan': round(avg_activities, 2),
            'cached_at': timezone.now().isoformat()
        }
        
        cache.set(cache_key, stats, 60 * 5)  # 5 minutos
        
        return Response(stats)


class CarePlanActivityViewSet(viewsets.ModelViewSet):
    """
    ViewSet para CarePlanActivity
    
    Endpoints:
    - GET /api/v1/careplan-activities/ - Listar atividades
    - GET /api/v1/careplan-activities/{id}/ - Buscar atividade
    - PATCH /api/v1/careplan-activities/{id}/ - Atualizar status/progress
    - POST /api/v1/careplan-activities/{id}/start/ - Iniciar atividade
    - POST /api/v1/careplan-activities/{id}/complete/ - Completar atividade
    """
    
    queryset = CarePlanActivity.objects.all()
    serializer_class = CarePlanActivitySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    
    filterset_fields = ['care_plan', 'status', 'kind']
    ordering_fields = ['scheduled_period_start', 'created_at']
    ordering = ['scheduled_period_start']
    
    def get_queryset(self):
        """Filtra conforme permissões"""
        queryset = super().get_queryset()
        user = self.request.user
        
        if user.is_staff or user.is_superuser:
            return queryset.select_related('care_plan', 'location')
        
        # Filtrar por planos acessíveis
        if hasattr(user, 'practitioner'):
            queryset = queryset.filter(
                Q(care_plan__author=user) |
                Q(care_plan__patient__practitioners=user.practitioner)
            ).distinct()
        
        elif hasattr(user, 'patient'):
            queryset = queryset.filter(care_plan__patient__user=user)
        
        return queryset.select_related('care_plan', 'location')
    
    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """Inicia atividade"""
        activity = self.get_object()
        
        if activity.status != 'not-started':
            return Response(
                {'error': f'Atividade já foi iniciada. Status: {activity.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        activity.status = 'in-progress'
        activity.save()
        
        serializer = self.get_serializer(activity)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Completa atividade"""
        activity = self.get_object()
        
        activity.status = 'completed'
        
        # Adicionar progress note
        progress = request.data.get('progress')
        if progress:
            existing = activity.progress or ''
            activity.progress = f"{existing}\n\n[{timezone.now().strftime('%Y-%m-%d %H:%M')}] {progress}"
        
        activity.save()
        
        serializer = self.get_serializer(activity)
        return Response(serializer.data)
