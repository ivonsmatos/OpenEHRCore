
import os
import django
from django.conf import settings

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from fhir_api.services.analytics_service import AnalyticsService

def test_analytics():
    print("Initializing AnalyticsService...")
    try:
        service = AnalyticsService()
        
        print("Testing Population Demographics...")
        pop_data = service.get_population_demographics()
        print(f"Population Data: {pop_data}")
        
        print("Testing Clinical Insights...")
        clin_data = service.get_clinical_insights()
        print(f"Clinical Data: {clin_data}")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_analytics()
