import React, { useState } from 'react';
import { colors, spacing, borderRadius } from '../../theme/colors';
import { PractitionerFormData } from '../../types/practitioner';
import Button from '../base/Button';

interface PractitionerFormProps {
    onSubmit: (data: PractitionerFormData) => Promise<void>;
    onCancel: () => void;
    initialData?: Partial<PractitionerFormData>;
}

const PractitionerForm: React.FC<PractitionerFormProps> = ({ onSubmit, onCancel, initialData }) => {
    const [formData, setFormData] = useState<PractitionerFormData>({
        family_name: initialData?.family_name || '',
        given_names: initialData?.given_names || [''],
        prefix: initialData?.prefix || '',
        gender: initialData?.gender || 'unknown',
        birthDate: initialData?.birthDate || '',
        phone: initialData?.phone || '',
        email: initialData?.email || '',
        crm: initialData?.crm || '',
        qualification_code: initialData?.qualification_code || 'MD',
        qualification_display: initialData?.qualification_display || '',
    });

    const [errors, setErrors] = useState<Record<string, string>>({});
    const [submitting, setSubmitting] = useState(false);

    const validateCRM = (crm: string): boolean => {
        // Format: CRM-UF-XXXXXX
        const crmRegex = /^CRM-[A-Z]{2}-\d{4,6}$/;
        return crmRegex.test(crm);
    };

    const validateEmail = (email: string): boolean => {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    };

    const validateForm = (): boolean => {
        const newErrors: Record<string, string> = {};

        if (!formData.family_name.trim()) {
            newErrors.family_name = 'Sobrenome é obrigatório';
        }

        if (!formData.given_names[0]?.trim()) {
            newErrors.given_names = 'Nome é obrigatório';
        }

        if (!formData.crm.trim()) {
            newErrors.crm = 'CRM é obrigatório';
        } else if (!validateCRM(formData.crm)) {
            newErrors.crm = 'Formato inválido. Use: CRM-UF-XXXXXX (ex: CRM-SP-123456)';
        }

        if (formData.email && !validateEmail(formData.email)) {
            newErrors.email = 'Email inválido';
        }

        if (!formData.qualification_display.trim()) {
            newErrors.qualification_display = 'Especialidade é obrigatória';
        }

        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        if (!validateForm()) {
            return;
        }

        setSubmitting(true);
        try {
            await onSubmit(formData);
        } catch (error) {
            console.error('Error submitting form:', error);
        } finally {
            setSubmitting(false);
        }
    };

    const inputStyle: React.CSSProperties = {
        width: '100%',
        padding: spacing.sm,
        border: `1px solid ${colors.border.light}`,
        borderRadius: borderRadius.md,
        fontSize: '1rem',
        fontFamily: 'inherit',
    };

    const labelStyle: React.CSSProperties = {
        display: 'block',
        marginBottom: spacing.xs,
        fontWeight: 500,
        color: colors.text.primary,
    };

    const errorStyle: React.CSSProperties = {
        color: colors.alert.critical,
        fontSize: '0.85rem',
        marginTop: spacing.xs,
    };

    return (
        <form onSubmit={handleSubmit} style={{ maxWidth: '600px' }}>
            {/* Prefix */}
            <div style={{ marginBottom: spacing.md }}>
                <label style={labelStyle}>Prefixo (opcional)</label>
                <select
                    value={formData.prefix}
                    onChange={(e) => setFormData({ ...formData, prefix: e.target.value })}
                    style={inputStyle}
                >
                    <option value="">Selecione...</option>
                    <option value="Dr.">Dr.</option>
                    <option value="Dra.">Dra.</option>
                    <option value="Enf.">Enf.</option>
                    <option value="Enfa.">Enfa.</option>
                </select>
            </div>

            {/* Given Names */}
            <div style={{ marginBottom: spacing.md }}>
                <label style={labelStyle}>Nome *</label>
                <input
                    type="text"
                    value={formData.given_names[0] || ''}
                    onChange={(e) => setFormData({ ...formData, given_names: [e.target.value] })}
                    style={inputStyle}
                    placeholder="Ex: Maria da Silva"
                />
                {errors.given_names && <div style={errorStyle}>{errors.given_names}</div>}
            </div>

            {/* Family Name */}
            <div style={{ marginBottom: spacing.md }}>
                <label style={labelStyle}>Sobrenome *</label>
                <input
                    type="text"
                    value={formData.family_name}
                    onChange={(e) => setFormData({ ...formData, family_name: e.target.value })}
                    style={inputStyle}
                    placeholder="Ex: Santos"
                />
                {errors.family_name && <div style={errorStyle}>{errors.family_name}</div>}
            </div>

            {/* CRM */}
            <div style={{ marginBottom: spacing.md }}>
                <label style={labelStyle}>CRM *</label>
                <input
                    type="text"
                    value={formData.crm}
                    onChange={(e) => setFormData({ ...formData, crm: e.target.value.toUpperCase() })}
                    style={inputStyle}
                    placeholder="Ex: CRM-SP-123456"
                />
                {errors.crm && <div style={errorStyle}>{errors.crm}</div>}
            </div>

            {/* Qualification */}
            <div style={{ marginBottom: spacing.md }}>
                <label style={labelStyle}>Qualificação *</label>
                <select
                    value={formData.qualification_code}
                    onChange={(e) => setFormData({ ...formData, qualification_code: e.target.value })}
                    style={inputStyle}
                >
                    <option value="MD">Médico(a)</option>
                    <option value="RN">Enfermeiro(a)</option>
                    <option value="PA">Auxiliar de Enfermagem</option>
                    <option value="PT">Fisioterapeuta</option>
                    <option value="DT">Dentista</option>
                </select>
            </div>

            {/* Specialty */}
            <div style={{ marginBottom: spacing.md }}>
                <label style={labelStyle}>Especialidade *</label>
                <input
                    type="text"
                    value={formData.qualification_display}
                    onChange={(e) => setFormData({ ...formData, qualification_display: e.target.value })}
                    style={inputStyle}
                    placeholder="Ex: Cardiologia, Clínica Geral, etc."
                />
                {errors.qualification_display && <div style={errorStyle}>{errors.qualification_display}</div>}
            </div>

            {/* Gender */}
            <div style={{ marginBottom: spacing.md }}>
                <label style={labelStyle}>Gênero</label>
                <select
                    value={formData.gender}
                    onChange={(e) => setFormData({ ...formData, gender: e.target.value as any })}
                    style={inputStyle}
                >
                    <option value="male">Masculino</option>
                    <option value="female">Feminino</option>
                    <option value="other">Outro</option>
                    <option value="unknown">Não informado</option>
                </select>
            </div>

            {/* Birth Date */}
            <div style={{ marginBottom: spacing.md }}>
                <label style={labelStyle}>Data de Nascimento</label>
                <input
                    type="date"
                    value={formData.birthDate}
                    onChange={(e) => setFormData({ ...formData, birthDate: e.target.value })}
                    style={inputStyle}
                />
            </div>

            {/* Phone */}
            <div style={{ marginBottom: spacing.md }}>
                <label style={labelStyle}>Telefone</label>
                <input
                    type="tel"
                    value={formData.phone}
                    onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                    style={inputStyle}
                    placeholder="(11) 98765-4321"
                />
            </div>

            {/* Email */}
            <div style={{ marginBottom: spacing.md }}>
                <label style={labelStyle}>Email</label>
                <input
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    style={inputStyle}
                    placeholder="exemplo@hospital.com"
                />
                {errors.email && <div style={errorStyle}>{errors.email}</div>}
            </div>

            {/* Actions */}
            <div style={{ display: 'flex', gap: spacing.md, marginTop: spacing.lg }}>
                <Button
                    type="submit"
                    disabled={submitting}
                    style={{ flex: 1 }}
                >
                    {submitting ? 'Salvando...' : 'Salvar Profissional'}
                </Button>
                <Button
                    type="button"
                    variant="secondary"
                    onClick={onCancel}
                    disabled={submitting}
                    style={{ flex: 1 }}
                >
                    Cancelar
                </Button>
            </div>
        </form>
    );
};

export default PractitionerForm;
