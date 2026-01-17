from django.urls import path
from .views import AnalyzeImageView, TranscribeAudioView

urlpatterns = [
    path('ai/analyze-image/', AnalyzeImageView.as_view(), name='analyze-image'),
    path('ai/transcribe/', TranscribeAudioView.as_view(), name='transcribe-audio'),
]
