import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { usePatients } from '../hooks/usePatients';
import { colors, spacing, borderRadius } from '../theme/colors';
import Card from './base/Card';
import Button from './base/Button';

export const PatientList: React.FC = () => {
    const { patients, loading, error, pagination, nextPage, prevPage } = usePatients();
    const [searchTerm, setSearchTerm] = useState('');
    const navigate = useNavigate();

    const filteredPatients = patients.filter(patient =>
        patient.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        patient.id.toLowerCase().includes(searchTerm.toLowerCase())
    );

    const calculateAge = (birthDate: string) => {
        const today = new Date();
        const birth = new Date(birthDate);
        let age = today.getFullYear() - birth.getFullYear();
        const monthDiff = today.getMonth() - birth.getMonth();
        if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birth.getDate())) {
            age--;
        }
        return age;
    };

    if (loading) {
        return (
            <div style={{ textAlign: 'center', padding: spacing.xl }}>
                <div style={{ fontSize: '2rem', marginBottom: spacing.md }}>⟳</div>
                <p>Carregando pacientes...</p>
            </div>
        );
    }

    return (
        <div style={{ padding: spacing.xl }}>
            {/* Header com busca e botão novo */}
            <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: spacing.lg,
                gap: spacing.md,
                flexWrap: 'wrap'
            }}>
                <input
                    type="text"
                    placeholder="🔍 Buscar paciente por nome ou ID..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    style={{
                        flex: 1,
                        minWidth: '300px',
                        padding: '12px 16px',
                        fontSize: '1rem',
                        border: `1px solid ${colors.border.default}`,
                        borderRadius: borderRadius.base,
                        fontFamily: 'inherit',
                    }}
                />
                <Button
                    variant="primary"
                    size="md"
                    onClick={() => navigate('/patients/new')}
                >
                    + Novo Paciente
                </Button>
            </div>

            {/* Mensagem de erro */}
            {error && (
                <div style={{
                    backgroundColor: `${colors.alert.critical}15`,
                    border: `1px solid ${colors.alert.critical}`,
                    color: colors.alert.critical,
                    padding: spacing.md,
                    borderRadius: borderRadius.base,
                    marginBottom: spacing.lg,
                }}>
                    {error}
                </div>
            )}

            {/* Lista de pacientes */}
            {filteredPatients.length === 0 ? (
                <Card padding="lg" elevation="base">
                    <div style={{ textAlign: 'center', padding: spacing.xl, color: colors.text.tertiary }}>
                        <div style={{ fontSize: '3rem', marginBottom: spacing.md }}>👤</div>
                        <p style={{ fontSize: '1.125rem', marginBottom: spacing.sm }}>
                            {searchTerm ? 'Nenhum paciente encontrado' : 'Nenhum paciente cadastrado'}
                        </p>
                        <p style={{ fontSize: '0.875rem' }}>
                            {searchTerm ? 'Tente outro termo de busca' : 'Clique em "Novo Paciente" para começar'}
                        </p>
                    </div>
                </Card>
            ) : (
                <div style={{ display: 'grid', gap: spacing.md }}>
                    {filteredPatients.map((patient) => (
                        <Card
                            key={patient.id}
                            padding="md"
                            elevation="base"
                            onClick={() => navigate(`/patients/${patient.id}`)}
                            style={{
                                cursor: 'pointer',
                                transition: 'all 200ms ease',
                            }}
                            onMouseEnter={(e) => {
                                e.currentTarget.style.transform = 'translateY(-2px)';
                                e.currentTarget.style.boxShadow = '0 8px 16px rgba(0,0,0,0.1)';
                            }}
                            onMouseLeave={(e) => {
                                e.currentTarget.style.transform = 'translateY(0)';
                                e.currentTarget.style.boxShadow = '0 2px 4px rgba(0,0,0,0.05)';
                            }}
                        >
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <div>
                                    <h3 style={{
                                        margin: 0,
                                        marginBottom: spacing.xs,
                                        fontSize: '1.125rem',
                                        fontWeight: 600,
                                        color: colors.text.primary,
                                    }}>
                                        👤 {patient.name}
                                    </h3>
                                    <div style={{
                                        display: 'flex',
                                        gap: spacing.md,
                                        fontSize: '0.875rem',
                                        color: colors.text.secondary,
                                    }}>
                                        <span>ID: {patient.id}</span>
                                        <span>•</span>
                                        <span>{calculateAge(patient.birthDate)} anos</span>
                                        <span>•</span>
                                        <span>{patient.gender === 'male' ? 'Masculino' : patient.gender === 'female' ? 'Feminino' : 'Outro'}</span>
                                    </div>
                                    {patient.email && (
                                        <div style={{
                                            marginTop: spacing.xs,
                                            fontSize: '0.875rem',
                                            color: colors.text.tertiary,
                                        }}>
                                            📧 {patient.email}
                                        </div>
                                    )}
                                </div>
                                <div style={{
                                    fontSize: '1.5rem',
                                    color: colors.primary.medium,
                                }}>
                                    →
                                </div>
                            </div>
                        </Card>
                    ))}
                </div>
            )}

            {/* Contador */}
            <div style={{
                marginTop: spacing.lg,
                textAlign: 'center',
                fontSize: '0.875rem',
                color: colors.text.tertiary,
            }}>
                {filteredPatients.length} {filteredPatients.length === 1 ? 'paciente' : 'pacientes'}
                {searchTerm && ` encontrado${filteredPatients.length === 1 ? '' : 's'}`}
            </div>

            {/* Paginação */}
            <div style={{
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                gap: spacing.md,
                marginTop: spacing.lg
            }}>
                <Button
                    variant="secondary"
                    size="sm"
                    onClick={prevPage}
                    disabled={pagination.current_page === 1 || loading}
                >
                    ← Anterior
                </Button>
                <div style={{ fontSize: '0.875rem', color: colors.text.secondary }}>
                    Página {pagination.current_page} de {pagination.total_pages}
                </div>
                <Button
                    variant="secondary"
                    size="sm"
                    onClick={nextPage}
                    disabled={pagination.current_page === pagination.total_pages || loading}
                >
                    Próxima →
                </Button>
            </div>
        </div>
    );
};

export default PatientList;
