from django.urls import path
from .views import (
    AnalyzeImageView, 
    TranscribeAudioView, 
    ParseClinicalNoteView,
    GetPatientSummaryView
)

urlpatterns = [
    # AI Vision - Image analysis with MedGemma
    path('ai/analyze-image/', AnalyzeImageView.as_view(), name='analyze-image'),
    
    # AI Voice - Transcription with Groq Whisper
    path('ai/transcribe/', TranscribeAudioView.as_view(), name='transcribe-audio'),
    
    # Clinical NLP - Parse note and create FHIR resources
    path('ai/parse-clinical-note/', ParseClinicalNoteView.as_view(), name='parse-clinical-note'),
    
    # AI Summary - Generate patient summary with Llama 3.3 70B
    path('ai/patient-summary/<str:patient_id>/', GetPatientSummaryView.as_view(), name='patient-summary'),
]
