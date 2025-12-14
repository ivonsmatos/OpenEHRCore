"""
Task Serializers

Sprint 34: Serialização de tasks genéricos
"""

from rest_framework import serializers
from .models_task import Task
from django.utils import timezone


class TaskSerializer(serializers.ModelSerializer):
    """Serializer básico para listagem"""
    
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    intent_display = serializers.CharField(source='get_intent_display', read_only=True)
    owner_name = serializers.CharField(source='owner_display', read_only=True)
    requester_name = serializers.CharField(source='requester_display', read_only=True)
    
    class Meta:
        model = Task
        fields = [
            'id', 'identifier', 'status', 'status_display',
            'priority', 'priority_display', 'intent', 'intent_display',
            'description', 'owner_name', 'requester_name',
            'for_patient_id', 'authored_on', 'last_modified'
        ]


class TaskDetailSerializer(serializers.ModelSerializer):
    """Serializer completo para visualização detalhada"""
    
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    intent_display = serializers.CharField(source='get_intent_display', read_only=True)
    
    class Meta:
        model = Task
        fields = '__all__'
        read_only_fields = ['id', 'identifier', 'authored_on', 'last_modified', 'created_by', 'updated_at']


class TaskFHIRSerializer(serializers.ModelSerializer):
    """Serializer que retorna formato FHIR R4"""
    
    class Meta:
        model = Task
        fields = ['id']
    
    def to_representation(self, instance):
        return instance.to_fhir()


class TaskCreateSerializer(serializers.Serializer):
    """Serializer para criar nova tarefa"""
    
    # Required
    status = serializers.ChoiceField(choices=Task.STATUS_CHOICES, default='requested')
    intent = serializers.ChoiceField(choices=Task.INTENT_CHOICES, default='order')
    
    # Optional
    priority = serializers.ChoiceField(choices=Task.PRIORITY_CHOICES, default='routine')
    status_reason = serializers.JSONField(required=False, allow_null=True)
    business_status = serializers.JSONField(required=False, allow_null=True)
    
    code = serializers.JSONField(required=False, allow_null=True)
    description = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    
    # Context
    focus = serializers.CharField(max_length=200, required=False, allow_null=True, allow_blank=True)
    for_patient_id = serializers.CharField(max_length=100, required=False, allow_null=True, allow_blank=True)
    encounter_id = serializers.CharField(max_length=100, required=False, allow_null=True, allow_blank=True)
    
    # Responsibilities
    requester_id = serializers.CharField(max_length=100, required=False, allow_null=True, allow_blank=True)
    requester_display = serializers.CharField(max_length=200, required=False, allow_null=True, allow_blank=True)
    owner_id = serializers.CharField(max_length=100, required=False, allow_null=True, allow_blank=True)
    owner_display = serializers.CharField(max_length=200, required=False, allow_null=True, allow_blank=True)
    
    # Timing
    execution_period_start = serializers.DateTimeField(required=False, allow_null=True)
    execution_period_end = serializers.DateTimeField(required=False, allow_null=True)
    
    # Relationships
    based_on = serializers.JSONField(required=False, allow_null=True)
    part_of = serializers.JSONField(required=False, allow_null=True)
    
    # Restrictions
    restriction_period_start = serializers.DateTimeField(required=False, allow_null=True)
    restriction_period_end = serializers.DateTimeField(required=False, allow_null=True)
    restriction_repetitions = serializers.IntegerField(required=False, allow_null=True)
    restriction_recipient = serializers.JSONField(required=False, allow_null=True)
    
    # Input/Output
    input = serializers.JSONField(required=False, allow_null=True)
    output = serializers.JSONField(required=False, allow_null=True)
    
    # Notes
    note = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    
    def validate(self, data):
        """Validações customizadas"""
        # Execution period validation
        if data.get('execution_period_start') and data.get('execution_period_end'):
            if data['execution_period_end'] <= data['execution_period_start']:
                raise serializers.ValidationError(
                    "execution_period_end must be after execution_period_start"
                )
        
        # Restriction period validation
        if data.get('restriction_period_start') and data.get('restriction_period_end'):
            if data['restriction_period_end'] <= data['restriction_period_start']:
                raise serializers.ValidationError(
                    "restriction_period_end must be after restriction_period_start"
                )
        
        return data
    
    def create(self, validated_data):
        """Cria Task"""
        # Set created_by from request user
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['created_by'] = request.user
        
        task = Task.objects.create(**validated_data)
        return task


class TaskUpdateSerializer(serializers.Serializer):
    """Serializer para atualizar tarefa (principalmente status e outputs)"""
    
    status = serializers.ChoiceField(choices=Task.STATUS_CHOICES, required=False)
    status_reason = serializers.JSONField(required=False, allow_null=True)
    business_status = serializers.JSONField(required=False, allow_null=True)
    
    priority = serializers.ChoiceField(choices=Task.PRIORITY_CHOICES, required=False)
    
    description = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    note = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    
    owner_id = serializers.CharField(max_length=100, required=False, allow_null=True, allow_blank=True)
    owner_display = serializers.CharField(max_length=200, required=False, allow_null=True, allow_blank=True)
    
    execution_period_start = serializers.DateTimeField(required=False, allow_null=True)
    execution_period_end = serializers.DateTimeField(required=False, allow_null=True)
    
    output = serializers.JSONField(required=False, allow_null=True)
    
    def validate(self, data):
        # Execution period validation
        if 'execution_period_start' in data and 'execution_period_end' in data:
            if data['execution_period_end'] and data['execution_period_start']:
                if data['execution_period_end'] <= data['execution_period_start']:
                    raise serializers.ValidationError(
                        "execution_period_end must be after execution_period_start"
                    )
        
        return data


class TaskTransitionSerializer(serializers.Serializer):
    """Serializer para transições de status com validação"""
    
    new_status = serializers.ChoiceField(choices=Task.STATUS_CHOICES)
    reason = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    note = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    output = serializers.JSONField(required=False, allow_null=True)
