
import React from 'react';
import { Activity } from 'lucide-react';
import { colors } from '../../theme/colors';

interface LoadingVitalSignProps {
    text?: string;
}

const LoadingVitalSign: React.FC<LoadingVitalSignProps> = ({ text = "Carregando..." }) => {
    return (
        <div style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            height: '100%',
            minHeight: '200px',
            gap: '16px'
        }}>
            <style>
                {`
                    @keyframes heartbeat {
                        0% { transform: scale(1); opacity: 0.5; }
                        25% { transform: scale(1.2); opacity: 1; }
                        50% { transform: scale(1); opacity: 0.5; }
                        75% { transform: scale(1.2); opacity: 1; }
                        100% { transform: scale(1); opacity: 0.5; }
                    }
                    .vital-sign-icon {
                        animation: heartbeat 1.5s infinite ease-in-out;
                        color: ${colors.primary.medium};
                    }
                `}
            </style>
            <Activity className="vital-sign-icon" size={48} strokeWidth={2.5} />
            <span style={{
                color: colors.text.secondary,
                fontSize: '0.95rem',
                fontWeight: 500,
                letterSpacing: '0.5px'
            }}>
                {text}
            </span>
        </div>
    );
};

export default LoadingVitalSign;
