"""
Questionnaire Views - FHIR Questionnaires & Assessments

Sprint 36: Dynamic Forms Endpoints
"""

import logging
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny

from .authentication import KeycloakAuthentication
from .services.questionnaire_service import QuestionnaireService, get_questionnaire_service

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([AllowAny])
def list_questionnaires(request):
    """
    List available questionnaires.
    
    GET /api/v1/questionnaires/
    GET /api/v1/questionnaires/?purpose=screening
    """
    purpose = request.query_params.get('purpose')
    
    questionnaires = QuestionnaireService.list_questionnaires(purpose)
    
    return Response({
        'count': len(questionnaires),
        'questionnaires': questionnaires
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def get_questionnaire(request, questionnaire_id):
    """
    Get a specific questionnaire.
    
    GET /api/v1/questionnaires/{id}/
    """
    questionnaire = QuestionnaireService.get_questionnaire(questionnaire_id)
    
    if not questionnaire:
        return Response({
            'error': f'Questionnaire not found: {questionnaire_id}'
        }, status=status.HTTP_404_NOT_FOUND)
    
    return Response(questionnaire.to_fhir())


@api_view(['POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def create_questionnaire(request):
    """
    Create a custom questionnaire.
    
    POST /api/v1/questionnaires/
    
    Body:
        {
            "title": "Meu Questionário",
            "name": "MeuQuestionario",
            "description": "Descrição",
            "purpose": "intake",
            "items": [...]
        }
    """
    try:
        questionnaire = QuestionnaireService.create_questionnaire(request.data)
        return Response(questionnaire.to_fhir(), status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def submit_response(request, questionnaire_id):
    """
    Submit a questionnaire response.
    
    POST /api/v1/questionnaires/{id}/responses/
    
    Body:
        {
            "patient_id": "patient-123",
            "answers": {
                "phq1": "2",
                "phq2": "1",
                ...
            }
        }
    """
    patient_id = request.data.get('patient_id')
    answers = request.data.get('answers', {})
    practitioner_id = request.data.get('practitioner_id')
    
    if not patient_id:
        return Response({
            'error': 'patient_id is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if not answers:
        return Response({
            'error': 'answers are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        result = QuestionnaireService.submit_response(
            questionnaire_id=questionnaire_id,
            patient_id=patient_id,
            answers=answers,
            practitioner_id=practitioner_id
        )
        return Response(result, status=status.HTTP_201_CREATED)
    except ValueError as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def get_responses(request):
    """
    Get questionnaire responses.
    
    GET /api/v1/questionnaire-responses/
    GET /api/v1/questionnaire-responses/?patient_id=123
    GET /api/v1/questionnaire-responses/?questionnaire_id=phq-9
    """
    patient_id = request.query_params.get('patient_id')
    questionnaire_id = request.query_params.get('questionnaire_id')
    
    responses = QuestionnaireService.get_responses(
        patient_id=patient_id,
        questionnaire_id=questionnaire_id
    )
    
    return Response({
        'count': len(responses),
        'responses': responses
    })


@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def get_response(request, response_id):
    """
    Get a specific questionnaire response.
    
    GET /api/v1/questionnaire-responses/{id}/
    """
    response = QuestionnaireService.get_response(response_id)
    
    if not response:
        return Response({
            'error': f'Response not found: {response_id}'
        }, status=status.HTTP_404_NOT_FOUND)
    
    return Response(response)


@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def patient_assessments(request, patient_id):
    """
    Get all assessments for a patient with scores.
    
    GET /api/v1/patients/{id}/assessments/
    """
    responses = QuestionnaireService.get_responses(patient_id=patient_id)
    
    # Group by questionnaire
    assessments = {}
    for resp in responses:
        q_id = resp['questionnaire_id']
        if q_id not in assessments:
            questionnaire = QuestionnaireService.get_questionnaire(q_id)
            assessments[q_id] = {
                'questionnaire': {
                    'id': q_id,
                    'title': questionnaire.title if questionnaire else q_id,
                    'purpose': questionnaire.purpose if questionnaire else None
                },
                'responses': []
            }
        
        assessments[q_id]['responses'].append({
            'id': resp['response']['id'],
            'date': resp['response'].get('authored'),
            'score': resp.get('score'),
            'interpretation': resp.get('interpretation')
        })
    
    return Response({
        'patient_id': patient_id,
        'assessments': list(assessments.values())
    })
