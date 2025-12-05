
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .services.fhir_core import FHIRService, FHIRServiceException
import logging

logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_immunization(request):
    """
    Cria registro de vacina.
    Payload: { "patient_id": "P1", "vaccine_code": "01", "vaccine_name": "BCG", "date": "2023-01-01", "lot_number": "L123" }
    """
    try:
        data = request.data
        patient_id = data.get('patient_id')
        vaccine_code = data.get('vaccine_code')
        vaccine_name = data.get('vaccine_name')
        date = data.get('date')
        lot_number = data.get('lot_number')

        if not all([patient_id, vaccine_code, vaccine_name, date]):
            return Response({"error": "Missing required fields"}, status=status.HTTP_400_BAD_REQUEST)

        fhir_service = FHIRService()
        result = fhir_service.create_immunization_resource(
            patient_id=patient_id,
            vaccine_code=vaccine_code,
            vaccine_name=vaccine_name,
            date=date,
            lot_number=lot_number
        )
        return Response(result, status=status.HTTP_201_CREATED)

    except FHIRServiceException as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_immunizations(request, patient_id):
    """
    Lista vacinas de um paciente.
    """
    try:
        fhir_service = FHIRService()
        results = fhir_service.search_resources('Immunization', {'patient': patient_id})
        
        # Simplify specific fields for frontend
        data = []
        for res in results:
            data.append({
                "id": res.get('id'),
                "status": res.get('status'),
                "vaccine_name": res.get('vaccineCode', {}).get('coding', [{}])[0].get('display', 'Unknown'),
                "date": res.get('occurrenceDateTime'),
                "lot_number": res.get('lotNumber')
            })
            
        return Response(data, status=status.HTTP_200_OK)

    except FHIRServiceException as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_diagnostic_report(request):
    """
    Cria resultado de exame.
    Payload: { "patient_id": "P1", "code": "L1", "name": "Hemograma", "date": "2023-01-01", "conclusion": "Normal" }
    """
    try:
        data = request.data
        patient_id = data.get('patient_id')
        code = data.get('code')
        name = data.get('name')
        date = data.get('date')
        conclusion = data.get('conclusion')

        if not all([patient_id, code, name, date, conclusion]):
            return Response({"error": "Missing required fields"}, status=status.HTTP_400_BAD_REQUEST)

        fhir_service = FHIRService()
        result = fhir_service.create_diagnostic_report_resource(
            patient_id=patient_id,
            code=code,
            name=name,
            date=date,
            conclusion=conclusion
        )
        return Response(result, status=status.HTTP_201_CREATED)

    except FHIRServiceException as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_diagnostic_reports(request, patient_id):
    """
    Lista resultados de exames de um paciente.
    """
    try:
        fhir_service = FHIRService()
        results = fhir_service.search_resources('DiagnosticReport', {'subject': f"Patient/{patient_id}"})
        
        data = []
        for res in results:
            data.append({
                "id": res.get('id'),
                "status": res.get('status'),
                "name": res.get('code', {}).get('coding', [{}])[0].get('display', 'Unknown'),
                "date": res.get('effectiveDateTime'),
                "conclusion": res.get('conclusion')
            })
            
        return Response(data, status=status.HTTP_200_OK)

    except FHIRServiceException as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
