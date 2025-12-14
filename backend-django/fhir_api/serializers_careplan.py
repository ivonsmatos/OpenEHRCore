"""
FHIR CarePlan Serializers - Sprint 33
"""

from rest_framework import serializers
from .models_careplan import CarePlan, CarePlanActivity
from django.utils import timezone


class CarePlanActivitySerializer(serializers.ModelSerializer):
    """Serializer para CarePlanActivity"""
    
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    kind_display = serializers.CharField(source='get_kind_display', read_only=True)
    
    class Meta:
        model = CarePlanActivity
        fields = [
            'id', 'care_plan', 'status', 'status_display',
            'kind', 'kind_display', 'code', 'description',
            'reason_code', 'reason_reference', 'goal',
            'scheduled_period_start', 'scheduled_period_end',
            'scheduled_string', 'location', 'performers',
            'product_reference', 'daily_amount', 'quantity',
            'progress', 'outcome_codeable_concept', 'outcome_reference',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate(self, data):
        """Validações"""
        # Scheduled period end deve ser após start
        start = data.get('scheduled_period_start')
        end = data.get('scheduled_period_end')
        
        if start and end and end < start:
            raise serializers.ValidationError(
                'scheduled_period_end deve ser posterior a scheduled_period_start'
            )
        
        return data


class CarePlanSerializer(serializers.ModelSerializer):
    """Serializer básico para CarePlan"""
    
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    intent_display = serializers.CharField(source='get_intent_display', read_only=True)
    patient_name = serializers.CharField(source='patient.name', read_only=True)
    author_name = serializers.CharField(source='author.get_full_name', read_only=True)
    activity_count = serializers.SerializerMethodField()
    
    class Meta:
        model = CarePlan
        fields = [
            'id', 'identifier', 'status', 'status_display',
            'intent', 'intent_display', 'title', 'description',
            'categories', 'patient', 'patient_name',
            'encounter', 'period_start', 'period_end',
            'author', 'author_name', 'care_team',
            'addresses', 'goals', 'notes', 'activity_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_activity_count(self, obj):
        """Conta atividades do plano"""
        return obj.activities.count()


class CarePlanDetailSerializer(serializers.ModelSerializer):
    """Serializer detalhado com atividades"""
    
    activities = CarePlanActivitySerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    patient_name = serializers.CharField(source='patient.name', read_only=True)
    author_name = serializers.CharField(source='author.get_full_name', read_only=True)
    
    class Meta:
        model = CarePlan
        fields = [
            'id', 'identifier', 'status', 'status_display',
            'intent', 'title', 'description', 'categories',
            'patient', 'patient_name', 'encounter',
            'period_start', 'period_end', 'author', 'author_name',
            'care_team', 'addresses', 'goals', 'notes',
            'activities', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class CarePlanFHIRSerializer(serializers.ModelSerializer):
    """Serializer FHIR R4 completo"""
    
    class Meta:
        model = CarePlan
        fields = ['id']
    
    def to_representation(self, instance):
        """Retorna formato FHIR canônico"""
        return instance.to_fhir()


class CarePlanCreateSerializer(serializers.Serializer):
    """Serializer para criar CarePlan"""
    
    title = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True)
    patient_id = serializers.UUIDField()
    status = serializers.ChoiceField(choices=CarePlan.STATUS_CHOICES, default='draft')
    intent = serializers.ChoiceField(choices=CarePlan.INTENT_CHOICES, default='plan')
    categories = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list
    )
    period_start = serializers.DateTimeField()
    period_end = serializers.DateTimeField(required=False, allow_null=True)
    encounter_id = serializers.UUIDField(required=False, allow_null=True)
    care_team_id = serializers.UUIDField(required=False, allow_null=True)
    goals = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        default=list
    )
    addresses = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        default=list
    )
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate_patient_id(self, value):
        """Valida que paciente existe"""
        from .models import Patient
        
        if not Patient.objects.filter(id=value).exists():
            raise serializers.ValidationError(f'Paciente {value} não encontrado')
        
        return value
    
    def validate(self, data):
        """Validações gerais"""
        # Period end deve ser após start
        if data.get('period_end') and data.get('period_start'):
            if data['period_end'] < data['period_start']:
                raise serializers.ValidationError(
                    'period_end deve ser posterior a period_start'
                )
        
        return data
    
    def create(self, validated_data):
        """Cria CarePlan"""
        from .models import Patient, Encounter, CareTeam
        
        patient = Patient.objects.get(id=validated_data['patient_id'])
        
        encounter = None
        if validated_data.get('encounter_id'):
            encounter = Encounter.objects.get(id=validated_data['encounter_id'])
        
        care_team = None
        if validated_data.get('care_team_id'):
            care_team = CareTeam.objects.get(id=validated_data['care_team_id'])
        
        care_plan = CarePlan.objects.create(
            title=validated_data['title'],
            description=validated_data.get('description', ''),
            patient=patient,
            status=validated_data['status'],
            intent=validated_data['intent'],
            categories=validated_data.get('categories', []),
            period_start=validated_data['period_start'],
            period_end=validated_data.get('period_end'),
            encounter=encounter,
            care_team=care_team,
            goals=validated_data.get('goals', []),
            addresses=validated_data.get('addresses', []),
            notes=validated_data.get('notes', ''),
            author=self.context['request'].user,
            created_by=self.context['request'].user
        )
        
        return care_plan


class CarePlanActivityCreateSerializer(serializers.Serializer):
    """Serializer para criar atividade"""
    
    care_plan_id = serializers.UUIDField()
    status = serializers.ChoiceField(choices=CarePlanActivity.STATUS_CHOICES, default='not-started')
    kind = serializers.ChoiceField(choices=CarePlanActivity.KIND_CHOICES, required=False)
    code = serializers.DictField()
    description = serializers.CharField(required=False, allow_blank=True)
    scheduled_period_start = serializers.DateTimeField(required=False)
    scheduled_period_end = serializers.DateTimeField(required=False)
    performers = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        default=list
    )
    goal = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        default=list
    )
    
    def create(self, validated_data):
        """Cria atividade"""
        care_plan = CarePlan.objects.get(id=validated_data['care_plan_id'])
        
        activity = CarePlanActivity.objects.create(
            care_plan=care_plan,
            status=validated_data['status'],
            kind=validated_data.get('kind'),
            code=validated_data['code'],
            description=validated_data.get('description', ''),
            scheduled_period_start=validated_data.get('scheduled_period_start'),
            scheduled_period_end=validated_data.get('scheduled_period_end'),
            performers=validated_data.get('performers', []),
            goal=validated_data.get('goal', [])
        )
        
        return activity
