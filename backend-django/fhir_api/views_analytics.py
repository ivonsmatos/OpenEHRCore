
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
import logging

from .services.analytics_service import AnalyticsService

logger = logging.getLogger(__name__)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_population_metrics(request):
    """
    GET /api/v1/analytics/population
    Retorna métricas demográficas (idade, gênero).
    """
    try:
        service = AnalyticsService()
        data = service.get_population_demographics()
        return Response(data, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Error serving population analytics: {e}")
        from django.http import JsonResponse
        return JsonResponse({"error": "Failed to generate analytics", "detail": str(e)}, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_clinical_metrics(request):
    """
    GET /api/v1/analytics/clinical
    Retorna métricas clínicas (top condições).
    """
    try:
        service = AnalyticsService()
        data = service.get_clinical_insights()
        return Response(data, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Error serving clinical analytics: {e}")
        from django.http import JsonResponse
        return JsonResponse({"error": "Failed to generate analytics", "detail": str(e)}, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_operational_metrics(request):
    """
    GET /api/v1/analytics/operational
    Retorna métricas operacionais (encounters).
    """
    try:
        service = AnalyticsService()
        data = service.get_operational_metrics()
        return Response(data, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Error serving operational analytics: {e}")
        from django.http import JsonResponse
        return JsonResponse({"error": "Failed to generate analytics", "detail": str(e)}, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_kpi_metrics(request):
    """
    GET /api/v1/analytics/kpi/
    Retorna métricas para os Cards principais.
    """
    try:
        service = AnalyticsService()
        data = service.get_kpi_summary()
        return Response(data, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Error serving KPI analytics: {e}")
        from django.http import JsonResponse
        return JsonResponse({"error": "Failed to generate analytics", "detail": str(e)}, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_survey_metrics(request):
    """
    GET /api/v1/analytics/survey/
    Retorna dados para o gráfico de linha.
    """
    try:
        service = AnalyticsService()
        data = service.get_hospital_survey_data()
        return Response(data, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Error serving survey analytics: {e}")
        from django.http import JsonResponse
        return JsonResponse({"error": "Failed to generate analytics", "detail": str(e)}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_admissions_metrics(request):
    """
    GET /api/v1/analytics/admissions/
    Retorna lista de internacoes recentes.
    """
    try:
        service = AnalyticsService()
        data = service.get_recent_admissions()
        return Response(data, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Error serving admissions analytics: {e}")
        from django.http import JsonResponse
        return JsonResponse({"error": "Failed to generate analytics", "detail": str(e)}, status=500)

