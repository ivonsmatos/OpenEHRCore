#!/usr/bin/env pwsh
# Script para criar issues no GitHub Projects usando GitHub CLI (gh)
# Pré-requisito: gh CLI instalado e autenticado (gh auth login)

$REPO = "ivonsmatos/OpenEHRCore"
$PROJECT_NUMBER = 1

Write-Host "🚀 Criando issues no GitHub Projects..." -ForegroundColor Green
Write-Host ""

# Função para criar issue
function Create-Issue {
    param(
        [string]$Title,
        [string]$Body,
        [string[]]$Labels,
        [string]$Milestone
    )
    
    $labelArgs = $Labels -join ","
    
    try {
        $issue = gh issue create `
            --repo $REPO `
            --title $Title `
            --body $Body `
            --label $labelArgs `
            --milestone $Milestone
        
        Write-Host "✅ Criada: $Title" -ForegroundColor Green
        return $issue
    } catch {
        Write-Host "❌ Erro ao criar: $Title" -ForegroundColor Red
        Write-Host $_.Exception.Message
    }
}

# Sprint 19: Practitioner Frontend (PRÓXIMO)
Write-Host "📋 Sprint 19: Practitioner Frontend" -ForegroundColor Cyan

Create-Issue `
    -Title "[Sprint 19] PractitionerWorkspace Component" `
    -Body "Criar componente de workspace para listagem de profissionais de saúde.

**Funcionalidades**:
- Lista de profissionais em cards/tabela
- Filtros (nome, especialidade, ativo)
- Botão 'Adicionar Profissional'
- Paginação
- Busca em tempo real

**Estimativa**: 4h
**Prioridade**: Alta" `
    -Labels @("frontend", "practitioner", "sprint-19") `
    -Milestone "Sprint 19"

Create-Issue `
    -Title "[Sprint 19] PractitionerForm Component" `
    -Body "Criar formulário para cadastro/edição de profissionais.

**Campos**:
- Nome completo, CRM, gênero, data nascimento
- Telefone, email
- Qualificação, especialidade

**Validações**:
- CRM: formato CRM-UF-XXXXXX
- Email e telefone válidos

**Estimativa**: 3h
**Prioridade**: Alta" `
    -Labels @("frontend", "practitioner", "forms", "sprint-19") `
    -Milestone "Sprint 19"

Create-Issue `
    -Title "[Sprint 19] PractitionerCard Component" `
    -Body "Criar card para exibição de profissional.

**Exibição**:
- Nome com prefixo
- CRM, especialidade
- Status (ativo/inativo)
- Ações: Ver, Editar, Desativar

**Estimativa**: 2h
**Prioridade**: Média" `
    -Labels @("frontend", "practitioner", "sprint-19") `
    -Milestone "Sprint 19"

Create-Issue `
    -Title "[Sprint 19] PractitionerDetail Component" `
    -Body "Criar componente de detalhes do profissional.

**Seções**:
- Informações pessoais
- Qualificações
- Papéis/Especialidades
- Locais de atuação
- Horários disponíveis

**Estimativa**: 3h
**Prioridade**: Média" `
    -Labels @("frontend", "practitioner", "sprint-19") `
    -Milestone "Sprint 19"

Create-Issue `
    -Title "[Sprint 19] usePractitioners Hook" `
    -Body "Criar hook customizado para integração com API de profissionais.

**Funções**:
- fetchPractitioners (com filtros)
- createPractitioner
- updatePractitioner
- deletePractitioner

**Estimativa**: 2h
**Prioridade**: Alta" `
    -Labels @("frontend", "hooks", "api", "sprint-19") `
    -Milestone "Sprint 19"

# Sprint 20: Busca FHIR Avançada
Write-Host ""
Write-Host "📋 Sprint 20: Busca FHIR Avançada" -ForegroundColor Cyan

Create-Issue `
    -Title "[Sprint 20] Backend: FHIR Search Parameters" `
    -Body "Implementar search parameters FHIR para todos os recursos.

**Recursos**:
- Patient (name, birthdate, identifier)
- Encounter (patient, date, status)
- Observation (patient, code, date)
- Condition (patient, code, clinical-status)
- Practitioner (name, identifier, specialty)

**Estimativa**: 12h total
**Prioridade**: Alta" `
    -Labels @("backend", "fhir", "search", "sprint-20") `
    -Milestone "Sprint 20"

Create-Issue `
    -Title "[Sprint 20] Frontend: SearchBar Component" `
    -Body "Criar componente de busca genérico reutilizável.

**Features**:
- Autocomplete
- Debounce (300ms)
- Filtros avançados
- Histórico de buscas

**Estimativa**: 3h
**Prioridade**: Alta" `
    -Labels @("frontend", "search", "sprint-20") `
    -Milestone "Sprint 20"

# Sprint 23: Testes Automatizados
Write-Host ""
Write-Host "📋 Sprint 23: Testes Automatizados" -ForegroundColor Cyan

Create-Issue `
    -Title "[Sprint 23] Backend Unit Tests (pytest)" `
    -Body "Implementar testes unitários para backend.

**Coverage Target**: > 80%

**Áreas**:
- FHIRService
- Views (todos os views_*.py)
- Authentication
- Utilities

**Estimativa**: 8h
**Prioridade**: Alta" `
    -Labels @("testing", "backend", "qa", "sprint-23") `
    -Milestone "Sprint 23"

Create-Issue `
    -Title "[Sprint 23] Frontend Component Tests" `
    -Body "Implementar testes de componentes React.

**Framework**: Jest + React Testing Library

**Componentes prioritários**:
- PatientDetail
- BedManagementWorkspace
- PractitionerWorkspace
- Forms (todos)

**Estimativa**: 8h
**Prioridade**: Alta" `
    -Labels @("testing", "frontend", "qa", "sprint-23") `
    -Milestone "Sprint 23"

Create-Issue `
    -Title "[Sprint 23] E2E Tests (Playwright)" `
    -Body "Implementar testes end-to-end.

**Fluxos críticos**:
- Login → Dashboard
- Criar paciente → Agendar consulta
- Admitir paciente → Dar alta
- Criar profissional → Atribuir papel

**Estimativa**: 8h
**Prioridade**: Alta" `
    -Labels @("testing", "e2e", "qa", "sprint-23") `
    -Milestone "Sprint 23"

Create-Issue `
    -Title "[Sprint 23] CI/CD - GitHub Actions" `
    -Body "Configurar pipeline CI/CD.

**Jobs**:
- Lint (ESLint, Pylint)
- Tests (pytest, Jest, Playwright)
- Build (Docker images)
- Deploy (staging)

**Estimativa**: 4h
**Prioridade**: Alta" `
    -Labels @("devops", "ci-cd", "sprint-23") `
    -Milestone "Sprint 23"

# Sprint 24: LGPD Compliance
Write-Host ""
Write-Host "📋 Sprint 24: LGPD Compliance" -ForegroundColor Cyan

Create-Issue `
    -Title "[Sprint 24] Consent Resource Implementation" `
    -Body "Implementar recurso FHIR Consent para LGPD.

**Backend**:
- Consent CRUD endpoints
- Tipos de consentimento (tratamento, pesquisa, etc.)

**Frontend**:
- UI de gerenciamento de consentimentos
- Formulário de consentimento

**Estimativa**: 8h
**Prioridade**: Alta (Legal)" `
    -Labels @("fhir", "consent", "lgpd", "sprint-24") `
    -Milestone "Sprint 24"

Create-Issue `
    -Title "[Sprint 24] Privacy Controls - Data Download/Deletion" `
    -Body "Implementar controles de privacidade LGPD Art. 18.

**Funcionalidades**:
- Download de dados do paciente (JSON/PDF)
- Solicitação de exclusão de dados
- Portabilidade de dados

**Estimativa**: 7h
**Prioridade**: Alta (Legal)" `
    -Labels @("security", "lgpd", "privacy", "sprint-24") `
    -Milestone "Sprint 24"

Write-Host ""
Write-Host "✅ Script concluído!" -ForegroundColor Green
Write-Host ""
Write-Host "📝 Próximos passos:" -ForegroundColor Yellow
Write-Host "1. Revisar issues criadas no GitHub"
Write-Host "2. Adicionar ao Project Board manualmente ou via:"
Write-Host "   gh project item-add $PROJECT_NUMBER --owner ivonsmatos --url <issue-url>"
