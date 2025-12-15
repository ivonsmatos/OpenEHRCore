import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'openehrcore.settings')
django.setup()

from fhir_api.services.fhir_core import FHIRService
from fhir_api.services.ai_service import AIService

print("\n🔍 Testando geração de resumo para paciente 860...\n")

# Get patient data
fhir_service = FHIRService()
patient = fhir_service.get_patient("860")

print(f"👤 Paciente: {patient.get('name')}")
print(f"📅 Data Nascimento: {patient.get('birth_date')}")

# Get clinical data
conditions = fhir_service.search_resources('Condition', {'patient': '860'})
observations = fhir_service.search_resources('Observation', {'patient': '860', '_count': '100'})
medications = fhir_service.search_resources('MedicationRequest', {'patient': '860'})
immunizations = fhir_service.search_resources('Immunization', {'patient': '860'})

print(f"\n🩺 Condições: {len(conditions)}")
print(f"🔬 Observações: {len(observations)}")
print(f"💊 Medicações: {len(medications)}")
print(f"💉 Vacinas: {len(immunizations)}")

# Prepare patient data
patient_data = {
    'name': patient.get('name'),
    'age': 38,  # Approximated from 1986
    'gender': patient.get('gender', 'N/A'),
    'conditions': conditions,
    'observations': observations,
    'medications': medications,
    'immunizations': immunizations,
    'diagnostic_reports': [],
    'appointments': []
}

# Generate summary
print("\n🤖 Gerando resumo com IA...\n")
ai_service = AIService(None)
result = ai_service.generate_patient_summary(patient_data)

print(f"✅ Resumo gerado!")
print(f"📏 Tamanho: {len(result['summary'])} caracteres")
print(f"🤖 Usando AI: {result['using_ai']}")
print(f"\n📄 Preview (500 chars):\n{result['summary'][:500]}\n")
