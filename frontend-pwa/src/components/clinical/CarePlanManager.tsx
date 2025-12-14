/**
 * CarePlan Manager - Gerenciamento de Planos de Cuidado
 * 
 * Sprint 33: FHIR CarePlan Implementation
 * Features:
 * - Visualização de planos de cuidado
 * - Timeline de atividades
 * - Atribuição de tarefas
 * - Status tracking
 * - Workflow (draft → active → completed)
 * - Mobile-first responsivo
 */

import React, { useState, useEffect } from 'react';
import {
  Calendar,
  CheckCircle2,
  Clock,
  Users,
  Plus,
  Play,
  Target,
  Activity
} from 'lucide-react';
import { colors } from '../../theme/colors';
import { useIsMobile } from '../../hooks/useMediaQuery';

interface CarePlan {
  id: string;
  title: string;
  description: string;
  status: string;
  status_display: string;
  intent: string;
  patient_name: string;
  author_name: string;
  period_start: string;
  period_end: string | null;
  categories: string[];
  activity_count: number;
  created_at: string;
}

interface CarePlanActivity {
  id: string;
  status: string;
  status_display: string;
  kind: string;
  kind_display: string;
  code: any;
  description: string;
  scheduled_period_start: string | null;
  scheduled_period_end: string | null;
  progress: string | null;
  performers: any[];
}

interface CarePlanManagerProps {
  patientId?: string;
}

const CarePlanManager: React.FC<CarePlanManagerProps> = ({ patientId }) => {
  const isMobile = useIsMobile();
  const [carePlans, setCarePlans] = useState<CarePlan[]>([]);
  const [selectedPlan, setSelectedPlan] = useState<CarePlan | null>(null);
  const [activities, setActivities] = useState<CarePlanActivity[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState('active');

  useEffect(() => {
    loadCarePlans();
  }, [patientId, statusFilter]);

  useEffect(() => {
    if (selectedPlan) {
      loadActivities(selectedPlan.id);
    }
  }, [selectedPlan]);

  const loadCarePlans = async () => {
    try {
      setLoading(true);
      const url = patientId
        ? `/api/v1/careplans/patient/${patientId}/?status=${statusFilter}`
        : `/api/v1/careplans/?status=${statusFilter}`;

      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });

      if (!response.ok) throw new Error('Erro ao carregar planos');

      const data = await response.json();
      setCarePlans(data.results || data);
      setError(null);
    } catch (err) {
      setError('Não foi possível carregar os planos de cuidado');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const loadActivities = async (planId: string) => {
    try {
      const response = await fetch(`/api/v1/careplans/${planId}/activities/`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });

      if (!response.ok) throw new Error('Erro ao carregar atividades');

      const data = await response.json();
      setActivities(data.activities || []);
    } catch (err) {
      console.error('Erro ao carregar atividades:', err);
    }
  };

  const activatePlan = async (planId: string) => {
    try {
      const response = await fetch(`/api/v1/careplans/${planId}/activate/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) throw new Error('Erro ao ativar plano');

      await loadCarePlans();
      if (selectedPlan?.id === planId) {
        const data = await response.json();
        setSelectedPlan(data);
      }
    } catch (err) {
      setError('Erro ao ativar plano de cuidado');
    }
  };

  const completePlan = async (planId: string) => {
    try {
      const response = await fetch(`/api/v1/careplans/${planId}/complete/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) throw new Error('Erro ao completar plano');

      await loadCarePlans();
      if (selectedPlan?.id === planId) {
        const data = await response.json();
        setSelectedPlan(data);
      }
    } catch (err) {
      setError('Erro ao completar plano de cuidado');
    }
  };

  const startActivity = async (activityId: string) => {
    try {
      const response = await fetch(`/api/v1/careplan-activities/${activityId}/start/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });

      if (!response.ok) throw new Error('Erro ao iniciar atividade');

      if (selectedPlan) {
        await loadActivities(selectedPlan.id);
      }
    } catch (err) {
      setError('Erro ao iniciar atividade');
    }
  };

  const completeActivity = async (activityId: string) => {
    try {
      const response = await fetch(`/api/v1/careplan-activities/${activityId}/complete/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) throw new Error('Erro ao completar atividade');

      if (selectedPlan) {
        await loadActivities(selectedPlan.id);
      }
    } catch (err) {
      setError('Erro ao completar atividade');
    }
  };

  const getStatusColor = (status: string) => {
    const statusColors: Record<string, string> = {
      'draft': colors.text.tertiary,
      'active': colors.primary.medium,
      'on-hold': colors.status.warning,
      'completed': colors.status.success,
      'revoked': colors.status.error,
      'not-started': colors.text.tertiary,
      'in-progress': colors.primary.medium,
      'scheduled': colors.status.info
    };
    return statusColors[status] || colors.text.secondary;
  };

  const formatDate = (dateString: string) => {
    if (!dateString) return 'Não definido';
    return new Date(dateString).toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: 'short',
      year: 'numeric'
    });
  };

  return (
    <div style={{
      padding: isMobile ? '16px' : '24px',
      backgroundColor: colors.background.surface
    }}>
      {/* Header */}
      <div style={{
        display: 'flex',
        flexDirection: isMobile ? 'column' : 'row',
        justifyContent: 'space-between',
        alignItems: isMobile ? 'stretch' : 'center',
        gap: '16px',
        marginBottom: '24px'
      }}>
        <h2 style={{
          fontSize: isMobile ? '1.5rem' : '1.75rem',
          fontWeight: 'bold',
          color: colors.text.primary,
          margin: 0
        }}>
          📋 Planos de Cuidado
        </h2>

        <button
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '12px 24px',
            backgroundColor: colors.primary.medium,
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            cursor: 'pointer',
            fontWeight: '600',
            width: isMobile ? '100%' : 'auto',
            justifyContent: 'center'
          }}
        >
          <Plus size={20} />
          Novo Plano
        </button>
      </div>

      {/* Status Filter */}
      <div style={{
        display: 'flex',
        gap: '8px',
        marginBottom: '24px',
        overflowX: 'auto',
        paddingBottom: '8px'
      }}>
        {['active', 'draft', 'completed', 'on-hold'].map(status => (
          <button
            key={status}
            onClick={() => setStatusFilter(status)}
            style={{
              padding: '8px 16px',
              borderRadius: '20px',
              border: `2px solid ${statusFilter === status ? colors.primary.medium : colors.border.default}`,
              backgroundColor: statusFilter === status ? colors.primary.light + '40' : 'white',
              color: statusFilter === status ? colors.primary.dark : colors.text.secondary,
              cursor: 'pointer',
              fontWeight: statusFilter === status ? '600' : '400',
              fontSize: '0.875rem',
              whiteSpace: 'nowrap'
            }}
          >
            {status === 'active' ? 'Ativos' :
             status === 'draft' ? 'Rascunhos' :
             status === 'completed' ? 'Completados' : 'Em Espera'}
          </button>
        ))}
      </div>

      {/* Loading/Error States */}
      {loading && (
        <div style={{ textAlign: 'center', padding: '48px' }}>
          <div className="spinner" style={{
            width: '40px',
            height: '40px',
            border: `3px solid ${colors.border.default}`,
            borderTop: `3px solid ${colors.primary.medium}`,
            borderRadius: '50%',
            animation: 'spin 1s linear infinite',
            margin: '0 auto 16px'
          }} />
          <p style={{ color: colors.text.secondary }}>Carregando planos...</p>
        </div>
      )}

      {error && (
        <div style={{
          backgroundColor: colors.status.error + '20',
          borderRadius: '8px',
          padding: '16px',
          marginBottom: '16px',
          color: colors.status.error
        }}>
          {error}
        </div>
      )}

      {/* Care Plans List */}
      {!loading && carePlans.length === 0 && (
        <div style={{
          backgroundColor: 'white',
          borderRadius: '12px',
          padding: '48px',
          textAlign: 'center',
          border: `2px dashed ${colors.border.default}`
        }}>
          <Target size={48} color={colors.text.tertiary} style={{ margin: '0 auto 16px' }} />
          <p style={{ color: colors.text.secondary, fontSize: '1rem' }}>
            Nenhum plano de cuidado encontrado
          </p>
        </div>
      )}

      <div style={{
        display: 'grid',
        gridTemplateColumns: isMobile ? '1fr' : selectedPlan ? '1fr 2fr' : '1fr',
        gap: '24px'
      }}>
        {/* Plans List */}
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          gap: '12px'
        }}>
          {carePlans.map(plan => (
            <div
              key={plan.id}
              onClick={() => setSelectedPlan(plan)}
              style={{
                backgroundColor: selectedPlan?.id === plan.id ? colors.primary.light + '20' : 'white',
                borderRadius: '12px',
                padding: '16px',
                border: `2px solid ${selectedPlan?.id === plan.id ? colors.primary.medium : colors.border.default}`,
                cursor: 'pointer',
                transition: 'all 0.2s'
              }}
            >
              {/* Status Badge */}
              <div style={{
                display: 'inline-block',
                padding: '4px 12px',
                borderRadius: '12px',
                backgroundColor: getStatusColor(plan.status) + '20',
                color: getStatusColor(plan.status),
                fontSize: '0.75rem',
                fontWeight: '600',
                marginBottom: '8px'
              }}>
                {plan.status_display}
              </div>

              <h3 style={{
                fontSize: '1.1rem',
                fontWeight: '600',
                color: colors.text.primary,
                margin: '8px 0'
              }}>
                {plan.title}
              </h3>

              <p style={{
                fontSize: '0.875rem',
                color: colors.text.secondary,
                marginBottom: '12px',
                lineHeight: '1.4'
              }}>
                {plan.description || 'Sem descrição'}
              </p>

              <div style={{
                display: 'flex',
                flexDirection: 'column',
                gap: '6px',
                fontSize: '0.75rem',
                color: colors.text.tertiary
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <Calendar size={14} />
                  {formatDate(plan.period_start)}
                  {plan.period_end && ` - ${formatDate(plan.period_end)}`}
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <Activity size={14} />
                  {plan.activity_count} atividade(s)
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <Users size={14} />
                  {plan.author_name}
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Plan Details & Activities */}
        {selectedPlan && (
          <div style={{
            backgroundColor: 'white',
            borderRadius: '12px',
            padding: '24px',
            border: `1px solid ${colors.border.default}`
          }}>
            {/* Plan Header */}
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'flex-start',
              marginBottom: '24px',
              paddingBottom: '16px',
              borderBottom: `1px solid ${colors.border.light}`
            }}>
              <div>
                <h2 style={{
                  fontSize: '1.5rem',
                  fontWeight: 'bold',
                  color: colors.text.primary,
                  margin: '0 0 8px 0'
                }}>
                  {selectedPlan.title}
                </h2>
                <p style={{
                  color: colors.text.secondary,
                  margin: 0
                }}>
                  {selectedPlan.description}
                </p>
              </div>

              <div style={{ display: 'flex', gap: '8px' }}>
                {selectedPlan.status === 'draft' && (
                  <button
                    onClick={() => activatePlan(selectedPlan.id)}
                    style={{
                      padding: '8px 16px',
                      backgroundColor: colors.status.success,
                      color: 'white',
                      border: 'none',
                      borderRadius: '6px',
                      cursor: 'pointer',
                      fontSize: '0.875rem',
                      fontWeight: '600',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px'
                    }}
                  >
                    <Play size={16} />
                    Ativar
                  </button>
                )}

                {selectedPlan.status === 'active' && (
                  <button
                    onClick={() => completePlan(selectedPlan.id)}
                    style={{
                      padding: '8px 16px',
                      backgroundColor: colors.primary.medium,
                      color: 'white',
                      border: 'none',
                      borderRadius: '6px',
                      cursor: 'pointer',
                      fontSize: '0.875rem',
                      fontWeight: '600',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px'
                    }}
                  >
                    <CheckCircle2 size={16} />
                    Completar
                  </button>
                )}
              </div>
            </div>

            {/* Activities Timeline */}
            <h3 style={{
              fontSize: '1.1rem',
              fontWeight: '600',
              color: colors.text.primary,
              margin: '0 0 16px 0'
            }}>
              Atividades ({activities.length})
            </h3>

            <div style={{
              display: 'flex',
              flexDirection: 'column',
              gap: '12px'
            }}>
              {activities.map((activity, index) => (
                <div
                  key={activity.id}
                  style={{
                    padding: '16px',
                    backgroundColor: colors.background.surface,
                    borderRadius: '8px',
                    borderLeft: `4px solid ${getStatusColor(activity.status)}`
                  }}
                >
                  <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'flex-start',
                    marginBottom: '8px'
                  }}>
                    <div>
                      <div style={{
                        display: 'inline-block',
                        padding: '3px 10px',
                        borderRadius: '10px',
                        backgroundColor: getStatusColor(activity.status) + '20',
                        color: getStatusColor(activity.status),
                        fontSize: '0.7rem',
                        fontWeight: '600',
                        marginBottom: '6px'
                      }}>
                        {activity.status_display}
                      </div>

                      <h4 style={{
                        fontSize: '1rem',
                        fontWeight: '600',
                        color: colors.text.primary,
                        margin: '4px 0'
                      }}>
                        {activity.code?.text || activity.description || `Atividade ${index + 1}`}
                      </h4>

                      {activity.description && activity.code?.text && (
                        <p style={{
                          fontSize: '0.875rem',
                          color: colors.text.secondary,
                          margin: '4px 0 0 0'
                        }}>
                          {activity.description}
                        </p>
                      )}
                    </div>

                    <div style={{ display: 'flex', gap: '6px' }}>
                      {activity.status === 'not-started' && (
                        <button
                          onClick={() => startActivity(activity.id)}
                          style={{
                            padding: '6px 12px',
                            backgroundColor: colors.primary.medium,
                            color: 'white',
                            border: 'none',
                            borderRadius: '4px',
                            cursor: 'pointer',
                            fontSize: '0.75rem'
                          }}
                        >
                          Iniciar
                        </button>
                      )}

                      {activity.status === 'in-progress' && (
                        <button
                          onClick={() => completeActivity(activity.id)}
                          style={{
                            padding: '6px 12px',
                            backgroundColor: colors.status.success,
                            color: 'white',
                            border: 'none',
                            borderRadius: '4px',
                            cursor: 'pointer',
                            fontSize: '0.75rem'
                          }}
                        >
                          Completar
                        </button>
                      )}
                    </div>
                  </div>

                  {activity.scheduled_period_start && (
                    <div style={{
                      fontSize: '0.75rem',
                      color: colors.text.tertiary,
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px'
                    }}>
                      <Clock size={12} />
                      {formatDate(activity.scheduled_period_start)}
                      {activity.scheduled_period_end && ` - ${formatDate(activity.scheduled_period_end)}`}
                    </div>
                  )}

                  {activity.progress && (
                    <div style={{
                      marginTop: '8px',
                      padding: '8px',
                      backgroundColor: 'white',
                      borderRadius: '4px',
                      fontSize: '0.75rem',
                      color: colors.text.secondary
                    }}>
                      <strong>Progresso:</strong> {activity.progress}
                    </div>
                  )}
                </div>
              ))}

              {activities.length === 0 && (
                <div style={{
                  padding: '24px',
                  textAlign: 'center',
                  color: colors.text.tertiary
                }}>
                  Nenhuma atividade cadastrada
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default CarePlanManager;
