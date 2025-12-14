"""
FHIR API Models

Este arquivo importa todos os models dos módulos separados
para que o Django detecte e crie as migrations.
"""

# Sprint 34-35: Novos recursos FHIR
from .models_medication_administration import MedicationAdministration
from .models_task import Task
from .models_goal import Goal, GoalTarget
from .models_media import Media

__all__ = [
    'MedicationAdministration',
    'Task',
    'Goal',
    'GoalTarget',
    'Media',
]
