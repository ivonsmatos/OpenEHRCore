"""
Views for FHIR AuditEvent - Audit Logging
FHIR R4 Compliant

AuditEvent records security-critical events for compliance and auditing.
Includes user actions, data access, and system events.
"""
import logging
from datetime import datetime
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response

from .services.fhir_core import FHIRService, FHIRServiceException
from .auth import KeycloakAuthentication, IsAuthenticated

logger = logging.getLogger(__name__)

# Audit event types based on FHIR/DICOM standards
AUDIT_EVENT_TYPES = {
    'login': {
        'code': '110114',
        'display': 'User Authentication',
        'system': 'http://dicom.nema.org/resources/ontology/DCM'
    },
    'logout': {
        'code': '110113',
        'display': 'Logout',
        'system': 'http://dicom.nema.org/resources/ontology/DCM'
    },
    'create': {
        'code': 'C',
        'display': 'Create',
        'system': 'http://terminology.hl7.org/CodeSystem/audit-event-action'
    },
    'read': {
        'code': 'R',
        'display': 'Read/View/Print',
        'system': 'http://terminology.hl7.org/CodeSystem/audit-event-action'
    },
    'update': {
        'code': 'U',
        'display': 'Update',
        'system': 'http://terminology.hl7.org/CodeSystem/audit-event-action'
    },
    'delete': {
        'code': 'D',
        'display': 'Delete',
        'system': 'http://terminology.hl7.org/CodeSystem/audit-event-action'
    },
    'export': {
        'code': '110106',
        'display': 'Export',
        'system': 'http://dicom.nema.org/resources/ontology/DCM'
    },
    'access_denied': {
        'code': '110127',
        'display': 'Emergency Override Started',
        'system': 'http://dicom.nema.org/resources/ontology/DCM'
    }
}

# Audit outcomes
AUDIT_OUTCOMES = {
    'success': 0,
    'minor_failure': 4,
    'serious_failure': 8,
    'major_failure': 12
}


def create_audit_event(
    user,
    event_type: str,
    resource_type: str = None,
    resource_id: str = None,
    outcome: str = 'success',
    outcome_desc: str = None,
    patient_id: str = None,
    details: dict = None
):
    """
    Helper function to create an AuditEvent record
    
    Args:
        user: The authenticated user
        event_type: One of AUDIT_EVENT_TYPES keys
        resource_type: FHIR resource type (Patient, Observation, etc)
        resource_id: ID of the resource being accessed
        outcome: 'success', 'minor_failure', 'serious_failure', 'major_failure'
        outcome_desc: Description of the outcome
        patient_id: Patient ID if action relates to a patient
        details: Additional details dict
    """
    try:
        fhir = FHIRService(user)
        
        event_info = AUDIT_EVENT_TYPES.get(event_type, AUDIT_EVENT_TYPES['read'])
        
        audit_event = {
            'resourceType': 'AuditEvent',
            'type': {
                'system': event_info['system'],
                'code': event_info['code'],
                'display': event_info['display']
            },
            'recorded': datetime.now().isoformat(),
            'outcome': AUDIT_OUTCOMES.get(outcome, 0),
            'agent': [{
                'who': {
                    'display': getattr(user, 'username', 'Unknown User')
                },
                'requestor': True,
                'network': {
                    'type': '2',  # IP Address
                    'address': getattr(user, 'ip_address', 'unknown')
                }
            }],
            'source': {
                'observer': {
                    'display': 'OpenEHRCore'
                },
                'type': [{
                    'system': 'http://terminology.hl7.org/CodeSystem/security-source-type',
                    'code': '4',
                    'display': 'Application Server'
                }]
            }
        }
        
        # Add outcome description
        if outcome_desc:
            audit_event['outcomeDesc'] = outcome_desc
        
        # Add entity (what was accessed)
        if resource_type and resource_id:
            audit_event['entity'] = [{
                'what': {
                    'reference': f"{resource_type}/{resource_id}"
                },
                'type': {
                    'system': 'http://terminology.hl7.org/CodeSystem/audit-entity-type',
                    'code': '2',
                    'display': 'System Object'
                },
                'role': {
                    'system': 'http://terminology.hl7.org/CodeSystem/object-role',
                    'code': '4',
                    'display': 'Domain Resource'
                }
            }]
        
        # Add patient reference if applicable
        if patient_id:
            if 'entity' not in audit_event:
                audit_event['entity'] = []
            audit_event['entity'].append({
                'what': {
                    'reference': f"Patient/{patient_id}"
                },
                'type': {
                    'system': 'http://terminology.hl7.org/CodeSystem/audit-entity-type',
                    'code': '1',
                    'display': 'Person'
                },
                'role': {
                    'system': 'http://terminology.hl7.org/CodeSystem/object-role',
                    'code': '1',
                    'display': 'Patient'
                }
            })
        
        # Add additional details
        if details:
            audit_event['extension'] = [{
                'url': 'http://openehrcore.local/fhir/StructureDefinition/audit-details',
                'valueString': str(details)
            }]
        
        result = fhir.create_resource('AuditEvent', audit_event)
        logger.info(f"AuditEvent created: {event_type} on {resource_type}/{resource_id}")
        return result
        
    except Exception as e:
        logger.error(f"Failed to create AuditEvent: {e}")
        return None


@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def list_audit_events(request):
    """
    List AuditEvent records with filtering
    
    GET /api/v1/audit-events/
    Query params:
    - patient: Filter by patient reference
    - agent: Filter by agent (user)
    - type: Filter by event type
    - date: Filter by date (FHIR date format)
    - outcome: Filter by outcome (0, 4, 8, 12)
    - _count: Number of results (default: 50)
    """
    try:
        fhir = FHIRService(request.user)
        
        params = {'_count': 50, '_sort': '-date'}
        
        if request.query_params.get('patient'):
            params['patient'] = request.query_params['patient']
        if request.query_params.get('agent'):
            params['agent'] = request.query_params['agent']
        if request.query_params.get('type'):
            params['type'] = request.query_params['type']
        if request.query_params.get('date'):
            params['date'] = request.query_params['date']
        if request.query_params.get('outcome'):
            params['outcome'] = request.query_params['outcome']
        if request.query_params.get('_count'):
            params['_count'] = min(int(request.query_params['_count']), 100)
        
        results = fhir.search_resources('AuditEvent', params)
        
        events = []
        for e in results:
            agent = e.get('agent', [{}])[0]
            entity = e.get('entity', [{}])[0] if e.get('entity') else {}
            
            events.append({
                'id': e.get('id'),
                'type': e.get('type', {}).get('display'),
                'typeCode': e.get('type', {}).get('code'),
                'recorded': e.get('recorded'),
                'outcome': e.get('outcome'),
                'outcomeDesc': e.get('outcomeDesc'),
                'agent': agent.get('who', {}).get('display'),
                'agentNetwork': agent.get('network', {}).get('address'),
                'entity': entity.get('what', {}).get('reference'),
                'entityRole': entity.get('role', {}).get('display')
            })
        
        return Response({
            'events': events,
            'total': len(events)
        })
        
    except Exception as e:
        logger.error(f"Error listing audit events: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def audit_event_detail(request, event_id):
    """
    Get details of a specific AuditEvent
    
    GET /api/v1/audit-events/{id}/
    """
    try:
        fhir = FHIRService(request.user)
        result = fhir.get_resource('AuditEvent', event_id)
        return Response(result)
    except FHIRServiceException as e:
        return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error getting audit event: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def patient_audit_trail(request, patient_id):
    """
    Get audit trail for a specific patient (all access to patient data)
    
    GET /api/v1/patients/{id}/audit-trail/
    """
    try:
        fhir = FHIRService(request.user)
        
        # Search for audit events involving this patient
        results = fhir.search_resources('AuditEvent', {
            'patient': patient_id,
            '_sort': '-date',
            '_count': int(request.query_params.get('_count', 100))
        })
        
        events = []
        for e in results:
            agent = e.get('agent', [{}])[0]
            events.append({
                'id': e.get('id'),
                'type': e.get('type', {}).get('display'),
                'recorded': e.get('recorded'),
                'outcome': 'success' if e.get('outcome') == 0 else 'failure',
                'user': agent.get('who', {}).get('display'),
                'action': e.get('type', {}).get('code')
            })
        
        return Response({
            'patient_id': patient_id,
            'audit_trail': events,
            'total': len(events)
        })
        
    except Exception as e:
        logger.error(f"Error getting patient audit trail: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def security_report(request):
    """
    Get security summary report
    
    GET /api/v1/audit-events/security-report/
    Query params:
    - period: last24h, last7d, last30d (default: last24h)
    """
    try:
        from datetime import timedelta
        
        fhir = FHIRService(request.user)
        period = request.query_params.get('period', 'last24h')
        
        # Calculate date range
        now = datetime.now()
        if period == 'last7d':
            start_date = (now - timedelta(days=7)).isoformat()
        elif period == 'last30d':
            start_date = (now - timedelta(days=30)).isoformat()
        else:  # last24h
            start_date = (now - timedelta(hours=24)).isoformat()
        
        # Get all events in period
        results = fhir.search_resources('AuditEvent', {
            'date': f'ge{start_date}',
            '_count': 500
        })
        
        # Analyze events
        total_events = len(results)
        success_count = sum(1 for e in results if e.get('outcome') == 0)
        failure_count = total_events - success_count
        
        # Count by type
        type_counts = {}
        for e in results:
            event_type = e.get('type', {}).get('display', 'Unknown')
            type_counts[event_type] = type_counts.get(event_type, 0) + 1
        
        # Unique users
        unique_users = set()
        for e in results:
            agents = e.get('agent', [])
            for a in agents:
                user = a.get('who', {}).get('display')
                if user:
                    unique_users.add(user)
        
        return Response({
            'period': period,
            'start_date': start_date,
            'end_date': now.isoformat(),
            'total_events': total_events,
            'success_count': success_count,
            'failure_count': failure_count,
            'success_rate': round(success_count / total_events * 100, 2) if total_events > 0 else 0,
            'unique_users': len(unique_users),
            'events_by_type': type_counts
        })
        
    except Exception as e:
        logger.error(f"Error generating security report: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
