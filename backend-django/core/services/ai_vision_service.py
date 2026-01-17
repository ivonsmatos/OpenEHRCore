import requests
import json
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

class MedicalVisionService:
    """
    Service for Medical Image Analysis using MedGemma via Ollama.
    """
    
    def __init__(self):
        # Configure Ollama URL from settings or default
        self.ollama_url = getattr(settings, 'OLLAMA_URL', 'http://ollama:11434/api/generate')
        self.model = "yenjia/medgemma-1.5-4b-it" 

    def analyze_image(self, image_base64: str, query: str) -> str:
        """
        Sends image and query to MedGemma (Ollama).
        """
        try:
            payload = {
                "model": self.model,
                "prompt": query,
                "images": [image_base64],
                "stream": False
            }
            
            response = requests.post(self.ollama_url, json=payload)
            response.raise_for_status()
            
            return response.json().get('response', '')
            
        except Exception as e:
            logger.error(f"MedGemma Analysis Failed: {str(e)}")
            raise e

    def refine_text(self, text: str) -> str:
        """
        Refines clinical text using MedGemma as an LLM.
        """
        prompt = f"Aja como um escriba médico. Formate este texto ditado, corrigindo termos técnicos e removendo vícios de linguagem: {text}"
        
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False
            }
            
            response = requests.post(self.ollama_url, json=payload)
            response.raise_for_status()
            
            return response.json().get('response', '')
            
        except Exception as e:
            logger.error(f"MedGemma Text Refinement Failed: {str(e)}")
            # Fallback to original text if LLM fails
            return text
