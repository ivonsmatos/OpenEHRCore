"""
CRM Validation API Views

Sprint 37+: Endpoints para validação de registros em conselhos profissionais.
Segue padrões LGPD, FHIR, GDPR.

Endpoints:
- POST /api/v1/crm/validate/ - Validar registro individual
- POST /api/v1/crm/validate-batch/ - Validar múltiplos registros
- GET /api/v1/crm/info/ - Informações sobre o serviço de validação
"""

import logging
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from .services.crm_validation_service import (
    CRMValidationService,
    ConselhoTipo,
    ValidationStatus
)

logger = logging.getLogger(__name__)


def get_client_ip(request) -> str:
    """Extrai IP do cliente de forma segura"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', 'unknown')


@api_view(['GET'])
@permission_classes([AllowAny])
def crm_validation_info(request):
    """
    GET /api/v1/crm/info/

    Informações sobre o serviço de validação de CRM.
    Não requer autenticação.
    """
    return Response({
        "service": "CRM Validation Service",
        "version": "1.0.0",
        "description": "Validação de registros em conselhos profissionais de saúde",
        "supported_councils": [c.value for c in ConselhoTipo],
        "valid_ufs": CRMValidationService.UF_VALIDAS,
        "validation_modes": {
            "local": "Validação de formato (sempre disponível)",
            "api": "Validação via API do conselho (quando disponível)"
        },
        "compliance": {
            "lgpd": True,
            "fhir_r4": True,
            "gdpr": True
        },
        "api_status": {
            "cfm": "configured" if CRMValidationService.CFM_API_URL else "not_configured",
            "coren": "not_configured",
            "cro": "not_configured"
        },
        "notes": [
            "A validação local verifica apenas o formato do número.",
            "A validação via API confirma o registro no conselho.",
            "Apenas dados públicos são retornados (LGPD Art. 7, II).",
            "Todas as validações são registradas em audit log."
        ],
        "documentation": "https://github.com/ivonsmatos/OpenEHRCore#crm-validation"
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def validate_crm(request):
    """
    POST /api/v1/crm/validate/

    Valida um registro de conselho profissional.

    Request body:
    {
        "conselho": "CRM",      // Obrigatório: CRM, COREN, CRO, etc.
        "numero": "123456",     // Obrigatório: número do registro
        "uf": "SP",             // Obrigatório: UF do conselho
        "use_api": true         // Opcional: se deve tentar validar via API externa
    }

    Response (200):
    {
        "status": "valid",
        "conselho": "CRM",
        "numero": "123456",
        "uf": "SP",
        "nome_profissional": "Dr. João da Silva",  // Se API disponível
        "especialidades": ["Cardiologia"],          // Se API disponível
        "situacao_registro": "Regular",             // Se API disponível
        "validation_id": "uuid",
        "validated_at": "2024-01-01T12:00:00",
        "validation_source": "api",
        "message": "Registro válido e ativo",
        "fhir_identifier": { ... }  // Identifier FHIR pronto para uso
    }
    """
    # Validar campos obrigatórios
    conselho = request.data.get('conselho')
    numero = request.data.get('numero')
    uf = request.data.get('uf')
    use_api = request.data.get('use_api', True)

    if not conselho:
        return Response(
            {"error": "Campo 'conselho' é obrigatório (ex: CRM, COREN, CRO)"},
            status=status.HTTP_400_BAD_REQUEST
        )
    if not numero:
        return Response(
            {"error": "Campo 'numero' é obrigatório"},
            status=status.HTTP_400_BAD_REQUEST
        )
    if not uf:
        return Response(
            {"error": "Campo 'uf' é obrigatório"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Obter dados do usuário para auditoria
    user_id = str(request.user.id) if request.user.is_authenticated else None
    ip_address = get_client_ip(request)

    # Executar validação
    result = CRMValidationService.validate(
        conselho=conselho,
        numero=numero,
        uf=uf,
        use_api=use_api,
        user_id=user_id,
        ip_address=ip_address
    )

    # Preparar resposta
    response_data = result.to_dict()
    response_data["fhir_identifier"] = result.to_fhir_identifier()

    # HTTP status baseado no resultado
    if result.status == ValidationStatus.VALID:
        return Response(response_data, status=status.HTTP_200_OK)
    elif result.status == ValidationStatus.INVALID_FORMAT:
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
    elif result.status in [ValidationStatus.SUSPENDED, ValidationStatus.CANCELLED, ValidationStatus.EXPIRED]:
        return Response(response_data, status=status.HTTP_200_OK)  # Válido mas com status especial
    elif result.status == ValidationStatus.NOT_FOUND:
        return Response(response_data, status=status.HTTP_404_NOT_FOUND)
    else:
        return Response(response_data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def validate_crm_batch(request):
    """
    POST /api/v1/crm/validate-batch/

    Valida múltiplos registros em lote.

    Request body:
    {
        "registros": [
            {"conselho": "CRM", "numero": "123456", "uf": "SP"},
            {"conselho": "COREN", "numero": "654321", "uf": "RJ"}
        ],
        "use_api": true
    }

    Response (200):
    {
        "total": 2,
        "valid_count": 2,
        "invalid_count": 0,
        "results": [ ... ]
    }
    """
    registros = request.data.get('registros', [])
    use_api = request.data.get('use_api', True)

    if not registros:
        return Response(
            {"error": "Lista de 'registros' é obrigatória"},
            status=status.HTTP_400_BAD_REQUEST
        )

    if len(registros) > 100:
        return Response(
            {"error": "Máximo de 100 registros por requisição"},
            status=status.HTTP_400_BAD_REQUEST
        )

    user_id = str(request.user.id) if request.user.is_authenticated else None

    results = CRMValidationService.batch_validate(
        registros=registros,
        use_api=use_api,
        user_id=user_id
    )

    response_results = []
    valid_count = 0
    for result in results:
        result_dict = result.to_dict()
        result_dict["fhir_identifier"] = result.to_fhir_identifier()
        response_results.append(result_dict)
        if result.status == ValidationStatus.VALID:
            valid_count += 1

    return Response({
        "total": len(results),
        "valid_count": valid_count,
        "invalid_count": len(results) - valid_count,
        "results": response_results
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def crm_validation_stats(request):
    """
    GET /api/v1/crm/stats/

    Estatísticas de validação (apenas admin).
    """
    # Verificar permissão de admin
    if not request.user.is_staff:
        return Response(
            {"error": "Apenas administradores podem acessar estatísticas"},
            status=status.HTTP_403_FORBIDDEN
        )

    stats = CRMValidationService.get_validation_stats()
    return Response(stats)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def invalidate_crm_cache(request):
    """
    POST /api/v1/crm/invalidate-cache/

    Invalida cache de uma validação específica (apenas admin).

    Request body:
    {
        "conselho": "CRM",
        "numero": "123456",
        "uf": "SP"
    }
    """
    if not request.user.is_staff:
        return Response(
            {"error": "Apenas administradores podem invalidar cache"},
            status=status.HTTP_403_FORBIDDEN
        )

    conselho = request.data.get('conselho')
    numero = request.data.get('numero')
    uf = request.data.get('uf')

    if not all([conselho, numero, uf]):
        return Response(
            {"error": "Campos 'conselho', 'numero' e 'uf' são obrigatórios"},
            status=status.HTTP_400_BAD_REQUEST
        )

    CRMValidationService.invalidate_cache(conselho, numero, uf)

    return Response({
        "message": "Cache invalidado com sucesso",
        "conselho": conselho,
        "numero": numero,
        "uf": uf
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def list_conselhos(request):
    """
    GET /api/v1/crm/conselhos/

    Lista todos os conselhos profissionais suportados.
    """
    conselhos = []
    descricoes = {
        "CRM": "Conselho Regional de Medicina",
        "COREN": "Conselho Regional de Enfermagem",
        "CRO": "Conselho Regional de Odontologia",
        "CRF": "Conselho Regional de Farmácia",
        "CREFITO": "Conselho Regional de Fisioterapia e Terapia Ocupacional",
        "CRN": "Conselho Regional de Nutrição",
        "CRFa": "Conselho Regional de Fonoaudiologia",
        "CRP": "Conselho Regional de Psicologia",
        "CRBM": "Conselho Regional de Biomedicina",
        "CRESS": "Conselho Regional de Serviço Social"
    }

    for conselho in ConselhoTipo:
        conselhos.append({
            "codigo": conselho.value,
            "descricao": descricoes.get(conselho.value, conselho.value),
            "formato_numero": CRMValidationService.FORMATO_PATTERNS.get(conselho, ""),
            "api_disponivel": conselho == ConselhoTipo.CRM and bool(CRMValidationService.CFM_API_URL)
        })

    return Response({
        "conselhos": conselhos,
        "ufs_validas": CRMValidationService.UF_VALIDAS
    })
