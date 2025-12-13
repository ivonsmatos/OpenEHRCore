"""Direct test of analytics service"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, 'backend-django')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'healthstack.settings')
django.setup()

from fhir_api.services.analytics_service import AnalyticsService

service = AnalyticsService()

# Test fetch appointments
print("Fetching appointments from FHIR...")
appointments = service._fetch_all_resources("Appointment", limit=500)
print(f"Total appointments fetched: {len(appointments)}")

if appointments:
    # Count by status
    statuses = {}
    for a in appointments:
        s = a.get("status", "unknown")
        statuses[s] = statuses.get(s, 0) + 1
    print(f"Status distribution: {statuses}")
    
    # Count active
    active_statuses = ["booked", "arrived", "fulfilled", "pending"]
    active_count = sum(1 for a in appointments if a.get("status") in active_statuses)
    print(f"Active appointments (booked/arrived/fulfilled/pending): {active_count}")
else:
    print("No appointments returned!")

# Test KPI
print("\n--- KPI Summary ---")
kpi = service.get_kpi_summary()
for key, val in kpi.items():
    print(f"  {key}: {val}")
