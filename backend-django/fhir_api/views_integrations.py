"""
Views de Integrações - Laboratório, PACS, Farmácia
"""

import logging
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework import status
from .auth import KeycloakAuthentication
from rest_framework.permissions import IsAuthenticated
from .services.lab_integration import LaboratoryIntegrationService, CategoriaExame, ResultadoExame
from .services.pacs_integration import PACSIntegrationService
from .services.pharmacy_integration import PharmacyIntegrationService, ItemDispensacao
from .services.fhir_core import FHIRService

logger = logging.getLogger(__name__)


# =============================================================================
# LABORATÓRIO
# =============================================================================

@api_view(['POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def receber_resultados_lab(request):
    """
    Recebe resultados de laboratório via Bundle FHIR.
    POST /api/v1/lab/results/
    
    Body: Bundle FHIR com DiagnosticReport e Observations
    """
    try:
        bundle = request.data
        
        if bundle.get('resourceType') != 'Bundle':
            return Response({
                'error': 'Esperado Bundle FHIR'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        lab_service = LaboratoryIntegrationService()
        resultado = lab_service.processar_bundle_resultados(bundle)
        
        return Response(resultado, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Erro ao processar resultados lab: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def converter_hl7_para_fhir(request):
    """
    Converte mensagem HL7 v2.x para Bundle FHIR.
    POST /api/v1/lab/convert-hl7/
    
    Body: {"message": "MSH|^~\\&|..."}
    """
    try:
        mensagem_hl7 = request.data.get('message', '')
        
        if not mensagem_hl7:
            return Response({
                'error': 'Mensagem HL7 não fornecida'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        lab_service = LaboratoryIntegrationService()
        bundle = lab_service.converter_hl7v2_para_fhir(mensagem_hl7)
        
        return Response(bundle)
        
    except Exception as e:
        logger.error(f"Erro ao converter HL7: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def criar_diagnostic_report(request):
    """
    Cria DiagnosticReport a partir de resultados estruturados.
    POST /api/v1/lab/diagnostic-report/
    """
    try:
        data = request.data
        
        # Construir lista de resultados
        resultados = []
        for r in data.get('resultados', []):
            resultados.append(ResultadoExame(
                codigo_loinc=r['codigo_loinc'],
                nome_exame=r['nome'],
                valor=str(r['valor']),
                unidade=r.get('unidade', ''),
                valor_referencia_min=r.get('referencia_min'),
                valor_referencia_max=r.get('referencia_max'),
                interpretacao=r.get('interpretacao')
            ))
        
        lab_service = LaboratoryIntegrationService()
        report = lab_service.criar_diagnostic_report(
            paciente_id=data['patient_id'],
            categoria=CategoriaExame[data.get('categoria', 'BIOQUIMICA').upper()],
            resultados=resultados,
            data_coleta=data['data_coleta'],
            laboratorio=data.get('laboratorio', 'Laboratório'),
            responsavel=data.get('responsavel', '')
        )
        
        # Salvar no FHIR Server
        fhir_service = FHIRService(request.user)
        result = fhir_service.create_resource('DiagnosticReport', report)
        
        return Response({
            'id': result.get('id'),
            'message': 'DiagnosticReport criado com sucesso'
        }, status=status.HTTP_201_CREATED)
        
    except KeyError as e:
        return Response({'error': f'Campo obrigatório: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Erro ao criar DiagnosticReport: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# =============================================================================
# PACS / IMAGENS
# =============================================================================

@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def pacs_status(request):
    """
    Verifica status da conexão com PACS.
    GET /api/v1/pacs/status/
    """
    try:
        pacs_url = request.query_params.get('pacs_url', 'http://localhost:8042')
        pacs_service = PACSIntegrationService(pacs_url=pacs_url)
        status_info = pacs_service.verificar_conexao()
        
        return Response(status_info)
        
    except Exception as e:
        return Response({
            'status': 'error',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def buscar_estudos_pacs(request):
    """
    Busca estudos no PACS.
    GET /api/v1/pacs/studies/?patient_id=123&modality=CT
    """
    try:
        pacs_service = PACSIntegrationService()
        
        estudos = pacs_service.buscar_estudos(
            patient_id=request.query_params.get('patient_id'),
            patient_name=request.query_params.get('patient_name'),
            study_date=request.query_params.get('study_date'),
            modality=request.query_params.get('modality'),
            accession_number=request.query_params.get('accession_number'),
            limit=int(request.query_params.get('limit', 50))
        )
        
        return Response({
            'count': len(estudos),
            'results': estudos
        })
        
    except Exception as e:
        logger.error(f"Erro ao buscar estudos PACS: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def estudos_paciente_pacs(request, patient_id):
    """
    Lista estudos de imagem de um paciente.
    GET /api/v1/patients/{patient_id}/imaging/
    """
    try:
        pacs_service = PACSIntegrationService()
        estudos = pacs_service.buscar_estudos_paciente(patient_id)
        
        return Response({
            'patient_id': patient_id,
            'count': len(estudos),
            'studies': estudos
        })
        
    except Exception as e:
        logger.error(f"Erro ao buscar imagens do paciente: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def obter_series_estudo(request, study_uid):
    """
    Lista séries de um estudo.
    GET /api/v1/pacs/studies/{study_uid}/series/
    """
    try:
        pacs_service = PACSIntegrationService()
        series = pacs_service.obter_series(study_uid)
        
        return Response({
            'study_instance_uid': study_uid,
            'count': len(series),
            'series': series
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def obter_viewer_url(request, study_uid):
    """
    Obtém URL para abrir estudo no viewer DICOM.
    GET /api/v1/pacs/studies/{study_uid}/viewer/
    """
    try:
        pacs_service = PACSIntegrationService()
        viewer_url = pacs_service.obter_url_viewer(study_uid)
        
        return Response({
            'study_instance_uid': study_uid,
            'viewer_url': viewer_url
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# =============================================================================
# FARMÁCIA
# =============================================================================

@api_view(['POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def processar_prescricao_farmacia(request):
    """
    Processa prescrição para dispensação.
    POST /api/v1/pharmacy/process/
    
    Body: MedicationRequest FHIR
    """
    try:
        medication_request = request.data
        
        if medication_request.get('resourceType') != 'MedicationRequest':
            return Response({
                'error': 'Esperado MedicationRequest FHIR'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        pharmacy_service = PharmacyIntegrationService()
        resultado = pharmacy_service.processar_prescricao(medication_request)
        
        return Response(resultado)
        
    except Exception as e:
        logger.error(f"Erro ao processar prescrição: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def criar_dispensacao(request):
    """
    Registra dispensação de medicamento.
    POST /api/v1/pharmacy/dispense/
    """
    try:
        data = request.data
        
        item = ItemDispensacao(
            medicamento_codigo=data['medicamento_codigo'],
            medicamento_nome=data['medicamento_nome'],
            lote=data['lote'],
            validade=data['validade'],
            quantidade_dispensada=float(data['quantidade']),
            unidade=data.get('unidade', 'UN'),
            fabricante=data.get('fabricante'),
            registro_anvisa=data.get('registro_anvisa')
        )
        
        pharmacy_service = PharmacyIntegrationService()
        dispense = pharmacy_service.criar_medication_dispense(
            medication_request_id=data['medication_request_id'],
            patient_id=data['patient_id'],
            item=item,
            performer_id=data['farmaceutico_id'],
            quando_preparado=data.get('quando_preparado'),
            quando_entregue=data.get('quando_entregue'),
            notas=data.get('notas')
        )
        
        # Salvar no FHIR Server
        fhir_service = FHIRService(request.user)
        result = fhir_service.create_resource('MedicationDispense', dispense)
        
        return Response({
            'id': result.get('id'),
            'message': 'Dispensação registrada com sucesso'
        }, status=status.HTTP_201_CREATED)
        
    except KeyError as e:
        return Response({'error': f'Campo obrigatório: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Erro ao criar dispensação: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def confirmar_entrega_medicamento(request, dispense_id):
    """
    Confirma entrega do medicamento.
    POST /api/v1/pharmacy/dispense/{dispense_id}/deliver/
    """
    try:
        data = request.data
        
        pharmacy_service = PharmacyIntegrationService()
        resultado = pharmacy_service.confirmar_entrega(
            dispense_id=dispense_id,
            recebido_por=data.get('recebido_por', ''),
            data_entrega=data.get('data_entrega')
        )
        
        return Response(resultado)
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def registrar_devolucao(request, dispense_id):
    """
    Registra devolução de medicamento.
    POST /api/v1/pharmacy/dispense/{dispense_id}/return/
    """
    try:
        data = request.data
        
        pharmacy_service = PharmacyIntegrationService()
        resultado = pharmacy_service.registrar_devolucao(
            dispense_id=dispense_id,
            quantidade_devolvida=float(data['quantidade']),
            motivo=data['motivo'],
            condicao_medicamento=data.get('condicao', 'bom_estado')
        )
        
        return Response(resultado)
        
    except KeyError as e:
        return Response({'error': f'Campo obrigatório: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def verificar_interacoes(request):
    """
    Verifica interações medicamentosas.
    POST /api/v1/pharmacy/interactions/
    
    Body: {"medication_requests": [<lista de MedicationRequest>]}
    """
    try:
        medication_requests = request.data.get('medication_requests', [])
        
        if not medication_requests:
            return Response({
                'error': 'Lista de prescrições vazia'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        pharmacy_service = PharmacyIntegrationService()
        interacoes = pharmacy_service.verificar_interacoes_prescricao(medication_requests)
        
        return Response({
            'count': len(interacoes),
            'interactions': interacoes,
            'has_severe': any(i['tipo'] == 'grave' for i in interacoes)
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def relatorio_consumo_farmacia(request):
    """
    Gera relatório de consumo de medicamentos.
    GET /api/v1/pharmacy/report/?start_date=2024-01-01&end_date=2024-01-31
    """
    try:
        data_inicio = request.query_params.get('start_date')
        data_fim = request.query_params.get('end_date')
        
        if not data_inicio or not data_fim:
            return Response({
                'error': 'start_date e end_date são obrigatórios'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        pharmacy_service = PharmacyIntegrationService()
        relatorio = pharmacy_service.gerar_relatorio_consumo(
            data_inicio=data_inicio,
            data_fim=data_fim,
            unidade_id=request.query_params.get('unit_id')
        )
        
        return Response(relatorio)
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
