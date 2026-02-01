# HealthStack

<div align="center">

**Plataforma de Interoperabilidade em Saude - FHIR R4 100% Nativo**

[![Versao](https://img.shields.io/badge/versao-2.2.0-7c3aed.svg)](https://github.com/ivonsmatos/OpenEHRCore)
[![FHIR](https://img.shields.io/badge/FHIR-R4_100%25-00d4ff.svg)](https://www.hl7.org/fhir/)
[![Licenca](https://img.shields.io/badge/licenca-MIT-green.svg)](LICENSE)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.2-blue.svg)](https://www.typescriptlang.org/)
[![Python](https://img.shields.io/badge/Python-3.11-yellow.svg)](https://www.python.org/)
[![RNDS](https://img.shields.io/badge/RNDS-Compliant-brightgreen.svg)](https://rnds.saude.gov.br/)

</div>

---

## Visao Geral

**HealthStack** e uma plataforma completa de interoperabilidade em saude construida sobre o padrao FHIR R4 com **conformidade 100%**. Fornece solucao completa para gestao de dados clinicos, incluindo funcionalidades de prontuario eletronico, fluxos clinicos e integracao com sistemas de saude brasileiros (RNDS, TISS).

### Caracteristicas Principais

| Categoria | Recursos |
|-----------|----------|
| **FHIR R4 100%** | Tipos de dados nativos, StructureDefinitions BR, Operacoes $expand/$validate-code/$lookup/$translate |
| **Audit Trail Completo** | AuditEvent (ATNA), Provenance, conformidade LGPD/HIPAA |
| **Terminologia** | ICD-10, SNOMED-CT, TUSS, CIAP-2, RxNorm com validacao |
| **Perfis Brasileiros** | Patient-BR, Practitioner-BR, Organization-BR (RNDS) |
| **Search Parameters** | _include, _revinclude, modifiers (:exact, :contains, :missing) |
| **PWA Offline-First** | Service Worker, IndexedDB, sincronizacao automatica |
| **Integracoes Brasil** | PIX, WhatsApp Business, Telemedicina, TISS, RNDS |
| **IA Multimodal** | MedGemma (Visao), MedASR (Voz), Resumo Inteligente |
| **Seguranca** | Keycloak SSO, RBAC, criptografia, auditoria completa |

---

## Novidades v2.2.0 - Sprint 36: FHIR R4 100% Compliance

### Tipos de Dados FHIR Nativos

Implementacao completa dos tipos de dados FHIR R4 em `fhir_types.py`:

```python
from fhir_api.fhir_types import (
    Identifier, CodeableConcept, Reference, Period,
    Quantity, HumanName, ContactPoint, Address,
    BrazilianIdentifiers, IdentifierList
)

# Criar identificador CPF
cpf = BrazilianIdentifiers.cpf_identifier("123.456.789-00")

# Criar identificador CRM
crm = BrazilianIdentifiers.crm_identifier("12345", "SP")

# CodeableConcept com terminologia
diagnosis = CodeableConcept.simple(
    code="J06.9",
    system="http://hl7.org/fhir/sid/icd-10",
    display="Acute upper respiratory infection"
)
```

### Perfis Brasileiros (RNDS)

StructureDefinitions para conformidade RNDS:

- **Patient-BR**: CPF/CNS obrigatorios, Raca/Cor, Nacionalidade
- **Practitioner-BR**: CRM, COREN, CRO, CRF, CRP com 58 especialidades CBO
- **Organization-BR**: CNES/CNPJ, tipos de estabelecimento

```python
from fhir_api.profiles import (
    PATIENT_BR_PROFILE,
    PRACTITIONER_BR_PROFILE,
    ORGANIZATION_BR_PROFILE
)
```

### Operacoes de Terminologia FHIR

Endpoints completos para operacoes de terminologia:

| Endpoint | Operacao | Descricao |
|----------|----------|-----------|
| `GET /terminology/ValueSet/$expand` | $expand | Expande ValueSet listando codigos |
| `GET /terminology/ValueSet/$validate-code` | $validate-code | Valida codigo em ValueSet |
| `GET /terminology/CodeSystem/$lookup` | $lookup | Busca detalhes de codigo |
| `GET /terminology/ConceptMap/$translate` | $translate | Traduz entre sistemas |

### AuditEvent e Provenance (LGPD/HIPAA)

Audit trail completo para conformidade regulatoria:

```python
from fhir_api.models_audit import AuditEvent, Provenance

# Registrar operacao REST
AuditEvent.log_rest_operation(
    action='R',  # Read
    resource_type='Patient',
    resource_id='123',
    user=request.user,
    request=request,
    outcome='0'  # Success
)

# Registrar proveniencia
Provenance.record_creation(
    target_references=[{'reference': 'Patient/123'}],
    agent_id='Practitioner/456',
    agent_name='Dr. Silva'
)
```

**Endpoints de Audit:**

| Endpoint | Descricao |
|----------|-----------|
| `GET /audit-events-v2/` | Lista eventos de auditoria |
| `GET /audit-events-v2/stats/` | Estatisticas de auditoria |
| `GET /audit-events-v2/by-patient/{id}/` | Eventos por paciente |
| `GET /audit-events-v2/security-report/` | Relatorio de seguranca |
| `GET /provenances/` | Lista proveniencias |
| `GET /provenances/by-target/` | Proveniencia por recurso |

### FHIR Search Parameters

Suporte completo a parametros de busca FHIR:

```python
from fhir_api.search import FHIRSearchMixin, SearchParameter, SearchParamType

class PatientViewSet(FHIRSearchMixin, viewsets.ModelViewSet):
    search_parameters = {
        'name': SearchParameter(
            name='name',
            type=SearchParamType.STRING,
            path='name',
            django_field='name'
        ),
        'birthdate': SearchParameter(
            name='birthdate',
            type=SearchParamType.DATE,
            path='birthDate',
            django_field='birth_date'
        ),
    }
```

**Recursos suportados:**
- `_include`: Inclui recursos referenciados
- `_revinclude`: Inclui recursos que referenciam
- Modifiers: `:exact`, `:contains`, `:missing`
- Prefixos: `eq`, `ne`, `gt`, `lt`, `ge`, `le`
- Paginacao: `_count`, `_offset`

### Validacao de Terminologia

```python
from fhir_api.validators import (
    TerminologyValidator,
    validate_code,
    BindingStrength
)

validator = TerminologyValidator()

# Validar codigo ICD-10
result = validator.validate_code(
    code="J06.9",
    system="http://hl7.org/fhir/sid/icd-10"
)

# Validar CPF brasileiro
is_valid = validator.validate_brazilian_cpf("123.456.789-00")

# Validar CNS
is_valid = validator.validate_brazilian_cns("123456789012345")
```

---

## Arquitetura

```
+---------------------------------------------------------------------+
|                         HealthStack v2.2.0                          |
+---------------------------------------------------------------------+
|                                                                      |
|  +-------------+  +-------------+  +-------------+                  |
|  |  Frontend   |  |   Backend   |  |  HAPI FHIR  |                  |
|  |  React PWA  |<-|   Django    |<-|   Server    |                  |
|  |  TypeScript |  |   Python    |  |   R4        |                  |
|  +-------------+  +-------------+  +-------------+                  |
|         |                |                |                          |
|         +----------------+----------------+                          |
|                          |                                           |
|  +-------------+  +-------------+  +-------------+                  |
|  |  Keycloak   |  |  PostgreSQL |  |   Redis     |                  |
|  |  Auth/SSO   |  |  Database   |  |   Cache     |                  |
|  +-------------+  +-------------+  +-------------+                  |
|                                                                      |
+---------------------------------------------------------------------+

+---------------------------------------------------------------------+
|  Agente On-Premise (Hospital)                                       |
|  +----------+ +----------+ +----------+                             |
|  | Lab      | | ECG      | | PACS     |                             |
|  | Analyzer | | Machine  | | DICOM    |                             |
|  +----+-----+ +----+-----+ +----+-----+                             |
|       | HL7/MLLP   | HL7       | DICOM                              |
|       +------------+-----------+                                    |
|                    |                                                 |
|            +-------+-------+                                        |
|            | HealthStack   |--------HTTPS--------> Servidor Cloud   |
|            |    Agent      |                                        |
|            +---------------+                                        |
+---------------------------------------------------------------------+
```

---

## Inicio Rapido

### Pre-requisitos

- Docker & Docker Compose
- Node.js 18+
- Python 3.11+

### Instalacao

```bash
# Clonar repositorio
git clone https://github.com/ivonsmatos/OpenEHRCore.git
cd OpenEHRCore

# Iniciar servicos
cd docker && docker-compose up -d

# Rodar migrations
docker-compose exec django python manage.py migrate

# Popular dados de exemplo
python scripts/seed/seed_fhir_direct.py

# Iniciar frontend
cd frontend-pwa && npm install && npm run dev
```

### Acesso

| Servico | URL |
|---------|-----|
| **Frontend** | http://localhost:5173 |
| **API Backend** | http://localhost:8000/api/v1 |
| **HAPI FHIR** | http://localhost:8080/fhir |
| **Keycloak** | http://localhost:8180 |
| **Swagger** | http://localhost:8000/api/v1/docs/swagger/ |

---

## Endpoints da API (130+)

### Recursos FHIR Principais

| Endpoint | Descricao |
|----------|-----------|
| `/api/v1/patients/` | Gestao de pacientes |
| `/api/v1/practitioners/` | Gestao de profissionais |
| `/api/v1/organizations/` | Gestao de organizacoes |
| `/api/v1/appointments/` | Agendamento de consultas |
| `/api/v1/encounters/` | Atendimentos clinicos |
| `/api/v1/observations/` | Sinais vitais e exames |
| `/api/v1/conditions/` | Diagnosticos |
| `/api/v1/medications/` | Prescricoes |
| `/api/v1/medication-administrations/` | Administracao de medicamentos |
| `/api/v1/tasks/` | Workflow e tarefas |
| `/api/v1/goals/` | Objetivos terapeuticos |
| `/api/v1/media/` | Imagens e videos clinicos |
| `/api/v1/documents/` | DocumentReference |
| `/api/v1/bundles/` | Transacoes em lote |
| `/api/v1/careplans/` | Planos de cuidado |
| `/api/v1/audit-events-v2/` | **NOVO** Eventos de auditoria |
| `/api/v1/provenances/` | **NOVO** Proveniencia de dados |

### Operacoes de Terminologia

| Endpoint | Descricao |
|----------|-----------|
| `/api/v1/terminology/ValueSet/$expand` | **NOVO** Expandir ValueSet |
| `/api/v1/terminology/ValueSet/$validate-code` | **NOVO** Validar codigo |
| `/api/v1/terminology/CodeSystem/$lookup` | **NOVO** Lookup de codigo |
| `/api/v1/terminology/ConceptMap/$translate` | **NOVO** Traduzir codigo |
| `/api/v1/terminology/rxnorm/search/` | Buscar medicamentos |
| `/api/v1/terminology/icd10/search/` | Buscar CID-10 |
| `/api/v1/terminology/tuss/search/` | Buscar procedimentos TUSS |

### Integracoes Brasil

| Endpoint | Descricao |
|----------|-----------|
| `/api/v1/pix/` | Pagamentos PIX |
| `/api/v1/whatsapp/` | Notificacoes WhatsApp |
| `/api/v1/telemedicine/` | Consultas por video |
| `/api/v1/tiss/` | Integracao ANS TISS |
| `/api/v1/rnds/` | RNDS Ministerio da Saude |

### IA e Analytics

| Endpoint | Descricao |
|----------|-----------|
| `/api/v1/ai/analyze-image/` | Analise de imagem (MedGemma) |
| `/api/v1/ai/transcribe/` | Transcricao de audio (MedASR) |
| `/api/v1/ai/summary/{id}/` | Resumo inteligente |
| `/api/v1/analytics/population/` | Metricas populacionais |
| `/api/v1/analytics/clinical/` | Metricas clinicas |

---

## Estrutura do Projeto

```
HealthStack/
+-- frontend-pwa/           # React TypeScript PWA
|   +-- src/
|   |   +-- components/     # Componentes reutilizaveis
|   |   +-- pages/          # Paginas
|   |   +-- hooks/          # Hooks customizados
|   |   +-- services/       # Servicos da API
|   |   +-- types/          # Tipos TypeScript
|
+-- backend-django/         # Django REST API
|   +-- fhir_api/
|   |   +-- fhir_types.py   # NOVO: Tipos FHIR R4 nativos
|   |   +-- models_audit.py # NOVO: AuditEvent e Provenance
|   |   +-- profiles/       # NOVO: StructureDefinitions BR
|   |   +-- search/         # NOVO: FHIR Search Parameters
|   |   +-- operations/     # NOVO: Operacoes de terminologia
|   |   +-- validators/     # NOVO: Validacao de terminologia
|   |   +-- views_*.py      # Views da API
|   |   +-- models_*.py     # Models Django
|
+-- agent/                  # Agente on-premise HL7/MLLP
+-- docker/                 # Configuracoes Docker
+-- docs/                   # Documentacao
+-- scripts/                # Scripts utilitarios
```

---

## Seguranca e Conformidade

| Padrao | Status |
|--------|--------|
| LGPD (Brasil) | Conforme |
| HIPAA | Pronto |
| ISO 27001 | Controles implementados |
| HL7 FHIR Security | OAuth 2.0, SMART on FHIR |
| IHE ATNA | AuditEvent completo |

### Recursos de Seguranca

- **Keycloak SSO** - Autenticacao centralizada
- **RBAC** - Controle de acesso baseado em papeis
- **AuditEvent** - Todas as acoes registradas (ATNA compliant)
- **Provenance** - Rastreabilidade de origem de dados
- **Criptografia** - Em repouso e em transito
- **Consentimento** - Rastreamento LGPD

---

## Historico de Versoes

### v2.2.0 - FHIR R4 100% Compliance (Sprint 36)

**Novos Recursos:**
- Tipos de dados FHIR R4 nativos (`fhir_types.py`)
- Perfis brasileiros RNDS (Patient-BR, Practitioner-BR, Organization-BR)
- Operacoes de terminologia ($expand, $validate-code, $lookup, $translate)
- AuditEvent e Provenance para conformidade LGPD/HIPAA
- FHIR Search Parameters (_include, _revinclude, modifiers)
- Validacao de terminologia com BindingStrength
- Validacao de identificadores brasileiros (CPF, CNS, CNES)

### v2.1.0 - Recursos FHIR Completos + Mobile-First

- MedicationAdministration, Task, Goal, Media
- Responsividade 100% em 15+ paginas
- Conformidade WCAG 2.1 AA

### v2.0.0 - IA Multimodal

- MedGemma para analise de imagens
- MedASR para transcricao de audio
- Resumo inteligente

---

## Documentacao

### Guias FHIR
- [Guia de Implementacao FHIR](docs/FHIR_IMPLEMENTATION_GUIDE.md)
- [Gestao de Documentos](docs/DOCUMENT_MANAGEMENT_GUIDE.md)

### Configuracao
- [Guia de Setup](docs/SETUP.md)
- [Setup Keycloak](docs/KEYCLOAK_SETUP.md)

### Seguranca
- [Auditoria de Seguranca](docs/seguranca/SECURITY_AUDIT_REPORT.md)

---

## Contribuindo

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/NovaFuncionalidade`)
3. Commit (`git commit -m 'Add nova funcionalidade'`)
4. Push (`git push origin feature/NovaFuncionalidade`)
5. Abra um Pull Request

### Padroes de Codigo

**Backend:**
- Siga padroes FHIR R4
- Use tipos de `fhir_types.py`
- Registre auditoria em acoes criticas
- Adicione testes unitarios

**Frontend:**
- Use hooks customizados (useIsMobile)
- Adicione aria-labels
- Siga WCAG 2.1 AA

---

## Licenca

MIT License - Veja [LICENSE](LICENSE) para detalhes.

---

<div align="center">

**Desenvolvido com amor para transformar a saude digital no Brasil**

[Website](https://healthstack.com.br) | [Documentacao](./docs) | [Issues](https://github.com/ivonsmatos/OpenEHRCore/issues)

</div>
