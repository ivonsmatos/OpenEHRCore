import React, { useState } from 'react';
import { useEncounters } from '../../hooks/useEncounters';
import { useIsMobile } from '../../hooks/useMediaQuery';
import Button from '../base/Button';
import { colors, spacing } from '../../theme/colors';

interface AllergyFormProps {
    patientId?: string;
    encounterId?: string | null;
    onSuccess?: () => void;
}

const COMMON_ALLERGIES = [
    { code: '91936005', display: 'Alergia a Penicilina' },
    { code: '294363003', display: 'Alergia a Dipirona' },
    { code: '293596007', display: 'Alergia a Ibuprofeno' },
    { code: '300916003', display: 'Alergia a Látex' },
    { code: '91935009', display: 'Alergia a Amendoim' },
    { code: '227313005', display: 'Alergia a Leite de Vaca' },
    { code: '227493005', display: 'Alergia a Frutos do Mar' },
    { code: '260147004', display: 'Alergia a Poeira Doméstica' },
    { code: '256277009', display: 'Alergia a Pólen' },
];

export const AllergyForm: React.FC<AllergyFormProps> = ({ patientId, encounterId, onSuccess }) => {
    const { createAllergy, loading } = useEncounters(patientId);
    const isMobile = useIsMobile();

    const [selectedAllergy, setSelectedAllergy] = useState<string>('');
    const [customAllergy, setCustomAllergy] = useState<string>('');
    const [clinicalStatus, setClinicalStatus] = useState<string>('active');
    const [criticality, setCriticality] = useState<string>('low');

    const [error, setError] = useState<string | null>(null);
    const [successMessage, setSuccessMessage] = useState<string | null>(null);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);
        setSuccessMessage(null);

        let code = '';
        let display = '';

        if (selectedAllergy === 'other') {
            if (!customAllergy.trim()) {
                setError("Por favor, digite o nome da alergia.");
                return;
            }
            code = '419199007'; // Allergy to substance (SNOMED) - Generic placeholder
            display = customAllergy;
        } else if (selectedAllergy) {
            const allergy = COMMON_ALLERGIES.find(c => c.code === selectedAllergy);
            if (allergy) {
                code = allergy.code;
                display = allergy.display;
            }
        } else {
            setError("Selecione uma alergia.");
            return;
        }

        try {
            await createAllergy({
                code,
                display,
                clinical_status: clinicalStatus,
                criticality: criticality,
                encounter_id: encounterId
            });

            setSuccessMessage("Alergia registrada com sucesso!");
            setSelectedAllergy('');
            setCustomAllergy('');
            if (onSuccess) onSuccess();

        } catch (err) {
            console.error(err);
            setError("Erro ao salvar alergia. Tente novamente.");
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
                Registrar Alergia (AllergyIntolerance)
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
                {/* Alergia */}
                <div>
                    <label style={labelStyle}>Alergia</label>
                    <select
                        value={selectedAllergy}
                        onChange={(e) => setSelectedAllergy(e.target.value)}
                        style={inputStyle}
                    >
                        <option value="">Selecione...</option>
                        {COMMON_ALLERGIES.map(c => (
                            <option key={c.code} value={c.code}>{c.display}</option>
                        ))}
                        <option value="other">Outra (Digitar)</option>
                    </select>
                </div>

                {selectedAllergy === 'other' && (
                    <div>
                        <label style={labelStyle}>Nome da Alergia</label>
                        <input
                            type="text"
                            value={customAllergy}
                            onChange={(e) => setCustomAllergy(e.target.value)}
                            style={inputStyle}
                            placeholder="Ex: Alergia a Mofo"
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
                            <option value="active">Ativa</option>
                            <option value="inactive">Inativa</option>
                            <option value="resolved">Resolvida</option>
                        </select>
                    </div>

                    {/* Criticalidade */}
                    <div>
                        <label style={labelStyle}>Criticidade</label>
                        <select
                            value={criticality}
                            onChange={(e) => setCriticality(e.target.value)}
                            style={inputStyle}
                        >
                            <option value="low">Baixa</option>
                            <option value="high">Alta</option>
                            <option value="unable-to-assess">Não avaliada</option>
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
                    {loading ? 'Salvando...' : 'Salvar Alergia'}
                </Button>
            </div>
        </form>
    );
};

export default AllergyForm;
