import logging
from core.services import llm_client

logger = logging.getLogger(__name__)


class MedicalVoiceService:
    """
    Transcrição de áudio clínico (speech-to-text) usando um servidor Whisper
    open-source self-hosted (faster-whisper-server / whisper.cpp), via API
    compatível com OpenAI. O áudio não sai do seu ambiente (LGPD).
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MedicalVoiceService, cls).__new__(cls)
        return cls._instance

    def transcribe_clinical_audio(self, audio_file) -> str:
        """
        Transcreve áudio (objeto file-like do Django ou bytes).

        Returns:
            Texto transcrito.
        """
        file_name = getattr(audio_file, "name", "audio.webm")
        text = llm_client.transcribe(audio_file, filename=file_name, language="pt")
        logger.info(f"Transcrição concluída: {len(text)} caracteres")
        return text
