import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'openehrcore.settings')

import django
django.setup()

from fhir_api.services.ai_service import AIService
import requests

# Buscar dados do paciente 512
patient_id = "512"
FHIR_URL = "http://localhost:8080/fhir"

# Buscar patient
patient = requests.get(f"{FHIR_URL}/Patient/{patient_id}").json()

# Buscar dados
conditions = requests.get(f"{FHIR_URL}/Condition?patient={patient_id}").json().get('entry', [])
medications = requests.get(f"{FHIR_URL}/MedicationRequest?patient={patient_id}").json().get('entry', [])
observations = requests.get(f"{FHIR_URL}/Observation?patient={patient_id}&category=vital-signs&_count=100").json().get('entry', [])
immunizations = requests.get(f"{FHIR_URL}/Immunization?patient={patient_id}").json().get('entry', [])
diagnostic_reports = requests.get(f"{FHIR_URL}/DiagnosticReport?patient={patient_id}").json().get('entry', [])
appointments = requests.get(f"{FHIR_URL}/Appointment?patient={patient_id}").json().get('entry', [])

# Preparar data
patient_data = {
    "name": "João Silva Santos",
    "age": 68,
    "gender": "male",
    "conditions": [c['resource'] for c in conditions],
    "medications": [m['resource'] for m in medications],
    "vital_signs": [o['resource'] for o in observations],
    "immunizations": [i['resource'] for i in immunizations],
    "diagnostic_reports": [d['resource'] for d in diagnostic_reports],
    "appointments": [a['resource'] for a in appointments]
}

# Gerar resumo
ai_service = AIService()
summary = ai_service.generate_patient_summary(patient_data)

print("="*80)
print("RESUMO GERADO:")
print("="*80)
print(summary)
print("="*80)
print(f"Tamanho: {len(summary)} caracteres")
