
import os
import django
from django.conf import settings

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from fhir_api.services.fhir_core import FHIRService

def check_data():
    try:
        service = FHIRService()
        patients = service.search_patients()
        print(f"Total Patients found in FHIR: {len(patients)}")
        
        # Check conditions
        # Quick hack to search all conditions if possible or just check a known patient
        if len(patients) > 0:
            pid = patients[0]['id']
            conditions = service.get_conditions_by_patient_id(pid)
            print(f"Conditions for patient {pid}: {len(conditions)}")
        else:
            print("No patients to check conditions for.")

    except Exception as e:
        print(f"ERROR: {str(e)}")

if __name__ == "__main__":
    check_data()
