"""
RAG (Retrieval-Augmented Generation) sobre manuais clínicos.

NÃO é treinamento/fine-tuning: os documentos viram uma base de conhecimento
pesquisável. A IA recupera os trechos mais relevantes e responde CITANDO A
FONTE — sempre como apoio à decisão; o profissional decide.

Fluxo:
  1. Ingestão: ler documentos (.txt/.md/.pdf) -> dividir em trechos -> embeddings
     (self-hosted, via llm_client.embed) -> salvar índice JSON.
  2. Consulta: embeddar a pergunta -> similaridade de cosseno -> top-k trechos ->
     montar prompt fundamentado -> llm_client.chat.

Produção/escala: trocar o índice JSON por pgvector (Postgres). A interface
pública (retrieve/answer) permanece a mesma.
"""

import os
import json
import math
import glob
import logging
from datetime import datetime, timezone

from decouple import config

from core.services import llm_client

logger = logging.getLogger(__name__)

RAG_ENABLED = config("RAG_ENABLED", default=False, cast=bool)
RAG_DOCS_DIR = config("RAG_DOCS_DIR", default="data/clinical_docs")
RAG_INDEX_PATH = config("RAG_INDEX_PATH", default="data/knowledge_index.json")
RAG_TOP_K = config("RAG_TOP_K", default=5, cast=int)
RAG_MIN_SCORE = config("RAG_MIN_SCORE", default=0.30, cast=float)
# 'generate' = LLM redige a resposta citando a fonte;
# 'retrieval' = sem LLM (custo zero): devolve os trechos do manual + fonte.
RAG_MODE = config("RAG_MODE", default="generate")

_index_cache = None


# ---------------------------------------------------------------------------
# Ingestão
# ---------------------------------------------------------------------------
def _read_file(path):
    ext = os.path.splitext(path)[1].lower()
    if ext in (".txt", ".md"):
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    if ext == ".pdf":
        try:
            from pypdf import PdfReader
        except ImportError:
            logger.warning("pypdf não instalado — pulando PDF %s (pip install pypdf)", path)
            return ""
        try:
            reader = PdfReader(path)
            return "\n".join((page.extract_text() or "") for page in reader.pages)
        except Exception as e:
            logger.warning("Falha ao ler PDF %s: %s", path, e)
            return ""
    return ""


def chunk_text(text, max_chars=1200, overlap=150):
    """Divide o texto em trechos com sobreposição, respeitando parágrafos."""
    text = (text or "").strip()
    if not text:
        return []
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks, buffer = [], ""
    for para in paragraphs:
        if len(buffer) + len(para) + 2 <= max_chars:
            buffer = f"{buffer}\n\n{para}".strip()
        else:
            if buffer:
                chunks.append(buffer)
            # overlap: mantém o final do trecho anterior como contexto
            tail = buffer[-overlap:] if buffer else ""
            buffer = f"{tail}\n\n{para}".strip() if tail else para
            # se um único parágrafo for maior que max_chars, fatia bruto
            while len(buffer) > max_chars:
                chunks.append(buffer[:max_chars])
                buffer = buffer[max_chars - overlap:]
    if buffer:
        chunks.append(buffer)
    return chunks


def build_index(docs_dir=None, index_path=None, batch_size=16):
    """Lê os documentos, gera embeddings e grava o índice JSON. Retorna stats."""
    docs_dir = docs_dir or RAG_DOCS_DIR
    index_path = index_path or RAG_INDEX_PATH

    files = []
    for ext in ("txt", "md", "pdf"):
        files.extend(glob.glob(os.path.join(docs_dir, "**", f"*.{ext}"), recursive=True))
    if not files:
        logger.warning("Nenhum documento encontrado em %s", docs_dir)
        return {"files": 0, "chunks": 0}

    records = []
    for path in sorted(files):
        source = os.path.relpath(path, docs_dir)
        text = _read_file(path)
        for i, chunk in enumerate(chunk_text(text)):
            # Ignora trechos vazios/curtos (ex.: páginas de PDF sem texto) —
            # eles fazem o provedor de embeddings rejeitar o lote inteiro.
            if chunk and len(chunk.strip()) >= 3:
                records.append({"source": source, "section": f"parte {i + 1}", "text": chunk.strip()})

    # Embeddings em lotes, de forma RESILIENTE: se um lote falha, tenta item a
    # item e pula apenas o(s) trecho(s) problemático(s) (não aborta tudo).
    good = []
    for start in range(0, len(records), batch_size):
        batch_recs = records[start:start + batch_size]
        vecs = llm_client.embed([r["text"] for r in batch_recs], timeout=600)
        if vecs and len(vecs) == len(batch_recs):
            for r, v in zip(batch_recs, vecs):
                r["embedding"] = v
                good.append(r)
        else:
            for r in batch_recs:
                v = llm_client.embed(r["text"], timeout=120)
                if v:
                    r["embedding"] = v
                    good.append(r)
                else:
                    logger.warning("Trecho ignorado (embedding falhou) em %s/%s", r["source"], r.get("section"))

    if not good:
        raise RuntimeError("Falha ao gerar embeddings — verifique LLM_BASE_URL/EMBEDDINGS_MODEL.")
    records = good

    os.makedirs(os.path.dirname(index_path) or ".", exist_ok=True)
    payload = {
        "model": llm_client.EMBEDDINGS_MODEL,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "chunks": records,
    }
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)

    global _index_cache
    _index_cache = payload
    logger.info("Índice RAG gerado: %d arquivos, %d trechos", len(files), len(records))
    return {"files": len(files), "chunks": len(records), "index_path": index_path}


# ---------------------------------------------------------------------------
# Consulta
# ---------------------------------------------------------------------------
def load_index(index_path=None):
    global _index_cache
    if _index_cache is not None:
        return _index_cache
    index_path = index_path or RAG_INDEX_PATH
    if not os.path.exists(index_path):
        return None
    with open(index_path, "r", encoding="utf-8") as f:
        _index_cache = json.load(f)
    return _index_cache


def _cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


def retrieve(query, k=None, min_score=None):
    """Retorna [(score, chunk)] dos top-k trechos mais relevantes."""
    k = k or RAG_TOP_K
    min_score = RAG_MIN_SCORE if min_score is None else min_score
    index = load_index()
    if not index or not index.get("chunks"):
        return []
    qvec = llm_client.embed(query)
    if not qvec:
        return []
    scored = [(_cosine(qvec, c["embedding"]), c) for c in index["chunks"]]
    scored.sort(key=lambda x: x[0], reverse=True)
    return [(s, c) for s, c in scored[:k] if s >= min_score]


def answer(query, k=None):
    """
    Responde à pergunta fundamentada nos manuais, citando a fonte.
    Retorna {'answer': str, 'sources': [...], 'grounded': bool}.
    """
    if not RAG_ENABLED:
        return {"answer": "RAG desativado (defina RAG_ENABLED=True).", "sources": [], "grounded": False}

    hits = retrieve(query, k=k)
    if not hits:
        return {
            "answer": "Não encontrei evidência sobre isso nos manuais cadastrados.",
            "sources": [],
            "grounded": False,
        }

    context_blocks, sources = [], []
    for i, (score, c) in enumerate(hits, start=1):
        ref = f"{c['source']} ({c.get('section', '')})".strip()
        context_blocks.append(f"[Fonte {i}: {ref}]\n{c['text']}")
        sources.append({"index": i, "source": c["source"], "section": c.get("section"), "score": round(score, 3)})

    # Modo retrieval-only: sem LLM (custo zero) — devolve os trechos + fonte.
    if RAG_MODE == "retrieval":
        return {
            "answer": "\n\n".join(context_blocks),
            "sources": sources,
            "grounded": True,
            "mode": "retrieval",
        }

    prompt = (
        "Responda à pergunta do profissional de saúde usando SOMENTE os trechos "
        "dos manuais abaixo. Cite a fonte entre colchetes (ex.: [Fonte 1]). Se a "
        "resposta não estiver nos trechos, diga que não há evidência no material.\n\n"
        f"PERGUNTA: {query}\n\nTRECHOS:\n" + "\n\n".join(context_blocks)
    )
    text = llm_client.chat(
        [
            {"role": "system", "content": llm_client.DEFAULT_CLINICAL_SYSTEM},
            {"role": "user", "content": prompt},
        ],
        max_tokens=900,
    )
    return {
        "answer": text or "Serviço de IA indisponível.",
        "sources": sources,
        "grounded": bool(text),
    }
