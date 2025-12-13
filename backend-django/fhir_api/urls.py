
from django.urls import path
from rest_framework.routers import DefaultRouter
from .views_financial import CoverageViewSet, AccountViewSet, InvoiceViewSet
from . import views_auth, views_documents, views_analytics, views_clinical, views_export, views_audit, views_ai, views_visitors, views_chat, views_ipd, views_practitioners, views_consent, views_search, views_organization, views_procedure, views_medication, views_healthcare_service, views_diagnostic_report, views_consent_fhir, views_audit_event, views_terminology, views_bulk_data, views_lgpd, views_health, views_careplan, views_composition, views_tiss, views_rnds, views_integrations, views_referral, views_communication, views_notifications, views_cbo
from .metrics import metrics_view

router = DefaultRouter()
router.register(r'financial/coverage', CoverageViewSet, basename='coverage')
router.register(r'financial/accounts', AccountViewSet, basename='account')
router.register(r'financial/invoices', InvoiceViewSet, basename='invoice')

urlpatterns = [
    # Health Check endpoints (robustos)
    path('health/', views_health.health_check, name='health_check'),
    path('health/live/', views_health.health_check_simple, name='health_live'),
    path('health/ready/', views_health.health_check_ready, name='health_ready'),
    path('metrics/', metrics_view, name='metrics'),
    
    # Autenticação
    path('auth/login/', views_auth.login, name='login'),
    
    # Patient endpoints
    path('patients/', views_auth.manage_patients, name='manage_patients'),
    path('patients/search/', views_auth.search_patients_advanced, name='search_patients_advanced'),  # Sprint 20
    path('patients/<str:patient_id>/', views_auth.get_patient, name='get_patient'),
    
    # Encounter endpoints
    path('encounters/', views_auth.create_encounter, name='create_encounter'),
    path('encounters/search/', views_search.search_encounters, name='search_encounters'),  # Sprint 20
    path('patients/<str:patient_id>/encounters/', views_auth.get_encounters, name='get_encounters'),
    
    # Observation endpoints
    path('observations/', views_auth.create_observation, name='create_observation'),
    path('observations/search/', views_search.search_observations, name='search_observations'),  # Sprint 20
    path('patients/<str:patient_id>/observations/', views_auth.get_observations, name='get_observations'),
    
    # Condition endpoints
    path('conditions/', views_auth.create_condition, name='create_condition'),
    path('conditions/search/', views_search.search_conditions, name='search_conditions'),  # Sprint 20
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
    path('practitioners/search/', views_search.search_practitioners, name='search_practitioners'),  # Sprint 20
    path('practitioners/specialties/', views_practitioners.list_specialties, name='list_specialties'),  # Sprint 21
    path('practitioners/validate-identifier/', views_practitioners.validate_identifier, name='validate_identifier'),  # Sprint 21
    path('practitioners/<str:practitioner_id>/', views_practitioners.get_practitioner, name='get_practitioner'),
    path('practitioner-roles/', views_practitioners.create_practitioner_role, name='create_practitioner_role'),
    
    # Sprint 24: Consent & Privacy (LGPD)
    path('consents/', views_consent.create_consent, name='create_consent'),
    path('consents/list/', views_consent.list_consents, name='list_consents'),
    
    # Sprint 21: Organization (Estrutura Organizacional)
    path('organizations/', views_organization.manage_organizations, name='manage_organizations'),
    path('organizations/<str:organization_id>/', views_organization.organization_detail, name='organization_detail'),
    path('organizations/<str:organization_id>/hierarchy/', views_organization.organization_hierarchy, name='organization_hierarchy'),
    
    # Sprint 21: Procedure (Procedimentos Médicos)
    path('procedures/', views_procedure.manage_procedures, name='manage_procedures'),
    path('procedures/<str:procedure_id>/', views_procedure.procedure_detail, name='procedure_detail'),
    path('patients/<str:patient_id>/procedures/', views_procedure.patient_procedures, name='patient_procedures'),
    
    # Sprint 21: MedicationRequest Aprimorado (Prescrições)
    path('medication-requests/', views_medication.manage_medication_requests, name='manage_medication_requests'),
    path('medication-requests/<str:medication_request_id>/', views_medication.medication_request_detail, name='medication_request_detail'),
    path('patients/<str:patient_id>/medications/', views_medication.patient_medications, name='patient_medications'),
    
    # Sprint 21: HealthcareService (Serviços de Saúde)
    path('healthcare-services/', views_healthcare_service.manage_healthcare_services, name='manage_healthcare_services'),
    path('healthcare-services/<str:service_id>/', views_healthcare_service.healthcare_service_detail, name='healthcare_service_detail'),
    path('organizations/<str:organization_id>/services/', views_healthcare_service.organization_services, name='organization_services'),
    
    # Sprint 21: DiagnosticReport CRUD Completo (Laudos/Exames)
    path('diagnostic-reports-v2/', views_diagnostic_report.manage_diagnostic_reports, name='manage_diagnostic_reports_v2'),
    path('diagnostic-reports-v2/<str:report_id>/', views_diagnostic_report.diagnostic_report_detail, name='diagnostic_report_detail_v2'),
    
    # Sprint 22: Consent FHIR (LGPD Compliance)
    path('consents-v2/', views_consent_fhir.manage_consents, name='manage_consents_v2'),
    path('consents-v2/<str:consent_id>/', views_consent_fhir.consent_detail, name='consent_detail_v2'),
    path('patients/<str:patient_id>/consents/', views_consent_fhir.patient_consents, name='patient_consents'),
    path('patients/<str:patient_id>/consents/revoke-all/', views_consent_fhir.revoke_all_consents, name='revoke_all_consents'),
    
    # Sprint 22: AuditEvent (Security Logging)
    path('audit-events/', views_audit_event.list_audit_events, name='list_audit_events'),
    path('audit-events/<str:event_id>/', views_audit_event.audit_event_detail, name='audit_event_detail'),
    path('audit-events/security-report/', views_audit_event.security_report, name='security_report'),
    path('patients/<str:patient_id>/audit-trail/', views_audit_event.patient_audit_trail, name='patient_audit_trail'),
    
    # Sprint 21: Terminology Services (RxNorm, ICD-10, TUSS)
    # RxNorm (Medications)
    path('terminology/rxnorm/search/', views_terminology.search_rxnorm, name='search_rxnorm'),
    path('terminology/rxnorm/<str:rxcui>/', views_terminology.get_rxnorm_details, name='get_rxnorm_details'),
    path('terminology/rxnorm/<str:rxcui>/interactions/', views_terminology.get_rxnorm_interactions, name='get_rxnorm_interactions'),
    path('terminology/rxnorm/interactions/check/', views_terminology.check_multi_interactions, name='check_multi_interactions'),
    
    # ICD-10 (Diagnoses)
    path('terminology/icd10/search/', views_terminology.search_icd10, name='search_icd10'),
    path('terminology/icd10/<str:code>/', views_terminology.validate_icd10, name='validate_icd10'),
    
    # TUSS (Brazilian Procedures)
    path('terminology/tuss/search/', views_terminology.search_tuss, name='search_tuss'),
    path('terminology/tuss/<str:code>/', views_terminology.validate_tuss, name='validate_tuss'),
    path('terminology/tuss/type/<str:procedure_type>/', views_terminology.list_tuss_by_type, name='list_tuss_by_type'),
    
    # Terminology Mapping (ICD-10 <-> SNOMED CT)
    path('terminology/map/icd10-to-snomed/<str:icd10_code>/', views_terminology.map_icd10_to_snomed, name='map_icd10_to_snomed'),
    path('terminology/map/snomed-to-icd10/<str:snomed_code>/', views_terminology.map_snomed_to_icd10, name='map_snomed_to_icd10'),
    
    # Sprint 22: FHIR Bulk Data Export ($export)
    path('export/Patient/', views_bulk_data.export_patient, name='export_patient'),
    path('export/Group/<str:group_id>/', views_bulk_data.export_group, name='export_group'),
    path('export/System/', views_bulk_data.export_system, name='export_system'),
    path('export/status/<str:job_id>/', views_bulk_data.export_status, name='export_status'),
    path('export/jobs/', views_bulk_data.list_exports, name='list_exports'),
    path('export/files/<str:job_id>/<str:file_name>/', views_bulk_data.download_export_file, name='download_export_file'),
    
    # Sprint 22: FHIR Bulk Data Import ($import)
    path('import/', views_bulk_data.import_bulk, name='import_bulk'),
    path('import/status/<str:job_id>/', views_bulk_data.import_status, name='import_status'),
    
    # Sprint 22: SMART on FHIR OAuth2 Scopes
    path('smart/scopes/', views_bulk_data.list_smart_scopes, name='list_smart_scopes'),
    path('smart/scopes/validate/', views_bulk_data.validate_smart_scopes, name='validate_smart_scopes'),
    path('smart/access/check/', views_bulk_data.check_smart_access, name='check_smart_access'),
    
    # Sprint 24: LGPD Privacy Controls
    path('patients/<str:patient_id>/access-logs/', views_lgpd.patient_access_logs, name='patient_access_logs'),
    path('patients/<str:patient_id>/data-export/', views_lgpd.request_data_export, name='request_data_export'),
    path('patients/<str:patient_id>/data-export/preview/', views_lgpd.preview_data_export, name='preview_data_export'),
    path('patients/<str:patient_id>/data-deletion/', views_lgpd.request_data_deletion, name='request_data_deletion'),
    path('patients/<str:patient_id>/check-consent/', views_lgpd.check_patient_consent, name='check_patient_consent'),
    path('patients/<str:patient_id>/lgpd-report/', views_lgpd.patient_lgpd_report, name='patient_lgpd_report'),
    
    # Sprint 24: LGPD Request Management
    path('lgpd/log-access/', views_lgpd.log_data_access, name='log_data_access'),
    path('lgpd/requests/', views_lgpd.lgpd_requests, name='lgpd_requests'),
    path('lgpd/requests/<str:request_id>/', views_lgpd.lgpd_request_detail, name='lgpd_request_detail'),
    path('lgpd/dashboard/', views_lgpd.lgpd_dashboard, name='lgpd_dashboard'),
    
    # ================================================================
    # Sprint 25: Novos Módulos FHIR
    # ================================================================
    
    # CarePlan - Plano de Cuidados
    path('careplans/', views_careplan.manage_careplans, name='manage_careplans'),
    path('careplans/<str:careplan_id>/', views_careplan.careplan_detail, name='careplan_detail'),
    path('careplans/<str:careplan_id>/activities/', views_careplan.add_careplan_activity, name='add_careplan_activity'),
    path('patients/<str:patient_id>/careplans/', views_careplan.patient_careplans, name='patient_careplans'),
    path('goals/', views_careplan.manage_goals, name='manage_goals'),
    
    # Composition - Prontuário Estruturado
    path('compositions/', views_composition.manage_compositions, name='manage_compositions'),
    path('compositions/types/', views_composition.composition_types, name='composition_types'),
    path('compositions/<str:composition_id>/', views_composition.composition_detail, name='composition_detail'),
    path('patients/<str:patient_id>/compositions/', views_composition.patient_compositions, name='patient_compositions'),
    
    # ================================================================
    # Sprint 26: Conformidade Regulatória Brasil
    # ================================================================
    
    # TISS/ANS - Faturamento Operadoras
    path('tiss/tipos/', views_tiss.tiss_tipos_guia, name='tiss_tipos'),
    path('tiss/consulta/', views_tiss.gerar_guia_consulta, name='tiss_consulta'),
    path('tiss/sadt/', views_tiss.gerar_guia_sadt, name='tiss_sadt'),
    path('tiss/internacao/', views_tiss.gerar_guia_internacao, name='tiss_internacao'),
    path('tiss/lote/', views_tiss.gerar_lote_tiss, name='tiss_lote'),
    path('tiss/validar/', views_tiss.validar_guia_tiss, name='tiss_validar'),
    
    # RNDS - Rede Nacional de Dados em Saúde
    path('rnds/status/', views_rnds.rnds_status, name='rnds_status'),
    path('rnds/paciente/', views_rnds.consultar_paciente_rnds, name='rnds_paciente'),
    path('rnds/sumario/', views_rnds.enviar_sumario_rnds, name='rnds_sumario'),
    path('rnds/exame/', views_rnds.enviar_resultado_exame_rnds, name='rnds_exame'),
    path('rnds/imunizacao/', views_rnds.enviar_imunizacao_rnds, name='rnds_imunizacao'),
    path('rnds/vacinas/', views_rnds.consultar_vacinas_rnds, name='rnds_vacinas'),
    
    # ================================================================
    # Sprint 27: Integrações Externas
    # ================================================================
    
    # Laboratório
    path('lab/results/', views_integrations.receber_resultados_lab, name='lab_results'),
    path('lab/convert-hl7/', views_integrations.converter_hl7_para_fhir, name='lab_convert_hl7'),
    path('lab/diagnostic-report/', views_integrations.criar_diagnostic_report, name='lab_diagnostic_report'),
    
    # PACS / Imagens
    path('pacs/status/', views_integrations.pacs_status, name='pacs_status'),
    path('pacs/studies/', views_integrations.buscar_estudos_pacs, name='pacs_studies'),
    path('pacs/studies/<str:study_uid>/series/', views_integrations.obter_series_estudo, name='pacs_series'),
    path('pacs/studies/<str:study_uid>/viewer/', views_integrations.obter_viewer_url, name='pacs_viewer'),
    path('patients/<str:patient_id>/imaging/', views_integrations.estudos_paciente_pacs, name='patient_imaging'),
    
    # Farmácia
    path('pharmacy/process/', views_integrations.processar_prescricao_farmacia, name='pharmacy_process'),
    path('pharmacy/dispense/', views_integrations.criar_dispensacao, name='pharmacy_dispense'),
    path('pharmacy/dispense/<str:dispense_id>/deliver/', views_integrations.confirmar_entrega_medicamento, name='pharmacy_deliver'),
    path('pharmacy/dispense/<str:dispense_id>/return/', views_integrations.registrar_devolucao, name='pharmacy_return'),
    path('pharmacy/interactions/', views_integrations.verificar_interacoes, name='pharmacy_interactions'),
    path('pharmacy/report/', views_integrations.relatorio_consumo_farmacia, name='pharmacy_report'),
    
    # ================================================================
    # Sprint 28: Encaminhamentos e Comunicação
    # ================================================================
    
    # Encaminhamentos (ServiceRequest + Task)
    path('referrals/', views_referral.manage_referrals, name='referrals'),
    path('referrals/pending/', views_referral.pending_referrals, name='pending_referrals'),
    path('referrals/<str:referral_id>/', views_referral.referral_detail, name='referral_detail'),
    path('referrals/<str:referral_id>/accept/', views_referral.accept_referral, name='accept_referral'),
    path('referrals/<str:referral_id>/complete/', views_referral.complete_referral, name='complete_referral'),
    path('patients/<str:patient_id>/referrals/', views_referral.patient_referrals, name='patient_referrals'),
    
    # Comunicação entre profissionais
    path('communications/', views_communication.manage_communications, name='communications'),
    path('communications/request-opinion/', views_communication.request_opinion, name='request_opinion'),
    path('communications/<str:communication_id>/', views_communication.communication_detail, name='communication_detail'),
    path('communications/<str:communication_id>/reply/', views_communication.reply_communication, name='reply_communication'),
    path('practitioners/<str:practitioner_id>/inbox/', views_communication.inbox, name='practitioner_inbox'),
    path('practitioners/<str:practitioner_id>/sent/', views_communication.sent_messages, name='practitioner_sent'),
    path('patients/<str:patient_id>/communications/', views_communication.patient_communications, name='patient_communications'),
    
    # Notificações Compulsórias (SINAN)
    path('notifications/', views_notifications.manage_notifications, name='notifications'),
    path('notifications/conditions/', views_notifications.list_notifiable_conditions, name='notifiable_conditions'),
    path('notifications/pending/', views_notifications.pending_notifications, name='pending_notifications'),
    path('notifications/stats/', views_notifications.notification_stats, name='notification_stats'),
    path('notifications/check/', views_notifications.check_notifiable, name='check_notifiable'),
    path('notifications/<str:notification_id>/send/', views_notifications.send_to_sinan, name='send_to_sinan'),
    
    # ================================================================
    # CBO - Classificação Brasileira de Ocupações
    # ================================================================
    path('cbo/families/', views_cbo.listar_familias_cbo, name='cbo_families'),
    path('cbo/search/', views_cbo.buscar_ocupacoes_cbo, name='cbo_search'),
    path('cbo/validate/', views_cbo.validar_cbo, name='cbo_validate'),
    path('cbo/practitioner-qualification/', views_cbo.gerar_qualification_practitioner, name='cbo_qualification'),
    path('cbo/doctors/', views_cbo.listar_medicos_cbo, name='cbo_doctors'),
    path('cbo/nurses/', views_cbo.listar_enfermeiros_cbo, name='cbo_nurses'),
    path('cbo/dentists/', views_cbo.listar_dentistas_cbo, name='cbo_dentists'),
    path('cbo/nursing-technicians/', views_cbo.listar_tecnicos_enfermagem_cbo, name='cbo_nursing_technicians'),
    path('cbo/<str:codigo>/', views_cbo.detalhe_cbo, name='cbo_detail'),
]


urlpatterns += router.urls
