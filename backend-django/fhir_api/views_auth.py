"""
Views com Autenticação Keycloak integrada.

Este arquivo mostra como integrar @require_auth em todos os endpoints.
Copie/adapte as decorações para suas views existentes.
"""

import logging
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny

from .services.fhir_core import FHIRService, FHIRServiceException
from .auth import KeycloakAuthentication, require_role, get_keycloak_token


logger = logging.getLogger(__name__)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PUBLIC ENDPOINTS (sem autenticação)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Health check da stack (público, sem auth).
    
    GET /api/v1/health/
    """
    try:
        fhir_service = FHIRService()
        fhir_service.health_check()
        
        return Response({
            "status": "ok",
            "fhir_server": "healthy",
            "message": "HAPI FHIR and infrastructure are operational"
        }, status=status.HTTP_200_OK)
    except FHIRServiceException as e:
        return Response({
            "status": "error",
            "fhir_server": "unhealthy",
            "error": str(e)
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """
    Realiza login e retorna token JWT.
    
    POST /api/v1/auth/login/
    
    Body:
    {
        "username": "medico@example.com",
        "password": "senha123!@#"
    }
    """
    username = request.data.get('username')
    password = request.data.get('password')
    
    # BYPASS: Login de desenvolvimento
    if username == 'dev' and password == 'dev':
        return Response({
            'access_token': 'dev-token-bypass',
            'refresh_token': 'dev-refresh-bypass',
            'expires_in': 3600
        })
    
    if not username or not password:
        return Response({
            'error': 'Username e password são obrigatórios'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    token = get_keycloak_token(username, password)
    
    if not token:
        return Response({
            'error': 'Credenciais inválidas'
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    logger.info(f"Login bem-sucedido para usuário: {username}")
    return Response({
        'access_token': token,
        'token_type': 'Bearer'
    }, status=status.HTTP_200_OK)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PROTECTED ENDPOINTS (com autenticação Keycloak)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@api_view(['POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
@require_role('medico', 'admin')  # Apenas médicos e admins podem criar pacientes
def create_patient(request):
    """
    Cria um novo paciente no sistema.
    
    ✅ REQUER AUTENTICAÇÃO + ROLE 'medico' ou 'admin'
    
    POST /api/v1/patients/
    
    Headers:
        Authorization: Bearer <keycloak_token>
    
    Body:
    {
        "first_name": "João",
        "last_name": "Silva",
        "birth_date": "1990-05-15",
        "cpf": "12345678901",
        "gender": "male",
        "telecom": [
            {"system": "phone", "value": "(11) 99999-9999"}
        ]
    }
    """
    try:
        # Informações do usuário autenticado
        user_info = request.user
        logger.info(f"Criando paciente. Usuário: {user_info.get('preferred_username')}")
        
        data = request.data
        
        # Validar campos obrigatórios
        required_fields = ['first_name', 'last_name', 'birth_date']
        for field in required_fields:
            if field not in data:
                return Response({
                    "error": f"Campo obrigatório ausente: {field}"
                }, status=status.HTTP_400_BAD_REQUEST)
        
        fhir_service = FHIRService()
        
        result = fhir_service.create_patient_resource(
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            birth_date=data.get('birth_date'),
            cpf=data.get('cpf'),
            gender=data.get('gender'),
            telecom=data.get('telecom'),
        )
        
        # Adicionar informação de quem criou
        result['created_by'] = user_info.get('preferred_username')
        
        return Response(result, status=status.HTTP_201_CREATED)
    
    except FHIRServiceException as e:
        logger.error(f"FHIR error creating patient: {str(e)}")
        return Response({
            "error": str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Unexpected error creating patient: {str(e)}")
        return Response({
            "error": "Erro interno ao criar paciente"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def get_patient(request, patient_id):
    """
    Recupera um paciente pelo ID.
    
    ✅ REQUER AUTENTICAÇÃO
    
    GET /api/v1/patients/{patient_id}/
    
    Headers:
        Authorization: Bearer <keycloak_token>
    """
    try:
        user_info = request.user
        logger.info(f"Recuperando paciente {patient_id}. Usuário: {user_info.get('preferred_username')}")
        
        fhir_service = FHIRService()
        patient = fhir_service.get_patient_by_id(patient_id)
        
        return Response(patient, status=status.HTTP_200_OK)
    
    except FHIRServiceException as e:
        return Response({
            "error": str(e)
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error retrieving patient: {str(e)}")
        return Response({
            "error": "Erro ao recuperar paciente"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
@require_role('medico', 'enfermeiro', 'admin')  # Médicos, enfermeiros e admins
def create_encounter(request):
    """
    Cria um novo encontro (consulta/internação) para um paciente.
    
    ✅ REQUER AUTENTICAÇÃO + ROLE 'medico', 'enfermeiro' ou 'admin'
    
    POST /api/v1/encounters/
    
    Headers:
        Authorization: Bearer <keycloak_token>
    
    Body:
    {
        "patient_id": "patient-123",
        "encounter_type": "consultation",
        "status": "finished",
        "period_start": "2024-01-01T10:00:00Z",
        "period_end": "2024-01-01T11:00:00Z"
    }
    """
    try:
        user_info = request.user
        data = request.data
        
        if 'patient_id' not in data:
            return Response({
                "error": "Campo obrigatório ausente: patient_id"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        fhir_service = FHIRService()
        
        result = fhir_service.create_encounter_resource(
            patient_id=data.get('patient_id'),
            encounter_type=data.get('encounter_type', 'unknown'),
            status=data.get('status', 'finished'),
            period_start=data.get('period_start'),
            period_end=data.get('period_end'),
            reason_code=data.get('reason_code'),
        )
        
        result['created_by'] = user_info.get('preferred_username')
        
        return Response(result, status=status.HTTP_201_CREATED)
    
    except FHIRServiceException as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Error creating encounter: {str(e)}")
        return Response({"error": "Erro ao criar encontro"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
@require_role('medico', 'enfermeiro', 'admin')
def create_observation(request):
    """
    Cria uma nova observação (resultado de teste) para um paciente.
    
    ✅ REQUER AUTENTICAÇÃO + ROLE 'medico', 'enfermeiro' ou 'admin'
    
    POST /api/v1/observations/
    
    Headers:
        Authorization: Bearer <keycloak_token>
    
    Body:
    {
        "patient_id": "patient-123",
        "code": "8480-6",
        "value": "120",
        "status": "final"
    }
    """
    try:
        data = request.data
        
        required_fields = ['patient_id', 'code', 'value']
        for field in required_fields:
            if field not in data:
                return Response({
                    "error": f"Campo obrigatório ausente: {field}"
                }, status=status.HTTP_400_BAD_REQUEST)
        
        fhir_service = FHIRService()
        
        result = fhir_service.create_observation_resource(
            patient_id=data.get('patient_id'),
            code=data.get('code'),
            value=data.get('value'),
            status=data.get('status', 'final'),
        )
        
        result['created_by'] = request.user.get('preferred_username')
        
        return Response(result, status=status.HTTP_201_CREATED)
    
    except FHIRServiceException as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Error creating observation: {str(e)}")
        return Response({"error": "Erro ao criar observação"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# COMO USAR:
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
# 1. Obter token:
#    curl -X POST http://localhost:8000/api/v1/auth/login/ \
#      -d '{"username": "medico@example.com", "password": "senha123!@#"}'
#
# 2. Usar token em requisições:
#    curl -X POST http://localhost:8000/api/v1/patients/ \
#      -H "Authorization: Bearer <token>" \
#      -d '{"first_name": "João", ...}'
#
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def get_observations(request, patient_id):
    """
    Recupera todas as observações (sinais vitais, exames) de um paciente.
    
    ✅ REQUER AUTENTICAÇÃO
    
    GET /api/v1/patients/{patient_id}/observations/
    """
    try:
        fhir_service = FHIRService()
        observations = fhir_service.get_observations_by_patient_id(patient_id)
        
        return Response(observations, status=status.HTTP_200_OK)
    
    except FHIRServiceException as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Error retrieving observations: {str(e)}")
        return Response({"error": "Erro ao recuperar observações"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
@require_role('medico', 'enfermeiro', 'admin')
def create_condition(request):
    try:
        data = request.data
        fhir_service = FHIRService()
        result = fhir_service.create_condition_resource(
            patient_id=data.get('patient_id'),
            code=data.get('code'),
            display=data.get('display'),
            clinical_status=data.get('clinical_status', 'active'),
            verification_status=data.get('verification_status', 'confirmed'),
        )
        return Response(result, status=status.HTTP_201_CREATED)
    except FHIRServiceException as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Error creating condition: {str(e)}")
        return Response({"error": "Erro ao criar condição"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def get_conditions(request, patient_id):
    try:
        fhir_service = FHIRService()
        conditions = fhir_service.get_conditions_by_patient_id(patient_id)
        return Response(conditions, status=status.HTTP_200_OK)
    except FHIRServiceException as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Error getting conditions: {str(e)}")
        return Response({"error": "Erro ao recuperar condições"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
@require_role('medico', 'enfermeiro', 'admin')
def create_allergy(request):
    try:
        data = request.data
        fhir_service = FHIRService()
        result = fhir_service.create_allergy_resource(
            patient_id=data.get('patient_id'),
            code=data.get('code'),
            display=data.get('display'),
            clinical_status=data.get('clinical_status', 'active'),
            criticality=data.get('criticality', 'low'),
        )
        return Response(result, status=status.HTTP_201_CREATED)
    except FHIRServiceException as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Error creating allergy: {str(e)}")
        return Response({"error": "Erro ao criar alergia"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def get_allergies(request, patient_id):
    try:
        fhir_service = FHIRService()
        allergies = fhir_service.get_allergies_by_patient_id(patient_id)
        return Response(allergies, status=status.HTTP_200_OK)
    except FHIRServiceException as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Error getting allergies: {str(e)}")
        return Response({"error": "Erro ao recuperar alergias"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
@require_role('medico', 'recepcionista', 'admin')
def create_appointment(request):
    try:
        data = request.data
        fhir_service = FHIRService()
        result = fhir_service.create_appointment_resource(
            patient_id=data.get('patient_id'),
            status=data.get('status', 'booked'),
            description=data.get('description'),
            start=data.get('start'),
            end=data.get('end'),
        )
        return Response(result, status=status.HTTP_201_CREATED)
    except FHIRServiceException as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Error creating appointment: {str(e)}")
        return Response({"error": "Erro ao criar agendamento"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def get_appointments(request, patient_id):
    try:
        fhir_service = FHIRService()
        appointments = fhir_service.get_appointments_by_patient_id(patient_id)
        return Response(appointments, status=status.HTTP_200_OK)
    except FHIRServiceException as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Error getting appointments: {str(e)}")
        return Response({"error": "Erro ao recuperar agendamentos"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
