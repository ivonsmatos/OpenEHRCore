import React, { useState, useEffect } from 'react';
import {
    TrendingUp, TrendingDown, DollarSign, CreditCard, FileText,
    Calendar, Users, PieChart, BarChart3, ArrowUpRight, ArrowDownRight,
    AlertCircle, CheckCircle, Clock, Building2
} from 'lucide-react';
import './FinancialDashboard.css';

interface FinancialMetrics {
    revenue: {
        current: number;
        previous: number;
        trend: 'up' | 'down';
        percentChange: number;
    };
    receivables: {
        overdue: number;
        pending: number;
        total: number;
    };
    invoices: {
        paid: number;
        pending: number;
        overdue: number;
        total: number;
    };
    coverage: {
        active: number;
        expiring: number;
        topProviders: { name: string; patients: number; revenue: number }[];
    };
    monthlyRevenue: { month: string; revenue: number; expenses: number }[];
    revenueBySource: { source: string; amount: number; percentage: number }[];
    recentTransactions: {
        id: string;
        type: 'payment' | 'invoice' | 'refund';
        description: string;
        amount: number;
        date: string;
        status: 'completed' | 'pending' | 'failed';
    }[];
}

const mockData: FinancialMetrics = {
    revenue: {
        current: 128450.00,
        previous: 115200.00,
        trend: 'up',
        percentChange: 11.5
    },
    receivables: {
        overdue: 12350.00,
        pending: 45200.00,
        total: 57550.00
    },
    invoices: {
        paid: 145,
        pending: 23,
        overdue: 8,
        total: 176
    },
    coverage: {
        active: 12,
        expiring: 3,
        topProviders: [
            { name: 'Unimed', patients: 234, revenue: 45200 },
            { name: 'Bradesco Saúde', patients: 156, revenue: 32100 },
            { name: 'SulAmérica', patients: 89, revenue: 18750 },
            { name: 'Amil', patients: 67, revenue: 14300 },
            { name: 'Porto Seguro', patients: 45, revenue: 9800 }
        ]
    },
    monthlyRevenue: [
        { month: 'Jul', revenue: 95000, expenses: 72000 },
        { month: 'Ago', revenue: 102000, expenses: 78000 },
        { month: 'Set', revenue: 98000, expenses: 75000 },
        { month: 'Out', revenue: 115000, expenses: 82000 },
        { month: 'Nov', revenue: 122000, expenses: 88000 },
        { month: 'Dez', revenue: 128450, expenses: 91000 }
    ],
    revenueBySource: [
        { source: 'Convênios', amount: 85000, percentage: 66 },
        { source: 'Particular', amount: 28000, percentage: 22 },
        { source: 'SUS', amount: 12000, percentage: 9 },
        { source: 'Outros', amount: 3450, percentage: 3 }
    ],
    recentTransactions: [
        { id: '1', type: 'payment', description: 'Pagamento Unimed - Lote 2024/12', amount: 15420.00, date: '2024-12-13', status: 'completed' },
        { id: '2', type: 'invoice', description: 'Fatura #INV-2024-1892', amount: 850.00, date: '2024-12-12', status: 'pending' },
        { id: '3', type: 'payment', description: 'Pagamento Particular - João Silva', amount: 320.00, date: '2024-12-12', status: 'completed' },
        { id: '4', type: 'invoice', description: 'Fatura #INV-2024-1891', amount: 1200.00, date: '2024-12-11', status: 'completed' },
        { id: '5', type: 'refund', description: 'Estorno - Procedimento cancelado', amount: -450.00, date: '2024-12-10', status: 'completed' }
    ]
};

const formatCurrency = (value: number): string => {
    return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL'
    }).format(value);
};

const formatDate = (dateStr: string): string => {
    return new Date(dateStr).toLocaleDateString('pt-BR');
};

export const FinancialDashboard: React.FC = () => {
    const [metrics, setMetrics] = useState<FinancialMetrics>(mockData);
    const [period, setPeriod] = useState<'week' | 'month' | 'quarter' | 'year'>('month');
    const [loading, setLoading] = useState(false);

    // Calculate max for chart scaling
    const maxRevenue = Math.max(...metrics.monthlyRevenue.map(m => m.revenue));

    return (
        <div className="financial-dashboard">
            {/* Header */}
            <div className="dashboard-header">
                <div className="header-title">
                    <h2>Dashboard Financeiro</h2>
                    <p>Visão geral da situação financeira</p>
                </div>
                <div className="period-selector">
                    <button
                        className={period === 'week' ? 'active' : ''}
                        onClick={() => setPeriod('week')}
                    >
                        Semana
                    </button>
                    <button
                        className={period === 'month' ? 'active' : ''}
                        onClick={() => setPeriod('month')}
                    >
                        Mês
                    </button>
                    <button
                        className={period === 'quarter' ? 'active' : ''}
                        onClick={() => setPeriod('quarter')}
                    >
                        Trimestre
                    </button>
                    <button
                        className={period === 'year' ? 'active' : ''}
                        onClick={() => setPeriod('year')}
                    >
                        Ano
                    </button>
                </div>
            </div>

            {/* KPI Cards */}
            <div className="kpi-grid">
                <div className="kpi-card revenue">
                    <div className="kpi-icon">
                        <DollarSign size={24} />
                    </div>
                    <div className="kpi-content">
                        <span className="kpi-label">Faturamento Total</span>
                        <span className="kpi-value">{formatCurrency(metrics.revenue.current)}</span>
                        <div className={`kpi-trend ${metrics.revenue.trend}`}>
                            {metrics.revenue.trend === 'up' ? (
                                <ArrowUpRight size={16} />
                            ) : (
                                <ArrowDownRight size={16} />
                            )}
                            <span>{metrics.revenue.percentChange}% vs mês anterior</span>
                        </div>
                    </div>
                </div>

                <div className="kpi-card receivables">
                    <div className="kpi-icon warning">
                        <Clock size={24} />
                    </div>
                    <div className="kpi-content">
                        <span className="kpi-label">A Receber</span>
                        <span className="kpi-value">{formatCurrency(metrics.receivables.total)}</span>
                        <div className="kpi-breakdown">
                            <span className="pending">{formatCurrency(metrics.receivables.pending)} pendente</span>
                            <span className="overdue">{formatCurrency(metrics.receivables.overdue)} vencido</span>
                        </div>
                    </div>
                </div>

                <div className="kpi-card invoices">
                    <div className="kpi-icon">
                        <FileText size={24} />
                    </div>
                    <div className="kpi-content">
                        <span className="kpi-label">Faturas do Mês</span>
                        <span className="kpi-value">{metrics.invoices.total}</span>
                        <div className="invoice-stats">
                            <span className="paid">
                                <CheckCircle size={14} /> {metrics.invoices.paid} pagas
                            </span>
                            <span className="pending">
                                <Clock size={14} /> {metrics.invoices.pending} pendentes
                            </span>
                            <span className="overdue">
                                <AlertCircle size={14} /> {metrics.invoices.overdue} vencidas
                            </span>
                        </div>
                    </div>
                </div>

                <div className="kpi-card coverage">
                    <div className="kpi-icon success">
                        <CreditCard size={24} />
                    </div>
                    <div className="kpi-content">
                        <span className="kpi-label">Convênios Ativos</span>
                        <span className="kpi-value">{metrics.coverage.active}</span>
                        {metrics.coverage.expiring > 0 && (
                            <div className="kpi-alert">
                                <AlertCircle size={14} />
                                <span>{metrics.coverage.expiring} expirando em breve</span>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Charts Row */}
            <div className="charts-grid">
                {/* Revenue Chart */}
                <div className="chart-card">
                    <div className="chart-header">
                        <h3><BarChart3 size={18} /> Faturamento vs Despesas</h3>
                        <span className="chart-period">Últimos 6 meses</span>
                    </div>
                    <div className="bar-chart">
                        {metrics.monthlyRevenue.map((item, index) => (
                            <div key={index} className="bar-group">
                                <div className="bars">
                                    <div
                                        className="bar revenue"
                                        style={{ height: `${(item.revenue / maxRevenue) * 100}%` }}
                                        title={formatCurrency(item.revenue)}
                                    />
                                    <div
                                        className="bar expenses"
                                        style={{ height: `${(item.expenses / maxRevenue) * 100}%` }}
                                        title={formatCurrency(item.expenses)}
                                    />
                                </div>
                                <span className="bar-label">{item.month}</span>
                            </div>
                        ))}
                    </div>
                    <div className="chart-legend">
                        <span className="legend-item revenue">
                            <span className="dot" /> Faturamento
                        </span>
                        <span className="legend-item expenses">
                            <span className="dot" /> Despesas
                        </span>
                    </div>
                </div>

                {/* Revenue by Source */}
                <div className="chart-card">
                    <div className="chart-header">
                        <h3><PieChart size={18} /> Receita por Fonte</h3>
                    </div>
                    <div className="donut-chart">
                        <div className="donut-container">
                            <svg viewBox="0 0 100 100" className="donut">
                                {metrics.revenueBySource.reduce((acc, item, index) => {
                                    const offset = acc.offset;
                                    const colors = ['#3b82f6', '#10b981', '#f59e0b', '#6b7280'];
                                    acc.elements.push(
                                        <circle
                                            key={index}
                                            cx="50"
                                            cy="50"
                                            r="40"
                                            fill="none"
                                            stroke={colors[index]}
                                            strokeWidth="12"
                                            strokeDasharray={`${item.percentage * 2.51} 251`}
                                            strokeDashoffset={-offset * 2.51}
                                            transform="rotate(-90 50 50)"
                                        />
                                    );
                                    acc.offset += item.percentage;
                                    return acc;
                                }, { elements: [] as JSX.Element[], offset: 0 }).elements}
                            </svg>
                            <div className="donut-center">
                                <span className="donut-total">{formatCurrency(metrics.revenue.current)}</span>
                                <span className="donut-label">Total</span>
                            </div>
                        </div>
                        <div className="donut-legend">
                            {metrics.revenueBySource.map((item, index) => {
                                const colors = ['#3b82f6', '#10b981', '#f59e0b', '#6b7280'];
                                return (
                                    <div key={index} className="legend-row">
                                        <span className="legend-color" style={{ backgroundColor: colors[index] }} />
                                        <span className="legend-name">{item.source}</span>
                                        <span className="legend-value">{formatCurrency(item.amount)}</span>
                                        <span className="legend-percent">{item.percentage}%</span>
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                </div>
            </div>

            {/* Bottom Row */}
            <div className="bottom-grid">
                {/* Top Providers */}
                <div className="providers-card">
                    <div className="card-header">
                        <h3><Building2 size={18} /> Top Convênios</h3>
                    </div>
                    <div className="providers-list">
                        {metrics.coverage.topProviders.map((provider, index) => (
                            <div key={index} className="provider-row">
                                <div className="provider-rank">{index + 1}</div>
                                <div className="provider-info">
                                    <span className="provider-name">{provider.name}</span>
                                    <span className="provider-patients">{provider.patients} pacientes</span>
                                </div>
                                <div className="provider-revenue">
                                    {formatCurrency(provider.revenue)}
                                </div>
                                <div className="provider-bar">
                                    <div
                                        className="bar-fill"
                                        style={{
                                            width: `${(provider.revenue / metrics.coverage.topProviders[0].revenue) * 100}%`
                                        }}
                                    />
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Recent Transactions */}
                <div className="transactions-card">
                    <div className="card-header">
                        <h3><FileText size={18} /> Últimas Transações</h3>
                        <button className="view-all-btn">Ver todas</button>
                    </div>
                    <div className="transactions-list">
                        {metrics.recentTransactions.map((tx) => (
                            <div key={tx.id} className={`transaction-row ${tx.type}`}>
                                <div className={`tx-icon ${tx.type}`}>
                                    {tx.type === 'payment' && <ArrowDownRight size={16} />}
                                    {tx.type === 'invoice' && <FileText size={16} />}
                                    {tx.type === 'refund' && <ArrowUpRight size={16} />}
                                </div>
                                <div className="tx-info">
                                    <span className="tx-description">{tx.description}</span>
                                    <span className="tx-date">{formatDate(tx.date)}</span>
                                </div>
                                <div className="tx-amount-wrapper">
                                    <span className={`tx-amount ${tx.amount < 0 ? 'negative' : ''}`}>
                                        {tx.amount < 0 ? '-' : '+'}{formatCurrency(Math.abs(tx.amount))}
                                    </span>
                                    <span className={`tx-status ${tx.status}`}>
                                        {tx.status === 'completed' && 'Concluído'}
                                        {tx.status === 'pending' && 'Pendente'}
                                        {tx.status === 'failed' && 'Falhou'}
                                    </span>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default FinancialDashboard;
