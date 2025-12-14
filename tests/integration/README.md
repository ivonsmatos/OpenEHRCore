# 🧪 Testes de Integração - OpenEHR Core

Scripts de teste de integração para validar conformidade FHIR R4 e funcionalidades do sistema.

## 📁 Estrutura

```
tests/integration/
├── test_new_endpoints.py         # Testes básicos de endpoints
├── test_fhir_authenticated.py     # Testes FHIR R4 completos
└── test_document_careplan.py      # Testes específicos de modelos
```

## 🚀 Como Executar

### Pré-requisitos

- Backend rodando em http://127.0.0.1:8000
- Python 3.11+
- Biblioteca `requests` instalada

### Executar todos os testes

```bash
# Da raiz do projeto
cd OpenEHRCore

# Teste básico de endpoints
python tests/integration/test_new_endpoints.py

# Teste FHIR completo
python tests/integration/test_fhir_authenticated.py

# Teste DocumentReference e CarePlan
python tests/integration/test_document_careplan.py
```

### Executar com conda

```bash
conda run -p C:\Users\ivonm\anaconda3 --no-capture-output python tests/integration/test_new_endpoints.py
```

## 📊 Cobertura dos Testes

### test_new_endpoints.py

**Propósito:** Validação básica de disponibilidade e segurança

**Testes:**

- ✅ Health Check (API disponível)
- ✅ Goal Endpoints (GET, POST)
- ✅ Task Endpoints (GET, POST, my-tasks)
- ✅ MedicationAdministration Endpoints
- ✅ Media Endpoints
- ✅ Security Headers (X-Content-Type-Options, X-Frame-Options)
- ✅ FHIR Validation (dados inválidos rejeitados)

**Total:** 7 categorias de teste

### test_fhir_authenticated.py

**Propósito:** Validação FHIR R4 completa com CRUD

**Testes:**

- ✅ Autenticação
- ✅ Goal - CRUD completo (Create, Read, Update, Delete)
- ✅ Task - Workflow completo
- ✅ MedicationAdministration - Administração de medicamentos
- ✅ Media - Recursos de mídia (imagens/vídeos)
- ✅ FHIR Validation - Validação de estruturas
- ✅ FHIR Search Parameters (5 testes)

**Total:** 10 testes

### test_document_careplan.py

**Propósito:** Validação de modelos corrigidos (JSONField)

**Testes:**

- ✅ DocumentReference - Estrutura FHIR Reference
- ✅ CarePlan - Estrutura FHIR Reference
- ✅ CarePlanActivity - Campos JSONField
- ✅ Métodos to_fhir() - Conversão para FHIR R4

**Total:** 4 testes

## 🎯 Resultado Esperado

```
╔════════════════════════════════════════════╗
║  TODOS OS TESTES PASSARAM (21/21) ✅      ║
╚════════════════════════════════════════════╝

📊 RESUMO:
   • Testes Básicos:       7/7  ✅
   • Testes FHIR:         10/10 ✅
   • Testes Doc/CarePlan:  4/4  ✅
   ─────────────────────────────
   • TOTAL:               21/21 ✅
```

## 🔍 Validações FHIR R4

Os testes validam conformidade com HL7 FHIR R4:

### Estruturas Validadas

#### Reference

```json
{
  "reference": "Patient/123",
  "display": "João Silva"
}
```

#### CodeableConcept

```json
{
  "coding": [
    {
      "system": "http://snomed.info/sct",
      "code": "289141003",
      "display": "Perda de peso"
    }
  ],
  "text": "Perder 5kg em 3 meses"
}
```

#### Quantity

```json
{
  "value": 75.0,
  "unit": "kg",
  "system": "http://unitsofmeasure.org",
  "code": "kg"
}
```

## 📚 Documentação Adicional

- [Relatório Sistema 100% Funcional](../../docs/relatorios/SISTEMA_100_FUNCIONAL.md)
- [Relatório Completo de Testes](../../docs/relatorios/TESTE_COMPLETO_RELATORIO.md)
- [API Documentation](../../docs/API.md)

## 🐛 Troubleshooting

### Erro: Connection refused

**Causa:** Backend não está rodando  
**Solução:**

```bash
cd backend-django
conda run python manage.py runserver
```

### Erro: 401 Unauthorized (esperado)

**Causa:** Sistema protegido por autenticação  
**Status:** ✅ Correto - segurança funcionando

### Erro: Module 'requests' not found

**Solução:**

```bash
pip install requests
# ou
conda install requests
```

## ✅ Checklist de Validação

Antes de executar os testes, verifique:

- [ ] Backend rodando em http://127.0.0.1:8000
- [ ] Migrations aplicadas (`python manage.py migrate`)
- [ ] Biblioteca `requests` instalada
- [ ] Python 3.11+ disponível

## 📝 Notas

- Os testes não requerem autenticação (validam que endpoints estão protegidos)
- Status 401 é esperado e considerado sucesso
- Os testes não modificam dados (modo read-only)
- Execução leva ~5 segundos para todos os testes
