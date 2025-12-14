/**
 * 🧪 TESTES DE COMPONENTES REACT - PATIENT DETAIL & PATIENT LIST
 * ==================================================================
 * 
 * Testa cenários críticos de UX e resiliência:
 * 1. Renderização com dados nulos/indefinidos
 * 2. Tratamento de erros de API
 * 3. Estados de loading
 * 4. Formatação de CPF
 * 5. Validação de dados FHIR
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { PatientDetail } from '../PatientDetail';
import { PatientList } from '../PatientList';
import { FHIRPatient } from '../../utils/fhirParser';

// Mock do hook usePatients
vi.mock('../../hooks/usePatients', () => ({
    usePatients: vi.fn()
}));

// Mock do react-router-dom
vi.mock('react-router-dom', async () => {
    const actual = await vi.importActual('react-router-dom');
    return {
        ...actual,
        useParams: vi.fn(),
        useNavigate: vi.fn()
    };
});

// ====================================================================
// 1. TESTES DE PATIENTDETAIL - DADOS NULOS/INDEFINIDOS
// ====================================================================

describe('PatientDetail - Null/Undefined Data Handling', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('deve renderizar sem crashes quando patient é undefined', () => {
        const { container } = render(
            <BrowserRouter>
                <PatientDetail patient={undefined} loading={false} />
            </BrowserRouter>
        );
        
        // Não deve causar crash
        expect(container).toBeTruthy();
    });

    it('deve renderizar sem crashes quando patient está vazio', () => {
        const emptyPatient = {} as FHIRPatient;
        
        const { container } = render(
            <BrowserRouter>
                <PatientDetail patient={emptyPatient} loading={false} />
            </BrowserRouter>
        );
        
        // Não deve causar crash
        expect(container).toBeTruthy();
    });

    it('deve tratar graciosamente patient sem campo name', () => {
        const patientSemNome: FHIRPatient = {
            resourceType: 'Patient',
            id: '123',
            // name: MISSING!
            gender: 'male',
            birthDate: '1990-01-01'
        };
        
        render(
            <BrowserRouter>
                <PatientDetail patient={patientSemNome} loading={false} />
            </BrowserRouter>
        );
        
        // Não deve ter erro de "Cannot read property 'given' of undefined"
        // Deve exibir fallback ou campo vazio
        const container = screen.getByTestId?.('patient-detail') || document.body;
        expect(container).toBeTruthy();
    });

    it('deve tratar graciosamente patient sem campo birthDate', () => {
        const patientSemDataNascimento: FHIRPatient = {
            resourceType: 'Patient',
            id: '123',
            name: [{ given: ['João'], family: 'Silva' }],
            gender: 'male'
            // birthDate: MISSING!
        };
        
        render(
            <BrowserRouter>
                <PatientDetail patient={patientSemDataNascimento} loading={false} />
            </BrowserRouter>
        );
        
        // Deve exibir "Idade desconhecida" ou similar
        // Não deve causar erro ao calcular idade
        expect(screen.queryByText(/desconhecid/i)).toBeTruthy();
    });

    it('deve tratar graciosamente patient sem identificador CPF', () => {
        const patientSemCPF: FHIRPatient = {
            resourceType: 'Patient',
            id: '123',
            name: [{ given: ['João'], family: 'Silva' }],
            gender: 'male',
            birthDate: '1990-01-01'
            // identifier: MISSING!
        };
        
        render(
            <BrowserRouter>
                <PatientDetail patient={patientSemCPF} loading={false} />
            </BrowserRouter>
        );
        
        // Não deve causar crash ao tentar extrair CPF
        expect(screen.queryByText(/CPF não cadastrado|Sem CPF/i)).toBeTruthy();
    });

    it('deve tratar múltiplos identificadores conflitantes', () => {
        const patientComMultiplosCPFs: FHIRPatient = {
            resourceType: 'Patient',
            id: '123',
            name: [{ given: ['João'], family: 'Silva' }],
            identifier: [
                {
                    system: 'http://openehrcore.com.br/cpf',
                    value: '12345678900'
                },
                {
                    system: 'http://gov.br/cpf',
                    value: '98765432100' // CPF diferente!
                }
            ]
        };
        
        render(
            <BrowserRouter>
                <PatientDetail patient={patientComMultiplosCPFs} loading={false} />
            </BrowserRouter>
        );
        
        // Deve priorizar o sistema padrão (openehrcore)
        expect(screen.queryByText(/12345678900|123\.456\.789-00/)).toBeTruthy();
    });
});

// ====================================================================
// 2. TESTES DE PATIENTDETAIL - ESTADOS DE ERRO
// ====================================================================

describe('PatientDetail - Error States', () => {
    it('deve exibir mensagem de erro quando API falha', () => {
        const errorMessage = 'FHIR Server unreachable';
        
        render(
            <BrowserRouter>
                <PatientDetail 
                    patient={undefined} 
                    loading={false} 
                    error={errorMessage} 
                />
            </BrowserRouter>
        );
        
        // Deve exibir mensagem de erro para o usuário
        expect(screen.getByText(/erro|error|falha/i)).toBeTruthy();
    });

    it('deve exibir mensagem amigável quando paciente não existe', () => {
        const errorMessage = 'Patient not found';
        
        render(
            <BrowserRouter>
                <PatientDetail 
                    patient={undefined} 
                    loading={false} 
                    error={errorMessage} 
                />
            </BrowserRouter>
        );
        
        // Deve exibir mensagem específica para 404
        expect(screen.getByText(/não encontrado|not found/i)).toBeTruthy();
    });

    it('deve exibir estado de loading enquanto busca dados', () => {
        render(
            <BrowserRouter>
                <PatientDetail 
                    patient={undefined} 
                    loading={true} 
                />
            </BrowserRouter>
        );
        
        // Deve exibir skeleton ou spinner
        expect(screen.getByTestId?.('loading-skeleton') || screen.getByText(/carregando|loading/i)).toBeTruthy();
    });
});

// ====================================================================
// 3. TESTES DE PATIENTDETAIL - FORMATAÇÃO DE CPF
// ====================================================================

describe('PatientDetail - CPF Formatting', () => {
    it('deve formatar CPF com pontuação correta', () => {
        const patientComCPF: FHIRPatient = {
            resourceType: 'Patient',
            id: '123',
            name: [{ given: ['João'], family: 'Silva' }],
            identifier: [
                {
                    system: 'http://openehrcore.com.br/cpf',
                    value: '12345678900' // Sem formatação
                }
            ]
        };
        
        render(
            <BrowserRouter>
                <PatientDetail patient={patientComCPF} loading={false} />
            </BrowserRouter>
        );
        
        // Deve exibir com formatação: 123.456.789-00
        expect(screen.queryByText(/123\.456\.789-00/)).toBeTruthy();
    });

    it('deve aceitar CPF já formatado', () => {
        const patientComCPFFormatado: FHIRPatient = {
            resourceType: 'Patient',
            id: '123',
            name: [{ given: ['João'], family: 'Silva' }],
            identifier: [
                {
                    system: 'http://openehrcore.com.br/cpf',
                    value: '123.456.789-00' // Já formatado
                }
            ]
        };
        
        render(
            <BrowserRouter>
                <PatientDetail patient={patientComCPFFormatado} loading={false} />
            </BrowserRouter>
        );
        
        // Deve exibir corretamente
        expect(screen.queryByText(/123\.456\.789-00/)).toBeTruthy();
    });
});

// ====================================================================
// 4. TESTES DE PATIENTLIST - LISTA VAZIA
// ====================================================================

describe('PatientList - Empty States', () => {
    beforeEach(() => {
        const { usePatients } = require('../../hooks/usePatients');
        usePatients.mockReturnValue({
            patients: [],
            loading: false,
            error: null,
            pagination: { page: 1, page_size: 10, total: 0 },
            fetchPatients: vi.fn(),
            goToPage: vi.fn(),
            setPageSize: vi.fn()
        });
    });

    it('deve exibir mensagem quando não há pacientes cadastrados', () => {
        render(
            <BrowserRouter>
                <PatientList />
            </BrowserRouter>
        );
        
        // Deve exibir mensagem de lista vazia
        expect(screen.getByText(/nenhum paciente|lista vazia|no patients/i)).toBeTruthy();
    });

    it('deve exibir botão para cadastrar novo paciente quando lista vazia', () => {
        render(
            <BrowserRouter>
                <PatientList />
            </BrowserRouter>
        );
        
        // Deve ter call-to-action para criar primeiro paciente
        expect(screen.getByText(/cadastrar|novo paciente|add patient/i)).toBeTruthy();
    });
});

// ====================================================================
// 5. TESTES DE PATIENTLIST - BUSCA SEM RESULTADOS
// ====================================================================

describe('PatientList - Search No Results', () => {
    beforeEach(() => {
        const { usePatients } = require('../../hooks/usePatients');
        usePatients.mockReturnValue({
            patients: [],
            loading: false,
            error: null,
            pagination: { page: 1, page_size: 10, total: 0 },
            fetchPatients: vi.fn(),
            goToPage: vi.fn(),
            setPageSize: vi.fn()
        });
    });

    it('deve exibir mensagem quando busca não retorna resultados', async () => {
        render(
            <BrowserRouter>
                <PatientList />
            </BrowserRouter>
        );
        
        // Simular busca
        const searchInput = screen.getByPlaceholderText(/buscar|search|pesquisar/i);
        fireEvent.change(searchInput, { target: { value: 'Nome Inexistente' } });
        fireEvent.submit(searchInput);
        
        // Deve exibir mensagem de "sem resultados"
        await waitFor(() => {
            expect(screen.getByText(/nenhum resultado|no results|não encontrado/i)).toBeTruthy();
        });
    });

    it('deve permitir limpar filtros quando não há resultados', async () => {
        render(
            <BrowserRouter>
                <PatientList />
            </BrowserRouter>
        );
        
        // Simular busca
        const searchInput = screen.getByPlaceholderText(/buscar|search|pesquisar/i);
        fireEvent.change(searchInput, { target: { value: 'Teste' } });
        
        // Deve ter botão para limpar filtros
        const clearButton = screen.queryByText(/limpar|clear|resetar/i);
        expect(clearButton).toBeTruthy();
    });
});

// ====================================================================
// 6. TESTES DE PATIENTLIST - ERRO DE API
// ====================================================================

describe('PatientList - API Errors', () => {
    beforeEach(() => {
        const { usePatients } = require('../../hooks/usePatients');
        usePatients.mockReturnValue({
            patients: [],
            loading: false,
            error: 'FHIR Server connection timeout',
            pagination: { page: 1, page_size: 10, total: 0 },
            fetchPatients: vi.fn(),
            goToPage: vi.fn(),
            setPageSize: vi.fn()
        });
    });

    it('deve exibir mensagem de erro quando API falha', () => {
        render(
            <BrowserRouter>
                <PatientList />
            </BrowserRouter>
        );
        
        // Deve exibir erro para o usuário
        expect(screen.getByText(/erro|error|falha|timeout/i)).toBeTruthy();
    });

    it('deve exibir botão de retry quando API falha', () => {
        render(
            <BrowserRouter>
                <PatientList />
            </BrowserRouter>
        );
        
        // Deve ter botão para tentar novamente
        expect(screen.getByText(/tentar novamente|retry|recarregar/i)).toBeTruthy();
    });

    it('deve permitir usuário continuar navegando mesmo com erro', () => {
        render(
            <BrowserRouter>
                <PatientList />
            </BrowserRouter>
        );
        
        // Deve ter navegação disponível (não travar a UI)
        const newPatientButton = screen.queryByText(/novo|new|cadastrar/i);
        expect(newPatientButton).toBeTruthy();
        expect(newPatientButton?.hasAttribute('disabled')).toBe(false);
    });
});

// ====================================================================
// 7. TESTES DE PATIENTLIST - PAGINAÇÃO
// ====================================================================

describe('PatientList - Pagination', () => {
    beforeEach(() => {
        const { usePatients } = require('../../hooks/usePatients');
        usePatients.mockReturnValue({
            patients: Array.from({ length: 10 }, (_, i) => ({
                resourceType: 'Patient',
                id: `patient-${i}`,
                name: [{ given: [`Paciente ${i}`], family: 'Silva' }]
            })),
            loading: false,
            error: null,
            pagination: { page: 1, page_size: 10, total: 50 },
            fetchPatients: vi.fn(),
            goToPage: vi.fn(),
            setPageSize: vi.fn()
        });
    });

    it('deve exibir controles de paginação quando há múltiplas páginas', () => {
        render(
            <BrowserRouter>
                <PatientList />
            </BrowserRouter>
        );
        
        // Deve ter botões de navegação
        expect(screen.getByText(/próxima|next|anterior|previous/i)).toBeTruthy();
    });

    it('deve exibir total de resultados', () => {
        render(
            <BrowserRouter>
                <PatientList />
            </BrowserRouter>
        );
        
        // Deve mostrar "Mostrando 1-10 de 50" ou similar
        expect(screen.getByText(/50|total/i)).toBeTruthy();
    });

    it('deve chamar goToPage quando usuário clica em próxima página', () => {
        const { usePatients } = require('../../hooks/usePatients');
        const mockGoToPage = vi.fn();
        
        usePatients.mockReturnValue({
            patients: Array.from({ length: 10 }, (_, i) => ({
                resourceType: 'Patient',
                id: `patient-${i}`,
                name: [{ given: [`Paciente ${i}`], family: 'Silva' }]
            })),
            loading: false,
            error: null,
            pagination: { page: 1, page_size: 10, total: 50 },
            fetchPatients: vi.fn(),
            goToPage: mockGoToPage,
            setPageSize: vi.fn()
        });
        
        render(
            <BrowserRouter>
                <PatientList />
            </BrowserRouter>
        );
        
        const nextButton = screen.getByText(/próxima|next/i);
        fireEvent.click(nextButton);
        
        expect(mockGoToPage).toHaveBeenCalledWith(2);
    });
});

// ====================================================================
// 8. TESTES DE RESILIÊNCIA - FHIR SERVER OFFLINE
// ====================================================================

describe('Patient Components - FHIR Server Offline Scenarios', () => {
    it('PatientDetail deve exibir dados do cache quando servidor offline', async () => {
        // Simular dados em cache
        const cachedPatient: FHIRPatient = {
            resourceType: 'Patient',
            id: '123',
            name: [{ given: ['João'], family: 'Silva' }],
            birthDate: '1990-01-01'
        };
        
        render(
            <BrowserRouter>
                <PatientDetail 
                    patient={cachedPatient} 
                    loading={false}
                    error="FHIR Server offline - showing cached data"
                />
            </BrowserRouter>
        );
        
        // Deve exibir dados do cache
        expect(screen.getByText(/joão silva/i)).toBeTruthy();
        
        // E aviso de que dados podem estar desatualizados
        expect(screen.queryByText(/cache|offline|desatualizado/i)).toBeTruthy();
    });

    it('PatientList deve degradar graciosamente quando servidor offline', () => {
        const { usePatients } = require('../../hooks/usePatients');
        usePatients.mockReturnValue({
            patients: [],
            loading: false,
            error: 'FHIR Server circuit breaker OPEN - retry in 60s',
            pagination: { page: 1, page_size: 10, total: 0 },
            fetchPatients: vi.fn(),
            goToPage: vi.fn(),
            setPageSize: vi.fn()
        });
        
        render(
            <BrowserRouter>
                <PatientList />
            </BrowserRouter>
        );
        
        // Deve exibir mensagem informando circuit breaker
        expect(screen.getByText(/circuit breaker|servidor indisponível|server unavailable/i)).toBeTruthy();
        
        // E quando será possível tentar novamente
        expect(screen.queryByText(/60s|1 minuto|retry/i)).toBeTruthy();
    });
});

// ====================================================================
// 9. TESTES DE VALIDAÇÃO DE DADOS FHIR
// ====================================================================

describe('Patient Components - FHIR Data Validation', () => {
    it('deve rejeitar resourceType inválido', () => {
        const invalidResource = {
            resourceType: 'Observation', // Esperava Patient!
            id: '123',
            name: [{ given: ['João'], family: 'Silva' }]
        } as any;
        
        render(
            <BrowserRouter>
                <PatientDetail patient={invalidResource} loading={false} />
            </BrowserRouter>
        );
        
        // Deve exibir erro de validação
        expect(screen.queryByText(/inválido|invalid|tipo incorreto/i)).toBeTruthy();
    });

    it('deve validar estrutura FHIR antes de renderizar', () => {
        const malformedPatient = {
            // Faltando resourceType!
            id: '123',
            name: 'João Silva' // Formato errado (deveria ser array)
        } as any;
        
        render(
            <BrowserRouter>
                <PatientDetail patient={malformedPatient} loading={false} />
            </BrowserRouter>
        );
        
        // Não deve causar crash
        expect(screen.queryByText(/erro|error|inválido/i)).toBeTruthy();
    });
});

// ====================================================================
// 10. TESTES DE ACESSIBILIDADE
// ====================================================================

describe('Patient Components - Accessibility', () => {
    it('PatientDetail deve ter landmarks ARIA apropriados', () => {
        const patient: FHIRPatient = {
            resourceType: 'Patient',
            id: '123',
            name: [{ given: ['João'], family: 'Silva' }]
        };
        
        const { container } = render(
            <BrowserRouter>
                <PatientDetail patient={patient} loading={false} />
            </BrowserRouter>
        );
        
        // Deve ter role="main" ou similar
        expect(container.querySelector('[role="main"]') || container.querySelector('main')).toBeTruthy();
    });

    it('PatientList deve ter aria-live para atualizações dinâmicas', () => {
        const { usePatients } = require('../../hooks/usePatients');
        usePatients.mockReturnValue({
            patients: [],
            loading: true,
            error: null,
            pagination: { page: 1, page_size: 10, total: 0 },
            fetchPatients: vi.fn(),
            goToPage: vi.fn(),
            setPageSize: vi.fn()
        });
        
        const { container } = render(
            <BrowserRouter>
                <PatientList />
            </BrowserRouter>
        );
        
        // Deve ter aria-live para anunciar mudanças
        expect(container.querySelector('[aria-live]')).toBeTruthy();
    });
});
