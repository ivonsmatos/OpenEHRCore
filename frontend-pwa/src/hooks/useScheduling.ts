import { useState, useCallback } from 'react';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export interface Slot {
    id: string;
    resourceType: string;
    scheduleId: string;
    start: string;
    end: string;
    status: string;
}

export interface Schedule {
    id: string;
    resourceType: string;
    actor: string;
    comment: string;
}

export const useScheduling = () => {
    const [slots, setSlots] = useState<Slot[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const createSchedule = async (practitionerId: string, actorDisplay: string, comment: string) => {
        setLoading(true);
        setError(null);
        try {
            const response = await axios.post(`${API_URL}/schedule/`, {
                practitioner_id: practitionerId,
                actor_display: actorDisplay,
                comment
            });
            return response.data;
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Erro ao criar agenda');
            throw err;
        } finally {
            setLoading(false);
        }
    };

    const createSlot = async (scheduleId: string, start: string, end: string, status: string = 'free') => {
        setLoading(true);
        setError(null);
        try {
            const response = await axios.post(`${API_URL}/slots/`, {
                schedule_id: scheduleId,
                start,
                end,
                status
            });
            return response.data;
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Erro ao criar slot');
            throw err;
        } finally {
            setLoading(false);
        }
    };

    const fetchSlots = useCallback(async (start?: string, end?: string) => {
        setLoading(true);
        setError(null);
        try {
            const params: any = {};
            if (start) params.start = start;
            if (end) params.end = end;

            const response = await axios.get(`${API_URL}/slots/search/`, { params });
            setSlots(response.data);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Erro ao buscar slots');
        } finally {
            setLoading(false);
        }
    }, []);

    return {
        slots,
        loading,
        error,
        createSchedule,
        createSlot,
        fetchSlots
    };
};
