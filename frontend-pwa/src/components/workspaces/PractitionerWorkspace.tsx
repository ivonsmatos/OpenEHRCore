import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { colors, spacing } from '../../theme/colors';
import { Practitioner, PractitionerFilters } from '../../types/practitioner';
import { usePractitioners } from '../../hooks/usePractitioners';
import PractitionerCard from '../practitioners/PractitionerCard';
import PractitionerForm from '../practitioners/PractitionerForm';
import Button from '../base/Button';
import Card from '../base/Card';
import { Plus, Search, Filter } from 'lucide-react';

const PractitionerWorkspace: React.FC = () => {
    const navigate = useNavigate();
    const { fetchPractitioners, createPractitioner, loading, error } = usePractitioners();
    const [practitioners, setPractitioners] = useState<Practitioner[]>([]);
    const [showForm, setShowForm] = useState(false);
    const [filters, setFilters] = useState<PractitionerFilters>({
        name: '',
        identifier: '',
        active: null,
    });
    const [searchTerm, setSearchTerm] = useState('');
    const [crmSearch, setCrmSearch] = useState('');

    useEffect(() => {
        loadPractitioners();
    }, []);

    const loadPractitioners = async () => {
        try {
            const response = await fetchPractitioners(filters);
            // Backend returns 'results' key, not 'practitioners'
            setPractitioners(response.results || response.practitioners || []);
        } catch (err) {
            console.error('Error loading practitioners:', err);
        }
    };

    const handleSearch = () => {
        setFilters({
            ...filters,
            name: searchTerm,
            identifier: crmSearch
        });
        loadPractitioners();
    };

    const handleCreatePractitioner = async (data: any) => {
        try {
            await createPractitioner(data);
            setShowForm(false);
            loadPractitioners();
            alert('Profissional criado com sucesso!');
        } catch (err) {
            alert('Erro ao criar profissional. Verifique os dados e tente novamente.');
        }
    };

    if (showForm) {
        return (
            <div style={{ padding: spacing.xl, maxWidth: '800px', margin: '0 auto' }}>
                <h1 style={{ marginBottom: spacing.lg }}>Novo Profissional</h1>
                <Card>
                    <PractitionerForm
                        onSubmit={handleCreatePractitioner}
                        onCancel={() => setShowForm(false)}
                    />
                </Card>
            </div>
        );
    }

    return (
        <div style={{ padding: spacing.xl }}>
            {/* Header */}
            <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: spacing.lg
            }}>
                <div>
                    <h1 style={{ margin: 0, marginBottom: spacing.xs }}>Profissionais de Saúde</h1>
                    <p style={{ margin: 0, color: colors.text.secondary }}>
                        Gerencie médicos, enfermeiros e outros profissionais
                    </p>
                </div>
                <Button onClick={() => setShowForm(true)}>
                    <Plus size={20} style={{ marginRight: spacing.xs }} />
                    Adicionar Profissional
                </Button>
            </div>

            {/* Search and Filters */}
            <Card style={{ marginBottom: spacing.lg }}>
                <div style={{ display: 'flex', gap: spacing.md, flexWrap: 'wrap', alignItems: 'flex-end' }}>
                    {/* Name Search */}
                    <div style={{ flex: 1, minWidth: '200px' }}>
                        <label style={{
                            display: 'block',
                            marginBottom: spacing.xs,
                            fontWeight: 500,
                            color: colors.text.primary
                        }}>
                            Buscar por nome
                        </label>
                        <input
                            type="text"
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                            placeholder="Digite o nome..."
                            style={{
                                width: '100%',
                                padding: spacing.sm,
                                border: `1px solid ${colors.border.light}`,
                                borderRadius: '8px',
                                fontSize: '1rem',
                            }}
                        />
                    </div>

                    {/* CRM Search */}
                    <div style={{ flex: 1, minWidth: '200px' }}>
                        <label style={{
                            display: 'block',
                            marginBottom: spacing.xs,
                            fontWeight: 500,
                            color: colors.text.primary
                        }}>
                            Buscar por CRM
                        </label>
                        <input
                            type="text"
                            value={crmSearch}
                            onChange={(e) => setCrmSearch(e.target.value.toUpperCase())}
                            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                            placeholder="Ex: CRM-SP-123456"
                            style={{
                                width: '100%',
                                padding: spacing.sm,
                                border: `1px solid ${colors.border.light}`,
                                borderRadius: '8px',
                                fontSize: '1rem',
                            }}
                        />
                    </div>

                    {/* Search Button */}
                    <div>
                        <Button onClick={handleSearch} variant="secondary">
                            <Search size={18} style={{ marginRight: spacing.xs }} />
                            Buscar
                        </Button>
                    </div>

                    {/* Status Filter */}
                    <div style={{ minWidth: '150px' }}>
                        <label style={{
                            display: 'block',
                            marginBottom: spacing.xs,
                            fontWeight: 500,
                            color: colors.text.primary
                        }}>
                            Status
                        </label>
                        <select
                            value={filters.active === null ? 'all' : filters.active ? 'active' : 'inactive'}
                            onChange={(e) => {
                                const value = e.target.value;
                                setFilters({
                                    ...filters,
                                    active: value === 'all' ? null : value === 'active'
                                });
                            }}
                            style={{
                                width: '100%',
                                padding: spacing.sm,
                                border: `1px solid ${colors.border.light}`,
                                borderRadius: '8px',
                                fontSize: '1rem',
                            }}
                        >
                            <option value="all">Todos</option>
                            <option value="active">Ativos</option>
                            <option value="inactive">Inativos</option>
                        </select>
                    </div>

                    {/* Apply Filters */}
                    <Button onClick={loadPractitioners} variant="secondary">
                        <Filter size={18} style={{ marginRight: spacing.xs }} />
                        Aplicar Filtros
                    </Button>
                </div>
            </Card>

            {/* Loading State */}
            {loading && (
                <div style={{ textAlign: 'center', padding: spacing.xl, color: colors.text.secondary }}>
                    Carregando profissionais...
                </div>
            )}

            {/* Error State */}
            {error && (
                <Card style={{
                    backgroundColor: '#fef2f2',
                    borderColor: colors.alert.critical,
                    marginBottom: spacing.lg
                }}>
                    <p style={{ color: colors.alert.critical, margin: 0 }}>
                        Erro ao carregar profissionais: {error}
                    </p>
                </Card>
            )}

            {/* Practitioners List */}
            {!loading && !error && (
                <>
                    <div style={{
                        marginBottom: spacing.md,
                        color: colors.text.secondary,
                        fontSize: '0.9rem'
                    }}>
                        {practitioners.length} profissional(is) encontrado(s)
                    </div>

                    {practitioners.length === 0 ? (
                        <Card>
                            <div style={{
                                textAlign: 'center',
                                padding: spacing.xl,
                                color: colors.text.secondary
                            }}>
                                <p style={{ marginBottom: spacing.md }}>
                                    Nenhum profissional encontrado.
                                </p>
                                <Button onClick={() => setShowForm(true)}>
                                    Adicionar Primeiro Profissional
                                </Button>
                            </div>
                        </Card>
                    ) : (
                        <div style={{
                            display: 'grid',
                            gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))',
                            gap: spacing.md
                        }}>
                            {practitioners.map((practitioner) => (
                                <PractitionerCard
                                    key={practitioner.id}
                                    practitioner={practitioner}
                                    onClick={() => {
                                        // Navigate to chat and select this practitioner
                                        sessionStorage.setItem('chat-practitioner', JSON.stringify({
                                            id: practitioner.id,
                                            name: practitioner.name?.[0]?.given?.join(' ') + ' ' + (practitioner.name?.[0]?.family || '')
                                        }));
                                        navigate('/chat');
                                    }}
                                />
                            ))}
                        </div>
                    )}
                </>
            )}
        </div>
    );
};

export default PractitionerWorkspace;
