import React, { useState } from 'react';
import { useEncounters } from '../../hooks/useEncounters';
import Button from '../base/Button';
import { colors, spacing } from '../../theme/colors';

interface AllergyFormProps {
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

export const AllergyForm: React.FC<AllergyFormProps> = ({ encounterId, onSuccess }) => {
    const { createAllergy, loading } = useEncounters();

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

    return (
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: spacing.lg }}>
            <h3 style={{ margin: 0, color: colors.text.primary }}>Registrar Alergia (AllergyIntolerance)</h3>

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
                {/* Alergia */}
                <div>
                    <label style={{ display: 'block', marginBottom: spacing.xs, fontSize: '0.875rem', fontWeight: 500 }}>Alergia</label>
                    <select
                        value={selectedAllergy}
                        onChange={(e) => setSelectedAllergy(e.target.value)}
                        style={{ width: '100%', padding: spacing.sm, borderRadius: '4px', border: `1px solid ${colors.border.default}` }}
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
                        <label style={{ display: 'block', marginBottom: spacing.xs, fontSize: '0.875rem', fontWeight: 500 }}>Nome da Alergia</label>
                        <input
                            type="text"
                            value={customAllergy}
                            onChange={(e) => setCustomAllergy(e.target.value)}
                            style={{ width: '100%', padding: spacing.sm, borderRadius: '4px', border: `1px solid ${colors.border.default}` }}
                            placeholder="Ex: Alergia a Gatos"
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
                            <option value="active">Ativa</option>
                            <option value="inactive">Inativa</option>
                            <option value="resolved">Resolvida</option>
                        </select>
                    </div>

                    {/* Criticalidade */}
                    <div>
                        <label style={{ display: 'block', marginBottom: spacing.xs, fontSize: '0.875rem', fontWeight: 500 }}>Severidade (Criticalidade)</label>
                        <select
                            value={criticality}
                            onChange={(e) => setCriticality(e.target.value)}
                            style={{ width: '100%', padding: spacing.sm, borderRadius: '4px', border: `1px solid ${colors.border.default}` }}
                        >
                            <option value="low">Baixa</option>
                            <option value="high">Alta</option>
                            <option value="unable-to-assess">Não avaliada</option>
                        </select>
                    </div>
                </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: spacing.md }}>
                <Button type="submit" disabled={loading}>
                    {loading ? 'Salvando...' : 'Salvar Alergia'}
                </Button>
            </div>
        </form>
    );
};

export default AllergyForm;
