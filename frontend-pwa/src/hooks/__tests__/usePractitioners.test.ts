import { renderHook, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { usePractitioners } from '../usePractitioners';

// Mock useAuth
const mockToken = 'test-token';
vi.mock('../useAuth', () => ({
    useAuth: () => ({
        token: mockToken
    })
}));

// Mock API Base
const API_BASE = 'http://localhost:8000/api/v1';

describe('usePractitioners', () => {
    // Setup global fetch mock
    const fetchMock = vi.fn();
    global.fetch = fetchMock;

    beforeEach(() => {
        fetchMock.mockClear();
    });

    afterEach(() => {
        vi.restoreAllMocks();
    });

    it('fetchPractitioners calls API with correct parameters', async () => {
        const mockResponse = { results: [], total: 0 };
        fetchMock.mockResolvedValueOnce({
            ok: true,
            json: async () => mockResponse
        });

        const { result } = renderHook(() => usePractitioners());

        await result.current.fetchPractitioners();

        expect(fetchMock).toHaveBeenCalledWith(
            expect.stringContaining(`${API_BASE}/practitioners/list/`),
            expect.objectContaining({
                headers: {
                    'Authorization': `Bearer ${mockToken}`
                }
            })
        );
    });

    it('fetchPractitioners sends filters correctly', async () => {
        const mockResponse = { results: [], total: 0 };
        fetchMock.mockResolvedValueOnce({
            ok: true,
            json: async () => mockResponse
        });

        const { result } = renderHook(() => usePractitioners());

        await result.current.fetchPractitioners({ name: 'Silva', active: true });

        expect(fetchMock).toHaveBeenCalledWith(
            expect.stringContaining(`${API_BASE}/practitioners/list/`),
            expect.anything()
        );

        const calledUrl = fetchMock.mock.calls[0][0] as string;
        expect(calledUrl).toContain('name=Silva');
        expect(calledUrl).toContain('active=true');
    });

    it('handles fetch error correctly', async () => {
        fetchMock.mockResolvedValueOnce({
            ok: false,
            status: 500,
            statusText: 'Internal Server Error'
        });

        const { result } = renderHook(() => usePractitioners());

        await expect(result.current.fetchPractitioners()).rejects.toThrow('Failed to fetch practitioners');

        await waitFor(() => {
            expect(result.current.error).toBe('Failed to fetch practitioners');
        });
    });

    it('createPractitioner calls API with correct body', async () => {
        const newPractitioner = {
            family_name: 'Santos',
            given_names: ['Pedro'],
            crm: 'CRM-RJ-999999',
            qualification_code: 'MD',
            qualification_display: 'Neurologia',
            gender: 'male' as const,
            birthDate: '1985-01-01',
            phone: '11999999999',
            email: 'pedro@example.com',
            prefix: 'Dr.'
        };

        const mockResponse = { id: '123', ...newPractitioner };
        fetchMock.mockResolvedValue({
            ok: true,
            json: async () => mockResponse
        });

        const { result } = renderHook(() => usePractitioners());

        const response = await result.current.createPractitioner(newPractitioner);

        expect(response).toEqual(mockResponse);
        expect(fetchMock).toHaveBeenCalledWith(
            `${API_BASE}/practitioners/`,
            expect.objectContaining({
                method: 'POST',
                body: JSON.stringify(newPractitioner),
                headers: expect.objectContaining({
                    'Content-Type': 'application/json'
                })
            })
        );
    });
});
