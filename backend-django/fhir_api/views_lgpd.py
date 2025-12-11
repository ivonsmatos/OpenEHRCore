"""
Sprint 24: LGPD Privacy Control Endpoints

REST API for LGPD compliance:
- Data Access Logging (Art. 19)
- Data Portability / Download (Art. 18, II)
- Data Deletion Request (Art. 18, VI)
- LGPD Request Management
- Compliance Reporting
"""

import logging
from datetime import datetime, timedelta
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.http import HttpResponse

from .authentication import KeycloakAuthentication
from .services.fhir_core import FHIRService
from .services.lgpd_service import (
    LGPDService,
    LGPDRequestType,
    LGPDRequestStatus
)

logger = logging.getLogger(__name__)


# ============================================================================
# Data Access Logging (LGPD Art. 19)
# ============================================================================

@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def patient_access_logs(request, patient_id):
    """
    Get data access logs for a patient.
    
    GET /api/v1/patients/{patient_id}/access-logs/
    
    Query params:
        - start_date: Filter from date (ISO format)
        - end_date: Filter to date (ISO format)
        - action: Filter by action (read, update, delete, export)
        - limit: Max results (default: 100)
    
    LGPD Art. 19: The data subject has the right to know
    what processing activities are being performed on their data.
    """
    try:
        start_date = None
        end_date = None
        
        if request.query_params.get('start_date'):
            start_date = datetime.fromisoformat(
                request.query_params['start_date'].replace('Z', '+00:00')
            )
        if request.query_params.get('end_date'):
            end_date = datetime.fromisoformat(
                request.query_params['end_date'].replace('Z', '+00:00')
            )
        
        action = request.query_params.get('action')
        limit = int(request.query_params.get('limit', 100))
        
        logs = LGPDService.get_access_logs(
            patient_id=patient_id,
            start_date=start_date,
            end_date=end_date,
            action=action
        )
        
        return Response({
            'patient_id': patient_id,
            'total': len(logs),
            'showing': min(len(logs), limit),
            'logs': [log.to_dict() for log in logs[:limit]]
        })
        
    except Exception as e:
        logger.error(f"Error getting access logs: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def log_data_access(request):
    """
    Log a data access event.
    
    POST /api/v1/lgpd/log-access/
    
    Body:
        {
            "patient_id": "patient-1",
            "resource_type": "Observation",
            "resource_id": "obs-123",
            "action": "read",
            "reason": "Consultation"
        }
    """
    try:
        data = request.data
        
        required_fields = ['patient_id', 'resource_type', 'resource_id', 'action']
        for field in required_fields:
            if not data.get(field):
                return Response({
                    'error': f'{field} is required'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get client info
        ip_address = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT')
        
        log = LGPDService.log_data_access(
            patient_id=data['patient_id'],
            resource_type=data['resource_type'],
            resource_id=data['resource_id'],
            action=data['action'],
            user=request.user,
            ip_address=ip_address,
            user_agent=user_agent,
            reason=data.get('reason')
        )
        
        return Response({
            'message': 'Access logged',
            'log_id': log.log_id
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Error logging access: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================================================
# Data Portability (LGPD Art. 18, II and V)
# ============================================================================

@api_view(['POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def request_data_export(request, patient_id):
    """
    Request data export for portability.
    
    POST /api/v1/patients/{patient_id}/data-export/
    
    Body:
        {
            "format": "json|zip",
            "requester_email": "patient@email.com"
        }
    
    LGPD Art. 18, II: Right to access data
    LGPD Art. 18, V: Right to data portability
    """
    try:
        data = request.data
        file_format = data.get('format', 'json')
        
        if file_format not in ['json', 'zip']:
            return Response({
                'error': 'Format must be json or zip'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create LGPD request record
        lgpd_request = LGPDService.create_lgpd_request(
            request_type=LGPDRequestType.PORTABILITY,
            patient_id=patient_id,
            requester_name=str(request.user),
            requester_email=data.get('requester_email', ''),
            reason="Data portability request"
        )
        
        # Log access
        LGPDService.log_data_access(
            patient_id=patient_id,
            resource_type="Patient",
            resource_id=patient_id,
            action="export",
            user=request.user,
            ip_address=request.META.get('REMOTE_ADDR'),
            reason="Data portability request"
        )
        
        # Perform export
        fhir = FHIRService(request.user)
        export_data = LGPDService.export_patient_data(patient_id, fhir, file_format)
        
        # Create file
        file_content = LGPDService.create_export_file(export_data, file_format)
        
        # Update request status
        LGPDService.update_request_status(
            lgpd_request.request_id,
            LGPDRequestStatus.COMPLETED
        )
        
        # Return file
        content_type = 'application/json' if file_format == 'json' else 'application/zip'
        filename = f"patient_{patient_id}_data.{file_format}"
        
        response = HttpResponse(file_content, content_type=content_type)
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
        
    except Exception as e:
        logger.error(f"Error exporting patient data: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def preview_data_export(request, patient_id):
    """
    Preview data export (metadata only, no download).
    
    GET /api/v1/patients/{patient_id}/data-export/preview/
    
    Returns statistics about what will be exported.
    """
    try:
        fhir = FHIRService(request.user)
        export_data = LGPDService.export_patient_data(patient_id, fhir)
        
        # Return only metadata, not actual data
        return Response({
            'patient_id': patient_id,
            'export_date': export_data['exportDate'],
            'statistics': export_data['statistics'],
            'available_formats': ['json', 'zip']
        })
        
    except Exception as e:
        logger.error(f"Error previewing export: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================================================
# Data Deletion (LGPD Art. 18, VI)
# ============================================================================

@api_view(['POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def request_data_deletion(request, patient_id):
    """
    Request data deletion/anonymization.
    
    POST /api/v1/patients/{patient_id}/data-deletion/
    
    Body:
        {
            "reason": "Patient request",
            "soft_delete": true,
            "requester_email": "patient@email.com"
        }
    
    LGPD Art. 18, VI: Right to deletion of personal data.
    
    Note: By default, performs anonymization (soft delete) to maintain
    audit trail. Set soft_delete=false for complete removal.
    """
    try:
        data = request.data
        soft_delete = data.get('soft_delete', True)
        
        # Create LGPD request
        lgpd_request = LGPDService.create_lgpd_request(
            request_type=LGPDRequestType.DELETION,
            patient_id=patient_id,
            requester_name=str(request.user),
            requester_email=data.get('requester_email', ''),
            reason=data.get('reason', 'Deletion request')
        )
        
        # Log access
        LGPDService.log_data_access(
            patient_id=patient_id,
            resource_type="Patient",
            resource_id=patient_id,
            action="delete",
            user=request.user,
            ip_address=request.META.get('REMOTE_ADDR'),
            reason="Data deletion request"
        )
        
        # Process deletion
        fhir = FHIRService(request.user)
        result = LGPDService.process_deletion_request(
            patient_id=patient_id,
            fhir_service=fhir,
            soft_delete=soft_delete
        )
        
        # Update request status
        status_val = LGPDRequestStatus.COMPLETED if result['success'] else LGPDRequestStatus.REJECTED
        LGPDService.update_request_status(
            lgpd_request.request_id,
            status_val,
            notes=str(result.get('errors', []))
        )
        
        return Response({
            'request_id': lgpd_request.request_id,
            'result': result
        })
        
    except Exception as e:
        logger.error(f"Error processing deletion: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================================================
# LGPD Request Management
# ============================================================================

@api_view(['GET', 'POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def lgpd_requests(request):
    """
    List or create LGPD requests.
    
    GET /api/v1/lgpd/requests/
    Query params:
        - patient_id: Filter by patient
        - status: Filter by status (pending, in_progress, completed, rejected)
    
    POST /api/v1/lgpd/requests/
    Body:
        {
            "request_type": "access|portability|deletion|anonymization|consent_revocation",
            "patient_id": "patient-1",
            "requester_name": "John Doe",
            "requester_email": "john@email.com",
            "reason": "I want to know my data"
        }
    """
    if request.method == 'GET':
        try:
            patient_id = request.query_params.get('patient_id')
            status_filter = request.query_params.get('status')
            
            lgpd_status = None
            if status_filter:
                try:
                    lgpd_status = LGPDRequestStatus(status_filter)
                except ValueError:
                    return Response({
                        'error': f'Invalid status. Use: pending, in_progress, completed, rejected'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            requests_list = LGPDService.list_lgpd_requests(
                patient_id=patient_id,
                status=lgpd_status
            )
            
            return Response({
                'total': len(requests_list),
                'requests': [r.to_dict() for r in requests_list]
            })
            
        except Exception as e:
            logger.error(f"Error listing requests: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'POST':
        try:
            data = request.data
            
            # Validate required fields
            required = ['request_type', 'patient_id', 'requester_name', 'requester_email']
            for field in required:
                if not data.get(field):
                    return Response({
                        'error': f'{field} is required'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # Parse request type
            try:
                req_type = LGPDRequestType(data['request_type'])
            except ValueError:
                return Response({
                    'error': f'Invalid request_type. Use: {[t.value for t in LGPDRequestType]}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            lgpd_request = LGPDService.create_lgpd_request(
                request_type=req_type,
                patient_id=data['patient_id'],
                requester_name=data['requester_name'],
                requester_email=data['requester_email'],
                reason=data.get('reason')
            )
            
            return Response(lgpd_request.to_dict(), status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error creating request: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'PUT'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def lgpd_request_detail(request, request_id):
    """
    Get or update an LGPD request.
    
    GET /api/v1/lgpd/requests/{request_id}/
    PUT /api/v1/lgpd/requests/{request_id}/
    Body:
        {
            "status": "in_progress|completed|rejected",
            "notes": "Processing notes"
        }
    """
    if request.method == 'GET':
        try:
            lgpd_request = LGPDService.get_lgpd_request(request_id)
            if not lgpd_request:
                return Response({
                    'error': 'Request not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            return Response(lgpd_request.to_dict())
            
        except Exception as e:
            logger.error(f"Error getting request: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'PUT':
        try:
            data = request.data
            
            if not data.get('status'):
                return Response({
                    'error': 'status is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                new_status = LGPDRequestStatus(data['status'])
            except ValueError:
                return Response({
                    'error': f'Invalid status. Use: pending, in_progress, completed, rejected'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            lgpd_request = LGPDService.update_request_status(
                request_id=request_id,
                status=new_status,
                notes=data.get('notes')
            )
            
            if not lgpd_request:
                return Response({
                    'error': 'Request not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            return Response(lgpd_request.to_dict())
            
        except Exception as e:
            logger.error(f"Error updating request: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================================================
# Consent Verification
# ============================================================================

@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def check_patient_consent(request, patient_id):
    """
    Check if patient has given consent for specific purposes.
    
    GET /api/v1/patients/{patient_id}/check-consent/
    Query params:
        - purpose: treatment, research, sharing, marketing, emergency
    """
    try:
        purpose = request.query_params.get('purpose', 'treatment')
        
        fhir = FHIRService(request.user)
        result = LGPDService.check_consent(patient_id, fhir, purpose)
        
        return Response(result)
        
    except Exception as e:
        logger.error(f"Error checking consent: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================================================
# LGPD Compliance Reporting
# ============================================================================

@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def patient_lgpd_report(request, patient_id):
    """
    Generate LGPD compliance report for a patient.
    
    GET /api/v1/patients/{patient_id}/lgpd-report/
    
    Returns comprehensive LGPD status including:
    - Data inventory
    - Active consents
    - Access logs
    - Pending requests
    - Compliance status
    """
    try:
        fhir = FHIRService(request.user)
        report = LGPDService.generate_lgpd_report(patient_id, fhir)
        
        return Response(report)
        
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def lgpd_dashboard(request):
    """
    LGPD dashboard with overall statistics.
    
    GET /api/v1/lgpd/dashboard/
    """
    try:
        # Get request statistics
        all_requests = LGPDService.list_lgpd_requests()
        
        pending = [r for r in all_requests if r.status == LGPDRequestStatus.PENDING]
        in_progress = [r for r in all_requests if r.status == LGPDRequestStatus.IN_PROGRESS]
        completed = [r for r in all_requests if r.status == LGPDRequestStatus.COMPLETED]
        
        # Group by type
        by_type = {}
        for req in all_requests:
            req_type = req.request_type.value
            by_type[req_type] = by_type.get(req_type, 0) + 1
        
        # Recent requests
        recent = sorted(all_requests, key=lambda x: x.created_at, reverse=True)[:10]
        
        return Response({
            'summary': {
                'total_requests': len(all_requests),
                'pending': len(pending),
                'in_progress': len(in_progress),
                'completed': len(completed),
                'by_type': by_type
            },
            'pending_requests': [r.to_dict() for r in pending],
            'recent_requests': [r.to_dict() for r in recent],
            'compliance_notes': [
                'LGPD requires response to data subject requests within 15 days',
                'All data access should be logged for auditing',
                'Consent must be obtained for data processing outside treatment'
            ]
        })
        
    except Exception as e:
        logger.error(f"Error getting dashboard: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
