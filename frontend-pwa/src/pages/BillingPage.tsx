// Billing Page - Coverage, Claims, and Financial Dashboard
// Sprint 30: Billing Completo

import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

interface BillingMetrics {
    total_claims: number;
    pending_claims: number;
    total_value: number;
    currency: string;
    active_coverages: number;
}

interface Claim {
    id: string;
    status: string;
    type: any;
    patient: any;
    created: string;
    total?: { value: number; currency: string };
    item?: any[];
}

interface Coverage {
    id: string;
    status: string;
    type: any;
    beneficiary: any;
    payor: any[];
    period?: { start: string; end?: string };
}

const BillingPage: React.FC = () => {
    const [metrics, setMetrics] = useState<BillingMetrics | null>(null);
    const [claims, setClaims] = useState<Claim[]>([]);
    const [coverages, setCoverages] = useState<Coverage[]>([]);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState<'dashboard' | 'claims' | 'coverage'>('dashboard');

    const getAuthHeaders = () => {
        const token = localStorage.getItem('access_token');
        return token ? { Authorization: `Bearer ${token}` } : {};
    };

    const fetchDashboard = useCallback(async () => {
        try {
            const headers = getAuthHeaders();
            const response = await axios.get(`${API_URL}/billing/dashboard/`, { headers });
            setMetrics(response.data.metrics);
            setClaims(response.data.recent_claims || []);
        } catch (error) {
            console.error('Error fetching billing dashboard:', error);
        }
    }, []);

    const fetchCoverages = useCallback(async () => {
        try {
            const headers = getAuthHeaders();
            const response = await axios.get(`${API_URL}/billing/coverage/`, { headers });
            setCoverages(response.data.results || []);
        } catch (error) {
            console.error('Error fetching coverages:', error);
        }
    }, []);

    useEffect(() => {
        const load = async () => {
            setLoading(true);
            await Promise.all([fetchDashboard(), fetchCoverages()]);
            setLoading(false);
        };
        load();
    }, [fetchDashboard, fetchCoverages]);

    const formatCurrency = (value: number, currency: string = 'BRL') => {
        return new Intl.NumberFormat('pt-BR', {
            style: 'currency',
            currency
        }).format(value);
    };

    const submitClaim = async (claimId: string) => {
        try {
            const headers = getAuthHeaders();
            const response = await axios.post(`${API_URL}/billing/claims/${claimId}/submit/`, {}, { headers });
            alert(`✅ ${response.data.message}`);
            await fetchDashboard();
        } catch (error) {
            console.error('Error submitting claim:', error);
            alert('❌ Erro ao enviar guia');
        }
    };

    if (loading) {
        return (
            <div className="billing-page" style={{ padding: '2rem', textAlign: 'center' }}>
                <p>Carregando faturamento...</p>
            </div>
        );
    }

    return (
        <div className="billing-page" style={{ padding: '2rem' }}>
            <h1 style={{ marginBottom: '1.5rem', color: '#1e3a5f' }}>
                💰 Faturamento
            </h1>

            {/* Tabs */}
            <div style={{ display: 'flex', gap: '1rem', marginBottom: '2rem' }}>
                {(['dashboard', 'claims', 'coverage'] as const).map((tab) => (
                    <button
                        key={tab}
                        onClick={() => setActiveTab(tab)}
                        style={{
                            padding: '0.75rem 1.5rem',
                            background: activeTab === tab ? '#1e3a5f' : 'white',
                            color: activeTab === tab ? 'white' : '#1e3a5f',
                            border: '2px solid #1e3a5f',
                            borderRadius: '8px',
                            cursor: 'pointer',
                            fontWeight: '600'
                        }}
                    >
                        {tab === 'dashboard' && '📊 Dashboard'}
                        {tab === 'claims' && '📋 Guias'}
                        {tab === 'coverage' && '🏥 Convênios'}
                    </button>
                ))}
            </div>

            {/* Dashboard Tab */}
            {activeTab === 'dashboard' && metrics && (
                <>
                    <div style={{
                        display: 'grid',
                        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                        gap: '1.5rem',
                        marginBottom: '2rem'
                    }}>
                        <MetricCard
                            label="Total de Guias"
                            value={metrics.total_claims.toString()}
                            icon="📋"
                            color="#3b82f6"
                        />
                        <MetricCard
                            label="Guias Pendentes"
                            value={metrics.pending_claims.toString()}
                            icon="⏳"
                            color="#f59e0b"
                        />
                        <MetricCard
                            label="Valor Total"
                            value={formatCurrency(metrics.total_value)}
                            icon="💵"
                            color="#10b981"
                        />
                        <MetricCard
                            label="Convênios Ativos"
                            value={metrics.active_coverages.toString()}
                            icon="🏥"
                            color="#8b5cf6"
                        />
                    </div>

                    <h2 style={{ color: '#1e3a5f', marginBottom: '1rem' }}>
                        📋 Guias Recentes
                    </h2>
                    <ClaimsTable claims={claims} onSubmit={submitClaim} />
                </>
            )}

            {/* Claims Tab */}
            {activeTab === 'claims' && (
                <>
                    <h2 style={{ color: '#1e3a5f', marginBottom: '1rem' }}>
                        📋 Todas as Guias
                    </h2>
                    <ClaimsTable claims={claims} onSubmit={submitClaim} />
                </>
            )}

            {/* Coverage Tab */}
            {activeTab === 'coverage' && (
                <>
                    <h2 style={{ color: '#1e3a5f', marginBottom: '1rem' }}>
                        🏥 Convênios Cadastrados
                    </h2>
                    <CoverageTable coverages={coverages} />
                </>
            )}
        </div>
    );
};

// Metric Card Component
const MetricCard: React.FC<{
    label: string;
    value: string;
    icon: string;
    color: string;
}> = ({ label, value, icon, color }) => (
    <div style={{
        background: 'white',
        borderRadius: '12px',
        padding: '1.5rem',
        boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
        borderLeft: `4px solid ${color}`
    }}>
        <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>{icon}</div>
        <p style={{ margin: 0, fontSize: '0.85rem', color: '#64748b' }}>{label}</p>
        <p style={{ margin: '0.25rem 0 0 0', fontSize: '1.5rem', fontWeight: 'bold', color }}>{value}</p>
    </div>
);

// Claims Table Component
const ClaimsTable: React.FC<{
    claims: Claim[];
    onSubmit: (id: string) => void;
}> = ({ claims, onSubmit }) => (
    <div style={{
        background: 'white',
        borderRadius: '12px',
        padding: '1rem',
        boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
        overflowX: 'auto'
    }}>
        {claims.length === 0 ? (
            <p style={{ textAlign: 'center', color: '#94a3b8', padding: '2rem' }}>
                Nenhuma guia registrada.
            </p>
        ) : (
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                    <tr style={{ borderBottom: '2px solid #e5e7eb' }}>
                        <th style={{ textAlign: 'left', padding: '0.75rem', color: '#64748b' }}>ID</th>
                        <th style={{ textAlign: 'left', padding: '0.75rem', color: '#64748b' }}>Tipo</th>
                        <th style={{ textAlign: 'left', padding: '0.75rem', color: '#64748b' }}>Paciente</th>
                        <th style={{ textAlign: 'left', padding: '0.75rem', color: '#64748b' }}>Valor</th>
                        <th style={{ textAlign: 'left', padding: '0.75rem', color: '#64748b' }}>Status</th>
                        <th style={{ textAlign: 'left', padding: '0.75rem', color: '#64748b' }}>Ações</th>
                    </tr>
                </thead>
                <tbody>
                    {claims.map((claim) => (
                        <tr key={claim.id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                            <td style={{ padding: '0.75rem', fontFamily: 'monospace', fontSize: '0.85rem' }}>
                                {claim.id?.slice(0, 8)}...
                            </td>
                            <td style={{ padding: '0.75rem' }}>
                                {claim.type?.coding?.[0]?.display || 'N/A'}
                            </td>
                            <td style={{ padding: '0.75rem' }}>
                                {claim.patient?.reference || 'N/A'}
                            </td>
                            <td style={{ padding: '0.75rem', fontWeight: 'bold', color: '#10b981' }}>
                                {claim.total ? `R$ ${claim.total.value.toFixed(2)}` : '-'}
                            </td>
                            <td style={{ padding: '0.75rem' }}>
                                <span style={{
                                    display: 'inline-block',
                                    padding: '0.25rem 0.5rem',
                                    borderRadius: '9999px',
                                    fontSize: '0.75rem',
                                    fontWeight: '600',
                                    background: claim.status === 'active' ? '#dbeafe' : '#d1fae5',
                                    color: claim.status === 'active' ? '#1e40af' : '#065f46'
                                }}>
                                    {claim.status}
                                </span>
                            </td>
                            <td style={{ padding: '0.75rem' }}>
                                <button
                                    onClick={() => onSubmit(claim.id)}
                                    style={{
                                        padding: '0.5rem 1rem',
                                        background: '#3b82f6',
                                        color: 'white',
                                        border: 'none',
                                        borderRadius: '6px',
                                        cursor: 'pointer',
                                        fontSize: '0.85rem'
                                    }}
                                >
                                    📤 Enviar
                                </button>
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        )}
    </div>
);

// Coverage Table Component
const CoverageTable: React.FC<{ coverages: Coverage[] }> = ({ coverages }) => (
    <div style={{
        background: 'white',
        borderRadius: '12px',
        padding: '1rem',
        boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
        overflowX: 'auto'
    }}>
        {coverages.length === 0 ? (
            <p style={{ textAlign: 'center', color: '#94a3b8', padding: '2rem' }}>
                Nenhum convênio cadastrado.
            </p>
        ) : (
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                    <tr style={{ borderBottom: '2px solid #e5e7eb' }}>
                        <th style={{ textAlign: 'left', padding: '0.75rem', color: '#64748b' }}>ID</th>
                        <th style={{ textAlign: 'left', padding: '0.75rem', color: '#64748b' }}>Tipo</th>
                        <th style={{ textAlign: 'left', padding: '0.75rem', color: '#64748b' }}>Beneficiário</th>
                        <th style={{ textAlign: 'left', padding: '0.75rem', color: '#64748b' }}>Operadora</th>
                        <th style={{ textAlign: 'left', padding: '0.75rem', color: '#64748b' }}>Status</th>
                    </tr>
                </thead>
                <tbody>
                    {coverages.map((coverage) => (
                        <tr key={coverage.id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                            <td style={{ padding: '0.75rem', fontFamily: 'monospace', fontSize: '0.85rem' }}>
                                {coverage.id?.slice(0, 8)}...
                            </td>
                            <td style={{ padding: '0.75rem' }}>
                                {coverage.type?.coding?.[0]?.display || 'N/A'}
                            </td>
                            <td style={{ padding: '0.75rem' }}>
                                {coverage.beneficiary?.reference || 'N/A'}
                            </td>
                            <td style={{ padding: '0.75rem' }}>
                                {coverage.payor?.[0]?.display || 'N/A'}
                            </td>
                            <td style={{ padding: '0.75rem' }}>
                                <span style={{
                                    display: 'inline-block',
                                    padding: '0.25rem 0.5rem',
                                    borderRadius: '9999px',
                                    fontSize: '0.75rem',
                                    fontWeight: '600',
                                    background: coverage.status === 'active' ? '#d1fae5' : '#fee2e2',
                                    color: coverage.status === 'active' ? '#065f46' : '#991b1b'
                                }}>
                                    {coverage.status === 'active' ? '✓ Ativo' : coverage.status}
                                </span>
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        )}
    </div>
);

export default BillingPage;
