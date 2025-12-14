"""
URL configuration for openehrcore project.
"""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods

@require_http_methods(["GET"])
def api_root(request):
    """API root endpoint with service information."""
    return JsonResponse({
        'name': 'OpenEHR Core FHIR API',
        'version': '1.0.0',
        'fhir_version': 'R4',
        'status': 'active',
        'endpoints': {
            'admin': '/admin/',
            'api': '/api/v1/',
            'fhir': '/api/v1/fhir/',
        },
        'documentation': '/api/v1/schema/',
    })

@require_http_methods(["GET"])
def favicon_view(request):
    """Return empty favicon to prevent 404 errors."""
    return HttpResponse(
        (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
            '<text y=".9em" font-size="90">🏥</text>'
            '</svg>'
        ),
        content_type='image/svg+xml',
    )

urlpatterns = [
    path('', api_root, name='api-root'),
    path('favicon.ico', favicon_view, name='favicon'),
    path('admin/', admin.site.urls),
    path('api/v1/', include('fhir_api.urls')),
]
