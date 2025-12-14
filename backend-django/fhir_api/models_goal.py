"""
Goal Models - FHIR R4

Sprint 35: Goal Resource standalone para objetivos terapêuticos
Resource independente (separado de CarePlan) com tracking de progresso
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
import uuid


class Goal(models.Model):
    """
    FHIR Goal Resource
    
    Objetivos terapêuticos para o paciente.
    Pode ser parte de um CarePlan ou independente.
    
    Campos principais:
    - lifecycleStatus: proposed | planned | accepted | active | on-hold | completed
                      | cancelled | entered-in-error | rejected
    - achievementStatus: in-progress | improving | worsening | no-change | achieved
                         | sustaining | not-achieved | no-progress | not-attainable
    - category: dietary | safety | behavioral | nursing | physiotherapy | etc
    - description: O que se quer alcançar
    - subject: Patient (required)
    - target: Medidas objetivas (value, date)
    - statusDate: Quando o status mudou
    - addresses: Condições/Observações relacionadas
    """
    
    LIFECYCLE_STATUS_CHOICES = [
        ('proposed', 'Proposed'),
        ('planned', 'Planned'),
        ('accepted', 'Accepted'),
        ('active', 'Active'),
        ('on-hold', 'On Hold'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('entered-in-error', 'Entered in Error'),
        ('rejected', 'Rejected'),
    ]
    
    ACHIEVEMENT_STATUS_CHOICES = [
        ('in-progress', 'In Progress'),
        ('improving', 'Improving'),
        ('worsening', 'Worsening'),
        ('no-change', 'No Change'),
        ('achieved', 'Achieved'),
        ('sustaining', 'Sustaining'),
        ('not-achieved', 'Not Achieved'),
        ('no-progress', 'No Progress'),
        ('not-attainable', 'Not Attainable'),
    ]
    
    PRIORITY_CHOICES = [
        ('high-priority', 'High Priority'),
        ('medium-priority', 'Medium Priority'),
        ('low-priority', 'Low Priority'),
    ]
    
    # Identificação
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    identifier = models.CharField(max_length=100, unique=True, db_index=True)
    
    # Status
    lifecycle_status = models.CharField(max_length=20, choices=LIFECYCLE_STATUS_CHOICES, default='proposed', db_index=True)
    achievement_status = models.CharField(max_length=20, choices=ACHIEVEMENT_STATUS_CHOICES, null=True, blank=True, db_index=True)
    
    # Categoria e prioridade
    category = models.JSONField(null=True, blank=True)  # Array of CodeableConcept
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, null=True, blank=True)
    
    # Descrição do objetivo
    description = models.JSONField()  # CodeableConcept (required)
    
    # Paciente
    subject_id = models.CharField(max_length=100, db_index=True)  # Reference Patient (required)
    
    # Datas importantes
    start_date = models.DateField(null=True, blank=True, db_index=True)
    status_date = models.DateField(null=True, blank=True)  # Quando status mudou
    
    # Contexto
    expressed_by_id = models.CharField(max_length=100, null=True, blank=True)  # Reference to who set the goal
    expressed_by_display = models.CharField(max_length=200, null=True, blank=True)
    
    # Endereços (condições/problemas que este goal aborda)
    addresses = models.JSONField(null=True, blank=True)  # Array of References to Condition/Observation
    
    # Notas
    note = models.TextField(null=True, blank=True)
    
    # Status reason
    status_reason = models.TextField(null=True, blank=True)
    
    # Auditoria
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_goals')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'fhir_goal'
        ordering = ['-start_date', '-created_at']
        indexes = [
            models.Index(fields=['subject_id', 'lifecycle_status']),
            models.Index(fields=['lifecycle_status', 'start_date']),
            models.Index(fields=['achievement_status']),
        ]
    
    def __str__(self):
        desc = self.description.get('text', 'Goal') if isinstance(self.description, dict) else 'Goal'
        return f"Goal {self.identifier}: {desc[:50]} ({self.lifecycle_status})"
    
    def clean(self):
        """Validações customizadas"""
        # Description é obrigatório
        if not self.description:
            raise ValidationError("Description is required")
        
        # Completed/achieved goals should have achievement_status
        if self.lifecycle_status == 'completed' and not self.achievement_status:
            raise ValidationError("Achievement status is required for completed goals")
        
        # Status date validation
        if self.status_date and self.start_date:
            if self.status_date < self.start_date:
                raise ValidationError("Status date cannot be before start date")
    
    def save(self, *args, **kwargs):
        # Gerar identifier se não existir
        if not self.identifier:
            self.identifier = f"GOAL-{self.id}"
        
        # Auto-set status_date when lifecycle_status changes
        if self.pk:
            old_goal = Goal.objects.get(pk=self.pk)
            if old_goal.lifecycle_status != self.lifecycle_status:
                self.status_date = timezone.now().date()
        
        self.full_clean()
        super().save(*args, **kwargs)
    
    def to_fhir(self):
        """
        Converte para FHIR Goal R4
        """
        resource = {
            'resourceType': 'Goal',
            'id': str(self.id),
            'identifier': [{
                'system': 'http://openehrcore.com.br/fhir/goal',
                'value': self.identifier
            }],
            'lifecycleStatus': self.lifecycle_status,
            'description': self.description,
            'subject': {
                'reference': f'Patient/{self.subject_id}'
            }
        }
        
        # Achievement status
        if self.achievement_status:
            resource['achievementStatus'] = {
                'coding': [{
                    'system': 'http://terminology.hl7.org/CodeSystem/goal-achievement',
                    'code': self.achievement_status,
                    'display': dict(self.ACHIEVEMENT_STATUS_CHOICES)[self.achievement_status]
                }]
            }
        
        # Category
        if self.category:
            resource['category'] = self.category if isinstance(self.category, list) else [self.category]
        
        # Priority
        if self.priority:
            resource['priority'] = {
                'coding': [{
                    'system': 'http://terminology.hl7.org/CodeSystem/goal-priority',
                    'code': self.priority,
                    'display': dict(self.PRIORITY_CHOICES)[self.priority]
                }]
            }
        
        # Start date
        if self.start_date:
            resource['startDate'] = self.start_date.isoformat()
        
        # Status date
        if self.status_date:
            resource['statusDate'] = self.status_date.isoformat()
        
        # Expressed by
        if self.expressed_by_id:
            resource['expressedBy'] = {'reference': self.expressed_by_id}
            if self.expressed_by_display:
                resource['expressedBy']['display'] = self.expressed_by_display
        
        # Addresses
        if self.addresses:
            resource['addresses'] = self.addresses if isinstance(self.addresses, list) else [self.addresses]
        
        # Note
        if self.note:
            resource['note'] = [{
                'text': self.note,
                'time': self.updated_at.isoformat()
            }]
        
        # Status reason
        if self.status_reason:
            resource['statusReason'] = self.status_reason
        
        return resource


class GoalTarget(models.Model):
    """
    Goal Target - medidas objetivas do objetivo
    
    Exemplos:
    - HbA1c < 7%
    - Peso: 75kg
    - Pressão arterial < 140/90
    - Caminhada: 30min/dia
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    goal = models.ForeignKey(Goal, on_delete=models.CASCADE, related_name='targets')
    
    # Medida
    measure = models.JSONField(null=True, blank=True)  # CodeableConcept (opcional)
    
    # Valor alvo
    detail_quantity_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    detail_quantity_unit = models.CharField(max_length=50, null=True, blank=True)
    detail_quantity_comparator = models.CharField(max_length=10, null=True, blank=True)  # <, <=, >=, >
    
    detail_range_low = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    detail_range_high = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    detail_codeable_concept = models.JSONField(null=True, blank=True)  # CodeableConcept
    detail_string = models.CharField(max_length=500, null=True, blank=True)
    detail_boolean = models.BooleanField(null=True, blank=True)
    detail_integer = models.IntegerField(null=True, blank=True)
    detail_ratio = models.JSONField(null=True, blank=True)  # Ratio
    
    # Data alvo
    due_date = models.DateField(null=True, blank=True)
    due_duration = models.JSONField(null=True, blank=True)  # Duration
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'fhir_goal_target'
        ordering = ['due_date']
    
    def __str__(self):
        if self.detail_quantity_value:
            comparator = self.detail_quantity_comparator or ''
            return f"{comparator}{self.detail_quantity_value} {self.detail_quantity_unit}"
        elif self.detail_string:
            return self.detail_string
        elif self.detail_range_low and self.detail_range_high:
            return f"{self.detail_range_low}-{self.detail_range_high}"
        return "Target"
    
    def to_fhir(self):
        """Converte para FHIR Goal.target"""
        target = {}
        
        # Measure
        if self.measure:
            target['measure'] = self.measure
        
        # Detail (apenas um tipo permitido)
        if self.detail_quantity_value is not None:
            detail = {
                'value': float(self.detail_quantity_value),
                'unit': self.detail_quantity_unit or 'unit',
                'system': 'http://unitsofmeasure.org',
                'code': self.detail_quantity_unit or '{unit}'
            }
            if self.detail_quantity_comparator:
                detail['comparator'] = self.detail_quantity_comparator
            target['detailQuantity'] = detail
        
        elif self.detail_range_low is not None or self.detail_range_high is not None:
            detail_range = {}
            if self.detail_range_low is not None:
                detail_range['low'] = {
                    'value': float(self.detail_range_low),
                    'unit': self.detail_quantity_unit or 'unit'
                }
            if self.detail_range_high is not None:
                detail_range['high'] = {
                    'value': float(self.detail_range_high),
                    'unit': self.detail_quantity_unit or 'unit'
                }
            target['detailRange'] = detail_range
        
        elif self.detail_codeable_concept:
            target['detailCodeableConcept'] = self.detail_codeable_concept
        
        elif self.detail_string:
            target['detailString'] = self.detail_string
        
        elif self.detail_boolean is not None:
            target['detailBoolean'] = self.detail_boolean
        
        elif self.detail_integer is not None:
            target['detailInteger'] = self.detail_integer
        
        elif self.detail_ratio:
            target['detailRatio'] = self.detail_ratio
        
        # Due
        if self.due_date:
            target['dueDate'] = self.due_date.isoformat()
        elif self.due_duration:
            target['dueDuration'] = self.due_duration
        
        return target
