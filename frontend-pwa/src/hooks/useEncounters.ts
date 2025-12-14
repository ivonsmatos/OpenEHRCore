import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export interface Encounter {
    id: string;
    resourceType: string;
    status: string;
    class?: {
        code: string;
        display?: string;
    };
    type?: Array<{
        text?: string;
        coding?: Array<{
            code: string;
            display: string;
        }>;
    }>;
    period?: {
        start: string;
        end?: string;
    };
    reasonCode?: Array<{
        text?: string;
    }>;
    created_by?: string;
}

export const useEncounters = (patientId?: string) => {
    const [encounters, setEncounters] = useState<Encounter[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const fetchEncounters = useCallback(async () => {
        if (!patientId) return;

        setLoading(true);
        setError(null);
        try {
            const response = await axios.get(`${API_URL}/patients/${patientId}/encounters/`);
            setEncounters(response.data);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Erro ao carregar encontros');
        } finally {
            setLoading(false);
        }
    }, [patientId]);

    const createEncounter = async (data: Partial<Encounter>) => {
        setLoading(true);
        setError(null);
        try {
            // O backend espera um formato simples, não FHIR completo
            const payload = {
                patient_id: patientId,
                encounter_type: 'consultation',
                status: data.status || 'in-progress',
                period_start: data.period?.start || new Date().toISOString(),
                reason_code: data.reasonCode?.[0]?.text || 'Atendimento Clínico'
            };

            console.log('Creating encounter with payload:', JSON.stringify(payload, null, 2));
            const response = await axios.post(`${API_URL}/encounters/`, payload);
            await fetchEncounters();
            return response.data;
        } catch (err: any) {
            const errorMessage = err.response?.data?.error || err.response?.data?.detail || err.message || 'Erro ao criar encontro';
            console.error('Error creating encounter:', {
                status: err.response?.status,
                statusText: err.response?.statusText,
                data: err.response?.data,
                headers: err.response?.headers,
                message: err.message,
                fullError: err
            });
            console.error('Full error response data:', JSON.stringify(err.response?.data, null, 2));
            setError(errorMessage);
            throw err;
        } finally {
            setLoading(false);
        }
    };

    const createObservation = async (data: any) => {
        setLoading(true);
        setError(null);
        try {
            const response = await axios.post(`${API_URL}/observations/`, {
                ...data,
                patient_id: patientId
            });
            return response.data;
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Erro ao criar observação');
            throw err;
        } finally {
            setLoading(false);
        }
    };

    const createCondition = async (data: any) => {
        setLoading(true);
        setError(null);
        try {
            const response = await axios.post(`${API_URL}/conditions/`, {
                ...data,
                patient_id: patientId
            });
            return response.data;
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Erro ao criar condição');
            throw err;
        } finally {
            setLoading(false);
        }
    };

    const createAllergy = async (data: any) => {
        setLoading(true);
        setError(null);
        try {
            const response = await axios.post(`${API_URL}/allergies/`, {
                ...data,
                patient_id: patientId
            });
            return response.data;
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Erro ao criar alergia');
            throw err;
        } finally {
            setLoading(false);
        }
    };

    const createPrescription = async (data: any) => {
        setLoading(true);
        setError(null);
        try {
            const response = await axios.post(`${API_URL}/medications/`, {
                ...data,
                patient_id: patientId
            });
            return response.data;
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Erro ao criar prescrição');
            throw err;
        } finally {
            setLoading(false);
        }
    };

    const createExam = async (data: any) => {
        setLoading(true);
        setError(null);
        try {
            const response = await axios.post(`${API_URL}/exams/`, {
                ...data,
                patient_id: patientId
            });
            return response.data;
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Erro ao criar solicitação de exame');
            throw err;
        } finally {
            setLoading(false);
        }
    };

    const createSOAPNote = async (data: any) => {
        setLoading(true);
        setError(null);
        try {
            const response = await axios.post(`${API_URL}/clinical-impressions/`, {
                ...data,
                patient_id: patientId
            });
            return response.data;
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Erro ao criar nota de evolução');
            throw err;
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (patientId) {
            fetchEncounters();
        }
    }, [patientId, fetchEncounters]);

    return {
        encounters,
        loading,
        error,
        fetchEncounters,
        createEncounter,
        createObservation,
        createCondition,
        createAllergy,
        createPrescription,
        createExam,
        createSOAPNote
    };
};
