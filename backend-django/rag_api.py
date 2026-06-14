"""
API mínima do Assistente Clínico (RAG) — apoio à decisão.

Expõe o caminho já validado de `fhir_api.services.rag_service` (recuperação nos
manuais + resposta fundamentada citando a fonte) como HTTP, SEM exigir o stack
Django completo (banco, Keycloak). Ideal para demo/piloto atrás do Cloudflare
Tunnel. Produção real: usar o backend Django completo + pgvector.

Rodar (a partir de backend-django/, onde está o .env):
    .venv/bin/uvicorn rag_api:app --host 127.0.0.1 --port 8010
"""

import os
import sys

# Permite importar `core` e `fhir_api` mesmo rodando de outro diretório.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from django.conf import settings  # noqa: E402

if not settings.configured:
    # Só precisamos da camada de serviço (decouple lê o .env); não subimos apps/DB.
    settings.configure(DEBUG=False)

from fastapi import FastAPI, Header, HTTPException, Depends  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from pydantic import BaseModel  # noqa: E402

from fhir_api.services import rag_service  # noqa: E402

# /docs e /openapi.json desabilitados: endpoint público não deve expor o schema.
app = FastAPI(
    title="OpenEHRCore — Assistente Clínico (RAG)",
    description="Apoio à decisão fundamentado em manuais clínicos. A IA não "
    "diagnostica nem prescreve de forma autônoma: o profissional decide.",
    version="1.0.0",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

# Proteção: /assistant exige header X-API-Key. A chave vem da env do serviço
# (ASSISTANT_API_KEY); /assistant chama o Gemini (pago), então não pode ser anônimo.
ASSISTANT_API_KEY = os.environ.get("ASSISTANT_API_KEY", "")


def require_api_key(x_api_key: str = Header(default="")):
    if not ASSISTANT_API_KEY:
        raise HTTPException(status_code=503, detail="Servidor sem ASSISTANT_API_KEY configurada.")
    if x_api_key != ASSISTANT_API_KEY:
        raise HTTPException(status_code=401, detail="X-API-Key ausente ou inválida.")

# O site institucional pode consumir esta API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://actahub.com.br",
        "https://www.actahub.com.br",
    ],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


class AssistantQuery(BaseModel):
    query: str
    k: int | None = None


@app.get("/health")
def health():
    idx = rag_service.load_index()
    return {
        "status": "ok",
        "rag_enabled": rag_service.RAG_ENABLED,
        "mode": rag_service.RAG_MODE,
        "chunks": len(idx.get("chunks", [])) if idx else 0,
        "embeddings_model": idx.get("model") if idx else None,
    }


@app.post("/assistant", dependencies=[Depends(require_api_key)])
def assistant(q: AssistantQuery):
    """Responde fundamentado nos manuais, citando a fonte. Apoio à decisão."""
    return rag_service.answer(q.query, k=q.k)
