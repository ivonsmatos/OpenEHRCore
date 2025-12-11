"""
Sprint 22: FHIR Bulk Data API Endpoints

Implements REST API for:
- $export operation (Patient, Group, System level)
- Export job management (status, cancel, delete)
- File downloads (NDJSON)
- $import operation
- SMART on FHIR scope validation
"""

import os
import logging
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.http import FileResponse

from .authentication import KeycloakAuthentication
from .services.bulk_data_service import (
    BulkExportService,
    BulkImportService,
    ExportLevel,
    ExportStatus,
    SMARTScopeValidator,
    SMART_SCOPES
)

logger = logging.getLogger(__name__)


# ============================================================================
# Export Operations
# ============================================================================

@api_view(['POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def export_patient(request):
    """
    Initiate Patient-level bulk export ($export).
    
    POST /api/v1/export/Patient/
    
    Request Body:
        {
            "patient_ids": ["patient-1", "patient-2"],  // Optional, defaults to all
            "resource_types": ["Patient", "Observation", "Condition"],  // Optional
            "_since": "2024-01-01T00:00:00Z",  // Optional
            "_typeFilter": "Observation?category=vital-signs"  // Optional
        }
    
    Returns:
        202 Accepted with Content-Location header for status polling
    """
    try:
        data = request.data
        patient_ids = data.get("patient_ids")
        resource_types = data.get("resource_types")
        since = data.get("_since")
        type_filter = data.get("_typeFilter")
        
        # Parse since date
        since_dt = None
        if since:
            from datetime import datetime
            try:
                since_dt = datetime.fromisoformat(since.replace("Z", "+00:00"))
            except ValueError:
                return Response({
                    "error": "Invalid _since date format. Use ISO 8601."
                }, status=status.HTTP_400_BAD_REQUEST)
        
        job = BulkExportService.create_export_job(
            level=ExportLevel.PATIENT,
            resource_types=resource_types,
            patient_ids=patient_ids,
            since=since_dt,
            type_filter=type_filter,
            user=request.user
        )
        
        response = Response({
            "status": "pending",
            "job_id": job.job_id,
            "message": "Export job started. Poll the status URL for updates."
        }, status=status.HTTP_202_ACCEPTED)
        
        response["Content-Location"] = f"/api/v1/export/status/{job.job_id}/"
        
        return response
        
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Error creating patient export: {e}")
        return Response({"error": "Erro ao iniciar exportação"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def export_group(request, group_id):
    """
    Initiate Group-level bulk export ($export).
    
    POST /api/v1/export/Group/{group_id}/
    
    Request Body:
        {
            "resource_types": ["Patient", "Observation"],  // Optional
            "_since": "2024-01-01T00:00:00Z"  // Optional
        }
    """
    try:
        data = request.data
        resource_types = data.get("resource_types")
        since = data.get("_since")
        
        since_dt = None
        if since:
            from datetime import datetime
            try:
                since_dt = datetime.fromisoformat(since.replace("Z", "+00:00"))
            except ValueError:
                return Response({
                    "error": "Invalid _since date format. Use ISO 8601."
                }, status=status.HTTP_400_BAD_REQUEST)
        
        job = BulkExportService.create_export_job(
            level=ExportLevel.GROUP,
            resource_types=resource_types,
            group_id=group_id,
            since=since_dt,
            user=request.user
        )
        
        response = Response({
            "status": "pending",
            "job_id": job.job_id,
            "group_id": group_id,
            "message": "Export job started. Poll the status URL for updates."
        }, status=status.HTTP_202_ACCEPTED)
        
        response["Content-Location"] = f"/api/v1/export/status/{job.job_id}/"
        
        return response
        
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Error creating group export: {e}")
        return Response({"error": "Erro ao iniciar exportação"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def export_system(request):
    """
    Initiate System-level bulk export ($export).
    
    POST /api/v1/export/System/
    
    Request Body:
        {
            "resource_types": ["Patient", "Practitioner", "Organization"],  // Optional
            "_since": "2024-01-01T00:00:00Z"  // Optional
        }
    
    Warning: System-level export may take a long time and generate large files.
    """
    try:
        data = request.data
        resource_types = data.get("resource_types")
        since = data.get("_since")
        
        since_dt = None
        if since:
            from datetime import datetime
            try:
                since_dt = datetime.fromisoformat(since.replace("Z", "+00:00"))
            except ValueError:
                return Response({
                    "error": "Invalid _since date format. Use ISO 8601."
                }, status=status.HTTP_400_BAD_REQUEST)
        
        job = BulkExportService.create_export_job(
            level=ExportLevel.SYSTEM,
            resource_types=resource_types,
            since=since_dt,
            user=request.user
        )
        
        response = Response({
            "status": "pending",
            "job_id": job.job_id,
            "message": "System-level export started. This may take a while."
        }, status=status.HTTP_202_ACCEPTED)
        
        response["Content-Location"] = f"/api/v1/export/status/{job.job_id}/"
        
        return response
        
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Error creating system export: {e}")
        return Response({"error": "Erro ao iniciar exportação"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def export_status(request, job_id):
    """
    Get the status of an export job.
    
    GET /api/v1/export/status/{job_id}/
    
    Returns:
        - 202 Accepted: Job still in progress
        - 200 OK: Job completed with output files
        - 500: Job failed
    """
    try:
        job = BulkExportService.get_job(job_id)
        
        if not job:
            return Response({
                "error": f"Export job {job_id} not found"
            }, status=status.HTTP_404_NOT_FOUND)
        
        response_data = job.to_dict()
        
        # Add download URLs for completed exports
        if job.status == ExportStatus.COMPLETED:
            response_data["output"] = [
                {
                    "type": f.get("type"),
                    "url": f.get("url"),
                    "count": f.get("count")
                }
                for f in job.output_files
            ]
            response_data["requiresAccessToken"] = True
            response_data["transactionTime"] = job.completed_time.isoformat() if job.completed_time else None
            return Response(response_data, status=status.HTTP_200_OK)
        
        elif job.status == ExportStatus.FAILED:
            return Response(response_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        elif job.status == ExportStatus.CANCELLED:
            return Response(response_data, status=status.HTTP_410_GONE)
        
        else:
            # Still processing
            response = Response(response_data, status=status.HTTP_202_ACCEPTED)
            response["X-Progress"] = f"{job.progress}%"
            response["Retry-After"] = "5"  # Poll every 5 seconds
            return response
        
    except Exception as e:
        logger.error(f"Error getting export status: {e}")
        return Response({"error": "Erro ao obter status"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def cancel_export(request, job_id):
    """
    Cancel an in-progress export job.
    
    DELETE /api/v1/export/status/{job_id}/
    """
    try:
        job = BulkExportService.get_job(job_id)
        
        if not job:
            return Response({
                "error": f"Export job {job_id} not found"
            }, status=status.HTTP_404_NOT_FOUND)
        
        if BulkExportService.cancel_job(job_id):
            return Response({
                "message": f"Export job {job_id} cancelled"
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                "error": "Job cannot be cancelled (already completed or failed)"
            }, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        logger.error(f"Error cancelling export: {e}")
        return Response({"error": "Erro ao cancelar exportação"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def list_exports(request):
    """
    List all export jobs.
    
    GET /api/v1/export/jobs/
    
    Query Parameters:
        - status: Filter by status (pending, in-progress, completed, failed)
    """
    try:
        status_filter = request.query_params.get("status")
        
        filter_status = None
        if status_filter:
            try:
                filter_status = ExportStatus(status_filter)
            except ValueError:
                return Response({
                    "error": f"Invalid status. Use: pending, in-progress, completed, failed"
                }, status=status.HTTP_400_BAD_REQUEST)
        
        jobs = BulkExportService.list_jobs(filter_status)
        
        return Response({
            "total": len(jobs),
            "jobs": [job.to_dict() for job in jobs]
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error listing exports: {e}")
        return Response({"error": "Erro ao listar exportações"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def download_export_file(request, job_id, file_name):
    """
    Download an export file.
    
    GET /api/v1/export/files/{job_id}/{file_name}
    
    Returns the NDJSON file as a download.
    """
    try:
        file_path = BulkExportService.get_export_file(job_id, file_name)
        
        if not file_path:
            return Response({
                "error": "File not found or export not completed"
            }, status=status.HTTP_404_NOT_FOUND)
        
        response = FileResponse(
            open(file_path, 'rb'),
            content_type='application/ndjson',
            as_attachment=True,
            filename=file_name
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error downloading export file: {e}")
        return Response({"error": "Erro ao baixar arquivo"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================================================
# Import Operations
# ============================================================================

@api_view(['POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def import_bulk(request):
    """
    Initiate bulk import ($import).
    
    POST /api/v1/import/
    
    Request Body:
        {
            "files": [
                {
                    "resource_type": "Patient",
                    "content": "{\\"resourceType\\":\\"Patient\\"...}\\n{\\"resourceType\\":\\"Patient\\"...}"
                }
            ]
        }
    
    The content should be NDJSON format (one JSON resource per line).
    """
    try:
        data = request.data
        files = data.get("files", [])
        
        if not files:
            return Response({
                "error": "No files provided for import"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        job = BulkImportService.create_import_job(files, request.user)
        
        response = Response({
            "status": "pending",
            "job_id": job.job_id,
            "message": "Import job started. Poll the status URL for updates."
        }, status=status.HTTP_202_ACCEPTED)
        
        response["Content-Location"] = f"/api/v1/import/status/{job.job_id}/"
        
        return response
        
    except Exception as e:
        logger.error(f"Error creating import job: {e}")
        return Response({"error": "Erro ao iniciar importação"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def import_status(request, job_id):
    """
    Get the status of an import job.
    
    GET /api/v1/import/status/{job_id}/
    """
    try:
        job = BulkImportService.get_job(job_id)
        
        if not job:
            return Response({
                "error": f"Import job {job_id} not found"
            }, status=status.HTTP_404_NOT_FOUND)
        
        response_data = job.to_dict()
        
        if job.status == ExportStatus.COMPLETED:
            return Response(response_data, status=status.HTTP_200_OK)
        elif job.status == ExportStatus.FAILED:
            return Response(response_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            response = Response(response_data, status=status.HTTP_202_ACCEPTED)
            response["X-Progress"] = f"{job.progress}%"
            response["Retry-After"] = "5"
            return response
        
    except Exception as e:
        logger.error(f"Error getting import status: {e}")
        return Response({"error": "Erro ao obter status"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================================================
# SMART on FHIR Scopes
# ============================================================================

@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def list_smart_scopes(request):
    """
    List all supported SMART on FHIR scopes.
    
    GET /api/v1/smart/scopes/
    """
    scopes = [
        {"scope": scope, "description": desc}
        for scope, desc in SMART_SCOPES.items()
    ]
    
    return Response({
        "total": len(scopes),
        "scopes": scopes
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def validate_smart_scopes(request):
    """
    Validate a list of SMART scopes.
    
    POST /api/v1/smart/scopes/validate/
    
    Request Body:
        {
            "scopes": ["patient/*.read", "user/Patient.write", "invalid/scope"]
        }
    """
    try:
        scopes = request.data.get("scopes", [])
        
        if not scopes:
            return Response({
                "error": "No scopes provided"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        result = SMARTScopeValidator.validate_scopes(scopes)
        
        return Response(result, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error validating scopes: {e}")
        return Response({"error": "Erro ao validar escopos"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def check_smart_access(request):
    """
    Check if access is granted for specific resource and action.
    
    POST /api/v1/smart/access/check/
    
    Request Body:
        {
            "granted_scopes": ["patient/*.read", "user/Patient.write"],
            "resource_type": "Patient",
            "action": "read",
            "context": "patient"
        }
    """
    try:
        data = request.data
        granted_scopes = data.get("granted_scopes", [])
        resource_type = data.get("resource_type")
        action = data.get("action")  # 'read' or 'write'
        context = data.get("context", "user")  # 'patient', 'user', or 'system'
        
        if not resource_type or not action:
            return Response({
                "error": "resource_type and action are required"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if action not in ["read", "write"]:
            return Response({
                "error": "action must be 'read' or 'write'"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        has_access = SMARTScopeValidator.check_access(
            granted_scopes, resource_type, action, context
        )
        
        return Response({
            "resource_type": resource_type,
            "action": action,
            "context": context,
            "granted": has_access
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error checking access: {e}")
        return Response({"error": "Erro ao verificar acesso"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
