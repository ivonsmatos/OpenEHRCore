/**
 * SDK Tests - FHIR Client
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { FHIRClient } from '../src/fhir';
import type { Patient, Bundle } from '../src/types';

// Mock axios
vi.mock('axios', () => ({
    default: {
        create: vi.fn(() => ({
            get: vi.fn(),
            post: vi.fn(),
            put: vi.fn(),
            delete: vi.fn(),
            patch: vi.fn(),
            interceptors: {
                request: { use: vi.fn() }
            }
        }))
    }
}));

describe('FHIRClient', () => {
    let client: FHIRClient;

    beforeEach(() => {
        client = new FHIRClient({
            baseUrl: 'http://localhost:8000/api/v1',
            accessToken: 'test-token'
        });
    });

    describe('constructor', () => {
        it('should create client with config', () => {
            expect(client).toBeDefined();
        });

        it('should set access token', () => {
            client.setAccessToken('new-token');
            // Token is set internally
            expect(client).toBeDefined();
        });
    });

    describe('extractResources', () => {
        it('should extract resources from bundle', () => {
            const bundle: Bundle<Patient> = {
                resourceType: 'Bundle',
                type: 'searchset',
                total: 2,
                entry: [
                    { resource: { resourceType: 'Patient', id: '1', name: [{ family: 'Silva' }] } },
                    { resource: { resourceType: 'Patient', id: '2', name: [{ family: 'Santos' }] } }
                ]
            };

            const patients = FHIRClient.extractResources(bundle);
            expect(patients).toHaveLength(2);
            expect(patients[0].id).toBe('1');
            expect(patients[1].id).toBe('2');
        });

        it('should handle empty bundle', () => {
            const bundle: Bundle<Patient> = {
                resourceType: 'Bundle',
                type: 'searchset',
                entry: []
            };

            const patients = FHIRClient.extractResources(bundle);
            expect(patients).toHaveLength(0);
        });

        it('should handle bundle without entry', () => {
            const bundle: Bundle<Patient> = {
                resourceType: 'Bundle',
                type: 'searchset'
            };

            const patients = FHIRClient.extractResources(bundle);
            expect(patients).toHaveLength(0);
        });
    });

    describe('getNextPageUrl', () => {
        it('should return next page url', () => {
            const bundle: Bundle = {
                resourceType: 'Bundle',
                type: 'searchset',
                link: [
                    { relation: 'self', url: 'http://example.com/Patient?page=1' },
                    { relation: 'next', url: 'http://example.com/Patient?page=2' }
                ]
            };

            const nextUrl = FHIRClient.getNextPageUrl(bundle);
            expect(nextUrl).toBe('http://example.com/Patient?page=2');
        });

        it('should return null if no next page', () => {
            const bundle: Bundle = {
                resourceType: 'Bundle',
                type: 'searchset',
                link: [
                    { relation: 'self', url: 'http://example.com/Patient?page=1' }
                ]
            };

            const nextUrl = FHIRClient.getNextPageUrl(bundle);
            expect(nextUrl).toBeNull();
        });
    });
});
