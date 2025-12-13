"""
Billing Views - Coverage, Claim, and Invoice management

Sprint 30: Billing Completo

FHIR Resources:
- Coverage: Insurance/health plan information
- Claim: Billing request
- ClaimResponse: Payer response
- Invoice: Financial invoice
"""

import logging
from datetime import datetime
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .authentication import KeycloakAuthentication
from .services.fhir_core import FHIRService

logger = logging.getLogger(__name__)


# ========== COVERAGE (Insurance) ==========

@api_view(['GET', 'POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def manage_coverage(request):
    """
    List or create Coverage resources (insurance/health plan).
    
    GET /api/v1/billing/coverage/
    POST /api/v1/billing/coverage/
    """
    fhir_service = FHIRService(request.user)
    
    if request.method == 'GET':
        patient_id = request.query_params.get('patient')
        params = {}
        if patient_id:
            params['beneficiary'] = f'Patient/{patient_id}'
        
        coverage_list = fhir_service.search_resources('Coverage', params)
        
        return Response({
            'count': len(coverage_list),
            'results': coverage_list
        })
    
    elif request.method == 'POST':
        data = request.data
        
        coverage = {
            'resourceType': 'Coverage',
            'status': data.get('status', 'active'),
            'type': {
                'coding': [{
                    'system': 'http://terminology.hl7.org/CodeSystem/coverage-type',
                    'code': data.get('type_code', 'HMO'),
                    'display': data.get('type_display', 'Health Maintenance Organization')
                }]
            },
            'subscriber': {
                'reference': f"Patient/{data.get('subscriber_id')}"
            },
            'beneficiary': {
                'reference': f"Patient/{data.get('patient_id')}"
            },
            'relationship': {
                'coding': [{
                    'system': 'http://terminology.hl7.org/CodeSystem/subscriber-relationship',
                    'code': data.get('relationship', 'self'),
                    'display': data.get('relationship_display', 'Self')
                }]
            },
            'period': {
                'start': data.get('start_date', datetime.now().strftime('%Y-%m-%d')),
                'end': data.get('end_date')
            },
            'payor': [{
                'display': data.get('payer_name', 'Plano de Saúde')
            }],
            'class': [{
                'type': {
                    'coding': [{
                        'system': 'http://terminology.hl7.org/CodeSystem/coverage-class',
                        'code': 'plan'
                    }]
                },
                'value': data.get('plan_code', ''),
                'name': data.get('plan_name', '')
            }],
            'identifier': [{
                'system': 'http://ans.gov.br/carteirinha',
                'value': data.get('card_number', '')
            }]
        }
        
        result = fhir_service.create_resource('Coverage', coverage)
        
        return Response(result, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PUT', 'DELETE'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def coverage_detail(request, coverage_id):
    """
    Get, update, or delete a Coverage.
    """
    fhir_service = FHIRService(request.user)
    
    if request.method == 'GET':
        coverage = fhir_service.get_resource('Coverage', coverage_id)
        return Response(coverage)
    
    elif request.method == 'PUT':
        result = fhir_service.update_resource('Coverage', coverage_id, request.data)
        return Response(result)
    
    elif request.method == 'DELETE':
        fhir_service.delete_resource('Coverage', coverage_id)
        return Response(status=status.HTTP_204_NO_CONTENT)


# ========== CLAIMS ==========

@api_view(['GET', 'POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def manage_claims(request):
    """
    List or create Claim resources.
    
    GET /api/v1/billing/claims/
    POST /api/v1/billing/claims/
    """
    fhir_service = FHIRService(request.user)
    
    if request.method == 'GET':
        patient_id = request.query_params.get('patient')
        claim_status = request.query_params.get('status')
        
        params = {}
        if patient_id:
            params['patient'] = f'Patient/{patient_id}'
        if claim_status:
            params['status'] = claim_status
        
        claims = fhir_service.search_resources('Claim', params)
        
        return Response({
            'count': len(claims),
            'results': claims
        })
    
    elif request.method == 'POST':
        data = request.data
        
        claim = {
            'resourceType': 'Claim',
            'status': 'active',
            'type': {
                'coding': [{
                    'system': 'http://terminology.hl7.org/CodeSystem/claim-type',
                    'code': data.get('type', 'professional'),
                    'display': data.get('type_display', 'Professional')
                }]
            },
            'use': data.get('use', 'claim'),
            'patient': {
                'reference': f"Patient/{data.get('patient_id')}"
            },
            'created': datetime.now().isoformat(),
            'provider': {
                'reference': f"Practitioner/{data.get('provider_id', 'default')}"
            },
            'priority': {
                'coding': [{
                    'code': data.get('priority', 'normal')
                }]
            },
            'insurance': [{
                'sequence': 1,
                'focal': True,
                'coverage': {
                    'reference': f"Coverage/{data.get('coverage_id')}"
                }
            }],
            'item': []
        }
        
        # Add claim items (procedures, services)
        for idx, item_data in enumerate(data.get('items', []), start=1):
            item = {
                'sequence': idx,
                'productOrService': {
                    'coding': [{
                        'system': item_data.get('code_system', 'http://www.ans.gov.br/tuss'),
                        'code': item_data.get('code'),
                        'display': item_data.get('display')
                    }]
                },
                'quantity': {
                    'value': item_data.get('quantity', 1)
                },
                'unitPrice': {
                    'value': item_data.get('unit_price', 0),
                    'currency': 'BRL'
                },
                'net': {
                    'value': item_data.get('total', 0),
                    'currency': 'BRL'
                }
            }
            
            if item_data.get('service_date'):
                item['servicedDate'] = item_data['service_date']
            
            claim['item'].append(item)
        
        # Calculate total
        total = sum(item.get('net', {}).get('value', 0) for item in claim['item'])
        claim['total'] = {'value': total, 'currency': 'BRL'}
        
        result = fhir_service.create_resource('Claim', claim)
        
        logger.info(f"Created claim for patient {data.get('patient_id')}: {result.get('id')}")
        return Response(result, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PUT'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def claim_detail(request, claim_id):
    """
    Get or update a Claim.
    """
    fhir_service = FHIRService(request.user)
    
    if request.method == 'GET':
        claim = fhir_service.get_resource('Claim', claim_id)
        return Response(claim)
    
    elif request.method == 'PUT':
        result = fhir_service.update_resource('Claim', claim_id, request.data)
        return Response(result)


@api_view(['POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def submit_claim(request, claim_id):
    """
    Submit a claim for processing.
    
    POST /api/v1/billing/claims/{id}/submit/
    """
    fhir_service = FHIRService(request.user)
    
    # Get the claim
    claim = fhir_service.get_resource('Claim', claim_id)
    
    if not claim:
        return Response({'error': 'Claim not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Update status to 'submitted' (simulated)
    claim['status'] = 'active'
    claim['meta'] = claim.get('meta', {})
    claim['meta']['lastUpdated'] = datetime.now().isoformat()
    
    # In production, this would submit to ANS/TISS
    # For now, create a mock ClaimResponse
    
    claim_response = {
        'resourceType': 'ClaimResponse',
        'status': 'active',
        'type': claim.get('type'),
        'use': 'claim',
        'patient': claim.get('patient'),
        'created': datetime.now().isoformat(),
        'insurer': {
            'display': 'Operadora ANS'
        },
        'request': {
            'reference': f'Claim/{claim_id}'
        },
        'outcome': 'complete',
        'disposition': 'Claim processed successfully',
        'total': [
            {
                'category': {
                    'coding': [{
                        'code': 'submitted'
                    }]
                },
                'amount': claim.get('total', {'value': 0, 'currency': 'BRL'})
            },
            {
                'category': {
                    'coding': [{
                        'code': 'benefit'
                    }]
                },
                'amount': claim.get('total', {'value': 0, 'currency': 'BRL'})
            }
        ]
    }
    
    response = fhir_service.create_resource('ClaimResponse', claim_response)
    
    return Response({
        'success': True,
        'claim_id': claim_id,
        'claim_response_id': response.get('id'),
        'outcome': 'complete',
        'message': 'Guia enviada para processamento'
    })


# ========== BILLING DASHBOARD ==========

@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def billing_dashboard(request):
    """
    Get billing dashboard metrics.
    
    GET /api/v1/billing/dashboard/
    """
    fhir_service = FHIRService(request.user)
    
    # Get claims
    claims = fhir_service.search_resources('Claim', {'_count': '100'})
    
    # Calculate metrics
    total_claims = len(claims)
    total_value = sum(
        claim.get('total', {}).get('value', 0) 
        for claim in claims
    )
    
    pending_claims = len([c for c in claims if c.get('status') == 'active'])
    
    # Get coverage count
    coverages = fhir_service.search_resources('Coverage', {'status': 'active', '_count': '100'})
    
    return Response({
        'metrics': {
            'total_claims': total_claims,
            'pending_claims': pending_claims,
            'total_value': total_value,
            'currency': 'BRL',
            'active_coverages': len(coverages)
        },
        'recent_claims': claims[:10]
    })
