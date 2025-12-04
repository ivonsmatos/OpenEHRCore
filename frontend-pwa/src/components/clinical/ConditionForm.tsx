import React, { useState } from 'react';
import { useEncounters } from '../../hooks/useEncounters';
import Button from '../base/Button';
import { colors, spacing } from '../../theme/colors';

interface ConditionFormProps {
    encounterId?: string | null;
    onSuccess?: () => void;
}

const COMMON_CONDITIONS = [
    { code: '38341003', display: 'Hipertensão Arterial Sistêmica' },
    { code: '44054006', display: 'Diabetes Mellitus Tipo 2' },
    { code: '195967001', display: 'Asma Brônquica' },
    { code: '68566005', display: 'Infecção do Trato Urinário' },
    { code: '398057008', display: 'Cefaleia Tensional' },
    { code: '21897009', display: 'Ansiedade Generalizada' },
    { code: '370143000', display: 'Depressão Maior' },
    { code: '54760002', display: 'Obesidade' },
    { code: '43878008', display: 'Gastrite' },
    { code: '233604007', display: 'Pneumonia' },
];

export const ConditionForm: React.FC<ConditionFormProps> = ({ encounterId, onSuccess }) => {
    const { createCondition, loading } = useEncounters();

    const [selectedCondition, setSelectedCondition] = useState<string>('');
    const [customCondition, setCustomCondition] = useState<string>('');
    const [clinicalStatus, setClinicalStatus] = useState<string>('active');
    const [verificationStatus, setVerificationStatus] = useState<string>('confirmed');

    const [error, setError] = useState<string | null>(null);
    const [successMessage, setSuccessMessage] = useState<string | null>(null);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);
        setSuccessMessage(null);

        let code = '';
        let display = '';

        if (selectedCondition === 'other') {
            if (!customCondition.trim()) {
                setError("Por favor, digite o nome do diagnóstico.");
                return;
            }
            code = '74964007'; // Other (SNOMED) - Generic placeholder
            display = customCondition;
        } else if (selectedCondition) {
            const condition = COMMON_CONDITIONS.find(c => c.code === selectedCondition);
            if (condition) {
                code = condition.code;
                display = condition.display;
            }
        } else {
            setError("Selecione um diagnóstico.");
            return;
        }

        try {
            await createCondition({
                code,
                display,
                clinical_status: clinicalStatus,
                verification_status: verificationStatus,
                encounter_id: encounterId
            });

            setSuccessMessage("Diagnóstico registrado com sucesso!");
            setSelectedCondition('');
            setCustomCondition('');
            if (onSuccess) onSuccess();

        } catch (err) {
            console.error(err);
            setError("Erro ao salvar diagnóstico. Tente novamente.");
        }
    };

    return (
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: spacing.lg }}>
            <h3 style={{ margin: 0, color: colors.text.primary }}>Registrar Diagnóstico (Condition)</h3>

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
                {/* Diagnóstico */}
                <div>
                    <label style={{ display: 'block', marginBottom: spacing.xs, fontSize: '0.875rem', fontWeight: 500 }}>Diagnóstico</label>
                    <select
                        value={selectedCondition}
                        onChange={(e) => setSelectedCondition(e.target.value)}
                        style={{ width: '100%', padding: spacing.sm, borderRadius: '4px', border: `1px solid ${colors.border.default}` }}
                    >
                        <option value="">Selecione...</option>
                        {COMMON_CONDITIONS.map(c => (
                            <option key={c.code} value={c.code}>{c.display}</option>
                        ))}
                        <option value="other">Outro (Digitar)</option>
                    </select>
                </div>

                {selectedCondition === 'other' && (
                    <div>
                        <label style={{ display: 'block', marginBottom: spacing.xs, fontSize: '0.875rem', fontWeight: 500 }}>Nome do Diagnóstico</label>
                        <input
                            type="text"
                            value={customCondition}
                            onChange={(e) => setCustomCondition(e.target.value)}
                            style={{ width: '100%', padding: spacing.sm, borderRadius: '4px', border: `1px solid ${colors.border.default}` }}
                            placeholder="Ex: Gripe Sazonal"
                        />
                    </div>
                )}

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: spacing.md }}>
                    {/* Status Clínico */}
                    <div>
                        <label style={{ display: 'block', marginBottom: spacing.xs, fontSize: '0.875rem', fontWeight: 500 }}>Status Clínico</label>
                        <select
                            value={clinicalStatus}
                            onChange={(e) => setClinicalStatus(e.target.value)}
                            style={{ width: '100%', padding: spacing.sm, borderRadius: '4px', border: `1px solid ${colors.border.default}` }}
                        >
                            <option value="active">Ativo</option>
                            <option value="recurrence">Recorrência</option>
                            <option value="relapse">Recaída</option>
                            <option value="inactive">Inativo</option>
                            <option value="remission">Remissão</option>
                            <option value="resolved">Resolvido</option>
                        </select>
                    </div>

                    {/* Status de Verificação */}
                    <div>
                        <label style={{ display: 'block', marginBottom: spacing.xs, fontSize: '0.875rem', fontWeight: 500 }}>Status de Verificação</label>
                        <select
                            value={verificationStatus}
                            onChange={(e) => setVerificationStatus(e.target.value)}
                            style={{ width: '100%', padding: spacing.sm, borderRadius: '4px', border: `1px solid ${colors.border.default}` }}
                        >
                            <option value="confirmed">Confirmado</option>
                            <option value="provisional">Provisório</option>
                            <option value="differential">Diferencial</option>
                            <option value="unconfirmed">Não confirmado</option>
                            <option value="refuted">Refutado</option>
                        </select>
                    </div>
                </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: spacing.md }}>
                <Button type="submit" disabled={loading}>
                    {loading ? 'Salvando...' : 'Salvar Diagnóstico'}
                </Button>
            </div>
        </form>
    );
};

export default ConditionForm;
