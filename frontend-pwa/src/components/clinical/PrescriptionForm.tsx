import React, { useState } from 'react';
import { useEncounters } from '../../hooks/useEncounters';
import Button from '../base/Button';
import { colors, spacing } from '../../theme/colors';

interface PrescriptionFormProps {
    encounterId?: string | null;
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

export const PrescriptionForm: React.FC<PrescriptionFormProps> = ({ encounterId, onSuccess }) => {
    const { createPrescription, loading } = useEncounters();

    const [selectedMedication, setSelectedMedication] = useState<string>('');
    const [customMedication, setCustomMedication] = useState<string>('');
    const [dosageInstruction, setDosageInstruction] = useState<string>('');
    const [status, setStatus] = useState<string>('active');

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

    return (
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: spacing.lg }}>
            <h3 style={{ margin: 0, color: colors.text.primary }}>Nova Prescrição</h3>

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

            <div style={{ display: 'flex', flexDirection: 'column', gap: spacing.md }}>
                {/* Medicamento */}
                <div>
                    <label style={{ display: 'block', marginBottom: spacing.xs, fontSize: '0.875rem', fontWeight: 500 }}>Medicamento</label>
                    <select
                        value={selectedMedication}
                        onChange={(e) => setSelectedMedication(e.target.value)}
                        style={{ width: '100%', padding: spacing.sm, borderRadius: '4px', border: `1px solid ${colors.border.default}` }}
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
                        <label style={{ display: 'block', marginBottom: spacing.xs, fontSize: '0.875rem', fontWeight: 500 }}>Nome do Medicamento</label>
                        <input
                            type="text"
                            value={customMedication}
                            onChange={(e) => setCustomMedication(e.target.value)}
                            style={{ width: '100%', padding: spacing.sm, borderRadius: '4px', border: `1px solid ${colors.border.default}` }}
                            placeholder="Ex: Cefalexina 500mg"
                        />
                    </div>
                )}

                {/* Posologia */}
                <div>
                    <label style={{ display: 'block', marginBottom: spacing.xs, fontSize: '0.875rem', fontWeight: 500 }}>Posologia / Instruções</label>
                    <textarea
                        value={dosageInstruction}
                        onChange={(e) => setDosageInstruction(e.target.value)}
                        style={{ width: '100%', padding: spacing.sm, borderRadius: '4px', border: `1px solid ${colors.border.default}`, minHeight: '80px' }}
                        placeholder="Ex: Tomar 1 comprimido via oral a cada 8 horas por 7 dias."
                    />
                </div>

                {/* Status */}
                <div>
                    <label style={{ display: 'block', marginBottom: spacing.xs, fontSize: '0.875rem', fontWeight: 500 }}>Status</label>
                    <select
                        value={status}
                        onChange={(e) => setStatus(e.target.value)}
                        style={{ width: '100%', padding: spacing.sm, borderRadius: '4px', border: `1px solid ${colors.border.default}` }}
                    >
                        <option value="active">Ativo</option>
                        <option value="completed">Concluído</option>
                        <option value="stopped">Suspenso</option>
                    </select>
                </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: spacing.md }}>
                <Button type="submit" disabled={loading}>
                    {loading ? 'Salvando...' : 'Salvar Prescrição'}
                </Button>
            </div>
        </form>
    );
};

export default PrescriptionForm;
