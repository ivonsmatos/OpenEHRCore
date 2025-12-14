# Portal de Documentação OpenEHR - Guia de Uso

## 🎉 Visão Geral

Portal de documentação interna desenvolvido com **React** + **Tailwind CSS**, seguindo a identidade visual do projeto OpenEHR Core. Design inspirado em **Medplum Docs** e **GitBook**.

## ✨ Características

### Design & UX

- ✅ **Sidebar responsiva** - Menu lateral que vira hambúrguer no mobile
- ✅ **Cores institucionais** - Paleta #0468BF, #0339A6, #F2F2F2
- ✅ **Typography moderna** - Sans-serif (Inter/Roboto)
- ✅ **Navegação intuitiva** - Categorias expansíveis
- ✅ **Mobile-first** - 100% responsivo

### Funcionalidades

- ✅ **Renderização Markdown** - Suporte completo a GFM (GitHub Flavored Markdown)
- ✅ **Syntax Highlighting** - Código com temas profissionais
- ✅ **Callouts/Alerts** - Blocos informativos coloridos
- ✅ **Tabelas responsivas** - Scroll horizontal em mobile
- ✅ **Copy to clipboard** - Botão para copiar códigos
- ✅ **Links externos** - Ícone indicativo
- ✅ **Breadcrumbs** - Navegação contextual
- 🔄 **Busca rápida** - Em desenvolvimento (Ctrl+K)
- 🔄 **Mermaid diagrams** - Planejado

## 📂 Estrutura de Arquivos

```
frontend-pwa/src/
├── layouts/
│   └── DocsLayout.tsx          # Layout principal com sidebar
├── pages/
│   ├── DocsHome.tsx            # Landing page do portal
│   └── DocsPage.tsx            # Renderizador de markdown
├── styles/
│   └── docs.css                # Estilos customizados
└── routes.tsx                  # Rotas /docs configuradas

docs/                           # Arquivos markdown
├── INDEX.md                    # Índice geral
├── SETUP.md                    # Guia de instalação
├── ARCHITECTURE.md             # Arquitetura do sistema
├── FAQ.md                      # Perguntas frequentes
├── WORKFLOWS.md                # Fluxos clínicos
├── implementacao/              # Guias de implementação
├── testes/                     # Documentação de testes
└── seguranca/                  # Auditorias e DevSecOps
```

## 🚀 Como Usar

### Acessando o Portal

1. Faça login no sistema
2. Clique em **"Documentação"** na sidebar (ícone de livro 📖)
3. Ou acesse diretamente: `http://localhost:3000/docs`

### Navegação

**Sidebar:**

- Clique em uma categoria para expandir
- Clique em um item para visualizar o documento
- No mobile: Use o hambúrguer (☰) para abrir o menu

**Página Inicial:**

- Cards de "Início Rápido" para tópicos principais
- Guias em destaque
- Busca rápida (em breve)

### Estrutura de URLs

| URL                               | Conteúdo               |
| --------------------------------- | ---------------------- |
| `/docs`                           | Home do portal         |
| `/docs/intro`                     | Introdução             |
| `/docs/setup`                     | Guia de instalação     |
| `/docs/auth/keycloak`             | Configuração Keycloak  |
| `/docs/implementation/responsive` | Guia de responsividade |
| `/docs/testing/guide`             | Testes automatizados   |
| `/docs/security/audit`            | Auditoria de segurança |

## 🎨 Componentes Customizados

### Callouts (Blocos de Aviso)

```markdown
> ℹ️ **Info:** Informação importante
> ⚠️ **Warning:** Cuidado com isso
> ✅ **Success:** Tudo certo!
> ❌ **Error:** Algo deu errado
```

### Code Blocks

````markdown
```typescript
const exemplo = "código com syntax highlighting";
```
````

### Tabelas

```markdown
| Coluna 1 | Coluna 2 |
| -------- | -------- |
| Valor A  | Valor B  |
```

### Links

```markdown
[Texto do link](https://exemplo.com) - Abre em nova aba
[Documento interno](/docs/setup) - Navegação interna
```

## 🔧 Desenvolvimento

### Adicionar Novo Documento

1. **Crie o arquivo .md:**

```bash
touch docs/meu-novo-doc.md
```

2. **Escreva o conteúdo:**

```markdown
# Meu Novo Documento

## Seção 1

Conteúdo...

## Seção 2

Mais conteúdo...
```

3. **Adicione ao mapeamento de rotas:**

```typescript
// frontend-pwa/src/pages/DocsPage.tsx
const routeMap: Record<string, string> = {
  // ...
  "categoria/meu-doc": "/docs/meu-novo-doc.md",
};
```

4. **Adicione ao menu da sidebar:**

```typescript
// frontend-pwa/src/layouts/DocsLayout.tsx
{
  title: 'Minha Categoria',
  icon: Book,
  items: [
    { title: 'Meu Novo Doc', path: '/docs/categoria/meu-doc' }
  ]
}
```

### Adicionar Nova Categoria

```typescript
// frontend-pwa/src/layouts/DocsLayout.tsx
const navigationSections: NavSection[] = [
  // ...
  {
    title: "Nova Categoria",
    icon: IconeDoLucide,
    items: [
      { title: "Doc 1", path: "/docs/categoria/doc1" },
      { title: "Doc 2", path: "/docs/categoria/doc2", badge: "Novo" },
    ],
  },
];
```

### Personalizar Estilos

Edite `frontend-pwa/src/styles/docs.css`:

```css
/* Exemplo: Mudar cor dos links */
.docs-content a {
  color: #0468bf; /* Sua cor */
}

/* Exemplo: Estilo de código */
.docs-content code {
  background: #f3f4f6;
  padding: 0.2rem 0.4rem;
}
```

## 🎯 Boas Práticas

### Escrita de Documentação

✅ **Faça:**

- Use títulos hierárquicos (H1 → H2 → H3)
- Adicione exemplos de código
- Use callouts para destacar informações importantes
- Inclua links para documentos relacionados
- Mantenha parágrafos curtos e objetivos

❌ **Evite:**

- Títulos genéricos ("Informações", "Detalhes")
- Blocos de código sem linguagem especificada
- Documentação desatualizada
- Assumir conhecimento prévio sem links

### Organização de Arquivos

```
docs/
├── README.md              # Intro geral
├── categoria1/
│   ├── intro.md
│   └── avancado.md
└── categoria2/
    ├── basico.md
    └── exemplos.md
```

### Markdown Guidelines

**Headings:**

```markdown
# Título Principal (H1) - Use apenas 1 por página

## Seção (H2)

### Subseção (H3)

#### Tópico (H4)
```

**Listas:**

```markdown
- Item não ordenado
  - Sub-item (2 espaços)
    - Sub-sub-item (4 espaços)

1. Item ordenado
2. Segundo item
```

**Código inline:**

```markdown
Use `código` para termos técnicos
```

**Imagens:**

```markdown
![Alt text](caminho/para/imagem.png)
```

## 🐛 Troubleshooting

### Documento não carrega

**Problema:** Erro 404 ao acessar documento

**Solução:**

1. Verifique se o arquivo .md existe em `/docs`
2. Confirme o mapeamento em `DocsPage.tsx`
3. Verifique o caminho (case-sensitive)

### Código sem highlight

**Problema:** Bloco de código aparece sem cores

**Solução:**
Use a linguagem correta:

````markdown
```typescript ← especifique a linguagem
const x = 1;
```
````

### Sidebar não expande

**Problema:** Categoria não abre no mobile

**Solução:**

- Verifique se `useState` está correto
- Confirme se o `toggleSection` está funcionando
- Teste em modo desktop primeiro

## 🚧 Roadmap

### v1.1 (Q1 2025)

- [ ] Busca full-text (Ctrl+K)
- [ ] Versionamento de docs
- [ ] Dark mode
- [ ] Favoritos/Bookmarks

### v1.2 (Q2 2025)

- [ ] Suporte a Mermaid diagrams
- [ ] Exportar como PDF
- [ ] Comentários inline
- [ ] Analytics de uso

### v2.0 (Q3 2025)

- [ ] Editor WYSIWYG
- [ ] Colaboração em tempo real
- [ ] Integração com GitHub
- [ ] API de documentação

## 📞 Suporte

**Issues:** [GitHub Issues](https://github.com/seu-org/OpenEHRCore/issues)  
**Email:** dev@openehrcore.com  
**Chat:** Canal #documentacao no Slack

---

**Criado por:** Time Frontend OpenEHR  
**Data:** Dezembro 2025  
**Versão:** 1.0.0
