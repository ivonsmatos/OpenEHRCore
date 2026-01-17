import React, { useState } from 'react';
import { useEncounters } from '../../hooks/useEncounters';
import { useIsMobile } from '../../hooks/useMediaQuery';
import Button from '../base/Button';
import { colors, spacing } from '../../theme/colors';
import AudioRecorder from '../ui/AudioRecorder';

interface SOAPNoteProps {
    patientId?: string;
    encounterId?: string | null;
    onSuccess?: () => void;
}

export const SOAPNote: React.FC<SOAPNoteProps> = ({ patientId, encounterId, onSuccess }) => {
    const { createSOAPNote, loading } = useEncounters(patientId);
    const isMobile = useIsMobile();

    // Single field for clinical notes
    const [clinicalNote, setClinicalNote] = useState<string>('');

    const [error, setError] = useState<string | null>(null);
    const [successMessage, setSuccessMessage] = useState<string | null>(null);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);
        setSuccessMessage(null);

        if (!clinicalNote.trim()) {
            setError("Preencha a nota clínica.");
            return;
        }

        try {
            const result = await createSOAPNote({
                summary: clinicalNote.trim(),
                status: 'completed',
                encounter_id: encounterId
            });

            console.log('Clinical Note created successfully:', result);
            setSuccessMessage("Nota de evolução salva com sucesso!");
            setClinicalNote('');
            if (onSuccess) onSuccess();

        } catch (err: any) {
            console.error('Error saving clinical note:', err);
            const errorMsg = err.message || "Erro ao salvar nota. Tente novamente.";
            setError(errorMsg);
        }
    };

    const handleDictation = (newText: string) => {
        setClinicalNote(prev => {
            const separator = prev.trim().length > 0 ? ' ' : '';
            return `${prev}${separator}${newText}`;
        });
    };

    const textareaStyle = {
        width: '100%',
        padding: spacing.md,
        borderRadius: '8px',
        border: `1px solid ${colors.border.default}`,
        minHeight: isMobile ? '250px' : '300px',
        fontFamily: 'inherit',
        fontSize: isMobile ? '16px' : '1rem',
        resize: 'vertical' as const,
        transition: 'border-color 0.2s ease',
        boxSizing: 'border-box' as const,
        lineHeight: '1.6'
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
                <div style={{ display: 'flex', alignItems: 'center', gap: spacing.sm }}>
                    <h3 style={{
                        margin: 0,
                        color: colors.text.primary,
                        fontSize: isMobile ? '1.1rem' : '1.25rem'
                    }}>
                        Nota de Evolução
                    </h3>
                </div>
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

            {/* Single clinical note field */}
            <div>
                <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    marginBottom: spacing.sm
                }}>
                    <span style={{
                        fontSize: isMobile ? '0.9rem' : '0.875rem',
                        fontWeight: 600,
                        color: colors.text.primary
                    }}>
                        Evolução Clínica
                    </span>
                    <AudioRecorder onTranscriptionComplete={handleDictation} />
                </div>
                <textarea
                    value={clinicalNote}
                    onChange={(e) => setClinicalNote(e.target.value)}
                    style={textareaStyle}
                    placeholder="Descreva a evolução do paciente: queixas, exame físico, hipóteses diagnósticas, conduta, prescrições e orientações..."
                />
                <p style={{
                    margin: `${spacing.xs} 0 0 0`,
                    fontSize: '0.75rem',
                    color: colors.text.secondary
                }}>
                    💡 Use o microfone para ditar sua nota ou digite livremente.
                </p>
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
