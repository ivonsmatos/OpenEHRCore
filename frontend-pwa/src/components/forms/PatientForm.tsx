import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { usePatients } from '../../hooks/usePatients';
import { colors, spacing, borderRadius } from '../../theme/colors';
import Card from '../base/Card';
import Button from '../base/Button';
import Header from '../base/Header';

const PatientForm: React.FC = () => {
    const navigate = useNavigate();
    const { createPatient, loading, error } = usePatients();

    const [formData, setFormData] = useState({
        first_name: '',
        last_name: '',
        birth_date: '',
        cpf: '',
        gender: 'male',
        phone: '',
        email: ''
    });

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

            await createPatient(patientData);
            navigate('/'); // Voltar para dashboard
        } catch (err) {
            console.error("Erro ao criar paciente:", err);
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
                    Novo Paciente
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
                            {loading ? 'Salvando...' : 'Cadastrar Paciente'}
                        </Button>
                    </div>
                </form>
            </Card>
        </div>
    );
};

export default PatientForm;
