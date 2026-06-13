"""
Ingestão dos manuais clínicos para a base de conhecimento (RAG).

Uso:
    python manage.py ingest_knowledge
    python manage.py ingest_knowledge --docs-dir data/clinical_docs --index data/knowledge_index.json

Pré-requisitos:
    - LLM_BASE_URL apontando para um servidor de embeddings (Ollama/vLLM)
    - EMBEDDINGS_MODEL configurado (ex.: bge-m3)
    - Documentos .txt/.md/.pdf em RAG_DOCS_DIR
"""

from django.core.management.base import BaseCommand

from fhir_api.services import rag_service


class Command(BaseCommand):
    help = "Gera o índice RAG a partir dos manuais clínicos (txt/md/pdf)."

    def add_arguments(self, parser):
        parser.add_argument("--docs-dir", default=None, help="Diretório dos documentos.")
        parser.add_argument("--index", default=None, help="Caminho do índice de saída.")

    def handle(self, *args, **options):
        self.stdout.write("Gerando índice RAG dos manuais clínicos...")
        try:
            stats = rag_service.build_index(
                docs_dir=options["docs_dir"],
                index_path=options["index"],
            )
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Falha na ingestão: {e}"))
            return

        if stats.get("chunks"):
            self.stdout.write(self.style.SUCCESS(
                f"OK: {stats['files']} arquivo(s), {stats['chunks']} trecho(s) -> {stats.get('index_path')}"
            ))
        else:
            self.stdout.write(self.style.WARNING(
                "Nenhum documento encontrado. Coloque os manuais em data/clinical_docs/."
            ))
