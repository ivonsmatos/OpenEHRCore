import React, { useState } from 'react';
import { useEncounters } from '../../hooks/useEncounters';
import { useIsMobile } from '../../hooks/useMediaQuery';
import Button from '../base/Button';
import { colors, spacing } from '../../theme/colors';

interface SOAPNoteProps {
    patientId?: string;
    encounterId?: string | null;
    onSuccess?: () => void;
}

export const SOAPNote: React.FC<SOAPNoteProps> = ({ patientId, encounterId, onSuccess }) => {
    const { createSOAPNote, loading } = useEncounters(patientId);
    const isMobile = useIsMobile();

    const [subjective, setSubjective] = useState<string>('');
    const [objective, setObjective] = useState<string>('');
    const [assessment, setAssessment] = useState<string>('');
    const [plan, setPlan] = useState<string>('');

    const [error, setError] = useState<string | null>(null);
    const [successMessage, setSuccessMessage] = useState<string | null>(null);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);
        setSuccessMessage(null);

        if (!subjective && !objective && !assessment && !plan) {
            setError("Preencha pelo menos um dos campos da nota.");
            return;
        }

        const summary = `
S (Subjetivo):
${subjective || '-'}

O (Objetivo):
${objective || '-'}

A (Avaliação):
${assessment || '-'}

P (Plano):
${plan || '-'}
        `.trim();

        try {
            const result = await createSOAPNote({
                summary: summary,
                status: 'completed',
                encounter_id: encounterId
            });

            console.log('SOAP Note created successfully:', result);
            setSuccessMessage("Nota de evolução salva com sucesso!");
            setSubjective('');
            setObjective('');
            setAssessment('');
            setPlan('');
            if (onSuccess) onSuccess();

        } catch (err: any) {
            console.error('Error saving SOAP note:', err);
            const errorMsg = err.message || "Erro ao salvar nota. Tente novamente.";
            setError(errorMsg);
        }
    };

    const textareaStyle = {
        width: '100%',
        padding: spacing.sm,
        borderRadius: '8px',
        border: `1px solid ${colors.border.default}`,
        minHeight: isMobile ? '100px' : '120px',
        fontFamily: 'inherit',
        fontSize: isMobile ? '16px' : '0.95rem', // 16px no mobile evita zoom automático no iOS
        resize: 'vertical' as const,
        transition: 'border-color 0.2s ease',
        boxSizing: 'border-box' as const
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
            <div style={{ 
                display: 'flex', 
                flexDirection: isMobile ? 'column' : 'row',
                justifyContent: 'space-between', 
                alignItems: isMobile ? 'flex-start' : 'center',
                gap: spacing.xs
            }}>
                <h3 style={{ 
                    margin: 0, 
                    color: colors.text.primary,
                    fontSize: isMobile ? '1.1rem' : '1.25rem'
                }}>
                    Nota de Evolução (SOAP)
                </h3>
                <span style={{ 
                    fontSize: '0.75rem', 
                    color: colors.text.secondary 
                }}>
                    {new Date().toLocaleDateString()}
                </span>
            </div>

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

            {/* Layout vertical: um campo embaixo do outro */}
            <div style={{ 
                display: 'flex', 
                flexDirection: 'column', 
                gap: spacing.lg 
            }}>
                {/* Subjective */}
                <div>
                    <label style={labelStyle}>S - Subjetivo</label>
                    <textarea
                        value={subjective}
                        onChange={(e) => setSubjective(e.target.value)}
                        style={textareaStyle}
                        placeholder="Queixas do paciente, história da moléstia atual..."
                    />
                </div>

                {/* Objective */}
                <div>
                    <label style={labelStyle}>O - Objetivo</label>
                    <textarea
                        value={objective}
                        onChange={(e) => setObjective(e.target.value)}
                        style={textareaStyle}
                        placeholder="Exame físico, resultados de exames..."
                    />
                </div>

                {/* Assessment */}
                <div>
                    <label style={labelStyle}>A - Avaliação</label>
                    <textarea
                        value={assessment}
                        onChange={(e) => setAssessment(e.target.value)}
                        style={textareaStyle}
                        placeholder="Hipóteses diagnósticas, análise do caso..."
                    />
                </div>

                {/* Plan */}
                <div>
                    <label style={labelStyle}>P - Plano</label>
                    <textarea
                        value={plan}
                        onChange={(e) => setPlan(e.target.value)}
                        style={textareaStyle}
                        placeholder="Conduta, prescrições, solicitações, orientações..."
                    />
                </div>
            </div>

            <div style={{ 
                display: 'flex', 
                justifyContent: 'flex-end', 
                marginTop: spacing.md 
            }}>
                <Button 
                    type="submit" 
                    disabled={loading}
                    style={{ 
                        width: isMobile ? '100%' : 'auto',
                        minWidth: isMobile ? '100%' : '150px'
                    }}
                >
                    {loading ? 'Salvando...' : 'Salvar Nota'}
                </Button>
            </div>
        </form>
    );
};

export default SOAPNote;
