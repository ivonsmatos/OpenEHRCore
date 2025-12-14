// Automation Page - Bots and Subscriptions Management
// Sprint 29: Bots/Automation

import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import './AutomationPage.css';

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
    result?: unknown;
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

    const getStatusClass = (status: string) => {
        switch (status) {
            case 'running': return 'status-running';
            case 'completed': return 'status-completed';
            case 'failed': return 'status-failed';
            default: return 'status-default';
        }
    };

    if (loading) {
        return (
            <div className="automation-page automation-page--loading">
                <p>Carregando automações...</p>
            </div>
        );
    }

    return (
        <div className="automation-page">
            <h1 className="automation-title">
                🤖 Automações (Bots)
            </h1>

            <p className="automation-description">
                Gerencie bots que executam automaticamente em resposta a eventos do sistema.
            </p>

            {/* Bots Grid */}
            <div className="bots-grid">
                {bots.map((bot) => (
                    <div
                        key={bot.id}
                        className={`bot-card ${bot.enabled ? 'bot-card--enabled' : ''}`}
                    >
                        <div className="bot-card__header">
                            <div>
                                <h3 className="bot-card__title">
                                    {getTriggerIcon(bot.trigger_type)} {bot.name}
                                </h3>
                                <p className="bot-card__description">
                                    {bot.description}
                                </p>
                            </div>
                            <label className="bot-card__toggle">
                                <input
                                    type="checkbox"
                                    checked={bot.enabled}
                                    onChange={(e) => toggleBot(bot.id, e.target.checked)}
                                />
                                <span className={`bot-card__toggle-label ${bot.enabled ? 'bot-card__toggle-label--active' : ''}`}>
                                    {bot.enabled ? 'Ativo' : 'Inativo'}
                                </span>
                            </label>
                        </div>

                        <div className="bot-card__meta">
                            <span>Trigger: <strong>{bot.trigger_type}</strong></span>
                            <span>
                                Status:
                                <span className={getStatusClass(bot.status)}>
                                    {' '}{bot.status}
                                </span>
                            </span>
                        </div>

                        <div className="bot-card__stats">
                            <div>
                                <span className="bot-card__stat-value--success">{bot.run_count}</span>
                                <span className="bot-card__stat-label">execuções</span>
                            </div>
                            <div>
                                <span className="bot-card__stat-value--error">{bot.error_count}</span>
                                <span className="bot-card__stat-label">erros</span>
                            </div>
                        </div>

                        {bot.last_run && (
                            <p className="bot-card__last-run">
                                Última execução: {new Date(bot.last_run).toLocaleString('pt-BR')}
                            </p>
                        )}

                        <button
                            onClick={() => executeBot(bot.id)}
                            disabled={executing === bot.id || !bot.enabled}
                            className="bot-card__execute-btn"
                        >
                            {executing === bot.id ? '⏳ Executando...' : '▶️ Executar Agora'}
                        </button>
                    </div>
                ))}
            </div>

            {/* Execution History */}
            <h2 className="history-title">
                📜 Histórico de Execuções
            </h2>

            <div className="history-container">
                {history.length === 0 ? (
                    <p className="history-empty">
                        Nenhuma execução registrada ainda.
                    </p>
                ) : (
                    <table className="history-table">
                        <thead>
                            <tr>
                                <th>Bot</th>
                                <th>Status</th>
                                <th>Duração</th>
                                <th>Timestamp</th>
                            </tr>
                        </thead>
                        <tbody>
                            {history.slice(0, 20).map((exec, idx) => (
                                <tr key={idx}>
                                    <td>{exec.bot_id}</td>
                                    <td>
                                        <span className={`status-badge ${exec.success ? 'status-badge--success' : 'status-badge--error'}`}>
                                            {exec.success ? '✓ Sucesso' : '✗ Erro'}
                                        </span>
                                    </td>
                                    <td className="history-table__duration">
                                        {exec.duration_ms.toFixed(0)}ms
                                    </td>
                                    <td className="history-table__timestamp">
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
