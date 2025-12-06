
import React, { useEffect, useState } from 'react';
import { Sparkles, AlertTriangle, X } from 'lucide-react';
import { colors, spacing } from '../../theme/colors';
import Card from '../base/Card';

interface AICopilotProps {
    patientId: string;
    onClose?: () => void;
}

const AICopilot: React.FC<AICopilotProps> = ({ patientId, onClose }) => {
    const [summary, setSummary] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchSummary = async () => {
            try {
                setLoading(true);
                const token = localStorage.getItem('token');
                const response = await fetch(`${import.meta.env.VITE_API_URL}/ai/summary/${patientId}/`, {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });

                if (!response.ok) throw new Error('Falha ao gerar resumo');

                const data = await response.json();
                setSummary(data.summary);
            } catch (err) {
                setError("Não foi possível conectar ao o serviço de IA.");
                console.error(err);
            } finally {
                setLoading(false);
            }
        };

        if (patientId) {
            fetchSummary();
        }
    }, [patientId]);

    if (!patientId) return null;

    return (
        <Card padding="none" style={{
            background: 'linear-gradient(135deg, #EFF6FF 0%, #FFFFFF 100%)',
            border: `1px solid ${colors.primary.light}`,
            position: 'relative',
            overflow: 'hidden'
        }}>
            {/* Header */}
            <div style={{
                padding: spacing.md,
                borderBottom: `1px solid ${colors.primary.light}`,
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                background: 'rgba(255,255,255,0.5)'
            }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: spacing.sm }}>
                    <Sparkles size={18} color={colors.primary.medium} />
                    <h3 style={{ margin: 0, fontSize: '1rem', fontWeight: 600, color: colors.primary.dark }}>
                        Resumo Inteligente (AI)
                    </h3>
                </div>
                {onClose && (
                    <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', opacity: 0.5 }}>
                        <X size={16} />
                    </button>
                )}
            </div>

            {/* Content */}
            <div style={{ padding: spacing.md }}>
                {loading ? (
                    <div style={{ display: 'flex', alignItems: 'center', gap: spacing.sm, color: colors.text.tertiary, fontSize: '0.9rem' }}>
                        <span style={{ animation: 'spin 1s linear infinite' }}>⟳</span>
                        Gerando insights clínicos...
                    </div>
                ) : error ? (
                    <div style={{ display: 'flex', alignItems: 'center', gap: spacing.sm, color: colors.alert.warning, fontSize: '0.9rem' }}>
                        <AlertTriangle size={16} />
                        {error}
                    </div>
                ) : (
                    <div style={{
                        fontSize: '0.95rem',
                        lineHeight: '1.6',
                        color: colors.text.secondary,
                        whiteSpace: 'pre-line'
                    }}>
                        {summary}
                    </div>
                )}
            </div>

            {/* Footer Disclaimer */}
            <div style={{
                padding: '8px 16px',
                backgroundColor: 'rgba(255,255,255,0.5)',
                borderTop: `1px solid ${colors.primary.light}`,
                fontSize: '0.7rem',
                color: colors.text.tertiary,
                textAlign: 'center'
            }}>
                Os insights são gerados automaticamente. Valide com os dados originais.
            </div>
        </Card>
    );
};

export default AICopilot;
