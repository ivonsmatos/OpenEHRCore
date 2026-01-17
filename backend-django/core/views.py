from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework import status
import logging

logger = logging.getLogger(__name__)


class AnalyzeImageView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser]

    def post(self, request):
        """
        Analyze a medical image using MedGemma.
        Payload: { "image": "base64...", "query": "Describe..." }
        """
        from .services.ai_vision_service import MedicalVisionService
        
        image_data = request.data.get('image')
        query = request.data.get('query', 'Describe this medical image.')
        
        if not image_data:
            return Response({"error": "Image data required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            service = MedicalVisionService()
            result = service.analyze_image(image_data, query)
            return Response({"analysis": result})
        except Exception as e:
            logger.error(f"Image analysis error: {e}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TranscribeAudioView(APIView):
    """
    Transcribes clinical audio using Groq Whisper API.
    Ultra-fast transcription with whisper-large-v3-turbo.
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        from .services.ai_voice_service import MedicalVoiceService
        
        # Get audio file from request
        audio_file = request.FILES.get('audio') or request.data.get('audio')
        
        if not audio_file:
            return Response(
                {"error": "Audio file required. Send as 'audio' field."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Transcribe using Groq Whisper API
            voice_service = MedicalVoiceService()
            transcribed_text = voice_service.transcribe_clinical_audio(audio_file)
            
            return Response({
                "text": transcribed_text,
                "success": True
            })
            
        except ValueError as e:
            # API key not configured
            logger.error(f"Transcription config error: {e}")
            return Response(
                {"error": str(e), "success": False}, 
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return Response(
                {"error": f"Failed to transcribe audio: {str(e)}", "success": False}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ParseClinicalNoteView(APIView):
    """
    Parses clinical note text and extracts structured data.
    Creates FHIR resources for: medications, diagnoses, exams, vitals.
    Uses Groq Llama 3.3 70B for NLP extraction.
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser]

    def post(self, request):
        from .services.clinical_parser_service import ClinicalParserService
        
        text = request.data.get('text', '')
        patient_id = request.data.get('patient_id')
        encounter_id = request.data.get('encounter_id')
        
        if not text:
            return Response(
                {"error": "Clinical note text required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not patient_id:
            return Response(
                {"error": "patient_id required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            parser_service = ClinicalParserService()
            result = parser_service.parse_clinical_note(
                text=text,
                patient_id=patient_id,
                encounter_id=encounter_id
            )
            
            if "error" in result and not result.get("resources_created"):
                return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            return Response(result)
            
        except Exception as e:
            logger.error(f"Clinical parsing error: {e}")
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GetPatientSummaryView(APIView):
    """
    Generates AI-powered patient summary using Groq Llama 3.3 70B.
    Analyzes FHIR data and returns: complexity, recommendations, alerts.
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser]

    def get(self, request, patient_id):
        from .services.ai_summary_service import AISummaryService
        
        if not patient_id:
            return Response(
                {"error": "patient_id required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            summary_service = AISummaryService()
            result = summary_service.generate_patient_summary(patient_id)
            return Response(result)
            
        except Exception as e:
            logger.error(f"Summary generation error: {e}")
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
