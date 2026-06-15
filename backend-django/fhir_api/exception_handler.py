"""
Handler de exceções padronizado da API: respostas de erro consistentes
no formato {"error", "detail", "status"} em vez de 500 genéricos/HTML.
"""

import logging

from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

logger = logging.getLogger(__name__)


def api_exception_handler(exc, context):
    response = drf_exception_handler(exc, context)

    if response is not None:
        data = response.data
        # Normaliza o "detail" do DRF para uma mensagem; mantém dicts de validação.
        if isinstance(data, dict) and set(data.keys()) == {"detail"}:
            detail = data["detail"]
        else:
            detail = data
        response.data = {
            "error": exc.__class__.__name__,
            "detail": detail,
            "status": response.status_code,
        }
        return response

    # Exceção não tratada pelo DRF. Em DEBUG, deixa o Django mostrar o traceback.
    if settings.DEBUG:
        return None

    logger.exception("Unhandled API exception", exc_info=exc)
    return Response(
        {"error": "InternalServerError", "detail": "Erro interno do servidor.", "status": 500},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
