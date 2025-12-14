"""
FHIR CarePlan Implementation - Sprint 33
HL7 FHIR R4 - CarePlan Resource

Features:
- Care coordination for multi-disciplinary teams
- Goal-based care planning
- Activity scheduling and tracking
- Team member assignments
- Status workflow (draft → active → completed)
- Audit trail for LGPD compliance
"""

from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
import uuid


class CarePlan(models.Model):
    """FHIR R4 CarePlan Resource"""
    
    STATUS_CHOICES = [
        ('draft', 'Rascunho'),
        ('active', 'Ativo'),
        ('on-hold', 'Em Espera'),
        ('revoked', 'Revogado'),
        ('completed', 'Completo'),
        ('entered-in-error', 'Erro de Entrada'),
        ('unknown', 'Desconhecido'),
    ]
    
    INTENT_CHOICES = [
        ('proposal', 'Proposta'),
        ('plan', 'Plano'),
        ('order', 'Ordem'),
        ('option', 'Opção'),
    ]
    
    CATEGORY_CHOICES = [
        ('assess-plan', 'Assessment and Plan'),
        ('careteam', 'Care Team Coordination'),
        ('episodeofcare', 'Episode of Care'),
        ('longitudinal', 'Longitudinal Care'),
        ('multidisciplinary', 'Multidisciplinary Care'),
        ('perioperative', 'Perioperative Care'),
        ('rehabilitation', 'Rehabilitation'),
        ('other', 'Other'),
    ]
    
    # Identificadores
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    identifier = models.CharField(max_length=255, unique=True, blank=True, null=True)
    
    # Status e Intent
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    intent = models.CharField(max_length=20, choices=INTENT_CHOICES, default='plan')
    
    # Categorias (pode ter múltiplas)
    categories = models.JSONField(
        default=list,
        blank=True
    )
    
    # Título e Descrição
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    
    # Paciente (subject) - Referência FHIR
    patient_reference = models.JSONField(
        help_text='Referência FHIR ao paciente: {"reference": "Patient/123", "display": "Nome"}'
    )
    
    # Encontro associado - Referência FHIR
    encounter_reference = models.JSONField(
        null=True,
        blank=True,
        help_text='Referência FHIR ao encontro: Encounter'
    )
    
    # Período de validade
    period_start = models.DateTimeField()
    period_end = models.DateTimeField(blank=True, null=True)
    
    # Criador do plano
    author = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='authored_careplans'
    )
    
    # Equipe de cuidado - Referência FHIR
    care_team_reference = models.JSONField(
        null=True,
        blank=True,
        help_text='Referência FHIR à equipe: CareTeam'
    )
    
    # Endereços (references a outros recursos)
    addresses = models.JSONField(
        default=list,
        help_text='Condições/problemas que o plano endereça'
    )
    
    # Objetivos
    goals = models.JSONField(
        default=list,
        help_text='Array de referências para Goal resources'
    )
    
    # Notas
    notes = models.TextField(blank=True, null=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_careplans'
    )
    
    class Meta:
        verbose_name = 'Care Plan'
        verbose_name_plural = 'Care Plans'
        ordering = ['-period_start']
        indexes = [
            models.Index(fields=['status', '-period_start']),
            models.Index(fields=['author', '-created_at']),
        ]
    
    def __str__(self):
        patient_display = self.patient_reference.get('display', 'N/A') if self.patient_reference else 'N/A'
        return f"{self.title} - {patient_display}"
    
    def clean(self):
        """Validações customizadas"""
        super().clean()
        
        # Period_end deve ser após period_start
        if self.period_end and self.period_start:
            if self.period_end < self.period_start:
                raise ValidationError('period_end deve ser posterior a period_start')
        
        # Status transitions
        if self.pk:  # Já existe
            old_instance = CarePlan.objects.get(pk=self.pk)
            invalid_transitions = {
                'completed': ['draft', 'active'],  # Completed não pode voltar
                'revoked': ['draft', 'active'],    # Revoked não pode voltar
            }
            
            if old_instance.status in invalid_transitions:
                if self.status in invalid_transitions[old_instance.status]:
                    raise ValidationError(
                        f'Transição inválida: {old_instance.status} → {self.status}'
                    )
    
    def to_fhir(self):
        """Converte para formato FHIR R4"""
        fhir_careplan = {
            'resourceType': 'CarePlan',
            'id': str(self.id),
            'status': self.status,
            'intent': self.intent,
            'title': self.title,
            'subject': self.patient_reference if self.patient_reference else {'reference': 'Patient/unknown'},
            'period': {
                'start': self.period_start.isoformat(),
            }
        }
        
        # Identifier
        if self.identifier:
            fhir_careplan['identifier'] = [{
                'system': 'http://openehrcore.com/fhir/CarePlan',
                'value': self.identifier
            }]
        
        # Categories
        if self.categories:
            fhir_careplan['category'] = [
                {
                    'coding': [{
                        'system': 'http://hl7.org/fhir/us/core/CodeSystem/careplan-category',
                        'code': cat,
                        'display': dict(self.CATEGORY_CHOICES).get(cat, cat)
                    }]
                }
                for cat in self.categories
            ]
        
        # Period end
        if self.period_end:
            fhir_careplan['period']['end'] = self.period_end.isoformat()
        
        # Description
        if self.description:
            fhir_careplan['description'] = self.description
        
        # Encounter
        if self.encounter_reference:
            fhir_careplan['encounter'] = self.encounter_reference
        
        # Author
        if self.author:
            fhir_careplan['author'] = {
                'reference': f"Practitioner/{self.author.id}",
                'display': self.author.get_full_name()
            }
        
        # Care Team
        if self.care_team_reference:
            fhir_careplan['careTeam'] = [self.care_team_reference]
        
        # Addresses
        if self.addresses:
            fhir_careplan['addresses'] = self.addresses
        
        # Goals
        if self.goals:
            fhir_careplan['goal'] = self.goals
        
        # Activities
        activities = self.activities.all()
        if activities:
            fhir_careplan['activity'] = [
                activity.to_fhir_activity()
                for activity in activities
            ]
        
        # Notes
        if self.notes:
            fhir_careplan['note'] = [{
                'text': self.notes,
                'time': self.updated_at.isoformat()
            }]
        
        return fhir_careplan


class CarePlanActivity(models.Model):
    """FHIR CarePlan.activity"""
    
    STATUS_CHOICES = [
        ('not-started', 'Não Iniciado'),
        ('scheduled', 'Agendado'),
        ('in-progress', 'Em Progresso'),
        ('on-hold', 'Em Espera'),
        ('completed', 'Completo'),
        ('cancelled', 'Cancelado'),
        ('stopped', 'Parado'),
        ('unknown', 'Desconhecido'),
        ('entered-in-error', 'Erro de Entrada'),
    ]
    
    KIND_CHOICES = [
        ('Appointment', 'Consulta'),
        ('CommunicationRequest', 'Solicitação de Comunicação'),
        ('DeviceRequest', 'Solicitação de Dispositivo'),
        ('MedicationRequest', 'Prescrição'),
        ('NutritionOrder', 'Ordem de Nutrição'),
        ('Task', 'Tarefa'),
        ('ServiceRequest', 'Solicitação de Serviço'),
        ('VisionPrescription', 'Prescrição de Visão'),
    ]
    
    # Identificadores
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # CarePlan pai
    care_plan = models.ForeignKey(
        CarePlan,
        on_delete=models.CASCADE,
        related_name='activities'
    )
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not-started')
    
    # Outcome (código SNOMED/LOINC)
    outcome_codeable_concept = models.JSONField(blank=True, null=True)
    outcome_reference = models.JSONField(blank=True, null=True)
    
    # Progress notes
    progress = models.TextField(blank=True, null=True)
    
    # Detail
    kind = models.CharField(max_length=50, choices=KIND_CHOICES, blank=True, null=True)
    code = models.JSONField(help_text='Código da atividade (SNOMED CT)')
    
    # Razão (por que fazer)
    reason_code = models.JSONField(blank=True, null=True)
    reason_reference = models.JSONField(blank=True, null=True)
    
    # Objetivos relacionados
    goal = models.JSONField(default=list, help_text='Referências para Goal resources')
    
    # Descrição
    description = models.TextField(blank=True, null=True)
    
    # Agendamento
    scheduled_timing = models.JSONField(
        blank=True,
        null=True,
        help_text='Timing para atividades recorrentes'
    )
    scheduled_period_start = models.DateTimeField(blank=True, null=True)
    scheduled_period_end = models.DateTimeField(blank=True, null=True)
    scheduled_string = models.CharField(max_length=255, blank=True, null=True)
    
    # Localização - Referência FHIR
    location_reference = models.JSONField(
        null=True,
        blank=True,
        help_text='Referência FHIR à localização: Location'
    )
    
    # Executores
    performers = models.JSONField(
        default=list,
        help_text='Profissionais responsáveis pela atividade'
    )
    
    # Produto (medicamento, dispositivo, etc.)
    product_reference = models.JSONField(blank=True, null=True)
    
    # Quantidade
    daily_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True
    )
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'CarePlan Activity'
        verbose_name_plural = 'CarePlan Activities'
        ordering = ['scheduled_period_start', 'created_at']
        indexes = [
            models.Index(fields=['care_plan', 'status']),
            models.Index(fields=['status', 'scheduled_period_start']),
        ]
    
    def __str__(self):
        code_display = self.code.get('text') if self.code else 'N/A'
        return f"{code_display} - {self.get_status_display()}"
    
    def to_fhir_activity(self):
        """Converte para FHIR CarePlan.activity"""
        activity = {
            'outcomeCodeableConcept': self.outcome_codeable_concept or [],
            'outcomeReference': self.outcome_reference or [],
            'detail': {
                'status': self.status,
            }
        }
        
        # Progress
        if self.progress:
            activity['progress'] = [{
                'text': self.progress,
                'time': self.updated_at.isoformat()
            }]
        
        # Detail fields
        detail = activity['detail']
        
        if self.kind:
            detail['kind'] = self.kind
        
        if self.code:
            detail['code'] = self.code
        
        if self.reason_code:
            detail['reasonCode'] = self.reason_code
        
        if self.reason_reference:
            detail['reasonReference'] = self.reason_reference
        
        if self.goal:
            detail['goal'] = self.goal
        
        if self.description:
            detail['description'] = self.description
        
        # Scheduling
        if self.scheduled_period_start or self.scheduled_period_end:
            detail['scheduledPeriod'] = {}
            if self.scheduled_period_start:
                detail['scheduledPeriod']['start'] = self.scheduled_period_start.isoformat()
            if self.scheduled_period_end:
                detail['scheduledPeriod']['end'] = self.scheduled_period_end.isoformat()
        
        if self.scheduled_timing:
            detail['scheduledTiming'] = self.scheduled_timing
        
        if self.scheduled_string:
            detail['scheduledString'] = self.scheduled_string
        
        # Location
        if self.location_reference:
            detail['location'] = self.location_reference
        
        # Performers
        if self.performers:
            detail['performer'] = self.performers
        
        # Product
        if self.product_reference:
            detail['productReference'] = self.product_reference
        
        # Quantities
        if self.daily_amount:
            detail['dailyAmount'] = {
                'value': float(self.daily_amount)
            }
        
        if self.quantity:
            detail['quantity'] = {
                'value': float(self.quantity)
            }
        
        return activity
