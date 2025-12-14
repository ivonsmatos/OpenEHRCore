"""
MedicationAdministration Serializers

Sprint 34: Serialização de administrações de medicamentos
"""

from rest_framework import serializers
from .models_medication_administration import MedicationAdministration
from django.utils import timezone


class MedicationAdministrationSerializer(serializers.ModelSerializer):
    """Serializer básico para listagem"""
    
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    medication_name = serializers.SerializerMethodField()
    performer_name = serializers.CharField(source='performer_actor_display', read_only=True)
    
    class Meta:
        model = MedicationAdministration
        fields = [
            'id', 'identifier', 'status', 'status_display',
            'medication_name', 'patient_id', 'encounter_id',
            'effective_datetime', 'performer_name',
            'dosage_text', 'note', 'created_at'
        ]
    
    def get_medication_name(self, obj):
        """Extrai nome do medicamento do JSON"""
        if isinstance(obj.medication_code, dict):
            # Tentar text primeiro
            if 'text' in obj.medication_code:
                return obj.medication_code['text']
            # Senão, tentar primeiro coding
            if 'coding' in obj.medication_code and len(obj.medication_code['coding']) > 0:
                return obj.medication_code['coding'][0].get('display', 'Unknown')
        return 'Unknown Medication'


class MedicationAdministrationDetailSerializer(serializers.ModelSerializer):
    """Serializer completo para visualização detalhada"""
    
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    medication_name = serializers.SerializerMethodField()
    
    class Meta:
        model = MedicationAdministration
        fields = '__all__'
        read_only_fields = ['id', 'identifier', 'created_at', 'updated_at', 'created_by']
    
    def get_medication_name(self, obj):
        if isinstance(obj.medication_code, dict):
            if 'text' in obj.medication_code:
                return obj.medication_code['text']
            if 'coding' in obj.medication_code and len(obj.medication_code['coding']) > 0:
                return obj.medication_code['coding'][0].get('display', 'Unknown')
        return 'Unknown Medication'


class MedicationAdministrationFHIRSerializer(serializers.ModelSerializer):
    """Serializer que retorna formato FHIR R4"""
    
    class Meta:
        model = MedicationAdministration
        fields = ['id']
    
    def to_representation(self, instance):
        return instance.to_fhir()


class MedicationAdministrationCreateSerializer(serializers.Serializer):
    """Serializer para criar nova administração"""
    
    # Required
    status = serializers.ChoiceField(choices=MedicationAdministration.STATUS_CHOICES, default='completed')
    patient_id = serializers.CharField(max_length=100)
    medication_code = serializers.JSONField()
    effective_datetime = serializers.DateTimeField(required=False, allow_null=True)
    
    # Optional
    medication_request = serializers.CharField(max_length=100, required=False, allow_null=True, allow_blank=True)
    encounter_id = serializers.CharField(max_length=100, required=False, allow_null=True, allow_blank=True)
    status_reason = serializers.JSONField(required=False, allow_null=True)
    
    # Effective period (alternative to datetime)
    effective_period_start = serializers.DateTimeField(required=False, allow_null=True)
    effective_period_end = serializers.DateTimeField(required=False, allow_null=True)
    
    # Performer
    performer_actor_id = serializers.CharField(max_length=100, required=False, allow_null=True, allow_blank=True)
    performer_actor_display = serializers.CharField(max_length=200, required=False, allow_null=True, allow_blank=True)
    performer_function = serializers.JSONField(required=False, allow_null=True)
    
    # Dosage
    dosage_text = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    dosage_site = serializers.JSONField(required=False, allow_null=True)
    dosage_route = serializers.JSONField(required=False, allow_null=True)
    dosage_method = serializers.JSONField(required=False, allow_null=True)
    dosage_dose_value = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    dosage_dose_unit = serializers.CharField(max_length=50, required=False, allow_null=True, allow_blank=True)
    dosage_rate_value = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    dosage_rate_unit = serializers.CharField(max_length=50, required=False, allow_null=True, allow_blank=True)
    
    # Reason
    reason_code = serializers.JSONField(required=False, allow_null=True)
    reason_reference = serializers.CharField(max_length=100, required=False, allow_null=True, allow_blank=True)
    
    # Other
    device = serializers.JSONField(required=False, allow_null=True)
    note = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    
    def validate(self, data):
        """Validações customizadas"""
        # Pelo menos effective_datetime OU effective_period deve existir
        has_datetime = data.get('effective_datetime') is not None
        has_period = data.get('effective_period_start') is not None or data.get('effective_period_end') is not None
        
        if not has_datetime and not has_period:
            raise serializers.ValidationError(
                "Either effective_datetime or effective_period (start/end) is required"
            )
        
        # Period validation
        if data.get('effective_period_start') and data.get('effective_period_end'):
            if data['effective_period_end'] <= data['effective_period_start']:
                raise serializers.ValidationError(
                    "effective_period_end must be after effective_period_start"
                )
        
        # Status not-done requires status_reason
        if data.get('status') == 'not-done' and not data.get('status_reason'):
            raise serializers.ValidationError(
                "status_reason is required when status is 'not-done'"
            )
        
        return data
    
    def create(self, validated_data):
        """Cria MedicationAdministration"""
        # Set created_by from request user
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['created_by'] = request.user
        
        # Default effective_datetime to now if not provided
        if not validated_data.get('effective_datetime') and not validated_data.get('effective_period_start'):
            validated_data['effective_datetime'] = timezone.now()
        
        administration = MedicationAdministration.objects.create(**validated_data)
        return administration


class MedicationAdministrationUpdateSerializer(serializers.Serializer):
    """Serializer para atualizar administração (principalmente status e notas)"""
    
    status = serializers.ChoiceField(choices=MedicationAdministration.STATUS_CHOICES, required=False)
    status_reason = serializers.JSONField(required=False, allow_null=True)
    note = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    effective_period_end = serializers.DateTimeField(required=False, allow_null=True)
    
    def validate(self, data):
        # Status not-done requires status_reason
        if data.get('status') == 'not-done' and not data.get('status_reason'):
            raise serializers.ValidationError(
                "status_reason is required when status is 'not-done'"
            )
        return data
