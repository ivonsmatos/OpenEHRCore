import React, { useState } from 'react';
import { useEncounters } from '../../hooks/useEncounters';
import { useIsMobile } from '../../hooks/useMediaQuery';
import Button from '../base/Button';
import { colors, spacing } from '../../theme/colors';

interface ConditionFormProps {
    patientId?: string;
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

export const ConditionForm: React.FC<ConditionFormProps> = ({ patientId, encounterId, onSuccess }) => {
    const { createCondition, loading } = useEncounters(patientId);
    const isMobile = useIsMobile();

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
                Registrar Diagnóstico (Condition)
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
                {/* Diagnóstico */}
                <div>
                    <label style={labelStyle}>Diagnóstico</label>
                    <select
                        value={selectedCondition}
                        onChange={(e) => setSelectedCondition(e.target.value)}
                        style={inputStyle}
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
                        <label style={labelStyle}>Nome do Diagnóstico</label>
                        <input
                            type="text"
                            value={customCondition}
                            onChange={(e) => setCustomCondition(e.target.value)}
                            style={inputStyle}
                            placeholder="Ex: Gripe Sazonal"
                        />
                    </div>
                )}

                <div style={{ 
                    display: 'grid', 
                    gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr', 
                    gap: spacing.md 
                }}>
                    {/* Status Clínico */}
                    <div>
                        <label style={labelStyle}>Status Clínico</label>
                        <select
                            value={clinicalStatus}
                            onChange={(e) => setClinicalStatus(e.target.value)}
                            style={inputStyle}
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
                        <label style={labelStyle}>Status de Verificação</label>
                        <select
                            value={verificationStatus}
                            onChange={(e) => setVerificationStatus(e.target.value)}
                            style={inputStyle}
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
                    {loading ? 'Salvando...' : 'Salvar Diagnóstico'}
                </Button>
            </div>
        </form>
    );
};

export default ConditionForm;
