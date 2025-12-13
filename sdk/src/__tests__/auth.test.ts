/**
 * SDK Tests - Auth Client
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { AuthClient } from '../auth';

// Mock axios
vi.mock('axios', () => ({
    default: {
        create: vi.fn(() => ({
            get: vi.fn(),
            post: vi.fn(),
        }))
    }
}));

describe('AuthClient', () => {
    let client: AuthClient;

    beforeEach(() => {
        client = new AuthClient({
            baseUrl: 'http://localhost:8000/api/v1',
            clientId: 'test-app',
            redirectUri: 'http://localhost:3000/callback',
            scopes: ['openid', 'patient/*.read']
        });
    });

    describe('constructor', () => {
        it('should create client with config', () => {
            expect(client).toBeDefined();
        });
    });

    describe('getAuthorizationUrl', () => {
        it('should generate authorization URL', () => {
            const url = client.getAuthorizationUrl('test-state');

            expect(url).toContain('http://localhost:8000/api/v1/smart/authorize');
            expect(url).toContain('response_type=code');
            expect(url).toContain('client_id=test-app');
            expect(url).toContain('redirect_uri=http%3A%2F%2Flocalhost%3A3000%2Fcallback');
            expect(url).toContain('state=test-state');
        });

        it('should include PKCE challenge if provided', () => {
            const url = client.getAuthorizationUrl('test-state', 'test-challenge');

            expect(url).toContain('code_challenge=test-challenge');
            expect(url).toContain('code_challenge_method=S256');
        });
    });

    describe('getAccessToken', () => {
        it('should return null initially', () => {
            expect(client.getAccessToken()).toBeNull();
        });
    });

    describe('getPatientContext', () => {
        it('should return null initially', () => {
            expect(client.getPatientContext()).toBeNull();
        });
    });

    describe('getEncounterContext', () => {
        it('should return null initially', () => {
            expect(client.getEncounterContext()).toBeNull();
        });
    });

    describe('isTokenExpired', () => {
        it('should return true when no token', () => {
            expect(client.isTokenExpired()).toBe(true);
        });
    });

    describe('generatePKCE', () => {
        it('should generate verifier and challenge', () => {
            const pkce = AuthClient.generatePKCE();

            expect(pkce).toHaveProperty('verifier');
            expect(pkce).toHaveProperty('challenge');
            expect(pkce.verifier.length).toBe(64);
        });
    });
});
