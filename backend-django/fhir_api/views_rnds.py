"""
Views RNDS - Endpoints para integração com Rede Nacional de Dados em Saúde
"""

import logging
from django.conf import settings
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework import status
from .auth import KeycloakAuthentication
from rest_framework.permissions import IsAuthenticated
from .services.rnds_service import RNDSService, ConfiguracaoRNDS, RNDSAmbiente
from .services.fhir_core import FHIRService

logger = logging.getLogger(__name__)


def _get_rnds_service() -> RNDSService:
    """Obtém instância configurada do RNDSService"""
    config = ConfiguracaoRNDS(
        ambiente=RNDSAmbiente.HOMOLOGACAO,  # Alterar para PRODUCAO em produção
        client_id=getattr(settings, 'RNDS_CLIENT_ID', ''),
        client_secret=getattr(settings, 'RNDS_CLIENT_SECRET', ''),
        cnes=getattr(settings, 'RNDS_CNES', ''),
        uf=getattr(settings, 'RNDS_UF', 'SP'),
        certificado_path=getattr(settings, 'RNDS_CERT_PATH', None),
        certificado_senha=getattr(settings, 'RNDS_CERT_PASSWORD', None)
    )
    return RNDSService(config)


@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def rnds_status(request):
    """
    Verifica status da conexão com RNDS
    GET /api/v1/rnds/status/
    """
    try:
        rnds = _get_rnds_service()
        status_info = rnds.verificar_status_conexao()
        return Response(status_info)
    except Exception as e:
        logger.error(f"Erro ao verificar status RNDS: {str(e)}")
        return Response({
            'status': 'erro',
            'erro': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def consultar_paciente_rnds(request):
    """
    Consulta paciente na RNDS por CPF ou CNS
    GET /api/v1/rnds/paciente/?cpf=12345678901
    GET /api/v1/rnds/paciente/?cns=123456789012345
    """
    try:
        cpf = request.query_params.get('cpf')
        cns = request.query_params.get('cns')
        
        if not cpf and not cns:
            return Response({
                'error': 'CPF ou CNS é obrigatório'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        rnds = _get_rnds_service()
        
        if cpf:
            result = rnds.consultar_paciente(cpf)
        else:
            result = rnds.consultar_cns(cns)
        
        return Response(result)
        
    except Exception as e:
        logger.error(f"Erro ao consultar paciente RNDS: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def enviar_sumario_rnds(request):
    """
    Envia Sumário de Paciente (IPS) para RNDS
    POST /api/v1/rnds/sumario/
    
    Body:
    {
        "patient_id": "123",
        "practitioner_cns": "123456789012345"
    }
    """
    try:
        data = request.data
        patient_id = data.get('patient_id')
        practitioner_cns = data.get('practitioner_cns')
        
        if not patient_id:
            return Response({'error': 'patient_id é obrigatório'}, status=status.HTTP_400_BAD_REQUEST)
        if not practitioner_cns:
            return Response({'error': 'practitioner_cns é obrigatório'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Buscar dados do paciente no FHIR local
        fhir_service = FHIRService(request.user)
        
        patient = fhir_service.get_resource('Patient', patient_id)
        if not patient:
            return Response({'error': 'Paciente não encontrado'}, status=status.HTTP_404_NOT_FOUND)
        
        # Extrair CPF do paciente
        identifiers = patient.get('identifier', [])
        cpf = None
        for ident in identifiers:
            if 'cpf' in ident.get('system', '').lower():
                cpf = ident.get('value')
                break
        
        if not cpf:
            return Response({'error': 'Paciente não possui CPF cadastrado'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Buscar dados clínicos
        conditions = fhir_service.search_resources('Condition', {'patient': patient_id, 'clinical-status': 'active'})
        allergies = fhir_service.search_resources('AllergyIntolerance', {'patient': patient_id})
        medications = fhir_service.search_resources('MedicationRequest', {'patient': patient_id, 'status': 'active'})
        immunizations = fhir_service.search_resources('Immunization', {'patient': patient_id})
        
        # Enviar para RNDS
        rnds = _get_rnds_service()
        result = rnds.enviar_sumario_paciente(
            patient_cpf=cpf,
            conditions=conditions,
            allergies=allergies,
            medications=medications,
            immunizations=immunizations,
            practitioner_cns=practitioner_cns
        )
        
        logger.info(f"Sumário enviado para RNDS - Paciente: {patient_id}")
        
        return Response({
            'message': 'Sumário enviado com sucesso para RNDS',
            'result': result
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Erro ao enviar sumário RNDS: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def enviar_resultado_exame_rnds(request):
    """
    Envia resultado de exame para RNDS
    POST /api/v1/rnds/exame/
    
    Body:
    {
        "patient_cpf": "12345678901",
        "exam_type": "Hemograma",
        "loinc_code": "26515-7",
        "result_value": "12.5",
        "result_unit": "g/dL",
        "exam_date": "2024-01-15",
        "practitioner_cns": "123456789012345",
        "interpretation": "N"
    }
    """
    try:
        data = request.data
        
        required_fields = ['patient_cpf', 'exam_type', 'loinc_code', 'result_value', 'result_unit', 'exam_date', 'practitioner_cns']
        for field in required_fields:
            if not data.get(field):
                return Response({'error': f'{field} é obrigatório'}, status=status.HTTP_400_BAD_REQUEST)
        
        rnds = _get_rnds_service()
        result = rnds.enviar_resultado_exame(
            patient_cpf=data['patient_cpf'],
            exam_type=data['exam_type'],
            result_value=data['result_value'],
            result_unit=data['result_unit'],
            exam_date=data['exam_date'],
            practitioner_cns=data['practitioner_cns'],
            loinc_code=data['loinc_code'],
            interpretation=data.get('interpretation')
        )
        
        return Response({
            'message': 'Resultado de exame enviado para RNDS',
            'result': result
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Erro ao enviar exame RNDS: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def enviar_imunizacao_rnds(request):
    """
    Registra imunização na RNDS
    POST /api/v1/rnds/imunizacao/
    
    Body:
    {
        "patient_cpf": "12345678901",
        "vaccine_code": "86",
        "vaccine_name": "COVID-19",
        "dose_number": 1,
        "vaccination_date": "2024-01-15",
        "lot_number": "ABC123",
        "practitioner_cns": "123456789012345",
        "manufacturer": "Pfizer"
    }
    """
    try:
        data = request.data
        
        required_fields = ['patient_cpf', 'vaccine_code', 'vaccine_name', 'dose_number', 'vaccination_date', 'lot_number', 'practitioner_cns']
        for field in required_fields:
            if not data.get(field):
                return Response({'error': f'{field} é obrigatório'}, status=status.HTTP_400_BAD_REQUEST)
        
        rnds = _get_rnds_service()
        result = rnds.enviar_imunizacao(
            patient_cpf=data['patient_cpf'],
            vaccine_code=data['vaccine_code'],
            vaccine_name=data['vaccine_name'],
            dose_number=int(data['dose_number']),
            vaccination_date=data['vaccination_date'],
            lot_number=data['lot_number'],
            practitioner_cns=data['practitioner_cns'],
            manufacturer=data.get('manufacturer')
        )
        
        return Response({
            'message': 'Imunização registrada na RNDS',
            'result': result
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Erro ao enviar imunização RNDS: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def consultar_vacinas_rnds(request):
    """
    Consulta histórico vacinal na RNDS
    GET /api/v1/rnds/vacinas/?cpf=12345678901
    """
    try:
        cpf = request.query_params.get('cpf')
        if not cpf:
            return Response({'error': 'CPF é obrigatório'}, status=status.HTTP_400_BAD_REQUEST)
        
        rnds = _get_rnds_service()
        result = rnds.consultar_historico_vacinal(cpf)
        
        return Response(result)
        
    except Exception as e:
        logger.error(f"Erro ao consultar vacinas RNDS: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
