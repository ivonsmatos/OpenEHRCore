
# FHIR Implementation Guide - OpenEHRCore

## Overview

OpenEHRCore implements **FHIR R4** (HL7 FHIR Release 4) as its healthcare data standard.

## Server Information

| Property | Value |
|----------|-------|
| FHIR Version | R4 (4.0.1) |
| Server | HAPI FHIR v7.2.0 |
| Base URL | `/fhir/` |
| Formats | `application/fhir+json` |

## Supported Resources

### Clinical Resources

| Resource | CRUD | Search | Notes |
|----------|------|--------|-------|
| Patient | ✅ | ✅ | Core demographics |
| Practitioner | ✅ | ✅ | Healthcare providers |
| Observation | ✅ | ✅ | Vital signs, lab results |
| Condition | ✅ | ✅ | Diagnoses |
| AllergyIntolerance | ✅ | ✅ | Allergies |
| MedicationRequest | ✅ | ✅ | Prescriptions |
| Procedure | ✅ | ✅ | Medical procedures |
| DiagnosticReport | ✅ | ✅ | Lab/imaging reports |
| Encounter | ✅ | ✅ | Visits |
| Appointment | ✅ | ✅ | Scheduling |

### Administrative Resources

| Resource | CRUD | Search | Notes |
|----------|------|--------|-------|
| Organization | ✅ | ✅ | Healthcare facilities |
| Location | ✅ | ✅ | Rooms, beds |
| HealthcareService | ✅ | ✅ | Services offered |
| Coverage | ✅ | ✅ | Insurance |

### Security Resources

| Resource | CRUD | Search | Notes |
|----------|------|--------|-------|
| Consent | ✅ | ✅ | LGPD compliance |
| AuditEvent | ✅ | ✅ | Access logging |
| Provenance | ✅ | - | Data origin tracking |

## Terminology Bindings

### Supported Code Systems

| System | URI | Usage |
|--------|-----|-------|
| ICD-10 | `http://hl7.org/fhir/sid/icd-10` | Diagnoses |
| SNOMED CT | `http://snomed.info/sct` | Clinical terms |
| LOINC | `http://loinc.org` | Observations |
| RxNorm | `http://www.nlm.nih.gov/research/umls/rxnorm` | Medications |
| TUSS | `http://www.ans.gov.br/tuss` | Brazilian procedures |

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

| Extension | Usage |
|-----------|-------|
| CPF Identifier | Patient.identifier |
| CNES Organization | Organization.identifier |

## Validation

Resources are validated against FHIR R4 schemas via:

1. `fhirclient` Python library (typed models)
2. HAPI FHIR server validation
3. Custom validators in `/fhir_api/validators/`

## Conformance

This implementation aims to be compliant with:

- HL7 FHIR R4 Specification
- RNDS (Rede Nacional de Dados em Saúde) - Brazil
- LGPD (Lei Geral de Proteção de Dados) - Brazil
