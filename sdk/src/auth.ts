/**
 * Authentication Client for OpenEHRCore
 *
 * Handles SMART on FHIR OAuth2 authentication
 */

import axios, { AxiosInstance } from 'axios';

export interface AuthConfig {
    baseUrl: string;
    clientId: string;
    clientSecret?: string;
    redirectUri: string;
    scopes?: string[];
}

export interface TokenResponse {
    access_token: string;
    token_type: string;
    expires_in: number;
    refresh_token?: string;
    scope: string;
    patient?: string;
    encounter?: string;
}

export interface SMARTConfiguration {
    issuer: string;
    authorization_endpoint: string;
    token_endpoint: string;
    introspection_endpoint: string;
    revocation_endpoint: string;
    scopes_supported: string[];
    capabilities: string[];
}

export class AuthClient {
    private config: AuthConfig;
    private httpClient: AxiosInstance;
    private tokenData: TokenResponse | null = null;

    constructor(config: AuthConfig) {
        this.config = config;
        this.httpClient = axios.create({
            baseURL: config.baseUrl,
            headers: {
                'Content-Type': 'application/json',
            },
        });
    }

    /**
     * Get SMART configuration from well-known endpoint
     */
    async getSMARTConfiguration(): Promise<SMARTConfiguration> {
        const response = await this.httpClient.get('/.well-known/smart-configuration');
        return response.data;
    }

    /**
     * Generate authorization URL for OAuth2 flow
     */
    getAuthorizationUrl(state: string, codeChallenge?: string): string {
        const params = new URLSearchParams({
            response_type: 'code',
            client_id: this.config.clientId,
            redirect_uri: this.config.redirectUri,
            scope: (this.config.scopes || ['openid', 'fhirUser', 'patient/*.read']).join(' '),
            state,
            aud: this.config.baseUrl,
        });

        if (codeChallenge) {
            params.set('code_challenge', codeChallenge);
            params.set('code_challenge_method', 'S256');
        }

        return `${this.config.baseUrl}/smart/authorize?${params.toString()}`;
    }

    /**
     * Exchange authorization code for tokens
     */
    async exchangeCode(code: string, codeVerifier?: string): Promise<TokenResponse> {
        const data: Record<string, string> = {
            grant_type: 'authorization_code',
            code,
            client_id: this.config.clientId,
            redirect_uri: this.config.redirectUri,
        };

        if (this.config.clientSecret) {
            data.client_secret = this.config.clientSecret;
        }

        if (codeVerifier) {
            data.code_verifier = codeVerifier;
        }

        const response = await this.httpClient.post('/smart/token', data);
        this.tokenData = response.data;
        return response.data;
    }

    /**
     * Refresh access token
     */
    async refreshToken(refreshToken: string): Promise<TokenResponse> {
        const data: Record<string, string> = {
            grant_type: 'refresh_token',
            refresh_token: refreshToken,
            client_id: this.config.clientId,
        };

        if (this.config.clientSecret) {
            data.client_secret = this.config.clientSecret;
        }

        const response = await this.httpClient.post('/smart/token', data);
        this.tokenData = response.data;
        return response.data;
    }

    /**
     * Introspect token
     */
    async introspectToken(token: string): Promise<Record<string, unknown>> {
        const response = await this.httpClient.post('/smart/introspect', { token });
        return response.data;
    }

    /**
     * Revoke token
     */
    async revokeToken(token: string): Promise<void> {
        await this.httpClient.post('/smart/revoke', { token });
    }

    /**
     * Get current access token
     */
    getAccessToken(): string | null {
        return this.tokenData?.access_token || null;
    }

    /**
     * Get patient context from launch
     */
    getPatientContext(): string | null {
        return this.tokenData?.patient || null;
    }

    /**
     * Get encounter context from launch
     */
    getEncounterContext(): string | null {
        return this.tokenData?.encounter || null;
    }

    /**
     * Check if token is expired
     */
    isTokenExpired(): boolean {
        // Simplified check - in production, decode JWT and check exp claim
        return this.tokenData === null;
    }

    /**
     * Generate PKCE code verifier and challenge
     */
    static generatePKCE(): { verifier: string; challenge: string } {
        const verifier = this.generateRandomString(64);
        const challenge = this.sha256Base64Url(verifier);
        return { verifier, challenge };
    }

    private static generateRandomString(length: number): string {
        const charset = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~';
        let result = '';
        const crypto = typeof window !== 'undefined' ? window.crypto : require('crypto');

        if (typeof window !== 'undefined') {
            const values = new Uint8Array(length);
            crypto.getRandomValues(values);
            for (let i = 0; i < length; i++) {
                result += charset[values[i] % charset.length];
            }
        } else {
            const randomBytes = crypto.randomBytes(length);
            for (let i = 0; i < length; i++) {
                result += charset[randomBytes[i] % charset.length];
            }
        }

        return result;
    }

    private static sha256Base64Url(input: string): string {
        if (typeof window !== 'undefined') {
            // Browser implementation would use SubtleCrypto
            // Simplified for SDK - actual implementation needs async
            return input; // Placeholder
        } else {
            const crypto = require('crypto');
            return crypto
                .createHash('sha256')
                .update(input)
                .digest('base64')
                .replace(/\+/g, '-')
                .replace(/\//g, '_')
                .replace(/=+$/, '');
        }
    }
}
