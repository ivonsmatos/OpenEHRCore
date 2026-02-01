"""
AuditEvent and Provenance Models - FHIR R4

Sprint 36: Conformidade FHIR R4 - Audit Trail completo

Implementa:
- AuditEvent: Registro de eventos de segurança/acesso (ATNA)
- Provenance: Rastreabilidade de origem de dados

Conformidade:
- LGPD (Lei Geral de Proteção de Dados)
- HIPAA (Health Insurance Portability and Accountability Act)
- IHE ATNA (Audit Trail and Node Authentication)
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid
import json


class AuditEvent(models.Model):
    """
    FHIR AuditEvent Resource

    Registra eventos de segurança e acesso a dados.
    Baseado em DICOM/IHE ATNA.

    Tipos de eventos:
    - rest: Operações REST (CRUD)
    - security: Login/logout, autenticação
    - emergency: Acesso de emergência (break-glass)
    - consent: Alterações de consentimento
    - disclosure: Divulgação de dados
    """

    # Tipos de evento
    TYPE_CHOICES = [
        ('rest', 'RESTful Operation'),
        ('security', 'Security Administration'),
        ('emergency', 'Emergency Access'),
        ('consent', 'Consent Management'),
        ('disclosure', 'Data Disclosure'),
        ('query', 'Query/Search'),
        ('export', 'Data Export'),
        ('import', 'Data Import'),
        ('transmit', 'Data Transmission'),
    ]

    # Subtipos (para REST)
    SUBTYPE_REST_CHOICES = [
        ('create', 'Create'),
        ('read', 'Read'),
        ('vread', 'Version Read'),
        ('update', 'Update'),
        ('patch', 'Patch'),
        ('delete', 'Delete'),
        ('history', 'History'),
        ('search', 'Search'),
        ('batch', 'Batch'),
        ('transaction', 'Transaction'),
        ('operation', 'Operation'),
    ]

    # Ações CRUD
    ACTION_CHOICES = [
        ('C', 'Create'),
        ('R', 'Read'),
        ('U', 'Update'),
        ('D', 'Delete'),
        ('E', 'Execute'),
    ]

    # Resultados
    OUTCOME_CHOICES = [
        ('0', 'Success'),
        ('4', 'Minor failure'),
        ('8', 'Serious failure'),
        ('12', 'Major failure'),
    ]

    # Identificação
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Tipo e subtipo
    type_code = models.CharField(max_length=50, choices=TYPE_CHOICES, db_index=True)
    type_system = models.CharField(
        max_length=200,
        default='http://terminology.hl7.org/CodeSystem/audit-event-type'
    )
    subtype_code = models.CharField(max_length=50, blank=True, null=True)
    subtype_system = models.CharField(max_length=200, blank=True, null=True)

    # Ação e resultado
    action = models.CharField(max_length=1, choices=ACTION_CHOICES, db_index=True)
    outcome = models.CharField(max_length=2, choices=OUTCOME_CHOICES, default='0', db_index=True)
    outcome_desc = models.TextField(blank=True, null=True)

    # Timing
    recorded = models.DateTimeField(default=timezone.now, db_index=True)
    period_start = models.DateTimeField(blank=True, null=True)
    period_end = models.DateTimeField(blank=True, null=True)

    # Agente (quem fez)
    agent_type = models.CharField(max_length=50, default='humanuser')  # humanuser, machine, software
    agent_who_id = models.CharField(max_length=100, db_index=True)  # Reference
    agent_who_display = models.CharField(max_length=200, blank=True, null=True)
    agent_alt_id = models.CharField(max_length=100, blank=True, null=True)  # Username
    agent_name = models.CharField(max_length=200, blank=True, null=True)  # Nome completo
    agent_requestor = models.BooleanField(default=True)  # É quem iniciou?
    agent_network_address = models.CharField(max_length=100, blank=True, null=True)  # IP
    agent_network_type = models.CharField(max_length=10, default='2')  # 1=machine, 2=IP, 3=phone
    agent_role = models.JSONField(blank=True, null=True)  # CodeableConcept[]

    # Fonte (onde aconteceu)
    source_site = models.CharField(max_length=200, blank=True, null=True)  # Nome do sistema
    source_observer_id = models.CharField(max_length=100, blank=True, null=True)  # Device/System
    source_observer_display = models.CharField(max_length=200, blank=True, null=True)
    source_type = models.JSONField(blank=True, null=True)  # Coding[]

    # Entidade (o que foi acessado)
    entity_what_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)  # Reference
    entity_what_display = models.CharField(max_length=200, blank=True, null=True)
    entity_type = models.CharField(max_length=50, blank=True, null=True)  # Tipo de recurso
    entity_role = models.CharField(max_length=50, blank=True, null=True)  # patient, practitioner, etc
    entity_lifecycle = models.CharField(max_length=50, blank=True, null=True)  # create, update, etc
    entity_security_label = models.JSONField(blank=True, null=True)  # Coding[]
    entity_name = models.CharField(max_length=200, blank=True, null=True)
    entity_description = models.TextField(blank=True, null=True)
    entity_query = models.TextField(blank=True, null=True)  # Base64 da query

    # Paciente (se aplicável)
    patient_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)

    # Metadados adicionais
    purpose_of_use = models.JSONField(blank=True, null=True)  # CodeableConcept[]
    http_method = models.CharField(max_length=10, blank=True, null=True)
    http_url = models.TextField(blank=True, null=True)
    http_status = models.IntegerField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)

    # Django audit
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'fhir_audit_event'
        ordering = ['-recorded']
        indexes = [
            models.Index(fields=['type_code', 'recorded']),
            models.Index(fields=['agent_who_id', 'recorded']),
            models.Index(fields=['entity_what_id', 'recorded']),
            models.Index(fields=['patient_id', 'recorded']),
            models.Index(fields=['action', 'outcome', 'recorded']),
        ]

    def __str__(self):
        return f"AuditEvent {self.id}: {self.type_code}/{self.action} by {self.agent_name or self.agent_who_id}"

    def to_fhir(self) -> dict:
        """Converte para FHIR AuditEvent R4"""
        resource = {
            'resourceType': 'AuditEvent',
            'id': str(self.id),
            'type': {
                'system': self.type_system,
                'code': self.type_code,
                'display': dict(self.TYPE_CHOICES).get(self.type_code, self.type_code)
            },
            'action': self.action,
            'recorded': self.recorded.isoformat(),
            'outcome': self.outcome,
            'agent': [{
                'type': {
                    'coding': [{
                        'system': 'http://terminology.hl7.org/CodeSystem/extra-security-role-type',
                        'code': self.agent_type
                    }]
                },
                'who': {
                    'reference': self.agent_who_id,
                    'display': self.agent_who_display
                },
                'requestor': self.agent_requestor
            }],
            'source': {
                'site': self.source_site,
                'observer': {
                    'reference': self.source_observer_id,
                    'display': self.source_observer_display
                }
            }
        }

        # Subtipo
        if self.subtype_code:
            resource['subtype'] = [{
                'system': self.subtype_system or 'http://hl7.org/fhir/restful-interaction',
                'code': self.subtype_code
            }]

        # Outcome description
        if self.outcome_desc:
            resource['outcomeDesc'] = self.outcome_desc

        # Period
        if self.period_start or self.period_end:
            resource['period'] = {}
            if self.period_start:
                resource['period']['start'] = self.period_start.isoformat()
            if self.period_end:
                resource['period']['end'] = self.period_end.isoformat()

        # Agent details
        agent = resource['agent'][0]
        if self.agent_alt_id:
            agent['altId'] = self.agent_alt_id
        if self.agent_name:
            agent['name'] = self.agent_name
        if self.agent_network_address:
            agent['network'] = {
                'address': self.agent_network_address,
                'type': self.agent_network_type
            }
        if self.agent_role:
            agent['role'] = self.agent_role

        # Source type
        if self.source_type:
            resource['source']['type'] = self.source_type

        # Entity
        if self.entity_what_id:
            entity = {
                'what': {
                    'reference': self.entity_what_id,
                    'display': self.entity_what_display
                }
            }
            if self.entity_type:
                entity['type'] = {
                    'system': 'http://terminology.hl7.org/CodeSystem/audit-entity-type',
                    'code': self.entity_type
                }
            if self.entity_role:
                entity['role'] = {
                    'system': 'http://terminology.hl7.org/CodeSystem/object-role',
                    'code': self.entity_role
                }
            if self.entity_lifecycle:
                entity['lifecycle'] = {
                    'system': 'http://terminology.hl7.org/CodeSystem/dicom-audit-lifecycle',
                    'code': self.entity_lifecycle
                }
            if self.entity_security_label:
                entity['securityLabel'] = self.entity_security_label
            if self.entity_name:
                entity['name'] = self.entity_name
            if self.entity_description:
                entity['description'] = self.entity_description
            if self.entity_query:
                entity['query'] = self.entity_query

            resource['entity'] = [entity]

        # Purpose of use
        if self.purpose_of_use:
            resource['purposeOfEvent'] = self.purpose_of_use

        return resource

    @classmethod
    def log_rest_operation(
        cls,
        action: str,
        resource_type: str,
        resource_id: str,
        user: User,
        request,
        outcome: str = '0',
        outcome_desc: str = None,
        patient_id: str = None
    ) -> 'AuditEvent':
        """
        Helper para logar operações REST

        Args:
            action: C, R, U, D, E
            resource_type: Tipo do recurso (Patient, Observation, etc)
            resource_id: ID do recurso
            user: Usuário que fez a operação
            request: Django request
            outcome: 0=success, 4=minor, 8=serious, 12=major
            outcome_desc: Descrição do erro
            patient_id: ID do paciente (se aplicável)
        """
        # Mapeia action para subtype
        subtype_map = {
            'C': 'create',
            'R': 'read',
            'U': 'update',
            'D': 'delete',
            'E': 'operation'
        }

        audit = cls(
            type_code='rest',
            subtype_code=subtype_map.get(action, 'read'),
            subtype_system='http://hl7.org/fhir/restful-interaction',
            action=action,
            outcome=outcome,
            outcome_desc=outcome_desc,
            # Agent
            agent_who_id=f'Practitioner/{user.id}' if user else 'anonymous',
            agent_who_display=user.get_full_name() if user else 'Anonymous',
            agent_alt_id=user.username if user else None,
            agent_name=user.get_full_name() if user else None,
            agent_network_address=cls._get_client_ip(request) if request else None,
            # Source
            source_site='OpenEHRCore',
            source_observer_id='Device/openehrcore-server',
            source_observer_display='OpenEHRCore FHIR Server',
            # Entity
            entity_what_id=f'{resource_type}/{resource_id}',
            entity_type='2' if resource_type == 'Patient' else '1',  # 2=System Object, 1=Person
            entity_role='1' if resource_type == 'Patient' else '4',  # 1=patient, 4=domain
            entity_lifecycle=subtype_map.get(action),
            # Patient
            patient_id=patient_id,
            # HTTP
            http_method=request.method if request else None,
            http_url=request.get_full_path() if request else None,
            user_agent=request.META.get('HTTP_USER_AGENT') if request else None
        )
        audit.save()
        return audit

    @classmethod
    def log_security_event(
        cls,
        subtype: str,
        user: User,
        request,
        outcome: str = '0',
        outcome_desc: str = None
    ) -> 'AuditEvent':
        """Helper para logar eventos de segurança (login, logout, etc)"""
        audit = cls(
            type_code='security',
            subtype_code=subtype,
            action='E',
            outcome=outcome,
            outcome_desc=outcome_desc,
            agent_who_id=f'Practitioner/{user.id}' if user else 'anonymous',
            agent_who_display=user.get_full_name() if user else 'Anonymous',
            agent_alt_id=user.username if user else None,
            agent_network_address=cls._get_client_ip(request) if request else None,
            source_site='OpenEHRCore',
            source_observer_id='Device/openehrcore-server',
        )
        audit.save()
        return audit

    @staticmethod
    def _get_client_ip(request) -> str:
        """Extrai IP do cliente do request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '')


class Provenance(models.Model):
    """
    FHIR Provenance Resource

    Registra a origem e cadeia de custódia de dados.
    Essencial para rastreabilidade em saúde.
    """

    # Atividades
    ACTIVITY_CHOICES = [
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('IMPORT', 'Import'),
        ('TRANSFORM', 'Transform'),
        ('MERGE', 'Merge'),
        ('SPLIT', 'Split'),
        ('TRANSMIT', 'Transmit'),
        ('VERIFY', 'Verify'),
        ('ATTEST', 'Attest'),
        ('SIGN', 'Sign'),
    ]

    # Roles do agente
    AGENT_ROLE_CHOICES = [
        ('author', 'Author'),
        ('performer', 'Performer'),
        ('verifier', 'Verifier'),
        ('attester', 'Attester'),
        ('informant', 'Informant'),
        ('custodian', 'Custodian'),
        ('assembler', 'Assembler'),
        ('composer', 'Composer'),
    ]

    # Identificação
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Target (o que tem essa provenance)
    target = models.JSONField(help_text='Array de References aos recursos')

    # Timing
    occurred_datetime = models.DateTimeField(blank=True, null=True)
    occurred_period_start = models.DateTimeField(blank=True, null=True)
    occurred_period_end = models.DateTimeField(blank=True, null=True)
    recorded = models.DateTimeField(default=timezone.now, db_index=True)

    # Localização
    location_id = models.CharField(max_length=100, blank=True, null=True)
    location_display = models.CharField(max_length=200, blank=True, null=True)

    # Policy/Reason
    policy = models.JSONField(blank=True, null=True)  # Array de URIs
    reason = models.JSONField(blank=True, null=True)  # Array de CodeableConcept

    # Atividade
    activity_code = models.CharField(max_length=50, choices=ACTIVITY_CHOICES, db_index=True)
    activity_system = models.CharField(
        max_length=200,
        default='http://terminology.hl7.org/CodeSystem/v3-DataOperation'
    )

    # Agentes (stored as JSON array)
    agents = models.JSONField(
        help_text='Array de agentes: [{type, role, who, onBehalfOf}]'
    )

    # Entidades fonte (stored as JSON array)
    entities = models.JSONField(
        blank=True,
        null=True,
        help_text='Array de entidades fonte: [{role, what}]'
    )

    # Assinatura digital
    signature = models.JSONField(blank=True, null=True)

    # Django audit
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_provenances'
    )

    class Meta:
        db_table = 'fhir_provenance'
        ordering = ['-recorded']
        indexes = [
            models.Index(fields=['activity_code', 'recorded']),
            models.Index(fields=['recorded']),
        ]

    def __str__(self):
        targets = self.target if isinstance(self.target, list) else [self.target]
        target_str = targets[0].get('reference', 'Unknown') if targets else 'Unknown'
        return f"Provenance {self.id}: {self.activity_code} on {target_str}"

    def to_fhir(self) -> dict:
        """Converte para FHIR Provenance R4"""
        resource = {
            'resourceType': 'Provenance',
            'id': str(self.id),
            'target': self.target if isinstance(self.target, list) else [self.target],
            'recorded': self.recorded.isoformat(),
            'activity': {
                'coding': [{
                    'system': self.activity_system,
                    'code': self.activity_code,
                    'display': dict(self.ACTIVITY_CHOICES).get(self.activity_code)
                }]
            },
            'agent': self.agents if isinstance(self.agents, list) else [self.agents]
        }

        # Occurred
        if self.occurred_datetime:
            resource['occurredDateTime'] = self.occurred_datetime.isoformat()
        elif self.occurred_period_start or self.occurred_period_end:
            resource['occurredPeriod'] = {}
            if self.occurred_period_start:
                resource['occurredPeriod']['start'] = self.occurred_period_start.isoformat()
            if self.occurred_period_end:
                resource['occurredPeriod']['end'] = self.occurred_period_end.isoformat()

        # Location
        if self.location_id:
            resource['location'] = {
                'reference': self.location_id,
                'display': self.location_display
            }

        # Policy
        if self.policy:
            resource['policy'] = self.policy if isinstance(self.policy, list) else [self.policy]

        # Reason
        if self.reason:
            resource['reason'] = self.reason if isinstance(self.reason, list) else [self.reason]

        # Entity
        if self.entities:
            resource['entity'] = self.entities if isinstance(self.entities, list) else [self.entities]

        # Signature
        if self.signature:
            resource['signature'] = self.signature if isinstance(self.signature, list) else [self.signature]

        return resource

    @classmethod
    def record_creation(
        cls,
        resource_type: str,
        resource_id: str,
        user: User,
        source_data: dict = None
    ) -> 'Provenance':
        """
        Helper para registrar provenance de criação

        Args:
            resource_type: Tipo do recurso criado
            resource_id: ID do recurso criado
            user: Usuário que criou
            source_data: Dados de origem (se importado)
        """
        agents = [{
            'type': {
                'coding': [{
                    'system': 'http://terminology.hl7.org/CodeSystem/provenance-participant-type',
                    'code': 'author'
                }]
            },
            'who': {
                'reference': f'Practitioner/{user.id}',
                'display': user.get_full_name()
            }
        }]

        entities = None
        if source_data:
            entities = [{
                'role': 'source',
                'what': source_data
            }]

        provenance = cls(
            target=[{'reference': f'{resource_type}/{resource_id}'}],
            occurred_datetime=timezone.now(),
            activity_code='CREATE',
            agents=agents,
            entities=entities,
            created_by=user
        )
        provenance.save()
        return provenance

    @classmethod
    def record_update(
        cls,
        resource_type: str,
        resource_id: str,
        user: User,
        previous_version: str = None
    ) -> 'Provenance':
        """Helper para registrar provenance de atualização"""
        agents = [{
            'type': {
                'coding': [{
                    'system': 'http://terminology.hl7.org/CodeSystem/provenance-participant-type',
                    'code': 'performer'
                }]
            },
            'who': {
                'reference': f'Practitioner/{user.id}',
                'display': user.get_full_name()
            }
        }]

        entities = None
        if previous_version:
            entities = [{
                'role': 'revision',
                'what': {
                    'reference': f'{resource_type}/{resource_id}/_history/{previous_version}'
                }
            }]

        provenance = cls(
            target=[{'reference': f'{resource_type}/{resource_id}'}],
            occurred_datetime=timezone.now(),
            activity_code='UPDATE',
            agents=agents,
            entities=entities,
            created_by=user
        )
        provenance.save()
        return provenance

    @classmethod
    def record_import(
        cls,
        resource_type: str,
        resource_id: str,
        user: User,
        source_system: str,
        source_reference: str
    ) -> 'Provenance':
        """Helper para registrar provenance de importação"""
        agents = [
            {
                'type': {
                    'coding': [{
                        'system': 'http://terminology.hl7.org/CodeSystem/provenance-participant-type',
                        'code': 'performer'
                    }]
                },
                'who': {
                    'reference': f'Practitioner/{user.id}',
                    'display': user.get_full_name()
                }
            },
            {
                'type': {
                    'coding': [{
                        'system': 'http://terminology.hl7.org/CodeSystem/provenance-participant-type',
                        'code': 'custodian'
                    }]
                },
                'who': {
                    'reference': f'Organization/{source_system}',
                    'display': source_system
                }
            }
        ]

        entities = [{
            'role': 'source',
            'what': {
                'reference': source_reference,
                'display': f'Imported from {source_system}'
            }
        }]

        provenance = cls(
            target=[{'reference': f'{resource_type}/{resource_id}'}],
            occurred_datetime=timezone.now(),
            activity_code='IMPORT',
            agents=agents,
            entities=entities,
            created_by=user
        )
        provenance.save()
        return provenance
