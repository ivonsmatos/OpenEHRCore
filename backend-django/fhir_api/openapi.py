"""
OpenAPI/Swagger Documentation for HealthStack API

Provides comprehensive API documentation following OpenAPI 3.0 specification.
"""

from django.urls import path
from django.http import JsonResponse, HttpResponse
from django.views.decorators.cache import cache_page
import json


# OpenAPI 3.0 Schema
OPENAPI_SCHEMA = {
    "openapi": "3.0.3",
    "info": {
        "title": "HealthStack API",
        "description": """
# HealthStack - Healthcare Interoperability Platform

FHIR R4 Native API for healthcare data management.

## Features
- 110+ API endpoints
- FHIR R4 compliant
- Brazil integrations (RNDS, TISS, PIX)
- Real-time notifications
- AI-powered clinical decision support

## Authentication
All endpoints (except public ones) require JWT authentication via Keycloak.

```
Authorization: Bearer <access_token>
```

## Rate Limiting
- Default: 60 requests/minute
- Auth endpoints: 10 requests/minute
- Bulk operations: 5 requests/minute

## FHIR Resources Supported
- Patient, Practitioner, Organization
- Observation, Condition, Procedure
- Encounter, Appointment
- MedicationRequest, CarePlan
- DiagnosticReport, and more...
        """,
        "version": "2.0.0",
        "contact": {
            "name": "HealthStack Support",
            "email": "support@healthstack.io"
        },
        "license": {
            "name": "MIT",
            "url": "https://opensource.org/licenses/MIT"
        }
    },
    "servers": [
        {
            "url": "http://localhost:8000/api/v1",
            "description": "Development server"
        },
        {
            "url": "https://api.healthstack.io/api/v1",
            "description": "Production server"
        }
    ],
    "tags": [
        {"name": "Authentication", "description": "User authentication and authorization"},
        {"name": "Patients", "description": "Patient management (FHIR Patient resource)"},
        {"name": "Practitioners", "description": "Healthcare practitioners"},
        {"name": "Appointments", "description": "Appointment scheduling"},
        {"name": "Clinical", "description": "Clinical data (Observations, Conditions, etc.)"},
        {"name": "FHIR Operations", "description": "FHIR-specific operations ($validate, bulk)"},
        {"name": "Brazil Integrations", "description": "PIX, WhatsApp, RNDS, TISS"},
        {"name": "Agent", "description": "On-premise agent management"},
        {"name": "AI", "description": "AI-powered features"},
    ],
    "paths": {
        "/patients/": {
            "get": {
                "tags": ["Patients"],
                "summary": "List patients",
                "description": "Get a paginated list of patients with optional filtering.",
                "operationId": "listPatients",
                "parameters": [
                    {
                        "name": "search",
                        "in": "query",
                        "description": "Search by name or CPF",
                        "schema": {"type": "string"}
                    },
                    {
                        "name": "page",
                        "in": "query",
                        "description": "Page number",
                        "schema": {"type": "integer", "default": 1}
                    },
                    {
                        "name": "page_size",
                        "in": "query",
                        "description": "Items per page",
                        "schema": {"type": "integer", "default": 20}
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Successful response",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/PatientList"}
                            }
                        }
                    },
                    "401": {"description": "Unauthorized"},
                    "429": {"description": "Rate limit exceeded"}
                },
                "security": [{"bearerAuth": []}]
            },
            "post": {
                "tags": ["Patients"],
                "summary": "Create patient",
                "description": "Create a new FHIR Patient resource.",
                "operationId": "createPatient",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/PatientCreate"}
                        }
                    }
                },
                "responses": {
                    "201": {"description": "Patient created"},
                    "400": {"description": "Invalid input"},
                    "422": {"description": "Validation error"}
                },
                "security": [{"bearerAuth": []}]
            }
        },
        "/patients/{id}/": {
            "get": {
                "tags": ["Patients"],
                "summary": "Get patient",
                "operationId": "getPatient",
                "parameters": [
                    {
                        "name": "id",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"}
                    }
                ],
                "responses": {
                    "200": {"description": "Patient details"},
                    "404": {"description": "Patient not found"}
                },
                "security": [{"bearerAuth": []}]
            }
        },
        "/appointments/": {
            "get": {
                "tags": ["Appointments"],
                "summary": "List appointments",
                "operationId": "listAppointments",
                "parameters": [
                    {"name": "date", "in": "query", "schema": {"type": "string", "format": "date"}},
                    {"name": "practitioner_id", "in": "query", "schema": {"type": "string"}},
                    {"name": "status", "in": "query", "schema": {"type": "string"}}
                ],
                "responses": {
                    "200": {"description": "List of appointments"}
                },
                "security": [{"bearerAuth": []}]
            }
        },
        "/observations/": {
            "get": {
                "tags": ["Clinical"],
                "summary": "List observations",
                "description": "Get clinical observations (vital signs, lab results).",
                "operationId": "listObservations",
                "responses": {"200": {"description": "List of observations"}},
                "security": [{"bearerAuth": []}]
            }
        },
        "/fhir/validate": {
            "post": {
                "tags": ["FHIR Operations"],
                "summary": "Validate FHIR resource",
                "description": "Validate a FHIR resource using HAPI FHIR $validate operation.",
                "operationId": "validateResource",
                "requestBody": {
                    "required": True,
                    "content": {"application/fhir+json": {"schema": {"type": "object"}}}
                },
                "responses": {
                    "200": {"description": "Validation result"},
                    "422": {"description": "Invalid resource"}
                },
                "security": [{"bearerAuth": []}]
            }
        },
        "/pix/payments/create/": {
            "post": {
                "tags": ["Brazil Integrations"],
                "summary": "Create PIX payment",
                "description": "Generate a PIX QR Code for payment.",
                "operationId": "createPixPayment",
                "responses": {"201": {"description": "PIX payment created"}},
                "security": [{"bearerAuth": []}]
            }
        },
        "/whatsapp/send/": {
            "post": {
                "tags": ["Brazil Integrations"],
                "summary": "Send WhatsApp message",
                "description": "Send a message via WhatsApp Business API.",
                "operationId": "sendWhatsApp",
                "responses": {"200": {"description": "Message sent"}},
                "security": [{"bearerAuth": []}]
            }
        },
        "/agent/register": {
            "post": {
                "tags": ["Agent"],
                "summary": "Register on-premise agent",
                "description": "Register a new on-premise HL7/DICOM agent.",
                "operationId": "registerAgent",
                "responses": {"201": {"description": "Agent registered"}},
                "security": [{"bearerAuth": []}]
            }
        },
        "/ai/summarize": {
            "post": {
                "tags": ["AI"],
                "summary": "Summarize clinical notes",
                "description": "Use AI to summarize clinical notes.",
                "operationId": "summarizeNotes",
                "responses": {"200": {"description": "Summary generated"}},
                "security": [{"bearerAuth": []}]
            }
        }
    },
    "components": {
        "schemas": {
            "PatientList": {
                "type": "object",
                "properties": {
                    "count": {"type": "integer"},
                    "next": {"type": "string", "nullable": True},
                    "previous": {"type": "string", "nullable": True},
                    "results": {
                        "type": "array",
                        "items": {"$ref": "#/components/schemas/Patient"}
                    }
                }
            },
            "Patient": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "resourceType": {"type": "string", "default": "Patient"},
                    "name": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "family": {"type": "string"},
                                "given": {"type": "array", "items": {"type": "string"}}
                            }
                        }
                    },
                    "gender": {"type": "string", "enum": ["male", "female", "other", "unknown"]},
                    "birthDate": {"type": "string", "format": "date"},
                    "identifier": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "system": {"type": "string"},
                                "value": {"type": "string"}
                            }
                        }
                    }
                }
            },
            "PatientCreate": {
                "type": "object",
                "required": ["name"],
                "properties": {
                    "name": {"type": "string", "description": "Full name"},
                    "cpf": {"type": "string", "description": "Brazilian CPF"},
                    "birthDate": {"type": "string", "format": "date"},
                    "gender": {"type": "string"}
                }
            },
            "Error": {
                "type": "object",
                "properties": {
                    "error": {"type": "string"},
                    "message": {"type": "string"},
                    "details": {"type": "object"}
                }
            }
        },
        "securitySchemes": {
            "bearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT"
            }
        }
    }
}


def openapi_schema(request):
    """Return OpenAPI 3.0 schema as JSON."""
    return JsonResponse(OPENAPI_SCHEMA)


def swagger_ui(request):
    """Return Swagger UI HTML page."""
    html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HealthStack API Documentation</title>
    <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui.css">
    <style>
        body { margin: 0; background: #1a1a2e; }
        .swagger-ui .topbar { display: none; }
        .swagger-ui { background: white; }
    </style>
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui-bundle.js"></script>
    <script>
        window.onload = function() {
            SwaggerUIBundle({
                url: "/api/v1/docs/openapi.json",
                dom_id: '#swagger-ui',
                deepLinking: true,
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIBundle.SwaggerUIStandalonePreset
                ],
                layout: "StandaloneLayout",
                persistAuthorization: true
            });
        };
    </script>
</body>
</html>
    """
    return HttpResponse(html, content_type='text/html')


def redoc(request):
    """Return ReDoc HTML page."""
    html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HealthStack API Documentation</title>
    <link href="https://fonts.googleapis.com/css?family=Montserrat:300,400,700|Roboto:300,400,700" rel="stylesheet">
    <style>
        body { margin: 0; padding: 0; }
    </style>
</head>
<body>
    <redoc spec-url="/api/v1/docs/openapi.json"></redoc>
    <script src="https://cdn.redoc.ly/redoc/latest/bundles/redoc.standalone.js"></script>
</body>
</html>
    """
    return HttpResponse(html, content_type='text/html')


# URL patterns for documentation
urlpatterns = [
    path('openapi.json', openapi_schema, name='openapi_schema'),
    path('swagger/', swagger_ui, name='swagger_ui'),
    path('redoc/', redoc, name='redoc'),
]
