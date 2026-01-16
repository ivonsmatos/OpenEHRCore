import torch
from transformers import pipeline
import logging
from decouple import config

logger = logging.getLogger(__name__)

class MedASRService:
    """
    Medical Speech Recognition Service.
    Uses Google MedASR when HF_TOKEN is configured, otherwise falls back to Whisper.
    """
    _instance = None
    _pipe = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MedASRService, cls).__new__(cls)
            cls._instance._initialize_model()
        return cls._instance

    def _initialize_model(self):
        try:
            logger.info("Initializing Speech Recognition model...")
            device = "cuda:0" if torch.cuda.is_available() else "cpu"
            logger.info(f"Using device: {device}")
            
            # Check for HF_TOKEN to use MedASR (reads from .env via decouple)
            hf_token = config('HF_TOKEN', default='')
            
            if hf_token:
                logger.info("HF_TOKEN found. Using Google MedASR model...")
                self._pipe = pipeline(
                    "automatic-speech-recognition",
                    model="google/medasr",
                    token=hf_token,
                    device=device
                )
                logger.info("MedASR model initialized successfully.")
            else:
                logger.info("HF_TOKEN not found. Using Whisper as fallback...")
                self._pipe = pipeline(
                    "automatic-speech-recognition",
                    model="openai/whisper-small",
                    device=device
                )
                logger.info("Whisper model initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize ASR model: {str(e)}")
            raise e

    def transcribe(self, audio_file_path):
        if not self._pipe:
            self._initialize_model()
        
        try:
            result = self._pipe(audio_file_path)
            return result["text"]
        except Exception as e:
            logger.error(f"Transcription failed: {str(e)}")
            raise e
