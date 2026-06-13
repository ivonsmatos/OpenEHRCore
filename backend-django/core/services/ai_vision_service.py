import logging
from core.services import llm_client

logger = logging.getLogger(__name__)


class MedicalVisionService:
    """
    Análise de imagens médicas (APOIO À DECISÃO) usando um modelo multimodal
    open-source self-hosted, via API compatível com OpenAI (vLLM/Ollama).
    O médico é responsável pela interpretação final.
    """

    def __init__(self):
        self.vision_model = llm_client.LLM_VISION_MODEL
        self.text_model = llm_client.LLM_MODEL

    def analyze_image(self, image_base64: str, query: str) -> str:
        """
        Envia imagem (base64 ou data URL) e pergunta ao modelo de visão.
        """
        data_url = image_base64 if image_base64.startswith("data:") \
            else f"data:image/jpeg;base64,{image_base64}"
        messages = [
            {"role": "system", "content": llm_client.DEFAULT_CLINICAL_SYSTEM},
            {"role": "user", "content": [
                {"type": "text", "text": query},
                {"type": "image_url", "image_url": {"url": data_url}},
            ]},
        ]
        result = llm_client.chat(messages, model=self.vision_model, max_tokens=1024)
        if result is None:
            raise RuntimeError("Serviço de visão indisponível.")
        return result

    def refine_text(self, text: str) -> str:
        """Refina texto clínico ditado. Faz fallback para o texto original."""
        prompt = (
            "Aja como um escriba médico. Formate este texto ditado, corrigindo "
            f"termos técnicos e removendo vícios de linguagem: {text}"
        )
        result = llm_client.chat(
            [{"role": "user", "content": prompt}],
            model=self.text_model, max_tokens=1024,
        )
        return result if result else text
