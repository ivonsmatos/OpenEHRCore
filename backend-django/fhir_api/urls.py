
from django.urls import path
from rest_framework.routers import DefaultRouter
from .views_financial import CoverageViewSet, AccountViewSet, InvoiceViewSet
from . import views_auth, views_documents, views_analytics, views_clinical, views_export, views_audit, views_ai, views_visitors, views_chat, views_ipd, views_practitioners

router = DefaultRouter()
router.register(r'financial/coverage', CoverageViewSet, basename='coverage')
router.register(r'financial/accounts', AccountViewSet, basename='account')
router.register(r'financial/invoices', InvoiceViewSet, basename='invoice')

urlpatterns = [
    # Health check
    path('health/', views_auth.health_check, name='health_check'),
    
    # Autenticação
    path('auth/login/', views_auth.login, name='login'),
    
    # Patient endpoints
    path('patients/', views_auth.manage_patients, name='manage_patients'),
    path('patients/<str:patient_id>/', views_auth.get_patient, name='get_patient'),
    
    # Encounter endpoints
    path('encounters/', views_auth.create_encounter, name='create_encounter'),
    path('patients/<str:patient_id>/encounters/', views_auth.get_encounters, name='get_encounters'),
    
    # Observation endpoints
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
    
    # Schedule & Slot endpoints
    path('schedule/', views_auth.create_schedule, name='create_schedule'),
    path('slots/', views_auth.create_slot, name='create_slot'),
    path('slots/search/', views_auth.get_slots, name='get_slots'),
    
    # Questionnaire endpoints
    path('questionnaires/', views_auth.create_questionnaire_view, name='create_questionnaire'),
    path('questionnaires/response/', views_auth.create_response_view, name='create_response'),

    # Sprint 5: Portal do Paciente
    path('patient/dashboard/', views_auth.patient_dashboard, name='patient_dashboard'),
    path('patient/appointments/', views_auth.get_my_appointments, name='patient_appointments'),
    path('patient/exams/', views_auth.get_my_exams, name='patient_exams'),
    
    # Sprint 8: Documentos & PDF
    path('documents/', views_documents.documents_list_create, name='documents_list_create'),
    path('documents/<str:composition_id>/', views_documents.delete_document, name='delete_document'), 
    path('documents/<str:composition_id>/pdf/', views_documents.generate_pdf, name='generate_pdf'),
    
    # Sprint 9: Analytics
    # Sprint 9: Analytics (Deprecated/Replaced)
    # path('analytics/dashboard/', views_analytics.dashboard_stats, name='dashboard_stats'),

    # Sprint 10: Immunization & Diagnostic Results
    path('immunizations/', views_clinical.create_immunization, name='create_immunization'),
    path('patients/<str:patient_id>/immunizations/', views_clinical.get_immunizations, name='get_immunizations'),
    path('diagnostic-reports/', views_clinical.create_diagnostic_report, name='create_diagnostic_report'),
    path('patients/<str:patient_id>/diagnostic-reports/', views_clinical.get_diagnostic_reports, name='get_diagnostic_reports'),

    # Sprint 11: Export Data & Audit
    path('patients/<str:patient_id>/export/', views_export.export_patient_data_view, name='export_patient_data'),
    path('audit/logs/', views_audit.get_audit_logs, name='get_audit_logs'),
    
    # Sprint 12: AI
    path('ai/summary/<str:patient_id>/', views_ai.get_patient_summary, name='ai_summary'),
    path('ai/interactions/', views_ai.check_interactions, name='ai_interactions'),

    # Sprint 13: Analytics
    path('analytics/population/', views_analytics.get_population_metrics),
    path('analytics/clinical/', views_analytics.get_clinical_metrics),
    path('analytics/operational/', views_analytics.get_operational_metrics),
    path('analytics/kpi/', views_analytics.get_kpi_metrics, name='analytics-kpi'),
    path('analytics/survey/', views_analytics.get_survey_metrics, name='analytics-survey'),
    path('analytics/admissions/', views_analytics.get_admissions_metrics, name='analytics-admissions'),
    path('analytics/report/', views_analytics.generate_analytics_report, name='analytics-report'),

    # Sprint 14: Visitors
    path('visitors/', views_visitors.list_visitors, name='list_visitors'),
    path('visitors/create/', views_visitors.create_visitor, name='create_visitor'),

    # Sprint 15: Chat (Gap Analysis)
    path('chat/channels/', views_chat.list_channels, name='list_channels'),
    path('chat/channels/create/', views_chat.create_channel, name='create_channel'),
    path('chat/messages/', views_chat.list_messages, name='list_messages'),
    path('chat/send/', views_chat.send_message, name='send_message'),

    # Sprint 16: Inpatient Management (Bed Management)
    path('ipd/locations/', views_ipd.list_locations, name='list_locations'),
    path('ipd/occupancy/', views_ipd.get_occupancy, name='get_occupancy'),
    path('ipd/admit/', views_ipd.admit_patient, name='admit_patient'),
    path('ipd/bed/<str:location_id>/details/', views_ipd.get_bed_details, name='get_bed_details'),
    path('ipd/discharge/', views_ipd.discharge_patient, name='discharge_patient'),
    path('ipd/bed/<str:location_id>/clean/', views_ipd.finish_cleaning, name='finish_cleaning'),
    path('ipd/transfer/', views_ipd.transfer_patient, name='transfer_patient'),
    path('ipd/bed/<str:location_id>/block/', views_ipd.block_bed, name='block_bed'),
    path('ipd/bed/<str:location_id>/history/', views_ipd.get_bed_history, name='get_bed_history'),
    
    # Sprint 18: Practitioner Management (FHIR Compliance)
    path('practitioners/', views_practitioners.create_practitioner, name='create_practitioner'),
    path('practitioners/list/', views_practitioners.list_practitioners, name='list_practitioners'),
    path('practitioners/<str:practitioner_id>/', views_practitioners.get_practitioner, name='get_practitioner'),
    path('practitioner-roles/', views_practitioners.create_practitioner_role, name='create_practitioner_role'),
]


urlpatterns += router.urls
