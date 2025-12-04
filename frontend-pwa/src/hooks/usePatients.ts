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

    const fetchPatients = async () => {
        setLoading(true);
        setError(null);
        try {
            const response = await axios.get(`${API_URL}/patients/`);
            setPatients(response.data);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Erro ao carregar pacientes');
        } finally {
            setLoading(false);
        }
    };

    const createPatient = async (data: Partial<Patient>) => {
        setLoading(true);
        setError(null);
        try {
            const response = await axios.post(`${API_URL}/patients/`, data);
            await fetchPatients(); // Recarregar lista
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
            await fetchPatients(); // Recarregar lista
            return response.data;
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Erro ao atualizar paciente');
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
        fetchPatients();
    }, []);

    return {
        patients,
        loading,
        error,
        fetchPatients,
        createPatient,
        updatePatient,
        getPatient,
    };
};
