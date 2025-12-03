from django.urls import path
from . import views
from . import views_auth

urlpatterns = [
    # Health check (público)
    path('health/', views.health_check, name='health_check'),
    
    # Autenticação
    path('auth/login/', views_auth.login, name='login'),
    
    # Patient endpoints (protegidos com auth)
    path('patients/', views_auth.create_patient, name='create_patient'),
    path('patients/<str:patient_id>/', views_auth.get_patient, name='get_patient'),
    
    # Encounter endpoints (protegidos com auth)
    path('encounters/', views_auth.create_encounter, name='create_encounter'),
    
    # Observation endpoints (protegidos com auth)
    path('observations/', views_auth.create_observation, name='create_observation'),
]
