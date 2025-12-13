// Automation Page - Bots and Subscriptions Management
// Sprint 29: Bots/Automation

import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

interface Bot {
    id: string;
    name: string;
    description: string;
    trigger_type: string;
    enabled: boolean;
    status: string;
    last_run: string | null;
    run_count: number;
    error_count: number;
}

interface ExecutionResult {
    bot_id: string;
    success: boolean;
    result?: any;
    error?: string;
    logs: string[];
    duration_ms: number;
    timestamp: string;
}

const AutomationPage: React.FC = () => {
    const [bots, setBots] = useState<Bot[]>([]);
    const [history, setHistory] = useState<ExecutionResult[]>([]);
    const [loading, setLoading] = useState(true);
    const [executing, setExecuting] = useState<string | null>(null);
    const [selectedBot, setSelectedBot] = useState<string | null>(null);

    const getAuthHeaders = () => {
        const token = localStorage.getItem('access_token');
        return token ? { Authorization: `Bearer ${token}` } : {};
    };

    const fetchBots = useCallback(async () => {
        try {
            const headers = getAuthHeaders();
            const response = await axios.get(`${API_URL}/bots/`, { headers });
            setBots(response.data.results || []);
        } catch (error) {
            console.error('Error fetching bots:', error);
        }
    }, []);

    const fetchHistory = useCallback(async () => {
        try {
            const headers = getAuthHeaders();
            const response = await axios.get(`${API_URL}/bots/history/`, { headers });
            setHistory(response.data.results || []);
        } catch (error) {
            console.error('Error fetching history:', error);
        }
    }, []);

    useEffect(() => {
        const load = async () => {
            setLoading(true);
            await Promise.all([fetchBots(), fetchHistory()]);
            setLoading(false);
        };
        load();
    }, [fetchBots, fetchHistory]);

    const executeBot = async (botId: string) => {
        setExecuting(botId);
        try {
            const headers = getAuthHeaders();
            const response = await axios.post(
                `${API_URL}/bots/${botId}/execute/`,
                {},
                { headers }
            );

            // Refresh history
            await fetchHistory();

            alert(response.data.success ? '✅ Bot executado com sucesso!' : `❌ Erro: ${response.data.error}`);
        } catch (error) {
            console.error('Error executing bot:', error);
            alert('Erro ao executar bot');
        } finally {
            setExecuting(null);
        }
    };

    const toggleBot = async (botId: string, enabled: boolean) => {
        try {
            const headers = getAuthHeaders();
            await axios.put(
                `${API_URL}/bots/${botId}/`,
                { enabled },
                { headers }
            );
            await fetchBots();
        } catch (error) {
            console.error('Error toggling bot:', error);
        }
    };

    const getTriggerIcon = (trigger: string) => {
        switch (trigger) {
            case 'resource-create': return '➕';
            case 'resource-update': return '✏️';
            case 'schedule': return '⏰';
            case 'webhook': return '🔗';
            default: return '🤖';
        }
    };

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'running': return '#3b82f6';
            case 'completed': return '#10b981';
            case 'failed': return '#ef4444';
            default: return '#6b7280';
        }
    };

    if (loading) {
        return (
            <div className="automation-page" style={{ padding: '2rem', textAlign: 'center' }}>
                <p>Carregando automações...</p>
            </div>
        );
    }

    return (
        <div className="automation-page" style={{ padding: '2rem' }}>
            <h1 style={{ marginBottom: '1.5rem', color: '#1e3a5f' }}>
                🤖 Automações (Bots)
            </h1>

            <p style={{ color: '#64748b', marginBottom: '2rem' }}>
                Gerencie bots que executam automaticamente em resposta a eventos do sistema.
            </p>

            {/* Bots Grid */}
            <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))',
                gap: '1.5rem',
                marginBottom: '3rem'
            }}>
                {bots.map((bot) => (
                    <div
                        key={bot.id}
                        style={{
                            background: 'white',
                            borderRadius: '12px',
                            padding: '1.5rem',
                            boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
                            border: bot.enabled ? '2px solid #10b981' : '2px solid #e5e7eb'
                        }}
                    >
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
                            <div>
                                <h3 style={{ margin: 0, fontSize: '1.1rem', color: '#1e3a5f' }}>
                                    {getTriggerIcon(bot.trigger_type)} {bot.name}
                                </h3>
                                <p style={{ margin: '0.5rem 0 0 0', fontSize: '0.85rem', color: '#64748b' }}>
                                    {bot.description}
                                </p>
                            </div>
                            <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
                                <input
                                    type="checkbox"
                                    checked={bot.enabled}
                                    onChange={(e) => toggleBot(bot.id, e.target.checked)}
                                    style={{ marginRight: '0.5rem' }}
                                />
                                <span style={{ fontSize: '0.75rem', color: bot.enabled ? '#10b981' : '#6b7280' }}>
                                    {bot.enabled ? 'Ativo' : 'Inativo'}
                                </span>
                            </label>
                        </div>

                        <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem', fontSize: '0.8rem', color: '#64748b' }}>
                            <span>Trigger: <strong>{bot.trigger_type}</strong></span>
                            <span>
                                Status:
                                <span style={{ color: getStatusColor(bot.status), marginLeft: '0.25rem' }}>
                                    {bot.status}
                                </span>
                            </span>
                        </div>

                        <div style={{ display: 'flex', gap: '1.5rem', marginBottom: '1rem', fontSize: '0.85rem' }}>
                            <div>
                                <span style={{ color: '#10b981', fontWeight: 'bold' }}>{bot.run_count}</span>
                                <span style={{ color: '#64748b', marginLeft: '0.25rem' }}>execuções</span>
                            </div>
                            <div>
                                <span style={{ color: '#ef4444', fontWeight: 'bold' }}>{bot.error_count}</span>
                                <span style={{ color: '#64748b', marginLeft: '0.25rem' }}>erros</span>
                            </div>
                        </div>

                        {bot.last_run && (
                            <p style={{ fontSize: '0.75rem', color: '#94a3b8', marginBottom: '1rem' }}>
                                Última execução: {new Date(bot.last_run).toLocaleString('pt-BR')}
                            </p>
                        )}

                        <button
                            onClick={() => executeBot(bot.id)}
                            disabled={executing === bot.id || !bot.enabled}
                            style={{
                                width: '100%',
                                padding: '0.75rem',
                                background: bot.enabled ? '#3b82f6' : '#e5e7eb',
                                color: bot.enabled ? 'white' : '#94a3b8',
                                border: 'none',
                                borderRadius: '8px',
                                cursor: bot.enabled ? 'pointer' : 'not-allowed',
                                fontWeight: '600'
                            }}
                        >
                            {executing === bot.id ? '⏳ Executando...' : '▶️ Executar Agora'}
                        </button>
                    </div>
                ))}
            </div>

            {/* Execution History */}
            <h2 style={{ color: '#1e3a5f', marginBottom: '1rem' }}>
                📜 Histórico de Execuções
            </h2>

            <div style={{
                background: 'white',
                borderRadius: '12px',
                padding: '1rem',
                boxShadow: '0 2px 8px rgba(0,0,0,0.08)'
            }}>
                {history.length === 0 ? (
                    <p style={{ textAlign: 'center', color: '#94a3b8', padding: '2rem' }}>
                        Nenhuma execução registrada ainda.
                    </p>
                ) : (
                    <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                        <thead>
                            <tr style={{ borderBottom: '2px solid #e5e7eb' }}>
                                <th style={{ textAlign: 'left', padding: '0.75rem', color: '#64748b' }}>Bot</th>
                                <th style={{ textAlign: 'left', padding: '0.75rem', color: '#64748b' }}>Status</th>
                                <th style={{ textAlign: 'left', padding: '0.75rem', color: '#64748b' }}>Duração</th>
                                <th style={{ textAlign: 'left', padding: '0.75rem', color: '#64748b' }}>Timestamp</th>
                            </tr>
                        </thead>
                        <tbody>
                            {history.slice(0, 20).map((exec, idx) => (
                                <tr key={idx} style={{ borderBottom: '1px solid #f1f5f9' }}>
                                    <td style={{ padding: '0.75rem' }}>{exec.bot_id}</td>
                                    <td style={{ padding: '0.75rem' }}>
                                        <span style={{
                                            display: 'inline-block',
                                            padding: '0.25rem 0.5rem',
                                            borderRadius: '9999px',
                                            fontSize: '0.75rem',
                                            fontWeight: '600',
                                            background: exec.success ? '#d1fae5' : '#fee2e2',
                                            color: exec.success ? '#065f46' : '#991b1b'
                                        }}>
                                            {exec.success ? '✓ Sucesso' : '✗ Erro'}
                                        </span>
                                    </td>
                                    <td style={{ padding: '0.75rem', fontSize: '0.85rem', color: '#64748b' }}>
                                        {exec.duration_ms.toFixed(0)}ms
                                    </td>
                                    <td style={{ padding: '0.75rem', fontSize: '0.85rem', color: '#94a3b8' }}>
                                        {new Date(exec.timestamp).toLocaleString('pt-BR')}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </div>
        </div>
    );
};

export default AutomationPage;
