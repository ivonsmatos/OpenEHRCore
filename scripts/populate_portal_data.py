import os
import sys
import django
from datetime import datetime, timedelta
import json

# Setup Django
sys.path.append(os.path.join(os.path.dirname(__file__), '../backend-django'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'healthstack.settings')
django.setup()

from fhir_api.services.fhir_core import FHIRService

def populate():
    service = FHIRService()
    patient_id = "patient-1"
    practitioner_id = "practitioner-1"

    print(f"Populating data for {patient_id}...")

    # 1. Ensure Patient Exists with fixed ID (using PUT)
    print(f"Creating/Updating Patient/{patient_id}...")
    
    patient_data = {
        "resourceType": "Patient",
        "id": patient_id,
        "name": [
            {
                "use": "official",
                "family": "Teste",
                "given": ["Paciente"]
            }
        ],
        "gender": "male",
        "birthDate": "1985-05-15",
        "telecom": [
            {
                "system": "email",
                "value": "paciente@teste.com"
            }
        ]
    }
    
    resp = service.session.put(
        f"{service.base_url}/Patient/{patient_id}",
        json=patient_data,
        timeout=service.timeout
    )
    if resp.status_code not in [200, 201]:
        print(f"Failed to create patient: {resp.text}")
        return
    print("Patient created/updated successfully.")

    # 2. Create Future Appointment (Telemedicine)
    # Using explicit ISO string with +00:00 to be safe.
    start_time = (datetime.utcnow() + timedelta(hours=2)).replace(microsecond=0)
    start_str = start_time.isoformat() + "+00:00"
    end_time = start_time + timedelta(minutes=30)
    end_str = end_time.isoformat() + "+00:00"
    
    print("Creating Appointment...")
    try:
        appt = service.create_appointment_resource(
            patient_id=patient_id,
            start=start_str,
            end=end_str,
            status="booked",
            description="Consulta de Retorno - Telemedicina"
        )
        print(f"Appointment created: {appt.get('id')}")
    except Exception as e:
        print(f"Error creating Appointment: {e}")

    # 3. Create Recent Exam Result (Observation)
    print("Creating Observation (Exam Result)...")
    
    past_start = (datetime.utcnow() - timedelta(days=2)).replace(microsecond=0)
    past_start_str = past_start.isoformat() + "+00:00"
    past_end = past_start + timedelta(minutes=20)
    past_end_str = past_end.isoformat() + "+00:00"
    
    # try:
    #     encounter = service.create_encounter_resource(
    #         patient_id=patient_id,
    #         encounter_type="AMB", 
    #         status="finished",
    #         period_start=past_start_str,
    #         period_end=past_end_str
    #     )
    #     encounter_id = encounter.get('id')
    #     print(f"Past Encounter created: {encounter_id}")

    #     # Create Observation linked to that encounter
    #     obs = service.create_observation_resource(
    #         patient_id=patient_id,
    #         encounter_id=encounter_id,
    #         code="8502-5", # Hemograma
    #         value="14.5",
    #         status="final"
    #     )
    #     print(f"Observation created: {obs.get('id')}")
    # except Exception as e:
    #     print(f"Error creating Encounter/Observation: {e}")

    # Fallback: Create Observation without Encounter
    try:
        print("Creating standalone Observation...")
        obs = service.create_observation_resource(
            patient_id=patient_id,
            encounter_id=None,
            code="8502-5",
            value="14.5",
            status="final"
        )
        print(f"Observation created: {obs.get('id')}")
    except Exception as e:
        print(f"Failed to create Observation: {e}")

    print("\nDone! Refresh the patient portal.")

if __name__ == "__main__":
    populate()
