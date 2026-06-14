"""Testes unitários do RAG (sem rede): chunking e similaridade de cosseno."""

from fhir_api.services import rag_service


def test_chunk_text_empty():
    assert rag_service.chunk_text("") == []
    assert rag_service.chunk_text("   ") == []


def test_chunk_text_splits_long_text():
    para = "Parágrafo de teste com conteúdo clínico relevante."
    text = "\n\n".join([para] * 80)  # bem maior que max_chars
    chunks = rag_service.chunk_text(text, max_chars=300, overlap=50)
    assert len(chunks) > 1
    assert all(len(c) <= 300 + 50 for c in chunks)


def test_cosine_identical_and_orthogonal():
    a = [1.0, 0.0, 0.0]
    assert abs(rag_service._cosine(a, a) - 1.0) < 1e-9
    assert abs(rag_service._cosine([1.0, 0.0], [0.0, 1.0])) < 1e-9


def test_cosine_handles_zero_vector():
    assert rag_service._cosine([0.0, 0.0], [1.0, 1.0]) == 0.0
