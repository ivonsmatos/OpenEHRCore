"""
Task Models - FHIR R4

Sprint 34: Task Resource para gerenciamento genérico de workflow
Resource independente para tarefas além de referrals
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
import uuid


class Task(models.Model):
    """
    FHIR Task Resource
    
    Gerenciamento genérico de tarefas e workflow.
    Pode ser usado para: referrals, ordens de exames, solicitações de documentos,
    aprovações, follow-ups, etc.
    
    Campos principais:
    - status: draft | requested | received | accepted | rejected | ready | cancelled
              | in-progress | on-hold | failed | completed | entered-in-error
    - intent: unknown | proposal | plan | order | original-order | reflex-order
              | filler-order | instance-order | option
    - businessStatus: Contexto específico do negócio (ex: "aguardando aprovação")
    - code: Tipo de tarefa (review-results, fulfill-order, etc)
    - focus: Recurso principal (ServiceRequest, MedicationRequest, etc)
    - for: Beneficiário (Patient)
    - owner: Responsável atual
    - requester: Quem solicitou
    """
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('requested', 'Requested'),
        ('received', 'Received'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('ready', 'Ready'),
        ('cancelled', 'Cancelled'),
        ('in-progress', 'In Progress'),
        ('on-hold', 'On Hold'),
        ('failed', 'Failed'),
        ('completed', 'Completed'),
        ('entered-in-error', 'Entered in Error'),
    ]
    
    INTENT_CHOICES = [
        ('unknown', 'Unknown'),
        ('proposal', 'Proposal'),
        ('plan', 'Plan'),
        ('order', 'Order'),
        ('original-order', 'Original Order'),
        ('reflex-order', 'Reflex Order'),
        ('filler-order', 'Filler Order'),
        ('instance-order', 'Instance Order'),
        ('option', 'Option'),
    ]
    
    PRIORITY_CHOICES = [
        ('routine', 'Routine'),
        ('urgent', 'Urgent'),
        ('asap', 'ASAP'),
        ('stat', 'STAT'),
    ]
    
    # Identificação
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    identifier = models.CharField(max_length=100, unique=True, db_index=True)
    
    # Status workflow
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='requested', db_index=True)
    status_reason = models.JSONField(null=True, blank=True)  # CodeableConcept
    business_status = models.JSONField(null=True, blank=True)  # CodeableConcept - specific to context
    
    # Intent e prioridade
    intent = models.CharField(max_length=20, choices=INTENT_CHOICES, default='order')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='routine', db_index=True)
    
    # Tipo de tarefa
    code = models.JSONField(null=True, blank=True)  # CodeableConcept
    description = models.TextField(null=True, blank=True)
    
    # Contexto
    focus = models.CharField(max_length=200, null=True, blank=True, db_index=True)  # Reference to main resource
    for_patient_id = models.CharField(max_length=100, null=True, blank=True, db_index=True)  # Reference Patient
    encounter_id = models.CharField(max_length=100, null=True, blank=True, db_index=True)  # Reference Encounter
    
    # Timing
    authored_on = models.DateTimeField(auto_now_add=True, db_index=True)
    last_modified = models.DateTimeField(auto_now=True)
    execution_period_start = models.DateTimeField(null=True, blank=True)
    execution_period_end = models.DateTimeField(null=True, blank=True)
    
    # Responsabilidades
    requester_id = models.CharField(max_length=100, null=True, blank=True, db_index=True)  # Reference
    requester_display = models.CharField(max_length=200, null=True, blank=True)
    owner_id = models.CharField(max_length=100, null=True, blank=True, db_index=True)  # Reference
    owner_display = models.CharField(max_length=200, null=True, blank=True)
    
    # Relacionamentos
    based_on = models.JSONField(null=True, blank=True)  # Array of References (CarePlan, etc)
    part_of = models.JSONField(null=True, blank=True)  # Array of References to parent Tasks
    
    # Restrições
    restriction_period_start = models.DateTimeField(null=True, blank=True)
    restriction_period_end = models.DateTimeField(null=True, blank=True)
    restriction_repetitions = models.IntegerField(null=True, blank=True)
    restriction_recipient = models.JSONField(null=True, blank=True)  # Array of References
    
    # Inputs e Outputs
    input = models.JSONField(null=True, blank=True)  # Array of {type, value}
    output = models.JSONField(null=True, blank=True)  # Array of {type, value}
    
    # Notas
    note = models.TextField(null=True, blank=True)
    
    # Auditoria
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_tasks')
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'fhir_task'
        ordering = ['-priority', '-authored_on']
        indexes = [
            models.Index(fields=['status', 'priority', 'authored_on']),
            models.Index(fields=['owner_id', 'status']),
            models.Index(fields=['for_patient_id', 'status']),
            models.Index(fields=['focus']),
        ]
    
    def __str__(self):
        desc = self.description[:50] if self.description else 'Task'
        return f"Task {self.identifier}: {desc} ({self.status})"
    
    def clean(self):
        """Validações customizadas"""
        # Execution period validation
        if self.execution_period_start and self.execution_period_end:
            if self.execution_period_end <= self.execution_period_start:
                raise ValidationError("Execution period end must be after start")
        
        # Restriction period validation
        if self.restriction_period_start and self.restriction_period_end:
            if self.restriction_period_end <= self.restriction_period_start:
                raise ValidationError("Restriction period end must be after start")
        
        # Status transitions
        if self.pk:  # Updating existing task
            old_task = Task.objects.get(pk=self.pk)
            if not self._is_valid_status_transition(old_task.status, self.status):
                raise ValidationError(f"Invalid status transition from {old_task.status} to {self.status}")
    
    def _is_valid_status_transition(self, old_status, new_status):
        """Valida transições de status permitidas"""
        # Draft pode ir para qualquer status
        if old_status == 'draft':
            return True
        
        # Entered-in-error é terminal
        if old_status == 'entered-in-error':
            return False
        
        # Completed é terminal (exceto entered-in-error)
        if old_status == 'completed' and new_status != 'entered-in-error':
            return False
        
        # Failed é terminal (exceto entered-in-error)
        if old_status == 'failed' and new_status != 'entered-in-error':
            return False
        
        # Cancelled é terminal (exceto entered-in-error)
        if old_status == 'cancelled' and new_status != 'entered-in-error':
            return False
        
        # Rejected é terminal (exceto entered-in-error)
        if old_status == 'rejected' and new_status != 'entered-in-error':
            return False
        
        return True
    
    def save(self, *args, **kwargs):
        # Gerar identifier se não existir
        if not self.identifier:
            self.identifier = f"TASK-{self.id}"
        
        self.full_clean()
        super().save(*args, **kwargs)
    
    def to_fhir(self):
        """
        Converte para FHIR Task R4
        """
        resource = {
            'resourceType': 'Task',
            'id': str(self.id),
            'identifier': [{
                'system': 'http://openehrcore.com.br/fhir/task',
                'value': self.identifier
            }],
            'status': self.status,
            'intent': self.intent,
            'priority': self.priority,
            'authoredOn': self.authored_on.isoformat(),
            'lastModified': self.last_modified.isoformat()
        }
        
        # Status reason
        if self.status_reason:
            resource['statusReason'] = self.status_reason
        
        # Business status
        if self.business_status:
            resource['businessStatus'] = self.business_status
        
        # Code
        if self.code:
            resource['code'] = self.code
        
        # Description
        if self.description:
            resource['description'] = self.description
        
        # Focus
        if self.focus:
            resource['focus'] = {'reference': self.focus}
        
        # For (patient)
        if self.for_patient_id:
            resource['for'] = {'reference': f'Patient/{self.for_patient_id}'}
        
        # Encounter
        if self.encounter_id:
            resource['encounter'] = {'reference': f'Encounter/{self.encounter_id}'}
        
        # Execution period
        if self.execution_period_start or self.execution_period_end:
            resource['executionPeriod'] = {}
            if self.execution_period_start:
                resource['executionPeriod']['start'] = self.execution_period_start.isoformat()
            if self.execution_period_end:
                resource['executionPeriod']['end'] = self.execution_period_end.isoformat()
        
        # Requester
        if self.requester_id:
            resource['requester'] = {'reference': self.requester_id}
            if self.requester_display:
                resource['requester']['display'] = self.requester_display
        
        # Owner
        if self.owner_id:
            resource['owner'] = {'reference': self.owner_id}
            if self.owner_display:
                resource['owner']['display'] = self.owner_display
        
        # Based on
        if self.based_on:
            resource['basedOn'] = self.based_on if isinstance(self.based_on, list) else [self.based_on]
        
        # Part of
        if self.part_of:
            resource['partOf'] = self.part_of if isinstance(self.part_of, list) else [self.part_of]
        
        # Restriction
        if any([self.restriction_period_start, self.restriction_period_end, self.restriction_repetitions, self.restriction_recipient]):
            restriction = {}
            
            if self.restriction_period_start or self.restriction_period_end:
                restriction['period'] = {}
                if self.restriction_period_start:
                    restriction['period']['start'] = self.restriction_period_start.isoformat()
                if self.restriction_period_end:
                    restriction['period']['end'] = self.restriction_period_end.isoformat()
            
            if self.restriction_repetitions:
                restriction['repetitions'] = self.restriction_repetitions
            
            if self.restriction_recipient:
                restriction['recipient'] = self.restriction_recipient if isinstance(self.restriction_recipient, list) else [self.restriction_recipient]
            
            resource['restriction'] = restriction
        
        # Input
        if self.input:
            resource['input'] = self.input if isinstance(self.input, list) else [self.input]
        
        # Output
        if self.output:
            resource['output'] = self.output if isinstance(self.output, list) else [self.output]
        
        # Note
        if self.note:
            resource['note'] = [{
                'text': self.note,
                'time': self.last_modified.isoformat()
            }]
        
        return resource
