"""
Views CBO - Classificação Brasileira de Ocupações
API para consulta e validação de códigos CBO
"""

import logging
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from .auth import KeycloakAuthentication
from .services.cbo_service import cbo_service

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([AllowAny])
def listar_familias_cbo(request):
    """
    Lista todas as famílias CBO de saúde.
    GET /api/v1/cbo/families/
    """
    familias = cbo_service.listar_familias()
    
    return Response({
        'count': len(familias),
        'results': [
            {'codigo': k, 'nome': v}
            for k, v in familias.items()
        ]
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def buscar_ocupacoes_cbo(request):
    """
    Busca ocupações por termo ou família.
    GET /api/v1/cbo/search/?q=medico
    GET /api/v1/cbo/search/?family=2251
    """
    termo = request.query_params.get('q', '')
    familia = request.query_params.get('family', '')
    limite = int(request.query_params.get('limit', 50))
    
    if familia:
        ocupacoes = cbo_service.listar_por_familia(familia)
    elif termo:
        ocupacoes = cbo_service.buscar_por_nome(termo, limite)
    else:
        return Response({
            'error': 'Informe q (termo) ou family (código família)'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    return Response({
        'count': len(ocupacoes),
        'results': [
            {
                'codigo': o.codigo,
                'nome': o.nome,
                'familia': o.familia,
                'familia_nome': o.familia_nome,
                'descricao': o.descricao
            }
            for o in ocupacoes
        ]
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def detalhe_cbo(request, codigo):
    """
    Obtém detalhes de uma ocupação CBO.
    GET /api/v1/cbo/{codigo}/
    """
    ocupacao = cbo_service.buscar_por_codigo(codigo)
    
    if not ocupacao:
        return Response({
            'error': f'Código CBO {codigo} não encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    
    return Response({
        'codigo': ocupacao.codigo,
        'nome': ocupacao.nome,
        'familia': ocupacao.familia,
        'familia_nome': ocupacao.familia_nome,
        'descricao': ocupacao.descricao,
        'fhir': {
            'coding': cbo_service.gerar_coding_fhir(codigo),
            'codeableConcept': cbo_service.gerar_codeable_concept_fhir(codigo)
        }
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def validar_cbo(request):
    """
    Valida um código CBO.
    POST /api/v1/cbo/validate/
    
    Body: {"codigo": "2251-25"}
    """
    codigo = request.data.get('codigo', '')
    
    if not codigo:
        return Response({
            'error': 'Código não informado'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    valido = cbo_service.validar_codigo(codigo)
    ocupacao = cbo_service.buscar_por_codigo(codigo) if valido else None
    
    return Response({
        'codigo': codigo,
        'valido': valido,
        'nome': ocupacao.nome if ocupacao else None,
        'descricao': ocupacao.descricao if ocupacao else None
    })


@api_view(['POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def gerar_qualification_practitioner(request):
    """
    Gera qualification FHIR para Practitioner.
    POST /api/v1/cbo/practitioner-qualification/
    
    Body: {
        "codigo_cbo": "2251-25",
        "numero_conselho": "123456",
        "conselho": "CRM",
        "uf": "SP"
    }
    """
    try:
        data = request.data
        
        codigo_cbo = data['codigo_cbo']
        numero_conselho = data['numero_conselho']
        conselho = data['conselho'].upper()
        uf = data['uf'].upper()
        
        # Validar CBO
        if not cbo_service.validar_codigo(codigo_cbo):
            return Response({
                'error': f'Código CBO {codigo_cbo} inválido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validar conselho
        conselhos_validos = ['CRM', 'COREN', 'CRO', 'CRF', 'CREFITO', 'CRN', 'CRFa', 'CRP', 'CRBM', 'CRESS']
        if conselho not in conselhos_validos:
            return Response({
                'error': f'Conselho inválido. Use: {", ".join(conselhos_validos)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        qualification = cbo_service.gerar_practitioner_qualification(
            codigo_cbo=codigo_cbo,
            numero_conselho=numero_conselho,
            conselho=conselho,
            uf=uf
        )
        
        return Response({
            'qualification': qualification,
            'usage': 'Adicione este objeto ao array Practitioner.qualification'
        })
        
    except KeyError as e:
        return Response({
            'error': f'Campo obrigatório: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([AllowAny])
def listar_medicos_cbo(request):
    """
    Lista especialidades médicas (família 2251).
    GET /api/v1/cbo/doctors/
    """
    ocupacoes = cbo_service.listar_por_familia('2251')
    
    return Response({
        'familia': '2251',
        'familia_nome': 'Médicos',
        'count': len(ocupacoes),
        'especialidades': [
            {
                'codigo': o.codigo,
                'nome': o.nome,
                'descricao': o.descricao
            }
            for o in ocupacoes
        ]
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def listar_enfermeiros_cbo(request):
    """
    Lista especialidades de enfermagem (família 2235).
    GET /api/v1/cbo/nurses/
    """
    ocupacoes = cbo_service.listar_por_familia('2235')
    
    return Response({
        'familia': '2235',
        'familia_nome': 'Enfermeiros e afins',
        'count': len(ocupacoes),
        'especialidades': [
            {
                'codigo': o.codigo,
                'nome': o.nome,
                'descricao': o.descricao
            }
            for o in ocupacoes
        ]
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def listar_dentistas_cbo(request):
    """
    Lista especialidades odontológicas (família 2232).
    GET /api/v1/cbo/dentists/
    """
    ocupacoes = cbo_service.listar_por_familia('2232')
    
    return Response({
        'familia': '2232',
        'familia_nome': 'Cirurgiões-dentistas',
        'count': len(ocupacoes),
        'especialidades': [
            {
                'codigo': o.codigo,
                'nome': o.nome,
                'descricao': o.descricao
            }
            for o in ocupacoes
        ]
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def listar_tecnicos_enfermagem_cbo(request):
    """
    Lista técnicos/auxiliares de enfermagem (família 3222).
    GET /api/v1/cbo/nursing-technicians/
    """
    ocupacoes = cbo_service.listar_por_familia('3222')
    
    return Response({
        'familia': '3222',
        'familia_nome': 'Técnicos e auxiliares de enfermagem',
        'count': len(ocupacoes),
        'ocupacoes': [
            {
                'codigo': o.codigo,
                'nome': o.nome,
                'descricao': o.descricao
            }
            for o in ocupacoes
        ]
    })
