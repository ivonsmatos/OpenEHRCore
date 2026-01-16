from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
import os
import uuid
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class TranscriptionViewSet(viewsets.ViewSet):
    """
    ViewSet for handling Medical Speech-to-Text operations.
    Follows FHIR-like structure for responses where applicable.
    """
    parser_classes = (MultiPartParser, FormParser)

    @action(detail=False, methods=['get'])
    def health(self, request):
        """Simple health check endpoint to verify routing works."""
        return Response({"status": "ok", "service": "transcription"})

    @action(detail=False, methods=['post'])
    def transcribe(self, request):
        # Lazy import to avoid blocking on model loading at startup
        try:
            from .services import MedASRService
        except Exception as e:
            logger.error(f"Failed to import MedASRService: {str(e)}")
            return Response(
                {"resourceType": "OperationOutcome", "issue": [{"severity": "error", "code": "exception", "diagnostics": f"Service not available: {str(e)}"}]},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        if 'audio' not in request.FILES:
            return Response(
                {"resourceType": "OperationOutcome", "issue": [{"severity": "error", "code": "required", "diagnostics": "No audio file provided."}]},
                status=status.HTTP_400_BAD_REQUEST
            )

        audio_file = request.FILES['audio']
        
        # Save temporary file
        temp_dir = os.path.join(settings.BASE_DIR, 'temp_audio')
        os.makedirs(temp_dir, exist_ok=True)
        file_ext = os.path.splitext(audio_file.name)[1] or '.wav'
        temp_path = os.path.join(temp_dir, f"{uuid.uuid4()}{file_ext}")

        try:
            with open(temp_path, 'wb+') as destination:
                for chunk in audio_file.chunks():
                    destination.write(chunk)

            # Transcribe
            service = MedASRService()
            text = service.transcribe(temp_path)

            # Construct FHIR DocumentReference-like response (simplified)
            response_data = {
                "resourceType": "DocumentReference",
                "status": "current",
                "docStatus": "preliminary",
                "type": {
                    "coding": [
                        {
                            "system": "http://loinc.org",
                            "code": "11506-3",
                            "display": "Progress note"
                        }
                    ],
                    "text": "Medical Transcription"
                },
                "content": [
                    {
                        "attachment": {
                            "contentType": "text/plain",
                            "data": text  # In a real FHIR resource this might be base64, but for convenience we return text
                        }
                    }
                ],
                "description": text # Redundant but useful for frontend
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error during transcription view: {str(e)}")
            return Response(
                {"resourceType": "OperationOutcome", "issue": [{"severity": "error", "code": "exception", "diagnostics": str(e)}]},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
