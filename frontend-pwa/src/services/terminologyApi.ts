/**
 * Sprint 21: Terminology API Service
 * 
 * Client-side service for interacting with the terminology API endpoints:
 * - RxNorm (Medications)
 * - ICD-10 (Diagnoses)
 * - TUSS (Brazilian Procedures)
 * - Terminology Mapping
 */

import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

// ============================================================================
// Types
// ============================================================================

export interface RxNormResult {
    rxcui: string;
    name: string;
    score: number;
    tty: string;
    synonym: string;
}

export interface RxNormDetails {
    rxcui: string;
    name: string;
    tty: string;
    synonym: string;
    language: string;
    active: boolean;
}

export interface DrugInteraction {
    source: string;
    severity: string;
    description: string;
    interacting_drug: string;
}

export interface MultiDrugInteraction {
    drug1: string;
    drug1_rxcui: string;
    drug2: string;
    drug2_rxcui: string;
    severity: string;
    description: string;
}

export interface ICD10Result {
    code: string;
    description: string;
    category: string;
    system: string;
}

export interface ICD10Validation {
    code: string;
    normalized?: string;
    description?: string;
    category?: string;
    valid: boolean;
    system?: string;
    error?: string;
}

export interface TUSSResult {
    code: string;
    description: string;
    type: string;
    category: string;
    system: string;
}

export interface TUSSValidation {
    code: string;
    description?: string;
    type?: string;
    category?: string;
    valid: boolean;
    system?: string;
    error?: string;
}

export interface TerminologyMapping {
    mapped: boolean;
    source_system?: string;
    source_code?: string;
    source_display?: string;
    target_system?: string;
    target_code?: string;
    target_display?: string;
    equivalence?: string;
    error?: string;
}

// ============================================================================
// RxNorm API
// ============================================================================

/**
 * Search RxNorm for medications by name.
 */
export async function searchRxNorm(query: string, maxResults: number = 20): Promise<RxNormResult[]> {
    const response = await axios.get(`${API_URL}/terminology/rxnorm/search/`, {
        params: { q: query, max: maxResults }
    });
    return response.data.results || [];
}

/**
 * Get detailed information for an RxNorm concept.
 */
export async function getRxNormDetails(rxcui: string): Promise<RxNormDetails | null> {
    try {
        const response = await axios.get(`${API_URL}/terminology/rxnorm/${rxcui}/`);
        return response.data;
    } catch {
        return null;
    }
}

/**
 * Get drug interactions for a single medication.
 */
export async function getRxNormInteractions(rxcui: string): Promise<DrugInteraction[]> {
    const response = await axios.get(`${API_URL}/terminology/rxnorm/${rxcui}/interactions/`);
    return response.data.interactions || [];
}

/**
 * Check interactions between multiple medications.
 */
export async function checkMultiDrugInteractions(rxcuis: string[]): Promise<{
    hasInteractions: boolean;
    interactions: MultiDrugInteraction[];
}> {
    const response = await axios.post(`${API_URL}/terminology/rxnorm/interactions/check/`, { rxcuis });
    return {
        hasInteractions: response.data.has_interactions || false,
        interactions: response.data.interactions || []
    };
}

// ============================================================================
// ICD-10 API
// ============================================================================

/**
 * Search ICD-10 codes by description or code.
 */
export async function searchICD10(query: string, maxResults: number = 20): Promise<ICD10Result[]> {
    const response = await axios.get(`${API_URL}/terminology/icd10/search/`, {
        params: { q: query, max: maxResults }
    });
    return response.data.results || [];
}

/**
 * Validate an ICD-10 code.
 */
export async function validateICD10(code: string): Promise<ICD10Validation> {
    try {
        const response = await axios.get(`${API_URL}/terminology/icd10/${code}/`);
        return response.data;
    } catch (error: unknown) {
        if (axios.isAxiosError(error) && error.response?.status === 404) {
            console.warn(`Recurso não encontrado: ${API_URL}/terminology/icd10/${code}/`); // Log de aviso para depuração
            return { code, valid: false, error: `Código CID-10 '${code}' não encontrado` };
        }
        throw error;
    }
}

// ============================================================================
// TUSS API
// ============================================================================

export type TUSSType = 'consulta' | 'exame' | 'imagem' | 'cirurgia' | 'terapia' | 'procedimento';

/**
 * Search TUSS codes by description or code.
 */
export async function searchTUSS(
    query: string,
    type?: TUSSType,
    maxResults: number = 20
): Promise<TUSSResult[]> {
    const response = await axios.get(`${API_URL}/terminology/tuss/search/`, {
        params: { q: query, type, max: maxResults }
    });
    return response.data.results || [];
}

/**
 * Validate a TUSS code.
 */
export async function validateTUSS(code: string): Promise<TUSSValidation> {
    try {
        const response = await axios.get(`${API_URL}/terminology/tuss/${code}/`);
        return response.data;
    } catch (error: unknown) {
        if (axios.isAxiosError(error) && error.response?.status === 404) {
            return { code, valid: false, error: `Código TUSS '${code}' não encontrado` };
        }
        throw error;
    }
}

/**
 * List TUSS codes by type.
 */
export async function listTUSSByType(type: TUSSType, maxResults: number = 50): Promise<TUSSResult[]> {
    const response = await axios.get(`${API_URL}/terminology/tuss/type/${type}/`, {
        params: { max: maxResults }
    });
    return response.data.results || [];
}

// ============================================================================
// Terminology Mapping API
// ============================================================================

/**
 * Map ICD-10 code to SNOMED CT.
 */
export async function mapICD10ToSNOMED(icd10Code: string): Promise<TerminologyMapping> {
    try {
        const response = await axios.get(`${API_URL}/terminology/map/icd10-to-snomed/${icd10Code}/`);
        return response.data;
    } catch (error: unknown) {
        if (axios.isAxiosError(error) && error.response?.status === 404) {
            return { mapped: false, error: `Nenhum mapeamento SNOMED CT encontrado para '${icd10Code}'` };
        }
        throw error;
    }
}

/**
 * Map SNOMED CT code to ICD-10.
 */
export async function mapSNOMEDToICD10(snomedCode: string): Promise<TerminologyMapping> {
    try {
        const response = await axios.get(`${API_URL}/terminology/map/snomed-to-icd10/${snomedCode}/`);
        return response.data;
    } catch (error: unknown) {
        if (axios.isAxiosError(error) && error.response?.status === 404) {
            return { mapped: false, error: `Nenhum mapeamento CID-10 encontrado para '${snomedCode}'` };
        }
        throw error;
    }
}

// ============================================================================
// Default Export
// ============================================================================

export default {
    // RxNorm
    searchRxNorm,
    getRxNormDetails,
    getRxNormInteractions,
    checkMultiDrugInteractions,

    // ICD-10
    searchICD10,
    validateICD10,

    // TUSS
    searchTUSS,
    validateTUSS,
    listTUSSByType,

    // Mapping
    mapICD10ToSNOMED,
    mapSNOMEDToICD10
};
