from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework import status
from .services.ai_vision_service import MedicalVisionService
from .services.ai_voice_service import MedicalVoiceService

class AnalyzeImageView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser]

    def post(self, request):
        """
        Analyze a medical image.
        Payload: { "image": "base64...", "query": "Describe..." }
        """
        image_data = request.data.get('image')
        query = request.data.get('query', 'Describe this medical image.')
        
        if not image_data:
            return Response({"error": "Image data required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            service = MedicalVisionService()
            result = service.analyze_image(image_data, query)
            return Response({"analysis": result})
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class TranscribeAudioView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        """
        Transcribe clinical audio and clean it via MedGemma.
        File field: 'audio'
        """
        audio_file = request.files.get('audio')
        if not audio_file:
            # DRF uses request.data for files in MultiPart
            audio_file = request.data.get('audio')

        if not audio_file:
            return Response({"error": "Audio file required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # 1. Transcribe (MedASR)
            voice_service = MedicalVoiceService()
            raw_text = voice_service.transcribe_clinical_audio(audio_file)
            
            # 2. Refine (MedGemma - "O Pulo do Gato")
            vision_service = MedicalVisionService() # Also handles LLM Tasks
            refined_text = vision_service.refine_text(raw_text)
            
            return Response({
                "original_transcription": raw_text,
                "clinical_note": refined_text
            })
            
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
