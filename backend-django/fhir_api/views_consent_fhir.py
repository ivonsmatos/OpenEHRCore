"""
Views for FHIR Consent (Consentimento do Paciente) - LGPD Compliance
FHIR R4 Compliant

Consent resource gerencia o consentimento do paciente para uso de dados,
procedimentos, compartilhamento de informações, etc.
"""
import logging
from datetime import datetime
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response

from .services.fhir_core import FHIRService, FHIRServiceException
from .auth import KeycloakAuthentication, IsAuthenticated

logger = logging.getLogger(__name__)

# Tipos de consentimento padrão LGPD
CONSENT_CATEGORIES = {
    'treatment': {
        'code': 'TREAT',
        'display': 'Tratamento de Dados de Saúde',
        'system': 'http://terminology.hl7.org/CodeSystem/v3-ActCode'
    },
    'research': {
        'code': 'RESEARCH',
        'display': 'Uso para Pesquisa',
        'system': 'http://terminology.hl7.org/CodeSystem/v3-ActCode'
    },
    'sharing': {
        'code': 'HPROVRD',
        'display': 'Compartilhamento com Outros Profissionais',
        'system': 'http://terminology.hl7.org/CodeSystem/v3-ActCode'
    },
    'marketing': {
        'code': 'HMARKT',
        'display': 'Comunicações de Marketing',
        'system': 'http://terminology.hl7.org/CodeSystem/v3-ActCode'
    },
    'emergency': {
        'code': 'ETREAT',
        'display': 'Tratamento de Emergência',
        'system': 'http://terminology.hl7.org/CodeSystem/v3-ActCode'
    }
}


@api_view(['GET', 'POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def manage_consents(request):
    """
    List or create Consent resources
    
    GET /api/v1/consents-v2/
    Query params:
    - patient: Filter by patient ID
    - status: Filter by status (active, inactive, rejected)
    - category: Filter by category (treatment, research, sharing, marketing)
    
    POST /api/v1/consents-v2/
    Body:
    {
        "patient_id": "patient-1",
        "category": "treatment",
        "status": "active",
        "scope": "patient-privacy",
        "date_start": "2024-01-01",
        "date_end": "2025-01-01",
        "performer_name": "Dr. João Silva",
        "organization_id": "org-1"
    }
    """
    fhir = FHIRService(request.user)
    
    if request.method == 'GET':
        try:
            params = {'_count': 50, '_sort': '-date'}
            
            if request.query_params.get('patient'):
                params['patient'] = request.query_params['patient']
            if request.query_params.get('status'):
                params['status'] = request.query_params['status']
            if request.query_params.get('category'):
                params['category'] = request.query_params['category']
            
            results = fhir.search_resources('Consent', params)
            
            consents = []
            for c in results:
                cat = c.get('category', [{}])[0].get('coding', [{}])[0]
                consents.append({
                    'id': c.get('id'),
                    'status': c.get('status'),
                    'scope': c.get('scope', {}).get('coding', [{}])[0].get('code'),
                    'category': cat.get('code'),
                    'categoryDisplay': cat.get('display'),
                    'patientId': c.get('patient', {}).get('reference', '').replace('Patient/', ''),
                    'dateTime': c.get('dateTime'),
                    'periodStart': c.get('provision', {}).get('period', {}).get('start'),
                    'periodEnd': c.get('provision', {}).get('period', {}).get('end'),
                    'performer': c.get('performer', [{}])[0].get('display') if c.get('performer') else None
                })
            
            return Response({
                'consents': consents,
                'total': len(consents)
            })
            
        except Exception as e:
            logger.error(f"Error listing consents: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'POST':
        try:
            data = request.data
            
            # Validate required fields
            if not data.get('patient_id'):
                return Response({'error': 'patient_id é obrigatório'}, status=status.HTTP_400_BAD_REQUEST)
            if not data.get('category'):
                return Response({'error': 'category é obrigatório'}, status=status.HTTP_400_BAD_REQUEST)
            
            category_info = CONSENT_CATEGORIES.get(data['category'])
            if not category_info:
                return Response({
                    'error': f'Categoria inválida. Use: {", ".join(CONSENT_CATEGORIES.keys())}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Build FHIR Consent resource
            consent = {
                'resourceType': 'Consent',
                'status': data.get('status', 'active'),
                'scope': {
                    'coding': [{
                        'system': 'http://terminology.hl7.org/CodeSystem/consentscope',
                        'code': data.get('scope', 'patient-privacy'),
                        'display': 'Privacidade do Paciente'
                    }]
                },
                'category': [{
                    'coding': [{
                        'system': category_info['system'],
                        'code': category_info['code'],
                        'display': category_info['display']
                    }]
                }],
                'patient': {
                    'reference': f"Patient/{data['patient_id']}"
                },
                'dateTime': data.get('dateTime', datetime.now().isoformat()),
                'policyRule': {
                    'coding': [{
                        'system': 'http://terminology.hl7.org/CodeSystem/v3-ActCode',
                        'code': 'LGPD',
                        'display': 'Lei Geral de Proteção de Dados'
                    }]
                }
            }
            
            # Performer (who obtained consent)
            if data.get('performer_name'):
                consent['performer'] = [{'display': data['performer_name']}]
            
            # Organization
            if data.get('organization_id'):
                consent['organization'] = [{'reference': f"Organization/{data['organization_id']}"}]
            
            # Provision (period and actions)
            provision = {'type': 'permit'}
            
            if data.get('date_start') or data.get('date_end'):
                provision['period'] = {}
                if data.get('date_start'):
                    provision['period']['start'] = data['date_start']
                if data.get('date_end'):
                    provision['period']['end'] = data['date_end']
            
            consent['provision'] = provision
            
            result = fhir.create_resource('Consent', consent)
            
            return Response(result, status=status.HTTP_201_CREATED)
            
        except FHIRServiceException as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error creating consent: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'PUT', 'DELETE'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def consent_detail(request, consent_id):
    """
    Get, update or delete a Consent
    
    GET /api/v1/consents-v2/{id}/
    PUT /api/v1/consents-v2/{id}/ - Update status/period
    DELETE /api/v1/consents-v2/{id}/ - Revoke consent
    """
    fhir = FHIRService(request.user)
    
    if request.method == 'GET':
        try:
            result = fhir.get_resource('Consent', consent_id)
            return Response(result)
        except FHIRServiceException as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error getting consent: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'PUT':
        try:
            data = request.data
            existing = fhir.get_resource('Consent', consent_id)
            
            # Update status
            if 'status' in data:
                existing['status'] = data['status']
            
            # Update provision period
            if data.get('date_end'):
                if 'provision' not in existing:
                    existing['provision'] = {}
                if 'period' not in existing['provision']:
                    existing['provision']['period'] = {}
                existing['provision']['period']['end'] = data['date_end']
            
            result = fhir.update_resource('Consent', consent_id, existing)
            return Response(result)
            
        except FHIRServiceException as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error updating consent: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'DELETE':
        try:
            # In FHIR, we typically mark consent as 'rejected' rather than delete
            existing = fhir.get_resource('Consent', consent_id)
            existing['status'] = 'rejected'
            fhir.update_resource('Consent', consent_id, existing)
            return Response({'message': 'Consentimento revogado'}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error revoking consent: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def patient_consents(request, patient_id):
    """
    List all consents for a patient
    
    GET /api/v1/patients/{id}/consents/
    """
    try:
        fhir = FHIRService(request.user)
        
        results = fhir.search_resources('Consent', {
            'patient': patient_id,
            '_sort': '-date',
            '_count': 50
        })
        
        consents = []
        for c in results:
            cat = c.get('category', [{}])[0].get('coding', [{}])[0]
            consents.append({
                'id': c.get('id'),
                'status': c.get('status'),
                'category': cat.get('code'),
                'categoryDisplay': cat.get('display'),
                'dateTime': c.get('dateTime'),
                'periodEnd': c.get('provision', {}).get('period', {}).get('end')
            })
        
        return Response({
            'consents': consents,
            'patient_id': patient_id,
            'total': len(consents)
        })
        
    except Exception as e:
        logger.error(f"Error listing patient consents: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def revoke_all_consents(request, patient_id):
    """
    Revoke all active consents for a patient (LGPD right to be forgotten)
    
    POST /api/v1/patients/{id}/consents/revoke-all/
    """
    try:
        fhir = FHIRService(request.user)
        
        # Find all active consents
        results = fhir.search_resources('Consent', {
            'patient': patient_id,
            'status': 'active',
            '_count': 100
        })
        
        revoked_count = 0
        for c in results:
            c['status'] = 'rejected'
            fhir.update_resource('Consent', c['id'], c)
            revoked_count += 1
        
        return Response({
            'message': f'{revoked_count} consentimento(s) revogado(s)',
            'patient_id': patient_id,
            'revoked_count': revoked_count
        })
        
    except Exception as e:
        logger.error(f"Error revoking consents: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
