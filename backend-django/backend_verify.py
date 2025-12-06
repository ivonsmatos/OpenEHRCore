
import os
import django
from django.conf import settings

# Setup Django (if not running via manage.py shell, but we will run via shell)
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
# django.setup()

from fhir_api.services.fhir_core import FHIRService
from fhir_api.services.analytics_service import AnalyticsService

def verify():
    print("--- Verifying Data ---")
    fhir = FHIRService()
    try:
        patients = fhir.search_patients() or []
        print(f"Total Patients in FHIR: {len(patients)}")
    except Exception as e:
        print(f"Error fetching patients: {e}")

    print("\n--- Verifying Analytics Service ---")
    analytics = AnalyticsService()
    try:
        pop_data = analytics.get_population_demographics()
        print(f"Population Metrics: {pop_data}")
        
        clin_data = analytics.get_clinical_insights()
        print(f"Clinical Metrics: {clin_data}")
        
        ops_data = analytics.get_operational_metrics()
        print(f"Operational Metrics: {ops_data}")
    except Exception as e:
        print(f"Error in Analytics Service: {e}")

if __name__ == "__main__":
    verify()
