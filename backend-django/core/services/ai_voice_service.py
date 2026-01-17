import logging
import requests
from decouple import config
import tempfile
import os

logger = logging.getLogger(__name__)

class MedicalVoiceService:
    """
    Medical Voice Service using Groq's Whisper API.
    Provides ultra-fast speech-to-text via Groq's LPU inference.
    """
    _instance = None
    
    # Groq API configuration
    GROQ_API_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
    GROQ_API_KEY = config('GROQ_API_KEY', default='')
    MODEL = "whisper-large-v3-turbo"  # Fastest model, ~200x real-time

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MedicalVoiceService, cls).__new__(cls)
        return cls._instance

    def transcribe_clinical_audio(self, audio_file) -> str:
        """
        Transcribes audio using Groq's Whisper API.
        Ultra-fast inference via Groq's LPU hardware.
        
        Args:
            audio_file: Django InMemoryUploadedFile or file-like object
            
        Returns:
            Transcribed text string
        """
        if not self.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY not configured. Set it in environment variables.")
        
        try:
            # Read audio bytes from uploaded file
            audio_bytes = audio_file.read()
            
            # Get file extension from name or default to webm
            file_name = getattr(audio_file, 'name', 'audio.webm')
            
            # Create temp file for Groq API (requires file, not bytes)
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file_name)[1] or '.webm') as tmp:
                tmp.write(audio_bytes)
                tmp_path = tmp.name
            
            try:
                # Call Groq Whisper API
                headers = {
                    "Authorization": f"Bearer {self.GROQ_API_KEY}"
                }
                
                with open(tmp_path, 'rb') as audio:
                    files = {
                        'file': (file_name, audio, 'audio/webm'),
                        'model': (None, self.MODEL),
                        'language': (None, 'pt'),  # Portuguese
                        'response_format': (None, 'json'),
                    }
                    
                    response = requests.post(
                        self.GROQ_API_URL,
                        headers=headers,
                        files=files,
                        timeout=30
                    )
                
                if response.status_code == 200:
                    result = response.json()
                    text = result.get('text', '')
                    logger.info(f"Groq transcription successful: {len(text)} characters")
                    return text
                else:
                    logger.error(f"Groq API error: {response.status_code} - {response.text}")
                    raise Exception(f"Groq API error: {response.status_code}")
                    
            finally:
                # Clean up temp file
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                    
        except Exception as e:
            logger.error(f"Transcription failed: {str(e)}")
            raise e
