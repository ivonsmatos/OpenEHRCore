
import os
import django
import sys
from pprint import pprint

# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'openehrcore.settings')
django.setup()

from fhir_api.services.analytics_service import AnalyticsService

def test_analytics():
    print("--- Initializing AnalyticsService ---")
    try:
        service = AnalyticsService()
        print(f"FHIR URL: {service.base_url}")
        
        print("\n--- Testing get_kpi_summary ---")
        kpi = service.get_kpi_summary()
        pprint(kpi)
        
        print("\n--- Testing Population ---")
        pop = service.get_population_demographics()
        print(f"Total Patients Found: {pop.get('total_patients')}")
        
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_analytics()
