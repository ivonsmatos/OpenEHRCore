"""
Views TISS - Endpoints para geração de guias TISS/ANS
"""

import logging
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework import status
from .auth import KeycloakAuthentication
from rest_framework.permissions import IsAuthenticated
from .services.tiss_service import (
    TISSService, TipoGuia, StatusGuia,
    DadosBeneficiario, DadosPrestador, Procedimento
)

logger = logging.getLogger(__name__)


def _get_tiss_service(request) -> TISSService:
    """Obtém instância do TISSService com dados do prestador"""
    # Em produção, buscar dados do prestador do banco/configurações
    prestador = DadosPrestador(
        codigo_na_operadora='PREST001',
        nome='Hospital OpenEHR',
        cnpj='00.000.000/0001-00',
        cnes='0000000',
        conselho_profissional='CRM',
        numero_conselho='12345',
        uf_conselho='SP'
    )
    return TISSService(prestador)


@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def tiss_tipos_guia(request):
    """
    Lista tipos de guias TISS disponíveis
    GET /api/v1/tiss/tipos/
    """
    tipos = [
        {'codigo': 'consulta', 'nome': 'Guia de Consulta', 'descricao': 'Para atendimentos ambulatoriais'},
        {'codigo': 'sadt', 'nome': 'Guia SP/SADT', 'descricao': 'Exames e procedimentos ambulatoriais'},
        {'codigo': 'internacao', 'nome': 'Guia de Internação', 'descricao': 'Admissões hospitalares'},
        {'codigo': 'honorarios', 'nome': 'Guia de Honorários', 'descricao': 'Honorários profissionais'},
    ]
    return Response({'tipos': tipos, 'versao_tiss': '4.01.00'})


@api_view(['POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def gerar_guia_consulta(request):
    """
    Gera Guia de Consulta TISS
    POST /api/v1/tiss/consulta/
    
    Body:
    {
        "beneficiario": {
            "numero_carteira": "123456789",
            "nome": "Nome do Paciente",
            "data_nascimento": "1990-01-01",
            "cpf": "12345678901"
        },
        "data_atendimento": "2024-01-15",
        "tipo_consulta": "1",
        "procedimento": {
            "codigo": "10101012",
            "descricao": "Consulta em consultório",
            "valor_unitario": 150.00
        },
        "numero_guia_operadora": "AUTH123456"
    }
    """
    try:
        data = request.data
        tiss_service = _get_tiss_service(request)
        
        # Validar dados obrigatórios
        if not data.get('beneficiario'):
            return Response({'error': 'Dados do beneficiário são obrigatórios'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Construir objetos
        beneficiario = DadosBeneficiario(
            numero_carteira=data['beneficiario']['numero_carteira'],
            nome=data['beneficiario']['nome'],
            data_nascimento=data['beneficiario']['data_nascimento'],
            cpf=data['beneficiario'].get('cpf'),
            cns=data['beneficiario'].get('cns')
        )
        
        proc_data = data.get('procedimento', {})
        procedimento = Procedimento(
            codigo=proc_data.get('codigo', '10101012'),
            descricao=proc_data.get('descricao', 'Consulta em consultório'),
            quantidade=proc_data.get('quantidade', 1),
            valor_unitario=float(proc_data.get('valor_unitario', 0))
        )
        
        # Gerar guia
        guia = tiss_service.gerar_guia_consulta(
            beneficiario=beneficiario,
            data_atendimento=data.get('data_atendimento'),
            tipo_consulta=data.get('tipo_consulta', '1'),
            procedimento=procedimento,
            numero_guia_operadora=data.get('numero_guia_operadora'),
            observacoes=data.get('observacoes')
        )
        
        # Validar guia
        validacao = tiss_service.validar_guia(guia)
        
        return Response({
            'guia': guia,
            'validacao': validacao
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Erro ao gerar guia de consulta: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def gerar_guia_sadt(request):
    """
    Gera Guia SP/SADT TISS
    POST /api/v1/tiss/sadt/
    
    Body:
    {
        "beneficiario": {...},
        "data_solicitacao": "2024-01-15",
        "indicacao_clinica": "Investigação diagnóstica",
        "carater_atendimento": "E",
        "procedimentos": [
            {"codigo": "40301630", "descricao": "Hemograma completo", "quantidade": 1, "valor_unitario": 25.00}
        ]
    }
    """
    try:
        data = request.data
        tiss_service = _get_tiss_service(request)
        
        beneficiario = DadosBeneficiario(
            numero_carteira=data['beneficiario']['numero_carteira'],
            nome=data['beneficiario']['nome'],
            data_nascimento=data['beneficiario']['data_nascimento'],
            cpf=data['beneficiario'].get('cpf')
        )
        
        procedimentos = []
        for p in data.get('procedimentos', []):
            procedimentos.append(Procedimento(
                codigo=p['codigo'],
                descricao=p['descricao'],
                quantidade=p.get('quantidade', 1),
                valor_unitario=float(p.get('valor_unitario', 0)),
                via_acesso=p.get('via_acesso'),
                tecnica=p.get('tecnica')
            ))
        
        guia = tiss_service.gerar_guia_sadt(
            beneficiario=beneficiario,
            procedimentos=procedimentos,
            data_solicitacao=data.get('data_solicitacao'),
            indicacao_clinica=data.get('indicacao_clinica', ''),
            carater_atendimento=data.get('carater_atendimento', 'E'),
            numero_guia_operadora=data.get('numero_guia_operadora')
        )
        
        validacao = tiss_service.validar_guia(guia)
        
        return Response({
            'guia': guia,
            'validacao': validacao
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Erro ao gerar guia SP/SADT: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def gerar_guia_internacao(request):
    """
    Gera Guia de Internação TISS
    POST /api/v1/tiss/internacao/
    """
    try:
        data = request.data
        tiss_service = _get_tiss_service(request)
        
        beneficiario = DadosBeneficiario(
            numero_carteira=data['beneficiario']['numero_carteira'],
            nome=data['beneficiario']['nome'],
            data_nascimento=data['beneficiario']['data_nascimento'],
            cpf=data['beneficiario'].get('cpf'),
            cns=data['beneficiario'].get('cns')
        )
        
        proc_data = data.get('procedimento_principal', {})
        procedimento = Procedimento(
            codigo=proc_data['codigo'],
            descricao=proc_data['descricao'],
            quantidade=proc_data.get('quantidade', 1),
            valor_unitario=float(proc_data.get('valor_unitario', 0))
        )
        
        guia = tiss_service.gerar_guia_internacao(
            beneficiario=beneficiario,
            data_internacao=data['data_internacao'],
            hora_internacao=data.get('hora_internacao', '08:00'),
            carater_internacao=data.get('carater_internacao', '1'),
            tipo_internacao=data.get('tipo_internacao', '1'),
            regime_internacao=data.get('regime_internacao', '1'),
            procedimento_principal=procedimento,
            cid_principal=data['cid_principal'],
            previsao_diarias=int(data.get('previsao_diarias', 3)),
            numero_guia_operadora=data.get('numero_guia_operadora'),
            data_alta=data.get('data_alta'),
            motivo_alta=data.get('motivo_alta')
        )
        
        validacao = tiss_service.validar_guia(guia)
        
        return Response({
            'guia': guia,
            'validacao': validacao
        }, status=status.HTTP_201_CREATED)
        
    except KeyError as e:
        return Response({'error': f'Campo obrigatório ausente: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Erro ao gerar guia de internação: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def gerar_lote_tiss(request):
    """
    Gera lote de guias TISS para envio
    POST /api/v1/tiss/lote/
    
    Body:
    {
        "guias": [<lista de guias>]
    }
    """
    try:
        data = request.data
        tiss_service = _get_tiss_service(request)
        
        guias = data.get('guias', [])
        if not guias:
            return Response({'error': 'Nenhuma guia fornecida'}, status=status.HTTP_400_BAD_REQUEST)
        
        lote = tiss_service.gerar_lote_guias(guias)
        
        return Response({
            'lote': lote,
            'message': f'Lote gerado com {len(guias)} guia(s)'
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Erro ao gerar lote TISS: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def validar_guia_tiss(request):
    """
    Valida guia TISS
    POST /api/v1/tiss/validar/
    """
    try:
        data = request.data
        tiss_service = _get_tiss_service(request)
        
        guia = data.get('guia', {})
        if not guia:
            return Response({'error': 'Guia não fornecida'}, status=status.HTTP_400_BAD_REQUEST)
        
        validacao = tiss_service.validar_guia(guia)
        
        return Response(validacao)
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
