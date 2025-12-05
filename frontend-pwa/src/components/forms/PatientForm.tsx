import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { usePatients, Patient } from '../../hooks/usePatients';
import { colors, spacing, borderRadius } from '../../theme/colors';
import Card from '../base/Card';
import Button from '../base/Button';
import Header from '../base/Header';
import { FHIRPatient, getPatientSummary } from '../../utils/fhirParser';

const PatientForm: React.FC = () => {
    const navigate = useNavigate();
    const location = useLocation();
    const { createPatient, updatePatient, loading, error } = usePatients();

    // Check if we are editing
    const editingPatient = location.state?.patient as FHIRPatient | undefined;
    const isEditing = !!editingPatient;

    const [formData, setFormData] = useState({
        first_name: '',
        last_name: '',
        birth_date: '',
        cpf: '',
        gender: 'male',
        phone: '',
        email: ''
    });

    useEffect(() => {
        if (editingPatient) {
            const summary = getPatientSummary(editingPatient);
            // Parsing names logic simplified for this form
            const given = editingPatient.name?.[0]?.given?.join(' ') || '';
            const family = editingPatient.name?.[0]?.family || '';

            // Extract phone and email
            const phone = editingPatient.telecom?.find(t => t.system === 'phone')?.value || '';
            const email = editingPatient.telecom?.find(t => t.system === 'email')?.value || '';

            setFormData({
                first_name: given,
                last_name: family,
                birth_date: editingPatient.birthDate || '',
                cpf: summary.cpf || '',
                gender: editingPatient.gender || 'unknown',
                phone: phone,
                email: email
            });
        }
    }, [editingPatient]);

    const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            // Formatar dados para o backend
            const patientData = {
                first_name: formData.first_name,
                last_name: formData.last_name,
                birth_date: formData.birth_date,
                cpf: formData.cpf,
                gender: formData.gender,
                telecom: [
                    { system: 'phone', value: formData.phone },
                    { system: 'email', value: formData.email }
                ].filter(t => t.value) // Remover vazios
            };

            if (isEditing && editingPatient?.id) {
                await updatePatient(editingPatient.id, patientData);
            } else {
                await createPatient(patientData);
            }

            navigate('/'); // Voltar para dashboard
        } catch (err) {
            console.error("Erro ao salvar paciente:", err);
        }
    };

    const inputStyle = {
        width: '100%',
        padding: '10px',
        borderRadius: borderRadius.base,
        border: `1px solid ${colors.border.default}`,
        fontSize: '1rem',
        marginTop: spacing.xs,
        marginBottom: spacing.md,
        fontFamily: 'inherit'
    };

    const labelStyle = {
        display: 'block',
        fontSize: '0.875rem',
        fontWeight: 600,
        color: colors.text.secondary,
    };

    return (
        <div>
            <div style={{ marginBottom: spacing.lg }}>
                <Button variant="secondary" size="sm" onClick={() => navigate('/')}>
                    ← Voltar para Dashboard
                </Button>
            </div>

            <Card padding="lg" elevation="base">
                <h2 style={{
                    marginTop: 0,
                    color: colors.text.primary,
                    borderBottom: `1px solid ${colors.border.light}`,
                    paddingBottom: spacing.md,
                    marginBottom: spacing.lg
                }}>
                    {isEditing ? 'Editar Paciente' : 'Novo Paciente'}
                </h2>

                {error && (
                    <div style={{
                        backgroundColor: `${colors.alert.critical}15`,
                        color: colors.alert.critical,
                        padding: spacing.md,
                        borderRadius: borderRadius.base,
                        marginBottom: spacing.lg
                    }}>
                        {error}
                    </div>
                )}

                <form onSubmit={handleSubmit}>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: spacing.md }}>
                        <div>
                            <label style={labelStyle}>Nome *</label>
                            <input
                                required
                                name="first_name"
                                value={formData.first_name}
                                onChange={handleChange}
                                style={inputStyle}
                                placeholder="Ex: João"
                            />
                        </div>
                        <div>
                            <label style={labelStyle}>Sobrenome *</label>
                            <input
                                required
                                name="last_name"
                                value={formData.last_name}
                                onChange={handleChange}
                                style={inputStyle}
                                placeholder="Ex: Silva"
                            />
                        </div>
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: spacing.md }}>
                        <div>
                            <label style={labelStyle}>Data de Nascimento *</label>
                            <input
                                required
                                type="date"
                                name="birth_date"
                                value={formData.birth_date}
                                onChange={handleChange}
                                style={inputStyle}
                            />
                        </div>
                        <div>
                            <label style={labelStyle}>CPF</label>
                            <input
                                name="cpf"
                                value={formData.cpf}
                                onChange={handleChange}
                                style={inputStyle}
                                placeholder="000.000.000-00"
                            />
                        </div>
                        <div>
                            <label style={labelStyle}>Gênero *</label>
                            <select
                                name="gender"
                                value={formData.gender}
                                onChange={handleChange}
                                style={inputStyle}
                            >
                                <option value="male">Masculino</option>
                                <option value="female">Feminino</option>
                                <option value="other">Outro</option>
                                <option value="unknown">Desconhecido</option>
                            </select>
                        </div>
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: spacing.md }}>
                        <div>
                            <label style={labelStyle}>Telefone</label>
                            <input
                                name="phone"
                                value={formData.phone}
                                onChange={handleChange}
                                style={inputStyle}
                                placeholder="(00) 00000-0000"
                            />
                        </div>
                        <div>
                            <label style={labelStyle}>Email</label>
                            <input
                                type="email"
                                name="email"
                                value={formData.email}
                                onChange={handleChange}
                                style={inputStyle}
                                placeholder="email@exemplo.com"
                            />
                        </div>
                    </div>

                    <div style={{ display: 'flex', justifyContent: 'flex-end', gap: spacing.md, marginTop: spacing.lg }}>
                        <Button
                            type="button"
                            variant="secondary"
                            onClick={() => navigate('/')}
                            disabled={loading}
                        >
                            Cancelar
                        </Button>
                        <Button
                            type="submit"
                            variant="primary"
                            disabled={loading}
                        >
                            {loading ? 'Salvando...' : (isEditing ? 'Salvar Alterações' : 'Cadastrar Paciente')}
                        </Button>
                    </div>
                </form>
            </Card>
        </div>
    );
};

export default PatientForm;
