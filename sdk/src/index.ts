/**
 * @openehrcore/sdk - TypeScript SDK for OpenEHRCore FHIR API
 *
 * Sprint 33: TypeScript SDK + FHIRcast
 */

// Core exports
export { OpenEHRClient, type OpenEHRClientConfig } from './client';
export { FHIRClient, type FHIRClientConfig } from './fhir';
export { AuthClient, type AuthConfig, type TokenResponse } from './auth';

// Types
export * from './types';

// Utilities
export { buildSearchParams, formatFHIRDate } from './utils';
