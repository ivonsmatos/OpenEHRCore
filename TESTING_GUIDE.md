# 🧪 GUIA DE TESTES - HEALTHSTACK

## 📋 Visão Geral

Este guia contém todas as instruções para executar os testes de cobertura total do HealthStack:

- **Backend (Pytest)**: Testes de segurança e integridade de rotas da API Django
- **Frontend (Playwright)**: Testes E2E de navegação, interação e validação visual

---

## 🔧 PRÉ-REQUISITOS

### 1. Backend Django rodando

```powershell
cd backend-django
python manage.py runserver
```

**URL esperada:** `http://localhost:8000`

### 2. Frontend React rodando

```powershell
cd frontend-pwa
npm start
```

**URL esperada:** `http://localhost:5173`

### 3. Instalar dependências de teste

#### Pytest (Backend)

```powershell
pip install pytest requests
```

#### Playwright (Frontend E2E)

```powershell
pip install pytest-playwright
playwright install
```

_Nota: `playwright install` baixa os navegadores (Chromium, Firefox, WebKit). Executar apenas uma vez._

---

## 🎯 MAPEAMENTO DE ROTAS

### Backend (Django API)

**Total:** 150+ rotas mapeadas

#### Rotas Públicas (6 rotas):

- `/api/v1/health/` - Health check
- `/api/v1/health/live/` - Liveness probe
- `/api/v1/health/ready/` - Readiness probe
- `/api/v1/metrics/` - Métricas Prometheus
- `/api/v1/docs/openapi.json` - Spec OpenAPI
- `/api/v1/auth/login/` - Login

#### Rotas Protegidas (144+ rotas):

Categorias principais:

- **Pacientes** (12 rotas): CRUD, busca, exportação
- **Atendimentos** (6 rotas): Encounters, observações
- **Clínica** (20 rotas): Condições, alergias, imunizações, procedimentos
- **Agendamento** (8 rotas): Appointments, slots, schedules
- **Documentos** (5 rotas): Compositions, PDF generation
- **Analytics** (8 rotas): Dashboards, KPIs, relatórios
- **Regulatório** (15 rotas): TISS, RNDS, notificações compulsórias
- **LGPD** (10 rotas): Consentimentos, anonimização, audit logs
- **Integrações** (12 rotas): Laboratório, PACS, Farmácia
- **Telemedicina** (8 rotas): Sessões, WebRTC
- **Automação** (6 rotas): Bots, webhooks, subscriptions
- **Billing** (6 rotas): Coverage, claims, faturas
- **SMART/FHIRcast** (10 rotas): OAuth2, context sync
- **Terminologias** (8 rotas): RxNorm, ICD-10, TUSS, CBO

### Frontend (React)

**Total:** 30 rotas mapeadas

#### Workspaces/Telas:

```
/                    → Dashboard Principal
/patients            → Lista de Pacientes
/patients/new        → Novo Paciente
/patients/:id        → Detalhes do Paciente
/practitioners       → Profissionais de Saúde
/scheduling          → Agendamento
/checkin             → Check-in
/portal              → Portal do Paciente
/finance             → Financeiro
/documents           → Documentos Clínicos
/visitors            → Visitantes
/chat                → Chat/Mensagens
/ipd                 → Gestão de Leitos
/organizations       → Organizações
/privacy             → LGPD Dashboard
/tiss                → TISS/ANS
/rnds                → RNDS Status
/notifications       → Notificações Compulsórias
/careplan            → Planos de Cuidado
/referrals           → Encaminhamentos
/composition         → Editor de Prontuário
/messages            → Inbox de Mensagens
/automation          → Automação (Bots)
/prescriptions       → Prescrições
/settings/*          → Configurações (4 telas)
```

---

## 🧪 EXECUTAR TESTES BACKEND (Pytest)

### 1. Testes de Segurança de Rotas

**Arquivo:** `tests/test_routes_security.py`

#### Executar todos os testes:

```powershell
pytest tests/test_routes_security.py -v
```

#### Ver apenas rotas públicas:

```powershell
pytest tests/test_routes_security.py::test_public_routes_without_auth -v
```

#### Ver apenas segurança de rotas protegidas:

```powershell
pytest tests/test_routes_security.py::test_protected_routes_without_auth -v
```

#### Testar rotas com autenticação:

```powershell
pytest tests/test_routes_security.py::test_protected_routes_with_auth -v
```

#### Testar validação de payloads vazios:

```powershell
pytest tests/test_routes_security.py::test_post_empty_payload_no_crash -v
```

### O que é testado?

✅ Rotas públicas retornam 200 sem autenticação  
✅ Rotas protegidas retornam 401/403 sem token  
✅ Rotas protegidas funcionam com token válido  
✅ **Nenhuma rota retorna 500** (crash)  
✅ Validação de entrada não causa crash

### Interpretando Resultados:

```
✅ PASSED  → Rota funcionando conforme esperado
❌ FAILED  → Bug detectado:
   • Status 500: Crash no servidor (erro crítico)
   • Rota protegida sem 401/403: Falha de segurança
   • Timeout: Performance issue
```

---

## 🎭 EXECUTAR TESTES E2E (Playwright)

### 1. Testes de Navegação e Interação

**Arquivo:** `tests/test_e2e_playwright.py`

#### Ver navegador (modo debug):

```powershell
pytest tests/test_e2e_playwright.py --headed --slowmo 100
```

_O navegador abre e você vê o "robô" clicando na tela._

#### Headless (rápido, para CI/CD):

```powershell
pytest tests/test_e2e_playwright.py
```

#### Testar apenas navegação (spider):

```powershell
pytest tests/test_e2e_playwright.py -k "route_loads" --headed
```

#### Testar apenas botões (button smashing):

```powershell
pytest tests/test_e2e_playwright.py -k "buttons" --headed
```

#### Testar validação de formulários:

```powershell
pytest tests/test_e2e_playwright.py -k "form" --headed
```

#### Gerar screenshots e vídeos de falhas:

```powershell
pytest tests/test_e2e_playwright.py --screenshot=on --video=retain-on-failure
```

### O que é testado?

✅ **Spider/Crawl:** Navega em todas as 30 rotas React  
✅ **Nenhuma página 404** ou em branco  
✅ **Button Smashing:** Clica em todos os botões visíveis sem crash  
✅ **Validação de Formulários:** Testa envio de dados vazios  
✅ **Performance:** Tempo de carregamento < 10s  
✅ **Mobile:** Funciona em viewport 375x667  
✅ **Acessibilidade:** Landmarks HTML semânticos

### Opções Avançadas:

#### Escolher navegador:

```powershell
pytest tests/test_e2e_playwright.py --browser firefox
pytest tests/test_e2e_playwright.py --browser webkit  # Safari
```

#### Pausar execução para debug:

Adicione no código:

```python
page.pause()  # Abre Playwright Inspector
```

#### Ver trace completo (gravação de tudo):

```powershell
pytest tests/test_e2e_playwright.py --tracing=on
playwright show-trace trace.zip
```

---

## 📊 RELATÓRIO DE COBERTURA

### Após executar todos os testes:

```powershell
# Backend
pytest tests/test_routes_security.py -v > backend_test_report.txt

# Frontend
pytest tests/test_e2e_playwright.py -v > frontend_test_report.txt
```

### Estatísticas Esperadas:

- **Backend:** ~150+ asserções (rotas testadas)
- **Frontend:** ~30+ asserções (rotas + interações)
- **Tempo total:** ~5-10 minutos (depende do hardware)

---

## 🐛 TROUBLESHOOTING

### Erro: "Connection refused" (Backend)

```powershell
# Certifique-se de que Django está rodando:
cd backend-django
python manage.py runserver
```

### Erro: "Target closed" (Frontend Playwright)

```powershell
# Certifique-se de que React está rodando:
cd frontend-pwa
npm start
```

### Erro: "playwright: command not found"

```powershell
# Reinstalar Playwright:
pip install playwright
playwright install
```

### Erro: "Token de autenticação não disponível"

Ajuste as credenciais em `test_routes_security.py`:

```python
TEST_USER = {
    "username": "seu_usuario",
    "password": "sua_senha"
}
```

### Teste muito lento (Playwright)

Remova `--slowmo` e use headless:

```powershell
pytest tests/test_e2e_playwright.py  # Sem --headed
```

---

## 🚀 INTEGRAÇÃO CONTÍNUA (CI/CD)

### GitHub Actions (exemplo):

```yaml
name: Tests

on: [push, pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.11"
      - name: Install dependencies
        run: pip install pytest requests
      - name: Run Django
        run: |
          cd backend-django
          python manage.py migrate
          python manage.py runserver &
          sleep 5
      - name: Run backend tests
        run: pytest tests/test_routes_security.py -v

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Node
        uses: actions/setup-node@v3
        with:
          node-version: "18"
      - name: Install dependencies
        run: |
          cd frontend-pwa
          npm ci
      - name: Install Playwright
        run: |
          pip install pytest-playwright
          playwright install --with-deps
      - name: Start frontend
        run: |
          cd frontend-pwa
          npm start &
          sleep 10
      - name: Run E2E tests
        run: pytest tests/test_e2e_playwright.py
```

---

## 📝 PRÓXIMOS PASSOS

### Expandir cobertura:

1. **Performance:** Adicionar testes de carga (Locust, k6)
2. **Segurança:** Scan de vulnerabilidades (OWASP ZAP)
3. **Acessibilidade:** Testes completos (Axe, Pa11y)
4. **Visual Regression:** Screenshots comparativos (Percy, Chromatic)
5. **API Contract:** Validação de schemas FHIR (Pact)

### Monitoramento em produção:

- **Sentry:** Rastreamento de erros
- **New Relic/DataDog:** APM e métricas
- **Uptime Robot:** Health checks automatizados

---

## 📚 REFERÊNCIAS

- [Pytest Docs](https://docs.pytest.org/)
- [Playwright Python](https://playwright.dev/python/)
- [Django Testing](https://docs.djangoproject.com/en/stable/topics/testing/)
- [React Testing Library](https://testing-library.com/react)

---

## ✅ CHECKLIST DE QUALIDADE

Antes de cada release, execute:

- [ ] `pytest tests/test_routes_security.py -v` → ✅ 100% pass
- [ ] `pytest tests/test_e2e_playwright.py --headed` → ✅ Sem crashes
- [ ] Verificar logs de erros no console do navegador
- [ ] Testar em mobile (viewport 375x667)
- [ ] Validar tempo de carregamento < 5s
- [ ] Nenhuma rota retorna 500
- [ ] Formulários validam corretamente campos vazios

---

**Última atualização:** 14 de dezembro de 2025  
**Versão:** 1.0.0
