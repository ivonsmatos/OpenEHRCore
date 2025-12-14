"""
MedicationAdministration Models - FHIR R4

Sprint 34: Registro de Administração de Medicamentos
Resource para documentar quando/como/por quem medicação foi administrada
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
import uuid


class MedicationAdministration(models.Model):
    """
    FHIR MedicationAdministration Resource
    
    Documenta a administração de medicamento ao paciente.
    Diferente de MedicationRequest (prescrição), este registra a execução.
    
    Campos principais:
    - status: in-progress | not-done | on-hold | completed | entered-in-error | stopped | unknown
    - medication: Referência ao medicamento administrado
    - subject: Patient (required)
    - context: Encounter (optional)
    - effective: Quando foi administrado (datetime ou period)
    - performer: Quem administrou (practitioner/patient)
    - dosage: Dose, via, rate administrados
    - reason: Por que foi administrado (ou não)
    """
    
    STATUS_CHOICES = [
        ('in-progress', 'In Progress'),
        ('not-done', 'Not Done'),
        ('on-hold', 'On Hold'),
        ('completed', 'Completed'),
        ('entered-in-error', 'Entered in Error'),
        ('stopped', 'Stopped'),
        ('unknown', 'Unknown'),
    ]
    
    # Identificação
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    identifier = models.CharField(max_length=100, unique=True, db_index=True)
    
    # Status e workflow
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='completed', db_index=True)
    status_reason = models.JSONField(null=True, blank=True)  # CodeableConcept - why not-done
    
    # Medicamento
    medication_code = models.JSONField()  # CodeableConcept (RxNorm, ANVISA)
    medication_request = models.CharField(max_length=100, null=True, blank=True)  # Reference to MedicationRequest
    
    # Contexto
    patient_id = models.CharField(max_length=100, db_index=True)  # Reference Patient
    encounter_id = models.CharField(max_length=100, null=True, blank=True, db_index=True)  # Reference Encounter
    
    # Timing - quando foi administrado
    effective_datetime = models.DateTimeField(null=True, blank=True, db_index=True)
    effective_period_start = models.DateTimeField(null=True, blank=True)
    effective_period_end = models.DateTimeField(null=True, blank=True)
    
    # Performer - quem administrou
    performer_function = models.JSONField(null=True, blank=True)  # CodeableConcept (nurse, physician)
    performer_actor_id = models.CharField(max_length=100, null=True, blank=True)  # Reference Practitioner/Patient
    performer_actor_display = models.CharField(max_length=200, null=True, blank=True)
    
    # Dosagem administrada
    dosage_text = models.TextField(null=True, blank=True)  # Texto livre
    dosage_site = models.JSONField(null=True, blank=True)  # CodeableConcept (body site)
    dosage_route = models.JSONField(null=True, blank=True)  # CodeableConcept (oral, IV, etc)
    dosage_method = models.JSONField(null=True, blank=True)  # CodeableConcept (push, infusion)
    dosage_dose_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    dosage_dose_unit = models.CharField(max_length=50, null=True, blank=True)
    dosage_rate_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    dosage_rate_unit = models.CharField(max_length=50, null=True, blank=True)
    
    # Razão
    reason_code = models.JSONField(null=True, blank=True)  # Array of CodeableConcept
    reason_reference = models.CharField(max_length=100, null=True, blank=True)  # Reference Condition/Observation
    
    # Dispositivos usados
    device = models.JSONField(null=True, blank=True)  # Array of References to Device
    
    # Notas e observações
    note = models.TextField(null=True, blank=True)
    
    # Eventos adversos
    event_history = models.JSONField(null=True, blank=True)  # Array of References to events
    
    # Auditoria
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='administered_medications')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'fhir_medication_administration'
        ordering = ['-effective_datetime', '-created_at']
        indexes = [
            models.Index(fields=['patient_id', 'effective_datetime']),
            models.Index(fields=['status', 'effective_datetime']),
            models.Index(fields=['performer_actor_id', 'created_at']),
            models.Index(fields=['medication_request']),
        ]
    
    def __str__(self):
        med_name = self.medication_code.get('text', 'Medication') if isinstance(self.medication_code, dict) else 'Medication'
        return f"MedicationAdministration {self.identifier}: {med_name} ({self.status})"
    
    def clean(self):
        """Validações customizadas"""
        # Pelo menos effective_datetime OU effective_period deve existir
        if not self.effective_datetime and not (self.effective_period_start or self.effective_period_end):
            raise ValidationError("Effective datetime or period is required")
        
        # Period end deve ser após start
        if self.effective_period_start and self.effective_period_end:
            if self.effective_period_end <= self.effective_period_start:
                raise ValidationError("Effective period end must be after start")
        
        # Status 'not-done' requer status_reason
        if self.status == 'not-done' and not self.status_reason:
            raise ValidationError("Status reason is required when status is 'not-done'")
    
    def save(self, *args, **kwargs):
        # Gerar identifier se não existir
        if not self.identifier:
            self.identifier = f"MA-{self.id}"
        
        self.full_clean()
        super().save(*args, **kwargs)
    
    def to_fhir(self):
        """
        Converte para FHIR MedicationAdministration R4
        """
        resource = {
            'resourceType': 'MedicationAdministration',
            'id': str(self.id),
            'identifier': [{
                'system': 'http://openehrcore.com.br/fhir/medication-administration',
                'value': self.identifier
            }],
            'status': self.status,
            'medicationCodeableConcept': self.medication_code,
            'subject': {
                'reference': f'Patient/{self.patient_id}'
            }
        }
        
        # Status reason (para not-done)
        if self.status_reason:
            resource['statusReason'] = self.status_reason if isinstance(self.status_reason, list) else [self.status_reason]
        
        # MedicationRequest original
        if self.medication_request:
            resource['request'] = {
                'reference': f'MedicationRequest/{self.medication_request}'
            }
        
        # Context (encounter)
        if self.encounter_id:
            resource['context'] = {
                'reference': f'Encounter/{self.encounter_id}'
            }
        
        # Effective timing
        if self.effective_datetime:
            resource['effectiveDateTime'] = self.effective_datetime.isoformat()
        elif self.effective_period_start or self.effective_period_end:
            resource['effectivePeriod'] = {}
            if self.effective_period_start:
                resource['effectivePeriod']['start'] = self.effective_period_start.isoformat()
            if self.effective_period_end:
                resource['effectivePeriod']['end'] = self.effective_period_end.isoformat()
        
        # Performer
        if self.performer_actor_id:
            performer = {
                'actor': {
                    'reference': self.performer_actor_id
                }
            }
            if self.performer_actor_display:
                performer['actor']['display'] = self.performer_actor_display
            if self.performer_function:
                performer['function'] = self.performer_function
            
            resource['performer'] = [performer]
        
        # Dosage
        if any([self.dosage_text, self.dosage_site, self.dosage_route, self.dosage_dose_value]):
            dosage = {}
            
            if self.dosage_text:
                dosage['text'] = self.dosage_text
            
            if self.dosage_site:
                dosage['site'] = self.dosage_site
            
            if self.dosage_route:
                dosage['route'] = self.dosage_route
            
            if self.dosage_method:
                dosage['method'] = self.dosage_method
            
            if self.dosage_dose_value:
                dosage['dose'] = {
                    'value': float(self.dosage_dose_value),
                    'unit': self.dosage_dose_unit or 'unit',
                    'system': 'http://unitsofmeasure.org',
                    'code': self.dosage_dose_unit or '{unit}'
                }
            
            if self.dosage_rate_value:
                dosage['rateQuantity'] = {
                    'value': float(self.dosage_rate_value),
                    'unit': self.dosage_rate_unit or 'mL/h',
                    'system': 'http://unitsofmeasure.org',
                    'code': self.dosage_rate_unit or 'mL/h'
                }
            
            resource['dosage'] = dosage
        
        # Reason
        if self.reason_code:
            resource['reasonCode'] = self.reason_code if isinstance(self.reason_code, list) else [self.reason_code]
        
        if self.reason_reference:
            resource['reasonReference'] = [{
                'reference': self.reason_reference
            }]
        
        # Device
        if self.device:
            resource['device'] = self.device if isinstance(self.device, list) else [self.device]
        
        # Note
        if self.note:
            resource['note'] = [{
                'text': self.note,
                'time': self.created_at.isoformat()
            }]
        
        # Event history
        if self.event_history:
            resource['eventHistory'] = self.event_history if isinstance(self.event_history, list) else [self.event_history]
        
        return resource
