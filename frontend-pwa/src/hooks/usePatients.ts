import { useState, useEffect } from 'react';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export interface Patient {
    id: string;
    name: string;
    birthDate: string;
    gender: string;
    email?: string;
    phone?: string;
}

export const usePatients = () => {
    const [patients, setPatients] = useState<Patient[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [pagination, setPagination] = useState({
        current_page: 1,
        total_count: 0,
        total_pages: 1
    });

    const fetchPatients = async (page = 1) => {
        setLoading(true);
        setError(null);
        try {
            const response = await axios.get(`${API_URL}/patients/?page=${page}`);
            // Check if backend returns paginated response
            if (response.data.results) {
                setPatients(response.data.results);
                setPagination({
                    current_page: response.data.current_page,
                    total_count: response.data.count,
                    total_pages: Math.ceil(response.data.count / response.data.page_size)
                });
            } else {
                // Fallback for flat list
                setPatients(response.data);
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Erro ao carregar pacientes');
        } finally {
            setLoading(false);
        }
    };

    const nextPage = () => {
        if (pagination.current_page < pagination.total_pages) {
            fetchPatients(pagination.current_page + 1);
        }
    };

    const prevPage = () => {
        if (pagination.current_page > 1) {
            fetchPatients(pagination.current_page - 1);
        }
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
        createPatient,
        updatePatient,
        deletePatient,
        getPatient,
    };
};
