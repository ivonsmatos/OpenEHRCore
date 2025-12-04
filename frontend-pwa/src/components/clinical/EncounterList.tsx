import React from 'react';
import { useEncounters } from '../../hooks/useEncounters';
import { colors, spacing, borderRadius } from '../../theme/colors';
import Card from '../base/Card';
import Button from '../base/Button';

interface EncounterListProps {
    patientId: string;
    onStartEncounter?: () => void;
}

const EncounterList: React.FC<EncounterListProps> = ({ patientId, onStartEncounter }) => {
    const { encounters, loading, error } = useEncounters(patientId);

    if (loading) {
        return <div style={{ padding: spacing.md, color: colors.text.secondary }}>Carregando atendimentos...</div>;
    }

    if (error) {
        return <div style={{ padding: spacing.md, color: colors.alert.critical }}>{error}</div>;
    }

    const formatDate = (dateString?: string) => {
        if (!dateString) return 'Data desconhecida';
        return new Date(dateString).toLocaleString('pt-BR');
    };

    return (
        <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: spacing.md }}>
                <h3 style={{ margin: 0, color: colors.text.secondary }}>Histórico de Atendimentos</h3>
                {onStartEncounter && (
                    <Button size="sm" onClick={onStartEncounter}>
                        + Iniciar Atendimento
                    </Button>
                )}
            </div>

            {encounters.length === 0 ? (
                <Card padding="md" style={{ textAlign: 'center', color: colors.text.tertiary }}>
                    Nenhum atendimento registrado.
                </Card>
            ) : (
                <div style={{ display: 'grid', gap: spacing.sm }}>
                    {encounters.map((encounter) => (
                        <Card key={encounter.id} padding="md" elevation="base">
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <div>
                                    <div style={{ fontWeight: 600, color: colors.text.primary }}>
                                        {encounter.type?.[0]?.text || 'Consulta'}
                                    </div>
                                    <div style={{ fontSize: '0.875rem', color: colors.text.secondary }}>
                                        {formatDate(encounter.period?.start)}
                                    </div>
                                </div>
                                <div style={{ textAlign: 'right' }}>
                                    <span style={{
                                        display: 'inline-block',
                                        padding: '2px 8px',
                                        borderRadius: borderRadius.sm,
                                        backgroundColor: encounter.status === 'finished' ? colors.alert.success : colors.alert.warning,
                                        color: '#FFFFFF', // Texto branco para contraste
                                        fontSize: '0.75rem',
                                        fontWeight: 600
                                    }}>
                                        {encounter.status === 'finished' ? 'Finalizado' : encounter.status}
                                    </span>
                                    {encounter.created_by && (
                                        <div style={{ fontSize: '0.75rem', color: colors.text.tertiary, marginTop: '4px' }}>
                                            Por: {encounter.created_by}
                                        </div>
                                    )}
                                </div>
                            </div>
                        </Card>
                    ))}
                </div>
            )}
        </div>
    );
};

export default EncounterList;
