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
 * 
 * Features:
 * - Cache de dados para evitar requisições duplicadas
 * - Debouncing automático
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

// Cache global para evitar requisições duplicadas
const dataCache = new Map<string, { data: any; timestamp: number }>();
const CACHE_DURATION = 30000; // 30 segundos

// Controle de requisições em andamento
const pendingRequests = new Map<string, Promise<any>>();

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
    const isMountedRef = useRef(true);

    useEffect(() => {
        isMountedRef.current = true;
        return () => {
            isMountedRef.current = false;
        };
    }, []);

    // Get token from param or localStorage
    const getAuthHeaders = () => {
        const authToken = token || localStorage.getItem('access_token');
        if (authToken) {
            return { Authorization: `Bearer ${authToken}` };
        }
        return {};
    };

    // Helper para fazer requisição com cache
    const fetchWithCache = async <T,>(
        url: string,
        cacheKey: string,
        headers: any
    ): Promise<T> => {
        // Verificar cache
        const cached = dataCache.get(cacheKey);
        if (cached && Date.now() - cached.timestamp < CACHE_DURATION) {
            return cached.data;
        }

        // Verificar se já existe requisição em andamento
        if (pendingRequests.has(cacheKey)) {
            return pendingRequests.get(cacheKey)!;
        }

        // Fazer nova requisição
        const request = axios.get(url, { headers })
            .then(response => {
                const data = response.data;
                // Salvar no cache
                dataCache.set(cacheKey, { data, timestamp: Date.now() });
                // Remover da lista de pendentes
                pendingRequests.delete(cacheKey);
                return data;
            })
            .catch(error => {
                // Remover da lista de pendentes em caso de erro
                pendingRequests.delete(cacheKey);
                throw error;
            });

        pendingRequests.set(cacheKey, request);
        return request;
    };

    // Fetch sinais vitais (from observations endpoint)
    const fetchVitals = useCallback(async () => {
        const headers = getAuthHeaders();
        if (!headers.Authorization || !isMountedRef.current) return;

        try {
            const cacheKey = `vitals_${patientId}`;
            const responseData = await fetchWithCache(
                `${API_URL}/patients/${patientId}/observations/`,
                cacheKey,
                headers
            );

            // Handle both array and object with results
            const vitals = Array.isArray(responseData)
                ? responseData
                : (responseData?.results || responseData?.observations || []);

            // Processar para formato padronizado (filter vital-signs only)
            const processed: VitalSign[] = vitals
                .filter((v: any) => {
                    // Check if it's a vital sign by category
                    const category = v.category?.[0]?.coding?.[0]?.code;
                    return category === 'vital-signs' || !category; // Include all if no category
                })
                .map((v: any) => ({
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
        } catch (err: any) {
            if (err.response?.status !== 429) { // Ignorar erros 429 silenciosamente
                console.error('Error fetching vitals:', err);
            }
        }
    }, [patientId, token]);

    // Fetch vacinas
    const fetchImmunizations = useCallback(async () => {
        const headers = getAuthHeaders();
        if (!headers.Authorization || !isMountedRef.current) return;

        try {
            const cacheKey = `immunizations_${patientId}`;
            const response = await fetchWithCache(
                `${API_URL}/patients/${patientId}/immunizations/`,
                cacheKey,
                headers
            );
            const immunizations = (response || []).map((i: any) => ({
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
        } catch (err: any) {
            if (err.response?.status !== 429) {
                console.error('Error fetching immunizations:', err);
            }
        }
    }, [patientId, token]);

    // Fetch medicamentos
    const fetchMedications = useCallback(async () => {
        const headers = getAuthHeaders();
        if (!headers.Authorization || !isMountedRef.current) return;

        try {
            const cacheKey = `medications_${patientId}`;
            const responseData = await fetchWithCache(
                `${API_URL}/patients/${patientId}/medications/`,
                cacheKey,
                headers
            );

            // Handle both array and object with results
            const medicationsData = Array.isArray(responseData)
                ? responseData
                : (responseData?.results || responseData?.medications || []);

            const medications = medicationsData.map((m: any) => ({
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
        } catch (err: any) {
            if (err.response?.status !== 429) {
                console.error('Error fetching medications:', err);
            }
        }
    }, [patientId, token]);

    // Fetch resultados de exames
    const fetchDiagnostics = useCallback(async () => {
        const headers = getAuthHeaders();
        if (!headers.Authorization || !isMountedRef.current) return;

        try {
            const cacheKey = `diagnostics_${patientId}`;
            const response = await fetchWithCache(
                `${API_URL}/patients/${patientId}/diagnostic-reports/`,
                cacheKey,
                headers
            );
            const diagnostics = (response || []).map((d: any) => ({
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
        } catch (err: any) {
            if (err.response?.status !== 429) {
                console.error('Error fetching diagnostics:', err);
            }
        }
    }, [patientId, token]);

    // Fetch condições
    const fetchConditions = useCallback(async () => {
        const headers = getAuthHeaders();
        if (!headers.Authorization || !isMountedRef.current) return;

        try {
            const cacheKey = `conditions_${patientId}`;
            const response = await fetchWithCache(
                `${API_URL}/patients/${patientId}/conditions/`,
                cacheKey,
                headers
            );
            setData(prev => ({ ...prev, conditions: response || [] }));
        } catch (err: any) {
            if (err.response?.status !== 429) {
                console.error('Error fetching conditions:', err);
            }
        }
    }, [patientId, token]);

    // Fetch alergias
    const fetchAllergies = useCallback(async () => {
        const headers = getAuthHeaders();
        if (!headers.Authorization || !isMountedRef.current) return;

        try {
            const cacheKey = `allergies_${patientId}`;
            const response = await fetchWithCache(
                `${API_URL}/patients/${patientId}/allergies/`,
                cacheKey,
                headers
            );
            setData(prev => ({ ...prev, allergies: response || [] }));
        } catch (err: any) {
            if (err.response?.status !== 429) {
                console.error('Error fetching allergies:', err);
            }
        }
    }, [patientId, token]);

    // Fetch encounters e construir timeline
    const fetchEncountersAndTimeline = useCallback(async () => {
        const headers = getAuthHeaders();
        if (!headers.Authorization || !isMountedRef.current) return;

        try {
            const cacheKey = `encounters_${patientId}`;
            const response = await fetchWithCache(
                `${API_URL}/patients/${patientId}/encounters/`,
                cacheKey,
                headers
            );
            const encounters = response || [];
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
        } catch (err: any) {
            if (err.response?.status !== 429) {
                console.error('Error fetching encounters:', err);
            }
        }
    }, [patientId, token]);

    // Carregar todos os dados com delay entre requisições
    const refresh = useCallback(async () => {
        if (!isMountedRef.current) return;
        
        setLoading(true);
        setError(null);
        
        try {
            // Carregar dados sequencialmente com pequeno delay para evitar 429
            await fetchVitals();
            await new Promise(resolve => setTimeout(resolve, 100));
            
            await fetchConditions();
            await new Promise(resolve => setTimeout(resolve, 100));
            
            await fetchAllergies();
            await new Promise(resolve => setTimeout(resolve, 100));
            
            await fetchEncountersAndTimeline();
            await new Promise(resolve => setTimeout(resolve, 100));
            
            await fetchImmunizations();
            await new Promise(resolve => setTimeout(resolve, 100));
            
            await fetchMedications();
            await new Promise(resolve => setTimeout(resolve, 100));
            
            await fetchDiagnostics();
        } catch (err: any) {
            if (err.response?.status !== 429) {
                setError('Erro ao carregar dados clínicos');
            }
        } finally {
            if (isMountedRef.current) {
                setLoading(false);
            }
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
