import React, { useState } from 'react';
import { useEncounters } from '../../hooks/useEncounters';
import Button from '../base/Button';
import { colors, spacing } from '../../theme/colors';

interface VitalSignsFormProps {
    encounterId?: string | null;
    onSuccess?: () => void;
}

interface VitalSignData {
    systolic?: string;
    diastolic?: string;
    heartRate?: string;
    respiratoryRate?: string;
    temperature?: string;
    spo2?: string;
    weight?: string;
    height?: string;
}

const LOINC_CODES = {
    BP_PANEL: '85354-9',
    BP_SYSTOLIC: '8480-6',
    BP_DIASTOLIC: '8462-4',
    HEART_RATE: '8867-4',
    RESPIRATORY_RATE: '9279-1',
    TEMPERATURE: '8310-5',
    SPO2: '2708-6',
    WEIGHT: '29463-7',
    HEIGHT: '8302-2',
};

export const VitalSignsForm: React.FC<VitalSignsFormProps> = ({ encounterId, onSuccess }) => {
    const { createObservation, loading } = useEncounters(); // Note: patientId is handled by the hook context if provided, but here we might need to ensure it's available. 
    // Actually, useEncounters expects patientId in the hook init. 
    // If ClinicalWorkspace initializes useEncounters without patientId, it might fail.
    // But ClinicalWorkspace uses useEncounters() without args? No, let's check ClinicalWorkspace.

    const [formData, setFormData] = useState<VitalSignData>({});
    const [error, setError] = useState<string | null>(null);
    const [successMessage, setSuccessMessage] = useState<string | null>(null);

    const handleChange = (field: keyof VitalSignData, value: string) => {
        setFormData(prev => ({ ...prev, [field]: value }));
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);
        setSuccessMessage(null);

        try {
            const promises = [];

            // 1. Blood Pressure (Complex)
            if (formData.systolic && formData.diastolic) {
                promises.push(createObservation({
                    code: LOINC_CODES.BP_PANEL,
                    status: 'final',
                    encounter_id: encounterId,
                    components: [
                        { code: LOINC_CODES.BP_SYSTOLIC, value: formData.systolic, unit: 'mmHg' },
                        { code: LOINC_CODES.BP_DIASTOLIC, value: formData.diastolic, unit: 'mmHg' }
                    ]
                }));
            }

            // 2. Heart Rate
            if (formData.heartRate) {
                promises.push(createObservation({
                    code: LOINC_CODES.HEART_RATE,
                    value: formData.heartRate,
                    status: 'final',
                    encounter_id: encounterId
                }));
            }

            // 3. Respiratory Rate
            if (formData.respiratoryRate) {
                promises.push(createObservation({
                    code: LOINC_CODES.RESPIRATORY_RATE,
                    value: formData.respiratoryRate,
                    status: 'final',
                    encounter_id: encounterId
                }));
            }

            // 4. Temperature
            if (formData.temperature) {
                promises.push(createObservation({
                    code: LOINC_CODES.TEMPERATURE,
                    value: formData.temperature,
                    status: 'final',
                    encounter_id: encounterId
                }));
            }

            // 5. SpO2
            if (formData.spo2) {
                promises.push(createObservation({
                    code: LOINC_CODES.SPO2,
                    value: formData.spo2,
                    status: 'final',
                    encounter_id: encounterId
                }));
            }

            // 6. Weight
            if (formData.weight) {
                promises.push(createObservation({
                    code: LOINC_CODES.WEIGHT,
                    value: formData.weight,
                    status: 'final',
                    encounter_id: encounterId
                }));
            }

            // 7. Height
            if (formData.height) {
                promises.push(createObservation({
                    code: LOINC_CODES.HEIGHT,
                    value: formData.height,
                    status: 'final',
                    encounter_id: encounterId
                }));
            }

            if (promises.length === 0) {
                setError("Preencha pelo menos um sinal vital.");
                return;
            }

            await Promise.all(promises);
            setSuccessMessage("Sinais vitais registrados com sucesso!");
            setFormData({}); // Clear form
            if (onSuccess) onSuccess();

        } catch (err) {
            console.error(err);
            setError("Erro ao salvar sinais vitais. Tente novamente.");
        }
    };

    return (
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: spacing.lg }}>
            <h3 style={{ margin: 0, color: colors.text.primary }}>Registrar Sinais Vitais</h3>

            {error && (
                <div style={{ padding: spacing.md, backgroundColor: `${colors.alert.critical}20`, color: colors.alert.critical, borderRadius: '4px' }}>
                    {error}
                </div>
            )}

            {successMessage && (
                <div style={{ padding: spacing.md, backgroundColor: `${colors.alert.success}20`, color: colors.alert.success, borderRadius: '4px' }}>
                    {successMessage}
                </div>
            )}

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: spacing.md }}>
                {/* Pressão Arterial */}
                <div style={{ gridColumn: '1 / -1', display: 'flex', gap: spacing.md }}>
                    <div style={{ flex: 1 }}>
                        <label style={{ display: 'block', marginBottom: spacing.xs, fontSize: '0.875rem', fontWeight: 500 }}>PA Sistólica (mmHg)</label>
                        <input
                            type="number"
                            value={formData.systolic || ''}
                            onChange={(e) => handleChange('systolic', e.target.value)}
                            style={{ width: '100%', padding: spacing.sm, borderRadius: '4px', border: `1px solid ${colors.border.default}` }}
                            placeholder="120"
                        />
                    </div>
                    <div style={{ flex: 1 }}>
                        <label style={{ display: 'block', marginBottom: spacing.xs, fontSize: '0.875rem', fontWeight: 500 }}>PA Diastólica (mmHg)</label>
                        <input
                            type="number"
                            value={formData.diastolic || ''}
                            onChange={(e) => handleChange('diastolic', e.target.value)}
                            style={{ width: '100%', padding: spacing.sm, borderRadius: '4px', border: `1px solid ${colors.border.default}` }}
                            placeholder="80"
                        />
                    </div>
                </div>

                {/* FC e FR */}
                <div>
                    <label style={{ display: 'block', marginBottom: spacing.xs, fontSize: '0.875rem', fontWeight: 500 }}>Freq. Cardíaca (bpm)</label>
                    <input
                        type="number"
                        value={formData.heartRate || ''}
                        onChange={(e) => handleChange('heartRate', e.target.value)}
                        style={{ width: '100%', padding: spacing.sm, borderRadius: '4px', border: `1px solid ${colors.border.medium}` }}
                        placeholder="75"
                    />
                </div>
                <div>
                    <label style={{ display: 'block', marginBottom: spacing.xs, fontSize: '0.875rem', fontWeight: 500 }}>Freq. Respiratória (rpm)</label>
                    <input
                        type="number"
                        value={formData.respiratoryRate || ''}
                        onChange={(e) => handleChange('respiratoryRate', e.target.value)}
                        style={{ width: '100%', padding: spacing.sm, borderRadius: '4px', border: `1px solid ${colors.border.medium}` }}
                        placeholder="16"
                    />
                </div>

                {/* Temp e SpO2 */}
                <div>
                    <label style={{ display: 'block', marginBottom: spacing.xs, fontSize: '0.875rem', fontWeight: 500 }}>Temperatura (°C)</label>
                    <input
                        type="number"
                        step="0.1"
                        value={formData.temperature || ''}
                        onChange={(e) => handleChange('temperature', e.target.value)}
                        style={{ width: '100%', padding: spacing.sm, borderRadius: '4px', border: `1px solid ${colors.border.medium}` }}
                        placeholder="36.5"
                    />
                </div>
                <div>
                    <label style={{ display: 'block', marginBottom: spacing.xs, fontSize: '0.875rem', fontWeight: 500 }}>Saturação O2 (%)</label>
                    <input
                        type="number"
                        value={formData.spo2 || ''}
                        onChange={(e) => handleChange('spo2', e.target.value)}
                        style={{ width: '100%', padding: spacing.sm, borderRadius: '4px', border: `1px solid ${colors.border.medium}` }}
                        placeholder="98"
                    />
                </div>

                {/* Peso e Altura */}
                <div>
                    <label style={{ display: 'block', marginBottom: spacing.xs, fontSize: '0.875rem', fontWeight: 500 }}>Peso (kg)</label>
                    <input
                        type="number"
                        step="0.1"
                        value={formData.weight || ''}
                        onChange={(e) => handleChange('weight', e.target.value)}
                        style={{ width: '100%', padding: spacing.sm, borderRadius: '4px', border: `1px solid ${colors.border.medium}` }}
                        placeholder="70.5"
                    />
                </div>
                <div>
                    <label style={{ display: 'block', marginBottom: spacing.xs, fontSize: '0.875rem', fontWeight: 500 }}>Altura (cm)</label>
                    <input
                        type="number"
                        value={formData.height || ''}
                        onChange={(e) => handleChange('height', e.target.value)}
                        style={{ width: '100%', padding: spacing.sm, borderRadius: '4px', border: `1px solid ${colors.border.medium}` }}
                        placeholder="175"
                    />
                </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: spacing.md }}>
                <Button type="submit" disabled={loading}>
                    {loading ? 'Salvando...' : 'Salvar Sinais Vitais'}
                </Button>
            </div>
        </form>
    );
};

export default VitalSignsForm;
