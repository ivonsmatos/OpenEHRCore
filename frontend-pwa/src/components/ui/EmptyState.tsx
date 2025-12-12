/**
 * EmptyState Component
 * 
 * Display when there's no data to show
 * Sprint 29: UI/UX Improvement
 */

import React from 'react';
import './EmptyState.css';

interface EmptyStateProps {
    icon?: React.ReactNode;
    title: string;
    description?: string;
    action?: {
        label: string;
        onClick: () => void;
    };
    variant?: 'default' | 'compact' | 'large';
    className?: string;
}

const defaultIcons: Record<string, string> = {
    patients: '👥',
    appointments: '📅',
    documents: '📄',
    search: '🔍',
    notifications: '🔔',
    error: '⚠️',
    empty: '📭',
};

export const EmptyState: React.FC<EmptyStateProps> = ({
    icon,
    title,
    description,
    action,
    variant = 'default',
    className = '',
}) => {
    return (
        <div className={`empty-state empty-state--${variant} ${className}`}>
            <div className="empty-state__icon">
                {icon || defaultIcons.empty}
            </div>

            <h3 className="empty-state__title">{title}</h3>

            {description && (
                <p className="empty-state__description">{description}</p>
            )}

            {action && (
                <button
                    className="empty-state__action"
                    onClick={action.onClick}
                >
                    {action.label}
                </button>
            )}
        </div>
    );
};

// Pre-built empty states for common scenarios
export const NoPatients: React.FC<{ onAdd?: () => void }> = ({ onAdd }) => (
    <EmptyState
        icon="👥"
        title="Nenhum paciente encontrado"
        description="Comece adicionando seu primeiro paciente ao sistema."
        action={onAdd ? { label: "Adicionar Paciente", onClick: onAdd } : undefined}
    />
);

export const NoAppointments: React.FC<{ onSchedule?: () => void }> = ({ onSchedule }) => (
    <EmptyState
        icon="📅"
        title="Nenhum agendamento"
        description="Não há consultas agendadas para este período."
        action={onSchedule ? { label: "Agendar Consulta", onClick: onSchedule } : undefined}
    />
);

export const NoResults: React.FC<{ query?: string }> = ({ query }) => (
    <EmptyState
        icon="🔍"
        title="Nenhum resultado encontrado"
        description={query ? `Não encontramos resultados para "${query}". Tente outros termos.` : "Tente ajustar os filtros de busca."}
        variant="compact"
    />
);

export const NoNotifications: React.FC = () => (
    <EmptyState
        icon="🔔"
        title="Tudo em dia!"
        description="Você não tem notificações pendentes."
        variant="compact"
    />
);

export const ErrorState: React.FC<{ onRetry?: () => void }> = ({ onRetry }) => (
    <EmptyState
        icon="⚠️"
        title="Algo deu errado"
        description="Não foi possível carregar os dados. Tente novamente."
        action={onRetry ? { label: "Tentar Novamente", onClick: onRetry } : undefined}
    />
);

export default EmptyState;
