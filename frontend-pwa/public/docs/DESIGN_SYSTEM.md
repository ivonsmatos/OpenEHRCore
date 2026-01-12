# Design System — OpenEHRCore

## 🎨 Paleta de Cores Institucional

A paleta foi projetada para transmitir **confiança**, **profissionalismo** e **segurança** — essencial em contextos de saúde.

### Cores Primárias

| Cor                  | Hex       | Uso                                  | WCAG |
| -------------------- | --------- | ------------------------------------ | ---- |
| **Primary Dark**     | `#0339A6` | Menu, header, elementos de confiança | AAA  |
| **Primary Medium**   | `#0468BF` | Botões, ações principais, links      | AAA  |
| **Secondary/Accent** | `#79ACD9` | Destaques suaves, badges             | AAA  |
| **Alert/Critical**   | `#D91A1A` | Erros, alertas médicos (risco)       | AAA  |
| **Background**       | `#F2F2F2` | Fundo geral (clean design)           | AAA  |

### Cores Neutras

| Cor         | Hex       | Uso                               |
| ----------- | --------- | --------------------------------- |
| **Light**   | `#EBEFF2` | Fundo muito claro, dividers sutis |
| **Lighter** | `#C5D0D9` | Bordas padrão, placeholders       |
| **Base**    | `#A3B2BF` | Textos secundários                |
| **Dark**    | `#595959` | Textos padrão                     |
| **Darkest** | `#0D0D0D` | Textos muito escuros, quase preto |

### Semântica de Cores

```
🟦 Confiança (Primary Dark)    → Autoridade, segurança
🟦 Ação (Primary Medium)       → Call-to-action, clicável
🟦 Destaque (Secondary)        → Informação importante
🔴 Alerta (Critical)           → Perigo, erro, ação crítica
⚪ Clean (Background)          → Espaço em branco, respiro visual
```

## 📐 Tipografia

### Escala

```
h1:   30px (1.875rem)  — Títulos principais
h2:   24px (1.5rem)    — Títulos de seção
h3:   20px (1.25rem)   — Subtítulos
body-lg: 18px (1.125rem)
body:    16px (1rem)   — Texto padrão
body-sm: 14px (0.875rem)
label:   14px (0.875rem) — Labels de campo
hint:    12px (0.75rem)  — Textos pequenos
```

### Fonte

- **Família**: Inter, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif
- **Pesos**: 400 (normal), 500 (medium), 600 (semibold), 700 (bold)
- **Line Height**: 1.5rem base (150%)

### Exemplos

```html
<h1 style="font-size: 1.875rem; font-weight: 700;">Prontuário do Paciente</h1>

<p style="font-size: 1rem; font-weight: 400; line-height: 1.5rem;">
  Informações clínicas do paciente...
</p>

<label style="font-size: 0.875rem; font-weight: 600;">
  Data de Nascimento
</label>
```

## 📏 Espaçamento (Whitespace Generoso)

Base: **8px** (escala octave)

```
xs:  8px  (0.5rem)   — Gaps pequenos entre elementos
sm: 16px  (1rem)     — Padding padrão
md: 24px  (1.5rem)   — Spacing entre sections
lg: 32px  (2rem)     — Padding de containers
xl: 48px  (3rem)     — Spacing principal (viewport)
```

### Aplicação

```html
<!-- Padding em card -->
<div style="padding: 24px;">Conteúdo com espaço generoso</div>

<!-- Gap entre elementos -->
<div style="display: flex; gap: 16px;">
  <button>Botão 1</button>
  <button>Botão 2</button>
</div>

<!-- Margin bottom entre seções -->
<section style="margin-bottom: 48px;">Seção 1</section>
<section>Seção 2</section>
```

## 🔲 Bordas e Raios

### Border Radius

```
soft:  6px  (0.375rem)   — Bordas suaves (inputs, chips)
base:  8px  (0.5rem)     — Padrão (botões, cards pequenos)
md:   12px  (0.75rem)    — Médio (modals)
lg:   16px  (1rem)       — Grande (cards principais)
full: 9999px             — Completo (badges, avatars)
```

### Bordas (Stroke)

```
color: #EBEFF2    — Muito sutil
color: #C5D0D9    — Padrão
color: #A3B2BF    — Mais forte

width: 1px        — Padrão
width: 2px        — Destaque (inputs focus)
```

## 🌈 Sombras (Profundidade)

### Escala de Sombras

```typescript
soft: "0 1px 3px rgba(0, 0, 0, 0.1)";
base: "0 4px 6px rgba(0, 0, 0, 0.1), 0 2px 4px rgba(0, 0, 0, 0.06)";
md: "0 10px 15px rgba(0, 0, 0, 0.1), 0 4px 6px rgba(0, 0, 0, 0.05)";
lg: "0 20px 25px rgba(0, 0, 0, 0.1), 0 10px 10px rgba(0, 0, 0, 0.04)";
```

### Aplicação

```html
<!-- Shadow soft para hover -->
<div style="box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);">Card leve</div>

<!-- Shadow base para cards normais -->
<div style="box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">Card padrão</div>

<!-- Shadow lg para modals -->
<div style="box-shadow: 0 20px 25px rgba(0, 0, 0, 0.1);">Modal grande</div>
```

## 🔘 Componentes Base

### Button

```typescript
interface ButtonProps {
  variant?: "primary" | "secondary" | "danger" | "ghost";
  size?: "sm" | "md" | "lg";
  disabled?: boolean;
  children: React.ReactNode;
}
```

#### Variantes

```
primary  → Bg: Primary Medium, Text: Branco (ações principais)
secondary → Bg: Neutral Light, Text: Darkest (ações secundárias)
danger   → Bg: Alert Critical, Text: Branco (destrutivas)
ghost    → Bg: Transparente, Text: Primary (links)
```

#### Tamanhos

```
sm  → 8px padding, 14px text
md  → 12px padding, 16px text  (padrão)
lg  → 16px padding, 18px text
```

**Exemplo:**

```tsx
<Button variant="primary" size="md">
  Salvar Paciente
</Button>

<Button variant="danger" size="sm">
  Deletar
</Button>

<Button variant="ghost">
  Cancelar
</Button>
```

### Card

```typescript
interface CardProps {
  children: React.ReactNode;
  padding?: "sm" | "md" | "lg";
  elevation?: "none" | "soft" | "base" | "md";
  onClick?: () => void;
}
```

**Características:**

- Fundo branco puro (`#FFFFFF`)
- Borda 1px em `#EBEFF2`
- Shadow padrão (`base`)
- Padding generoso

**Exemplo:**

```tsx
<Card padding="lg" elevation="base">
  <h3>Dados Pessoais</h3>
  <p>João Silva, 38 anos</p>
</Card>
```

### Header

```typescript
interface HeaderProps {
  title: string;
  subtitle?: string;
  children?: React.ReactNode;
}
```

**Características:**

- Fundo Primary Dark (`#0339A6`)
- Texto branco
- Padding xl (48px)
- Shadow sutil

**Exemplo:**

```tsx
<Header title="Prontuário do Paciente" subtitle="ID: patient-123">
  <Button variant="secondary" size="sm">
    Editar
  </Button>
</Header>
```

## ✨ Principios de Design

### 1. **Whitespace is Beautiful**

- Não tenha medo de espaço em branco
- Respire visualmente (padding xl entre sections)
- Menos é mais

### 2. **Tipografia Hierárquica**

- h1, h2, h3 para estrutura clara
- Textos em escala bem definida
- Labels para campos obrigatórios

### 3. **Contraste WCAG AAA**

- Todos os textos com contraste ≥ 7:1
- Cores acessíveis para daltonismo
- Responsive design mobile-first

### 4. **Feedback Claro**

- Hover states em botões
- Erros em Alert Red (`#D91A1A`)
- Sucesso em verde (extensão)
- Loading spinners para ações async

### 5. **Minimalismo**

- UI não pode parecer "sistema antigo de hospital"
- Foco em dados clínicos, não em decoração
- Transições suaves (250ms base)

## 🎯 Layout Patterns

### Card Grid (Dados do Paciente)

```html
<div
  style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 24px;"
>
  <Card>Nome</Card>
  <Card>Data Nascimento</Card>
  <Card>Gênero</Card>
</div>
```

### Section Spacing

```html
<div style="max-width: 1200px; margin: 0 auto; padding: 48px;">
  <section style="margin-bottom: 48px;">
    <h2>Dados Pessoais</h2>
    <!-- conteúdo -->
  </section>

  <section style="margin-bottom: 48px;">
    <h2>Contatos</h2>
    <!-- conteúdo -->
  </section>
</div>
```

### Form Fields

```html
<div style="margin-bottom: 24px;">
  <label style="font-size: 14px; font-weight: 600; margin-bottom: 8px;">
    Nome do Paciente *
  </label>
  <input
    type="text"
    style="width: 100%; padding: 12px; border-radius: 8px; border: 1px solid #C5D0D9;"
  />
</div>
```

## 🌐 Responsividade

### Breakpoints

```typescript
sm:  640px   (mobile)
md:  768px   (tablet)
lg: 1024px   (desktop)
xl: 1280px   (large desktop)
```

### Mobile-First Approach

```html
<!-- Mobile: 1 coluna -->
<div style="display: flex; flex-direction: column;">
  <Card>Card 1</Card>
  <Card>Card 2</Card>
</div>

<!-- Desktop: 2 colunas (via media query ou grid) -->
@media (min-width: 768px) { display: grid; grid-template-columns: repeat(2,
1fr); gap: 24px; }
```

## 🎬 Animações

### Transitions

```
fast:   150ms ease-in-out  (hover rápido)
base:   250ms ease-in-out  (padrão)
slow:   350ms ease-in-out  (modals, grandes mudanças)
```

**Exemplo:**

```css
button {
  transition: all 250ms ease-in-out;
}

button:hover {
  opacity: 0.9;
  box-shadow: 0 4px 12px rgba(3, 57, 166, 0.2);
}
```

## 📱 Estado dos Componentes

### Button States

```
default  → cor normal
hover    → opacidade 0.9 + shadow base
active   → opacidade 0.95
focus    → ring 2px da cor, offset 2px
disabled → opacity 0.5, cursor not-allowed
loading  → spinner + disabled
```

### Card States

```
default  → shadow base
hover    → shadow md (se clicável)
loading  → opacity 0.7
error    → border red, bg red-10%
```

## 🚀 Implementação (Tailwind)

No `tailwind.config.js` já está definido:

```javascript
colors: {
  primary: {
    dark: "#0339A6",
    medium: "#0468BF",
    light: "#79ACD9",
  },
  alert: { critical: "#D91A1A" },
  background: { surface: "#F2F2F2" },
  // ... resto das cores
}

spacing: {
  xs: "0.5rem", sm: "1rem", md: "1.5rem", lg: "2rem", ...
}

borderRadius: {
  soft: "0.375rem", base: "0.5rem", md: "0.75rem", ...
}

shadows: { soft, base, md, lg, xl, ... }
```

**Uso em componentes:**

```tsx
// Usando classes Tailwind
<div className="bg-background-surface p-lg rounded-lg shadow-base">
  Conteúdo
</div>

// Ou inline styles (para componentes React)
<div style={{
  backgroundColor: colors.background.surface,
  padding: spacing.lg,
  borderRadius: borderRadius.lg,
  boxShadow: shadows.base,
}}>
  Conteúdo
</div>
```

## 📖 Referências

- [WCAG 2.1 Accessibility Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [Material Design 3](https://m3.material.io/)
- [Tailwind CSS Documentation](https://tailwindcss.com/)
- [Inter Font](https://fonts.google.com/specimen/Inter)

---

**Última atualização**: 3 de dezembro de 2025  
**Versão**: 1.0.0  
**Mantido por**: @ivonsmatos
