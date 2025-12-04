import React, { useState } from 'react';
import { useEncounters } from '../../hooks/useEncounters';
import Button from '../base/Button';
import { colors, spacing } from '../../theme/colors';

interface ExamFormProps {
    encounterId?: string | null;
    onSuccess?: () => void;
}

const COMMON_EXAMS = [
    { code: '58410-2', display: 'Hemograma Completo' },
    { code: '1558-6', display: 'Glicemia de Jejum' },
    { code: '2093-3', display: 'Colesterol Total' },
    { code: '2571-8', display: 'Triglicerídeos' },
    { code: '3016-3', display: 'TSH' },
    { code: '3024-7', display: 'T4 Livre' },
    { code: '24356-8', display: 'Urina Tipo 1' },
    { code: '630-4', display: 'Urocultura' },
    { code: '36642-7', display: 'Raio-X de Tórax' },
    { code: '11524-6', display: 'Eletrocardiograma' },
];

export const ExamForm: React.FC<ExamFormProps> = ({ encounterId, onSuccess }) => {
    const { createExam, loading } = useEncounters();

    const [selectedExam, setSelectedExam] = useState<string>('');
    const [customExam, setCustomExam] = useState<string>('');
    const [status, setStatus] = useState<string>('active');

    const [error, setError] = useState<string | null>(null);
    const [successMessage, setSuccessMessage] = useState<string | null>(null);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);
        setSuccessMessage(null);

        let code = '';
        let display = '';

        if (selectedExam === 'other') {
            if (!customExam.trim()) {
                setError("Por favor, digite o nome do exame.");
                return;
            }
            code = '000000'; // Generic/Unknown code
            display = customExam;
        } else if (selectedExam) {
            const exam = COMMON_EXAMS.find(c => c.code === selectedExam);
            if (exam) {
                code = exam.code;
                display = exam.display;
            }
        } else {
            setError("Selecione um exame.");
            return;
        }

        try {
            await createExam({
                code: code,
                display: display,
                status: status,
                intent: 'order',
                encounter_id: encounterId
            });

            setSuccessMessage("Exame solicitado com sucesso!");
            setSelectedExam('');
            setCustomExam('');
            if (onSuccess) onSuccess();

        } catch (err) {
            console.error(err);
            setError("Erro ao solicitar exame. Tente novamente.");
        }
    };

    return (
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: spacing.lg }}>
            <h3 style={{ margin: 0, color: colors.text.primary }}>Solicitação de Exames</h3>

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
                {/* Exame */}
                <div>
                    <label style={{ display: 'block', marginBottom: spacing.xs, fontSize: '0.875rem', fontWeight: 500 }}>Exame</label>
                    <select
                        value={selectedExam}
                        onChange={(e) => setSelectedExam(e.target.value)}
                        style={{ width: '100%', padding: spacing.sm, borderRadius: '4px', border: `1px solid ${colors.border.default}` }}
                    >
                        <option value="">Selecione...</option>
                        {COMMON_EXAMS.map(c => (
                            <option key={c.code} value={c.code}>{c.display}</option>
                        ))}
                        <option value="other">Outro (Digitar)</option>
                    </select>
                </div>

                {selectedExam === 'other' && (
                    <div>
                        <label style={{ display: 'block', marginBottom: spacing.xs, fontSize: '0.875rem', fontWeight: 500 }}>Nome do Exame</label>
                        <input
                            type="text"
                            value={customExam}
                            onChange={(e) => setCustomExam(e.target.value)}
                            style={{ width: '100%', padding: spacing.sm, borderRadius: '4px', border: `1px solid ${colors.border.default}` }}
                            placeholder="Ex: Ressonância Magnética de Crânio"
                        />
                    </div>
                )}

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
                        <option value="revoked">Cancelado</option>
                    </select>
                </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: spacing.md }}>
                <Button type="submit" disabled={loading}>
                    {loading ? 'Enviando...' : 'Solicitar Exame'}
                </Button>
            </div>
        </form>
    );
};

export default ExamForm;
