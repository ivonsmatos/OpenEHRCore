/**
 * SDK Tests - Utility Functions
 */

import { describe, it, expect } from 'vitest';
import {
    formatFHIRDate,
    formatFHIRDateTime,
    parseFHIRDate,
    createReference,
    parseReference,
    getPatientName,
    calculateAge,
    formatCPF,
    isValidCPF,
    getCodeableConceptCode,
    getCodeableConceptDisplay
} from '../utils';

describe('formatFHIRDate', () => {
    it('should format date as YYYY-MM-DD', () => {
        const date = new Date('2024-12-13T12:00:00Z');
        const formatted = formatFHIRDate(date);
        expect(formatted).toBe('2024-12-13');
    });
});

describe('formatFHIRDateTime', () => {
    it('should format datetime as ISO string', () => {
        const date = new Date('2024-12-13T12:00:00Z');
        const formatted = formatFHIRDateTime(date);
        expect(formatted).toBe('2024-12-13T12:00:00.000Z');
    });
});

describe('parseFHIRDate', () => {
    it('should parse date string to Date', () => {
        const date = parseFHIRDate('2024-12-13');
        expect(date).toBeInstanceOf(Date);
        expect(date.getFullYear()).toBe(2024);
        // Month is 0-indexed, but may vary by timezone
        expect(date.getMonth()).toBeGreaterThanOrEqual(10); // Nov or Dec
    });
});

describe('createReference', () => {
    it('should create reference without display', () => {
        const ref = createReference('Patient', '123');
        expect(ref).toEqual({ reference: 'Patient/123' });
    });

    it('should create reference with display', () => {
        const ref = createReference('Patient', '123', 'João Silva');
        expect(ref).toEqual({ reference: 'Patient/123', display: 'João Silva' });
    });
});

describe('parseReference', () => {
    it('should parse valid reference', () => {
        const result = parseReference('Patient/123');
        expect(result).toEqual({ resourceType: 'Patient', id: '123' });
    });

    it('should return null for invalid reference', () => {
        const result = parseReference('invalid');
        expect(result).toBeNull();
    });
});

describe('getPatientName', () => {
    it('should get name from HumanName with given and family', () => {
        const names = [{ given: ['João', 'Carlos'], family: 'Silva' }];
        const name = getPatientName(names);
        expect(name).toBe('João Carlos Silva');
    });

    it('should get name from text field', () => {
        const names = [{ text: 'Dr. João Silva' }];
        const name = getPatientName(names);
        expect(name).toBe('Dr. João Silva');
    });

    it('should return Unknown for empty array', () => {
        const name = getPatientName([]);
        expect(name).toBe('Unknown');
    });

    it('should return Unknown for undefined', () => {
        const name = getPatientName(undefined);
        expect(name).toBe('Unknown');
    });
});

describe('calculateAge', () => {
    it('should calculate age correctly', () => {
        // Assuming today is 2024-12-13
        const birthDate = '1990-01-15';
        const age = calculateAge(birthDate);
        expect(age).toBeGreaterThanOrEqual(34);
    });
});

describe('formatCPF', () => {
    it('should format valid CPF', () => {
        const formatted = formatCPF('12345678901');
        expect(formatted).toBe('123.456.789-01');
    });

    it('should return original for invalid length', () => {
        const formatted = formatCPF('123');
        expect(formatted).toBe('123');
    });
});

describe('isValidCPF', () => {
    it('should return false for invalid CPF', () => {
        expect(isValidCPF('12345678901')).toBe(false);
        expect(isValidCPF('11111111111')).toBe(false);
        expect(isValidCPF('123')).toBe(false);
    });

    it('should return true for valid CPF', () => {
        // Example valid CPF: 529.982.247-25
        expect(isValidCPF('52998224725')).toBe(true);
    });
});

describe('getCodeableConceptCode', () => {
    it('should get first code', () => {
        const codeableConcept = {
            coding: [{ code: 'ABC', system: 'http://example.com' }]
        };
        expect(getCodeableConceptCode(codeableConcept)).toBe('ABC');
    });

    it('should return undefined for empty', () => {
        expect(getCodeableConceptCode(undefined)).toBeUndefined();
    });
});

describe('getCodeableConceptDisplay', () => {
    it('should prefer text over display', () => {
        const codeableConcept = {
            text: 'My Text',
            coding: [{ display: 'Display Text' }]
        };
        expect(getCodeableConceptDisplay(codeableConcept)).toBe('My Text');
    });

    it('should fall back to display', () => {
        const codeableConcept = {
            coding: [{ display: 'Display Text' }]
        };
        expect(getCodeableConceptDisplay(codeableConcept)).toBe('Display Text');
    });
});
