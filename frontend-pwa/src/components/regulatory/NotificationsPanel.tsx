import React, { useState, useEffect } from 'react';
import { api } from '../../services/api';

interface Notification {
    id: string;
    cid_code: string;
    disease: string;
    patient: string;
    patient_name?: string;
    practitioner: string;
    onset_date: string;
    recorded_date: string;
    notification_status: 'pending' | 'sent';
    urgency: 'immediate' | 'weekly';
    sent_date?: string;
}

interface NotificationStats {
    total: number;
    pending: number;
    sent: number;
    by_urgency: {
        immediate: number;
        weekly: number;
    };
}

export const NotificationsPanel: React.FC = () => {
    const [notifications, setNotifications] = useState<Notification[]>([]);
    const [pending, setPending] = useState<Notification[]>([]);
    const [stats, setStats] = useState<NotificationStats | null>(null);
    const [loading, setLoading] = useState(true);
    const [checkCid, setCheckCid] = useState('');
    const [checkResult, setCheckResult] = useState<any>(null);

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            setLoading(true);
            const [allRes, pendingRes, statsRes] = await Promise.all([
                api.get('/notifications/'),
                api.get('/notifications/pending/'),
                api.get('/notifications/stats/')
            ]);
            setNotifications(allRes.data.results || []);
            setPending(pendingRes.data.results || []);
            setStats(statsRes.data);
        } catch (err) {
            console.error('Erro ao carregar notificações:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleSendToSinan = async (notificationId: string) => {
        try {
            await api.post(`/notifications/${notificationId}/send/`);
            loadData();
        } catch (err) {
            console.error('Erro ao enviar ao SINAN:', err);
        }
    };

    const handleCheckCid = async () => {
        if (!checkCid) return;
        try {
            const res = await api.post('/notifications/check/', { cid_code: checkCid });
            setCheckResult(res.data);
        } catch (err) {
            console.error('Erro ao verificar CID:', err);
        }
    };

    const getUrgencyBadge = (urgency: string) => {
        if (urgency === 'immediate') {
            return <span className="urgency-badge immediate">⚡ Imediata (24h)</span>;
        }
        return <span className="urgency-badge weekly">📅 Semanal (7 dias)</span>;
    };

    return (
        <div className="notifications-panel">
            <header className="panel-header">
                <h2>🔔 Notificações Compulsórias</h2>
            </header>

            {/* Estatísticas */}
            {stats && (
                <div className="stats-grid">
                    <div className="stat-card">
                        <span className="stat-value">{stats.total}</span>
                        <span className="stat-label">Total</span>
                    </div>
                    <div className="stat-card pending">
                        <span className="stat-value">{stats.pending}</span>
                        <span className="stat-label">Pendentes</span>
                    </div>
                    <div className="stat-card sent">
                        <span className="stat-value">{stats.sent}</span>
                        <span className="stat-label">Enviadas</span>
                    </div>
                    <div className="stat-card immediate">
                        <span className="stat-value">{stats.by_urgency.immediate}</span>
                        <span className="stat-label">Imediatas</span>
                    </div>
                </div>
            )}

            {/* Verificar CID */}
            <section className="check-section">
                <h3>Verificar CID</h3>
                <div className="check-form">
                    <input
                        type="text"
                        placeholder="Digite o código CID (ex: A90)"
                        value={checkCid}
                        onChange={(e) => setCheckCid(e.target.value.toUpperCase())}
                        aria-label="Código CID"
                    />
                    <button onClick={handleCheckCid}>Verificar</button>
                </div>
                {checkResult && (
                    <div className={`check-result ${checkResult.is_notifiable ? 'notifiable' : ''}`}>
                        {checkResult.is_notifiable ? (
                            <>
                                <span className="alert-icon">⚠️</span>
                                <div>
                                    <strong>{checkResult.disease}</strong>
                                    <p>{checkResult.alert}</p>
                                    <span className="deadline">Prazo: {checkResult.deadline}</span>
                                </div>
                            </>
                        ) : (
                            <>
                                <span className="ok-icon">✓</span>
                                <p>{checkResult.message}</p>
                            </>
                        )}
                    </div>
                )}
            </section>

            {/* Notificações Pendentes */}
            <section className="pending-section">
                <h3>⏳ Pendentes de Envio ({pending.length})</h3>
                {pending.length === 0 ? (
                    <p className="empty">Nenhuma notificação pendente</p>
                ) : (
                    <div className="notifications-list">
                        {pending.map(notification => (
                            <div key={notification.id} className="notification-card pending">
                                <div className="card-content">
                                    <div className="disease-info">
                                        <span className="cid">{notification.cid_code}</span>
                                        <span className="disease">{notification.disease}</span>
                                    </div>
                                    {getUrgencyBadge(notification.urgency)}
                                    <div className="meta">
                                        <span>📅 {new Date(notification.recorded_date).toLocaleDateString()}</span>
                                    </div>
                                </div>
                                <button
                                    className="btn-send"
                                    onClick={() => handleSendToSinan(notification.id)}
                                >
                                    Enviar ao SINAN
                                </button>
                            </div>
                        ))}
                    </div>
                )}
            </section>

            {/* Lista Geral */}
            <section className="all-section">
                <h3>📋 Todas as Notificações</h3>
                {loading ? (
                    <p className="loading">Carregando...</p>
                ) : notifications.length === 0 ? (
                    <p className="empty">Nenhuma notificação registrada</p>
                ) : (
                    <table className="notifications-table">
                        <thead>
                            <tr>
                                <th>CID</th>
                                <th>Doença</th>
                                <th>Data</th>
                                <th>Urgência</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            {notifications.map(notification => (
                                <tr key={notification.id}>
                                    <td className="cid">{notification.cid_code}</td>
                                    <td>{notification.disease}</td>
                                    <td>{new Date(notification.recorded_date).toLocaleDateString()}</td>
                                    <td>
                                        <span className={`urgency ${notification.urgency}`}>
                                            {notification.urgency === 'immediate' ? '⚡' : '📅'}
                                        </span>
                                    </td>
                                    <td>
                                        <span className={`status ${notification.notification_status}`}>
                                            {notification.notification_status === 'sent' ? '✓ Enviada' : '⏳ Pendente'}
                                        </span>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </section>

            <style>{`
        .notifications-panel {
          padding: 1.5rem;
        }

        .panel-header h2 {
          margin: 0 0 1.5rem;
        }

        .stats-grid {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          gap: 1rem;
          margin-bottom: 2rem;
        }

        .stat-card {
          background: var(--color-surface, white);
          border: 1px solid var(--color-border, #e5e7eb);
          border-radius: 12px;
          padding: 1.25rem;
          text-align: center;
        }

        .stat-card.pending {
          border-left: 4px solid #f59e0b;
        }

        .stat-card.sent {
          border-left: 4px solid #16a34a;
        }

        .stat-card.immediate {
          border-left: 4px solid #dc2626;
        }

        .stat-value {
          display: block;
          font-size: 2rem;
          font-weight: 700;
          color: var(--color-text-primary, #1f2937);
        }

        .stat-label {
          font-size: 0.875rem;
          color: var(--color-text-secondary, #6b7280);
        }

        .check-section {
          background: var(--color-surface, white);
          border: 1px solid var(--color-border, #e5e7eb);
          border-radius: 12px;
          padding: 1.25rem;
          margin-bottom: 2rem;
        }

        .check-section h3 {
          margin: 0 0 1rem;
        }

        .check-form {
          display: flex;
          gap: 0.5rem;
        }

        .check-form input {
          flex: 1;
          padding: 0.75rem;
          border: 1px solid var(--color-border, #e5e7eb);
          border-radius: 8px;
          font-size: 1rem;
        }

        .check-form button {
          background: var(--color-primary, #0468BF);
          color: white;
          border: none;
          padding: 0.75rem 1.5rem;
          border-radius: 8px;
          cursor: pointer;
        }

        .check-result {
          margin-top: 1rem;
          padding: 1rem;
          border-radius: 8px;
          display: flex;
          align-items: center;
          gap: 1rem;
          background: #f0fdf4;
        }

        .check-result.notifiable {
          background: #fef3c7;
        }

        .alert-icon, .ok-icon {
          font-size: 1.5rem;
        }

        .deadline {
          display: block;
          font-size: 0.875rem;
          color: #92400e;
          font-weight: 500;
        }

        .pending-section, .all-section {
          margin-bottom: 2rem;
        }

        .pending-section h3, .all-section h3 {
          margin: 0 0 1rem;
        }

        .notifications-list {
          display: flex;
          flex-direction: column;
          gap: 0.75rem;
        }

        .notification-card {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 1rem;
          background: var(--color-surface, white);
          border: 1px solid var(--color-border, #e5e7eb);
          border-radius: 8px;
          border-left: 4px solid #f59e0b;
        }

        .disease-info {
          display: flex;
          align-items: center;
          gap: 0.75rem;
        }

        .cid {
          background: var(--color-primary, #0468BF);
          color: white;
          padding: 0.25rem 0.5rem;
          border-radius: 4px;
          font-weight: 600;
          font-size: 0.875rem;
        }

        .disease {
          font-weight: 500;
        }

        .urgency-badge {
          font-size: 0.75rem;
          padding: 0.25rem 0.5rem;
          border-radius: 4px;
        }

        .urgency-badge.immediate {
          background: #fee2e2;
          color: #991b1b;
        }

        .urgency-badge.weekly {
          background: #dbeafe;
          color: #1e40af;
        }

        .btn-send {
          background: #16a34a;
          color: white;
          border: none;
          padding: 0.5rem 1rem;
          border-radius: 6px;
          cursor: pointer;
        }

        .notifications-table {
          width: 100%;
          border-collapse: collapse;
          background: var(--color-surface, white);
          border-radius: 8px;
          overflow: hidden;
        }

        .notifications-table th,
        .notifications-table td {
          padding: 0.75rem;
          text-align: left;
          border-bottom: 1px solid var(--color-border, #e5e7eb);
        }

        .notifications-table th {
          background: var(--color-background, #f9fafb);
          font-weight: 600;
          font-size: 0.875rem;
        }

        .status.sent {
          color: #16a34a;
        }

        .status.pending {
          color: #f59e0b;
        }

        .empty, .loading {
          text-align: center;
          padding: 2rem;
          color: var(--color-text-secondary, #6b7280);
        }
      `}</style>
        </div>
    );
};

export default NotificationsPanel;
