# Guia: Como Adicionar Tasks ao GitHub Projects

## Opção 1: Importar CSV (Recomendado - Mais Rápido)

### Passo 1: Preparar o CSV
O arquivo `github_project_tasks.csv` já está pronto com todas as tasks.

### Passo 2: Importar no GitHub Projects
1. Acesse: https://github.com/users/ivonsmatos/projects/1
2. Clique no botão **"+"** (Add item)
3. Selecione **"Import from CSV"** ou **"Bulk add"**
4. Faça upload do arquivo `github_project_tasks.csv`
5. Mapeie as colunas:
   - Title → Title
   - Status → Status
   - Priority → Custom field "Priority"
   - Sprint → Custom field "Sprint"
   - Labels → Labels

**Nota**: Se o GitHub Projects não suportar import direto de CSV, use a Opção 2.

---

## Opção 2: Usar GitHub CLI (Automático)

### Pré-requisitos
1. Instalar GitHub CLI: https://cli.github.com/
2. Autenticar:
   ```powershell
   gh auth login
   ```

### Passo 1: Criar Milestones
```powershell
gh milestone create "Sprint 19" --repo ivonsmatos/OpenEHRCore --description "Practitioner Frontend"
gh milestone create "Sprint 20" --repo ivonsmatos/OpenEHRCore --description "FHIR Advanced Search"
gh milestone create "Sprint 23" --repo ivonsmatos/OpenEHRCore --description "Automated Testing"
gh milestone create "Sprint 24" --repo ivonsmatos/OpenEHRCore --description "LGPD Compliance"
```

### Passo 2: Executar Script
```powershell
cd C:\Users\ivonm\OneDrive\Documents\GitHub\OpenEHRCore
.\create_github_issues.ps1
```

### Passo 3: Adicionar Issues ao Project
Após criar as issues, adicione ao project:
```powershell
# Para cada issue criada
gh project item-add 1 --owner ivonsmatos --url <issue-url>
```

Ou use o script automático (se disponível):
```powershell
# Listar todas as issues
$issues = gh issue list --repo ivonsmatos/OpenEHRCore --limit 100 --json number,url

# Adicionar ao project
foreach ($issue in $issues) {
    gh project item-add 1 --owner ivonsmatos --url $issue.url
}
```

---

## Opção 3: Manual (Mais Trabalhoso)

### Para cada task no arquivo CSV:

1. Acesse: https://github.com/ivonsmatos/OpenEHRCore/issues/new
2. Preencha:
   - **Title**: Copie da coluna "Title"
   - **Description**: Adicione detalhes do Sprint
   - **Labels**: Adicione as labels da coluna "Labels"
   - **Milestone**: Selecione o Sprint correspondente
3. Clique em **"Submit new issue"**
4. Vá para o Project: https://github.com/users/ivonsmatos/projects/1
5. Clique em **"Add item"** e selecione a issue criada
6. Configure:
   - **Status**: "To Do" ou "Done" conforme CSV
   - **Priority**: Alta/Média/Baixa
   - **Sprint**: Sprint correspondente

---

## Resumo de Tasks

### ✅ Concluídas (32 tasks)
- Sprints 1-18 completos
- FHIR R4 ~95% compliant
- Backend Practitioner API
- Gestão de Leitos completa

### 🚧 Pendentes (53 tasks)

**Sprint 19** (8 tasks) - Practitioner Frontend
**Sprint 20** (10 tasks) - Busca FHIR Avançada
**Sprint 21** (5 tasks) - Terminologias
**Sprint 22** (7 tasks) - Bulk Data & Interop
**Sprint 23** (8 tasks) - Testes Automatizados
**Sprint 24** (6 tasks) - LGPD Compliance
**Sprint 25** (6 tasks) - Performance
**Sprint 26** (4 tasks) - Mobile App

---

## Estrutura de Labels Sugerida

Crie estas labels no repositório:

**Por Tipo**:
- `frontend` (azul)
- `backend` (verde)
- `fhir` (roxo)
- `testing` (amarelo)
- `documentation` (cinza)

**Por Prioridade**:
- `priority: high` (vermelho)
- `priority: medium` (laranja)
- `priority: low` (verde claro)

**Por Sprint**:
- `sprint-19`, `sprint-20`, etc.

**Por Feature**:
- `practitioner`, `patient`, `ipd`, `search`, etc.

---

## Comandos Úteis GitHub CLI

```powershell
# Listar issues
gh issue list --repo ivonsmatos/OpenEHRCore

# Criar label
gh label create "sprint-19" --color "0366d6" --repo ivonsmatos/OpenEHRCore

# Ver project
gh project view 1 --owner ivonsmatos

# Adicionar issue ao project
gh project item-add 1 --owner ivonsmatos --url https://github.com/ivonsmatos/OpenEHRCore/issues/1
```

---

## Recomendação

**Use Opção 2 (GitHub CLI)** para automação completa. Se não funcionar, use **Opção 1 (CSV)** para import em massa.
