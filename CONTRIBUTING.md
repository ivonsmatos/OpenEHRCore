# Guia de Contribuição — OpenEHRCore / HealthStack

Obrigado por contribuir! Este guia resume o fluxo de trabalho e os padrões de
qualidade do projeto.

## 🔀 Fluxo de trabalho

1. Faça um fork e crie uma branch a partir de `develop` (ou `main`):
   `git checkout -b feat/minha-funcionalidade`
2. Faça commits seguindo **Conventional Commits** (veja abaixo).
3. Garanta que os testes e o lint passam localmente.
4. Abra um Pull Request descrevendo a mudança e o motivo.

## ✍️ Conventional Commits

O título de commits e PRs é validado no CI. Use os prefixos:

`feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`,
`chore`, `revert`.

Exemplo: `feat(fhir): adiciona suporte ao recurso ServiceRequest`

## 🧪 Testes

**Backend (Django/pytest):**

```bash
cd backend-django
pip install -r requirements.txt
pip install pytest pytest-django pytest-cov
pytest fhir_api/tests/ -v
```

> Os testes usam `openehrcore.test_settings`, que aplica uma autenticação de
> bypass **apenas em teste** (`dev-token-bypass`) e SQLite em memória. Nenhum
> bypass existe em produção.

**Frontend (Vitest):**

```bash
cd frontend-pwa
npm ci
npm test            # watch
npm run coverage    # uma execução, com cobertura
```

**E2E (Playwright):**

```bash
cd frontend-pwa
npx playwright install --with-deps
npx playwright test
```

## ✅ Padrões de código

**Backend**

- Siga os padrões FHIR R4.
- Adicione docstrings nos métodos públicos.
- Use serializers para validação e `permissions` para RBAC.
- **Nunca** use `except:` nu — capture exceções específicas e registre log.
- **Nunca** use `@permission_classes([AllowAny])` em endpoints que expõem dados
  clínicos/pessoais. Endpoints públicos legítimos: health checks, descoberta
  SMART (`.well-known`), login.
- Registre auditoria (`AuditEvent`) em ações críticas.

**Frontend**

- Use os hooks de responsividade (`useIsMobile`).
- Adicione `aria-label` em componentes interativos (WCAG 2.1 AA).
- Use as variáveis do Design System (`colors.*`, `spacing.*`).
- `font-size: 16px` em inputs mobile (evita zoom no iOS).

## 🔐 Segurança

- Não commite segredos. Use `.env` (veja os arquivos `.env.example`).
- Reporte vulnerabilidades de forma privada ao mantenedor antes de abrir issue
  pública.

## 📦 Dependências

- Backend principal: `requirements.txt`. IA local (torch/transformers, opcional
  e pesada): `requirements-ml.txt`.
- Use limites de versão (`>=x,<y`) ao adicionar dependências.

---

Licença: ao contribuir, você concorda que sua contribuição será licenciada sob
a [Licença MIT](LICENSE).
