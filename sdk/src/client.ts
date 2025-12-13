/**
 * OpenEHRCore Client - Main entry point
 *
 * Unified client that combines FHIR and Auth functionality
 */

import { FHIRClient, type FHIRClientConfig } from './fhir';
import { AuthClient, type AuthConfig, type TokenResponse } from './auth';
import type { Patient, Observation, Bundle, SearchParams } from './types';

export interface OpenEHRClientConfig {
    baseUrl: string;
    clientId?: string;
    clientSecret?: string;
    redirectUri?: string;
    scopes?: string[];
    accessToken?: string;
}

export class OpenEHRClient {
    public readonly fhir: FHIRClient;
    public readonly auth: AuthClient | null;
    private config: OpenEHRClientConfig;

    constructor(config: OpenEHRClientConfig) {
        this.config = config;

        // Initialize FHIR client
        this.fhir = new FHIRClient({
            baseUrl: config.baseUrl,
            accessToken: config.accessToken,
        });

        // Initialize Auth client if OAuth config provided
        if (config.clientId && config.redirectUri) {
            this.auth = new AuthClient({
                baseUrl: config.baseUrl,
                clientId: config.clientId,
                clientSecret: config.clientSecret,
                redirectUri: config.redirectUri,
                scopes: config.scopes,
            });
        } else {
            this.auth = null;
        }
    }

    /**
     * Set access token for API calls
     */
    setAccessToken(token: string): void {
        this.config.accessToken = token;
        this.fhir.setAccessToken(token);
    }

    // ============================================================================
    // Patient Helpers
    // ============================================================================

    /**
     * Get patient by ID
     */
    async getPatient(id: string): Promise<Patient> {
        return this.fhir.read<Patient>('Patient', id);
    }

    /**
     * Search patients
     */
    async searchPatients(params?: {
        name?: string;
        identifier?: string;
        birthdate?: string;
        gender?: string;
        _count?: number;
    }): Promise<Patient[]> {
        const bundle = await this.fhir.search<Patient>('Patient', params as SearchParams);
        return FHIRClient.extractResources(bundle);
    }

    /**
     * Create a new patient
     */
    async createPatient(patient: Omit<Patient, 'resourceType'>): Promise<Patient> {
        return this.fhir.create('Patient', { resourceType: 'Patient', ...patient });
    }

    /**
     * Update a patient
     */
    async updatePatient(id: string, patient: Patient): Promise<Patient> {
        return this.fhir.update('Patient', id, patient);
    }

    // ============================================================================
    // Observation Helpers
    // ============================================================================

    /**
     * Get observations for a patient
     */
    async getPatientObservations(
        patientId: string,
        params?: {
            category?: string;
            code?: string;
            date?: string;
            _count?: number;
            _sort?: string;
        }
    ): Promise<Observation[]> {
        const searchParams: SearchParams = {
            subject: `Patient/${patientId}`,
            ...params,
        };
        const bundle = await this.fhir.search<Observation>('Observation', searchParams);
        return FHIRClient.extractResources(bundle);
    }

    /**
     * Get vital signs for a patient
     */
    async getVitalSigns(patientId: string, limit = 20): Promise<Observation[]> {
        return this.getPatientObservations(patientId, {
            category: 'vital-signs',
            _count: limit,
            _sort: '-date',
        });
    }

    /**
     * Get lab results for a patient
     */
    async getLabResults(patientId: string, limit = 20): Promise<Observation[]> {
        return this.getPatientObservations(patientId, {
            category: 'laboratory',
            _count: limit,
            _sort: '-date',
        });
    }

    /**
     * Create an observation
     */
    async createObservation(observation: Omit<Observation, 'resourceType'>): Promise<Observation> {
        return this.fhir.create('Observation', { resourceType: 'Observation', ...observation });
    }

    // ============================================================================
    // Patient Portal Helpers
    // ============================================================================

    /**
     * Get patient summary (all relevant data)
     */
    async getPatientSummary(patientId: string): Promise<{
        patient: Patient;
        observations: Observation[];
        conditions: unknown[];
        medications: unknown[];
    }> {
        const [patient, observations, conditions, medications] = await Promise.all([
            this.getPatient(patientId),
            this.getPatientObservations(patientId, { _count: 50, _sort: '-date' }),
            this.fhir.search('Condition', { subject: `Patient/${patientId}` }),
            this.fhir.search('MedicationRequest', { subject: `Patient/${patientId}` }),
        ]);

        return {
            patient,
            observations,
            conditions: FHIRClient.extractResources(conditions),
            medications: FHIRClient.extractResources(medications),
        };
    }

    // ============================================================================
    // AI Features
    // ============================================================================

    /**
     * Get AI-generated patient summary
     */
    async getAIPatientSummary(patientId: string): Promise<{ summary: string; suggestions: string[] }> {
        const response = await this.fhir['httpClient'].post(`/ai/patients/${patientId}/summary/`);
        return response.data;
    }

    /**
     * Check drug interactions
     */
    async checkDrugInteractions(medications: string[]): Promise<{ interactions: unknown[] }> {
        const response = await this.fhir['httpClient'].post('/ai/drug-interactions/', { medications });
        return response.data;
    }

    // ============================================================================
    // Prescription Features
    // ============================================================================

    /**
     * Search for drugs
     */
    async searchDrugs(query: string): Promise<unknown[]> {
        const response = await this.fhir['httpClient'].get('/prescriptions/drugs/', { params: { q: query } });
        return response.data.results;
    }

    /**
     * Create a prescription
     */
    async createPrescription(data: {
        patient_id: string;
        items: Array<{
            drug_code: string;
            dosage: string;
            frequency: string;
            duration: string;
            quantity: number;
        }>;
        notes?: string;
    }): Promise<unknown> {
        const response = await this.fhir['httpClient'].post('/prescriptions/', data);
        return response.data;
    }
}
