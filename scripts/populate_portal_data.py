import os
import sys
import django
from datetime import datetime, timedelta

# Setup Django
sys.path.append(os.path.join(os.path.dirname(__file__), '../backend-django'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'openehrcore.settings')
django.setup()

from fhir_api.services.fhir_core import FHIRService

def populate():
    service = FHIRService()
    patient_id = "patient-1"

    print(f"Populating data for {patient_id}...")

    # 1. Ensure Patient Exists (or at least referenced)
    # in a real scenario we'd create the patient resource first if missing, 
    # but FHIRService methods often just take the ID.
    
    # 2. Create Future Appointment (Telemedicine)
    start_time = (datetime.utcnow() + timedelta(hours=2)).replace(microsecond=0)
    start_str = start_time.strftime("%Y-%m-%dT%H:%M:%SZ")
    end_time = start_time + timedelta(minutes=30)
    end_str = end_time.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    # practitioner_id not supported in create_appointment_resource currently
    # We might need to implement it later or just simulate it for now
    
    appt = service.create_appointment_resource(
        patient_id=patient_id,
        start=start_str,
        end=end_str,
        status="booked",
        description="Consulta de Retorno - Telemedicina"
    )
    print(f"Appointment created: {appt.get('id')}")

    # 3. Create Recent Exam Result (Observation)
    print("Creating Observation (Exam Result)...")
    
    past_start = (datetime.utcnow() - timedelta(days=2)).replace(microsecond=0)
    past_start_str = past_start.strftime("%Y-%m-%dT%H:%M:%SZ")
    past_end = past_start + timedelta(minutes=20)
    past_end_str = past_end.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    encounter = service.create_encounter_resource(
        patient_id=patient_id,
        encounter_type="AMB", # Changed arg name
        status="finished",
        period_start=past_start_str,
        period_end=past_end_str
    )
    encounter_id = encounter.get('id')
    print(f"Past Encounter created: {encounter_id}")

    # Create Observation linked to that encounter
    obs = service.create_observation_resource(
        patient_id=patient_id,
        encounter_id=encounter_id,
        code_text="Hemograma Completo",
        value_quantity=14.5,
        unit="g/dL",
        status="final"
    )
    print(f"Observation created: {obs.get('id')}")

    print("\nDone! Refresh the patient portal.")

if __name__ == "__main__":
    populate()
