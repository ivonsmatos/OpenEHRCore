
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
import logging
from io import BytesIO
from datetime import datetime
from django.http import HttpResponse

# ReportLab imports
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet

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


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def generate_analytics_report(request):
    """
    GET /api/v1/analytics/report/
    Gera um relatório gerencial em PDF com os KPIs atuais.
    """
    try:
        service = AnalyticsService()
        
        # Fetching Data
        kpi = service.get_kpi_summary()
        survey = service.get_hospital_survey_data()
        clinical = service.get_clinical_insights()
        
        # Buffer for PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=18)
        
        elements = []
        styles = getSampleStyleSheet()
        
        # Title
        elements.append(Paragraph("Relatório Gerencial Hospitalar", styles['Title']))
        elements.append(Spacer(1, 12))
        
        # Header Info
        date_str = datetime.now().strftime("%d/%m/%Y %H:%M")
        elements.append(Paragraph(f"Gerado em: {date_str}", styles['Normal']))
        user_display = getattr(request.user, 'username', str(request.user))
        elements.append(Paragraph(f"Solicitado por: {user_display}", styles['Normal']))
        elements.append(Spacer(1, 24))
        
        # Section 1: KPIs
        elements.append(Paragraph("Indicadores Principais (KPIs)", styles['Heading2']))
        elements.append(Spacer(1, 12))
        
        kpi_data = [
            ["Indicador", "Valor"],
            ["Novos Pacientes", str(kpi.get('new_patients', 0))],
            ["Pacientes Ambulatório", str(kpi.get('opd_patients', 0))],
            ["Cirurgias Hoje", str(kpi.get('todays_operations', 0))],
            ["Visitantes", str(kpi.get('visitors', 0))]
        ]
        
        t_kpi = Table(kpi_data, colWidths=[200, 100])
        t_kpi.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(t_kpi)
        elements.append(Spacer(1, 24))

        # Section 2: Clinical Data
        elements.append(Paragraph("Top Condições Clínicas", styles['Heading2']))
        elements.append(Spacer(1, 12))
        
        conditions = clinical.get('series', [{}])[0].get('data', [])
        # Mocking labels from service if available, or just generic
        # The service returns 'series' and 'options' usually for charts.
        # Let's inspect clinical data structure in verification step or assume standard ApexCharts format
        # Clinical structure in analytics_service.py: { "series": [{"data": [...]}], "xaxis": {"categories": [...]} }
        
        clin_cats = clinical.get('xaxis', {}).get('categories', [])
        clin_vals = conditions
        
        clin_table_data = [["Condição", "Casos"]]
        for i in range(min(len(clin_cats), len(clin_vals))):
             clin_table_data.append([clin_cats[i], str(clin_vals[i])])
             
        if len(clin_table_data) > 1:
            t_clin = Table(clin_table_data, colWidths=[200, 100])
            t_clin.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.cadetblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(t_clin)
        else:
            elements.append(Paragraph("Nenhum dado clínico disponível.", styles['Normal']))
            
        elements.append(Spacer(1, 24))
        
        # Build PDF
        doc.build(elements)
        
        # Response
        pdf = buffer.getvalue()
        buffer.close()
        
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="relatorio_gerencial_{datetime.now().strftime("%Y%m%d")}.pdf"'
        response.write(pdf)
        return response
        
    except Exception as e:
        logger.error(f"Error generating PDF report: {e}")
        from django.http import JsonResponse
        return JsonResponse({"error": "Failed to generate report", "detail": str(e)}, status=500)
