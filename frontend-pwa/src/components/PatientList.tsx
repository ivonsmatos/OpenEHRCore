import React, { useState, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { usePatients, PatientSearchFilters } from '../hooks/usePatients';
import Card from './base/Card';
import Button from './base/Button';
import SearchBar from './base/SearchBar';
import AdvancedFilters, { FilterConfig } from './base/AdvancedFilters';
import PaginatedResults from './base/PaginatedResults';
import './PatientList.css';

export const PatientList: React.FC = () => {
    const {
        patients,
        loading,
        error,
        pagination,
        fetchPatients,
        goToPage,
        setPageSize
    } = usePatients();

    const [searchTerm, setSearchTerm] = useState('');
    const [advancedFilters, setAdvancedFilters] = useState<Record<string, any>>({});
    const navigate = useNavigate();

    // Filter configurations for AdvancedFilters component
    const filterConfigs: FilterConfig[] = useMemo(() => [
        {
            key: 'identifier',
            label: 'CPF',
            type: 'text',
            placeholder: 'Ex: 123.456.789-00'
        },
        {
            key: 'gender',
            label: 'Gênero',
            type: 'select',
            options: [
                { value: 'male', label: 'Masculino' },
                { value: 'female', label: 'Feminino' },
                { value: 'other', label: 'Outro' },
                { value: 'unknown', label: 'Não informado' }
            ]
        },
        {
            key: 'birthdate',
            label: 'Data de Nascimento',
            type: 'daterange',
        }
    ], []);

    // Execute search with current filters
    const executeSearch = useCallback((query: string) => {
        setSearchTerm(query);
        const filters: PatientSearchFilters = { name: query };

        // Parse advanced filters
        if (advancedFilters.identifier) {
            filters.identifier = advancedFilters.identifier;
        }
        if (advancedFilters.gender) {
            filters.gender = advancedFilters.gender;
        }
        if (advancedFilters.birthdate) {
            const [start, end] = advancedFilters.birthdate.split(',');
            if (start) filters.birthdateGe = start;
            if (end) filters.birthdateLe = end;
        }

        fetchPatients(1, pagination.page_size, filters);
    }, [advancedFilters, fetchPatients, pagination.page_size]);

    // Apply advanced filters
    const handleApplyFilters = useCallback(() => {
        executeSearch(searchTerm);
    }, [executeSearch, searchTerm]);

    // Clear all filters
    const handleClearFilters = useCallback(() => {
        setAdvancedFilters({});
        setSearchTerm('');
        fetchPatients(1, pagination.page_size, {});
    }, [fetchPatients, pagination.page_size]);

    // Handle page change
    const handlePageChange = useCallback((page: number) => {
        goToPage(page);
    }, [goToPage]);

    // Handle page size change
    const handlePageSizeChange = useCallback((size: number) => {
        setPageSize(size);
    }, [setPageSize]);

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

    if (loading && patients.length === 0) {
        return (
            <div className="patient-list__loading">
                <div className="patient-list__loading-spinner">⟳</div>
                <p>Carregando pacientes...</p>
            </div>
        );
    }

    return (
        <div className="patient-list">
            {/* Header com busca e botão novo */}
            <div className="patient-list__header">
                <div className="patient-list__search-wrapper">
                    <SearchBar
                        placeholder="🔍 Buscar paciente por nome..."
                        onSearch={executeSearch}
                        loading={loading}
                        initialValue={searchTerm}
                        debounceMs={300}
                    />
                </div>
                <Button
                    variant="primary"
                    size="md"
                    onClick={() => navigate('/patients/new')}
                >
                    + Novo Paciente
                </Button>
            </div>

            {/* Filtros avançados */}
            <AdvancedFilters
                filters={filterConfigs}
                values={advancedFilters}
                onChange={setAdvancedFilters}
                onApply={handleApplyFilters}
                onClear={handleClearFilters}
                defaultCollapsed={true}
            />

            {/* Mensagem de erro */}
            {error && (
                <div className="patient-list__error">
                    {error}
                </div>
            )}

            {/* Lista de pacientes */}
            {patients.length === 0 ? (
                <Card padding="lg" elevation="base">
                    <div className="patient-list__empty">
                        <div className="patient-list__empty-icon">👤</div>
                        <p className="patient-list__empty-title">
                            {searchTerm || Object.keys(advancedFilters).length > 0
                                ? 'Nenhum paciente encontrado'
                                : 'Nenhum paciente cadastrado'}
                        </p>
                        <p className="patient-list__empty-subtitle">
                            {searchTerm || Object.keys(advancedFilters).length > 0
                                ? 'Tente outros filtros ou termos de busca'
                                : 'Clique em "Novo Paciente" para começar'}
                        </p>
                    </div>
                </Card>
            ) : (
                <div className="patient-list__grid">
                    {patients.map((patient) => (
                        <Card
                            key={patient.id}
                            padding="md"
                            elevation="base"
                            onClick={() => navigate(`/patients/${patient.id}`)}
                            className="patient-card"
                        >
                            <div className="patient-card__content">
                                <div>
                                    <h3 className="patient-card__name">
                                        👤 {patient.name}
                                    </h3>
                                    <div className="patient-card__info">
                                        <span>ID: {patient.id}</span>
                                        <span>•</span>
                                        <span>{calculateAge(patient.birthDate)} anos</span>
                                        <span>•</span>
                                        <span>{patient.gender === 'male' ? 'Masculino' : patient.gender === 'female' ? 'Feminino' : 'Outro'}</span>
                                    </div>
                                    {patient.email && (
                                        <div className="patient-card__email">
                                            📧 {patient.email}
                                        </div>
                                    )}
                                </div>
                                <div className="patient-card__arrow">
                                    →
                                </div>
                            </div>
                        </Card>
                    ))}
                </div>
            )}

            {/* Paginação */}
            {pagination.total_count > 0 && (
                <div className="patient-list__pagination">
                    <PaginatedResults
                        total={pagination.total_count}
                        currentPage={pagination.current_page}
                        pageSize={pagination.page_size}
                        onPageChange={handlePageChange}
                        onPageSizeChange={handlePageSizeChange}
                        loading={loading}
                    />
                </div>
            )}
        </div>
    );
};

export default PatientList;
