"""
CarePlan - Plano de Cuidados FHIR
Gerenciamento de planos de tratamento para pacientes crônicos
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


@api_view(['GET', 'POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def manage_careplans(request):
    """
    GET: Lista todos os CarePlans
    POST: Cria novo CarePlan
    
    Endpoints:
    GET  /api/v1/careplans/
    POST /api/v1/careplans/
    """
    fhir_service = FHIRService(request.user)
    
    if request.method == 'GET':
        try:
            # Parâmetros de busca
            patient_id = request.query_params.get('patient')
            status_filter = request.query_params.get('status', 'active')
            category = request.query_params.get('category')
            
            search_params = {}
            if patient_id:
                search_params['patient'] = patient_id
            if status_filter:
                search_params['status'] = status_filter
            if category:
                search_params['category'] = category
            
            careplans = fhir_service.search_resources('CarePlan', search_params)
            
            # Formatar resposta
            result = []
            for cp in careplans:
                result.append({
                    'id': cp.get('id'),
                    'status': cp.get('status'),
                    'intent': cp.get('intent'),
                    'title': cp.get('title'),
                    'description': cp.get('description'),
                    'subject': cp.get('subject', {}).get('reference'),
                    'period': cp.get('period'),
                    'category': [cat.get('coding', [{}])[0].get('display') for cat in cp.get('category', [])],
                    'author': cp.get('author', {}).get('reference'),
                    'created': cp.get('created'),
                    'goal_count': len(cp.get('goal', [])),
                    'activity_count': len(cp.get('activity', []))
                })
            
            return Response({
                'count': len(result),
                'results': result
            })
        except Exception as e:
            logger.error(f"Erro ao buscar CarePlans: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'POST':
        try:
            data = request.data
            
            # Validar campos obrigatórios
            if not data.get('patient_id'):
                return Response({'error': 'patient_id é obrigatório'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Construir recurso CarePlan FHIR
            careplan = {
                'resourceType': 'CarePlan',
                'status': data.get('status', 'active'),
                'intent': data.get('intent', 'plan'),
                'title': data.get('title'),
                'description': data.get('description'),
                'subject': {
                    'reference': f"Patient/{data['patient_id']}"
                },
                'period': {
                    'start': data.get('start_date', datetime.now().strftime('%Y-%m-%d'))
                },
                'category': [{
                    'coding': [{
                        'system': 'http://snomed.info/sct',
                        'code': data.get('category_code', '734163000'),
                        'display': data.get('category_display', 'Plano de cuidados')
                    }]
                }],
                'created': datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
                'author': {
                    'reference': f"Practitioner/{data.get('author_id', 'unknown')}"
                }
            }
            
            # Adicionar período de término se fornecido
            if data.get('end_date'):
                careplan['period']['end'] = data['end_date']
            
            # Adicionar metas se fornecidas
            if data.get('goals'):
                careplan['goal'] = []
                for goal in data['goals']:
                    careplan['goal'].append({
                        'reference': goal if goal.startswith('Goal/') else f"Goal/{goal}"
                    })
            
            # Adicionar atividades se fornecidas
            if data.get('activities'):
                careplan['activity'] = []
                for activity in data['activities']:
                    careplan['activity'].append({
                        'detail': {
                            'status': activity.get('status', 'not-started'),
                            'description': activity.get('description'),
                            'code': {
                                'coding': [{
                                    'system': 'http://snomed.info/sct',
                                    'code': activity.get('code', ''),
                                    'display': activity.get('display', '')
                                }]
                            } if activity.get('code') else None
                        }
                    })
            
            # Criar no FHIR server
            result = fhir_service.create_resource('CarePlan', careplan)
            
            logger.info(f"CarePlan criado: {result.get('id')} para paciente {data['patient_id']}")
            
            return Response({
                'id': result.get('id'),
                'message': 'Plano de cuidados criado com sucesso',
                'careplan': result
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Erro ao criar CarePlan: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'PUT', 'DELETE'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def careplan_detail(request, careplan_id):
    """
    GET: Obtém detalhes do CarePlan
    PUT: Atualiza CarePlan
    DELETE: Remove CarePlan
    
    Endpoints:
    GET    /api/v1/careplans/{id}/
    PUT    /api/v1/careplans/{id}/
    DELETE /api/v1/careplans/{id}/
    """
    fhir_service = FHIRService(request.user)
    
    if request.method == 'GET':
        try:
            careplan = fhir_service.get_resource('CarePlan', careplan_id)
            if not careplan:
                return Response({'error': 'CarePlan não encontrado'}, status=status.HTTP_404_NOT_FOUND)
            
            return Response(careplan)
        except Exception as e:
            logger.error(f"Erro ao buscar CarePlan {careplan_id}: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'PUT':
        try:
            data = request.data
            
            # Buscar CarePlan existente
            existing = fhir_service.get_resource('CarePlan', careplan_id)
            if not existing:
                return Response({'error': 'CarePlan não encontrado'}, status=status.HTTP_404_NOT_FOUND)
            
            # Atualizar campos
            if 'status' in data:
                existing['status'] = data['status']
            if 'title' in data:
                existing['title'] = data['title']
            if 'description' in data:
                existing['description'] = data['description']
            if 'end_date' in data:
                existing['period']['end'] = data['end_date']
            
            # Atualizar no FHIR server
            result = fhir_service.update_resource('CarePlan', careplan_id, existing)
            
            return Response({
                'message': 'CarePlan atualizado com sucesso',
                'careplan': result
            })
        except Exception as e:
            logger.error(f"Erro ao atualizar CarePlan {careplan_id}: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'DELETE':
        try:
            fhir_service.delete_resource('CarePlan', careplan_id)
            return Response({'message': 'CarePlan removido'}, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            logger.error(f"Erro ao remover CarePlan {careplan_id}: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def patient_careplans(request, patient_id):
    """
    Lista CarePlans de um paciente específico
    GET /api/v1/patients/{patient_id}/careplans/
    """
    fhir_service = FHIRService(request.user)
    
    try:
        status_filter = request.query_params.get('status', 'active')
        
        careplans = fhir_service.search_resources('CarePlan', {
            'patient': patient_id,
            'status': status_filter
        })
        
        return Response({
            'patient_id': patient_id,
            'count': len(careplans),
            'results': careplans
        })
    except Exception as e:
        logger.error(f"Erro ao buscar CarePlans do paciente {patient_id}: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def add_careplan_activity(request, careplan_id):
    """
    Adiciona atividade ao CarePlan
    POST /api/v1/careplans/{id}/activities/
    """
    fhir_service = FHIRService(request.user)
    
    try:
        data = request.data
        
        # Buscar CarePlan
        careplan = fhir_service.get_resource('CarePlan', careplan_id)
        if not careplan:
            return Response({'error': 'CarePlan não encontrado'}, status=status.HTTP_404_NOT_FOUND)
        
        # Criar atividade
        activity = {
            'detail': {
                'status': data.get('status', 'not-started'),
                'description': data.get('description'),
                'scheduledPeriod': {
                    'start': data.get('start_date'),
                    'end': data.get('end_date')
                } if data.get('start_date') else None
            }
        }
        
        # Se referência a procedimento
        if data.get('procedure_reference'):
            activity['reference'] = {
                'reference': data['procedure_reference']
            }
        
        # Adicionar ao CarePlan
        if 'activity' not in careplan:
            careplan['activity'] = []
        careplan['activity'].append(activity)
        
        # Atualizar
        result = fhir_service.update_resource('CarePlan', careplan_id, careplan)
        
        return Response({
            'message': 'Atividade adicionada ao CarePlan',
            'activity_count': len(result.get('activity', []))
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Erro ao adicionar atividade ao CarePlan {careplan_id}: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def manage_goals(request):
    """
    Gerencia Goals (Metas) FHIR
    GET: Lista metas
    POST: Cria nova meta
    
    Endpoints:
    GET  /api/v1/goals/
    POST /api/v1/goals/
    """
    fhir_service = FHIRService(request.user)
    
    if request.method == 'GET':
        try:
            patient_id = request.query_params.get('patient')
            search_params = {}
            if patient_id:
                search_params['patient'] = patient_id
            
            goals = fhir_service.search_resources('Goal', search_params)
            return Response({
                'count': len(goals),
                'results': goals
            })
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'POST':
        try:
            data = request.data
            
            goal = {
                'resourceType': 'Goal',
                'lifecycleStatus': data.get('status', 'active'),
                'description': {
                    'text': data.get('description')
                },
                'subject': {
                    'reference': f"Patient/{data['patient_id']}"
                },
                'startDate': data.get('start_date', datetime.now().strftime('%Y-%m-%d')),
                'target': [{
                    'measure': {
                        'coding': [{
                            'display': data.get('target_measure', '')
                        }]
                    },
                    'detailString': data.get('target_value'),
                    'dueDate': data.get('due_date')
                }] if data.get('target_measure') or data.get('due_date') else None
            }
            
            result = fhir_service.create_resource('Goal', goal)
            
            return Response({
                'id': result.get('id'),
                'message': 'Meta criada com sucesso'
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Erro ao criar Goal: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
