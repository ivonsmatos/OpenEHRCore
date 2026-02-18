import React, { useState } from 'react';
import { useEncounters } from '../../hooks/useEncounters';
import { useIsMobile } from '../../hooks/useMediaQuery';
import Button from '../base/Button';
import { colors, spacing } from '../../theme/colors';
import AudioRecorder from '../ui/AudioRecorder';
import api from '../../api/client';

interface SOAPNoteProps {
    patientId?: string;
    encounterId?: string | null;
    onSuccess?: () => void;
}

interface CreatedResource {
    type: string;
    id: string;
    display: string;
}

export const SOAPNote: React.FC<SOAPNoteProps> = ({ patientId, encounterId, onSuccess }) => {
    const { createSOAPNote, loading } = useEncounters(patientId);
    const isMobile = useIsMobile();

    // Single field for clinical notes
    const [clinicalNote, setClinicalNote] = useState<string>('');
    const [isParsing, setIsParsing] = useState(false);

    const [error, setError] = useState<string | null>(null);
    const [successMessage, setSuccessMessage] = useState<string | null>(null);
    const [createdResources, setCreatedResources] = useState<CreatedResource[]>([]);

    const parseClinicalNote = async (text: string) => {
        if (!patientId || text.length < 20) return;

        setIsParsing(true);
        try {
            const response = await api.post('/ai/parse-clinical-note/', {
                text,
                patient_id: patientId,
                encounter_id: encounterId
            });

            if (response.data.resources_created?.length > 0) {
                setCreatedResources(response.data.resources_created);
            }
        } catch (err) {
            console.log('Clinical parsing skipped:', err);
            // Don't show error - parsing is optional enhancement
        } finally {
            setIsParsing(false);
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);
        setSuccessMessage(null);
        setCreatedResources([]);

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

            // Parse clinical note with AI to create FHIR resources
            await parseClinicalNote(clinicalNote.trim());

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

    const getResourceIcon = (type: string) => {
        switch (type) {
            case 'MedicationRequest': return '💊';
            case 'Condition': return '🏥';
            case 'ServiceRequest': return '🔬';
            case 'Observation': return '📊';
            default: return '📋';
        }
    };

    const getResourceLabel = (type: string) => {
        switch (type) {
            case 'MedicationRequest': return 'Prescrição';
            case 'Condition': return 'Diagnóstico';
            case 'ServiceRequest': return 'Exame';
            case 'Observation': return 'Sinal Vital';
            default: return type;
        }
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
                    {isParsing && (
                        <span style={{ fontSize: '0.75rem', color: colors.text.secondary }}>
                            🧠 Analisando com IA...
                        </span>
                    )}
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

            {/* Show created FHIR resources */}
            {createdResources.length > 0 && (
                <div style={{
                    padding: spacing.md,
                    backgroundColor: `${colors.primary.main}10`,
                    borderRadius: '8px',
                    border: `1px solid ${colors.primary.main}30`
                }}>
                    <p style={{
                        margin: `0 0 ${spacing.sm} 0`,
                        fontWeight: 600,
                        color: colors.text.primary,
                        fontSize: '0.9rem'
                    }}>
                        ✨ Recursos criados automaticamente:
                    </p>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: spacing.xs }}>
                        {createdResources.map((resource, idx) => (
                            <span key={idx} style={{
                                display: 'inline-flex',
                                alignItems: 'center',
                                gap: '4px',
                                padding: `${spacing.xs} ${spacing.sm}`,
                                backgroundColor: colors.background.paper,
                                borderRadius: '16px',
                                fontSize: '0.8rem',
                                color: colors.text.secondary
                            }}>
                                {getResourceIcon(resource.type)} {getResourceLabel(resource.type)}: {resource.display}
                            </span>
                        ))}
                    </div>
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
                    placeholder="Descreva a evolução do paciente: queixas, exame físico, hipóteses diagnósticas, conduta, prescrições e orientações. A IA irá extrair automaticamente medicamentos, exames e diagnósticos."
                />
                <p style={{
                    margin: `${spacing.xs} 0 0 0`,
                    fontSize: '0.75rem',
                    color: colors.text.secondary
                }}>
                    💡 Use o microfone para ditar. A IA preencherá automaticamente Prescrição, Exames e Diagnósticos.
                </p>
            </div>

            <div style={{
                display: 'flex',
                justifyContent: 'flex-end',
                marginTop: spacing.md
            }}>
                <Button
                    type="submit"
                    disabled={loading || isParsing}
                    style={{
                        width: isMobile ? '100%' : 'auto',
                        minWidth: isMobile ? '100%' : '150px'
                    }}
                >
                    {loading ? 'Salvando...' : isParsing ? '🧠 Analisando...' : 'Salvar Nota'}
                </Button>
            </div>
        </form>
    );
};

export default SOAPNote;
