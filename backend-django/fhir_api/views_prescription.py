"""
e-Prescribing Views - Prescription endpoints

Sprint 31: Receita Digital
"""

import logging
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .authentication import KeycloakAuthentication
from .services.memed_service import get_memed_service
from .services.fhir_core import FHIRService

logger = logging.getLogger(__name__)


@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def search_drugs(request):
    """
    Search for drugs in the database.
    
    GET /api/v1/prescriptions/drugs/?q=<query>
    """
    query = request.query_params.get('q', '')
    limit = int(request.query_params.get('limit', 20))
    
    if len(query) < 2:
        return Response({
            'error': 'Query deve ter pelo menos 2 caracteres'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    memed = get_memed_service()
    results = memed.search_drugs(query, limit)
    
    return Response({
        'count': len(results),
        'results': results
    })


@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def get_drug_details(request, drug_code):
    """
    Get drug details by code.
    
    GET /api/v1/prescriptions/drugs/<code>/
    """
    memed = get_memed_service()
    drug = memed.get_drug_by_code(drug_code)
    
    if not drug:
        return Response({
            'error': 'Medicamento não encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    
    return Response(drug)


@api_view(['POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def create_prescription(request):
    """
    Create a new electronic prescription.
    
    POST /api/v1/prescriptions/
    
    Body:
        {
            "patient_id": "123",
            "items": [
                {
                    "drug_code": "1001",
                    "dosage": "500mg",
                    "frequency": "8/8h",
                    "duration": "7 dias",
                    "quantity": 21,
                    "instructions": "Tomar com água"
                }
            ],
            "notes": "Observações clínicas"
        }
    """
    data = request.data
    patient_id = data.get('patient_id')
    items = data.get('items', [])
    notes = data.get('notes')
    
    if not patient_id:
        return Response({
            'error': 'patient_id é obrigatório'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if not items:
        return Response({
            'error': 'Pelo menos um medicamento é obrigatório'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Get practitioner ID from token
    practitioner_id = getattr(request.user, 'practitioner_id', 'default')
    
    memed = get_memed_service()
    result = memed.create_prescription(
        patient_id=patient_id,
        practitioner_id=practitioner_id,
        items=items,
        notes=notes
    )
    
    if not result['success']:
        return Response({
            'error': result.get('error')
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Also create MedicationRequest in FHIR
    fhir_service = FHIRService(request.user)
    prescription = result['prescription']
    
    for item in prescription['items']:
        medication_request = {
            'resourceType': 'MedicationRequest',
            'status': 'active',
            'intent': 'order',
            'subject': {'reference': f"Patient/{patient_id}"},
            'requester': {'reference': f"Practitioner/{practitioner_id}"},
            'medicationCodeableConcept': {
                'coding': [{
                    'system': 'http://memed.com.br/drugs',
                    'code': item['drug_code'],
                    'display': item['drug_name']
                }],
                'text': item['drug_name']
            },
            'dosageInstruction': [{
                'text': f"{item['dosage']} - {item['frequency']} por {item['duration']}",
                'timing': {
                    'repeat': {
                        'frequency': 1,
                        'period': 8,
                        'periodUnit': 'h'
                    }
                },
                'additionalInstruction': [{
                    'text': item.get('instructions', '')
                }]
            }],
            'dispenseRequest': {
                'quantity': {
                    'value': item.get('quantity', 1),
                    'unit': 'unidade'
                }
            },
            'note': [{'text': notes}] if notes else []
        }
        
        try:
            fhir_service.create_resource('MedicationRequest', medication_request)
        except Exception as e:
            logger.warning(f"Failed to create FHIR MedicationRequest: {e}")
    
    logger.info(f"Created prescription {prescription['id']} for patient {patient_id}")
    
    return Response(result, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def validate_controlled_drug(request, drug_code):
    """
    Validate ANVISA rules for controlled substances.
    
    POST /api/v1/prescriptions/drugs/<code>/validate/
    
    Body:
        {
            "patient_age": 45,
            "patient_gender": "male"
        }
    """
    patient_data = {
        'age': request.data.get('patient_age'),
        'gender': request.data.get('patient_gender')
    }
    
    memed = get_memed_service()
    result = memed.validate_anvisa(drug_code, patient_data)
    
    return Response(result)


@api_view(['POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def sign_prescription(request, prescription_id):
    """
    Digitally sign a prescription.
    
    POST /api/v1/prescriptions/<id>/sign/
    """
    certificate = request.data.get('certificate', 'mock-certificate')
    
    memed = get_memed_service()
    result = memed.sign_prescription(prescription_id, certificate)
    
    return Response(result)


@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def patient_prescriptions(request, patient_id):
    """
    Get prescriptions for a patient.
    
    GET /api/v1/patients/<id>/prescriptions/
    """
    fhir_service = FHIRService(request.user)
    
    medications = fhir_service.search_resources('MedicationRequest', {
        'subject': f'Patient/{patient_id}',
        '_sort': '-authoredon',
        '_count': '50'
    })
    
    return Response({
        'count': len(medications),
        'results': medications
    })
