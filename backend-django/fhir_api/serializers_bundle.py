"""
FHIR Bundle Serializers - Sprint 33
HL7 FHIR R4 Bundle Resource Serialization
"""

from rest_framework import serializers
from .models_bundle import Bundle, BundleEntry
from django.utils import timezone


class BundleEntrySerializer(serializers.ModelSerializer):
    """Serializer para BundleEntry individual"""
    
    class Meta:
        model = BundleEntry
        fields = [
            'id', 'full_url', 'resource_type', 'resource_id',
            'request_method', 'request_url', 'response_status',
            'response_location', 'resource_json', 'processed',
            'error_message', 'created_at'
        ]
        read_only_fields = ['id', 'processed', 'created_at']


class BundleSerializer(serializers.ModelSerializer):
    """Serializer básico para Bundle"""
    
    entry_count = serializers.SerializerMethodField()
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = Bundle
        fields = [
            'id', 'identifier', 'type', 'timestamp', 'total',
            'status', 'result_message', 'entry_count',
            'created_by', 'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'status', 'result_message', 'created_at', 'updated_at']
    
    def get_entry_count(self, obj):
        """Retorna número de entries no bundle"""
        return len(obj.entries) if obj.entries else 0


class BundleFHIRSerializer(serializers.ModelSerializer):
    """Serializer completo FHIR R4"""
    
    class Meta:
        model = Bundle
        fields = ['id', 'type', 'timestamp', 'entries']
    
    def to_representation(self, instance):
        """Retorna formato FHIR canônico"""
        return instance.to_fhir()
    
    def to_internal_value(self, data):
        """Converte FHIR JSON para formato interno"""
        if not isinstance(data, dict):
            raise serializers.ValidationError('Bundle deve ser um objeto JSON')
        
        if data.get('resourceType') != 'Bundle':
            raise serializers.ValidationError('resourceType deve ser "Bundle"')
        
        bundle_type = data.get('type')
        if not bundle_type:
            raise serializers.ValidationError('Campo "type" é obrigatório')
        
        entries = data.get('entry', [])
        
        return {
            'type': bundle_type,
            'timestamp': data.get('timestamp', timezone.now().isoformat()),
            'total': data.get('total'),
            'identifier': data.get('identifier', {}).get('value') if 'identifier' in data else None,
            'entries': entries
        }


class BundleCreateSerializer(serializers.Serializer):
    """Serializer para criar Bundle via API"""
    
    type = serializers.ChoiceField(choices=Bundle.BUNDLE_TYPE_CHOICES)
    entries = serializers.ListField(
        child=serializers.DictField(),
        min_length=1,
        help_text='Array de BundleEntry conforme especificação FHIR'
    )
    identifier = serializers.CharField(max_length=255, required=False, allow_blank=True)
    timestamp = serializers.DateTimeField(required=False)
    
    def validate_entries(self, entries):
        """Valida estrutura das entries"""
        for idx, entry in enumerate(entries):
            # Transaction/Batch devem ter request
            if self.initial_data.get('type') in ['transaction', 'batch']:
                if 'request' not in entry:
                    raise serializers.ValidationError(
                        f'Entry {idx} deve ter campo "request" para bundles do tipo transaction/batch'
                    )
                
                request = entry['request']
                if 'method' not in request or 'url' not in request:
                    raise serializers.ValidationError(
                        f'Entry {idx} request deve ter "method" e "url"'
                    )
                
                # POST/PUT/PATCH devem ter resource
                if request['method'].upper() in ['POST', 'PUT', 'PATCH']:
                    if 'resource' not in entry:
                        raise serializers.ValidationError(
                            f'Entry {idx} deve ter campo "resource" para método {request["method"]}'
                        )
                    
                    resource = entry['resource']
                    if 'resourceType' not in resource:
                        raise serializers.ValidationError(
                            f'Entry {idx} resource deve ter campo "resourceType"'
                        )
        
        return entries
    
    def create(self, validated_data):
        """Cria Bundle no banco de dados"""
        user = self.context['request'].user
        
        bundle = Bundle.objects.create(
            type=validated_data['type'],
            identifier=validated_data.get('identifier'),
            timestamp=validated_data.get('timestamp', timezone.now()),
            entries=validated_data['entries'],
            created_by=user,
            status='pending'
        )
        
        return bundle


class BundleProcessSerializer(serializers.Serializer):
    """Serializer para processar Bundle"""
    
    auto_process = serializers.BooleanField(
        default=True,
        help_text='Se True, processa o bundle imediatamente'
    )
    
    def validate(self, data):
        """Valida se bundle pode ser processado"""
        bundle = self.instance
        
        if bundle.status in ['processing', 'completed']:
            raise serializers.ValidationError(
                f'Bundle já está {bundle.status}. Não pode ser processado novamente.'
            )
        
        if bundle.type not in ['transaction', 'batch']:
            raise serializers.ValidationError(
                f'Apenas bundles do tipo transaction/batch podem ser processados. Tipo atual: {bundle.type}'
            )
        
        return data
