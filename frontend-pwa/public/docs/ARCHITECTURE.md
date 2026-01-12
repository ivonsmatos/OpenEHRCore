# Arquitetura Técnica — OpenEHRCore (FHIR-First)

## 📋 Visão Geral

OpenEHRCore é um sistema EHR enterprise-grade baseado no padrão **HL7 FHIR R4**, projetado para clínicas e hospitais. A arquitetura segue o princípio **FHIR-First**: o HAPI FHIR Server é a autoridade absoluta dos dados clínicos.

```
┌─────────────────────────────────────────────────────────────────┐
│  FRONTEND PWA (React 18 + TypeScript + Tailwind)                │
│  - Design System limpo e minimalista                            │
│  - Parsing seguro de JSON FHIR                                  │
│  - Offline-first com Service Workers (Phase 2)                  │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTP/REST
                         │
┌────────────────────────▼────────────────────────────────────────┐
│  BFF — Backend (Django 4.2 + Python 3.10)                       │
│  - Guardião: Protege HAPI FHIR com autenticação                │
│  - fhirclient SDK: Manipulação segura de recursos FHIR         │
│  - Keycloak Integration: OAuth2/OIDC                           │
│  - Validação FHIR antes de persistir                           │
└────────────────────────┬────────────────────────────────────────┘
                         │ FHIR REST API
                         │
┌────────────────────────▼────────────────────────────────────────┐
│  HAPI FHIR Server 7.2 (JPA Mode)                                │
│  - Porta 8080: /fhir/* endpoints FHIR R4                        │
│  - PostgreSQL: Persistência de dados clínicos                   │
│  - CapabilityStatement completo                                 │
│  - Validação nativa FHIR antes de aceitar recursos              │
└─────────────────────────────────────────────────────────────────┘
```

## 🔐 Princípios Arquiteturais

### 1. FHIR-First (Autoridade Absoluta)

- **HAPI FHIR é o dono dos dados**, não o Django
- Django manipula dados apenas através da lib `fhirclient`
- Todos os recursos seguem stricto senso a spec FHIR R4
- Não existem tabelas Django para dados clínicos (Patient, Encounter, Observation)

### 2. BFF Pattern (Backend for Frontend)

- Django atua como **Guardião**, não como proprietário
- Responsabilidades:
  - Autenticação/Autorização (Keycloak)
  - Validação de negócio
  - Orquestração de recursos FHIR
  - Sanitização de dados antes de enviar ao frontend

### 3. Zero-Trust Security

- Keycloak para autenticação de todos os usuários
- Tokens JWT validados em cada requisição
- Django valida permissions antes de permitir acesso
- HTTPS only em produção
- LGPD/HIPAA compliance

### 4. Type Safety

- TypeScript end-to-end (Frontend)
- Python type hints (Backend)
- SDK `fhirclient` garante tipos FHIR válidos
- OpenAPI specs para documentação automática

## 📁 Estrutura do Projeto

```
OpenEHRCore/
│
├── docker/
│   └── docker-compose.yml          # Stack: HAPI FHIR + PostgreSQL + Keycloak
│
├── backend-django/
│   ├── manage.py
│   ├── requirements.txt
│   ├── openehrcore/
│   │   ├── settings.py             # Configuração Django
│   │   ├── urls.py                 # Rotas da aplicação
│   │   └── wsgi.py
│   ├── fhir_api/
│   │   ├── views.py                # REST endpoints
│   │   ├── urls.py
│   │   └── services/
│   │       └── fhir_core.py        # ⭐ FHIRService (orquestração)
│   └── venv/
│
├── frontend-pwa/
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js          # Design System tokens
│   ├── src/
│   │   ├── theme/
│   │   │   └── colors.ts           # ⭐ Paleta institucional
│   │   ├── components/
│   │   │   ├── base/               # Design System
│   │   │   │   ├── Button.tsx
│   │   │   │   ├── Card.tsx
│   │   │   │   └── Header.tsx
│   │   │   └── PatientDetail.tsx    # ⭐ Exemplo: tela de paciente
│   │   ├── utils/
│   │   │   └── fhirParser.ts       # ⭐ Parsing seguro FHIR
│   │   └── App.tsx
│   └── public/
│
├── docs/
│   ├── ARCHITECTURE.md             # Este arquivo
│   ├── SETUP.md
│   └── DESIGN_SYSTEM.md
│
├── scripts/
│   └── validate-stack.sh
│
├── .gitignore
└── README.md
```

## 🏗️ Componentes Principais

### Backend — FHIRService (`backend-django/fhir_api/services/fhir_core.py`)

Classe centralizada que gerencia toda comunicação com HAPI FHIR:

```python
class FHIRService:
    def health_check(self) -> bool
    def create_patient_resource(self, ...) -> Dict
    def get_patient_by_id(self, patient_id) -> Dict
    def create_encounter_resource(self, ...) -> Dict
    def create_observation_resource(self, ...) -> Dict
```

**Exemplo de uso:**

```python
fhir_service = FHIRService()

# Criar paciente com validação FHIR nativa
patient = fhir_service.create_patient_resource(
    first_name="João",
    last_name="Silva",
    birth_date="1990-05-15",
    cpf="12345678901",
    gender="male"
)

# Resultado é um recurso Patient válido no HAPI FHIR
```

### Frontend — PatientDetail (`frontend-pwa/src/components/PatientDetail.tsx`)

Componente React que exibe informações de paciente com:

- Parsing seguro de JSON FHIR complexo
- Design System com paleta institucional
- Whitespace generoso e tipografia moderna

**Utiliza utilitários em `fhirParser.ts`:**

```typescript
getPatientFullName(patient); // Extrai nome com segurança
getPatientCPF(patient); // Busca CPF por system
formatPatientBirthDate(birthDate); // Formata com Intl API
calculatePatientAge(birthDate); // Calcula idade
getPatientSummary(patient); // Resume completo
```

### Design System — Tema (`frontend-pwa/src/theme/colors.ts`)

Token centralizado da paleta institucional:

```typescript
colors.primary.dark = "#0339A6"; // Menu/Header
colors.primary.medium = "#0468BF"; // Botões
colors.accent.primary = "#79ACD9"; // Destaques
colors.alert.critical = "#D91A1A"; // Alertas
colors.background.surface = "#F2F2F2"; // Fundo
```

## 🔄 Fluxo de Dados (Exemplo: Criar Paciente)

```
1. Frontend (React)
   └─> Button "Criar Paciente" + formulário
        └─> POST /api/v1/patients/
            Body: { first_name, last_name, birth_date, ... }

2. Backend (Django/FHIRService)
   └─> views.create_patient()
        └─> FHIRService.create_patient_resource()
            ├─> Instancia objeto fhirclient.Patient
            ├─> Popula fields conforme FHIR R4 spec
            ├─> Serializa para JSON FHIR
            └─> POST http://hapi-fhir:8080/fhir/Patient

3. HAPI FHIR Server
   └─> Valida contra perfil FHIR R4
        ├─> Gera ID único
        ├─> Persiste em PostgreSQL
        └─> Retorna Patient com id + metadata

4. Frontend (React)
   └─> Recebe { resourceType, id, name, ... }
        └─> PatientDetail.tsx exibe com segurança
            ├─> getPatientFullName() para nome
            ├─> getPatientCPF() para CPF
            └─> Renderiza com Design System
```

## 🔌 APIs Principais (Django)

| Endpoint                 | Method | Descrição                   |
| ------------------------ | ------ | --------------------------- |
| `/api/v1/health/`        | GET    | Health check da stack       |
| `/api/v1/patients/`      | POST   | Cria novo paciente          |
| `/api/v1/patients/{id}/` | GET    | Recupera paciente por ID    |
| `/api/v1/encounters/`    | POST   | Cria encontro (consulta)    |
| `/api/v1/observations/`  | POST   | Cria observação (resultado) |

**Exemplo: Criar paciente**

```bash
curl -X POST http://localhost:8000/api/v1/patients/ \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "João",
    "last_name": "Silva",
    "birth_date": "1990-05-15",
    "cpf": "12345678901",
    "gender": "male"
  }'
```

## 🎨 Design System

### Paleta Institucional

- **Primary Dark (#0339A6)**: Menu, header, elementos confiança
- **Primary Medium (#0468BF)**: Botões, ações principais
- **Secondary (#79ACD9)**: Destaques suaves
- **Alert (#D91A1A)**: Erros e alertas médicos críticos
- **Background (#F2F2F2)**: Fundo geral clean

### Princípios

1. **Whitespace generoso** — Espaçamento 8px base
2. **Tipografia limpa** — Sans-serif moderna (Inter/System)
3. **Bordas suaves** — Rounded 6-12px
4. **Sombras sutis** — Profundidade sem peso visual

### Componentes Base

- **Button** — Variantes: primary, secondary, danger, ghost
- **Card** — Agrupador de conteúdo com shadow
- **Header** — Cabeçalho fixo azul escuro

## 📦 Stack Técnico

| Camada      | Tecnologia         | Versão   |
| ----------- | ------------------ | -------- |
| Frontend    | React + TypeScript | 18 / 5.2 |
| Build       | Vite               | 5.0      |
| Styles      | Tailwind CSS       | 3.3      |
| Backend     | Django             | 4.2      |
| Python      | Python             | 3.10+    |
| FHIR SDK    | fhirclient         | 4.2      |
| Auth        | Keycloak           | 24.0     |
| FHIR Server | HAPI FHIR JPA      | 7.2      |
| Database    | PostgreSQL         | 14+      |
| Container   | Docker Compose     | 3.8      |

## 🔐 Segurança

### Autenticação

- Keycloak (OAuth2/OIDC)
- Tokens JWT validados em cada request
- Refresh tokens persistidos seguramente

### Autorização

- RBAC (Role-Based Access Control) via Keycloak
- Django valida permissions antes de manipular FHIR

### Dados

- Criptografia em trânsito (HTTPS/TLS em prod)
- FHIR valida estrutura antes de persistir
- PostgreSQL com backups diários
- LGPD/HIPAA compliance

## 🧪 Validação

### FHIR Native

- `fhirclient` valida tipos e estrutura antes de enviar
- HAPI FHIR valida novamente no servidor
- Erros retornam OperationOutcome FHIR

### Type Safety

- TypeScript strict mode (Frontend)
- Python type hints (Backend)
- IDE autocomplete para recursos FHIR

## 🚀 Deployment (Phase 2)

```bash
# Docker Compose (desenvolvimento)
cd docker && docker-compose up -d

# Kubernetes (produção)
kubectl apply -f k8s/

# CI/CD: GitHub Actions
.github/workflows/deploy.yml
```

## 📖 Referências

- [HL7 FHIR R4 Spec](https://www.hl7.org/fhir/R4/)
- [HAPI FHIR Documentation](https://hapifhir.io/)
- [fhirclient Python SDK](https://github.com/smart-on-fhir/client-py)
- [Keycloak Admin Guide](https://www.keycloak.org/documentation)

---

**Status**: 🟢 Alpha (Scaffolding completo, features base implementadas)  
**Próximas fases**: Keycloak integration, offline-first, observações clínicas, auditoria
