
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
    Lista resultados de exames de um paciente com dados completos.
    """
    try:
        fhir_service = FHIRService()
        results = fhir_service.search_resources('DiagnosticReport', {'subject': f"Patient/{patient_id}"})
        
        data = []
        for res in results:
            # Extrair código do exame
            code_obj = res.get('code', {})
            code_display = code_obj.get('coding', [{}])[0].get('display', 'Exame sem nome')
            code_code = code_obj.get('coding', [{}])[0].get('code', '')
            
            # Extrair categoria
            category_obj = res.get('category', [{}])[0] if res.get('category') else {}
            category_coding = category_obj.get('coding', [{}])[0] if category_obj.get('coding') else {}
            category_display = category_coding.get('display') or category_coding.get('code', '')
            
            # Fallback: converter código para display legível
            category_map = {
                'LAB': 'Laboratório',
                'MB': 'Microbiologia',
                'RAD': 'Radiologia',
                'HM': 'Hematologia',
                'CH': 'Química',
                'OTH': 'Outros'
            }
            if category_display in category_map:
                category_display = category_map[category_display]
            elif not category_display:
                category_display = 'Laboratório'
            
            # Extrair resultados (Observations referenciadas)
            result_refs = res.get('result', [])
            observations = []
            for ref in result_refs:
                obs_id = ref.get('reference', '').replace('Observation/', '')
                if obs_id:
                    try:
                        obs = fhir_service.read_resource('Observation', obs_id)
                        observations.append({
                            'code': obs.get('code', {}).get('coding', [{}])[0].get('code', ''),
                            'display': obs.get('code', {}).get('coding', [{}])[0].get('display', 'Resultado'),
                            'value': obs.get('valueQuantity', {}).get('value', obs.get('valueString', '')),
                            'unit': obs.get('valueQuantity', {}).get('unit', ''),
                            'interpretation': obs.get('interpretation', [{}])[0].get('coding', [{}])[0].get('code', 'normal'),
                            'referenceRange': obs.get('referenceRange', [{}])[0].get('text', '')
                        })
                    except:
                        pass
            
            data.append({
                "id": res.get('id'),
                "status": res.get('status', 'final'),
                "category": category_display,
                "code": code_code,
                "display": code_display,
                "effectiveDateTime": res.get('effectiveDateTime', res.get('issued', '')),
                "conclusion": res.get('conclusion', ''),
                "results": observations,
                "performer": res.get('performer', [{}])[0].get('display', '')
            })
            
        return Response(data, status=status.HTTP_200_OK)

    except FHIRServiceException as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
