"""
Cliente único de IA via servidor compatível com a API da OpenAI
(open-source / self-hosted).

Funciona, sem alterar o código, com:
  - vLLM            (recomendado em produção, GPU no Brasil/on-prem)
  - Ollama          (desenvolvimento local)
  - LM Studio / llama.cpp server
  - faster-whisper-server / whisper.cpp  (transcrição de áudio)

Todos expõem /v1/chat/completions e /v1/audio/transcriptions. Como o modelo
roda no SEU ambiente, os dados NÃO saem (sem transferência internacional),
o que atende melhor à LGPD para dados de saúde.

Configuração (.env):
  LLM_BASE_URL      (default http://localhost:11434/v1)   # Ollama dev / vLLM prod
  LLM_MODEL         (default qwen2.5:7b-instruct)          # ex.: llama3.3:70b em prod
  LLM_VISION_MODEL  (default qwen2.5vl:7b)
  LLM_API_KEY       (opcional — para endpoints protegidos)
  LLM_TIMEOUT       (default 60)
  ASR_BASE_URL      (default http://localhost:8001/v1)     # faster-whisper-server
  ASR_MODEL         (default Systran/faster-whisper-large-v3)
  ASR_API_KEY       (opcional)
"""

import re
import logging
import requests
from decouple import config

logger = logging.getLogger(__name__)

LLM_BASE_URL = config("LLM_BASE_URL", default="http://localhost:11434/v1").rstrip("/")
LLM_MODEL = config("LLM_MODEL", default="qwen2.5:7b-instruct")
LLM_VISION_MODEL = config("LLM_VISION_MODEL", default="qwen2.5vl:7b")
LLM_API_KEY = config("LLM_API_KEY", default="")
LLM_TIMEOUT = config("LLM_TIMEOUT", default=60, cast=int)

ASR_BASE_URL = config("ASR_BASE_URL", default="http://localhost:8001/v1").rstrip("/")
ASR_MODEL = config("ASR_MODEL", default="Systran/faster-whisper-large-v3")
ASR_API_KEY = config("ASR_API_KEY", default="")

EMBEDDINGS_MODEL = config("EMBEDDINGS_MODEL", default="bge-m3")
# Embeddings podem usar um endpoint SEPARADO do chat — ex.: chat no Gemini
# (nuvem) e embeddings locais no Ollama, para casar com o índice já gerado.
# Default: mesmo endpoint/chave do chat.
EMBEDDINGS_BASE_URL = config("EMBEDDINGS_BASE_URL", default=LLM_BASE_URL).rstrip("/")
EMBEDDINGS_API_KEY = config("EMBEDDINGS_API_KEY", default=LLM_API_KEY)

# LGPD: redigir PII (CPF, CNS, telefone, e-mail, CEP...) ANTES de enviar qualquer
# texto ao provedor de IA (Gemini/nuvem). Defesa em profundidade — minimiza
# transferência de dado pessoal. Desligue só com endpoint 100% on-premise/Brasil.
REDACT_PII_TO_LLM = config("REDACT_PII_TO_LLM", default=True, cast=bool)

# Prompt de sistema padrão: a IA é APOIO À DECISÃO (exigência do CFM).
DEFAULT_CLINICAL_SYSTEM = (
    "Você é um assistente de APOIO À DECISÃO clínica. Você NÃO realiza "
    "diagnósticos nem prescrições de forma autônoma: apenas organiza, resume e "
    "contextualiza informações para que o profissional de saúde — responsável "
    "pela decisão — avalie. Baseie-se exclusivamente nos dados e fontes "
    "fornecidos, cite as fontes quando houver e NUNCA invente informações. "
    "Responda em português do Brasil."
)

# Padrões de PII para redação antes do envio ao modelo (defesa em profundidade).
_PII_PATTERNS = {
    "cpf": r"\d{3}\.?\d{3}\.?\d{3}-?\d{2}",
    "cnpj": r"\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}",
    "cns": r"\b\d{15}\b",
    "telefone": r"\(?\d{2}\)?\s?9?\d{4}-?\d{4}",
    "email": r"[\w.\-]+@[\w.\-]+\.\w+",
    "cep": r"\b\d{5}-?\d{3}\b",
}


def redact_pii(text):
    """Substitui PII comum por marcadores. Reduz exposição de dados pessoais."""
    if not text:
        return text
    out = text
    for label, pattern in _PII_PATTERNS.items():
        out = re.sub(pattern, f"[{label.upper()}]", out)
    return out


def available():
    """True se há um endpoint de LLM configurado."""
    return bool(LLM_BASE_URL)


def _auth_headers(api_key):
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    return headers


def chat(messages, model=None, max_tokens=1000, temperature=0.3, json_mode=False, timeout=None):
    """
    Chama /v1/chat/completions (compatível com OpenAI).
    Retorna o conteúdo de texto ou None em caso de falha.
    """
    try:
        if REDACT_PII_TO_LLM:
            messages = [
                {**m, "content": redact_pii(m["content"])}
                if isinstance(m.get("content"), str)
                else m
                for m in messages
            ]
        payload = {
            "model": model or LLM_MODEL,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        resp = requests.post(
            f"{LLM_BASE_URL}/chat/completions",
            headers=_auth_headers(LLM_API_KEY),
            json=payload,
            timeout=timeout or LLM_TIMEOUT,
        )
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"]
        logger.error(f"LLM error {resp.status_code}: {resp.text[:300]}")
        return None
    except Exception as e:
        logger.error(f"Falha ao chamar LLM: {e}")
        return None


def embed(texts, model=None, timeout=None):
    """
    Gera embeddings via /v1/embeddings (compatível com OpenAI; ex.: bge-m3).
    Aceita str ou lista de str. Retorna lista de vetores (lista de floats).
    """
    single = isinstance(texts, str)
    inputs = [texts] if single else list(texts)
    if REDACT_PII_TO_LLM:
        inputs = [redact_pii(t) if isinstance(t, str) else t for t in inputs]
    try:
        resp = requests.post(
            f"{EMBEDDINGS_BASE_URL}/embeddings",
            headers=_auth_headers(EMBEDDINGS_API_KEY),
            json={"model": model or EMBEDDINGS_MODEL, "input": inputs},
            timeout=timeout or LLM_TIMEOUT,
        )
        if resp.status_code == 200:
            vectors = [item["embedding"] for item in resp.json()["data"]]
            return vectors[0] if single else vectors
        logger.error(f"Embeddings error {resp.status_code}: {resp.text[:300]}")
        return None
    except Exception as e:
        logger.error(f"Falha ao gerar embeddings: {e}")
        return None


def transcribe(file_obj, filename="audio.webm", language="pt", model=None, timeout=120):
    """
    Chama /v1/audio/transcriptions (compatível com OpenAI; faster-whisper-server).
    `file_obj` pode ser bytes ou um objeto file-like. Retorna o texto.
    """
    try:
        data = file_obj.read() if hasattr(file_obj, "read") else file_obj
        headers = {}
        if ASR_API_KEY:
            headers["Authorization"] = f"Bearer {ASR_API_KEY}"
        resp = requests.post(
            f"{ASR_BASE_URL}/audio/transcriptions",
            headers=headers,
            files={"file": (filename, data)},
            data={"model": model or ASR_MODEL, "language": language, "response_format": "json"},
            timeout=timeout,
        )
        if resp.status_code == 200:
            return resp.json().get("text", "")
        logger.error(f"ASR error {resp.status_code}: {resp.text[:300]}")
        raise RuntimeError(f"ASR error {resp.status_code}")
    except Exception as e:
        logger.error(f"Falha na transcrição: {e}")
        raise
