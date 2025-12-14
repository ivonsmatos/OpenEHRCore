"""
Bundle Processor - FHIR Transaction/Batch Processing
Sprint 33

Responsável por processar Bundle.entry[] e executar operações CRUD
em múltiplos recursos FHIR de forma atômica (transaction) ou independente (batch)
"""

from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import ValidationError as DRFValidationError
import logging

logger = logging.getLogger(__name__)


class BundleTransactionProcessor:
    """
    Processa Bundle do tipo 'transaction' com garantia ACID
    Rollback completo se qualquer operação falhar
    """
    
    def __init__(self, bundle):
        self.bundle = bundle
        self.results = []
        self.resource_registry = {}  # Para resolver referências internas
    
    @transaction.atomic
    def process(self):
        """
        Processa todas as entries do bundle de forma atômica
        
        Returns:
            dict: Bundle FHIR com responses
        """
        logger.info(f"Processing transaction bundle {self.bundle.id}")
        
        try:
            # Validar bundle
            self._validate_bundle()
            
            # Processar cada entry em ordem
            for idx, entry in enumerate(self.bundle.entries):
                logger.debug(f"Processing entry {idx + 1}/{len(self.bundle.entries)}")
                
                result = self._process_entry(entry, idx)
                self.results.append(result)
            
            # Criar response bundle
            response_bundle = {
                'resourceType': 'Bundle',
                'id': str(self.bundle.id),
                'type': 'transaction-response',
                'timestamp': timezone.now().isoformat(),
                'entry': self.results
            }
            
            logger.info(f"Transaction bundle {self.bundle.id} completed successfully")
            return response_bundle
            
        except Exception as e:
            logger.error(f"Transaction bundle {self.bundle.id} failed: {str(e)}")
            # Django transaction.atomic() fará rollback automático
            raise
    
    def _validate_bundle(self):
        """Valida estrutura do bundle"""
        if not self.bundle.entries:
            raise DRFValidationError('Bundle transaction deve ter pelo menos uma entry')
        
        for idx, entry in enumerate(self.bundle.entries):
            if 'request' not in entry:
                raise DRFValidationError(f'Entry {idx} deve ter campo "request"')
            
            if 'method' not in entry['request']:
                raise DRFValidationError(f'Entry {idx} request deve ter campo "method"')
            
            if 'url' not in entry['request']:
                raise DRFValidationError(f'Entry {idx} request deve ter campo "url"')
    
    def _process_entry(self, entry, idx):
        """
        Processa uma entry individual
        
        Args:
            entry (dict): BundleEntry FHIR
            idx (int): Índice da entry
        
        Returns:
            dict: Response entry
        """
        request_data = entry['request']
        method = request_data['method'].upper()
        url = request_data['url']
        resource = entry.get('resource')
        
        # Resolver referências internas (urn:uuid:xxx)
        if resource:
            resource = self._resolve_references(resource)
        
        # Executar operação conforme método HTTP
        if method == 'POST':
            return self._handle_post(url, resource, entry, idx)
        elif method == 'PUT':
            return self._handle_put(url, resource, entry, idx)
        elif method == 'PATCH':
            return self._handle_patch(url, resource, entry, idx)
        elif method == 'DELETE':
            return self._handle_delete(url, entry, idx)
        elif method == 'GET':
            return self._handle_get(url, entry, idx)
        else:
            raise DRFValidationError(f'Método HTTP não suportado: {method}')
    
    def _handle_post(self, url, resource, entry, idx):
        """Cria novo recurso"""
        from . import serializers_factory
        
        resource_type = resource.get('resourceType')
        
        # Obter serializer apropriado
        serializer_class = serializers_factory.get_serializer(resource_type)
        if not serializer_class:
            raise DRFValidationError(f'Tipo de recurso não suportado: {resource_type}')
        
        serializer = serializer_class(data=resource)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        
        # Registrar para resolução de referências
        full_url = entry.get('fullUrl')
        if full_url and full_url.startswith('urn:uuid:'):
            self.resource_registry[full_url] = f"{resource_type}/{instance.id}"
        
        # Criar response
        location = f"/{resource_type}/{instance.id}"
        return {
            'fullUrl': f"http://openehrcore.com/fhir{location}",
            'resource': serializer.data,
            'response': {
                'status': '201 Created',
                'location': location,
                'etag': f'W/"{instance.meta.version_id}"' if hasattr(instance, 'meta') else None,
                'lastModified': timezone.now().isoformat()
            }
        }
    
    def _handle_put(self, url, resource, entry, idx):
        """Atualiza recurso existente"""
        from . import serializers_factory, models_factory
        
        # Parsear URL (ex: "Patient/123")
        parts = url.split('/')
        if len(parts) < 2:
            raise DRFValidationError(f'URL inválida para PUT: {url}')
        
        resource_type = parts[0]
        resource_id = parts[1]
        
        # Obter model e serializer
        model_class = models_factory.get_model(resource_type)
        serializer_class = serializers_factory.get_serializer(resource_type)
        
        if not model_class or not serializer_class:
            raise DRFValidationError(f'Tipo de recurso não suportado: {resource_type}')
        
        # Buscar instância existente
        try:
            instance = model_class.objects.get(id=resource_id)
        except model_class.DoesNotExist:
            raise DRFValidationError(f'{resource_type}/{resource_id} não encontrado')
        
        # Atualizar
        serializer = serializer_class(instance, data=resource, partial=False)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        
        return {
            'fullUrl': f"http://openehrcore.com/fhir/{resource_type}/{instance.id}",
            'resource': serializer.data,
            'response': {
                'status': '200 OK',
                'etag': f'W/"{instance.meta.version_id}"' if hasattr(instance, 'meta') else None,
                'lastModified': timezone.now().isoformat()
            }
        }
    
    def _handle_patch(self, url, resource, entry, idx):
        """Atualização parcial"""
        from . import serializers_factory, models_factory
        
        parts = url.split('/')
        resource_type = parts[0]
        resource_id = parts[1]
        
        model_class = models_factory.get_model(resource_type)
        serializer_class = serializers_factory.get_serializer(resource_type)
        
        instance = model_class.objects.get(id=resource_id)
        serializer = serializer_class(instance, data=resource, partial=True)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        
        return {
            'fullUrl': f"http://openehrcore.com/fhir/{resource_type}/{instance.id}",
            'resource': serializer.data,
            'response': {
                'status': '200 OK',
                'lastModified': timezone.now().isoformat()
            }
        }
    
    def _handle_delete(self, url, entry, idx):
        """Deleta recurso"""
        from . import models_factory
        
        parts = url.split('/')
        resource_type = parts[0]
        resource_id = parts[1]
        
        model_class = models_factory.get_model(resource_type)
        instance = model_class.objects.get(id=resource_id)
        instance.delete()
        
        return {
            'response': {
                'status': '204 No Content'
            }
        }
    
    def _handle_get(self, url, entry, idx):
        """Busca recurso (não recomendado em transaction)"""
        raise DRFValidationError('GET não é permitido em Bundle do tipo transaction')
    
    def _resolve_references(self, resource):
        """
        Resolve referências urn:uuid:xxx para IDs reais
        
        Ex: { "subject": { "reference": "urn:uuid:abc-123" } }
        -> { "subject": { "reference": "Patient/real-id" } }
        """
        if isinstance(resource, dict):
            for key, value in resource.items():
                if key == 'reference' and isinstance(value, str) and value.startswith('urn:uuid:'):
                    if value in self.resource_registry:
                        resource[key] = self.resource_registry[value]
                elif isinstance(value, (dict, list)):
                    resource[key] = self._resolve_references(value)
        
        elif isinstance(resource, list):
            return [self._resolve_references(item) for item in resource]
        
        return resource


class BundleBatchProcessor:
    """
    Processa Bundle do tipo 'batch'
    Operações independentes, não faz rollback se uma falhar
    """
    
    def __init__(self, bundle):
        self.bundle = bundle
        self.results = []
    
    def process(self):
        """Processa batch bundle (sem transação atômica)"""
        logger.info(f"Processing batch bundle {self.bundle.id}")
        
        for idx, entry in enumerate(self.bundle.entries):
            try:
                # Processar entry individualmente (sem transaction.atomic)
                processor = BundleTransactionProcessor(self.bundle)
                result = processor._process_entry(entry, idx)
                self.results.append(result)
                
            except Exception as e:
                # Registrar erro mas continuar processando
                logger.error(f"Batch entry {idx} failed: {str(e)}")
                self.results.append({
                    'response': {
                        'status': '400 Bad Request',
                        'outcome': {
                            'resourceType': 'OperationOutcome',
                            'issue': [{
                                'severity': 'error',
                                'code': 'processing',
                                'diagnostics': str(e)
                            }]
                        }
                    }
                })
        
        response_bundle = {
            'resourceType': 'Bundle',
            'id': str(self.bundle.id),
            'type': 'batch-response',
            'timestamp': timezone.now().isoformat(),
            'entry': self.results
        }
        
        logger.info(f"Batch bundle {self.bundle.id} completed")
        return response_bundle
