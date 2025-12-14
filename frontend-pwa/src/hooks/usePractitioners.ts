import { useState, useCallback } from 'react';
import { useAuth } from './useAuth';
import { Practitioner, PractitionerFormData, PractitionerFilters, PractitionerListResponse, PractitionerRole } from '../types/practitioner';

const API_BASE = 'http://localhost:8000/api/v1';

export const usePractitioners = () => {
    const { token } = useAuth();
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const fetchPractitioners = useCallback(async (filters?: PractitionerFilters): Promise<PractitionerListResponse> => {
        setLoading(true);
        setError(null);

        try {
            const params = new URLSearchParams();
            if (filters?.name) params.append('name', filters.name);
            if (filters?.identifier) params.append('identifier', filters.identifier);
            if (filters?.active !== null && filters?.active !== undefined) {
                params.append('active', String(filters.active));
            }

            const response = await fetch(
                `${API_BASE}/practitioners/list/?${params}`,
                {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                }
            );

            if (!response.ok) {
                throw new Error('Failed to fetch practitioners');
            }

            const data = await response.json();
            return data;
        } catch (err) {
            const message = err instanceof Error ? err.message : 'Unknown error';
            setError(message);
            throw err;
        } finally {
            setLoading(false);
        }
    }, [token]);

    const getPractitioner = useCallback(async (id: string): Promise<Practitioner> => {
        setLoading(true);
        setError(null);

        try {
            const response = await fetch(
                `${API_BASE}/practitioners/${id}/`,
                {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                }
            );

            if (!response.ok) {
                throw new Error('Failed to fetch practitioner');
            }

            return await response.json();
        } catch (err) {
            const message = err instanceof Error ? err.message : 'Unknown error';
            setError(message);
            throw err;
        } finally {
            setLoading(false);
        }
    }, [token]);

    const createPractitioner = useCallback(async (data: PractitionerFormData): Promise<Practitioner> => {
        setLoading(true);
        setError(null);

        try {
            const response = await fetch(
                `${API_BASE}/practitioners/`,
                {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(data)
                }
            );

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to create practitioner');
            }

            return await response.json();
        } catch (err) {
            const message = err instanceof Error ? err.message : 'Unknown error';
            setError(message);
            throw err;
        } finally {
            setLoading(false);
        }
    }, [token]);

    const updatePractitioner = useCallback(async (id: string, data: PractitionerFormData): Promise<Practitioner> => {
        setLoading(true);
        setError(null);

        try {
            const response = await fetch(
                `${API_BASE}/practitioners/${id}/`,
                {
                    method: 'PUT',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(data)
                }
            );

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to update practitioner');
            }

            return await response.json();
        } catch (err) {
            const message = err instanceof Error ? err.message : 'Unknown error';
            setError(message);
            throw err;
        } finally {
            setLoading(false);
        }
    }, [token]);

    const createPractitionerRole = useCallback(async (data: {
        practitioner_id: string;
        organization_id?: string;
        specialty_code?: string;
        specialty_display?: string;
        location_ids?: string[];
        available_days?: string[];
        available_start?: string;
        available_end?: string;
    }): Promise<PractitionerRole> => {
        setLoading(true);
        setError(null);

        try {
            const response = await fetch(
                `${API_BASE}/practitioner-roles/`,
                {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(data)
                }
            );

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to create practitioner role');
            }

            return await response.json();
        } catch (err) {
            const message = err instanceof Error ? err.message : 'Unknown error';
            setError(message);
            throw err;
        } finally {
            setLoading(false);
        }
    }, [token]);

    return {
        loading,
        error,
        fetchPractitioners,
        getPractitioner,
        createPractitioner,
        updatePractitioner,
        createPractitionerRole
    };
};
