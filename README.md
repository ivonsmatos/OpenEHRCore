# OpenEHRCore — Sistema de Gestão de Prontuários Eletrônicos (EHR) Seguro com FHIR

Um sistema EHR enterprise-grade baseado no padrão **HL7 FHIR R4** para clínicas e hospitais.

## 🏗️ Arquitetura FHIR-First

```
┌─────────────────────────────────────────────────────────────────┐
│  FRONTEND PWA (React + TypeScript)                              │
│  - UI/UX limpo e moderno (Design System)                        │
│  - Consumo seguro de JSON FHIR                                  │
│  - Offline-first com Service Workers                            │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│  BFF - Backend (Django + Python)                                │
│  - fhirclient para manipulação segura de recursos FHIR          │
│  - Keycloak integration (OAuth2/OIDC)                           │
│  - Validação de dados antes de persistir                        │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│  HAPI FHIR Server (JPA + PostgreSQL)                            │
│  - Autoridade absoluta dos dados clínicos                       │
│  - CapabilityStatement FHIR R4 completo                         │
│  - RESTful API /fhir/Patient, /fhir/Encounter, etc              │
└─────────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### 1. Levantar infraestrutura (Docker Compose)

```bash
cd docker
docker-compose up -d
```

Validar stack:

```bash
curl http://localhost:8080/fhir/metadata
```

### 2. Backend Django

```bash
cd backend-django
python -m venv venv
source venv/bin/activate  # ou venv\Scripts\activate no Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### 3. Frontend React PWA

```bash
cd frontend-pwa
npm install
npm run dev
```

## 📁 Estrutura do Projeto

```
OpenEHRCore/
├── backend-django/
│   ├── manage.py
│   ├── requirements.txt
│   ├── openehrcore/
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   ├── fhir_api/
│   │   ├── views.py
│   │   ├── urls.py
│   │   └── services/
│   │       └── fhir_core.py
│   └── venv/
├── frontend-pwa/
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── src/
│   │   ├── theme/
│   │   │   └── colors.ts
│   │   ├── components/
│   │   │   ├── base/
│   │   │   │   ├── Button.tsx
│   │   │   │   ├── Card.tsx
│   │   │   │   └── Header.tsx
│   │   │   └── PatientDetail.tsx
│   │   └── App.tsx
│   └── node_modules/
├── docker/
│   └── docker-compose.yml
├── docs/
│   ├── ARCHITECTURE.md
│   ├── SETUP.md
│   └── DESIGN_SYSTEM.md
├── scripts/
│   └── validate-stack.sh
├── .gitignore
└── README.md
```

## 🎨 Design System

**Paleta Institucional:**

- **Primary Dark:** `#0339A6` (Menu/Header)
- **Primary Medium:** `#0468BF` (Botões/Ações)
- **Secondary/Accent:** `#79ACD9` (Destaques)
- **Alert/Critical:** `#D91A1A` (Erros/Alertas médicos)
- **Background/Surface:** `#F2F2F2` (Fundo geral)

**Princípios:** Clean design, whitespace generoso, tipografia sans-serif moderna, bordas suaves.

## 🔐 Segurança

- **Zero-Trust:** Keycloak para autenticação/autorização
- **LGPD/HIPAA:** Conformidade de dados clínicos
- **BFF Pattern:** Django protege HAPI FHIR do acesso direto
- **Validação FHIR:** fhirclient valida estrutura antes de persistir

## 📚 Documentação

- [ARCHITECTURE.md](docs/ARCHITECTURE.md) — Decisões arquiteturais e padrões
- [SETUP.md](docs/SETUP.md) — Instruções de setup detalhadas
- [DESIGN_SYSTEM.md](docs/DESIGN_SYSTEM.md) — Guia de componentes e tokens

## 🛠️ Tech Stack

- **Frontend:** React 18 + TypeScript + Vite + Tailwind CSS
- **Backend:** Django 4.x + Python 3.10+
- **FHIR:** HAPI FHIR Server (JPA) + fhirclient
- **Database:** PostgreSQL 14+
- **Auth:** Keycloak 20+
- **Containerization:** Docker + Docker Compose

## 📝 Licença

Copyright © 2025. Todos os direitos reservados.

---

**Status:** 🟢 Em produção. FHIR R4 Compliant (~95%).

## ✅ FHIR R4 Compliance

**Conformidade:** ~95% com HL7 FHIR R4

### Recursos Implementados

- ✅ **Patient** - Gestão completa de pacientes com identificadores brasileiros (CPF)
- ✅ **Practitioner** - Profissionais de saúde com CRM brasileiro
- ✅ **PractitionerRole** - Papéis, especialidades e organizações
- ✅ **Encounter** - Consultas e internações
- ✅ **Observation** - Sinais vitais com códigos LOINC
- ✅ **Condition** - Diagnósticos com SNOMED CT
- ✅ **MedicationRequest** - Prescrições
- ✅ **Composition** - Documentos clínicos
- ✅ **Location** - Hierarquia de leitos (Building → Ward → Room → Bed)
- ✅ **Appointment/Schedule/Slot** - Agendamentos
- ✅ **RelatedPerson** - Visitantes
- ✅ **Communication** - Mensagens/Chat

### Terminologias Suportadas

- **LOINC** - Observações e resultados laboratoriais
- **SNOMED CT** - Condições clínicas
- **HL7 CodeSystems** - Status e categorias
- **Brazilian NamingSystems** - CPF, CRM

### Novidades (Sprint 18 & 19)

- 🆕 **Sprint 18 - QA & FHIR R4 Compliance**
  - API completa para Practitioner (médicos, enfermeiros)
  - PractitionerRole para especialidades e organizações
  - Identificadores brasileiros (CPF, CRM) seguindo padrão HL7 BR
  - Auditoria FHIR R4 completa documentada
  - Suite de testes de conformidade FHIR
- 🆕 **Sprint 19 - Practitioner Frontend**
  - Interface completa de gerenciamento de profissionais
  - Formulário de cadastro com validação (CRM, email)
  - Busca por nome e CRM
  - Filtros por status (ativo/inativo)
  - Componentes React testados e documentados
  - Hook `usePractitioners` para integração com API
