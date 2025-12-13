# OpenEHRCore API Documentation

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

All endpoints require Bearer token authentication via Keycloak:

```http
Authorization: Bearer <access_token>
```

For development, use `Bearer dev-token-bypass`.

---

## 🏥 Core FHIR Resources

### Patients

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/patients/search/` | Search patients |
| GET | `/patients/{id}/` | Get patient by ID |
| POST | `/patients/` | Create patient |
| PUT | `/patients/{id}/` | Update patient |
| DELETE | `/patients/{id}/` | Delete patient |

**Search Parameters:**

- `name` - Patient name (partial match)
- `identifier` - CPF or CNS
- `birthdate` - Date of birth
- `gender` - male/female
- `_count` - Results per page (default: 10)
- `_offset` - Pagination offset

---

### Observations (Vital Signs & Labs)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/observations/?subject=Patient/{id}` | Get observations |
| POST | `/observations/` | Create observation |

**Query Parameters:**

- `subject` - Patient reference
- `category` - vital-signs / laboratory
- `code` - LOINC code
- `_sort` - Sort order (e.g., `-date`)

---

## 💊 e-Prescribing (Sprint 31)

### Drug Search

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/prescriptions/drugs/` | Search drugs |
| GET | `/prescriptions/drugs/{code}/` | Get drug details |
| POST | `/prescriptions/drugs/{code}/validate/` | Validate controlled drug |

**Example:**

```http
GET /api/v1/prescriptions/drugs/?q=amoxicilina
```

**Response:**

```json
{
  "count": 1,
  "results": [{
    "code": "1001",
    "name": "Amoxicilina 500mg",
    "presentation": "Cápsulas",
    "class": "Antibiótico",
    "controlled": false
  }]
}
```

### Prescriptions

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/prescriptions/` | Create prescription |
| POST | `/prescriptions/{id}/sign/` | Sign prescription |
| GET | `/patients/{id}/prescriptions/` | Patient prescriptions |

**Create Prescription:**

```http
POST /api/v1/prescriptions/
Content-Type: application/json

{
  "patient_id": "patient-123",
  "items": [{
    "drug_code": "1001",
    "dosage": "500mg",
    "frequency": "3x/dia",
    "duration": "7 dias",
    "quantity": 21
  }],
  "notes": "Tomar após refeições"
}
```

---

## 🔐 SMART on FHIR (Sprint 32)

### Configuration

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/.well-known/smart-configuration` | SMART config |
| GET | `/metadata` | Capability statement |
| GET | `/smart/scopes/` | Available scopes |

### OAuth2 Flow

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/smart/authorize` | Authorization endpoint |
| POST | `/smart/token` | Token endpoint |
| POST | `/smart/introspect` | Token introspection |
| POST | `/smart/revoke` | Token revocation |
| POST | `/smart/launch` | EHR launch context |

**Authorization Request:**

```http
GET /api/v1/smart/authorize?
  response_type=code&
  client_id=my-app&
  redirect_uri=http://localhost:3000/callback&
  scope=openid%20patient/*.read&
  state=random-state
```

**Token Exchange:**

```http
POST /api/v1/smart/token
Content-Type: application/json

{
  "grant_type": "authorization_code",
  "code": "auth-code",
  "client_id": "my-app",
  "redirect_uri": "http://localhost:3000/callback"
}
```

### Supported Scopes

| Scope | Description |
|-------|-------------|
| `patient/*.read` | Read all patient data |
| `patient/*.write` | Write all patient data |
| `user/*.read` | User-level read access |
| `launch/patient` | Get patient context |
| `launch/encounter` | Get encounter context |
| `openid` | OpenID Connect |
| `fhirUser` | FHIR user resource |
| `offline_access` | Refresh token |

---

## 📡 FHIRcast (Sprint 34)

Real-time clinical context synchronization.

### Configuration

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/.well-known/fhircast-configuration` | FHIRcast config |
| GET | `/fhircast/events` | Supported event types |

### Sessions & Subscriptions

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/fhircast/session` | Create session |
| POST | `/fhircast/subscribe` | Subscribe to topic |
| POST | `/fhircast/unsubscribe` | Unsubscribe |

**Create Session:**

```http
POST /api/v1/fhircast/session
Content-Type: application/json

{
  "context": {"patient": "123"}
}
```

**Response:**

```json
{
  "session_id": "abc-123",
  "hub.url": "/api/v1/fhircast/hub",
  "hub.topic": "fhircast/abc-123"
}
```

### Event Operations

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/fhircast/{topic}` | Get current context |
| POST | `/fhircast/{topic}/publish` | Publish event |
| GET | `/fhircast/{topic}/history` | Event history |
| GET | `/fhircast/{topic}/subscribers` | List subscribers |

**Publish Event:**

```http
POST /api/v1/fhircast/abc-123/publish
Content-Type: application/json

{
  "hub.event": "Patient-open",
  "context": {
    "resourceType": "Patient",
    "id": "patient-456",
    "name": [{"family": "Silva"}]
  }
}
```

### Supported Events

| Event | Description |
|-------|-------------|
| `Patient-open` | Patient context opened |
| `Patient-close` | Patient context closed |
| `Encounter-open` | Encounter opened |
| `Encounter-close` | Encounter closed |
| `ImagingStudy-open` | Imaging study opened |
| `DiagnosticReport-open` | Report opened |
| `UserLogout` | User logged out |
| `SyncError` | Sync error |

---

## 🤖 AI Features (Sprint 27)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/ai/patients/{id}/summary/` | AI patient summary |
| POST | `/ai/icd-suggestions/` | ICD code suggestions |
| POST | `/ai/drug-interactions/` | Drug interactions |
| POST | `/ai/chat/` | AI chat assistant |
| POST | `/ai/clinical-note/` | Generate clinical note |

---

## ⚡ Automation & Bots (Sprint 29)

### Subscriptions

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/subscriptions/` | List subscriptions |
| POST | `/subscriptions/` | Create subscription |
| DELETE | `/subscriptions/{id}/` | Delete subscription |

### Bots

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/bots/` | List bots |
| POST | `/bots/` | Create bot |
| POST | `/bots/{id}/execute/` | Execute bot |
| GET | `/bots/{id}/history/` | Bot history |

---

## 💰 Billing (Sprint 30)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/billing/coverage/` | List coverages |
| POST | `/billing/coverage/` | Create coverage |
| GET | `/billing/claims/` | List claims |
| POST | `/billing/claims/` | Create claim |
| POST | `/billing/claims/{id}/submit/` | Submit claim |
| GET | `/billing/dashboard/` | Billing metrics |

---

## Error Responses

```json
{
  "error": "error_code",
  "error_description": "Human readable message"
}
```

| HTTP Code | Meaning |
|-----------|---------|
| 400 | Bad request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not found |
| 500 | Server error |
