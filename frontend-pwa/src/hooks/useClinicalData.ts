/**
 * useClinicalData - Hook centralizado para dados clínicos do paciente
 * 
 * Carrega todos os dados relevantes do FHIR:
 * - Sinais vitais (Observation)
 * - Vacinas (Immunization)
 * - Medicamentos (MedicationRequest)
 * - Exames (DiagnosticReport)
 * - Condições (Condition)
 * - Alergias (AllergyIntolerance)
 * - Atendimentos (Encounter)
 */

import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

// Tipos de sinais vitais LOINC
export const VITAL_SIGN_CODES = {
    heartRate: { loinc: '8867-4', display: 'Frequência Cardíaca', unit: 'bpm' },
    systolicBP: { loinc: '8480-6', display: 'Pressão Sistólica', unit: 'mmHg' },
    diastolicBP: { loinc: '8462-4', display: 'Pressão Diastólica', unit: 'mmHg' },
    temperature: { loinc: '8310-5', display: 'Temperatura', unit: '°C' },
    spo2: { loinc: '59408-5', display: 'SpO2', unit: '%' },
    respiratoryRate: { loinc: '9279-1', display: 'Freq. Respiratória', unit: 'rpm' },
    weight: { loinc: '29463-7', display: 'Peso', unit: 'kg' },
    height: { loinc: '8302-2', display: 'Altura', unit: 'cm' },
    bmi: { loinc: '39156-5', display: 'IMC', unit: 'kg/m²' },
    pain: { loinc: '72514-3', display: 'Dor', unit: '0-10' },
    glucose: { loinc: '2339-0', display: 'Glicemia', unit: 'mg/dL' },
};

export interface VitalSign {
    id: string;
    code: string;
    display: string;
    value: number;
    unit: string;
    date: string;
    status: string;
}

export interface Immunization {
    id: string;
    vaccineName: string;
    vaccineCode: string;
    date: string;
    status: string;
    lotNumber?: string;
    site?: string;
    performer?: string;
}

export interface Medication {
    id: string;
    name: string;
    dosage: string;
    frequency: string;
    route: string;
    status: 'active' | 'completed' | 'stopped' | 'on-hold' | 'cancelled';
    startDate?: string;
    endDate?: string;
    prescriber?: string;
    notes?: string;
}

export interface DiagnosticResult {
    id: string;
    category: string;
    code: string;
    display: string;
    status: string;
    effectiveDate: string;
    results: Array<{
        code: string;
        display: string;
        value: string | number;
        unit: string;
        referenceRange?: string;
        interpretation?: 'normal' | 'high' | 'low' | 'critical';
    }>;
    performer?: string;
}

export interface TimelineEvent {
    id: string;
    type: 'encounter' | 'observation' | 'medication' | 'immunization' | 'procedure' | 'diagnostic';
    date: string;
    title: string;
    description: string;
    icon: string;
    status?: string;
    details?: any;
}

export interface ClinicalData {
    vitalSigns: VitalSign[];
    latestVitals: Record<string, VitalSign>;
    immunizations: Immunization[];
    medications: Medication[];
    diagnosticResults: DiagnosticResult[];
    timeline: TimelineEvent[];
    conditions: any[];
    allergies: any[];
    encounters: any[];
}

interface UseClinicalDataResult {
    data: ClinicalData;
    loading: boolean;
    error: string | null;
    refresh: () => void;
    refreshVitals: () => void;
    refreshMedications: () => void;
    refreshImmunizations: () => void;
    refreshDiagnostics: () => void;
}

export function useClinicalData(patientId: string, token?: string): UseClinicalDataResult {
    const [data, setData] = useState<ClinicalData>({
        vitalSigns: [],
        latestVitals: {},
        immunizations: [],
        medications: [],
        diagnosticResults: [],
        timeline: [],
        conditions: [],
        allergies: [],
        encounters: [],
    });
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // Get token from param or localStorage
    const getAuthHeaders = () => {
        const authToken = token || localStorage.getItem('access_token');
        if (authToken) {
            return { Authorization: `Bearer ${authToken}` };
        }
        return {};
    };

    // Fetch sinais vitais
    const fetchVitals = useCallback(async () => {
        const headers = getAuthHeaders();
        if (!headers.Authorization) return;

        try {
            const response = await axios.get(`${API_URL}/patients/${patientId}/vitals/`, { headers });
            const vitals = response.data || [];

            // Processar para formato padronizado
            const processed: VitalSign[] = vitals.map((v: any) => ({
                id: v.id,
                code: v.code?.coding?.[0]?.code || '',
                display: v.code?.coding?.[0]?.display || v.type || '',
                value: v.valueQuantity?.value || v.value || 0,
                unit: v.valueQuantity?.unit || v.unit || '',
                date: v.effectiveDateTime || v.date || '',
                status: v.status || 'final',
            }));

            // Calcular últimos valores por tipo
            const latest: Record<string, VitalSign> = {};
            processed.forEach(v => {
                const key = v.code || v.display.toLowerCase().replace(/\s/g, '_');
                if (!latest[key] || new Date(v.date) > new Date(latest[key].date)) {
                    latest[key] = v;
                }
            });

            setData(prev => ({ ...prev, vitalSigns: processed, latestVitals: latest }));
        } catch (err) {
            console.error('Error fetching vitals:', err);
        }
    }, [patientId, token]);

    // Fetch vacinas
    const fetchImmunizations = useCallback(async () => {
        const headers = getAuthHeaders();
        if (!headers.Authorization) return;

        try {
            const response = await axios.get(`${API_URL}/patients/${patientId}/immunizations/`, { headers });
            const immunizations = (response.data || []).map((i: any) => ({
                id: i.id,
                vaccineName: i.vaccineCode?.coding?.[0]?.display || i.vaccine_name || i.name || '',
                vaccineCode: i.vaccineCode?.coding?.[0]?.code || '',
                date: i.occurrenceDateTime || i.date || '',
                status: i.status || 'completed',
                lotNumber: i.lotNumber || i.lot_number || '',
                site: i.site?.coding?.[0]?.display || '',
                performer: i.performer?.[0]?.actor?.display || '',
            }));
            setData(prev => ({ ...prev, immunizations }));
        } catch (err) {
            console.error('Error fetching immunizations:', err);
        }
    }, [patientId, token]);

    // Fetch medicamentos
    const fetchMedications = useCallback(async () => {
        const headers = getAuthHeaders();
        if (!headers.Authorization) return;

        try {
            const response = await axios.get(`${API_URL}/patients/${patientId}/medications/`, { headers });
            const medications = (response.data || []).map((m: any) => ({
                id: m.id,
                name: m.medicationCodeableConcept?.coding?.[0]?.display || m.name || m.medication_name || '',
                dosage: m.dosageInstruction?.[0]?.doseAndRate?.[0]?.doseQuantity?.value +
                    (m.dosageInstruction?.[0]?.doseAndRate?.[0]?.doseQuantity?.unit || '') || m.dosage || '',
                frequency: m.dosageInstruction?.[0]?.timing?.repeat?.frequency + 'x/' +
                    m.dosageInstruction?.[0]?.timing?.repeat?.period +
                    m.dosageInstruction?.[0]?.timing?.repeat?.periodUnit || m.frequency || '',
                route: m.dosageInstruction?.[0]?.route?.coding?.[0]?.display || m.route || '',
                status: m.status || 'active',
                startDate: m.authoredOn || m.start_date || '',
                endDate: m.dispenseRequest?.validityPeriod?.end || m.end_date || '',
                prescriber: m.requester?.display || m.prescriber || '',
                notes: m.note?.[0]?.text || m.notes || '',
            }));
            setData(prev => ({ ...prev, medications }));
        } catch (err) {
            console.error('Error fetching medications:', err);
        }
    }, [patientId, token]);

    // Fetch resultados de exames
    const fetchDiagnostics = useCallback(async () => {
        const headers = getAuthHeaders();
        if (!headers.Authorization) return;

        try {
            const response = await axios.get(`${API_URL}/patients/${patientId}/diagnostic-reports/`, { headers });
            const diagnostics = (response.data || []).map((d: any) => ({
                id: d.id,
                category: d.category?.[0]?.coding?.[0]?.display || '',
                code: d.code?.coding?.[0]?.code || '',
                display: d.code?.coding?.[0]?.display || d.title || '',
                status: d.status || 'final',
                effectiveDate: d.effectiveDateTime || d.issued || d.date || '',
                results: (d.result || []).map((r: any) => ({
                    code: r.code?.coding?.[0]?.code || '',
                    display: r.code?.coding?.[0]?.display || r.name || '',
                    value: r.valueQuantity?.value || r.value || '',
                    unit: r.valueQuantity?.unit || '',
                    referenceRange: r.referenceRange?.[0]?.text || '',
                    interpretation: r.interpretation?.[0]?.coding?.[0]?.code || 'normal',
                })),
                performer: d.performer?.[0]?.display || '',
            }));
            setData(prev => ({ ...prev, diagnosticResults: diagnostics }));
        } catch (err) {
            console.error('Error fetching diagnostics:', err);
        }
    }, [patientId, token]);

    // Fetch condições
    const fetchConditions = useCallback(async () => {
        const headers = getAuthHeaders();
        if (!headers.Authorization) return;

        try {
            const response = await axios.get(`${API_URL}/patients/${patientId}/conditions/`, { headers });
            setData(prev => ({ ...prev, conditions: response.data || [] }));
        } catch (err) {
            console.error('Error fetching conditions:', err);
        }
    }, [patientId, token]);

    // Fetch alergias
    const fetchAllergies = useCallback(async () => {
        const headers = getAuthHeaders();
        if (!headers.Authorization) return;

        try {
            const response = await axios.get(`${API_URL}/patients/${patientId}/allergies/`, { headers });
            setData(prev => ({ ...prev, allergies: response.data || [] }));
        } catch (err) {
            console.error('Error fetching allergies:', err);
        }
    }, [patientId, token]);

    // Fetch encounters e construir timeline
    const fetchEncountersAndTimeline = useCallback(async () => {
        const headers = getAuthHeaders();
        if (!headers.Authorization) return;

        try {
            const response = await axios.get(`${API_URL}/patients/${patientId}/encounters/`, { headers });
            const encounters = response.data || [];
            setData(prev => ({ ...prev, encounters }));

            // Construir timeline unificada
            const timeline: TimelineEvent[] = [];

            // Adicionar encounters
            encounters.forEach((e: any) => {
                timeline.push({
                    id: e.id,
                    type: 'encounter',
                    date: e.period?.start || e.date || '',
                    title: e.type?.[0]?.coding?.[0]?.display || 'Atendimento',
                    description: e.reasonCode?.[0]?.text || e.reason || 'Consulta realizada',
                    icon: '🏥',
                    status: e.status,
                });
            });

            setData(prev => ({ ...prev, timeline }));
        } catch (err) {
            console.error('Error fetching encounters:', err);
        }
    }, [patientId, token]);

    // Carregar todos os dados
    const refresh = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            await Promise.all([
                fetchVitals(),
                fetchImmunizations(),
                fetchMedications(),
                fetchDiagnostics(),
                fetchConditions(),
                fetchAllergies(),
                fetchEncountersAndTimeline(),
            ]);
        } catch (err) {
            setError('Erro ao carregar dados clínicos');
        } finally {
            setLoading(false);
        }
    }, [fetchVitals, fetchImmunizations, fetchMedications, fetchDiagnostics, fetchConditions, fetchAllergies, fetchEncountersAndTimeline]);

    useEffect(() => {
        if (patientId) {
            refresh();
        }
    }, [patientId]);

    return {
        data,
        loading,
        error,
        refresh,
        refreshVitals: fetchVitals,
        refreshMedications: fetchMedications,
        refreshImmunizations: fetchImmunizations,
        refreshDiagnostics: fetchDiagnostics,
    };
}

export default useClinicalData;
