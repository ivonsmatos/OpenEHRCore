import React from 'react';
import { colors, spacing, borderRadius } from '../../theme/colors';
import { Practitioner } from '../../types/practitioner';
import { User, Mail, Phone, Stethoscope } from 'lucide-react';

interface PractitionerCardProps {
    practitioner: Practitioner;
    onClick?: () => void;
}

const PractitionerCard: React.FC<PractitionerCardProps> = ({ practitioner, onClick }) => {
    // Extract name
    const nameObj = practitioner.name?.[0];
    const prefix = nameObj?.prefix?.[0] || '';
    const given = nameObj?.given?.join(' ') || '';
    const family = nameObj?.family || '';
    const fullName = `${prefix} ${given} ${family}`.trim();

    // Extract CRM
    const crm = practitioner.identifier?.find(id =>
        id.system === 'http://hl7.org.br/fhir/r4/NamingSystem/crm'
    )?.value;

    // Extract specialty
    const specialty = practitioner.qualification?.[0]?.code?.text ||
        practitioner.qualification?.[0]?.code?.coding?.[0]?.display ||
        'Não especificado';

    // Extract contact
    const phone = practitioner.telecom?.find(t => t.system === 'phone')?.value;
    const email = practitioner.telecom?.find(t => t.system === 'email')?.value;

    const isActive = practitioner.active !== false;

    return (
        <div
            onClick={onClick}
            style={{
                backgroundColor: colors.background.default,
                borderRadius: borderRadius.lg,
                padding: spacing.md,
                border: `1px solid ${colors.border.light}`,
                cursor: onClick ? 'pointer' : 'default',
                transition: 'all 0.2s ease',
                opacity: isActive ? 1 : 0.6,
            }}
            onMouseEnter={(e) => {
                if (onClick) {
                    e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.1)';
                    e.currentTarget.style.transform = 'translateY(-2px)';
                }
            }}
            onMouseLeave={(e) => {
                if (onClick) {
                    e.currentTarget.style.boxShadow = 'none';
                    e.currentTarget.style.transform = 'translateY(0)';
                }
            }}
        >
            <div style={{ display: 'flex', alignItems: 'flex-start', gap: spacing.md }}>
                {/* Avatar */}
                <div
                    style={{
                        width: 56,
                        height: 56,
                        borderRadius: borderRadius.full,
                        backgroundColor: isActive ? colors.primary.light : colors.neutral.lighter,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        flexShrink: 0,
                    }}
                >
                    <User size={28} color={isActive ? colors.primary.medium : colors.neutral.base} />
                </div>

                {/* Content */}
                <div style={{ flex: 1, minWidth: 0 }}>
                    {/* Name and Status */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: spacing.sm, marginBottom: spacing.xs }}>
                        <h3 style={{
                            margin: 0,
                            fontSize: '1.1rem',
                            fontWeight: 600,
                            color: colors.text.primary,
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            whiteSpace: 'nowrap',
                        }}>
                            {fullName}
                        </h3>
                        <span
                            style={{
                                padding: `2px ${spacing.xs}`,
                                backgroundColor: isActive ? '#d1fae5' : '#f3f4f6',
                                color: isActive ? '#047857' : '#6b7280',
                                borderRadius: borderRadius.full,
                                fontSize: '0.75rem',
                                fontWeight: 600,
                                flexShrink: 0,
                            }}
                        >
                            {isActive ? 'Ativo' : 'Inativo'}
                        </span>
                    </div>

                    {/* CRM */}
                    {crm && (
                        <div style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: spacing.xs,
                            marginBottom: spacing.xs,
                            color: colors.text.secondary,
                            fontSize: '0.9rem',
                        }}>
                            <Stethoscope size={16} style={{ flexShrink: 0 }} />
                            <span>{crm}</span>
                        </div>
                    )}

                    {/* Specialty */}
                    <div style={{
                        marginBottom: spacing.sm,
                        color: colors.text.secondary,
                        fontSize: '0.9rem',
                    }}>
                        {specialty}
                    </div>

                    {/* Contact Info */}
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: spacing.md, fontSize: '0.85rem' }}>
                        {phone && (
                            <div style={{ display: 'flex', alignItems: 'center', gap: 4, color: colors.text.secondary }}>
                                <Phone size={14} style={{ flexShrink: 0 }} />
                                <span>{phone}</span>
                            </div>
                        )}
                        {email && (
                            <div style={{ display: 'flex', alignItems: 'center', gap: 4, color: colors.text.secondary }}>
                                <Mail size={14} style={{ flexShrink: 0 }} />
                                <span>{email}</span>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default PractitionerCard;
