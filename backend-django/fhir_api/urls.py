from django.urls import path
from .views_financial import CoverageViewSet, AccountViewSet, InvoiceViewSet
from . import views
from . import views_auth
from . import views_documents

urlpatterns = [
    # Health check (público)
    path('health/', views_auth.health_check, name='health_check'),
    
    # Autenticação
    path('auth/login/', views_auth.login, name='login'),
    
    # Patient endpoints (protegidos com auth)
    path('patients/', views_auth.manage_patients, name='manage_patients'),
    path('patients/<str:patient_id>/', views_auth.get_patient, name='get_patient'),
    
    # Encounter endpoints (protegidos com auth)
    path('encounters/', views_auth.create_encounter, name='create_encounter'),
    path('patients/<str:patient_id>/encounters/', views_auth.get_encounters, name='get_encounters'),
    
    # Observation endpoints (protegidos com auth)
    path('observations/', views_auth.create_observation, name='create_observation'),
    path('patients/<str:patient_id>/observations/', views_auth.get_observations, name='get_observations'),
    
    # Condition endpoints
    path('conditions/', views_auth.create_condition, name='create_condition'),
    path('patients/<str:patient_id>/conditions/', views_auth.get_conditions, name='get_conditions'),
    
    # Allergy endpoints
    path('allergies/', views_auth.create_allergy, name='create_allergy'),
    path('patients/<str:patient_id>/allergies/', views_auth.get_allergies, name='get_allergies'),
    
    # Appointment endpoints
    path('appointments/', views_auth.create_appointment, name='create_appointment'),
    path('patients/<str:patient_id>/appointments/', views_auth.get_appointments, name='get_appointments'),
    
    # Medication endpoints
    path('medications/', views_auth.create_medication_request, name='create_medication_request'),
    
    # ServiceRequest endpoints
    path('exams/', views_auth.create_service_request, name='create_service_request'),
    
    # ClinicalImpression endpoints
    path('clinical-impressions/', views_auth.create_clinical_impression, name='create_clinical_impression'),
    
    # Schedule & Slot endpoints (Sprint 4)
    path('schedule/', views_auth.create_schedule, name='create_schedule'),
    path('slots/', views_auth.create_slot, name='create_slot'),
    path('slots/search/', views_auth.get_slots, name='get_slots'),
    
    # Questionnaire endpoints (Sprint 4)
    path('questionnaires/', views_auth.create_questionnaire_view, name='create_questionnaire'),
    path('questionnaires/response/', views_auth.create_response_view, name='create_response'),

# ----------------------------------------------------------------------
    # Sprint 5: Portal do Paciente
    # ----------------------------------------------------------------------
    path('patient/dashboard/', views_auth.patient_dashboard, name='patient_dashboard'),
    path('patient/appointments/', views_auth.get_my_appointments, name='patient_appointments'),
    path('patient/exams/', views_auth.get_my_exams, name='patient_exams'),
    # ----------------------------------------------------------------------
    # Sprint 8: Documentos & PDF
    # ----------------------------------------------------------------------
    path('documents/', views_documents.documents_list_create, name='documents_list_create'),
    path('documents/<str:composition_id>/', views_documents.delete_document, name='delete_document'), # Supports DELETE
    path('documents/<str:composition_id>/pdf/', views_documents.generate_pdf, name='generate_pdf'),
]

from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'financial/coverage', CoverageViewSet, basename='coverage')
router.register(r'financial/accounts', AccountViewSet, basename='account')
router.register(r'financial/invoices', InvoiceViewSet, basename='invoice')

urlpatterns += router.urls
