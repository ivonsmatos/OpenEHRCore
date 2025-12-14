# 🚀 Guia de Correções Rápidas - Design System

**Tempo estimado:** 2-3 horas  
**Impacto:** Alto (melhora consistência, acessibilidade e manutenibilidade)

---

## 📦 1. Substituir Button.tsx Atual

### Passo 1: Backup do arquivo atual

```powershell
# Windows PowerShell
Copy-Item frontend-pwa\src\components\base\Button.tsx frontend-pwa\src\components\base\Button.BACKUP.tsx
```

### Passo 2: Substituir pelo refatorado

```powershell
# Renomear arquivo refatorado
Move-Item -Force `
  frontend-pwa\src\components\base\Button.REFACTORED.tsx `
  frontend-pwa\src\components\base\Button.tsx
```

### Passo 3: Instalar dependências (se necessário)

```powershell
cd frontend-pwa
npm install lucide-react
```

### Passo 4: Testar em todos os pontos de uso

```bash
# Procurar todos os imports
npx grep-it '<Button' --include='*.tsx' --include='*.ts'
```

**Arquivos que usam Button:**

- `PatientDetail.tsx` - ✅ Compatível (já usa props corretas)
- `BillingPage.tsx` - ⚠️ Precisa ajustes (remove inline styles)
- `PractitionerForm.tsx` - ✅ Compatível
- `OrganizationWorkspace.tsx` - ✅ Compatível

---

## 🎨 2. Corrigir BillingPage.tsx (30+ Hardcoded Colors)

### Script de Busca e Substituição

```typescript
// Use VS Code Find & Replace (Ctrl+H) com Regex ativado

// SUBSTITUIÇÃO 1: Cores do header
// BUSCAR:
background: activeTab === tab \? '#1e3a5f' : 'white',\s*color: activeTab === tab \? 'white' : '#1e3a5f'

// SUBSTITUIR POR:
className={cn(
  "px-4 py-2 rounded-md transition-colors",
  activeTab === tab
    ? "bg-primary-dark text-white"
    : "bg-white text-primary-dark hover:bg-primary-light/10"
)}

// SUBSTITUIÇÃO 2: Badges de status
// BUSCAR:
background: claim\.status === 'active' \? '#dbeafe' : '#d1fae5',\s*color: claim\.status === 'active' \? '#1e40af' : '#065f46'

// SUBSTITUIR POR:
className={cn(
  "px-3 py-1 rounded-md text-sm font-medium",
  claim.status === 'active'
    ? "bg-primary-light/20 text-primary-dark"
    : "bg-status-success/20 text-status-success"
)}

// SUBSTITUIÇÃO 3: Títulos
// BUSCAR:
<h([12]) style=\{\{ [^}]*color: '#1e3a5f'[^}]* \}\}>

// SUBSTITUIR POR:
<h$1 className="text-primary-dark font-bold mb-md">
```

### Arquivo Corrigido Completo

**ANTES (linha 107-125):**

```tsx
<div
  style={{
    display: "flex",
    gap: "8px",
    marginBottom: "1.5rem",
    borderBottom: "2px solid #e5e7eb",
  }}
>
  {["dashboard", "claims", "reports"].map((tab) => (
    <button
      key={tab}
      onClick={() => setActiveTab(tab)}
      style={{
        padding: "12px 24px",
        background: activeTab === tab ? "#1e3a5f" : "white",
        color: activeTab === tab ? "white" : "#1e3a5f",
        border: "2px solid #1e3a5f",
        borderRadius: "8px",
        cursor: "pointer",
        transition: "all 0.2s",
      }}
    >
      {tab.charAt(0).toUpperCase() + tab.slice(1)}
    </button>
  ))}
</div>
```

**DEPOIS:**

```tsx
<div className="flex gap-sm mb-lg border-b-2 border-neutral-light">
  {[
    { id: "dashboard", label: "Dashboard" },
    { id: "claims", label: "Guias" },
    { id: "reports", label: "Relatórios" },
  ].map((tab) => (
    <button
      key={tab.id}
      onClick={() => setActiveTab(tab.id)}
      className={cn(
        "px-6 py-3 rounded-t-md font-medium transition-all",
        "focus:outline-none focus:ring-2 focus:ring-primary-dark",
        activeTab === tab.id
          ? "bg-primary-dark text-white shadow-md -mb-0.5 border-b-2 border-primary-dark"
          : "bg-white text-primary-dark hover:bg-primary-light/10 border-b-2 border-transparent"
      )}
      aria-current={activeTab === tab.id ? "page" : undefined}
    >
      {tab.label}
    </button>
  ))}
</div>
```

**Benefícios:**

- ✅ Zero hardcoded colors
- ✅ Usa `cn()` utility para conditional classes
- ✅ Adiciona `aria-current` para acessibilidade
- ✅ Focus ring visível
- ✅ Hover state suave

---

## ♿ 3. Adicionar aria-labels nos Botões de Ícone

### PatientDetail.tsx (linha 203-228)

**Script de Substituição:**

```typescript
// BUSCAR:
<Button variant="secondary" onClick=\{handleEdit\}>\s*✎ Editar\s*</Button>

// SUBSTITUIR POR:
<Button
  variant="secondary"
  onClick={handleEdit}
  aria-label="Editar dados do paciente"
>
  <Edit2 className="w-4 h-4" aria-hidden="true" />
  <span>Editar</span>
</Button>

// BUSCAR:
<Button variant="danger" onClick=\{handleDelete\}>\s*🗑 Excluir\s*</Button>

// SUBSTITUIR POR:
<Button
  variant="danger"
  onClick={handleDelete}
  aria-label="Excluir paciente do sistema"
>
  <Trash2 className="w-4 h-4" aria-hidden="true" />
  <span>Excluir</span>
</Button>
```

### Importar ícones corretos

```typescript
// Adicionar no topo do PatientDetail.tsx
import { Edit2, Trash2, Download, ShieldCheck, Play } from "lucide-react";

// Remover emojis Unicode: ✎, 🗑, ▶
```

---

## 🎯 4. Melhorar Hierarquia Visual

### PatientDetail.tsx - Header Refatorado

**Arquivo completo:** Veja a seção "Melhoria #2" da auditoria.

**Quick Win (apenas estrutura):**

```tsx
// ANTES: 5 botões inline confusos
<div style={{ display: "flex", gap: spacing.sm }}>
  <Button>▶ Iniciar Atendimento</Button>
  <Button><Download /> Exportar</Button>
  <Button><ShieldCheck /> Audit</Button>
  <Button>✎ Editar</Button>
  <Button>🗑 Excluir</Button>
</div>

// DEPOIS: Hierarquia clara
<div className="flex items-center justify-between gap-md">
  {/* Primária - Destaque */}
  <Button variant="primary" size="lg" leftIcon={<Play />}>
    Iniciar Atendimento
  </Button>

  {/* Secundárias - Agrupadas */}
  <div className="flex gap-sm">
    <Button variant="ghost" aria-label="Editar">
      <Edit2 className="w-4 h-4" />
    </Button>
    <Button variant="ghost" aria-label="Exportar">
      <Download className="w-4 h-4" />
    </Button>
  </div>

  {/* Destrutiva - Menu dropdown */}
  <DropdownMenu>
    <DropdownMenuTrigger asChild>
      <Button variant="ghost" size="sm" aria-label="Mais opções">
        <MoreVertical className="w-4 h-4" />
      </Button>
    </DropdownMenuTrigger>
    <DropdownMenuContent>
      <DropdownMenuItem onClick={handleDelete} className="text-alert-critical">
        <Trash2 className="w-4 h-4 mr-2" />
        Excluir Paciente
      </DropdownMenuItem>
    </DropdownMenuContent>
  </DropdownMenu>
</div>
```

---

## 🔍 5. Adicionar ESLint Rule para Prevenir Hardcoded Colors

### .eslintrc.js

```javascript
module.exports = {
  // ... configuração existente
  rules: {
    // ... regras existentes

    /**
     * PROIBIR CORES HEXADECIMAIS HARDCODED
     * Força uso de variáveis do Design System
     */
    "no-restricted-syntax": [
      "error",
      {
        selector: "Literal[value=/#[0-9A-Fa-f]{3,6}/]",
        message:
          "🚨 Use variáveis do Design System (ex: colors.primary.dark) em vez de cores hexadecimais hardcoded",
      },
      {
        selector: "TemplateLiteral[quasis.0.value.raw=/#[0-9A-Fa-f]{3,6}/]",
        message:
          "🚨 Use variáveis do Design System em vez de cores hexadecimais hardcoded",
      },
    ],

    /**
     * AVISAR SOBRE INLINE STYLES COM CORES
     */
    "no-restricted-properties": [
      "warn",
      {
        object: "style",
        property: "backgroundColor",
        message:
          "⚠️ Prefira usar classes Tailwind (bg-*) em vez de inline styles",
      },
      {
        object: "style",
        property: "color",
        message:
          "⚠️ Prefira usar classes Tailwind (text-*) em vez de inline styles",
      },
    ],
  },
};
```

### Testar a regra

```powershell
# Rodar ESLint em BillingPage
npx eslint frontend-pwa/src/pages/BillingPage.tsx

# Deve mostrar ~30 erros de cores hardcoded
```

---

## 📊 6. Validar Contraste de Cores

### Instalar ferramenta de teste

```powershell
npm install --save-dev @axe-core/cli
```

### Criar script de teste

**package.json:**

```json
{
  "scripts": {
    "test:a11y": "axe http://localhost:3000 --tags wcag21aa --save a11y-report.json"
  }
}
```

### Rodar teste

```powershell
# 1. Iniciar app
npm run dev

# 2. Em outro terminal, rodar teste
npm run test:a11y
```

### Interpretar resultados

```json
// a11y-report.json
{
  "violations": [
    {
      "id": "color-contrast",
      "impact": "serious",
      "description": "Contraste insuficiente entre texto e fundo",
      "nodes": [
        {
          "html": "<span style=\"color: white; background: #79ACD9\">Badge</span>",
          "failureSummary": "Contraste 2.94:1 (mínimo: 4.5:1)"
        }
      ]
    }
  ]
}
```

**Correção:**

```tsx
// ❌ ANTES: Contraste 2.94:1 (FALHA)
<span style={{ color: 'white', background: '#79ACD9' }}>
  Badge
</span>

// ✅ DEPOIS: Contraste 9.58:1 (AAA)
<span className="bg-primary-light/20 text-primary-dark">
  Badge
</span>
```

---

## ✅ Checklist de Implementação

### Fase 1: Componentes Base (1h)

- [ ] Substituir `Button.tsx` pelo refatorado
- [ ] Instalar `lucide-react` icons
- [ ] Testar Button em Storybook (se existir)
- [ ] Verificar se todos os imports funcionam

### Fase 2: Páginas Críticas (2h)

- [ ] Refatorar `BillingPage.tsx` (substituir 30 cores)
- [ ] Refatorar `PatientDetail.tsx` (adicionar aria-labels)
- [ ] Adicionar imports de ícones do `lucide-react`
- [ ] Remover todos os emojis Unicode (▶, ✎, 🗑)

### Fase 3: Qualidade (30min)

- [ ] Adicionar regra ESLint para cores hardcoded
- [ ] Rodar `npm run lint` e corrigir warnings
- [ ] Rodar teste de acessibilidade `@axe-core/cli`
- [ ] Documentar mudanças no CHANGELOG.md

### Fase 4: Testes (30min)

- [ ] Testar navegação por teclado (Tab, Enter, Esc)
- [ ] Testar com leitor de tela (NVDA/VoiceOver)
- [ ] Verificar contraste no modo claro
- [ ] Verificar responsividade (mobile, tablet, desktop)

---

## 🎯 Resultados Esperados

### Antes (Scorecard: 6.5/10)

- ❌ 30+ cores hardcoded em BillingPage
- ❌ Button com anti-pattern (dupla definição)
- ❌ Emojis inacessíveis (✎, 🗑, ▶)
- ❌ Sem aria-labels em botões de ícone
- ❌ Contraste insuficiente em alguns badges

### Depois (Scorecard Esperado: 9/10)

- ✅ **Zero cores hardcoded** (100% Design System)
- ✅ Button limpo (apenas Tailwind classes)
- ✅ Ícones SVG acessíveis (lucide-react)
- ✅ Todos os botões com aria-labels
- ✅ Contraste WCAG 2.1 AA em todos os elementos
- ✅ ESLint previne regressões

---

## 📚 Documentação Adicional

### Guia de Estilo Completo

Criar arquivo `DESIGN_SYSTEM.md`:

```markdown
# Design System - OpenEHR PWA

## Cores

### Primárias

- `bg-primary-dark` (#0339A6) - Ações principais
- `bg-primary-medium` (#0468BF) - Botões primary
- `bg-primary-light` (#79ACD9) - Backgrounds suaves

### Semânticas

- `bg-alert-critical` (#D91A1A) - Erros, exclusões
- `bg-status-success` (#10b981) - Sucesso, confirmações
- `bg-alert-warning` (#f59e0b) - Avisos

### Neutrals

- `bg-background-surface` (#F2F2F2) - Fundo cards
- `text-neutral-dark` (#64748b) - Texto secundário

## Spacing

- `gap-xs` (0.5rem / 4px)
- `gap-sm` (1rem / 8px)
- `gap-md` (1.5rem / 12px)
- `gap-lg` (2rem / 16px)
- `gap-xl` (3rem / 24px)

## Typography

- `text-xs` (0.75rem) - Labels
- `text-sm` (0.875rem) - Body
- `text-base` (1rem) - Default
- `text-lg` (1.125rem) - Subtitles
- `text-xl` (1.25rem) - Titles

## Exemplos

### Botão Primário

\`\`\`tsx
<Button variant="primary" size="md">
Salvar Prontuário
</Button>
\`\`\`

### Badge de Status

\`\`\`tsx
<span className="bg-status-success/20 text-status-success px-3 py-1 rounded-md text-sm">
Ativo
</span>
\`\`\`
```

---

**Tempo total estimado:** 3-4 horas  
**Impacto:** 🔥 Alto (melhora UX, acessibilidade e manutenibilidade)  
**Prioridade:** 🔴 Crítica
