/**
 * FHIR Client for OpenEHRCore
 *
 * Generic FHIR R4 client for resource operations
 */

import axios, { AxiosInstance, AxiosRequestConfig } from 'axios';
import type { Resource, Bundle, SearchParams, ApiError } from './types';

export interface FHIRClientConfig {
    baseUrl: string;
    accessToken?: string;
    headers?: Record<string, string>;
}

export class FHIRClient {
    private httpClient: AxiosInstance;
    private config: FHIRClientConfig;

    constructor(config: FHIRClientConfig) {
        this.config = config;
        this.httpClient = axios.create({
            baseURL: config.baseUrl,
            headers: {
                'Content-Type': 'application/fhir+json',
                Accept: 'application/fhir+json',
                ...config.headers,
            },
        });

        // Add auth interceptor
        this.httpClient.interceptors.request.use((reqConfig) => {
            if (this.config.accessToken) {
                reqConfig.headers.Authorization = `Bearer ${this.config.accessToken}`;
            }
            return reqConfig;
        });
    }

    /**
     * Set access token for subsequent requests
     */
    setAccessToken(token: string): void {
        this.config.accessToken = token;
    }

    /**
     * Read a resource by ID
     */
    async read<T extends Resource>(resourceType: string, id: string): Promise<T> {
        const response = await this.httpClient.get<T>(`/${resourceType}/${id}`);
        return response.data;
    }

    /**
     * Search for resources
     */
    async search<T extends Resource>(
        resourceType: string,
        params?: SearchParams
    ): Promise<Bundle<T>> {
        const response = await this.httpClient.get<Bundle<T>>(`/${resourceType}`, {
            params,
        });
        return response.data;
    }

    /**
     * Create a new resource
     */
    async create<T extends Resource>(resourceType: string, resource: T): Promise<T> {
        const response = await this.httpClient.post<T>(`/${resourceType}`, resource);
        return response.data;
    }

    /**
     * Update an existing resource
     */
    async update<T extends Resource>(resourceType: string, id: string, resource: T): Promise<T> {
        const response = await this.httpClient.put<T>(`/${resourceType}/${id}`, resource);
        return response.data;
    }

    /**
     * Delete a resource
     */
    async delete(resourceType: string, id: string): Promise<void> {
        await this.httpClient.delete(`/${resourceType}/${id}`);
    }

    /**
     * Patch a resource (JSON Patch)
     */
    async patch<T extends Resource>(
        resourceType: string,
        id: string,
        operations: PatchOperation[]
    ): Promise<T> {
        const response = await this.httpClient.patch<T>(`/${resourceType}/${id}`, operations, {
            headers: { 'Content-Type': 'application/json-patch+json' },
        });
        return response.data;
    }

    /**
     * Get resource history
     */
    async history<T extends Resource>(resourceType: string, id?: string): Promise<Bundle<T>> {
        const path = id ? `/${resourceType}/${id}/_history` : `/${resourceType}/_history`;
        const response = await this.httpClient.get<Bundle<T>>(path);
        return response.data;
    }

    /**
     * Execute a FHIR operation
     */
    async operation<T>(
        resourceType: string,
        operationName: string,
        parameters?: Record<string, unknown>,
        id?: string
    ): Promise<T> {
        const path = id
            ? `/${resourceType}/${id}/$${operationName}`
            : `/${resourceType}/$${operationName}`;

        const response = await this.httpClient.post<T>(path, parameters || {});
        return response.data;
    }

    /**
     * Execute a transaction/batch
     */
    async transaction<T extends Resource>(bundle: Bundle<T>): Promise<Bundle<T>> {
        const response = await this.httpClient.post<Bundle<T>>('/', bundle);
        return response.data;
    }

    /**
     * Get capability statement
     */
    async capabilities(): Promise<Resource> {
        const response = await this.httpClient.get('/metadata');
        return response.data;
    }

    /**
     * Validate a resource
     */
    async validate<T extends Resource>(resourceType: string, resource: T): Promise<Resource> {
        const response = await this.httpClient.post<Resource>(
            `/${resourceType}/$validate`,
            resource
        );
        return response.data;
    }

    /**
     * Helper method to extract resources from a Bundle
     */
    static extractResources<T extends Resource>(bundle: Bundle<T>): T[] {
        return (bundle.entry || [])
            .filter((entry) => entry.resource)
            .map((entry) => entry.resource as T);
    }

    /**
     * Helper method to get next page URL from bundle
     */
    static getNextPageUrl(bundle: Bundle): string | null {
        const nextLink = bundle.link?.find((link) => link.relation === 'next');
        return nextLink?.url || null;
    }

    /**
     * Iterate through all pages of a search result
     */
    async *searchAll<T extends Resource>(
        resourceType: string,
        params?: SearchParams
    ): AsyncGenerator<T, void, unknown> {
        let bundle = await this.search<T>(resourceType, params);

        for (const entry of bundle.entry || []) {
            if (entry.resource) {
                yield entry.resource;
            }
        }

        while (FHIRClient.getNextPageUrl(bundle)) {
            const nextUrl = FHIRClient.getNextPageUrl(bundle)!;
            const response = await this.httpClient.get<Bundle<T>>(nextUrl);
            bundle = response.data;

            for (const entry of bundle.entry || []) {
                if (entry.resource) {
                    yield entry.resource;
                }
            }
        }
    }
}

export interface PatchOperation {
    op: 'add' | 'remove' | 'replace' | 'move' | 'copy' | 'test';
    path: string;
    value?: unknown;
    from?: string;
}
