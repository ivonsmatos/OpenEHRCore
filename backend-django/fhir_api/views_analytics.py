
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .services.fhir_core import FHIRService
import datetime

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    """
    Retorna métricas para o Dashboard:
    - Total de Pacientes
    - Consultas Hoje
    - Receita Estimada (Mock por enquanto)
    - Total de Documentos
    """
    fhir_service = FHIRService()
    
    # 1. Total Patients
    total_patients = fhir_service.get_total_count('Patient')
    
    # 2. Appointments Today
    today = datetime.date.today().isoformat()
    appointments_today = fhir_service.get_total_count('Appointment', {'date': today})
    
    # 3. Documents
    total_documents = fhir_service.get_total_count('Composition')
    
    # 4. Revenue (Mock logic until Invoice is fully populated)
    # We could supply a count of Invoices if we wanted, but revenue needs summation.
    # For now, let's return a mocked value or sum of invoices if possible. 
    # Attempting to sum invoices might be heavy if many.
    # Let's count Invoices for now.
    total_invoices = fhir_service.get_total_count('Invoice')
    
    data = {
        "stats": {
            "patients": total_patients,
            "appointments_today": appointments_today,
            "documents": total_documents,
            "invoices_count": total_invoices,
            "revenue": 0 # Placeholder
        },
        "trends": {
            "patients": "+5%", # Mock trend
            "revenue": "+12%"
        }
    }
    
    return Response(data)
