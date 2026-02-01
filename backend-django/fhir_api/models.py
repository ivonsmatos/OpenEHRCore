"""
FHIR API Models

Este arquivo importa todos os models dos módulos separados
para que o Django detecte e crie as migrations.
"""

# Sprint 33: Documentos, Bundles, CarePlans
from .models_careplan import CarePlan, CarePlanActivity
from .models_bundle import Bundle, BundleEntry
from .models_document import DocumentReference, DocumentAttachment

# Sprint 34-35: Novos recursos FHIR
from .models_medication_administration import MedicationAdministration
from .models_task import Task
from .models_goal import Goal, GoalTarget
from .models_media import Media

# Sprint 36: Conformidade FHIR R4 - Audit Trail
from .models_audit import AuditEvent, Provenance

__all__ = [
    # Sprint 33
    'CarePlan',
    'CarePlanActivity',
    'Bundle',
    'BundleEntry',
    'DocumentReference',
    'DocumentAttachment',
    # Sprint 34-35
    'MedicationAdministration',
    'Task',
    'Goal',
    'GoalTarget',
    'Media',
    # Sprint 36
    'AuditEvent',
    'Provenance',
]
