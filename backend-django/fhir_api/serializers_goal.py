"""
Goal Serializers

Sprint 35: Serialização de objetivos terapêuticos
"""

from rest_framework import serializers
from .models_goal import Goal, GoalTarget
from django.utils import timezone


class GoalTargetSerializer(serializers.ModelSerializer):
    """Serializer para targets de Goal"""
    
    target_display = serializers.SerializerMethodField()
    
    class Meta:
        model = GoalTarget
        fields = [
            'id', 'measure', 'target_display',
            'detail_quantity_value', 'detail_quantity_unit', 'detail_quantity_comparator',
            'detail_range_low', 'detail_range_high',
            'detail_string', 'detail_boolean', 'detail_integer',
            'due_date', 'created_at'
        ]
    
    def get_target_display(self, obj):
        """Retorna representação legível do target"""
        return str(obj)


class GoalSerializer(serializers.ModelSerializer):
    """Serializer básico para listagem"""
    
    lifecycle_status_display = serializers.CharField(source='get_lifecycle_status_display', read_only=True)
    achievement_status_display = serializers.CharField(source='get_achievement_status_display', read_only=True)
    description_text = serializers.SerializerMethodField()
    targets_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Goal
        fields = [
            'id', 'identifier', 'lifecycle_status', 'lifecycle_status_display',
            'achievement_status', 'achievement_status_display',
            'description_text', 'subject_id', 'start_date', 'status_date',
            'priority', 'targets_count', 'created_at'
        ]
    
    def get_description_text(self, obj):
        """Extrai texto da descrição"""
        if isinstance(obj.description, dict):
            return obj.description.get('text', 'Goal')
        return 'Goal'
    
    def get_targets_count(self, obj):
        """Conta targets associados"""
        return obj.targets.count()


class GoalDetailSerializer(serializers.ModelSerializer):
    """Serializer completo para visualização detalhada"""
    
    lifecycle_status_display = serializers.CharField(source='get_lifecycle_status_display', read_only=True)
    achievement_status_display = serializers.CharField(source='get_achievement_status_display', read_only=True)
    targets = GoalTargetSerializer(many=True, read_only=True)
    
    class Meta:
        model = Goal
        fields = '__all__'
        read_only_fields = ['id', 'identifier', 'created_at', 'updated_at', 'created_by', 'status_date']


class GoalFHIRSerializer(serializers.ModelSerializer):
    """Serializer que retorna formato FHIR R4"""
    
    target = serializers.SerializerMethodField()
    
    class Meta:
        model = Goal
        fields = ['id']
    
    def get_target(self, obj):
        """Inclui targets no formato FHIR"""
        return [t.to_fhir() for t in obj.targets.all()]
    
    def to_representation(self, instance):
        fhir_resource = instance.to_fhir()
        
        # Adicionar targets
        targets = [t.to_fhir() for t in instance.targets.all()]
        if targets:
            fhir_resource['target'] = targets
        
        return fhir_resource


class GoalCreateSerializer(serializers.Serializer):
    """Serializer para criar novo objetivo"""
    
    # Required
    description = serializers.JSONField()
    subject_id = serializers.CharField(max_length=100)
    
    # Optional
    lifecycle_status = serializers.ChoiceField(choices=Goal.LIFECYCLE_STATUS_CHOICES, default='proposed')
    achievement_status = serializers.ChoiceField(choices=Goal.ACHIEVEMENT_STATUS_CHOICES, required=False, allow_null=True)
    
    category = serializers.JSONField(required=False, allow_null=True)
    priority = serializers.ChoiceField(choices=Goal.PRIORITY_CHOICES, required=False, allow_null=True)
    
    start_date = serializers.DateField(required=False, allow_null=True)
    
    expressed_by_id = serializers.CharField(max_length=100, required=False, allow_null=True, allow_blank=True)
    expressed_by_display = serializers.CharField(max_length=200, required=False, allow_null=True, allow_blank=True)
    
    addresses = serializers.JSONField(required=False, allow_null=True)
    note = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    status_reason = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    
    # Targets (array)
    targets = serializers.ListField(child=serializers.DictField(), required=False, allow_null=True)
    
    def validate_description(self, value):
        """Valida description (deve ser CodeableConcept)"""
        if isinstance(value, dict):
            if 'text' not in value and 'coding' not in value:
                raise serializers.ValidationError("Description must have 'text' or 'coding'")
        return value
    
    def validate(self, data):
        """Validações customizadas"""
        # Completed goals should have achievement_status
        if data.get('lifecycle_status') == 'completed' and not data.get('achievement_status'):
            raise serializers.ValidationError(
                "achievement_status is required for completed goals"
            )
        
        return data
    
    def create(self, validated_data):
        """Cria Goal com targets"""
        # Extract targets
        targets_data = validated_data.pop('targets', [])
        
        # Set created_by from request user
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['created_by'] = request.user
        
        # Create Goal
        goal = Goal.objects.create(**validated_data)
        
        # Create targets
        for target_data in targets_data:
            GoalTarget.objects.create(goal=goal, **target_data)
        
        return goal


class GoalUpdateSerializer(serializers.Serializer):
    """Serializer para atualizar objetivo"""
    
    lifecycle_status = serializers.ChoiceField(choices=Goal.LIFECYCLE_STATUS_CHOICES, required=False)
    achievement_status = serializers.ChoiceField(choices=Goal.ACHIEVEMENT_STATUS_CHOICES, required=False, allow_null=True)
    
    priority = serializers.ChoiceField(choices=Goal.PRIORITY_CHOICES, required=False, allow_null=True)
    
    description = serializers.JSONField(required=False)
    note = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    status_reason = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    
    start_date = serializers.DateField(required=False, allow_null=True)
    
    # Targets (adicionar/remover)
    add_targets = serializers.ListField(child=serializers.DictField(), required=False, allow_null=True)
    
    def validate(self, data):
        # Completed goals should have achievement_status
        if data.get('lifecycle_status') == 'completed':
            if not data.get('achievement_status'):
                # Check if instance already has achievement_status
                instance = self.instance
                if instance and not instance.achievement_status:
                    raise serializers.ValidationError(
                        "achievement_status is required for completed goals"
                    )
        
        return data


class GoalTargetCreateSerializer(serializers.Serializer):
    """Serializer para adicionar target a goal existente"""
    
    measure = serializers.JSONField(required=False, allow_null=True)
    
    # Detail options (apenas um deve ser usado)
    detail_quantity_value = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    detail_quantity_unit = serializers.CharField(max_length=50, required=False, allow_null=True, allow_blank=True)
    detail_quantity_comparator = serializers.CharField(max_length=10, required=False, allow_null=True, allow_blank=True)
    
    detail_range_low = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    detail_range_high = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    
    detail_string = serializers.CharField(max_length=500, required=False, allow_null=True, allow_blank=True)
    detail_boolean = serializers.BooleanField(required=False, allow_null=True)
    detail_integer = serializers.IntegerField(required=False, allow_null=True)
    
    # Due
    due_date = serializers.DateField(required=False, allow_null=True)
    
    def validate(self, data):
        """Valida que pelo menos um detail foi fornecido"""
        detail_fields = [
            'detail_quantity_value', 'detail_range_low', 'detail_range_high',
            'detail_string', 'detail_boolean', 'detail_integer'
        ]
        
        has_detail = any(data.get(field) is not None for field in detail_fields)
        
        if not has_detail:
            raise serializers.ValidationError(
                "At least one detail field must be provided (quantity, range, string, boolean, or integer)"
            )
        
        return data
