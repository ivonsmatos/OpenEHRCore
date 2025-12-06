
import os
import django
from django.conf import settings
import sys

# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'openehrcore.settings')
django.setup()

from fhir_api.services.ai_service import AIService
from fhir_api.services.fhir_core import FHIRService

def test_ai():
    print("Testing AI Service directly...")
    try:
        service = AIService()
        # Mock data
        pdata = {
            "name": "Test Patient",
            "age": "30",
            "gender": "male",
            "conditions": [],
            "medications": []
        }
        summary = service.generate_patient_summary(pdata)
        print("Summary generated successfully:")
        print(summary[:100] + "...")
    except Exception as e:
        print(f"FAIL: AI Service crashed: {e}")
        import traceback
        traceback.print_exc()

def test_fhir_search_conditions():
    print("\nTesting FHIR Search for Conditions (Simulating views_ai)...")
    try:
        fhir = FHIRService()
        # Get first patient ID
        pats = fhir.search_resources("Patient", search_params={"_count": 1})
        if not pats:
            print("No patients found to test.")
            return
        
        pid = pats[0]['id']
        print(f"Testing with Patient ID: {pid}")
        
        conds = fhir.search_resources("Condition", search_params={"patient": pid})
        print(f"Found {len(conds)} conditions.")
        
    except Exception as e:
        print(f"FAIL: FHIR Search crashed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ai()
    test_fhir_search_conditions()
