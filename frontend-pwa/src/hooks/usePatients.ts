import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

// Helper to get token from localStorage
const getAuthHeaders = () => {
    const token = localStorage.getItem('access_token');
    if (token) {
        return { Authorization: `Bearer ${token}` };
    }
    return {};
};

export interface Patient {
    id: string;
    name: string;
    birthDate: string;
    gender: string;
    email?: string;
    phone?: string;
}

export interface PatientSearchFilters {
    name?: string;
    identifier?: string;
    gender?: string;
    birthdate?: string;
    birthdateGe?: string;
    birthdateLe?: string;
}

export const usePatients = () => {
    const [patients, setPatients] = useState<Patient[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [pagination, setPagination] = useState({
        current_page: 1,
        total_count: 0,
        total_pages: 1,
        page_size: 20
    });
    const [currentFilters, setCurrentFilters] = useState<PatientSearchFilters>({});

    const fetchPatients = useCallback(async (page = 1, pageSize = 20, filters: PatientSearchFilters = {}) => {
        // Check if user is logged in
        const token = localStorage.getItem('access_token');
        if (!token) {
            console.log('No token found, skipping patient fetch');
            return;
        }

        setLoading(true);
        setError(null);
        setCurrentFilters(filters);
        try {
            const params = new URLSearchParams();
            params.append('_count', pageSize.toString());
            params.append('_getpagesoffset', ((page - 1) * pageSize).toString());

            // Add search filters
            if (filters.name) params.append('name', filters.name);
            if (filters.identifier) params.append('identifier', filters.identifier);
            if (filters.gender) params.append('gender', filters.gender);
            if (filters.birthdate) params.append('birthdate', filters.birthdate);
            if (filters.birthdateGe) params.append('birthdate', `ge${filters.birthdateGe}`);
            if (filters.birthdateLe) params.append('birthdate', `le${filters.birthdateLe}`);

            // Use advanced search endpoint with explicit headers
            const response = await axios.get(`${API_URL}/patients/search/`, {
                params,
                headers: getAuthHeaders()
            });

            if (response.data.results) {
                setPatients(response.data.results);
                const total = response.data.total || response.data.results.length;
                setPagination({
                    current_page: page,
                    total_count: total,
                    total_pages: Math.ceil(total / pageSize),
                    page_size: pageSize
                });
            } else {
                setPatients(response.data);
            }
        } catch (err: any) {
            console.error('Error fetching patients:', err);
            const message = err.response?.data?.error || err.message || 'Erro ao carregar pacientes';
            setError(message);
        } finally {
            setLoading(false);
        }
    }, []);

    const nextPage = () => {
        if (pagination.current_page < pagination.total_pages) {
            fetchPatients(pagination.current_page + 1, pagination.page_size, currentFilters);
        }
    };

    const prevPage = () => {
        if (pagination.current_page > 1) {
            fetchPatients(pagination.current_page - 1, pagination.page_size, currentFilters);
        }
    };

    const goToPage = (page: number) => {
        if (page >= 1 && page <= pagination.total_pages) {
            fetchPatients(page, pagination.page_size, currentFilters);
        }
    };

    const setPageSize = (size: number) => {
        fetchPatients(1, size, currentFilters);
    };

    const createPatient = async (data: Partial<Patient>) => {
        setLoading(true);
        setError(null);
        try {
            const response = await axios.post(`${API_URL}/patients/`, data);
            await fetchPatients(pagination.current_page); // Recarregar página atual
            return response.data;
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Erro ao criar paciente');
            throw err;
        } finally {
            setLoading(false);
        }
    };

    const updatePatient = async (id: string, data: Partial<Patient>) => {
        setLoading(true);
        setError(null);
        try {
            const response = await axios.put(`${API_URL}/patients/${id}/`, data);
            await fetchPatients(pagination.current_page);
            return response.data;
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Erro ao atualizar paciente');
            throw err;
        } finally {
            setLoading(false);
        }
    };

    const deletePatient = async (id: string) => {
        setLoading(true);
        setError(null);
        try {
            await axios.delete(`${API_URL}/patients/${id}/`);
            await fetchPatients(pagination.current_page);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Erro ao excluir paciente');
            throw err;
        } finally {
            setLoading(false);
        }
    };

    const getPatient = async (id: string) => {
        setLoading(true);
        setError(null);
        try {
            const response = await axios.get(`${API_URL}/patients/${id}/`);
            return response.data;
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Erro ao carregar paciente');
            throw err;
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchPatients(1);
    }, []);

    return {
        patients,
        loading,
        error,
        pagination,
        fetchPatients,
        nextPage,
        prevPage,
        goToPage,
        setPageSize,
        createPatient,
        updatePatient,
        deletePatient,
        getPatient,
    };
};
