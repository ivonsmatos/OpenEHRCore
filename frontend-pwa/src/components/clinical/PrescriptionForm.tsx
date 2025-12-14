import React, { useState } from 'react';
import { useEncounters } from '../../hooks/useEncounters';
import { useIsMobile } from '../../hooks/useMediaQuery';
import Button from '../base/Button';
import { colors, spacing } from '../../theme/colors';

interface PrescriptionFormProps {
    encounterId?: string | null;
    patientId?: string;
    onSuccess?: () => void;
}

const COMMON_MEDICATIONS = [
    { code: '329526', display: 'Paracetamol 500mg' },
    { code: '328498', display: 'Dipirona 500mg' },
    { code: '197361', display: 'Amoxicilina 500mg' },
    { code: '310965', display: 'Ibuprofeno 400mg' },
    { code: '312133', display: 'Omeprazol 20mg' },
    { code: '311354', display: 'Losartana 50mg' },
    { code: '312936', display: 'Simvastatina 20mg' },
    { code: '311584', display: 'Metformina 500mg' },
];

export const PrescriptionForm: React.FC<PrescriptionFormProps> = ({ encounterId, patientId, onSuccess }) => {
    const { createPrescription, loading } = useEncounters();
    const isMobile = useIsMobile();

    const [selectedMedication, setSelectedMedication] = useState<string>('');
    const [customMedication, setCustomMedication] = useState<string>('');
    const [dosageInstruction, setDosageInstruction] = useState<string>('');
    const [status, setStatus] = useState<string>('active');

    // AI Interaction Check
    const [interactionAlerts, setInteractionAlerts] = useState<any[]>([]);
    const [checkingInteractions, setCheckingInteractions] = useState(false);

    const checkInteractions = async (medicationName: string) => {
        if (!medicationName || !patientId) return;

        try {
            setCheckingInteractions(true);
            setInteractionAlerts([]); // Clear previous

            const token = localStorage.getItem('token');
            const response = await fetch(`${import.meta.env.VITE_API_URL}/ai/interactions/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    new_medication: medicationName,
                    patient_id: patientId
                })
            });

            if (response.ok) {
                const data = await response.json();
                setInteractionAlerts(data.alerts || []);
            }
        } catch (err) {
            console.error("Failed to check interactions", err);
        } finally {
            setCheckingInteractions(false);
        }
    };

    // Trigger check when selecting dropdown
    const handleMedicationChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
        const val = e.target.value;
        setSelectedMedication(val);

        if (val && val !== 'other') {
            const med = COMMON_MEDICATIONS.find(c => c.code === val);
            if (med) checkInteractions(med.display);
        } else {
            setInteractionAlerts([]);
        }
    };

    const [error, setError] = useState<string | null>(null);
    const [successMessage, setSuccessMessage] = useState<string | null>(null);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);
        setSuccessMessage(null);

        let code = '';
        let display = '';

        if (selectedMedication === 'other') {
            if (!customMedication.trim()) {
                setError("Por favor, digite o nome do medicamento.");
                return;
            }
            code = '000000'; // Generic/Unknown code
            display = customMedication;
        } else if (selectedMedication) {
            const med = COMMON_MEDICATIONS.find(c => c.code === selectedMedication);
            if (med) {
                code = med.code;
                display = med.display;
            }
        } else {
            setError("Selecione um medicamento.");
            return;
        }

        if (!dosageInstruction.trim()) {
            setError("Por favor, informe a posologia.");
            return;
        }

        try {
            await createPrescription({
                medication_code: code,
                medication_display: display,
                dosage_instruction: dosageInstruction,
                status: status,
                intent: 'order',
                encounter_id: encounterId
            });

            setSuccessMessage("Prescrição registrada com sucesso!");
            setSelectedMedication('');
            setCustomMedication('');
            setDosageInstruction('');
            if (onSuccess) onSuccess();

        } catch (err) {
            console.error(err);
            setError("Erro ao salvar prescrição. Tente novamente.");
        }
    };

    const inputStyle = {
        width: '100%',
        padding: spacing.sm,
        borderRadius: '8px',
        border: `1px solid ${colors.border.default}`,
        fontSize: isMobile ? '16px' : '0.95rem',
        boxSizing: 'border-box' as const,
        transition: 'border-color 0.2s ease'
    };

    const labelStyle = {
        display: 'block',
        marginBottom: spacing.xs,
        fontSize: isMobile ? '0.9rem' : '0.875rem',
        fontWeight: 600,
        color: colors.text.primary
    };

    return (
        <form onSubmit={handleSubmit} style={{ 
            display: 'flex', 
            flexDirection: 'column', 
            gap: spacing.lg,
            maxWidth: '100%',
            padding: isMobile ? spacing.sm : 0
        }}>
            <h3 style={{ 
                margin: 0, 
                color: colors.text.primary,
                fontSize: isMobile ? '1.1rem' : '1.25rem'
            }}>
                Nova Prescrição
            </h3>

            {error && (
                <div style={{ 
                    padding: spacing.md, 
                    backgroundColor: `${colors.alert.critical}20`, 
                    color: colors.alert.critical, 
                    borderRadius: '8px',
                    fontSize: isMobile ? '0.875rem' : '0.9rem'
                }}>
                    {error}
                </div>
            )}

            {successMessage && (
                <div style={{ 
                    padding: spacing.md, 
                    backgroundColor: `${colors.alert.success}20`, 
                    color: colors.alert.success, 
                    borderRadius: '8px',
                    fontSize: isMobile ? '0.875rem' : '0.9rem'
                }}>
                    {successMessage}
                </div>
            )}

            <div style={{ display: 'flex', flexDirection: 'column', gap: spacing.md }}>
                {/* Medicamento */}
                <div>
                    <label style={labelStyle}>Medicamento</label>
                    <select
                        value={selectedMedication}
                        onChange={handleMedicationChange}
                        style={inputStyle}
                    >
                        <option value="">Selecione...</option>
                        {COMMON_MEDICATIONS.map(c => (
                            <option key={c.code} value={c.code}>{c.display}</option>
                        ))}
                        <option value="other">Outro (Digitar)</option>
                    </select>
                </div>

                {selectedMedication === 'other' && (
                    <div>
                        <label style={labelStyle}>Nome do Medicamento</label>
                        <input
                            type="text"
                            value={customMedication}
                            onChange={(e) => setCustomMedication(e.target.value)}
                            style={inputStyle}
                            placeholder="Ex: Cefalexina 500mg"
                        />
                    </div>
                )}

                {/* Interaction Alerts */}
                {checkingInteractions && (
                    <div style={{ fontSize: '0.8rem', color: colors.text.tertiary }}>
                        Verificando interações medicamentosas...
                    </div>
                )}

                {interactionAlerts.length > 0 && (
                    <div style={{
                        padding: spacing.md,
                        backgroundColor: '#FEF2F2',
                        border: `1px solid ${colors.alert.critical}`,
                        borderRadius: '6px'
                    }}>
                        <h4 style={{ margin: '0 0 8px 0', color: colors.alert.critical, fontSize: '0.9rem', display: 'flex', alignItems: 'center', gap: '6px' }}>
                            ⚠️ Alerta de Interação Medicamentosa
                        </h4>
                        <ul style={{ margin: 0, paddingLeft: '20px', fontSize: '0.85rem', color: colors.text.secondary }}>
                            {interactionAlerts.map((alert, idx) => (
                                <li key={idx} style={{ marginBottom: '4px' }}>
                                    <strong>{alert.title}:</strong> {alert.description}
                                </li>
                            ))}
                        </ul>
                    </div>
                )}

                {/* Posologia */}
                <div>
                    <label style={labelStyle}>Posologia / Instruções</label>
                    <textarea
                        value={dosageInstruction}
                        onChange={(e) => setDosageInstruction(e.target.value)}
                        style={{ 
                            ...inputStyle, 
                            minHeight: isMobile ? '80px' : '100px',
                            resize: 'vertical' as const
                        }}
                        placeholder="Ex: Tomar 1 comprimido via oral a cada 8 horas por 7 dias."
                    />
                </div>

                {/* Status */}
                <div>
                    <label style={labelStyle}>Status</label>
                    <select
                        value={status}
                        onChange={(e) => setStatus(e.target.value)}
                        style={inputStyle}
                    >
                        <option value="active">Ativo</option>
                        <option value="completed">Concluído</option>
                        <option value="stopped">Suspenso</option>
                    </select>
                </div>
            </div>

            <div style={{ 
                display: 'flex', 
                justifyContent: isMobile ? 'stretch' : 'flex-end', 
                marginTop: spacing.md 
            }}>
                <Button 
                    type="submit" 
                    disabled={loading}
                    style={{ 
                        width: isMobile ? '100%' : 'auto',
                        padding: spacing.md,
                        fontSize: isMobile ? '1rem' : '0.95rem'
                    }}
                >
                    {loading ? 'Salvando...' : 'Salvar Prescrição'}
                </Button>
            </div>
        </form>
    );
};

export default PrescriptionForm;
