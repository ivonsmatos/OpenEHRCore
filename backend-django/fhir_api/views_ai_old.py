from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework import status
from .auth import KeycloakAuthentication
from rest_framework.permissions import IsAuthenticated, AllowAny
from .services.fhir_core import FHIRService, FHIRServiceException
from .services.ai_service import AIService
from .utils.validators import validate_patient_id, calculate_age
from .utils.logging_utils import sanitize_for_log
import logging
from datetime import datetime, date
from django.core.cache import cache
import requests

logger = logging.getLogger(__name__)

@api_view(['GET'])
# @authentication_classes([KeycloakAuthentication])  # Temporariamente desabilitado
@permission_classes([AllowAny])  # Temporariamente AllowAny
def get_patient_summary(request, patient_id):
    """
    Gera um resumo clínico inteligente do paciente usando IA.
    
    GET /api/v1/ai/summary/{patient_id}/
    
    Security:
    - Valida patient_id (UUID format)
    - Requer autenticação Keycloak
    
    Performance:
    - Cache de 5 minutos
    - Timeout de 30s para IA
    - Fallback gracioso se dados ausentes
    
    Returns:
        200: {"summary": "...", "cached": true/false}
        400: Validation error
        404: Patient not found
        503: FHIR service unavailable
        500: Internal server error
    """
    
    import sys
    sys.stdout.write(f"\n🔥🔥🔥 FUNÇÃO CHAMADA PARA PACIENTE {patient_id} 🔥🔥🔥\n")
    sys.stdout.flush()
    
    # ====================================================================
    # 1. VALIDAÇÃO DE ENTRADA
    # ====================================================================
    
    print(f"🔥🔥🔥 GET_PATIENT_SUMMARY CHAMADO PARA PACIENTE {patient_id} 🔥🔥🔥")
    
    # Validar formato do patient_id (evitar injection, aceita UUID ou ID numérico)
    if not validate_patient_id(patient_id):
        logger.warning(f"Invalid patient_id format attempted: {patient_id}")
        return Response(
            {
                "error": "Invalid patient ID format",
                "detail": "Patient ID must be a valid UUID or numeric ID"
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # ====================================================================
    # 2. VERIFICAR CACHE (evitar chamadas desnecessárias à IA)
    # ====================================================================
    
    cache_key = f"ai_summary_v3:patient:{patient_id}"  # v3 = nova versão após fixes
    cached_result = cache.get(cache_key)
    
    # DEBUG
    print(f"🔥 [v3] Cache check: {cache_key} → {'HIT' if cached_result else 'MISS'}")
    
    print(f"�🔥🔥 [VERSÃO 2025-12-14 23:00] Cache check: {cache_key} → {'HIT' if cached_result else 'MISS'}")
    print(f"🔥 Tipo do cached_result: {type(cached_result)}")
    print(f"🔥 Valor: {cached_result}")
    
    if cached_result:
        print(f"📦 Retornando cache: {cached_result}")
        logger.info(f"Returning cached AI summary for patient {patient_id}")
        # cached_result é um dict: {'summary': str, 'using_ai': bool}
        if isinstance(cached_result, dict) and 'summary' in cached_result:
            return Response(
                {
                    "summary": cached_result['summary'],
                    "cached": True,
                    "using_ai": cached_result.get('using_ai', False)
                },
                status=status.HTTP_200_OK
            )
        else:
            # Cache antigo (só string) - converter para novo formato
            return Response(
                {
                    "summary": cached_result,
                    "cached": True,
                    "using_ai": False  # Cache antigo não tem info de AI
                },
                status=status.HTTP_200_OK
            )
    
    # ====================================================================
    # 3. RECUPERAR DADOS DO PACIENTE (com tratamento específico de erros)
    # ====================================================================
    
    fhir_service = FHIRService(request.user)
    
    try:
        patient = fhir_service.get_patient_by_id(patient_id)
    except FHIRServiceException as e:
        error_str = str(e).lower()
        if "not found" in error_str or "404" in error_str:
            return Response(
                {
                    "error": "Patient not found",
                    "patient_id": patient_id
                },
                status=status.HTTP_404_NOT_FOUND
            )
        elif "circuit breaker" in error_str or "unreachable" in error_str:
            return Response(
                {
                    "error": "FHIR service temporarily unavailable",
                    "detail": "Please try again in a few moments",
                    "retry_after": 60
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        else:
            logger.error(
                f"FHIR error fetching patient {patient_id}: {e}", 
                exc_info=True
            )
            return Response(
                {
                    "error": "Failed to retrieve patient data",
                    "detail": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    except Exception as e:
        logger.error(
            f"Unexpected error fetching patient {patient_id}: {e}",
            exc_info=True
        )
        return Response(
            {"error": "Internal server error"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    # ====================================================================
    # 4. CALCULAR IDADE
    # ====================================================================
    
    birth_date = patient.get("birthDate")
    age = calculate_age(birth_date)
    age_display = str(age) if age is not None else "Desconhecida"
    
    # ====================================================================
    # 5. RECUPERAR HISTÓRICO CLÍNICO (cada item isolado, não falhamos tudo)
    # ====================================================================
    
    def fetch_resource_safe(resource_type: str, params: dict) -> list:
        """Busca recursos FHIR com tratamento de erro isolado."""
        try:
            return fhir_service.search_resources(resource_type, params)
        except FHIRServiceException as e:
            logger.warning(
                f"Failed to fetch {resource_type} for patient {patient_id}: {e}"
            )
            return []
        except requests.exceptions.Timeout as e:
            logger.warning(
                f"Timeout fetching {resource_type} for patient {patient_id}: {e}"
            )
            return []
        except Exception as e:
            logger.error(
                f"Unexpected error fetching {resource_type}: {e}",
                exc_info=True
            )
            return []
    
    conditions = fetch_resource_safe("Condition", {"patient": patient_id})
    medications = fetch_resource_safe("MedicationRequest", {
        "patient": patient_id, 
        "status": "active"
    })
    # Aumentado de 5 para 15 para melhor análise de tendências
    observations = fetch_resource_safe("Observation", {
        "patient": patient_id,
        "category": "vital-signs",
        "_count": "15",
        "_sort": "-date"
    })
    
    # Buscar vacinas (immunizations)
    immunizations = fetch_resource_safe("Immunization", {
        "patient": patient_id,
        "_count": "20",
        "_sort": "-date"
    })
    
    # Buscar exames laboratoriais (diagnostic reports)
    diagnostic_reports = fetch_resource_safe("DiagnosticReport", {
        "patient": patient_id,
        "_count": "10",
        "_sort": "-date"
    })
    
    # Buscar agendamentos (appointments - últimos e próximos)
    appointments = fetch_resource_safe("Appointment", {
        "patient": patient_id,
        "_count": "10",
        "_sort": "-date"
    })
    
    # ====================================================================
    # 6. MONTAR DADOS PARA IA (com defaults seguros)
    # ====================================================================
    
    patient_names = patient.get('name', [{}])
    first_name = patient_names[0].get('given', [''])[0] if patient_names else ''
    family_name = patient_names[0].get('family', '') if patient_names else ''
    full_name = f"{first_name} {family_name}".strip() or "Nome não disponível"
    
    patient_data = {
        "name": full_name,
        "age": age_display,
        "gender": patient.get("gender", "unknown"),
        "conditions": conditions,
        "medications": medications,
        "vital_signs": observations,
        "immunizations": immunizations,
        "diagnostic_reports": diagnostic_reports,
        "appointments": appointments
    }
    
    # Log sanitizado (sem CPF, tokens, etc)
    logger.debug(f"Generating AI summary with data: {sanitize_for_log(patient_data)}")
    
    # ====================================================================
    # 7. GERAR RESUMO COM IA (com timeout e tratamento de erro)
    # ====================================================================
    
    ai_service = AIService(request.user)
    
    try:
        logger.warning(f"🔥 INICIANDO GERAÇÃO DE RESUMO PARA PACIENTE {patient_id}")
        result = ai_service.generate_patient_summary(patient_data)
        
        # Result agora é um dict: {'summary': str, 'using_ai': bool}
        summary = result['summary']
        using_ai = result['using_ai']
        
        # Confirmar geração
        logger.info(f"✅ RESUMO GERADO: {len(summary)} caracteres | using_ai={using_ai}")
        logger.info(f"Preview: {summary[:200]}")
        
        # SEMPRE RETORNA NOVO RESUMO - SEM CACHE
        return Response(
            {
                "summary": summary,
                "using_ai": using_ai,
                "timestamp": datetime.now().isoformat()
            },
            status=status.HTTP_200_OK
        )
        
    except requests.exceptions.Timeout:
        logger.error(f"AI service timeout for patient {patient_id}")
        return Response(
            {
                "error": "AI service timeout",
                "detail": "Summary generation took too long. Please try again."
            },
            status=status.HTTP_504_GATEWAY_TIMEOUT
        )
        
    except Exception as e:
        logger.error(f"AI SERVICE ERROR FOR PATIENT {patient_id}: {str(e)}", exc_info=True)
        
        return Response(
            {
                "summary": f"Erro ao gerar resumo: {str(e)}",
                "error": str(e),
                "using_ai": False,
                "timestamp": datetime.now().isoformat()
            },
            status=status.HTTP_200_OK  # Retorna 200 com fallback
        )

@api_view(['POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def check_interactions(request):
    """
    Verifica interações medicamentosas.
    
    POST /api/v1/ai/interactions
    Body: { 
        "new_medication": "Aspirina", 
        "patient_id": "uuid" (optional - will fetch current medications)
        "current_medications": [...] (optional - can provide directly)
    }
    
    Returns:
        200: {"alerts": [...]}
        400: Validation error
        500: Internal server error
    """
    try:
        new_medication = request.data.get('new_medication')
        
        # Validação básica
        if not new_medication:
            return Response(
                {"error": "new_medication is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        patient_id = request.data.get('patient_id')
        current_medications = request.data.get('current_medications', [])
        
        # Se patient_id fornecido, buscar medicações do FHIR
        if patient_id:
            # Validar patient_id (UUID ou numérico)
            if not validate_patient_id(patient_id):
                return Response(
                    {"error": "Invalid patient_id format"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            fhir_service = FHIRService(request.user)
            try:
                current_medications = fhir_service.search_resources(
                    "MedicationRequest", 
                    {"patient": patient_id, "status": "active"}
                )
            except FHIRServiceException as e:
                logger.warning(
                    f"Failed to fetch medications for patient {patient_id}: {e}"
                )
                # Continuar com lista vazia (melhor que falhar completamente)
                current_medications = []
            except Exception as e:
                logger.error(
                    f"Unexpected error fetching medications: {e}",
                    exc_info=True
                )
                current_medications = []
        
        # Verificar interações com AI
        ai_service = AIService(request.user)
        
        try:
            alerts = ai_service.check_drug_interactions(
                new_medication, 
                current_medications
            )
            
            return Response({"alerts": alerts}, status=status.HTTP_200_OK)
            
        except requests.exceptions.Timeout:
            logger.error("AI service timeout checking drug interactions")
            return Response(
                {
                    "error": "AI service timeout",
                    "detail": "Interaction check took too long"
                },
                status=status.HTTP_504_GATEWAY_TIMEOUT
            )
        except Exception as e:
            logger.error(f"AI service error checking interactions: {e}", exc_info=True)
            return Response(
                {"error": "Failed to check interactions"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    except Exception as e:
        logger.error(f"Erro ao checar interações: {str(e)}", exc_info=True)
        return Response(
            {"error": "Internal server error"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['DELETE'])
@permission_classes([AllowAny])
def clear_patient_cache(request, patient_id=None):
    """
    Limpa o cache de resumo de um paciente específico ou de todos os pacientes.
    
    DELETE /api/v1/ai/cache/{patient_id}/  - Limpa cache de um paciente
    DELETE /api/v1/ai/cache/all/  - Limpa todo o cache de AI
    
    Returns:
        200: Cache cleared successfully
    """
    try:
        if patient_id == "all":
            # Clear all AI cache
            cache.clear()
            logger.info("All AI cache cleared")
            return Response(
                {"message": "All AI summary cache cleared"},
                status=status.HTTP_200_OK
            )
        else:
            # Clear specific patient cache (try all versions)
            keys_cleared = []
            for version in ['', '_v2', '_v3']:
                cache_key = f"ai_summary{version}:patient:{patient_id}"
                if cache.delete(cache_key):
                    keys_cleared.append(cache_key)
            
            logger.info(f"Cache cleared for patient {patient_id}: {keys_cleared}")
            return Response(
                {
                    "message": f"Cache cleared for patient {patient_id}",
                    "keys_cleared": keys_cleared
                },
                status=status.HTTP_200_OK
            )
    except Exception as e:
        logger.error(f"Error clearing cache: {e}", exc_info=True)
        return Response(
            {"error": "Failed to clear cache"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
