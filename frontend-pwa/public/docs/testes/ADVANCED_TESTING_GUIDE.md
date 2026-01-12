# 🚀 Guia de Testes Avançados - OpenEHR FHIR API

**Data de Criação:** 14 de Dezembro de 2024  
**Status:** ✅ Implementado Completamente

---

## 📋 Índice

1. [Performance Testing](#1-performance-testing-locust)
2. [Security Scanning](#2-security-scanning-owasp-zap)
3. [Accessibility Testing](#3-accessibility-testing-axe-core)
4. [Visual Regression](#4-visual-regression-playwright)
5. [API Contract Validation](#5-api-contract-validation-fhir-schema)
6. [Integração CI/CD](#6-integração-cicd)

---

## 1. Performance Testing (Locust)

### 📄 Arquivo: `backend-django/locustfile.py`

### Instalação

```bash
pip install locust
```

### Uso

#### Modo UI (Desenvolvimento)

```bash
cd backend-django
locust -f locustfile.py --host=http://localhost:8000
```

Acesse: http://localhost:8089

#### Modo Headless (CI/CD)

```bash
locust -f locustfile.py \
  --host=http://localhost:8000 \
  --users 100 \
  --spawn-rate 10 \
  --run-time 60s \
  --headless \
  --html=locust_report.html
```

### Características

- ✅ **70% leitura** (GET patients, health check, analytics)
- ✅ **20% escrita** (POST patients, encounters)
- ✅ **10% edge cases** (UUID inválido, paginação grande)
- ✅ **CPF válido** gerado automaticamente (com dígitos verificadores)
- ✅ **AdminUser** separado (operações pesadas)

### Métricas Alvo

| Métrica           | Objetivo    | Status    |
| ----------------- | ----------- | --------- |
| P95 response time | < 1000ms    | ⏱️ Testar |
| Taxa de erro      | < 1%        | ⏱️ Testar |
| Throughput        | > 100 req/s | ⏱️ Testar |

### Exemplo de Saída

```
=================================================================
🚀 INICIANDO LOAD TEST - OpenEHR FHIR API
=================================================================
Host: http://localhost:8000
Users: 100
=================================================================

📊 Resumo:
  Total de requisições: 5432
  Falhas: 12 (0.22%)
  Tempo médio: 234.56ms
  P95: 876.32ms
  P99: 1234.56ms
  RPS: 90.53 req/s

🎯 SLA Check:
  P95 < 1000ms: ✅ (876.32ms)
  Taxa de erro < 1%: ✅ (0.22%)
=================================================================
```

---

## 2. Security Scanning (OWASP ZAP)

### 📄 Arquivo: `backend-django/security/owasp_zap_scan.py`

### Instalação

```bash
# 1. Instale OWASP ZAP
# Download: https://www.zaproxy.org/download/

# 2. Instale biblioteca Python
pip install python-owasp-zap-v2.4
```

### Uso

#### Scan Rápido (Spider + Passive)

```bash
# Inicie ZAP primeiro (GUI ou headless)
zap.sh -daemon -port 8080 -config api.key=your_api_key

# Execute scan
python security/owasp_zap_scan.py --mode quick
```

#### Scan Completo (Spider + Active)

```bash
python security/owasp_zap_scan.py \
  --mode full \
  --target http://localhost:8000 \
  --auth jwt \
  --token "eyJhbGciOi..."
```

#### CI/CD (Falha em HIGH alerts)

```bash
python security/owasp_zap_scan.py \
  --mode full \
  --exit-on-high
```

### Características

- ✅ **Spider Scan** - Descobre endpoints automaticamente
- ✅ **AJAX Spider** - Suporta SPAs (React/Vue)
- ✅ **Passive Scan** - Não invasivo
- ✅ **Active Scan** - Testes invasivos (apenas em DEV!)
- ✅ **Autenticação** - JWT, Basic Auth
- ✅ **Relatórios** - HTML, JSON, XML, Markdown

### Relatórios Gerados

```
security/reports/
├── zap_report_20241214_083045.html   # Relatório visual
├── zap_report_20241214_083045.json   # Para CI/CD
└── zap_report_20241214_083045.md     # Para documentação
```

### Exemplo de Saída

```
================================================================================
📊 OWASP ZAP SCAN SUMMARY
================================================================================
Target: http://localhost:8000
Total Alerts: 12
--------------------------------------------------------------------------------
🔴 High:          2
🟡 Medium:        5
🟢 Low:           3
🔵 Informational: 2
================================================================================

🔴 HIGH RISK ALERTS:
   - SQL Injection (http://localhost:8000/api/v1/patients/?search=test)
   - Cross-Site Scripting (http://localhost:8000/api/v1/documents/)
```

---

## 3. Accessibility Testing (Axe-Core)

### 📄 Arquivo: `frontend-pwa/e2e/accessibility.spec.ts`

### Instalação

```bash
cd frontend-pwa
npm install --save-dev @axe-core/playwright
```

### Uso

```bash
# Rodar todos os testes de acessibilidade
npx playwright test e2e/accessibility.spec.ts

# Com relatório HTML
npx playwright test e2e/accessibility.spec.ts --reporter=html

# Apenas violações críticas
npx playwright test e2e/accessibility.spec.ts --grep "critical"
```

### Características

- ✅ **WCAG 2.1 Level AA** compliance
- ✅ **Testes de teclado** (Tab navigation)
- ✅ **Contraste de cores** (4.5:1 mínimo)
- ✅ **Labels em formulários**
- ✅ **Alt text em imagens**
- ✅ **ARIA compliance**
- ✅ **Touch targets** (44x44px mínimo)
- ✅ **Mobile responsive**

### Páginas Testadas

- ✅ Login page
- ✅ Patient list
- ✅ Patient details
- ✅ Patient forms
- ✅ Navigation
- ✅ Interactive elements

### Exemplo de Saída

```
♿ ACCESSIBILITY TESTING COMPLETE
================================================================================

❌ Violações de Acessibilidade em: Login Page
Total: 3

1. color-contrast (serious)
   Descrição: Elements must have sufficient color contrast
   Help: https://dequeuniversity.com/rules/axe/4.4/color-contrast
   Afeta 2 elemento(s)
   - Elemento 1: <button class="btn-primary">Login</button>
     Seletor: #login-form > button

2. label (critical)
   Descrição: Form elements must have labels
   Help: https://dequeuniversity.com/rules/axe/4.4/label
   Afeta 1 elemento(s)
   - Elemento 1: <input type="text" name="username">
     Seletor: #login-form > input[name="username"]
```

---

## 4. Visual Regression (Playwright)

### 📄 Arquivo: `frontend-pwa/e2e/visual-regression.spec.ts`

### Instalação

```bash
cd frontend-pwa
# Playwright já instalado, nenhuma dependência extra necessária

# Opcional: Percy para cloud-based visual testing
npm install --save-dev @percy/cli @percy/playwright
```

### Uso

#### Local (Playwright Screenshots)

```bash
# Primeira execução - cria baselines
npx playwright test e2e/visual-regression.spec.ts

# Execuções seguintes - compara com baseline
npx playwright test e2e/visual-regression.spec.ts

# Atualizar baselines após mudanças intencionais
npx playwright test e2e/visual-regression.spec.ts --update-snapshots
```

#### Com Percy (Cloud)

```bash
export PERCY_TOKEN=your_percy_token
npx percy exec -- npx playwright test e2e/visual-regression.spec.ts
```

### Características

- ✅ **Full page screenshots**
- ✅ **Component screenshots**
- ✅ **Responsive viewports** (mobile, tablet, desktop)
- ✅ **Dark mode** testing
- ✅ **Interactive states** (hover, focus, error)
- ✅ **Modal/overlay** testing
- ✅ **Máscara de conteúdo dinâmico** (timestamps, IDs)

### Viewports Testados

| Viewport | Width  | Height | Device    |
| -------- | ------ | ------ | --------- |
| Mobile   | 375px  | 667px  | iPhone SE |
| Tablet   | 768px  | 1024px | iPad      |
| Desktop  | 1920px | 1080px | Full HD   |

### Screenshots Gerados

```
e2e/visual-regression.spec.ts-snapshots/
├── login-page-chromium-darwin.png
├── patient-list-mobile-chromium-darwin.png
├── patient-list-tablet-chromium-darwin.png
├── patient-list-desktop-chromium-darwin.png
├── patient-card-component-chromium-darwin.png
└── ...
```

### Exemplo de Diff

```
❌ Screenshot comparison failed: patient-list-with-data.png
   Expected: e2e/visual-regression.spec.ts-snapshots/patient-list-with-data-chromium-darwin.png
   Received: test-results/visual-regression-patient-list/patient-list-with-data-actual.png
   Diff: test-results/visual-regression-patient-list/patient-list-with-data-diff.png

   Pixels changed: 234 (0.5%)
   Max threshold: 100 pixels
```

---

## 5. API Contract Validation (FHIR Schema)

### 📄 Arquivo: `backend-django/tests/test_fhir_schema_validation.py`

### Instalação

```bash
pip install fhir.resources
```

### Uso

```bash
# Validar todos os recursos
pytest tests/test_fhir_schema_validation.py -v

# Validar apenas Patient
pytest tests/test_fhir_schema_validation.py::TestPatientSchema -v

# Gerar relatório
pytest tests/test_fhir_schema_validation.py --html=fhir_validation_report.html

# Modo relatório rápido
python tests/test_fhir_schema_validation.py --report
```

### Características

- ✅ **Validação Pydantic** - Usa modelos oficiais FHIR R4
- ✅ **Recursos suportados**:
  - Patient
  - Observation
  - Condition
  - MedicationRequest
  - Encounter
  - Practitioner
  - Organization
  - Bundle
- ✅ **Validação de campos obrigatórios**
- ✅ **Validação de tipos de dados**
- ✅ **Validação de códigos** (LOINC, SNOMED CT)
- ✅ **Validação de referências**

### Exemplo de Teste

```python
def test_patient_with_cpf_identifier(self):
    """Patient com identificador CPF (extensão brasileira)"""
    patient = {
        "resourceType": "Patient",
        "id": "test-456",
        "identifier": [{
            "system": "http://rnds.saude.gov.br/fhir/r4/NamingSystem/cpf",
            "value": "123.456.789-09"
        }],
        "name": [{
            "family": "Santos",
            "given": ["Maria"]
        }],
        "gender": "female",
        "birthDate": "1990-05-15"
    }

    is_valid, error = self.validator.validate_resource(patient, 'Patient')
    self.assertTrue(is_valid)
```

### Exemplo de Saída

```
================================================================================
🔍 FHIR R4 SCHEMA VALIDATION REPORT
================================================================================

📊 Validados 3 endpoints:

✅ /patients/patient-123 (Patient)
❌ /observations/obs-123 (Observation)
   Erro: status -> field required
✅ /conditions/cond-123 (Condition)

================================================================================

✅ Válidos: 2/3
❌ Inválidos: 1/3

================================================================================
```

---

## 6. Integração CI/CD

### GitHub Actions

```yaml
name: Advanced Testing Suite

on: [push, pull_request]

jobs:
  performance:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          pip install locust

      - name: Run Load Tests
        run: |
          cd backend-django
          locust -f locustfile.py \
            --host=http://localhost:8000 \
            --users 50 \
            --spawn-rate 5 \
            --run-time 30s \
            --headless \
            --html=locust_report.html

      - name: Upload Performance Report
        uses: actions/upload-artifact@v3
        with:
          name: performance-report
          path: backend-django/locust_report.html

  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: OWASP ZAP Baseline Scan
        uses: zaproxy/action-baseline@v0.7.0
        with:
          target: "http://localhost:8000"
          rules_file_name: ".zap/rules.tsv"
          cmd_options: "-a"

  accessibility:
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
          npx playwright install --with-deps

      - name: Run Accessibility Tests
        run: |
          cd frontend-pwa
          npx playwright test e2e/accessibility.spec.ts

      - name: Upload Test Results
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: accessibility-report
          path: frontend-pwa/playwright-report/

  visual-regression:
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
          npx playwright install --with-deps

      - name: Run Visual Regression Tests
        run: |
          cd frontend-pwa
          npx playwright test e2e/visual-regression.spec.ts

      - name: Upload Screenshots
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: visual-regression-screenshots
          path: frontend-pwa/test-results/

  fhir-validation:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          pip install fhir.resources pytest pytest-html

      - name: Run FHIR Schema Validation
        run: |
          cd backend-django
          pytest tests/test_fhir_schema_validation.py \
            --html=fhir_validation_report.html \
            --self-contained-html

      - name: Upload Validation Report
        uses: actions/upload-artifact@v3
        with:
          name: fhir-validation-report
          path: backend-django/fhir_validation_report.html
```

---

## 📊 Resumo de Implementação

| Tipo                  | Ferramenta  | Arquivo                                | Status | Comandos                                               |
| --------------------- | ----------- | -------------------------------------- | ------ | ------------------------------------------------------ |
| **Performance**       | Locust      | `locustfile.py`                        | ✅     | `locust -f locustfile.py --host=http://localhost:8000` |
| **Security**          | OWASP ZAP   | `security/owasp_zap_scan.py`           | ✅     | `python security/owasp_zap_scan.py --mode full`        |
| **Accessibility**     | Axe-Core    | `e2e/accessibility.spec.ts`            | ✅     | `npx playwright test e2e/accessibility.spec.ts`        |
| **Visual Regression** | Playwright  | `e2e/visual-regression.spec.ts`        | ✅     | `npx playwright test e2e/visual-regression.spec.ts`    |
| **API Contract**      | FHIR Schema | `tests/test_fhir_schema_validation.py` | ✅     | `pytest tests/test_fhir_schema_validation.py`          |

---

## 🎯 Próximos Passos

1. ✅ **Executar testes localmente** para estabelecer baselines
2. ⏭️ **Configurar CI/CD** (GitHub Actions, GitLab CI, Jenkins)
3. ⏭️ **Treinar equipe** nos novos testes
4. ⏭️ **Integrar com Percy/Chromatic** (visual regression cloud)
5. ⏭️ **Configurar alertas** para falhas de teste

---

**📝 Última Atualização:** 14 de Dezembro de 2024  
**👤 Responsável:** QA Senior Engineer & Security Specialist
