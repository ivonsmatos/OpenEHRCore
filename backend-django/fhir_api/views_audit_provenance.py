"""
AuditEvent and Provenance ViewSets - FHIR R4

Sprint 36: Conformidade FHIR R4 - Audit Trail completo

Endpoints:
- /audit-events-v2/ - AuditEvent CRUD
- /provenances/ - Provenance CRUD
"""

import logging
from django.db.models import Q, Count
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import serializers

from .models_audit import AuditEvent, Provenance
from .authentication import KeycloakAuthentication
from .search import FHIRSearchMixin, SearchParameter, SearchParamType

logger = logging.getLogger(__name__)


# ============================================================================
# Serializers
# ============================================================================

class AuditEventSerializer(serializers.ModelSerializer):
    """Serializer para AuditEvent"""

    class Meta:
        model = AuditEvent
        fields = '__all__'
        read_only_fields = ['id', 'recorded', 'created_at']

    def to_representation(self, instance):
        """Retorna representação FHIR"""
        return instance.to_fhir()


class AuditEventCreateSerializer(serializers.Serializer):
    """Serializer para criação de AuditEvent"""
    type_code = serializers.ChoiceField(choices=AuditEvent.TYPE_CHOICES)
    subtype_code = serializers.CharField(required=False, allow_null=True)
    action = serializers.ChoiceField(choices=AuditEvent.ACTION_CHOICES)
    outcome = serializers.ChoiceField(choices=AuditEvent.OUTCOME_CHOICES, default='0')
    outcome_desc = serializers.CharField(required=False, allow_null=True)

    # Agent
    agent_who_id = serializers.CharField()
    agent_who_display = serializers.CharField(required=False, allow_null=True)
    agent_name = serializers.CharField(required=False, allow_null=True)
    agent_network_address = serializers.CharField(required=False, allow_null=True)

    # Entity
    entity_what_id = serializers.CharField(required=False, allow_null=True)
    entity_what_display = serializers.CharField(required=False, allow_null=True)
    entity_type = serializers.CharField(required=False, allow_null=True)

    # Patient
    patient_id = serializers.CharField(required=False, allow_null=True)


class ProvenanceSerializer(serializers.ModelSerializer):
    """Serializer para Provenance"""

    class Meta:
        model = Provenance
        fields = '__all__'
        read_only_fields = ['id', 'recorded', 'created_at']

    def to_representation(self, instance):
        """Retorna representação FHIR"""
        return instance.to_fhir()


class ProvenanceCreateSerializer(serializers.Serializer):
    """Serializer para criação de Provenance"""
    target = serializers.JSONField()
    activity_code = serializers.ChoiceField(choices=Provenance.ACTIVITY_CHOICES)
    agents = serializers.JSONField()
    occurred_datetime = serializers.DateTimeField(required=False, allow_null=True)
    location_id = serializers.CharField(required=False, allow_null=True)
    location_display = serializers.CharField(required=False, allow_null=True)
    policy = serializers.JSONField(required=False, allow_null=True)
    reason = serializers.JSONField(required=False, allow_null=True)
    entities = serializers.JSONField(required=False, allow_null=True)


# ============================================================================
# ViewSets
# ============================================================================

class AuditEventViewSet(FHIRSearchMixin, viewsets.ModelViewSet):
    """
    ViewSet para AuditEvent (FHIR R4)

    Endpoints:
    - GET /audit-events-v2/ - Lista eventos de auditoria
    - GET /audit-events-v2/{id}/ - Detalhe do evento
    - POST /audit-events-v2/ - Cria novo evento
    - GET /audit-events-v2/stats/ - Estatísticas
    - GET /audit-events-v2/by-patient/{patient_id}/ - Eventos por paciente
    - GET /audit-events-v2/by-agent/{agent_id}/ - Eventos por agente
    - GET /audit-events-v2/security-report/ - Relatório de segurança

    FHIR Search Parameters:
    - type: Type of audit event
    - action: Type of action performed
    - outcome: Outcome of the event
    - agent: Who was involved
    - patient: Patient involved
    - entity: What was involved
    - date: When the event occurred
    """
    queryset = AuditEvent.objects.all()
    authentication_classes = [KeycloakAuthentication]
    permission_classes = [IsAuthenticated]

    # FHIR Search Parameters
    search_parameters = {
        'type': SearchParameter(
            name='type',
            type=SearchParamType.TOKEN,
            path='type',
            django_field='type_code',
            description='Type/identifier of event'
        ),
        'action': SearchParameter(
            name='action',
            type=SearchParamType.TOKEN,
            path='action',
            django_field='action',
            description='Type of action performed'
        ),
        'outcome': SearchParameter(
            name='outcome',
            type=SearchParamType.TOKEN,
            path='outcome',
            django_field='outcome',
            description='Whether the event succeeded or failed'
        ),
        'agent': SearchParameter(
            name='agent',
            type=SearchParamType.REFERENCE,
            path='agent.who',
            django_field='agent_who_id',
            description='Identifier of who'
        ),
        'patient': SearchParameter(
            name='patient',
            type=SearchParamType.REFERENCE,
            path='entity.what',
            django_field='patient_id',
            description='Patient involved',
            target_resources=['Patient']
        ),
        'entity': SearchParameter(
            name='entity',
            type=SearchParamType.REFERENCE,
            path='entity.what',
            django_field='entity_what_id',
            description='Specific instance of resource'
        ),
        'date': SearchParameter(
            name='date',
            type=SearchParamType.DATE,
            path='recorded',
            django_field='recorded',
            description='Time when the event was recorded'
        ),
    }

    def get_serializer_class(self):
        if self.action == 'create':
            return AuditEventCreateSerializer
        return AuditEventSerializer

    def get_queryset(self):
        """Aplica filtros de busca"""
        queryset = AuditEvent.objects.all().order_by('-recorded')

        # Filtros
        type_code = self.request.query_params.get('type')
        action = self.request.query_params.get('action')
        outcome = self.request.query_params.get('outcome')
        agent = self.request.query_params.get('agent')
        patient = self.request.query_params.get('patient')
        entity = self.request.query_params.get('entity')
        date_from = self.request.query_params.get('date')
        date_to = self.request.query_params.get('date_to')

        if type_code:
            queryset = queryset.filter(type_code=type_code)
        if action:
            queryset = queryset.filter(action=action)
        if outcome:
            queryset = queryset.filter(outcome=outcome)
        if agent:
            queryset = queryset.filter(
                Q(agent_who_id__icontains=agent) |
                Q(agent_name__icontains=agent) |
                Q(agent_alt_id__icontains=agent)
            )
        if patient:
            queryset = queryset.filter(patient_id=patient)
        if entity:
            queryset = queryset.filter(entity_what_id__icontains=entity)
        if date_from:
            queryset = queryset.filter(recorded__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(recorded__date__lte=date_to)

        return queryset

    def create(self, request, *args, **kwargs):
        """Cria novo AuditEvent"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        audit = AuditEvent(
            type_code=data['type_code'],
            subtype_code=data.get('subtype_code'),
            action=data['action'],
            outcome=data.get('outcome', '0'),
            outcome_desc=data.get('outcome_desc'),
            agent_who_id=data['agent_who_id'],
            agent_who_display=data.get('agent_who_display'),
            agent_name=data.get('agent_name'),
            agent_network_address=data.get('agent_network_address'),
            entity_what_id=data.get('entity_what_id'),
            entity_what_display=data.get('entity_what_display'),
            entity_type=data.get('entity_type'),
            patient_id=data.get('patient_id'),
            source_site='OpenEHRCore',
            source_observer_id='Device/openehrcore-server',
        )
        audit.save()

        return Response(audit.to_fhir(), status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Estatísticas de auditoria"""
        queryset = self.get_queryset()

        # Total
        total = queryset.count()

        # Por tipo
        by_type = queryset.values('type_code').annotate(count=Count('id'))

        # Por ação
        by_action = queryset.values('action').annotate(count=Count('id'))

        # Por outcome
        by_outcome = queryset.values('outcome').annotate(count=Count('id'))

        # Últimas 24h
        last_24h = queryset.filter(
            recorded__gte=timezone.now() - timezone.timedelta(hours=24)
        ).count()

        # Falhas
        failures = queryset.filter(outcome__in=['4', '8', '12']).count()

        return Response({
            'total': total,
            'last_24h': last_24h,
            'failures': failures,
            'by_type': {item['type_code']: item['count'] for item in by_type},
            'by_action': {item['action']: item['count'] for item in by_action},
            'by_outcome': {item['outcome']: item['count'] for item in by_outcome},
        })

    @action(detail=False, methods=['get'], url_path='by-patient/(?P<patient_id>[^/.]+)')
    def by_patient(self, request, patient_id=None):
        """Eventos por paciente"""
        queryset = self.get_queryset().filter(patient_id=patient_id)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='by-agent/(?P<agent_id>[^/.]+)')
    def by_agent(self, request, agent_id=None):
        """Eventos por agente"""
        queryset = self.get_queryset().filter(
            Q(agent_who_id__icontains=agent_id) |
            Q(agent_alt_id=agent_id)
        )

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='security-report')
    def security_report(self, request):
        """Relatório de segurança"""
        days = int(request.query_params.get('days', 7))
        start_date = timezone.now() - timezone.timedelta(days=days)

        queryset = self.get_queryset().filter(recorded__gte=start_date)

        # Eventos de segurança
        security_events = queryset.filter(type_code='security')

        # Logins
        logins = security_events.filter(subtype_code='login')
        login_success = logins.filter(outcome='0').count()
        login_failure = logins.exclude(outcome='0').count()

        # Acessos de emergência
        emergency_access = queryset.filter(type_code='emergency').count()

        # Top agents por atividade
        top_agents = queryset.values('agent_who_id', 'agent_name').annotate(
            count=Count('id')
        ).order_by('-count')[:10]

        # Top recursos acessados
        top_resources = queryset.values('entity_what_id', 'entity_type').annotate(
            count=Count('id')
        ).order_by('-count')[:10]

        # Falhas por dia
        failures_by_day = queryset.filter(
            outcome__in=['4', '8', '12']
        ).extra(
            select={'day': 'DATE(recorded)'}
        ).values('day').annotate(count=Count('id')).order_by('day')

        return Response({
            'period_days': days,
            'total_events': queryset.count(),
            'security_events': security_events.count(),
            'logins': {
                'success': login_success,
                'failure': login_failure,
            },
            'emergency_access': emergency_access,
            'top_agents': list(top_agents),
            'top_resources': list(top_resources),
            'failures_by_day': list(failures_by_day),
        })


class ProvenanceViewSet(FHIRSearchMixin, viewsets.ModelViewSet):
    """
    ViewSet para Provenance (FHIR R4)

    Endpoints:
    - GET /provenances/ - Lista provenances
    - GET /provenances/{id}/ - Detalhe
    - POST /provenances/ - Cria novo
    - GET /provenances/by-target/ - Por target
    - GET /provenances/by-activity/ - Por atividade

    FHIR Search Parameters:
    - target: Target Reference(s) (usually version specific)
    - recorded: When the activity was recorded
    - activity: Activity that occurred
    - agent: Who participated
    - location: Where the activity occurred
    """
    queryset = Provenance.objects.all()
    authentication_classes = [KeycloakAuthentication]
    permission_classes = [IsAuthenticated]

    # FHIR Search Parameters
    search_parameters = {
        'target': SearchParameter(
            name='target',
            type=SearchParamType.REFERENCE,
            path='target',
            django_field='target',
            description='Target Reference(s)'
        ),
        'recorded': SearchParameter(
            name='recorded',
            type=SearchParamType.DATE,
            path='recorded',
            django_field='recorded',
            description='When the activity was recorded'
        ),
        'activity': SearchParameter(
            name='activity',
            type=SearchParamType.TOKEN,
            path='activity',
            django_field='activity_code',
            description='Activity that occurred'
        ),
        'agent': SearchParameter(
            name='agent',
            type=SearchParamType.REFERENCE,
            path='agent.who',
            django_field='agents',
            description='Who participated'
        ),
        'location': SearchParameter(
            name='location',
            type=SearchParamType.REFERENCE,
            path='location',
            django_field='location_id',
            description='Where the activity occurred'
        ),
    }

    def get_serializer_class(self):
        if self.action == 'create':
            return ProvenanceCreateSerializer
        return ProvenanceSerializer

    def get_queryset(self):
        """Aplica filtros de busca"""
        queryset = Provenance.objects.all().order_by('-recorded')

        # Filtros
        activity = self.request.query_params.get('activity')
        agent = self.request.query_params.get('agent')
        target = self.request.query_params.get('target')
        date_from = self.request.query_params.get('date')

        if activity:
            queryset = queryset.filter(activity_code=activity)
        if agent:
            queryset = queryset.filter(agents__contains=agent)
        if target:
            queryset = queryset.filter(target__contains=target)
        if date_from:
            queryset = queryset.filter(recorded__date__gte=date_from)

        return queryset

    def create(self, request, *args, **kwargs):
        """Cria novo Provenance"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        provenance = Provenance(
            target=data['target'],
            activity_code=data['activity_code'],
            agents=data['agents'],
            occurred_datetime=data.get('occurred_datetime'),
            location_id=data.get('location_id'),
            location_display=data.get('location_display'),
            policy=data.get('policy'),
            reason=data.get('reason'),
            entities=data.get('entities'),
            created_by=request.user if request.user.is_authenticated else None,
        )
        provenance.save()

        return Response(provenance.to_fhir(), status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], url_path='by-target')
    def by_target(self, request):
        """Busca provenances por target"""
        target_ref = request.query_params.get('reference')
        if not target_ref:
            return Response(
                {'error': 'Query parameter "reference" is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        queryset = self.get_queryset().filter(target__contains=target_ref)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='by-activity')
    def by_activity(self, request):
        """Busca provenances por tipo de atividade"""
        activity = request.query_params.get('code')
        if not activity:
            return Response(
                {'error': 'Query parameter "code" is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        queryset = self.get_queryset().filter(activity_code=activity)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Estatísticas de provenance"""
        queryset = self.get_queryset()

        by_activity = queryset.values('activity_code').annotate(count=Count('id'))

        return Response({
            'total': queryset.count(),
            'by_activity': {item['activity_code']: item['count'] for item in by_activity},
        })
