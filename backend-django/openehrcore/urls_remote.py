"""
URL configuration for openehrcore project.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('fhir_api.urls')),
]
