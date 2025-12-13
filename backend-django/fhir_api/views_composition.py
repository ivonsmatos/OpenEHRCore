"""
Composition - Prontuário Clínico Estruturado FHIR
Documentos clínicos: Resumo de Alta, Evolução, Nota de Admissão, Relatório Operatório
"""

import logging
from datetime import datetime
from django.conf import settings
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework import status
from .auth import KeycloakAuthentication
from rest_framework.permissions import IsAuthenticated
from .services.fhir_core import FHIRService

logger = logging.getLogger(__name__)

# Tipos de composição suportados
COMPOSITION_TYPES = {
    'discharge-summary': {
        'code': '18842-5',
        'display': 'Resumo de Alta Hospitalar',
        'system': 'http://loinc.org'
    },
    'progress-note': {
        'code': '11506-3',
        'display': 'Evolução Médica',
        'system': 'http://loinc.org'
    },
    'admission-note': {
        'code': '34133-9',
        'display': 'Nota de Admissão',
        'system': 'http://loinc.org'
    },
    'operative-note': {
        'code': '11504-8',
        'display': 'Relatório Operatório',
        'system': 'http://loinc.org'
    },
    'consultation-note': {
        'code': '11488-4',
        'display': 'Parecer Médico',
        'system': 'http://loinc.org'
    },
    'nursing-note': {
        'code': '34746-8',
        'display': 'Anotação de Enfermagem',
        'system': 'http://loinc.org'
    }
}


@api_view(['GET', 'POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def manage_compositions(request):
    """
    GET: Lista composições/documentos clínicos
    POST: Cria nova composição
    
    Endpoints:
    GET  /api/v1/compositions/
    POST /api/v1/compositions/
    """
    fhir_service = FHIRService(request.user)
    
    if request.method == 'GET':
        try:
            patient_id = request.query_params.get('patient')
            composition_type = request.query_params.get('type')
            encounter_id = request.query_params.get('encounter')
            
            search_params = {}
            if patient_id:
                search_params['subject'] = f'Patient/{patient_id}'
            if composition_type:
                type_info = COMPOSITION_TYPES.get(composition_type, {})
                if type_info:
                    search_params['type'] = type_info.get('code')
            if encounter_id:
                search_params['encounter'] = f'Encounter/{encounter_id}'
            
            compositions = fhir_service.search_resources('Composition', search_params)
            
            result = []
            for comp in compositions:
                type_coding = comp.get('type', {}).get('coding', [{}])[0]
                result.append({
                    'id': comp.get('id'),
                    'status': comp.get('status'),
                    'type': type_coding.get('display'),
                    'type_code': type_coding.get('code'),
                    'title': comp.get('title'),
                    'date': comp.get('date'),
                    'subject': comp.get('subject', {}).get('reference'),
                    'author': [a.get('reference') for a in comp.get('author', [])],
                    'encounter': comp.get('encounter', {}).get('reference'),
                    'section_count': len(comp.get('section', []))
                })
            
            return Response({
                'count': len(result),
                'results': result,
                'available_types': list(COMPOSITION_TYPES.keys())
            })
            
        except Exception as e:
            logger.error(f"Erro ao buscar Compositions: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'POST':
        try:
            data = request.data
            
            # Validações
            if not data.get('patient_id'):
                return Response({'error': 'patient_id é obrigatório'}, status=status.HTTP_400_BAD_REQUEST)
            if not data.get('type'):
                return Response({'error': 'type é obrigatório'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Obter informações do tipo
            composition_type = data['type']
            type_info = COMPOSITION_TYPES.get(composition_type)
            if not type_info:
                return Response({
                    'error': f'Tipo inválido. Tipos válidos: {list(COMPOSITION_TYPES.keys())}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Construir Composition FHIR
            composition = {
                'resourceType': 'Composition',
                'status': data.get('status', 'final'),
                'type': {
                    'coding': [{
                        'system': type_info['system'],
                        'code': type_info['code'],
                        'display': type_info['display']
                    }]
                },
                'subject': {
                    'reference': f"Patient/{data['patient_id']}"
                },
                'date': datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
                'title': data.get('title', type_info['display']),
                'author': [{
                    'reference': f"Practitioner/{data.get('author_id', 'unknown')}"
                }]
            }
            
            # Adicionar encounter se fornecido
            if data.get('encounter_id'):
                composition['encounter'] = {
                    'reference': f"Encounter/{data['encounter_id']}"
                }
            
            # Construir seções do documento
            composition['section'] = []
            
            # Seções específicas por tipo de documento
            if composition_type == 'discharge-summary':
                composition['section'] = build_discharge_sections(data)
            elif composition_type == 'progress-note':
                composition['section'] = build_progress_sections(data)
            elif composition_type == 'operative-note':
                composition['section'] = build_operative_sections(data)
            elif composition_type == 'admission-note':
                composition['section'] = build_admission_sections(data)
            else:
                # Seção genérica
                if data.get('content'):
                    composition['section'].append({
                        'title': 'Conteúdo',
                        'text': {
                            'status': 'generated',
                            'div': f"<div xmlns=\"http://www.w3.org/1999/xhtml\">{data['content']}</div>"
                        }
                    })
            
            # Criar no FHIR server
            result = fhir_service.create_resource('Composition', composition)
            
            logger.info(f"Composition {composition_type} criada: {result.get('id')}")
            
            return Response({
                'id': result.get('id'),
                'type': composition_type,
                'message': f'{type_info["display"]} criado com sucesso'
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Erro ao criar Composition: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def build_discharge_sections(data):
    """Constrói seções para Resumo de Alta"""
    sections = []
    
    # Motivo da internação
    if data.get('admission_reason'):
        sections.append({
            'title': 'Motivo da Internação',
            'code': {
                'coding': [{'system': 'http://loinc.org', 'code': '46241-6', 'display': 'Hospital admission diagnosis'}]
            },
            'text': {
                'status': 'generated',
                'div': f"<div xmlns=\"http://www.w3.org/1999/xhtml\">{data['admission_reason']}</div>"
            }
        })
    
    # Resumo da evolução
    if data.get('clinical_evolution'):
        sections.append({
            'title': 'Evolução Clínica',
            'code': {
                'coding': [{'system': 'http://loinc.org', 'code': '8648-8', 'display': 'Hospital course'}]
            },
            'text': {
                'status': 'generated',
                'div': f"<div xmlns=\"http://www.w3.org/1999/xhtml\">{data['clinical_evolution']}</div>"
            }
        })
    
    # Diagnóstico de alta
    if data.get('discharge_diagnosis'):
        sections.append({
            'title': 'Diagnóstico de Alta',
            'code': {
                'coding': [{'system': 'http://loinc.org', 'code': '11535-2', 'display': 'Hospital discharge diagnosis'}]
            },
            'text': {
                'status': 'generated',
                'div': f"<div xmlns=\"http://www.w3.org/1999/xhtml\">{data['discharge_diagnosis']}</div>"
            }
        })
    
    # Condições de alta
    if data.get('discharge_condition'):
        sections.append({
            'title': 'Condições de Alta',
            'code': {
                'coding': [{'system': 'http://loinc.org', 'code': '8650-4', 'display': 'Hospital discharge status'}]
            },
            'text': {
                'status': 'generated',
                'div': f"<div xmlns=\"http://www.w3.org/1999/xhtml\">{data['discharge_condition']}</div>"
            }
        })
    
    # Orientações de alta
    if data.get('discharge_instructions'):
        sections.append({
            'title': 'Orientações de Alta',
            'code': {
                'coding': [{'system': 'http://loinc.org', 'code': '8653-8', 'display': 'Hospital discharge instructions'}]
            },
            'text': {
                'status': 'generated',
                'div': f"<div xmlns=\"http://www.w3.org/1999/xhtml\">{data['discharge_instructions']}</div>"
            }
        })
    
    # Medicamentos de alta
    if data.get('discharge_medications'):
        sections.append({
            'title': 'Prescrição de Alta',
            'code': {
                'coding': [{'system': 'http://loinc.org', 'code': '10183-2', 'display': 'Hospital discharge medications'}]
            },
            'text': {
                'status': 'generated',
                'div': f"<div xmlns=\"http://www.w3.org/1999/xhtml\">{data['discharge_medications']}</div>"
            }
        })
    
    return sections


def build_progress_sections(data):
    """Constrói seções para Evolução Médica (SOAP)"""
    sections = []
    
    # Subjetivo
    if data.get('subjective'):
        sections.append({
            'title': 'Subjetivo',
            'code': {
                'coding': [{'system': 'http://loinc.org', 'code': '61150-9', 'display': 'Subjective'}]
            },
            'text': {
                'status': 'generated',
                'div': f"<div xmlns=\"http://www.w3.org/1999/xhtml\">{data['subjective']}</div>"
            }
        })
    
    # Objetivo
    if data.get('objective'):
        sections.append({
            'title': 'Objetivo',
            'code': {
                'coding': [{'system': 'http://loinc.org', 'code': '61149-1', 'display': 'Objective'}]
            },
            'text': {
                'status': 'generated',
                'div': f"<div xmlns=\"http://www.w3.org/1999/xhtml\">{data['objective']}</div>"
            }
        })
    
    # Avaliação
    if data.get('assessment'):
        sections.append({
            'title': 'Avaliação',
            'code': {
                'coding': [{'system': 'http://loinc.org', 'code': '51848-0', 'display': 'Assessment'}]
            },
            'text': {
                'status': 'generated',
                'div': f"<div xmlns=\"http://www.w3.org/1999/xhtml\">{data['assessment']}</div>"
            }
        })
    
    # Plano
    if data.get('plan'):
        sections.append({
            'title': 'Plano',
            'code': {
                'coding': [{'system': 'http://loinc.org', 'code': '18776-5', 'display': 'Plan of care'}]
            },
            'text': {
                'status': 'generated',
                'div': f"<div xmlns=\"http://www.w3.org/1999/xhtml\">{data['plan']}</div>"
            }
        })
    
    return sections


def build_operative_sections(data):
    """Constrói seções para Relatório Operatório"""
    sections = []
    
    if data.get('preoperative_diagnosis'):
        sections.append({
            'title': 'Diagnóstico Pré-operatório',
            'text': {
                'status': 'generated',
                'div': f"<div xmlns=\"http://www.w3.org/1999/xhtml\">{data['preoperative_diagnosis']}</div>"
            }
        })
    
    if data.get('postoperative_diagnosis'):
        sections.append({
            'title': 'Diagnóstico Pós-operatório',
            'text': {
                'status': 'generated',
                'div': f"<div xmlns=\"http://www.w3.org/1999/xhtml\">{data['postoperative_diagnosis']}</div>"
            }
        })
    
    if data.get('procedure_performed'):
        sections.append({
            'title': 'Procedimento Realizado',
            'text': {
                'status': 'generated',
                'div': f"<div xmlns=\"http://www.w3.org/1999/xhtml\">{data['procedure_performed']}</div>"
            }
        })
    
    if data.get('surgical_findings'):
        sections.append({
            'title': 'Achados Cirúrgicos',
            'text': {
                'status': 'generated',
                'div': f"<div xmlns=\"http://www.w3.org/1999/xhtml\">{data['surgical_findings']}</div>"
            }
        })
    
    if data.get('anesthesia'):
        sections.append({
            'title': 'Anestesia',
            'text': {
                'status': 'generated',
                'div': f"<div xmlns=\"http://www.w3.org/1999/xhtml\">{data['anesthesia']}</div>"
            }
        })
    
    if data.get('complications'):
        sections.append({
            'title': 'Complicações',
            'text': {
                'status': 'generated',
                'div': f"<div xmlns=\"http://www.w3.org/1999/xhtml\">{data['complications']}</div>"
            }
        })
    
    return sections


def build_admission_sections(data):
    """Constrói seções para Nota de Admissão"""
    sections = []
    
    if data.get('chief_complaint'):
        sections.append({
            'title': 'Queixa Principal',
            'code': {
                'coding': [{'system': 'http://loinc.org', 'code': '10154-3', 'display': 'Chief complaint'}]
            },
            'text': {
                'status': 'generated',
                'div': f"<div xmlns=\"http://www.w3.org/1999/xhtml\">{data['chief_complaint']}</div>"
            }
        })
    
    if data.get('history_present_illness'):
        sections.append({
            'title': 'História da Doença Atual',
            'code': {
                'coding': [{'system': 'http://loinc.org', 'code': '10164-2', 'display': 'History of present illness'}]
            },
            'text': {
                'status': 'generated',
                'div': f"<div xmlns=\"http://www.w3.org/1999/xhtml\">{data['history_present_illness']}</div>"
            }
        })
    
    if data.get('past_medical_history'):
        sections.append({
            'title': 'Antecedentes Médicos',
            'code': {
                'coding': [{'system': 'http://loinc.org', 'code': '11348-0', 'display': 'Past medical history'}]
            },
            'text': {
                'status': 'generated',
                'div': f"<div xmlns=\"http://www.w3.org/1999/xhtml\">{data['past_medical_history']}</div>"
            }
        })
    
    if data.get('physical_exam'):
        sections.append({
            'title': 'Exame Físico',
            'code': {
                'coding': [{'system': 'http://loinc.org', 'code': '29545-1', 'display': 'Physical examination'}]
            },
            'text': {
                'status': 'generated',
                'div': f"<div xmlns=\"http://www.w3.org/1999/xhtml\">{data['physical_exam']}</div>"
            }
        })
    
    if data.get('admission_diagnosis'):
        sections.append({
            'title': 'Hipótese Diagnóstica',
            'code': {
                'coding': [{'system': 'http://loinc.org', 'code': '46241-6', 'display': 'Hospital admission diagnosis'}]
            },
            'text': {
                'status': 'generated',
                'div': f"<div xmlns=\"http://www.w3.org/1999/xhtml\">{data['admission_diagnosis']}</div>"
            }
        })
    
    if data.get('initial_plan'):
        sections.append({
            'title': 'Plano Inicial',
            'text': {
                'status': 'generated',
                'div': f"<div xmlns=\"http://www.w3.org/1999/xhtml\">{data['initial_plan']}</div>"
            }
        })
    
    return sections


@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def composition_detail(request, composition_id):
    """
    Obtém detalhes de uma composição
    GET /api/v1/compositions/{id}/
    """
    fhir_service = FHIRService(request.user)
    
    try:
        composition = fhir_service.get_resource('Composition', composition_id)
        if not composition:
            return Response({'error': 'Composição não encontrada'}, status=status.HTTP_404_NOT_FOUND)
        
        return Response(composition)
    except Exception as e:
        logger.error(f"Erro ao buscar Composition {composition_id}: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def patient_compositions(request, patient_id):
    """
    Lista documentos de um paciente
    GET /api/v1/patients/{patient_id}/compositions/
    """
    fhir_service = FHIRService(request.user)
    
    try:
        compositions = fhir_service.search_resources('Composition', {
            'subject': f'Patient/{patient_id}'
        })
        
        return Response({
            'patient_id': patient_id,
            'count': len(compositions),
            'results': compositions
        })
    except Exception as e:
        logger.error(f"Erro ao buscar Compositions do paciente {patient_id}: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def composition_types(request):
    """
    Lista tipos de composição disponíveis
    GET /api/v1/compositions/types/
    """
    types = []
    for key, value in COMPOSITION_TYPES.items():
        types.append({
            'code': key,
            'display': value['display'],
            'loinc_code': value['code']
        })
    
    return Response({
        'count': len(types),
        'types': types
    })
