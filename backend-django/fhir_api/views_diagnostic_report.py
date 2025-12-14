"""
Views for DiagnosticReport (Laudos e Resultados de Exames) management
FHIR R4 Compliant

DiagnosticReport representa laudos e resultados de exames,
como hemograma, ECG, raio-X, etc.
"""
import logging
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response

from .services.fhir_core import FHIRService, FHIRServiceException
from .auth import KeycloakAuthentication, IsAuthenticated

logger = logging.getLogger(__name__)


@api_view(['GET', 'POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def manage_diagnostic_reports(request):
    """
    List or create DiagnosticReport resources
    
    GET /api/v1/diagnostic-reports/
    Query params:
    - patient: Filter by patient ID
    - category: Filter by category (LAB, RAD, etc)
    - code: Filter by LOINC code
    - status: Filter by status (final, preliminary, etc)
    - date: Filter by effective date
    - _count: Number of results
    
    POST /api/v1/diagnostic-reports/
    Body:
    {
        "patient_id": "patient-1",
        "encounter_id": "encounter-1",
        "category_code": "LAB",
        "category_display": "Laboratory",
        "code": "58410-2",
        "code_display": "Hemograma Completo",
        "status": "final",
        "conclusion": "Valores dentro da normalidade.",
        "performer_name": "Laboratório Premium",
        "results": [
            {"code": "718-7", "display": "Hemoglobina", "value": 14.5, "unit": "g/dL"}
        ]
    }
    """
    fhir = FHIRService(request.user)
    
    if request.method == 'GET':
        try:
            params = {}
            
            if request.query_params.get('patient'):
                params['patient'] = request.query_params['patient']
            if request.query_params.get('category'):
                params['category'] = request.query_params['category']
            if request.query_params.get('code'):
                params['code'] = request.query_params['code']
            if request.query_params.get('status'):
                params['status'] = request.query_params['status']
            if request.query_params.get('date'):
                params['date'] = request.query_params['date']
            
            params['_count'] = min(int(request.query_params.get('_count', 20)), 100)
            params['_sort'] = '-date'
            
            results = fhir.search_resources('DiagnosticReport', params)
            
            reports = []
            for r in results:
                reports.append({
                    'id': r.get('id'),
                    'resourceType': 'DiagnosticReport',
                    'status': r.get('status'),
                    'category': r.get('category', [{}])[0].get('coding', [{}])[0].get('display') if r.get('category') else None,
                    'code': r.get('code', {}).get('coding', [{}])[0].get('display') if r.get('code') else None,
                    'codeValue': r.get('code', {}).get('coding', [{}])[0].get('code') if r.get('code') else None,
                    'patientId': r.get('subject', {}).get('reference', '').replace('Patient/', ''),
                    'effectiveDateTime': r.get('effectiveDateTime'),
                    'issued': r.get('issued'),
                    'conclusion': r.get('conclusion'),
                    'performer': r.get('performer', [{}])[0].get('display') if r.get('performer') else None
                })
            
            return Response({
                'reports': reports,
                'total': len(reports)
            })
            
        except Exception as e:
            logger.error(f"Error listing diagnostic reports: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'POST':
        try:
            data = request.data
            
            # Validate required
            required = ['patient_id', 'code', 'code_display']
            for field in required:
                if not data.get(field):
                    return Response({'error': f'Campo {field} é obrigatório'}, status=status.HTTP_400_BAD_REQUEST)
            
            from datetime import datetime
            
            # Build FHIR resource
            report = {
                'resourceType': 'DiagnosticReport',
                'status': data.get('status', 'final'),
                'subject': {'reference': f"Patient/{data['patient_id']}"},
                'code': {
                    'coding': [{
                        'system': 'http://loinc.org',
                        'code': data['code'],
                        'display': data['code_display']
                    }],
                    'text': data['code_display']
                },
                'effectiveDateTime': data.get('effectiveDateTime', datetime.now().isoformat()),
                'issued': data.get('issued', datetime.now().isoformat())
            }
            
            # Category
            category_code = data.get('category_code', 'LAB')
            category_display = data.get('category_display', 'Laboratory')
            report['category'] = [{
                'coding': [{
                    'system': 'http://terminology.hl7.org/CodeSystem/v2-0074',
                    'code': category_code,
                    'display': category_display
                }]
            }]
            
            # Encounter reference
            if data.get('encounter_id'):
                report['encounter'] = {'reference': f"Encounter/{data['encounter_id']}"}
            
            # Performer
            if data.get('performer_name'):
                report['performer'] = [{'display': data['performer_name']}]
            
            # Conclusion
            if data.get('conclusion'):
                report['conclusion'] = data['conclusion']
            
            # Results (Observations references)
            if data.get('results'):
                report['result'] = []
                # Create observations for each result
                for res in data['results']:
                    obs = {
                        'resourceType': 'Observation',
                        'status': 'final',
                        'category': [{'coding': [{'system': 'http://terminology.hl7.org/CodeSystem/observation-category', 'code': 'laboratory'}]}],
                        'code': {'coding': [{'system': 'http://loinc.org', 'code': res.get('code', ''), 'display': res.get('display', '')}]},
                        'subject': {'reference': f"Patient/{data['patient_id']}"},
                        'effectiveDateTime': report['effectiveDateTime'],
                        'valueQuantity': {
                            'value': res.get('value'),
                            'unit': res.get('unit', ''),
                            'system': 'http://unitsofmeasure.org'
                        }
                    }
                    obs_result = fhir.create_resource('Observation', obs)
                    report['result'].append({'reference': f"Observation/{obs_result['id']}"})
            
            # Create in FHIR
            result = fhir.create_resource('DiagnosticReport', report)
            
            return Response(result, status=status.HTTP_201_CREATED)
            
        except FHIRServiceException as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error creating diagnostic report: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'PUT', 'DELETE'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def diagnostic_report_detail(request, report_id):
    """
    Get, update or delete a DiagnosticReport
    
    GET /api/v1/diagnostic-reports/{id}/
    PUT /api/v1/diagnostic-reports/{id}/
    DELETE /api/v1/diagnostic-reports/{id}/
    """
    fhir = FHIRService(request.user)
    
    if request.method == 'GET':
        try:
            result = fhir.get_resource('DiagnosticReport', report_id)
            
            # Include referenced observations if present
            if result.get('result'):
                observations = []
                for ref in result['result']:
                    obs_id = ref.get('reference', '').replace('Observation/', '')
                    if obs_id:
                        try:
                            obs = fhir.get_resource('Observation', obs_id)
                            observations.append({
                                'id': obs.get('id'),
                                'code': obs.get('code', {}).get('coding', [{}])[0].get('display'),
                                'value': obs.get('valueQuantity', {}).get('value'),
                                'unit': obs.get('valueQuantity', {}).get('unit')
                            })
                        except FHIRServiceException as e:
                            # Log but continue - individual observation failure shouldn't break entire report
                            logger.warning(f"Failed to fetch observation {obs_id}: {str(e)}")
                        except Exception as e:
                            logger.warning(f"Unexpected error fetching observation {obs_id}: {str(e)}")
                result['_observations'] = observations
            
            return Response(result)
        except FHIRServiceException as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error getting diagnostic report: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'PUT':
        try:
            data = request.data
            existing = fhir.get_resource('DiagnosticReport', report_id)
            
            if 'status' in data:
                existing['status'] = data['status']
            if 'conclusion' in data:
                existing['conclusion'] = data['conclusion']
            if 'effectiveDateTime' in data:
                existing['effectiveDateTime'] = data['effectiveDateTime']
            
            result = fhir.update_resource('DiagnosticReport', report_id, existing)
            return Response(result)
            
        except FHIRServiceException as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error updating diagnostic report: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'DELETE':
        try:
            fhir.delete_resource('DiagnosticReport', report_id)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            logger.error(f"Error deleting diagnostic report: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
