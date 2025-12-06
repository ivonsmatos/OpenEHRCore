
import os
import django
import sys
from pprint import pprint

# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'openehrcore.settings')
django.setup()

from fhir_api.services.fhir_core import FHIRService

def debug_pagination():
    print("--- Initializing FHIRService ---")
    try:
        service = FHIRService()
        print(f"FHIR URL: {service.base_url}")
        
        print("\n--- Testing search_patients with pagination ---")
        # Simulating page=1
        page = 1
        count = 20
        offset = 0
        
        print(f"Calling search_patients(offset={offset}, count={count})")
        data = service.search_patients(name=None, offset=offset, count=count)
        
        print("\n--- Result ---")
        pprint(data)
        
    except Exception as e:
        print(f"\nCRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_pagination()
