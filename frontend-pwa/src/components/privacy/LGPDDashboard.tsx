/**
 * Sprint 24: LGPD Privacy Dashboard Component
 * 
 * React component for managing LGPD privacy controls
 */

import React, { useState, useEffect } from 'react';
import {
    Shield,
    Download,
    Trash2,
    Eye,
    FileText,
    Clock,
    CheckCircle,
    AlertTriangle,
    XCircle,
    RefreshCw
} from 'lucide-react';
import lgpdApi, {
    LGPDDashboard,
    LGPDRequest,
    LGPDRequestStatus,
    LGPDRequestType
} from '../../services/lgpdApi';
import './LGPDDashboard.css';

interface LGPDDashboardProps {
    patientId?: string;
    isAdmin?: boolean;
}

const statusIcons: Record<LGPDRequestStatus, React.ReactNode> = {
    pending: <Clock className="status-icon pending" />,
    in_progress: <RefreshCw className="status-icon in-progress" />,
    completed: <CheckCircle className="status-icon completed" />,
    rejected: <XCircle className="status-icon rejected" />,
    expired: <AlertTriangle className="status-icon expired" />
};

const statusLabels: Record<LGPDRequestStatus, string> = {
    pending: 'Pendente',
    in_progress: 'Em Andamento',
    completed: 'Concluído',
    rejected: 'Rejeitado',
    expired: 'Expirado'
};

const requestTypeLabels: Record<LGPDRequestType, string> = {
    confirmation: 'Confirmação de Dados',
    access: 'Acesso aos Dados',
    correction: 'Correção de Dados',
    anonymization: 'Anonimização',
    blocking: 'Bloqueio de Dados',
    deletion: 'Exclusão de Dados',
    portability: 'Portabilidade',
    info_sharing: 'Info. Compartilhamento',
    consent_revocation: 'Revogação de Consentimento'
};

export const LGPDDashboardComponent: React.FC<LGPDDashboardProps> = ({
    patientId,
    isAdmin: _isAdmin = false
}) => {
    const [dashboard, setDashboard] = useState<LGPDDashboard | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [activeTab, setActiveTab] = useState<'overview' | 'requests' | 'actions'>('overview');

    useEffect(() => {
        loadDashboard();
    }, [patientId]);

    const loadDashboard = async () => {
        try {
            setLoading(true);
            setError(null);
            const data = await lgpdApi.getLGPDDashboard();
            setDashboard(data);
        } catch (err) {
            setError('Erro ao carregar dashboard LGPD');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const handleExportData = async () => {
        if (!patientId) return;

        try {
            const blob = await lgpdApi.requestDataExport(patientId, 'json');
            lgpdApi.downloadPatientData(blob, `dados_paciente_${patientId}.json`);
        } catch (err) {
            setError('Erro ao exportar dados');
        }
    };

    const handleDeleteRequest = async () => {
        if (!patientId) return;

        if (!window.confirm('Tem certeza que deseja solicitar a exclusão dos seus dados? Esta ação é irreversível.')) {
            return;
        }

        try {
            await lgpdApi.requestDataDeletion(patientId, {
                reason: 'Solicitação do titular',
                soft_delete: true
            });
            alert('Solicitação de exclusão registrada com sucesso.');
            loadDashboard();
        } catch (err) {
            setError('Erro ao solicitar exclusão');
        }
    };

    if (loading) {
        return (
            <div className="lgpd-dashboard loading">
                <RefreshCw className="spinner" />
                <p>Carregando...</p>
            </div>
        );
    }

    if (error) {
        return (
            <div className="lgpd-dashboard error">
                <AlertTriangle />
                <p>{error}</p>
                <button onClick={loadDashboard}>Tentar novamente</button>
            </div>
        );
    }

    return (
        <div className="lgpd-dashboard">
            <header className="lgpd-header">
                <div className="header-title">
                    <Shield className="header-icon" />
                    <h1>Privacidade e LGPD</h1>
                </div>
                <p className="header-subtitle">
                    Gerencie seus dados pessoais conforme a Lei Geral de Proteção de Dados
                </p>
            </header>

            <nav className="lgpd-tabs">
                <button
                    className={activeTab === 'overview' ? 'active' : ''}
                    onClick={() => setActiveTab('overview')}
                >
                    <Eye /> Visão Geral
                </button>
                <button
                    className={activeTab === 'requests' ? 'active' : ''}
                    onClick={() => setActiveTab('requests')}
                >
                    <FileText /> Solicitações
                </button>
                <button
                    className={activeTab === 'actions' ? 'active' : ''}
                    onClick={() => setActiveTab('actions')}
                >
                    <Shield /> Ações
                </button>
            </nav>

            {activeTab === 'overview' && dashboard && (
                <div className="tab-content overview">
                    <div className="stats-grid">
                        <div className="stat-card">
                            <div className="stat-value">{dashboard.summary.total_requests}</div>
                            <div className="stat-label">Total de Solicitações</div>
                        </div>
                        <div className="stat-card pending">
                            <div className="stat-value">{dashboard.summary.pending}</div>
                            <div className="stat-label">Pendentes</div>
                        </div>
                        <div className="stat-card in-progress">
                            <div className="stat-value">{dashboard.summary.in_progress}</div>
                            <div className="stat-label">Em Andamento</div>
                        </div>
                        <div className="stat-card completed">
                            <div className="stat-value">{dashboard.summary.completed}</div>
                            <div className="stat-label">Concluídas</div>
                        </div>
                    </div>

                    <section className="compliance-notes">
                        <h3>Seus Direitos (LGPD Art. 18)</h3>
                        <ul>
                            {dashboard.compliance_notes.map((note, i) => (
                                <li key={i}>{note}</li>
                            ))}
                        </ul>
                    </section>

                    {dashboard.summary.by_type && Object.keys(dashboard.summary.by_type).length > 0 && (
                        <section className="requests-by-type">
                            <h3>Solicitações por Tipo</h3>
                            <div className="type-list">
                                {Object.entries(dashboard.summary.by_type).map(([type, count]) => (
                                    <div key={type} className="type-item">
                                        <span className="type-name">
                                            {requestTypeLabels[type as LGPDRequestType] || type}
                                        </span>
                                        <span className="type-count">{count}</span>
                                    </div>
                                ))}
                            </div>
                        </section>
                    )}
                </div>
            )}

            {activeTab === 'requests' && dashboard && (
                <div className="tab-content requests">
                    {dashboard.pending_requests.length > 0 && (
                        <section className="pending-section">
                            <h3>Solicitações Pendentes</h3>
                            <div className="requests-list">
                                {dashboard.pending_requests.map(req => (
                                    <RequestCard key={req.request_id} request={req} />
                                ))}
                            </div>
                        </section>
                    )}

                    <section className="recent-section">
                        <h3>Solicitações Recentes</h3>
                        {dashboard.recent_requests.length === 0 ? (
                            <p className="empty-message">Nenhuma solicitação encontrada.</p>
                        ) : (
                            <div className="requests-list">
                                {dashboard.recent_requests.map(req => (
                                    <RequestCard key={req.request_id} request={req} />
                                ))}
                            </div>
                        )}
                    </section>
                </div>
            )}

            {activeTab === 'actions' && (
                <div className="tab-content actions">
                    <div className="actions-grid">
                        <div className="action-card">
                            <Download className="action-icon" />
                            <h3>Exportar Meus Dados</h3>
                            <p>Baixe uma cópia completa de todos os seus dados pessoais (Art. 18, II)</p>
                            <button
                                className="action-button primary"
                                onClick={handleExportData}
                                disabled={!patientId}
                            >
                                Exportar Dados
                            </button>
                        </div>

                        <div className="action-card">
                            <Eye className="action-icon" />
                            <h3>Histórico de Acessos</h3>
                            <p>Veja quem acessou seus dados e quando (Art. 19)</p>
                            <button
                                className="action-button secondary"
                                disabled={!patientId}
                            >
                                Ver Histórico
                            </button>
                        </div>

                        <div className="action-card">
                            <FileText className="action-icon" />
                            <h3>Relatório de Conformidade</h3>
                            <p>Gere um relatório completo sobre o tratamento dos seus dados</p>
                            <button
                                className="action-button secondary"
                                disabled={!patientId}
                            >
                                Gerar Relatório
                            </button>
                        </div>

                        <div className="action-card danger">
                            <Trash2 className="action-icon" />
                            <h3>Solicitar Exclusão</h3>
                            <p>Solicite a exclusão dos seus dados pessoais (Art. 18, VI)</p>
                            <button
                                className="action-button danger"
                                onClick={handleDeleteRequest}
                                disabled={!patientId}
                            >
                                Solicitar Exclusão
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

interface RequestCardProps {
    request: LGPDRequest;
}

const RequestCard: React.FC<RequestCardProps> = ({ request }) => {
    const formatDate = (dateStr: string) => {
        return new Date(dateStr).toLocaleDateString('pt-BR', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    return (
        <div className={`request-card ${request.status}`}>
            <div className="request-header">
                <span className="request-type">
                    {requestTypeLabels[request.request_type] || request.request_type}
                </span>
                <span className={`request-status ${request.status}`}>
                    {statusIcons[request.status]}
                    {statusLabels[request.status]}
                </span>
            </div>
            <div className="request-body">
                <div className="request-info">
                    <span className="label">Solicitante:</span>
                    <span className="value">{request.requester_name}</span>
                </div>
                <div className="request-info">
                    <span className="label">Data:</span>
                    <span className="value">{formatDate(request.created_at)}</span>
                </div>
                {request.reason && (
                    <div className="request-info">
                        <span className="label">Motivo:</span>
                        <span className="value">{request.reason}</span>
                    </div>
                )}
            </div>
            {request.notes && (
                <div className="request-notes">
                    <span className="label">Observações:</span>
                    <p>{request.notes}</p>
                </div>
            )}
        </div>
    );
};

export default LGPDDashboardComponent;
