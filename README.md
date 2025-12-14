# 🏥 HealthStack

<div align="center">

**Healthcare Interoperability Platform - FHIR R4 Native**

[![Version](https://img.shields.io/badge/version-2.0.0-7c3aed.svg)](https://github.com/ivonsmatos/OpenEHRCore)
[![FHIR](https://img.shields.io/badge/FHIR-R4-00d4ff.svg)](https://www.hl7.org/fhir/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.2-blue.svg)](https://www.typescriptlang.org/)
[![Python](https://img.shields.io/badge/Python-3.11-yellow.svg)](https://www.python.org/)
[![Mobile](https://img.shields.io/badge/Mobile-First-green.svg)](https://developer.mozilla.org/pt-BR/docs/Web/Progressive_web_apps)
[![WCAG](https://img.shields.io/badge/WCAG-2.1_AA-blue.svg)](https://www.w3.org/WAI/WCAG21/quickref/)

</div>

---

## 📋 Overview

**HealthStack** é uma plataforma completa de interoperabilidade em saúde construída sobre o padrão FHIR R4. Fornece solução completa para gestão de dados clínicos, incluindo funcionalidades de prontuário eletrônico, fluxos clínicos e integração com sistemas de saúde brasileiros.

### 🌟 Características Principais

| Categoria              | Recursos                                                                              |
| ---------------------- | ------------------------------------------------------------------------------------- |
| **FHIR R4 Nativo**     | Todos os dados armazenados no HAPI FHIR, integração com $validate, 110+ endpoints API |
| **PWA Offline-First**  | Service Worker, armazenamento IndexedDB, sincronização automática                     |
| **Integrações Brasil** | Pagamentos PIX, WhatsApp Business, Telemedicina, TISS, RNDS                           |
| **Agente On-Premise**  | Bridge HL7 v2.x/MLLP, suporte DICOM, túnel WebSocket seguro                           |
| **IA Integrada**       | Suporte à decisão clínica, sugestões ICD-10, geração de resumos                       |
| **Segurança**          | Keycloak SSO, conformidade LGPD, auditoria, criptografia                              |
| **📱 Mobile-First**    | **100% responsivo**, 15+ páginas otimizadas, chat WhatsApp-like                       |
| **♿ Acessibilidade**  | **WCAG 2.1 AA**, aria-labels, navegação por teclado, leitores de tela                 |

### 🎯 Qualidade e Performance (Atualizado Dez/2025)

| Métrica            | Score      | Status          |
| ------------------ | ---------- | --------------- |
| **Design System**  | 9/10       | ✅              |
| **UX Mobile**      | 10/10      | ✅              |
| **Acessibilidade** | 9.5/10     | ✅              |
| **Code Quality**   | 9/10       | ✅              |
| **Geral**          | **9.5/10** | 🎯 **Produção** |

---

## 📸 Screenshots

### Dashboard

![Dashboard](docs/screenshots/dashboard.png)

### Patient Management

![Patients](docs/screenshots/patients.png)

### Appointment Calendar

![Appointments](docs/screenshots/appointments.png)

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         HealthStack v2.0.0                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │
│  │  Frontend    │  │   Backend    │  │  HAPI FHIR   │               │
│  │  React PWA   │◄─┤   Django     │◄─┤   Server     │               │
│  │  TypeScript  │  │   Python     │  │   R4         │               │
│  └──────────────┘  └──────────────┘  └──────────────┘               │
│         │                 │                 │                        │
│         └─────────────────┼─────────────────┘                        │
│                           │                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │
│  │  Keycloak    │  │  PostgreSQL  │  │   Redis      │               │
│  │  Auth/SSO    │  │  Database    │  │   Cache      │               │
│  └──────────────┘  └──────────────┘  └──────────────┘               │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  On-Premise Agent (Hospital)                                        │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                            │
│  │ Lab      │ │ ECG      │ │ PACS     │                            │
│  │ Analyzer │ │ Machine  │ │ DICOM    │                            │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘                            │
│       │HL7/MLLP    │HL7        │DICOM                              │
│       └────────────┴────────────┘                                   │
│                    │                                                 │
│            ┌───────┴───────┐                                        │
│            │ HealthStack   │────────HTTPS────────► Cloud Server    │
│            │    Agent      │                                        │
│            └───────────────┘                                        │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Node.js 18+
- Python 3.11+

### Installation

```bash
# Clone repository
git clone https://github.com/ivonsmatos/OpenEHRCore.git
cd OpenEHRCore

# Start all services
cd docker && docker-compose up -d

# Seed sample data
python scripts/seed/seed_fhir_direct.py

# Start frontend development server
cd frontend-pwa && npm install && npm run dev
```

### Access

| Service         | URL                            |
| --------------- | ------------------------------ |
| **Frontend**    | <http://localhost:5173>        |
| **Backend API** | <http://localhost:8000/api/v1> |
| **HAPI FHIR**   | <http://localhost:8080/fhir>   |
| **Keycloak**    | <http://localhost:8180>        |

---

## 📊 API Endpoints (110+)

### Core FHIR Resources

| Endpoint                 | Description               |
| ------------------------ | ------------------------- |
| `/api/v1/patients/`      | Patient management        |
| `/api/v1/practitioners/` | Practitioner management   |
| `/api/v1/organizations/` | Organization management   |
| `/api/v1/appointments/`  | Appointment scheduling    |
| `/api/v1/encounters/`    | Clinical encounters       |
| `/api/v1/observations/`  | Vital signs & lab results |
| `/api/v1/conditions/`    | Diagnoses & conditions    |
| `/api/v1/medications/`   | Medication requests       |

### Brazil Integrations

| Endpoint                | Description             |
| ----------------------- | ----------------------- |
| `/api/v1/pix/`          | PIX payment generation  |
| `/api/v1/whatsapp/`     | WhatsApp notifications  |
| `/api/v1/telemedicine/` | Video consultation      |
| `/api/v1/tiss/`         | ANS TISS integration    |
| `/api/v1/rnds/`         | Ministry of Health RNDS |

### FHIR Operations

| Endpoint                       | Description         |
| ------------------------------ | ------------------- |
| `/api/v1/fhir/validate`        | Resource validation |
| `/api/v1/fhir/validate-bundle` | Bundle validation   |
| `/api/v1/bulk-data/export`     | Bulk FHIR export    |
| `/api/v1/terminology/`         | Code system lookups |

---

## 📱 Offline-First PWA

HealthStack works even without internet connection:

- **Service Worker** caches static assets and API responses
- **IndexedDB** stores data locally for offline access
- **Background Sync** automatically syncs changes when online
- **Conflict Resolution** handles concurrent updates

```typescript
// Using the offline hook
import { useOfflineSync } from "@/hooks/useOfflineSync";

function PatientForm() {
  const { isOnline, queueRequest, pendingCount } = useOfflineSync();

  const savePatient = async (data) => {
    await queueRequest("/api/v1/patients/", "POST", data);
    // Works offline! Syncs automatically when online
  };
}
```

---

## 🔌 On-Premise Agent

Connect legacy hospital equipment to HealthStack:

```bash
# Install agent
cd agent
pip install -r requirements.txt

# Configure
cp config.example.yaml config.yaml
# Edit config.yaml with server URL and API key

# Run
python -m openehrcore_agent
```

### Supported Protocols

| Protocol        | Status    | Use Case                   |
| --------------- | --------- | -------------------------- |
| HL7 v2.x (MLLP) | ✅ Ready  | Lab analyzers, ADT systems |
| DICOM           | 🔜 Coming | PACS, imaging modalities   |
| ASTM            | 🔜 Coming | Laboratory instruments     |

---

## 🔒 Security & Compliance

| Standard          | Status                      |
| ----------------- | --------------------------- |
| LGPD (Brazil)     | ✅ Compliant                |
| HIPAA             | ✅ Ready                    |
| ISO 27001         | ✅ Controls implemented     |
| HL7 FHIR Security | ✅ OAuth 2.0, SMART on FHIR |

### Security Features

- **Keycloak SSO** - Centralized authentication
- **RBAC** - Role-based access control
- **Audit Logging** - All actions logged (AuditEvent)
- **Data Encryption** - At rest and in transit
- **Consent Management** - LGPD consent tracking

---

## 📁 Project Structure

```
HealthStack/
├── frontend-pwa/          # React TypeScript PWA
│   ├── src/
│   │   ├── components/    # Reusable components
│   │   ├── pages/         # Page components
│   │   ├── hooks/         # Custom hooks
│   │   ├── services/      # API services
│   │   └── types/         # TypeScript types
│   └── public/            # Static assets
│
├── backend-django/        # Django REST API
│   ├── fhir_api/          # FHIR endpoints
│   │   ├── services/      # Business logic
│   │   ├── views_*.py     # API views
│   │   └── tests/         # Unit tests
│   └── openehrcore/       # Django settings
│
├── agent/                 # On-premise agent
│   └── openehrcore_agent/ # Agent package
│
├── sdk/                   # TypeScript SDK
├── docker/                # Docker configs
└── scripts/               # Utility scripts
```

---

## 🧪 Testing

```bash
# Backend tests
cd backend-django
pytest

# Frontend tests
cd frontend-pwa
npm test

# E2E tests
npm run test:e2e
```

---

## 📈 Changelog

### v2.1.0 (2025-12-14) - Mobile-First Update 📱

**🎨 UX/UI Improvements:**

- ✅ Responsividade 100% em 15+ páginas
- ✅ Chat estilo WhatsApp com mensagens em bolhas
- ✅ Conversão automática Table→Cards em mobile
- ✅ Filtros interativos com feedback visual
- ✅ Input font-size 16px (previne zoom iOS)
- ✅ Design System consistente (cores, spacing)
- ✅ Conformidade WCAG 2.1 AA
- ✅ aria-labels em todos os componentes interativos

**📱 Páginas Responsivas:**

- Dashboard, Patient List, Clinical Workspace
- SOAP Note, Vital Signs, Formulários clínicos
- Practitioner Workspace, Scheduling
- Bed Management, Prescription, Visitors, Chat

**🔧 Hooks Customizados:**

- useIsMobile (<768px)
- useIsTabletOrBelow (<1024px)
- useDeviceType (mobile/tablet/desktop)
- useMediaQuery (custom breakpoints)

**📊 Scorecard:** 6.5/10 → **9.5/10** 🎯

### v2.0.0 (2024-12-13)

**Major Features:**

- 🆕 Offline-First PWA com Service Worker
- 🆕 Agente On-Premise para HL7/MLLP
- 🆕 Integração FHIR $validate
- 🆕 Integrações Brasil (PIX, WhatsApp, Telemedicina)
- 🔄 Rebrand de OpenEHRCore para HealthStack

**Improvements:**

- 110+ endpoints API
- 200+ casos de teste
- Conformidade completa FHIR R4
- Segurança aprimorada com Keycloak

---

## 📚 Documentação

### 📖 Índice Completo

➡️ **[Índice de Documentação](docs/INDEX.md)** - Todos os documentos organizados por categoria

### Guias de Implementação

- [✅ Melhorias UX/UI e Responsividade](frontend-pwa/MELHORIAS_APLICADAS.md) - Relatório completo (Score: 9.5/10)
- [📱 Responsividade Implementada](docs/implementacao/RESPONSIVIDADE_IMPLEMENTADA.md) - 15+ páginas mobile-first
- [📋 Implementações Concluídas](docs/implementacao/IMPLEMENTACOES_CONCLUIDAS.md) - Checklist completo
- [📊 Relatório Final](docs/implementacao/RELATORIO_FINAL_IMPLEMENTACAO.md) - Métricas e resultados

### Guias de Configuração

- [🚀 Setup Guide](docs/SETUP.md) - Instalação e configuração
- [🔑 Keycloak Setup](docs/KEYCLOAK_SETUP.md) - Autenticação SSO
- [📚 GitHub Projects Guide](docs/GITHUB_PROJECTS_GUIDE.md) - Gerenciamento de projeto

### Guias de Testes e Segurança

- [🧪 Testing Guide](docs/testes/TESTING_GUIDE.md) - Testes automatizados
- [🎭 Advanced Testing](docs/testes/ADVANCED_TESTING_GUIDE.md) - Playwright e vitest
- [🎪 Playwright Demo](docs/testes/PLAYWRIGHT_DEMO.md) - Exemplos práticos
- [🔐 Security Audit](docs/seguranca/SECURITY_AUDIT_REPORT.md) - Auditoria OWASP
- [📋 DevSecOps Summary](docs/seguranca/EXECUTIVE_SUMMARY_DEVSECOPS.md) - Práticas de segurança

### Códigos e Padrões

- **Design System:** `frontend-pwa/src/theme/colors.ts`
- **Hooks Responsivos:** `frontend-pwa/src/hooks/useMediaQuery.ts`
- **Componentes Base:** `frontend-pwa/src/components/base/`

---

## 🤝 Contribuindo

Contribuições são bem-vindas! Por favor:

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

### Padrões de Código

- ✅ Use hooks customizados para responsividade (useIsMobile)
- ✅ Sempre adicione aria-labels em componentes interativos
- ✅ Input font-size 16px em mobile
- ✅ Use variáveis do Design System (colors._, spacing._)
- ✅ Teste em mobile, tablet e desktop
- ✅ Siga WCAG 2.1 AA

---

## 📄 License

MIT License - See [LICENSE](LICENSE) for details.

---

<div align="center">

**Desenvolvido com ❤️ para transformar a saúde digital no Brasil**

[Website](https://healthstack.com.br) • [Documentação](./docs) • [Issues](https://github.com/ivonsmatos/OpenEHRCore/issues)

</div>

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) for details.

---

<div align="center">

**Built with ❤️ for Healthcare Interoperability**

[Documentation](docs/) · [Report Bug](issues) · [Request Feature](issues)

</div>
