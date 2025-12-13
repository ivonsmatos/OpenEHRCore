/**
 * Utility functions for HealthStack SDK
 */

import type { SearchParams } from './types';

/**
 * Build URL search parameters from SearchParams object
 */
export function buildSearchParams(params: SearchParams): URLSearchParams {
    const searchParams = new URLSearchParams();

    for (const [key, value] of Object.entries(params)) {
        if (value !== undefined && value !== null) {
            searchParams.set(key, String(value));
        }
    }

    return searchParams;
}

/**
 * Format a JavaScript Date to FHIR date format (YYYY-MM-DD)
 */
export function formatFHIRDate(date: Date): string {
    return date.toISOString().split('T')[0];
}

/**
 * Format a JavaScript Date to FHIR datetime format
 */
export function formatFHIRDateTime(date: Date): string {
    return date.toISOString();
}

/**
 * Parse a FHIR date string to JavaScript Date
 */
export function parseFHIRDate(dateString: string): Date {
    return new Date(dateString);
}

/**
 * Create a FHIR Reference from resourceType and id
 */
export function createReference(resourceType: string, id: string, display?: string) {
    return {
        reference: `${resourceType}/${id}`,
        ...(display && { display }),
    };
}

/**
 * Extract resourceType and id from a FHIR reference string
 */
export function parseReference(reference: string): { resourceType: string; id: string } | null {
    const match = reference.match(/^(\w+)\/(.+)$/);
    if (match) {
        return { resourceType: match[1], id: match[2] };
    }
    return null;
}

/**
 * Check if a resource has a specific profile
 */
export function hasProfile(resource: { meta?: { profile?: string[] } }, profileUrl: string): boolean {
    return resource.meta?.profile?.includes(profileUrl) ?? false;
}

/**
 * Get the first value from a CodeableConcept
 */
export function getCodeableConceptCode(codeableConcept?: {
    coding?: Array<{ code?: string; system?: string }>;
}): string | undefined {
    return codeableConcept?.coding?.[0]?.code;
}

/**
 * Get display text from a CodeableConcept
 */
export function getCodeableConceptDisplay(codeableConcept?: {
    text?: string;
    coding?: Array<{ display?: string }>;
}): string | undefined {
    return codeableConcept?.text ?? codeableConcept?.coding?.[0]?.display;
}

/**
 * Get the first family name from HumanName array
 */
export function getPatientName(names?: Array<{
    family?: string;
    given?: string[];
    text?: string;
}>): string {
    if (!names || names.length === 0) return 'Unknown';

    const name = names[0];
    if (name.text) return name.text;

    const given = name.given?.join(' ') || '';
    const family = name.family || '';

    return `${given} ${family}`.trim() || 'Unknown';
}

/**
 * Calculate age from birthDate
 */
export function calculateAge(birthDate: string): number {
    const birth = new Date(birthDate);
    const today = new Date();
    let age = today.getFullYear() - birth.getFullYear();
    const monthDiff = today.getMonth() - birth.getMonth();

    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birth.getDate())) {
        age--;
    }

    return age;
}

/**
 * Format CPF (Brazilian ID)
 */
export function formatCPF(cpf: string): string {
    const cleaned = cpf.replace(/\D/g, '');
    if (cleaned.length !== 11) return cpf;
    return cleaned.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4');
}

/**
 * Validate CPF
 */
export function isValidCPF(cpf: string): boolean {
    const cleaned = cpf.replace(/\D/g, '');
    if (cleaned.length !== 11) return false;
    if (/^(\d)\1+$/.test(cleaned)) return false;

    let sum = 0;
    for (let i = 0; i < 9; i++) {
        sum += parseInt(cleaned[i]) * (10 - i);
    }
    let remainder = (sum * 10) % 11;
    if (remainder === 10) remainder = 0;
    if (remainder !== parseInt(cleaned[9])) return false;

    sum = 0;
    for (let i = 0; i < 10; i++) {
        sum += parseInt(cleaned[i]) * (11 - i);
    }
    remainder = (sum * 10) % 11;
    if (remainder === 10) remainder = 0;
    if (remainder !== parseInt(cleaned[10])) return false;

    return true;
}
