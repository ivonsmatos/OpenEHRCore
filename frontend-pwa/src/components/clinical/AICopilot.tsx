
import React, { useEffect, useState } from 'react';
import { Sparkles, AlertTriangle, X } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { colors, spacing } from '../../theme/colors';
import Card from '../base/Card';

import { useAuth } from '../../hooks/useAuth';

interface AICopilotProps {
    patientId: string;
    onClose?: () => void;
}

const AICopilot: React.FC<AICopilotProps> = ({ patientId, onClose }) => {
    const { token } = useAuth();
    const [summary, setSummary] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchSummary = async () => {
            try {
                setLoading(true);
                const response = await fetch(`${import.meta.env.VITE_API_URL}/ai/summary/${patientId}/`, {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });

                if (!response.ok) {
                    const errData = await response.json().catch(() => ({ error: 'Falha ao conectar' }));
                    throw new Error(errData.error || 'Falha ao gerar resumo');
                }

                const data = await response.json();
                setSummary(data.summary);
            } catch (err: any) {
                // If message contains "Patient not found" or "404", be specific
                let msg = err.message || "Não foi possível conectar ao serviço de IA.";
                if (msg.includes("404") || msg.includes("not found")) {
                    msg = "Paciente não encontrado. Verifique se o ID é válido.";
                }
                setError(msg);
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
                    <div className="ai-summary-content" style={{
                        fontSize: '0.95rem',
                        lineHeight: '1.6',
                        color: colors.text.secondary
                    }}>
                        <ReactMarkdown
                            components={{
                                // Custom rendering for better clinical display
                                strong: ({ children }) => (
                                    <strong style={{ color: colors.text.primary, fontWeight: 600 }}>{children}</strong>
                                ),
                                p: ({ children }) => (
                                    <p style={{ margin: '0.5rem 0' }}>{children}</p>
                                ),
                                ul: ({ children }) => (
                                    <ul style={{ margin: '0.25rem 0', paddingLeft: '1rem' }}>{children}</ul>
                                ),
                                li: ({ children }) => (
                                    <li style={{ margin: '0.15rem 0' }}>{children}</li>
                                )
                            }}
                        >
                            {summary || ''}
                        </ReactMarkdown>
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
