import { useState } from 'react';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export interface QuestionnaireItem {
    linkId: string;
    text: string;
    type: string;
}

export interface QuestionnaireResponseAnswer {
    linkId: string;
    text: string;
    valueString: string;
}

export const useCheckIn = () => {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const createQuestionnaire = async (title: string, items: QuestionnaireItem[]) => {
        setLoading(true);
        setError(null);
        try {
            const response = await axios.post(`${API_URL}/questionnaires/`, {
                title,
                items
            });
            return response.data;
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Erro ao criar questionário');
            throw err;
        } finally {
            setLoading(false);
        }
    };

    const submitResponse = async (questionnaireId: string, patientId: string, answers: QuestionnaireResponseAnswer[]) => {
        setLoading(true);
        setError(null);
        try {
            const response = await axios.post(`${API_URL}/questionnaires/response/`, {
                questionnaire_id: questionnaireId,
                patient_id: patientId,
                answers
            });
            return response.data;
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Erro ao enviar resposta');
            throw err;
        } finally {
            setLoading(false);
        }
    };

    return {
        loading,
        error,
        createQuestionnaire,
        submitResponse
    };
};
