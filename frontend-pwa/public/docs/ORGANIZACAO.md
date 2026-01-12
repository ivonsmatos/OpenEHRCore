# 📂 Organização do Projeto - OpenEHR Core

**Atualizado em:** 14 de dezembro de 2025

Este documento descreve a estrutura organizada do projeto após limpeza e consolidação de arquivos.

---

## 🎯 Mudanças Realizadas

### ✅ Arquivos Movidos e Organizados

#### 1. Testes de Integração

**Antes:** Arquivos soltos na raiz do projeto  
**Depois:** Organizados em `tests/integration/`

```
✓ test_new_endpoints.py → tests/integration/test_new_endpoints.py
✓ test_fhir_authenticated.py → tests/integration/test_fhir_authenticated.py
✓ test_document_careplan.py → tests/integration/test_document_careplan.py
```

#### 2. Scripts de Seed

**Antes:** Arquivos soltos na raiz do projeto  
**Depois:** Organizados em `backend-django/scripts/seed/`

```
✓ seed_dashboard_data.py → backend-django/scripts/seed/seed_dashboard_data.py
✓ seed_fhir_direct.py → backend-django/scripts/seed/seed_fhir_direct.py
✓ seed_practitioners_beds.py → backend-django/scripts/seed/seed_practitioners_beds.py
```

#### 3. Relatórios e Documentação

**Antes:** Arquivos na raiz do projeto  
**Depois:** Organizados em `docs/relatorios/`

```
✓ SISTEMA_100_FUNCIONAL.md → docs/relatorios/SISTEMA_100_FUNCIONAL.md
✓ TESTE_COMPLETO_RELATORIO.md → docs/relatorios/TESTE_COMPLETO_RELATORIO.md
```

### ✅ Documentação Criada

```
✓ tests/integration/README.md - Guia completo de testes de integração
✓ backend-django/scripts/seed/README.md - Guia de scripts de seed
✓ docs/ORGANIZACAO.md - Este documento
```

---

## 📁 Estrutura Atual do Projeto

```
OpenEHRCore/
│
├── 📱 frontend-pwa/              # Frontend React PWA
│   ├── src/
│   │   ├── components/          # Componentes reutilizáveis
│   │   │   ├── clinical/        # GoalTracker, MediaViewer, etc
│   │   │   ├── dashboard/       # Componentes do dashboard
│   │   │   ├── patient/         # Componentes de pacientes
│   │   │   └── base/            # Componentes base (Button, Card, etc)
│   │   ├── pages/               # 15+ páginas
│   │   ├── hooks/               # Hooks customizados
│   │   ├── services/            # Serviços da API
│   │   ├── types/               # Tipos TypeScript
│   │   └── utils/               # Utilitários
│   ├── public/                  # Assets estáticos
│   └── package.json
│
├── 🐍 backend-django/            # Backend Django
│   ├── fhir_api/                # App principal FHIR
│   │   ├── models_*.py          # Models por recurso FHIR
│   │   ├── serializers_*.py     # Serializers
│   │   ├── views_*.py           # Views da API
│   │   ├── permissions.py       # Permissões RBAC
│   │   ├── urls.py              # Rotas da API
│   │   └── tests/               # Testes unitários
│   ├── openehrcore/             # Configurações Django
│   ├── scripts/
│   │   └── seed/                # 📌 Scripts de seed
│   │       ├── seed_fhir_data.py
│   │       ├── seed_hospital_structure.py
│   │       ├── seed_practitioners.py
│   │       ├── seed_admissions.py
│   │       ├── seed_dashboard_data.py
│   │       ├── seed_fhir_direct.py
│   │       ├── seed_practitioners_beds.py
│   │       └── README.md        # 📚 Documentação de seeds
│   └── manage.py
│
├── 🧪 tests/                     # Testes do projeto
│   ├── integration/             # 📌 Testes de integração
│   │   ├── test_new_endpoints.py
│   │   ├── test_fhir_authenticated.py
│   │   ├── test_document_careplan.py
│   │   └── README.md            # 📚 Guia de testes
│   ├── test_analytics.py
│   ├── test_analytics_direct.py
│   ├── test_dicom_processor.py
│   ├── test_e2e_playwright.py
│   ├── test_hl7_minimal.py
│   ├── test_hl7_parser.py
│   ├── test_hl7_processor.py
│   └── test_routes_security.py
│
├── 📚 docs/                      # Documentação
│   ├── relatorios/              # 📌 Relatórios de testes
│   │   ├── SISTEMA_100_FUNCIONAL.md
│   │   └── TESTE_COMPLETO_RELATORIO.md
│   ├── testes/                  # Guias de teste
│   │   ├── TESTING_GUIDE.md
│   │   ├── ADVANCED_TESTING_GUIDE.md
│   │   └── PLAYWRIGHT_DEMO.md
│   ├── seguranca/               # Documentação de segurança
│   │   ├── SECURITY_AUDIT_REPORT.md
│   │   └── EXECUTIVE_SUMMARY_DEVSECOPS.md
│   ├── API.md                   # Documentação da API
│   ├── SETUP.md                 # Guia de instalação
│   ├── FAQ.md
│   ├── WORKFLOWS.md
│   ├── ORGANIZACAO.md           # 📌 Este documento
│   └── INDEX.md
│
├── 🤖 agent/                     # Agente on-premise
│   └── openehrcore_agent/
│
├── 📱 mobile-app/                # App React Native
│
├── 🔧 sdk/                       # TypeScript SDK
│
├── 🐳 docker/                    # Docker configs
│   ├── docker-compose.yml
│   └── ...
│
├── ☸️  kubernetes/               # Kubernetes configs
│
├── 🛠️ scripts/                   # Scripts utilitários
│
├── .github/                     # GitHub configs
├── .gitignore
├── README.md                    # 📌 README principal
└── PORTAL_IMPLEMENTACAO.md

```

---

## 🎯 Convenções de Organização

### Princípios Adotados

1. **Separação por Contexto**

   - `/tests` - Todos os testes
   - `/docs` - Toda documentação
   - `/scripts` - Scripts utilitários

2. **Estrutura Clara**

   - Cada pasta tem um `README.md` explicativo
   - Sem arquivos duplicados ou versionados (teste1, teste2, etc)
   - Nomenclatura consistente

3. **Facilidade de Navegação**
   - Estrutura de pastas intuitiva
   - Documentação próxima ao código relacionado
   - Links entre documentos

---

## 📍 Guia de Localização Rápida

### Quero executar testes...

```bash
# Testes de integração FHIR
cd tests/integration
python test_new_endpoints.py

# Veja: tests/integration/README.md
```

### Quero popular o banco de dados...

```bash
# Scripts de seed
cd backend-django/scripts/seed
python seed_fhir_data.py

# Veja: backend-django/scripts/seed/README.md
```

### Quero ver relatórios de testes...

```bash
# Relatórios completos
docs/relatorios/SISTEMA_100_FUNCIONAL.md
docs/relatorios/TESTE_COMPLETO_RELATORIO.md
```

### Quero ver documentação técnica...

```bash
# Documentação da API
docs/API.md

# Guia de instalação
docs/SETUP.md

# Guias de teste
docs/testes/TESTING_GUIDE.md
```

### Quero desenvolver...

```bash
# Frontend
cd frontend-pwa
npm run dev

# Backend
cd backend-django
python manage.py runserver
```

---

## 🧹 Arquivos Removidos/Consolidados

### ❌ Não há mais arquivos soltos na raiz

**Antes:**

```
❌ test_new_endpoints.py
❌ test_fhir_authenticated.py
❌ test_document_careplan.py
❌ seed_dashboard_data.py
❌ seed_fhir_direct.py
❌ seed_practitioners_beds.py
❌ SISTEMA_100_FUNCIONAL.md
❌ TESTE_COMPLETO_RELATORIO.md
```

**Depois:**

```
✅ Todos organizados em pastas apropriadas
✅ Documentação em docs/
✅ Testes em tests/
✅ Scripts em backend-django/scripts/
```

---

## 📝 Manutenção da Organização

### Regras para Novos Arquivos

#### Testes

```
✅ Testes unitários → backend-django/fhir_api/tests/
✅ Testes de integração → tests/integration/
✅ Testes E2E → tests/
```

#### Documentação

```
✅ Relatórios → docs/relatorios/
✅ Guias técnicos → docs/
✅ Documentação de API → docs/API.md
```

#### Scripts

```
✅ Scripts de seed → backend-django/scripts/seed/
✅ Scripts de migração → backend-django/scripts/
✅ Scripts utilitários → scripts/
```

### Nomenclatura

```
✅ USAR: test_fhir_goals.py
❌ EVITAR: teste1.py, teste2.py, test_final.py

✅ USAR: RELATORIO_TESTES_SPRINT_35.md
❌ EVITAR: doc1.md, relatorio_v2.md, relatorio_final_FINAL.md

✅ USAR: seed_practitioners.py
❌ EVITAR: populate_db.py, import_data_v3.py
```

---

## ✅ Checklist de Organização

Use este checklist ao adicionar novos arquivos:

- [ ] O arquivo está na pasta correta?
- [ ] O nome do arquivo é descritivo?
- [ ] Não há arquivos duplicados?
- [ ] Há um README.md na pasta?
- [ ] O arquivo está documentado?
- [ ] Há links para o arquivo em documentação relevante?

---

## 📚 Documentação Relacionada

- [README Principal](../README.md)
- [Guia de Testes](tests/integration/README.md)
- [Guia de Seeds](backend-django/scripts/seed/README.md)
- [Relatório Sistema 100% Funcional](docs/relatorios/SISTEMA_100_FUNCIONAL.md)
- [Relatório Completo de Testes](docs/relatorios/TESTE_COMPLETO_RELATORIO.md)

---

## 🎯 Benefícios da Nova Organização

1. **Fácil Navegação** - Estrutura intuitiva
2. **Manutenibilidade** - Cada coisa em seu lugar
3. **Documentação** - READMEs em cada pasta importante
4. **Escalabilidade** - Fácil adicionar novos componentes
5. **Colaboração** - Equipe encontra arquivos rapidamente
6. **Profissionalismo** - Projeto limpo e organizado

---

**Última atualização:** 14 de dezembro de 2025  
**Mantido por:** Equipe OpenEHR Core
