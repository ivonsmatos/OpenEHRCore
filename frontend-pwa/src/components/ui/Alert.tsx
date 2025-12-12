/**
 * Alert Component
 * 
 * Unified alert/notification component for consistent feedback
 * Sprint 29: UI/UX Improvement
 */

import React from 'react';
import './Alert.css';

export type AlertVariant = 'info' | 'success' | 'warning' | 'error';

interface AlertProps {
    variant?: AlertVariant;
    title?: string;
    children: React.ReactNode;
    dismissible?: boolean;
    onDismiss?: () => void;
    icon?: React.ReactNode;
    className?: string;
}

const defaultIcons: Record<AlertVariant, string> = {
    info: 'ℹ️',
    success: '✅',
    warning: '⚠️',
    error: '❌',
};

export const Alert: React.FC<AlertProps> = ({
    variant = 'info',
    title,
    children,
    dismissible = false,
    onDismiss,
    icon,
    className = '',
}) => {
    return (
        <div
            className={`alert alert--${variant} ${className}`}
            role="alert"
            aria-live={variant === 'error' ? 'assertive' : 'polite'}
        >
            <div className="alert__icon">
                {icon || defaultIcons[variant]}
            </div>

            <div className="alert__content">
                {title && <div className="alert__title">{title}</div>}
                <div className="alert__message">{children}</div>
            </div>

            {dismissible && (
                <button
                    className="alert__dismiss"
                    onClick={onDismiss}
                    aria-label="Fechar alerta"
                >
                    ✕
                </button>
            )}
        </div>
    );
};

// Toast-style alerts for notifications
export const Toast: React.FC<AlertProps & { isVisible: boolean }> = ({
    isVisible,
    ...props
}) => {
    if (!isVisible) return null;

    return (
        <div className="toast-container">
            <Alert {...props} />
        </div>
    );
};

export default Alert;
