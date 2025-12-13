# @openehrcore/sdk

TypeScript SDK for OpenEHRCore FHIR API.

## Installation

```bash
npm install @openehrcore/sdk
```

## Quick Start

```typescript
import { OpenEHRClient } from '@openehrcore/sdk';

// Initialize client
const client = new OpenEHRClient({
  baseUrl: 'http://localhost:8000/api/v1',
  accessToken: 'your-access-token',
});

// Get a patient
const patient = await client.getPatient('patient-123');

// Search patients
const patients = await client.searchPatients({ name: 'Silva' });

// Get vital signs
const vitals = await client.getVitalSigns('patient-123');

// Get lab results
const labs = await client.getLabResults('patient-123');
```

## SMART on FHIR Authentication

```typescript
import { AuthClient } from '@openehrcore/sdk';

const auth = new AuthClient({
  baseUrl: 'http://localhost:8000/api/v1',
  clientId: 'my-app',
  redirectUri: 'http://localhost:3000/callback',
  scopes: ['openid', 'fhirUser', 'patient/*.read'],
});

// Generate PKCE
const { verifier, challenge } = AuthClient.generatePKCE();

// Get authorization URL
const authUrl = auth.getAuthorizationUrl('random-state', challenge);

// After redirect, exchange code for tokens
const tokens = await auth.exchangeCode(code, verifier);
```

## Direct FHIR Operations

```typescript
import { FHIRClient } from '@openehrcore/sdk';

const fhir = new FHIRClient({
  baseUrl: 'http://localhost:8000/api/v1',
  accessToken: 'token',
});

// Create a resource
const patient = await fhir.create('Patient', {
  resourceType: 'Patient',
  name: [{ family: 'Silva', given: ['João'] }],
  gender: 'male',
});

// Search resources
const bundle = await fhir.search('Observation', {
  subject: 'Patient/123',
  category: 'vital-signs',
  _count: 10,
});

// Update a resource
await fhir.update('Patient', patient.id, {
  ...patient,
  active: true,
});

// Delete a resource
await fhir.delete('Patient', 'patient-id');
```

## Utility Functions

```typescript
import { 
  formatFHIRDate, 
  createReference, 
  getPatientName,
  calculateAge,
  isValidCPF 
} from '@openehrcore/sdk';

// Format date for FHIR
const date = formatFHIRDate(new Date()); // '2024-12-13'

// Create a FHIR reference
const ref = createReference('Patient', '123', 'João Silva');
// { reference: 'Patient/123', display: 'João Silva' }

// Get patient name from HumanName array
const name = getPatientName(patient.name); // 'João Silva'

// Calculate age from birthDate
const age = calculateAge('1990-05-15'); // 34

// Validate Brazilian CPF
const valid = isValidCPF('123.456.789-00'); // false
```

## API Reference

### OpenEHRClient

Main client with high-level helpers.

| Method | Description |
|--------|-------------|
| `getPatient(id)` | Get patient by ID |
| `searchPatients(params)` | Search patients |
| `createPatient(patient)` | Create new patient |
| `getVitalSigns(patientId)` | Get vital signs |
| `getLabResults(patientId)` | Get lab results |
| `getPatientSummary(patientId)` | Get full summary |
| `searchDrugs(query)` | Search drug database |
| `createPrescription(data)` | Create prescription |

### FHIRClient

Generic FHIR R4 client.

| Method | Description |
|--------|-------------|
| `read(resourceType, id)` | Read resource by ID |
| `search(resourceType, params)` | Search resources |
| `create(resourceType, resource)` | Create resource |
| `update(resourceType, id, resource)` | Update resource |
| `delete(resourceType, id)` | Delete resource |
| `history(resourceType, id?)` | Get history |
| `operation(resourceType, name, params, id?)` | Execute operation |

### AuthClient

OAuth2/SMART on FHIR authentication.

| Method | Description |
|--------|-------------|
| `getAuthorizationUrl(state, challenge?)` | Get auth URL |
| `exchangeCode(code, verifier?)` | Exchange code for tokens |
| `refreshToken(token)` | Refresh access token |
| `introspectToken(token)` | Introspect token |
| `revokeToken(token)` | Revoke token |

## License

MIT
