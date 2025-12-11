# OpenEHRCore — Sistema de Gestão de Prontuários Eletrônicos (EHR) Seguro com FHIR

Um sistema EHR enterprise-grade baseado no padrão **HL7 FHIR R4** para clínicas e hospitais, com suporte a apps web e mobile.

## 🏗️ Arquitetura FHIR-First

```mermaid
graph TD
    UserWeb[Frontend Web (PWA)] --> BFF
    UserMobile[Mobile App (React Native)] --> BFF
    BFF[BFF - Backend (Django)] --> Cache[Redis Cache]
    BFF --> FHIR[HAPI FHIR Server]
    BFF --> Auth[Keycloak (OAuth2)]
    FHIR --> DB[(PostgreSQL)]
```

## 📅 Roadmap de Implementação (Histórico Cronológico)

O desenvolvimento do OpenEHRCore seguiu uma abordagem ágil, entregando valor incrementalmente a cada Sprint. Abaixo, o histórico das principais entregas:

### Fase 1: Fundação e Core (Sprints 1-19)

- **Infraestrutura:** Setup de Docker Compose com HAPI FHIR, PostgreSQL e Keycloak.
- **Backend Core:** Implementação do BFF em Django, autenticação OAuth2 e serviços FHIR básicos.
- **Frontend Core:** Setup do React PWA, Design System inicial e telas de autenticação.
- **Recursos FHIR:** Implementação dos recursos base (Patient, Practitioner, Encounter, Observation).

### Fase 2: Funcionalidades Avançadas (Sprints 20-23)

- ✅ **Sprint 20 - Busca Avançada:**
  - Backend: Parâmetros de busca complexos para Pacientes e Profissionais.
  - Frontend: Filtros avançados, paginação e barra de busca global.
- ✅ **Sprint 21 - Terminologias:**
  - Integração com LOINC (Exames), SNOMED CT (Diagnósticos), ICD-10 e RxNorm.
  - TUSS (Tabela SUS) para procedimentos nacionais.
- ✅ **Sprint 22 - Bulk Data (Interoperabilidade):**
  - Operações `$export` e `$import` seguindo padrão FHIR Bulk Data.
  - Suporte a NDJSON para transferência de grandes volumes de dados.
- ✅ **Sprint 23 - Qualidade e CI/CD:**
  - Testes unitários, integração e E2E (Playwright).
  - Pipelines de CI/CD no GitHub Actions.

### Fase 3: Segurança, Performance e Mobile (Sprints 24-26)

- ✅ **Sprint 24 - LGPD & Privacidade:**
  - Gestão de Consentimento (FHIR Consent).
  - Dashboard de Privacidade para o paciente.
  - Logs de acesso auditáveis e direito ao esquecimento/exportação.
- ✅ **Sprint 25 - Performance:**
  - **Backend:** Redis Cache, otimização de queries Django, middlewares de performance.
  - **Frontend:** Code splitting, Lazy Loading de rotas.
- ✅ **Sprint 26 - Mobile App (React Native):**
  - **Portal do Paciente:** App iOS/Android completo.
  - **Features:** Agendamento, Prontuário, Notificações Push e Biometria.

## 🚀 Funcionalidades Principais por Módulo

### 🏥 Clínico (Web e Backend)

- Prontuário Eletrônico do Paciente (PEP) completo.
- Prescrição Eletrônica e Solicitação de Exames.
- Gestão de Internação e Leitos.
- Chat seguro entre profissionais.

### 📱 Portal do Paciente (Mobile)

- Acesso rápido a resultados de exames e receitas.
- Agendamento de consultas (Presencial/Telemedicina).
- Notificações em tempo real.
- Controle total sobre dados e privacidade.

### 🛡️ Segurança e Infraestrutura

- Conformidade HL7 FHIR R4 (~95%).
- Autenticação Zero-Trust via Keycloak.
- Auditoria granular de acessos.
- Alta disponibilidade com Containerização.

## 🛠️ Tech Stack

- **Frontend Web:** React 18, TypeScript, Vite, Vitest.
- **Mobile:** React Native, Expo SDK 51, TypeScript.
- **Backend:** Django 4.x, Python 3.10+, Redis.
- **FHIR:** HAPI FHIR Server (Java/JPA).
- **Database:** PostgreSQL 14+.
- **Auth:** Keycloak 20+.

## 🚀 Quick Start

### 1. Infraestrutura (Docker)

```bash
cd docker
docker-compose up -d
```

### 2. Backend Django

```bash
cd backend-django
# Configurar venv e instalar deps...
python manage.py runserver
```

### 3. Frontend Web

```bash
cd frontend-pwa
npm run dev
```

### 4. Mobile App

```bash
cd mobile-app
npm start
```

## 📁 Estrutura do Monorepo

```
OpenEHRCore/
├── backend-django/       # API Gateway & Business Logic
├── frontend-pwa/         # Web App (React)
├── mobile-app/           # Mobile App (React Native)
├── docker/               # Infraestrutura
└── docs/                 # Documentação
```

## 📝 Licença

Copyright © 2025 OpenEHRCore Team. Todos os direitos reservados.
