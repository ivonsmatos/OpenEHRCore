import React, { useState, useEffect } from 'react';
import { api } from '../../services/api';

interface Referral {
    id: string;
    status: string;
    priority: string;
    reason: string;
    clinical_indication: string;
    patient: string;
    patient_name?: string;
    requester: string;
    requester_name?: string;
    performer: string;
    specialty: string;
    authored_on: string;
    notes: string;
    task?: {
        id: string;
        status: string;
        scheduled_start: string;
        completed_at: string;
        outcome: string;
    };
}

export const ReferralWorkspace: React.FC = () => {
    const [referrals, setReferrals] = useState<Referral[]>([]);
    const [pendingReferrals, setPendingReferrals] = useState<Referral[]>([]);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState<'all' | 'pending' | 'completed'>('all');
    const [showCreateForm, setShowCreateForm] = useState(false);

    useEffect(() => {
        loadReferrals();
    }, []);

    const loadReferrals = async () => {
        try {
            setLoading(true);
            const [allRes, pendingRes] = await Promise.all([
                api.get('/referrals/'),
                api.get('/referrals/pending/')
            ]);
            setReferrals(allRes.data.results || []);
            setPendingReferrals(pendingRes.data.results || []);
        } catch (err) {
            console.error('Erro ao carregar encaminhamentos:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleAccept = async (referralId: string) => {
        try {
            await api.post(`/referrals/${referralId}/accept/`, {
                scheduled_date: new Date().toISOString()
            });
            loadReferrals();
        } catch (err) {
            console.error('Erro ao aceitar encaminhamento:', err);
        }
    };

    const handleComplete = async (referralId: string, outcome: string) => {
        try {
            await api.post(`/referrals/${referralId}/complete/`, { outcome });
            loadReferrals();
        } catch (err) {
            console.error('Erro ao concluir encaminhamento:', err);
        }
    };

    const getStatusColor = (status: string) => {
        const colors: Record<string, string> = {
            'active': '#2563eb',
            'completed': '#16a34a',
            'revoked': '#dc2626',
            'draft': '#f59e0b'
        };
        return colors[status] || '#6b7280';
    };

    const getPriorityIcon = (priority: string) => {
        const icons: Record<string, string> = {
            'urgent': '🔴',
            'asap': '🟠',
            'routine': '🟢'
        };
        return icons[priority] || '⚪';
    };

    const filteredReferrals = activeTab === 'pending'
        ? pendingReferrals
        : activeTab === 'completed'
            ? referrals.filter(r => r.status === 'completed')
            : referrals;

    return (
        <div className="referral-workspace">
            <header className="workspace-header">
                <h2>🔄 Encaminhamentos</h2>
                <button className="btn-primary" onClick={() => setShowCreateForm(true)}>
                    + Novo Encaminhamento
                </button>
            </header>

            <nav className="tabs">
                <button
                    className={activeTab === 'all' ? 'active' : ''}
                    onClick={() => setActiveTab('all')}
                >
                    Todos ({referrals.length})
                </button>
                <button
                    className={activeTab === 'pending' ? 'active' : ''}
                    onClick={() => setActiveTab('pending')}
                >
                    Pendentes ({pendingReferrals.length})
                </button>
                <button
                    className={activeTab === 'completed' ? 'active' : ''}
                    onClick={() => setActiveTab('completed')}
                >
                    Concluídos
                </button>
            </nav>

            {loading ? (
                <div className="loading">Carregando...</div>
            ) : filteredReferrals.length === 0 ? (
                <div className="empty-state">
                    <span>📭</span>
                    <p>Nenhum encaminhamento encontrado</p>
                </div>
            ) : (
                <div className="referrals-list">
                    {filteredReferrals.map(referral => (
                        <div key={referral.id} className="referral-card">
                            <div className="card-left">
                                <span className="priority">{getPriorityIcon(referral.priority)}</span>
                                <div className="info">
                                    <h3>{referral.reason || 'Encaminhamento'}</h3>
                                    <p className="specialty">{referral.specialty || 'Especialidade não informada'}</p>
                                    <p className="indication">{referral.clinical_indication}</p>
                                    <div className="meta">
                                        <span>📅 {new Date(referral.authored_on).toLocaleDateString()}</span>
                                        {referral.patient_name && <span>👤 {referral.patient_name}</span>}
                                    </div>
                                </div>
                            </div>

                            <div className="card-right">
                                <span
                                    className="status-badge"
                                    style={{ backgroundColor: getStatusColor(referral.status) }}
                                >
                                    {referral.status}
                                </span>

                                <div className="actions">
                                    {referral.status === 'active' && (
                                        <>
                                            <button
                                                className="btn-accept"
                                                onClick={() => handleAccept(referral.id)}
                                            >
                                                ✓ Aceitar
                                            </button>
                                            <button className="btn-decline">
                                                ✗ Recusar
                                            </button>
                                        </>
                                    )}
                                    {referral.task?.status === 'accepted' && (
                                        <button
                                            className="btn-complete"
                                            onClick={() => handleComplete(referral.id, 'Consulta realizada')}
                                        >
                                            Concluir
                                        </button>
                                    )}
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            <style>{`
        .referral-workspace {
          padding: 1.5rem;
        }

        .workspace-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 1.5rem;
        }

        .workspace-header h2 {
          margin: 0;
        }

        .btn-primary {
          background: var(--color-primary, #0468BF);
          color: white;
          border: none;
          padding: 0.75rem 1.25rem;
          border-radius: 8px;
          cursor: pointer;
          font-weight: 500;
        }

        .tabs {
          display: flex;
          gap: 0.5rem;
          margin-bottom: 1.5rem;
          border-bottom: 1px solid var(--color-border, #e5e7eb);
          padding-bottom: 0.5rem;
        }

        .tabs button {
          background: none;
          border: none;
          padding: 0.5rem 1rem;
          cursor: pointer;
          color: var(--color-text-secondary, #6b7280);
          border-radius: 6px;
        }

        .tabs button.active {
          background: var(--color-primary, #0468BF);
          color: white;
        }

        .referrals-list {
          display: flex;
          flex-direction: column;
          gap: 1rem;
        }

        .referral-card {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          padding: 1.25rem;
          background: var(--color-surface, white);
          border: 1px solid var(--color-border, #e5e7eb);
          border-radius: 12px;
        }

        .card-left {
          display: flex;
          gap: 1rem;
        }

        .priority {
          font-size: 1.5rem;
        }

        .info h3 {
          margin: 0 0 0.25rem;
          font-size: 1rem;
        }

        .specialty {
          color: var(--color-primary, #0468BF);
          font-weight: 500;
          margin: 0 0 0.5rem;
        }

        .indication {
          color: var(--color-text-secondary, #6b7280);
          font-size: 0.875rem;
          margin: 0 0 0.5rem;
        }

        .meta {
          display: flex;
          gap: 1rem;
          font-size: 0.75rem;
          color: var(--color-text-muted, #9ca3af);
        }

        .card-right {
          display: flex;
          flex-direction: column;
          align-items: flex-end;
          gap: 0.75rem;
        }

        .status-badge {
          font-size: 0.75rem;
          padding: 0.25rem 0.75rem;
          border-radius: 999px;
          color: white;
          text-transform: capitalize;
        }

        .actions {
          display: flex;
          gap: 0.5rem;
        }

        .btn-accept {
          background: #16a34a;
          color: white;
          border: none;
          padding: 0.5rem 1rem;
          border-radius: 6px;
          cursor: pointer;
        }

        .btn-decline {
          background: #dc2626;
          color: white;
          border: none;
          padding: 0.5rem 1rem;
          border-radius: 6px;
          cursor: pointer;
        }

        .btn-complete {
          background: var(--color-primary, #0468BF);
          color: white;
          border: none;
          padding: 0.5rem 1rem;
          border-radius: 6px;
          cursor: pointer;
        }

        .empty-state {
          text-align: center;
          padding: 3rem;
          color: var(--color-text-secondary, #6b7280);
        }

        .empty-state span {
          font-size: 3rem;
          display: block;
          margin-bottom: 1rem;
        }

        .loading {
          text-align: center;
          padding: 2rem;
          color: var(--color-text-secondary, #6b7280);
        }
      `}</style>
        </div>
    );
};

export default ReferralWorkspace;
