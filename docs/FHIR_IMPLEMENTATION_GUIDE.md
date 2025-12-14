# FHIR Implementation Guide - OpenEHRCore

## Overview

OpenEHRCore implements **FHIR R4** (HL7 FHIR Release 4) as its healthcare data standard.

## Server Information

| Property     | Value                   |
| ------------ | ----------------------- |
| FHIR Version | R4 (4.0.1)              |
| Server       | HAPI FHIR v7.2.0        |
| Base URL     | `/fhir/`                |
| Formats      | `application/fhir+json` |

## Supported Resources

### Clinical Resources

| Resource              | CRUD | Search | Notes                                     |
| --------------------- | ---- | ------ | ----------------------------------------- |
| Patient               | ✅   | ✅     | Core demographics                         |
| Practitioner          | ✅   | ✅     | Healthcare providers                      |
| Observation           | ✅   | ✅     | Vital signs, lab results                  |
| Condition             | ✅   | ✅     | Diagnoses                                 |
| AllergyIntolerance    | ✅   | ✅     | Allergies                                 |
| MedicationRequest     | ✅   | ✅     | Prescriptions                             |
| Procedure             | ✅   | ✅     | Medical procedures                        |
| DiagnosticReport      | ✅   | ✅     | Lab/imaging reports                       |
| Encounter             | ✅   | ✅     | Visits                                    |
| Appointment           | ✅   | ✅     | Scheduling                                |
| **DocumentReference** | ✅   | ✅     | **Medical documents, attachments**        |
| **Bundle**            | ✅   | ✅     | **Atomic transactions, batch operations** |
| **CarePlan**          | ✅   | ✅     | **Care coordination, activities**         |

### Administrative Resources

| Resource          | CRUD | Search | Notes                 |
| ----------------- | ---- | ------ | --------------------- |
| Organization      | ✅   | ✅     | Healthcare facilities |
| Location          | ✅   | ✅     | Rooms, beds           |
| HealthcareService | ✅   | ✅     | Services offered      |
| Coverage          | ✅   | ✅     | Insurance             |

### Security Resources

| Resource   | CRUD | Search | Notes                |
| ---------- | ---- | ------ | -------------------- |
| Consent    | ✅   | ✅     | LGPD compliance      |
| AuditEvent | ✅   | ✅     | Access logging       |
| Provenance | ✅   | -      | Data origin tracking |

## Terminology Bindings

### Supported Code Systems

| System    | URI                                           | Usage                |
| --------- | --------------------------------------------- | -------------------- |
| ICD-10    | `http://hl7.org/fhir/sid/icd-10`              | Diagnoses            |
| SNOMED CT | `http://snomed.info/sct`                      | Clinical terms       |
| LOINC     | `http://loinc.org`                            | Observations         |
| RxNorm    | `http://www.nlm.nih.gov/research/umls/rxnorm` | Medications          |
| TUSS      | `http://www.ans.gov.br/tuss`                  | Brazilian procedures |

### Terminology API Endpoints

```
GET /api/v1/terminology/rxnorm/search/?q={term}
GET /api/v1/terminology/icd10/search/?q={term}
GET /api/v1/terminology/tuss/search/?q={term}
GET /api/v1/terminology/map/icd10-to-snomed/{code}/
```

## Authentication

OAuth2/OIDC via Keycloak:

```
POST /api/v1/auth/login/
Authorization: Bearer {access_token}
```

## Operations

### DocumentReference Operations

**Upload Document**

```http
POST /api/v1/documents/
Content-Type: multipart/form-data

{
  "type": "clinical-note",
  "subject": "patient-uuid",
  "encounter": "encounter-uuid",
  "file": <binary>
}
```

**Search Documents**

```http
GET /api/v1/documents/?patient={id}&type={type}&status={status}
GET /api/v1/documents/patient/{patient_id}/
```

**Download Document**

```http
GET /api/v1/documents/{id}/download/
Response: Binary file with audit logging
```

**Security Features:**

- ✅ RBAC permissions (CanViewPatientDocuments, CanCreateDocuments)
- ✅ Audit logging (created_by, created_at tracking)
- ✅ Secure file storage (media_root isolation)
- ✅ MIME type validation (PDF, DOCX, PNG, JPEG, DICOM)

---

### Bundle Operations

**Create Transaction Bundle**

```http
POST /api/v1/bundles/
Content-Type: application/fhir+json

{
  "resourceType": "Bundle",
  "type": "transaction",
  "entry": [
    {
      "request": {
        "method": "POST",
        "url": "Patient"
      },
      "resource": {
        "resourceType": "Patient",
        "name": [{"family": "Silva", "given": ["João"]}]
      }
    },
    {
      "request": {
        "method": "POST",
        "url": "Observation"
      },
      "resource": {
        "resourceType": "Observation",
        "subject": {"reference": "urn:uuid:patient-temp-id"}
      }
    }
  ]
}
```

**Process Bundle**

```http
POST /api/v1/bundles/{id}/process/
Response: Bundle with type "transaction-response" or "batch-response"
```

**Bundle Types:**

- `transaction`: ACID atomic operations (all-or-nothing)
- `batch`: Independent operations (continues on errors)
- `document`: Clinical document bundle
- `message`: Messaging bundle
- `collection`: Grouped resources

**Retry Failed Bundle**

```http
POST /api/v1/bundles/{id}/retry/
```

**Bundle Statistics**

```http
GET /api/v1/bundles/statistics/
Response: {
  "total": 150,
  "by_type": {"transaction": 80, "batch": 70},
  "by_status": {"completed": 120, "failed": 10, "pending": 20}
}
```

---

### CarePlan Operations

**Create Care Plan**

```http
POST /api/v1/careplans/
Content-Type: application/json

{
  "title": "Diabetes Management Plan",
  "description": "3-month diabetes control program",
  "status": "draft",
  "intent": "plan",
  "patient_id": "patient-uuid",
  "period_start": "2024-01-01",
  "categories": ["diabetes", "chronic-disease"],
  "goals": [
    {
      "description": "HbA1c < 7%",
      "target": {"measure": "HbA1c", "detailQuantity": {"value": 7, "unit": "%"}}
    }
  ]
}
```

**Activate Plan (draft → active)**

```http
POST /api/v1/careplans/{id}/activate/
Response: CarePlan with status="active", period_start updated
```

**Complete Plan (active → completed)**

```http
POST /api/v1/careplans/{id}/complete/
Request: {"notes": "Patient achieved all goals"}
Response: CarePlan with status="completed", period_end set
```

**Add Activity to Plan**

```http
POST /api/v1/careplans/{id}/activities/
Content-Type: application/json

{
  "status": "not-started",
  "kind": "Appointment",
  "code": {"text": "Endocrinologist consultation"},
  "scheduled_period_start": "2024-01-15T09:00:00Z",
  "performers": [{"display": "Dr. Silva"}]
}
```

**Start Activity (not-started → in-progress)**

```http
POST /api/v1/careplan-activities/{id}/start/
```

**Complete Activity (in-progress → completed)**

```http
POST /api/v1/careplan-activities/{id}/complete/
Request: {"progress": "Patient attended, labs ordered"}
```

**Get Patient's Care Plans**

```http
GET /api/v1/careplans/patient/{patient_id}/?status=active
```

**CarePlan Statistics**

```http
GET /api/v1/careplans/statistics/
Response: {
  "total": 45,
  "by_status": {"active": 20, "draft": 10, "completed": 15},
  "by_intent": {"plan": 35, "order": 10},
  "avg_activities_per_plan": 4.2
}
```

**Status Workflow:**

```
draft → active → on-hold → active → completed
              ↘ revoked
```

**Activity Kinds:**

- `Appointment`: Scheduled consultations
- `MedicationRequest`: Prescription orders
- `Task`: Generic care tasks
- `ServiceRequest`: Lab/imaging orders
- `Procedure`: Planned procedures
- `DiagnosticReport`: Expected results
- `Communication`: Patient education
- `NutritionOrder`: Dietary plans

---

### Bulk Data Export ($export)

```
POST /api/v1/bulk-data/export/
GET /api/v1/bulk-data/export/{job_id}/status/
GET /api/v1/bulk-data/export/{job_id}/download/
```

### Patient Everything

```
GET /api/v1/patients/{id}/?_include=*
```

## Extensions

### Brazilian Extensions

| Extension         | Usage                   |
| ----------------- | ----------------------- |
| CPF Identifier    | Patient.identifier      |
| CNES Organization | Organization.identifier |

---

## Resource Implementations Details

### DocumentReference

**Model Fields:**

- `identifier`: Unique document identifier (UUID)
- `status`: current | superseded | entered-in-error
- `doc_status`: preliminary | final | amended | corrected
- `type`: CodeableConcept (clinical-note, lab-report, imaging-report, discharge-summary, prescription, consent-form)
- `category`: CodeableConcept (clinical, administrative, financial)
- `subject`: FK to Patient (required)
- `date`: Document creation timestamp
- `author`: FK to Practitioner
- `authenticator`: FK to Practitioner (who verified)
- `custodian`: FK to Organization
- `description`: Human-readable summary
- `security_label`: Confidentiality level (normal, restricted, very-restricted)
- `context_encounter`: FK to Encounter
- `context_period_start/end`: Document context timeframe

**DocumentAttachment Model:**

- `document`: FK to DocumentReference
- `content_type`: MIME type (application/pdf, image/png, etc.)
- `language`: pt-BR, en-US
- `data`: Binary file field
- `url`: External document URL (alternative to data)
- `size`: File size in bytes
- `hash`: SHA-256 checksum
- `title`: Display name
- `creation`: File creation timestamp

**Permissions:**

- `CanViewPatientDocuments`: Read access to patient documents
- `CanCreateDocuments`: Upload and create documents
- Practitioners: see documents for patients under their care
- Patients: see only their own documents
- Admins: full access

**FHIR R4 Compliance:**

```json
{
  "resourceType": "DocumentReference",
  "id": "doc-123",
  "status": "current",
  "type": {
    "coding": [
      {
        "system": "http://loinc.org",
        "code": "34108-1",
        "display": "Outpatient Note"
      }
    ]
  },
  "subject": { "reference": "Patient/patient-uuid" },
  "date": "2024-01-15T10:30:00Z",
  "author": [{ "reference": "Practitioner/pract-uuid" }],
  "content": [
    {
      "attachment": {
        "contentType": "application/pdf",
        "url": "https://api.openehercore.com/media/documents/file.pdf",
        "size": 245678,
        "hash": "sha256-abc123...",
        "title": "Lab Results - Dec 2024"
      }
    }
  ]
}
```

---

### Bundle

**Model Fields:**

- `identifier`: Unique bundle identifier (UUID)
- `type`: document | message | transaction | transaction-response | batch | batch-response | history | searchset | collection
- `timestamp`: Bundle creation time
- `total`: Number of entries (for searchset/history)
- `signature`: Digital signature (JSON)
- `entries`: JSON array of bundle entries
- `status`: pending | processing | completed | failed
- `error_message`: Processing error details
- `created_by`: FK to User (audit)

**BundleEntry Model:**

- `bundle`: FK to Bundle
- `full_url`: Resource identifier (urn:uuid:xxx or absolute URL)
- `resource_type`: Patient, Observation, etc.
- `resource_id`: UUID of created resource
- `resource_json`: Full resource JSON
- `request_method`: POST, PUT, PATCH, DELETE, GET
- `request_url`: Relative URL (e.g., "Patient")
- `request_if_match`: ETag for conditional updates
- `request_if_none_match`: ETag for conditional creates
- `response_status`: HTTP status code (201, 200, 404, etc.)
- `response_location`: Created resource URL
- `response_etag`: Version identifier
- `response_outcome`: OperationOutcome JSON

**Bundle Processor:**

- **Transaction Mode**: @transaction.atomic decorator, rollback on ANY failure, ACID guarantees
- **Batch Mode**: Independent operations, continues on errors, each entry has individual outcome
- **Reference Resolution**: Converts `urn:uuid:temp-id` to real resource URLs after creation
- **Supported Operations**: POST (create), PUT (update), PATCH (partial update), DELETE (remove), GET (read)

**FHIR R4 Transaction Example:**

```json
{
  "resourceType": "Bundle",
  "type": "transaction",
  "entry": [
    {
      "fullUrl": "urn:uuid:patient-temp",
      "resource": {
        "resourceType": "Patient",
        "name": [{ "family": "Silva", "given": ["Maria"] }]
      },
      "request": {
        "method": "POST",
        "url": "Patient"
      }
    },
    {
      "resource": {
        "resourceType": "Observation",
        "status": "final",
        "code": {
          "coding": [
            {
              "system": "http://loinc.org",
              "code": "85354-9",
              "display": "Blood pressure"
            }
          ]
        },
        "subject": { "reference": "urn:uuid:patient-temp" },
        "valueQuantity": { "value": 120, "unit": "mmHg" }
      },
      "request": {
        "method": "POST",
        "url": "Observation"
      }
    }
  ]
}
```

**Transaction Response:**

```json
{
  "resourceType": "Bundle",
  "type": "transaction-response",
  "entry": [
    {
      "response": {
        "status": "201 Created",
        "location": "Patient/abc-123/_history/1",
        "etag": "W/\"1\""
      }
    },
    {
      "response": {
        "status": "201 Created",
        "location": "Observation/def-456/_history/1"
      }
    }
  ]
}
```

---

### CarePlan

**CarePlan Model Fields:**

- `identifier`: Unique plan identifier (UUID)
- `status`: draft | active | on-hold | revoked | completed | entered-in-error | unknown
- `intent`: proposal | plan | order | option
- `category`: ArrayField (assessment, education, chronic-disease, mental-health, end-of-life, medication, oncology, palliative)
- `title`: Plan name (max 200 chars)
- `description`: Detailed plan description
- `subject`: FK to Patient (required)
- `encounter`: FK to Encounter (optional)
- `period_start/end`: Plan active timeframe
- `created_at`: Timestamp
- `author`: FK to Practitioner
- `care_team`: FK to CareTeam
- `addresses`: JSON array of conditions/problems addressed
- `supporting_info`: JSON array of reference documents
- `goal`: JSON array of FHIR Goal structures
- `activity_count`: Computed field

**Status Transition Validation:**

- ✅ draft → active, on-hold, revoked
- ✅ active → on-hold, completed, revoked
- ✅ on-hold → active, revoked
- ❌ completed → ANY (immutable)
- ❌ revoked → ANY (immutable)

**CarePlanActivity Model Fields:**

- `care_plan`: FK to CarePlan (CASCADE delete)
- `status`: not-started | scheduled | in-progress | on-hold | completed | cancelled | stopped | unknown | entered-in-error
- `kind`: Appointment | CommunicationRequest | DeviceRequest | MedicationRequest | NutritionOrder | Task | ServiceRequest | VisionPrescription
- `code`: SNOMED CT code (JSON) - what activity is
- `reason_code`: CodeableConcept - why activity needed
- `reason_reference`: FK to Condition/Observation
- `goal`: JSON array - which goals this supports
- `description`: Human-readable activity summary
- `scheduled_timing`: Recurring schedule (JSON)
- `scheduled_period_start/end`: One-time scheduled period
- `scheduled_string`: Human-readable schedule
- `location`: FK to Location
- `performers`: JSON array of practitioners/organizations
- `product_code`: CodeableConcept for medication/device
- `daily_amount`: Quantity per day
- `quantity`: Total quantity
- `progress`: Text notes on progress
- `outcome_reference`: FK to resulting resource

**FHIR R4 CarePlan Example:**

```json
{
  "resourceType": "CarePlan",
  "id": "cp-123",
  "status": "active",
  "intent": "plan",
  "category": [
    {
      "coding": [
        {
          "system": "http://hl7.org/fhir/care-plan-category",
          "code": "chronic-disease",
          "display": "Chronic Disease Management"
        }
      ]
    }
  ],
  "title": "Hypertension Management Plan",
  "description": "6-month plan for blood pressure control",
  "subject": { "reference": "Patient/patient-uuid" },
  "period": {
    "start": "2024-01-01",
    "end": "2024-06-30"
  },
  "author": { "reference": "Practitioner/pract-uuid" },
  "goal": [
    {
      "description": { "text": "Blood pressure < 140/90 mmHg" },
      "target": {
        "measure": {
          "coding": [{ "system": "http://loinc.org", "code": "85354-9" }]
        },
        "detailQuantity": { "value": 140, "unit": "mmHg" }
      }
    }
  ],
  "activity": [
    {
      "detail": {
        "kind": "MedicationRequest",
        "code": {
          "coding": [
            {
              "system": "http://snomed.info/sct",
              "code": "396458002",
              "display": "Amlodipine"
            }
          ]
        },
        "status": "in-progress",
        "scheduledTiming": {
          "repeat": { "frequency": 1, "period": 1, "periodUnit": "d" }
        },
        "description": "Amlodipine 5mg once daily"
      }
    }
  ]
}
```

**Permission Matrix:**
| Role | View Plans | Create Plans | Activate | Complete | Add Activities |
|------|-----------|--------------|----------|----------|----------------|
| Admin | All | ✅ | ✅ | ✅ | ✅ |
| Practitioner | Authored + Patients under care | ✅ | ✅ (own) | ✅ (own) | ✅ (own) |
| Patient | Own only | ❌ | ❌ | ❌ | ❌ |

---

## Validation

Resources are validated against FHIR R4 schemas via:

1. `fhirclient` Python library (typed models)
2. HAPI FHIR server validation
3. Custom validators in `/fhir_api/validators/`

## Conformance

This implementation aims to be compliant with:

- HL7 FHIR R4 Specification (v4.0.1)
- RNDS (Rede Nacional de Dados em Saúde) - Brazil
- LGPD (Lei Geral de Proteção de Dados) - Brazil

### LGPD Compliance Features

**Data Protection Measures:**

- ✅ **Consent Management**: FHIR Consent resources track patient data sharing permissions
- ✅ **Audit Logging**: AuditEvent resources record all data access (who, when, what, why)
- ✅ **Data Minimization**: Role-based access control (RBAC) limits data exposure
- ✅ **Right to Access**: Patient portal provides full data download
- ✅ **Right to Erasure**: Soft delete with anonymization workflows
- ✅ **Data Portability**: FHIR JSON export for data portability
- ✅ **Security Labels**: DocumentReference.securityLabel for confidentiality levels
- ✅ **Encrypted Storage**: Files encrypted at rest (Django media storage)
- ✅ **Secure Transmission**: HTTPS/TLS 1.3 required for all API calls

**LGPD Data Categories:**

- **Sensitive Personal Data**: Health records flagged in Consent resources
- **Children's Data**: Age-based consent validation (< 18 requires guardian)
- **Special Categories**: Mental health, genetic data flagged with security labels

---

## API Endpoints Summary

### DocumentReference Endpoints (10)

```
GET    /api/v1/documents/                    # List documents
POST   /api/v1/documents/                    # Upload document
GET    /api/v1/documents/{id}/               # Get document metadata
PUT    /api/v1/documents/{id}/               # Update metadata
DELETE /api/v1/documents/{id}/               # Soft delete
GET    /api/v1/documents/{id}/download/      # Download file
GET    /api/v1/documents/{id}/attachments/   # List attachments
GET    /api/v1/documents/patient/{id}/       # Patient's documents
GET    /api/v1/documents/encounter/{id}/     # Encounter documents
GET    /api/v1/documents/statistics/         # Document stats (cached)
```

### Bundle Endpoints (8)

```
GET    /api/v1/bundles/                      # List bundles
POST   /api/v1/bundles/                      # Create bundle
GET    /api/v1/bundles/{id}/                 # Get bundle
DELETE /api/v1/bundles/{id}/                 # Delete bundle
POST   /api/v1/bundles/{id}/process/         # Execute transaction/batch
GET    /api/v1/bundles/{id}/entries/         # List bundle entries
POST   /api/v1/bundles/{id}/retry/           # Retry failed bundle
GET    /api/v1/bundles/statistics/           # Bundle stats (cached)
```

### CarePlan Endpoints (10)

```
GET    /api/v1/careplans/                    # List care plans
POST   /api/v1/careplans/                    # Create plan
GET    /api/v1/careplans/{id}/               # Get plan
PUT    /api/v1/careplans/{id}/               # Update plan
PATCH  /api/v1/careplans/{id}/               # Partial update
DELETE /api/v1/careplans/{id}/               # Delete plan
GET    /api/v1/careplans/patient/{id}/       # Patient's plans
POST   /api/v1/careplans/{id}/activate/      # draft → active
POST   /api/v1/careplans/{id}/complete/      # active → completed
GET    /api/v1/careplans/{id}/activities/    # List activities
POST   /api/v1/careplans/{id}/activities/    # Add activity
GET    /api/v1/careplans/statistics/         # Plan stats (cached)
```

### CarePlan Activity Endpoints (5)

```
GET    /api/v1/careplan-activities/          # List activities
PATCH  /api/v1/careplan-activities/{id}/     # Update activity
POST   /api/v1/careplan-activities/{id}/start/     # not-started → in-progress
POST   /api/v1/careplan-activities/{id}/complete/  # in-progress → completed
DELETE /api/v1/careplan-activities/{id}/     # Delete activity
```

**Total New Endpoints:** 33

---

## Performance & Caching

**Cached Endpoints (5 minutes):**

- `/api/v1/documents/statistics/`
- `/api/v1/bundles/statistics/`
- `/api/v1/careplans/statistics/`

**Database Indexes:**

- DocumentReference: (patient, date), (encounter, date), (type, status), (created_by, created_at)
- Bundle: (timestamp), (type, timestamp), (status), (created_by, timestamp)
- CarePlan: (patient, period_start), (status, period_start), (author, created_at)
- CarePlanActivity: (care_plan, status), (status, scheduled_period_start)

**Pagination:**

- Default: 50 results per page
- Max: 100 results per page
- Query params: `?page=2&page_size=50`

---

## Error Handling

**OperationOutcome Format:**

```json
{
  "resourceType": "OperationOutcome",
  "issue": [
    {
      "severity": "error",
      "code": "processing",
      "diagnostics": "Patient with ID patient-123 not found",
      "expression": ["Bundle.entry[0].resource.subject.reference"]
    }
  ]
}
```

**Common HTTP Status Codes:**

- `200 OK`: Successful GET/PUT/PATCH
- `201 Created`: Successful POST
- `204 No Content`: Successful DELETE
- `400 Bad Request`: Validation error
- `401 Unauthorized`: Missing/invalid token
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource doesn't exist
- `409 Conflict`: Version mismatch (ETag)
- `422 Unprocessable Entity`: Business logic error
- `500 Internal Server Error`: Server failure

---

## Testing

**Postman Collection:**

- Import from `/docs/postman/OpenEHRCore_FHIR.postman_collection.json`
- Includes all 33 endpoints with example requests
- Pre-configured JWT authentication

**Unit Tests:**

```bash
cd backend-django
python manage.py test fhir_api.tests.test_documents
python manage.py test fhir_api.tests.test_bundles
python manage.py test fhir_api.tests.test_careplans
```

**Integration Tests:**

```bash
pytest backend-django/fhir_api/tests/integration/
```

---

## Migration Guide

### From Previous Implementation

**DocumentReference Migration:**

```python
# Old: Function-based views
from .views_documents import upload_document

# New: ViewSet with 10 endpoints
from .views_documents import DocumentReferenceViewSet
```

**CarePlan Migration:**

```python
# Old: Basic care plan model
status = models.CharField(max_length=20)

# New: Validated workflow
STATUS_CHOICES = [('draft', 'Draft'), ('active', 'Active'), ...]
status = models.CharField(max_length=20, choices=STATUS_CHOICES)

def clean(self):
    # Prevents invalid status transitions
    if self.status in ['completed', 'revoked'] and self._state.adding is False:
        raise ValidationError("Cannot modify completed/revoked plans")
```

**Bundle Implementation:**

```python
# New feature - no previous equivalent
# Enables atomic multi-resource operations
bundle = Bundle.objects.create(type='transaction', ...)
result = bundle.process_transaction()  # ACID guarantees
```

---

## Changelog

### Sprint 34-35 (December 2024)

**Added:**

- ✅ **MedicationAdministration** resource (8 endpoints)
  - Registro de administração real de medicamentos (quem/quando/quanto)
  - Suporte a dosagem (dose, via, rate)
  - Workflow (in-progress → completed/stopped)
  - Integração com MedicationRequest
  - Estatísticas de completude
- ✅ **Task** resource genérico (12 endpoints)
  - Workflow completo (requested → accepted → in-progress → completed)
  - 12 estados de lifecycle
  - Atribuição de responsáveis (owner, requester)
  - Inputs e Outputs estruturados
  - Restrições de período e repetições
- ✅ **Goal** resource standalone (10 endpoints)
  - Objetivos terapêuticos independentes de CarePlan
  - Lifecycle status (9 estados: proposed → active → completed)
  - Achievement status (9 estados: improving, achieved, etc)
  - Targets mensuráveis (quantidade, range, boolean)
  - Tracking de progresso com datas
- ✅ **Media** resource (9 endpoints)
  - Upload de imagens clínicas (JPEG, PNG, WEBP)
  - Upload de vídeos (MP4, WEBM)
  - Upload de áudios (MP3, WAV, OGG)
  - Geração automática de thumbnails
  - Preview inline e download
  - Metadados (dimensões, tamanho, hash SHA-256)
  - Suporte a body site e modalidade

**Frontend Components:**

- ✅ **MediaViewer.tsx** (React + TypeScript)
  - Grid de thumbnails
  - Zoom in/out para imagens
  - Player de vídeo/áudio integrado
  - Filtros por tipo (image/video/audio)
  - Download de arquivos
  - Visualização de metadados
- ✅ **GoalTracker.tsx** (React + TypeScript)
  - Cards com progresso visual (LinearProgress)
  - Filtro de objetivos ativos
  - Ícones de status (improving, worsening, achieved)
  - Quick actions (ativar, marcar como alcançado)
  - Dialog com detalhes e targets

**Backend Infrastructure:**

- ✅ Migrations criadas para 5 novos models (MedicationAdministration, Task, Goal, GoalTarget, Media)
- ✅ URLs registradas no router do Django
- ✅ Permissions module criado (CanViewPatientDocuments, CanCreateDocuments, etc)
- ✅ Audit logging module criado
- ✅ Serializers com validação FHIR completa
- ✅ ViewSets com actions customizadas (complete, activate, achieve, etc)

**FHIR Compliance:**

- ✅ MedicationAdministration R4 (100% compliant)
- ✅ Task R4 (100% compliant)
- ✅ Goal R4 (100% compliant com targets)
- ✅ Media R4 (100% compliant)

---

### Sprint 33 (December 2024)

**Added:**

- ✅ DocumentReference resource (10 endpoints)
  - File upload with MIME validation (PDF, DOCX, PNG, JPEG, DICOM)
  - Secure download with audit logging
  - RBAC permissions (CanViewPatientDocuments, CanCreateDocuments)
  - Multi-attachment support per document
- ✅ Bundle resource (8 endpoints)
  - Transaction mode (ACID atomic operations)
  - Batch mode (independent operations)
  - Reference resolution (urn:uuid → real URLs)
  - Support for POST/PUT/PATCH/DELETE/GET operations
  - Retry mechanism for failed bundles
- ✅ CarePlan resource (10 endpoints + 5 activity endpoints)
  - Status workflow validation (draft → active → completed)
  - Activity tracking (9 status states, 8 kinds)
  - Patient-specific permissions
  - Multi-disciplinary care team support
  - Goal tracking with measurable targets

**Frontend Components:**

- ✅ DocumentManager.tsx (React + TypeScript)
  - Drag-and-drop upload
  - Document preview
  - Mobile-first responsive design
- ✅ CarePlanManager.tsx (React + TypeScript)
  - Master-detail layout
  - Activity timeline
  - Status filters
  - Workflow actions (activate, complete)

**Documentation:**

- ✅ FHIR_IMPLEMENTATION_GUIDE.md (updated)
- ✅ DOCUMENT_MANAGEMENT_GUIDE.md (technical documentation)
- ✅ DOCUMENT_QUICK_START.md (user guide)

---

## Support

For questions or issues:

- GitHub Issues: https://github.com/OpenEHRCore/issues
- Documentation: `/docs/`
- API Docs: `/api/docs/` (Swagger UI)

**Last Updated:** December 14, 2024
