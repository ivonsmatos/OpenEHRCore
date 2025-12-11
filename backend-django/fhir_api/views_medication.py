"""
Views for Medication and MedicationRequest management
FHIR R4 Compliant - Enhanced

Suporte aprimorado para prescrições médicas:
- Códigos ANVISA (RxNorm brasileiro)
- Dosagem estruturada (dose, frequência, via)
- Timing FHIR (período, frequência)
- Dispense request (quantidade, dias)
- Validade da prescrição
"""
import logging
import re
from datetime import datetime, timedelta
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response

from .services.fhir_core import FHIRService, FHIRServiceException
from .auth import KeycloakAuthentication, IsAuthenticated

logger = logging.getLogger(__name__)

# Status válidos para MedicationRequest FHIR R4
VALID_STATUSES = [
    'active',       # Ativa
    'on-hold',      # Em espera
    'cancelled',    # Cancelada
    'completed',    # Concluída
    'entered-in-error',  # Erro de entrada
    'stopped',      # Parada
    'draft',        # Rascunho
    'unknown'       # Desconhecido
]

# Intents válidos
VALID_INTENTS = [
    'proposal',     # Proposta
    'plan',         # Plano
    'order',        # Pedido
    'original-order',   # Pedido original
    'reflex-order', # Pedido reflexo
    'filler-order', # Pedido preenchedor
    'instance-order',   # Instância
    'option'        # Opção
]

# Vias de administração comuns
ROUTES = {
    'oral': ('26643006', 'Oral route'),
    'iv': ('47625008', 'Intravenous route'),
    'im': ('78421000', 'Intramuscular route'),
    'sc': ('34206005', 'Subcutaneous route'),
    'topical': ('6064005', 'Topical route'),
    'inhalation': ('18679011000001101', 'Inhalation route'),
    'rectal': ('37161004', 'Rectal route'),
    'sublingual': ('37839007', 'Sublingual route'),
}


def validate_anvisa_code(code: str) -> bool:
    """
    Valida código de registro ANVISA.
    Formato: 1.0000.0000.000-0 ou numérico de 13 dígitos
    """
    # Remove caracteres não numéricos
    clean = re.sub(r'[^0-9]', '', code)
    return len(clean) >= 9 and len(clean) <= 15


@api_view(['GET', 'POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def manage_medication_requests(request):
    """
    GET: Lista prescrições (com filtros)
    POST: Cria nova prescrição médica aprimorada
    
    FHIR R4 MedicationRequest Resource
    
    Parâmetros de busca (GET):
    - patient: ID do paciente
    - status: Status da prescrição (active, completed, etc.)
    - intent: Tipo de intent
    - medication: Código do medicamento
    - requester: ID do prescritor
    - authoredon: Data de criação (ge/le para range)
    
    Body (POST):
    {
        "patient_id": "patient-123",
        "encounter_id": "encounter-456",  # Opcional
        "medication": {
            "code": "12345678901",  # Código ANVISA ou RxNorm
            "code_system": "anvisa",  # "anvisa" ou "rxnorm"
            "display": "Dipirona 500mg comprimido",
            "form": "comprimido"  # Opcional: forma farmacêutica
        },
        "dosage": {
            "dose_value": 1,
            "dose_unit": "comprimido",
            "route": "oral",  # oral, iv, im, sc, topical, etc.
            "frequency": {
                "value": 8,  # A cada 8 horas
                "unit": "h",  # h (horas), d (dias), wk (semanas)
            },
            "duration": {
                "value": 7,  # Por 7 dias
                "unit": "d"
            },
            "instructions": "Tomar com água, após as refeições"
        },
        "dispense": {
            "quantity": 21,  # Quantidade total a dispensar
            "supply_duration": 7  # Dias de tratamento
        },
        "requester_id": "practitioner-789",
        "priority": "routine",  # routine, urgent, asap, stat
        "reason": "Dor moderada",
        "substitution_allowed": true,
        "validity_period": 30  # Dias de validade da receita
    }
    """
    fhir = FHIRService(request.user)
    
    if request.method == 'GET':
        try:
            params = {}
            
            # Filtro por paciente
            if request.query_params.get('patient'):
                params['subject'] = f"Patient/{request.query_params['patient']}"
            
            # Filtro por status
            if request.query_params.get('status'):
                req_status = request.query_params['status']
                if req_status not in VALID_STATUSES:
                    return Response(
                        {'error': f'Status inválido. Use: {", ".join(VALID_STATUSES)}'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                params['status'] = req_status
            
            # Filtro por intent
            if request.query_params.get('intent'):
                params['intent'] = request.query_params['intent']
            
            # Filtro por medicamento
            if request.query_params.get('medication'):
                params['medication.code'] = request.query_params['medication']
            
            # Filtro por prescritor
            if request.query_params.get('requester'):
                params['requester'] = f"Practitioner/{request.query_params['requester']}"
            
            # Filtro por data
            if request.query_params.get('authoredon'):
                params['authoredon'] = request.query_params['authoredon']
            
            # Paginação
            count = int(request.query_params.get('_count', 50))
            offset = int(request.query_params.get('_getpagesoffset', 0))
            params['_count'] = count
            if offset > 0:
                params['_getpagesoffset'] = offset
            params['_sort'] = '-authoredon'
            
            results = fhir.search_resources('MedicationRequest', params)
            
            return Response({
                'total': len(results),
                'count': count,
                'offset': offset,
                'results': results
            })
            
        except Exception as e:
            logger.error(f"Error listing medication requests: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    elif request.method == 'POST':
        try:
            data = request.data
            
            # Validar campos obrigatórios
            if not data.get('patient_id'):
                return Response(
                    {'error': 'Campo obrigatório ausente: patient_id'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if not data.get('medication'):
                return Response(
                    {'error': 'Campo obrigatório ausente: medication'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            med = data['medication']
            if not med.get('code') or not med.get('display'):
                return Response(
                    {'error': 'medication deve conter code e display'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Construir recurso MedicationRequest FHIR
            med_request = {
                'resourceType': 'MedicationRequest',
                'status': data.get('status', 'active'),
                'intent': data.get('intent', 'order'),
                'subject': {
                    'reference': f"Patient/{data['patient_id']}"
                }
            }
            
            # Validar status e intent
            if med_request['status'] not in VALID_STATUSES:
                return Response(
                    {'error': f'Status inválido. Use: {", ".join(VALID_STATUSES)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if med_request['intent'] not in VALID_INTENTS:
                return Response(
                    {'error': f'Intent inválido. Use: {", ".join(VALID_INTENTS)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Medicamento (ANVISA ou RxNorm)
            code_system = med.get('code_system', 'anvisa')
            if code_system == 'anvisa':
                system_url = 'http://www.anvisa.gov.br/medicamentos'
            else:
                system_url = 'http://www.nlm.nih.gov/research/umls/rxnorm'
            
            med_request['medicationCodeableConcept'] = {
                'coding': [{
                    'system': system_url,
                    'code': med['code'],
                    'display': med['display']
                }],
                'text': med['display']
            }
            
            # Dosagem estruturada
            if data.get('dosage'):
                dosage_data = data['dosage']
                dosage = {
                    'text': dosage_data.get('instructions', f"{dosage_data.get('dose_value', 1)} {dosage_data.get('dose_unit', 'unidade')}")
                }
                
                # Dose
                if dosage_data.get('dose_value'):
                    dosage['doseAndRate'] = [{
                        'type': {
                            'coding': [{
                                'system': 'http://terminology.hl7.org/CodeSystem/dose-rate-type',
                                'code': 'ordered',
                                'display': 'Ordered'
                            }]
                        },
                        'doseQuantity': {
                            'value': dosage_data['dose_value'],
                            'unit': dosage_data.get('dose_unit', 'unidade'),
                            'system': 'http://unitsofmeasure.org',
                            'code': dosage_data.get('dose_unit', '{unit}')
                        }
                    }]
                
                # Via de administração
                if dosage_data.get('route'):
                    route_key = dosage_data['route'].lower()
                    if route_key in ROUTES:
                        route_code, route_display = ROUTES[route_key]
                        dosage['route'] = {
                            'coding': [{
                                'system': 'http://snomed.info/sct',
                                'code': route_code,
                                'display': route_display
                            }]
                        }
                
                # Timing (frequência)
                if dosage_data.get('frequency'):
                    freq = dosage_data['frequency']
                    timing = {'repeat': {}}
                    
                    # Frequência: a cada X horas/dias
                    if freq.get('value') and freq.get('unit'):
                        timing['repeat']['frequency'] = 1
                        timing['repeat']['period'] = freq['value']
                        unit_map = {'h': 'h', 'd': 'd', 'wk': 'wk', 'mo': 'mo'}
                        timing['repeat']['periodUnit'] = unit_map.get(freq['unit'], 'h')
                    
                    # Duração do tratamento
                    if dosage_data.get('duration'):
                        dur = dosage_data['duration']
                        timing['repeat']['boundsDuration'] = {
                            'value': dur['value'],
                            'unit': 'dias' if dur['unit'] == 'd' else dur['unit'],
                            'system': 'http://unitsofmeasure.org',
                            'code': dur['unit']
                        }
                    
                    dosage['timing'] = timing
                
                # Instruções adicionais
                if dosage_data.get('instructions'):
                    dosage['patientInstruction'] = dosage_data['instructions']
                
                med_request['dosageInstruction'] = [dosage]
            
            # Dispense request (quantidade)
            if data.get('dispense'):
                disp = data['dispense']
                dispense_req = {}
                
                if disp.get('quantity'):
                    dispense_req['quantity'] = {
                        'value': disp['quantity'],
                        'unit': med.get('form', 'unidade'),
                        'system': 'http://unitsofmeasure.org',
                        'code': '{unit}'
                    }
                
                if disp.get('supply_duration'):
                    dispense_req['expectedSupplyDuration'] = {
                        'value': disp['supply_duration'],
                        'unit': 'dias',
                        'system': 'http://unitsofmeasure.org',
                        'code': 'd'
                    }
                
                if dispense_req:
                    med_request['dispenseRequest'] = dispense_req
            
            # Validade da receita
            if data.get('validity_period'):
                now = datetime.utcnow()
                end = now + timedelta(days=data['validity_period'])
                med_request['dispenseRequest'] = med_request.get('dispenseRequest', {})
                med_request['dispenseRequest']['validityPeriod'] = {
                    'start': now.strftime('%Y-%m-%d'),
                    'end': end.strftime('%Y-%m-%d')
                }
            
            # Encounter
            if data.get('encounter_id'):
                med_request['encounter'] = {
                    'reference': f"Encounter/{data['encounter_id']}"
                }
            
            # Prescritor
            if data.get('requester_id'):
                med_request['requester'] = {
                    'reference': f"Practitioner/{data['requester_id']}"
                }
            
            # Prioridade
            if data.get('priority'):
                med_request['priority'] = data['priority']
            
            # Motivo/Razão
            if data.get('reason'):
                med_request['reasonCode'] = [{
                    'text': data['reason']
                }]
            
            # Substituição permitida
            if 'substitution_allowed' in data:
                med_request['substitution'] = {
                    'allowedBoolean': data['substitution_allowed']
                }
            
            # Data de criação
            med_request['authoredOn'] = datetime.utcnow().isoformat() + 'Z'
            
            # Criar no HAPI FHIR
            result = fhir.create_resource('MedicationRequest', med_request)
            
            logger.info(f"MedicationRequest created: {result.get('id')} - {med['display']}")
            
            return Response({
                'id': result.get('id'),
                'resourceType': 'MedicationRequest',
                'status': med_request['status'],
                'medication': med['display'],
                'patient_id': data['patient_id'],
                'message': 'Prescrição criada com sucesso'
            }, status=status.HTTP_201_CREATED)
            
        except FHIRServiceException as e:
            logger.error(f"FHIR error creating medication request: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            logger.error(f"Error creating medication request: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@api_view(['GET', 'PUT', 'DELETE'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def medication_request_detail(request, medication_request_id):
    """
    GET: Busca prescrição por ID
    PUT: Atualiza prescrição (status, dosagem)
    DELETE: Cancela prescrição
    """
    fhir = FHIRService(request.user)
    
    if request.method == 'GET':
        try:
            results = fhir.search_resources('MedicationRequest', {'_id': medication_request_id})
            
            if not results:
                return Response(
                    {'error': 'Prescrição não encontrada'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            return Response(results[0])
            
        except Exception as e:
            logger.error(f"Error getting medication request {medication_request_id}: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    elif request.method == 'PUT':
        try:
            data = request.data
            
            # Buscar prescrição existente
            results = fhir.search_resources('MedicationRequest', {'_id': medication_request_id}, use_cache=False)
            
            if not results:
                return Response(
                    {'error': 'Prescrição não encontrada'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            existing = results[0]
            
            # Atualizar campos permitidos
            if data.get('status'):
                if data['status'] not in VALID_STATUSES:
                    return Response(
                        {'error': f'Status inválido. Use: {", ".join(VALID_STATUSES)}'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                existing['status'] = data['status']
            
            # Atualizar via PUT
            response = fhir.session.put(
                f"{fhir.base_url}/MedicationRequest/{medication_request_id}",
                json=existing,
                timeout=fhir.timeout
            )
            
            if response.status_code not in [200, 201]:
                raise FHIRServiceException(f"Failed to update: {response.text}")
            
            fhir.clear_cache('MedicationRequest')
            
            return Response(response.json())
            
        except Exception as e:
            logger.error(f"Error updating medication request {medication_request_id}: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    elif request.method == 'DELETE':
        try:
            # Cancelar prescrição (soft delete)
            results = fhir.search_resources('MedicationRequest', {'_id': medication_request_id}, use_cache=False)
            
            if not results:
                return Response(
                    {'error': 'Prescrição não encontrada'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            existing = results[0]
            existing['status'] = 'cancelled'
            
            response = fhir.session.put(
                f"{fhir.base_url}/MedicationRequest/{medication_request_id}",
                json=existing,
                timeout=fhir.timeout
            )
            
            if response.status_code not in [200, 201]:
                raise FHIRServiceException(f"Failed to cancel: {response.text}")
            
            fhir.clear_cache('MedicationRequest')
            
            return Response({
                'message': 'Prescrição cancelada com sucesso',
                'id': medication_request_id
            })
            
        except Exception as e:
            logger.error(f"Error cancelling medication request {medication_request_id}: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def patient_medications(request, patient_id):
    """
    Lista todas as prescrições de um paciente.
    
    GET /api/v1/patients/<patient_id>/medications/
    
    Parâmetros:
    - status: Filtrar por status (active, completed, etc.)
    - _count: Limite de resultados
    """
    fhir = FHIRService(request.user)
    
    try:
        params = {
            'subject': f"Patient/{patient_id}",
            '_sort': '-authoredon'
        }
        
        if request.query_params.get('status'):
            params['status'] = request.query_params['status']
        
        count = int(request.query_params.get('_count', 50))
        params['_count'] = count
        
        results = fhir.search_resources('MedicationRequest', params)
        
        return Response({
            'patient_id': patient_id,
            'total': len(results),
            'medications': results
        })
        
    except Exception as e:
        logger.error(f"Error getting medications for patient {patient_id}: {e}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
