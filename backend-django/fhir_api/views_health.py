"""
Health Check Endpoint - Verificação robusta de dependências
Verifica: HAPI FHIR, PostgreSQL, Keycloak, Memória, Disco
"""

import os
import psutil
import requests
import logging
from datetime import datetime
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)

# Configurações
FHIR_SERVER_URL = getattr(settings, 'FHIR_SERVER_URL', 'http://localhost:8080/fhir')
KEYCLOAK_URL = getattr(settings, 'KEYCLOAK_URL', 'http://localhost:8180')


def check_fhir_server():
    """Verifica conexão com HAPI FHIR Server"""
    try:
        response = requests.get(
            f"{FHIR_SERVER_URL}/metadata",
            timeout=5,
            headers={'Accept': 'application/fhir+json'}
        )
        if response.status_code == 200:
            return {
                'status': 'healthy',
                'message': 'HAPI FHIR Server conectado',
                'version': response.json().get('fhirVersion', 'R4'),
                'response_time_ms': response.elapsed.total_seconds() * 1000
            }
        return {
            'status': 'unhealthy',
            'message': f'FHIR retornou status {response.status_code}',
            'response_time_ms': response.elapsed.total_seconds() * 1000
        }
    except requests.exceptions.ConnectionError:
        return {
            'status': 'unhealthy',
            'message': 'Não foi possível conectar ao HAPI FHIR Server',
            'error': 'CONNECTION_REFUSED'
        }
    except requests.exceptions.Timeout:
        return {
            'status': 'unhealthy',
            'message': 'Timeout ao conectar com HAPI FHIR',
            'error': 'TIMEOUT'
        }
    except Exception as e:
        return {
            'status': 'unhealthy',
            'message': str(e),
            'error': 'UNKNOWN'
        }


def check_database():
    """Verifica conexão com banco de dados Django"""
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return {
            'status': 'healthy',
            'message': 'Banco de dados conectado',
            'engine': connection.vendor
        }
    except Exception as e:
        return {
            'status': 'unhealthy',
            'message': f'Erro de conexão: {str(e)}',
            'error': 'DATABASE_ERROR'
        }


def check_keycloak():
    """Verifica conexão com Keycloak"""
    try:
        response = requests.get(
            f"{KEYCLOAK_URL}/health/ready",
            timeout=5
        )
        if response.status_code == 200:
            return {
                'status': 'healthy',
                'message': 'Keycloak disponível',
                'response_time_ms': response.elapsed.total_seconds() * 1000
            }
        return {
            'status': 'degraded',
            'message': f'Keycloak retornou status {response.status_code}'
        }
    except requests.exceptions.ConnectionError:
        return {
            'status': 'unhealthy',
            'message': 'Keycloak não disponível',
            'error': 'CONNECTION_REFUSED'
        }
    except Exception as e:
        return {
            'status': 'degraded',
            'message': str(e)
        }


def check_system_resources():
    """Verifica recursos do sistema (CPU, Memória, Disco)"""
    try:
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        cpu_percent = psutil.cpu_percent(interval=0.1)
        
        # Determinar status baseado nos limites
        memory_status = 'healthy' if memory.percent < 85 else 'degraded' if memory.percent < 95 else 'unhealthy'
        disk_status = 'healthy' if disk.percent < 85 else 'degraded' if disk.percent < 95 else 'unhealthy'
        cpu_status = 'healthy' if cpu_percent < 80 else 'degraded' if cpu_percent < 95 else 'unhealthy'
        
        return {
            'status': 'healthy' if all(s == 'healthy' for s in [memory_status, disk_status, cpu_status]) else 'degraded',
            'memory': {
                'status': memory_status,
                'used_percent': memory.percent,
                'available_gb': round(memory.available / (1024**3), 2)
            },
            'disk': {
                'status': disk_status,
                'used_percent': disk.percent,
                'free_gb': round(disk.free / (1024**3), 2)
            },
            'cpu': {
                'status': cpu_status,
                'used_percent': cpu_percent
            }
        }
    except Exception as e:
        return {
            'status': 'unknown',
            'message': str(e)
        }


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Endpoint de Health Check completo.
    GET /api/v1/health/
    
    Retorna status de todas as dependências:
    - HAPI FHIR Server
    - Banco de Dados
    - Keycloak
    - Recursos do Sistema
    """
    start_time = datetime.now()
    
    # Executar verificações
    checks = {
        'fhir_server': check_fhir_server(),
        'database': check_database(),
        'keycloak': check_keycloak(),
        'system': check_system_resources()
    }
    
    # Determinar status geral
    statuses = [check.get('status', 'unknown') for check in checks.values()]
    
    if all(s == 'healthy' for s in statuses):
        overall_status = 'healthy'
        http_status = status.HTTP_200_OK
    elif any(s == 'unhealthy' for s in statuses):
        overall_status = 'unhealthy'
        http_status = status.HTTP_503_SERVICE_UNAVAILABLE
    else:
        overall_status = 'degraded'
        http_status = status.HTTP_200_OK
    
    response_time = (datetime.now() - start_time).total_seconds() * 1000
    
    response_data = {
        'status': overall_status,
        'timestamp': datetime.now().isoformat(),
        'version': getattr(settings, 'VERSION', '1.0.0'),
        'environment': 'development' if settings.DEBUG else 'production',
        'response_time_ms': round(response_time, 2),
        'checks': checks
    }
    
    # Log se houver problemas
    if overall_status != 'healthy':
        logger.warning(f"Health check status: {overall_status}", extra=response_data)
    
    return Response(response_data, status=http_status)


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check_simple(request):
    """
    Health check simplificado para load balancers.
    GET /api/v1/health/live/
    
    Retorna apenas 200 OK se a aplicação está rodando.
    """
    return Response({'status': 'ok'}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check_ready(request):
    """
    Readiness check para Kubernetes.
    GET /api/v1/health/ready/
    
    Verifica se a aplicação está pronta para receber tráfego.
    """
    fhir_check = check_fhir_server()
    db_check = check_database()
    
    is_ready = (
        fhir_check.get('status') == 'healthy' and
        db_check.get('status') == 'healthy'
    )
    
    if is_ready:
        return Response({'status': 'ready'}, status=status.HTTP_200_OK)
    else:
        return Response({
            'status': 'not_ready',
            'fhir': fhir_check.get('status'),
            'database': db_check.get('status')
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
