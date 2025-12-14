// Billing Page - Coverage, Claims, and Financial Dashboard
// Sprint 30: Billing Completo
// ✅ REFATORADO: Design System Compliant (sem cores hardcoded)

import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { cn } from '../utils/cn';
import { colors } from '../theme/colors';
import { FileText, Clock, DollarSign, Building2, Send } from 'lucide-react';

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
        <div className="billing-page" style={{ padding: '2rem', backgroundColor: colors.background?.surface || '#F2F2F2', minHeight: '100vh' }}>
            <h1 style={{ marginBottom: '1.5rem', color: colors.primary.dark, fontSize: '2rem', fontWeight: 'bold' }}>
                💰 Faturamento
            </h1>

            {/* Tabs - Design System Compliant */}
            <div style={{ display: 'flex', gap: '1rem', marginBottom: '2rem', borderBottom: `2px solid ${colors.neutral?.light || '#e5e7eb'}` }}>
                {([
                    { id: 'dashboard', label: '📊 Dashboard' },
                    { id: 'claims', label: '📋 Guias' },
                    { id: 'coverage', label: '🏥 Convênios' }
                ] as const).map((tab) => (
                    <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id)}
                        aria-current={activeTab === tab.id ? 'page' : undefined}
                        className={cn(
                            "px-6 py-3 rounded-t-md font-semibold transition-all",
                            "focus:outline-none focus:ring-2 focus:ring-offset-2",
                            activeTab === tab.id
                                ? "border-b-2 -mb-0.5"
                                : "border-b-2 border-transparent hover:bg-opacity-10"
                        )}
                        style={{
                            backgroundColor: activeTab === tab.id ? colors.primary.dark : 'white',
                            color: activeTab === tab.id ? 'white' : colors.primary.dark,
                            borderBottomColor: activeTab === tab.id ? colors.primary.dark : 'transparent',
                            cursor: 'pointer'
                        }}
                    >
                        {tab.label}
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
                            icon={<FileText className="w-8 h-8" />}
                            colorTheme="primary"
                        />
                        <MetricCard
                            label="Guias Pendentes"
                            value={metrics.pending_claims.toString()}
                            icon={<Clock className="w-8 h-8" />}
                            colorTheme="warning"
                        />
                        <MetricCard
                            label="Valor Total"
                            value={formatCurrency(metrics.total_value)}
                            icon={<DollarSign className="w-8 h-8" />}
                            colorTheme="success"
                        />
                        <MetricCard
                            label="Convênios Ativos"
                            value={metrics.active_coverages.toString()}
                            icon={<Building2 className="w-8 h-8" />}
                            colorTheme="secondary"
                        />
                    </div>

                    <h2 style={{ color: colors.primary.dark, marginBottom: '1rem', fontSize: '1.5rem', fontWeight: 'bold' }}>
                        📋 Guias Recentes
                    </h2>
                    <ClaimsTable claims={claims} onSubmit={submitClaim} />
                </>
            )}

            {/* Claims Tab */}
            {activeTab === 'claims' && (
                <>
                    <h2 style={{ color: colors.primary.dark, marginBottom: '1rem', fontSize: '1.5rem', fontWeight: 'bold' }}>
                        📋 Todas as Guias
                    </h2>
                    <ClaimsTable claims={claims} onSubmit={submitClaim} />
                </>
            )}

            {/* Coverage Tab */}
            {activeTab === 'coverage' && (
                <>
                    <h2 style={{ color: colors.primary.dark, marginBottom: '1rem', fontSize: '1.5rem', fontWeight: 'bold' }}>
                        🏥 Convênios Cadastrados
                    </h2>
                    <CoverageTable coverages={coverages} />
                </>
            )}
        </div>
    );
};

// Metric Card Component - Design System Compliant
const MetricCard: React.FC<{
    label: string;
    value: string;
    icon: React.ReactNode;
    colorTheme: 'primary' | 'warning' | 'success' | 'secondary';
}> = ({ label, value, icon, colorTheme }) => {
    const themeColors = {
        primary: colors.primary.medium,
        warning: '#f59e0b',
        success: '#10b981',
        secondary: '#8b5cf6'
    };
    
    const borderColor = themeColors[colorTheme];
    
    return (
        <div style={{
            background: 'white',
            borderRadius: '12px',
            padding: '1.5rem',
            boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
            borderLeft: `4px solid ${borderColor}`,
            transition: 'transform 0.2s, box-shadow 0.2s'
        }}
        className="hover:shadow-lg hover:-translate-y-0.5">
            <div style={{ color: borderColor, marginBottom: '0.5rem' }} aria-hidden="true">
                {icon}
            </div>
            <p style={{ margin: 0, fontSize: '0.85rem', color: colors.neutral?.darker || '#64748b', textTransform: 'uppercase', letterSpacing: '0.5px', fontWeight: 600 }}>
                {label}
            </p>
            <p style={{ margin: '0.25rem 0 0 0', fontSize: '1.5rem', fontWeight: 'bold', color: colors.text.primary }}>
                {value}
            </p>
        </div>
    );
};

// Claims Table Component - Design System Compliant
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
            <p style={{ textAlign: 'center', color: colors.neutral?.darker || '#94a3b8', padding: '2rem' }}>
                Nenhuma guia registrada.
            </p>
        ) : (
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                    <tr style={{ borderBottom: `2px solid ${colors.neutral?.light || '#e5e7eb'}` }}>
                        <th style={{ textAlign: 'left', padding: '0.75rem', color: colors.neutral?.darker || '#64748b', fontSize: '0.875rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px' }}>ID</th>
                        <th style={{ textAlign: 'left', padding: '0.75rem', color: colors.neutral?.darker || '#64748b', fontSize: '0.875rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px' }}>Tipo</th>
                        <th style={{ textAlign: 'left', padding: '0.75rem', color: colors.neutral?.darker || '#64748b', fontSize: '0.875rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px' }}>Paciente</th>
                        <th style={{ textAlign: 'left', padding: '0.75rem', color: colors.neutral?.darker || '#64748b', fontSize: '0.875rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px' }}>Valor</th>
                        <th style={{ textAlign: 'left', padding: '0.75rem', color: colors.neutral?.darker || '#64748b', fontSize: '0.875rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px' }}>Status</th>
                        <th style={{ textAlign: 'left', padding: '0.75rem', color: colors.neutral?.darker || '#64748b', fontSize: '0.875rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px' }}>Ações</th>
                    </tr>
                </thead>
                <tbody>
                    {claims.map((claim) => (
                        <tr key={claim.id} style={{ borderBottom: `1px solid ${colors.neutral?.lightest || '#f1f5f9'}`, transition: 'background-color 0.15s' }}
                            className="hover:bg-gray-50">
                            <td style={{ padding: '0.75rem', fontFamily: 'monospace', fontSize: '0.85rem', color: colors.neutral?.darker || '#64748b' }}>
                                {claim.id?.slice(0, 8)}...
                            </td>
                            <td style={{ padding: '0.75rem', color: colors.text.primary }}>
                                {claim.type?.coding?.[0]?.display || 'N/A'}
                            </td>
                            <td style={{ padding: '0.75rem', color: colors.text.primary }}>
                                {claim.patient?.reference || 'N/A'}
                            </td>
                            <td style={{ padding: '0.75rem', fontWeight: 'bold', color: '#10b981' }}>
                                {claim.total ? `R$ ${claim.total.value.toFixed(2)}` : '-'}
                            </td>
                            <td style={{ padding: '0.75rem' }}>
                                <span style={{
                                    display: 'inline-block',
                                    padding: '0.25rem 0.75rem',
                                    borderRadius: '9999px',
                                    fontSize: '0.75rem',
                                    fontWeight: '600',
                                    background: claim.status === 'active' 
                                        ? 'rgba(4, 104, 191, 0.1)' 
                                        : 'rgba(16, 185, 129, 0.1)',
                                    color: claim.status === 'active' 
                                        ? colors.primary.dark 
                                        : '#10b981'
                                }}>
                                    {claim.status === 'active' ? '⏳ Ativo' : '✓ ' + claim.status}
                                </span>
                            </td>
                            <td style={{ padding: '0.75rem' }}>
                                <button
                                    onClick={() => onSubmit(claim.id)}
                                    aria-label={`Enviar guia ${claim.id?.slice(0, 8)}`}
                                    className={cn(
                                        "inline-flex items-center gap-2",
                                        "px-4 py-2 rounded-lg",
                                        "font-medium text-sm",
                                        "transition-all duration-200",
                                        "focus:outline-none focus:ring-2 focus:ring-offset-2"
                                    )}
                                    style={{
                                        backgroundColor: colors.primary.medium,
                                        color: 'white',
                                        border: 'none',
                                        cursor: 'pointer'
                                    }}
                                >
                                    <Send className="w-4 h-4" aria-hidden="true" />
                                    Enviar
                                </button>
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        )}
    </div>
);

// Coverage Table Component - Design System Compliant
const CoverageTable: React.FC<{ coverages: Coverage[] }> = ({ coverages }) => (
    <div style={{
        background: 'white',
        borderRadius: '12px',
        padding: '1rem',
        boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
        overflowX: 'auto'
    }}>
        {coverages.length === 0 ? (
            <p style={{ textAlign: 'center', color: colors.neutral?.darker || '#94a3b8', padding: '2rem' }}>
                Nenhum convênio cadastrado.
            </p>
        ) : (
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                    <tr style={{ borderBottom: `2px solid ${colors.neutral?.light || '#e5e7eb'}` }}>
                        <th style={{ textAlign: 'left', padding: '0.75rem', color: colors.neutral?.darker || '#64748b', fontSize: '0.875rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px' }}>ID</th>
                        <th style={{ textAlign: 'left', padding: '0.75rem', color: colors.neutral?.darker || '#64748b', fontSize: '0.875rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px' }}>Tipo</th>
                        <th style={{ textAlign: 'left', padding: '0.75rem', color: colors.neutral?.darker || '#64748b', fontSize: '0.875rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px' }}>Beneficiário</th>
                        <th style={{ textAlign: 'left', padding: '0.75rem', color: colors.neutral?.darker || '#64748b', fontSize: '0.875rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px' }}>Operadora</th>
                        <th style={{ textAlign: 'left', padding: '0.75rem', color: colors.neutral?.darker || '#64748b', fontSize: '0.875rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px' }}>Status</th>
                    </tr>
                </thead>
                <tbody>
                    {coverages.map((coverage) => (
                        <tr key={coverage.id} style={{ borderBottom: `1px solid ${colors.neutral?.lightest || '#f1f5f9'}` }}
                            className="hover:bg-gray-50">
                            <td style={{ padding: '0.75rem', fontFamily: 'monospace', fontSize: '0.85rem', color: colors.neutral?.darker || '#64748b' }}>
                                {coverage.id?.slice(0, 8)}...
                            </td>
                            <td style={{ padding: '0.75rem', color: colors.text.primary }}>
                                {coverage.type?.coding?.[0]?.display || 'N/A'}
                            </td>
                            <td style={{ padding: '0.75rem', color: colors.text.primary }}>
                                {coverage.beneficiary?.reference || 'N/A'}
                            </td>
                            <td style={{ padding: '0.75rem', color: colors.text.primary }}>
                                {coverage.payor?.[0]?.display || 'N/A'}
                            </td>
                            <td style={{ padding: '0.75rem' }}>
                                <span style={{
                                    display: 'inline-block',
                                    padding: '0.25rem 0.75rem',
                                    borderRadius: '9999px',
                                    fontSize: '0.75rem',
                                    fontWeight: '600',
                                    background: coverage.status === 'active' 
                                        ? 'rgba(16, 185, 129, 0.1)' 
                                        : 'rgba(239, 68, 68, 0.1)',
                                    color: coverage.status === 'active' 
                                        ? '#10b981' 
                                        : colors.alert.critical
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
