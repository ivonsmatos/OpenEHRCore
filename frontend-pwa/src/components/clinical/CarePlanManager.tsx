import React, { useState, useEffect } from 'react';
import { api } from '../../services/api';

interface Goal {
    id: string;
    description: string;
    status: string;
    target_date: string;
    progress: number;
}

interface Activity {
    description: string;
    status: string;
    scheduled_date: string;
}

interface CarePlan {
    id: string;
    title: string;
    status: string;
    intent: string;
    category: string;
    patient_id: string;
    patient_name?: string;
    period_start: string;
    period_end: string;
    activities: Activity[];
    goals: Goal[];
    created: string;
}

interface CarePlanManagerProps {
    patientId?: string;
}

export const CarePlanManager: React.FC<CarePlanManagerProps> = ({ patientId }) => {
    const [carePlans, setCarePlans] = useState<CarePlan[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [showCreateModal, setShowCreateModal] = useState(false);
    const [selectedPlan, setSelectedPlan] = useState<CarePlan | null>(null);

    useEffect(() => {
        loadCarePlans();
    }, [patientId]);

    const loadCarePlans = async () => {
        try {
            setLoading(true);
            const endpoint = patientId
                ? `/patients/${patientId}/careplans/`
                : '/careplans/';
            const response = await api.get(endpoint);
            setCarePlans(response.data.results || []);
        } catch (err) {
            setError('Erro ao carregar planos de cuidado');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const handleStatusChange = async (planId: string, newStatus: string) => {
        try {
            await api.put(`/careplans/${planId}/`, { status: newStatus });
            loadCarePlans();
        } catch (err) {
            console.error('Erro ao atualizar status:', err);
        }
    };

    const getStatusColor = (status: string) => {
        const colors: Record<string, string> = {
            'active': 'var(--color-success)',
            'completed': 'var(--color-primary)',
            'revoked': 'var(--color-error)',
            'draft': 'var(--color-warning)',
            'on-hold': 'var(--color-secondary)'
        };
        return colors[status] || 'var(--color-secondary)';
    };

    const getCategoryIcon = (category: string) => {
        const icons: Record<string, string> = {
            'diabetes': '🩸',
            'hypertension': '❤️',
            'asthma': '🌬️',
            'chronic-kidney': '💧',
            'heart-failure': '💓',
            'default': '📋'
        };
        return icons[category] || icons.default;
    };

    if (loading) {
        return (
            <div className="careplan-loading">
                <div className="spinner"></div>
                <p>Carregando planos de cuidado...</p>
            </div>
        );
    }

    if (error) {
        return (
            <div className="careplan-error">
                <span className="error-icon">⚠️</span>
                <p>{error}</p>
                <button onClick={loadCarePlans}>Tentar novamente</button>
            </div>
        );
    }

    return (
        <div className="careplan-manager">
            <header className="careplan-header">
                <h2>Planos de Cuidado</h2>
                <button
                    className="btn-primary"
                    onClick={() => setShowCreateModal(true)}
                >
                    + Novo Plano
                </button>
            </header>

            {carePlans.length === 0 ? (
                <div className="careplan-empty">
                    <span className="empty-icon">📋</span>
                    <p>Nenhum plano de cuidado encontrado</p>
                    <button onClick={() => setShowCreateModal(true)}>
                        Criar primeiro plano
                    </button>
                </div>
            ) : (
                <div className="careplan-grid">
                    {carePlans.map(plan => (
                        <div
                            key={plan.id}
                            className="careplan-card"
                            onClick={() => setSelectedPlan(plan)}
                        >
                            <div className="card-header">
                                <span className="category-icon">
                                    {getCategoryIcon(plan.category)}
                                </span>
                                <h3>{plan.title}</h3>
                                <span
                                    className="status-badge"
                                    style={{ backgroundColor: getStatusColor(plan.status) }}
                                >
                                    {plan.status}
                                </span>
                            </div>

                            <div className="card-body">
                                <div className="period">
                                    <span>📅</span>
                                    <span>
                                        {new Date(plan.period_start).toLocaleDateString()} -
                                        {plan.period_end ? new Date(plan.period_end).toLocaleDateString() : 'Contínuo'}
                                    </span>
                                </div>

                                <div className="goals-summary">
                                    <span>🎯</span>
                                    <span>{plan.goals?.length || 0} metas</span>
                                </div>

                                <div className="activities-summary">
                                    <span>📝</span>
                                    <span>{plan.activities?.length || 0} atividades</span>
                                </div>
                            </div>

                            <div className="card-actions">
                                <button
                                    className="btn-secondary"
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        setSelectedPlan(plan);
                                    }}
                                >
                                    Ver Detalhes
                                </button>
                                <select
                                    value={plan.status}
                                    onChange={(e) => handleStatusChange(plan.id, e.target.value)}
                                    onClick={(e) => e.stopPropagation()}
                                    aria-label="Alterar status do plano"
                                >
                                    <option value="active">Ativo</option>
                                    <option value="on-hold">Em Espera</option>
                                    <option value="completed">Concluído</option>
                                    <option value="revoked">Cancelado</option>
                                </select>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {/* Modal de Detalhes */}
            {selectedPlan && (
                <div className="careplan-modal-overlay" onClick={() => setSelectedPlan(null)}>
                    <div className="careplan-modal" onClick={(e) => e.stopPropagation()}>
                        <header>
                            <h2>{selectedPlan.title}</h2>
                            <button className="close-btn" onClick={() => setSelectedPlan(null)}>×</button>
                        </header>

                        <div className="modal-content">
                            <section className="goals-section">
                                <h3>🎯 Metas</h3>
                                {selectedPlan.goals?.length > 0 ? (
                                    <ul className="goals-list">
                                        {selectedPlan.goals.map((goal, idx) => (
                                            <li key={idx} className={`goal-item ${goal.status}`}>
                                                <span className="goal-desc">{goal.description}</span>
                                                <div className="goal-progress">
                                                    <div
                                                        className="progress-bar"
                                                        style={{ width: `${goal.progress || 0}%` }}
                                                    />
                                                </div>
                                                <span className="goal-target">
                                                    Meta: {new Date(goal.target_date).toLocaleDateString()}
                                                </span>
                                            </li>
                                        ))}
                                    </ul>
                                ) : (
                                    <p className="empty-message">Nenhuma meta definida</p>
                                )}
                            </section>

                            <section className="activities-section">
                                <h3>📝 Atividades</h3>
                                {selectedPlan.activities?.length > 0 ? (
                                    <ul className="activities-list">
                                        {selectedPlan.activities.map((activity, idx) => (
                                            <li key={idx} className={`activity-item ${activity.status}`}>
                                                <span className="activity-desc">{activity.description}</span>
                                                <span className="activity-date">
                                                    {new Date(activity.scheduled_date).toLocaleDateString()}
                                                </span>
                                                <span className={`activity-status ${activity.status}`}>
                                                    {activity.status}
                                                </span>
                                            </li>
                                        ))}
                                    </ul>
                                ) : (
                                    <p className="empty-message">Nenhuma atividade agendada</p>
                                )}
                            </section>
                        </div>

                        <footer>
                            <button className="btn-secondary" onClick={() => setSelectedPlan(null)}>
                                Fechar
                            </button>
                            <button className="btn-primary">
                                Adicionar Atividade
                            </button>
                        </footer>
                    </div>
                </div>
            )}

            <style>{`
        .careplan-manager {
          padding: 1.5rem;
        }

        .careplan-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 1.5rem;
        }

        .careplan-header h2 {
          margin: 0;
          color: var(--color-text-primary);
        }

        .btn-primary {
          background: var(--color-primary);
          color: white;
          border: none;
          padding: 0.75rem 1.5rem;
          border-radius: 8px;
          cursor: pointer;
          font-weight: 500;
        }

        .btn-primary:hover {
          opacity: 0.9;
        }

        .btn-secondary {
          background: var(--color-surface);
          color: var(--color-text-primary);
          border: 1px solid var(--color-border);
          padding: 0.5rem 1rem;
          border-radius: 6px;
          cursor: pointer;
        }

        .careplan-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
          gap: 1rem;
        }

        .careplan-card {
          background: var(--color-surface);
          border-radius: 12px;
          padding: 1.25rem;
          border: 1px solid var(--color-border);
          cursor: pointer;
          transition: transform 0.2s, box-shadow 0.2s;
        }

        .careplan-card:hover {
          transform: translateY(-2px);
          box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }

        .card-header {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          margin-bottom: 1rem;
        }

        .category-icon {
          font-size: 1.5rem;
        }

        .card-header h3 {
          flex: 1;
          margin: 0;
          font-size: 1rem;
        }

        .status-badge {
          font-size: 0.75rem;
          padding: 0.25rem 0.5rem;
          border-radius: 4px;
          color: white;
          text-transform: capitalize;
        }

        .card-body {
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
          margin-bottom: 1rem;
          color: var(--color-text-secondary);
          font-size: 0.875rem;
        }

        .card-body > div {
          display: flex;
          align-items: center;
          gap: 0.5rem;
        }

        .card-actions {
          display: flex;
          gap: 0.5rem;
        }

        .card-actions select {
          padding: 0.5rem;
          border-radius: 6px;
          border: 1px solid var(--color-border);
          background: var(--color-surface);
          font-size: 0.875rem;
        }

        .careplan-empty {
          text-align: center;
          padding: 3rem;
          color: var(--color-text-secondary);
        }

        .empty-icon {
          font-size: 3rem;
          display: block;
          margin-bottom: 1rem;
        }

        .careplan-modal-overlay {
          position: fixed;
          inset: 0;
          background: rgba(0,0,0,0.5);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 1000;
        }

        .careplan-modal {
          background: var(--color-surface);
          border-radius: 16px;
          width: 90%;
          max-width: 600px;
          max-height: 80vh;
          overflow: hidden;
          display: flex;
          flex-direction: column;
        }

        .careplan-modal header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 1.25rem;
          border-bottom: 1px solid var(--color-border);
        }

        .careplan-modal header h2 {
          margin: 0;
        }

        .close-btn {
          background: none;
          border: none;
          font-size: 1.5rem;
          cursor: pointer;
          color: var(--color-text-secondary);
        }

        .modal-content {
          flex: 1;
          overflow-y: auto;
          padding: 1.25rem;
        }

        .modal-content section {
          margin-bottom: 1.5rem;
        }

        .modal-content h3 {
          font-size: 1rem;
          margin-bottom: 0.75rem;
        }

        .goals-list, .activities-list {
          list-style: none;
          padding: 0;
          margin: 0;
        }

        .goal-item, .activity-item {
          padding: 0.75rem;
          background: var(--color-background);
          border-radius: 8px;
          margin-bottom: 0.5rem;
        }

        .progress-bar {
          height: 4px;
          background: var(--color-primary);
          border-radius: 2px;
          margin: 0.5rem 0;
        }

        .careplan-modal footer {
          display: flex;
          justify-content: flex-end;
          gap: 0.75rem;
          padding: 1.25rem;
          border-top: 1px solid var(--color-border);
        }

        .careplan-loading {
          display: flex;
          flex-direction: column;
          align-items: center;
          padding: 3rem;
        }

        .spinner {
          width: 40px;
          height: 40px;
          border: 3px solid var(--color-border);
          border-top-color: var(--color-primary);
          border-radius: 50%;
          animation: spin 1s linear infinite;
        }

        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
        </div>
    );
};

export default CarePlanManager;
