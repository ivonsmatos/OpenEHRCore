# Guia Rápido - Resumos Clínicos por IA

## 🎯 Como Funciona

O sistema gera resumos clínicos inteligentes que ajudam profissionais de saúde a tomar **decisões assertivas**.

---

## 📡 Endpoint da API

```http
GET /api/v1/ai/summary/{patient_id}/
```

**Autenticação**: Keycloak (Bearer Token)  
**Cache**: 5 minutos (Redis)  
**Timeout**: 30 segundos

### Exemplo de Uso:

```bash
curl -H "Authorization: Bearer {token}" \
  https://api.example.com/api/v1/ai/summary/123e4567-e89b-12d3-a456-426614174000/
```

---

## 🧠 Tecnologia

### Modelo LLM:

- **BioMistral 7B** (GGUF) - Modelo médico especializado
- **Fallback Inteligente**: Sistema baseado em regras clínicas se LLM não disponível

### Dados Utilizados:

```python
✅ Patient (demografa: nome, idade, sexo)
✅ Condition (diagnósticos ativos e históricos)
✅ MedicationRequest (medicações ativas)
✅ Observation (sinais vitais - últimos 15 registros)
```

### Dados Planejados (Roadmap):

```python
⏳ AllergyIntolerance (alergias e reações adversas)
⏳ DiagnosticReport (resultados de exames laboratoriais)
⏳ Procedure (procedimentos realizados)
⏳ Immunization (vacinações)
```

---

## 📋 Estrutura do Resumo

### 1. **Resumo Executivo** 🎯

- Complexidade clínica (BAIXA/MODERADA/ALTA)
- Principais condições ativas
- Número de alertas clínicos

**Exemplo**:

```
🎯 RESUMO EXECUTIVO
Paciente com complexidade clínica ALTA.
Principais condições ativas: Diabetes, Hipertensão, IC.
🚨 3 alerta(s) clínico(s) - verificar seção de alertas.
```

### 2. **Alertas Clínicos** 🚨

- Múltiplas comorbidades (≥3)
- Polifarmácia (≥5 medicamentos)
- Sinais vitais críticos
- Dados faltantes

**Exemplo**:

```
🚨 ALERTAS CLÍNICOS
⚠️ Paciente com 5 comorbidades ativas
⚠️ Polifarmácia: revisar interações medicamentosas
🔴 PA Sistólica: 185 mmHg - Hipertensão Estágio 3
```

### 3. **Perfil do Paciente** 📋

- Nome, idade, sexo

### 4. **Sinais Vitais** 💓

- Últimos valores registrados
- Status visual (✅ Normal, ⚠️ Atenção, 🔴 Crítico)
- Interpretação clínica automatizada

**Exemplo**:

```
💓 SINAIS VITAIS
• ✅ FC: 75 bpm - Normal
• ⚠️ PA Sistólica: 145 mmHg - Hipertensão Estágio 1
• 🔴 SpO2: 88% - Hipoxemia moderada
```

### 5. **Condições Clínicas** 🩺

- Número de diagnósticos
- Condições ativas destacadas
- Alertas de comorbidades

### 6. **Medicamentos** 💊

- Lista de medicamentos ativos
- Contagem total
- Alerta de polifarmácia

### 7. **Recomendações Clínicas** 📌

- Específicas por condição (baseadas em guidelines)
- Rastreamento preventivo (idade/gênero)
- Próximos passos sugeridos
- Dados faltantes identificados

**Exemplos**:

```
📌 RECOMENDAÇÕES CLÍNICAS
• DIABETES: Verificar última HbA1c (meta <7%)
• HIPERTENSÃO: PA meta <140/90 mmHg, ajustar medicação
• RASTREAMENTO: Mamografia anual (≥40 anos)
• ⚠️ DADOS INCOMPLETOS: Registrar alergias conhecidas
```

---

## 🎨 Frontend (AICopilot Component)

### Localização:

```
frontend-pwa/src/components/clinical/AICopilot.tsx
```

### Uso:

```tsx
import AICopilot from "@/components/clinical/AICopilot";

<AICopilot patientId={patientId} />;
```

### Features:

- Loading state com spinner
- Error handling amigável
- Renderização Markdown
- Atualização automática

---

## 📊 Interpretação de Sinais Vitais

### Faixas de Referência (Adultos):

| Sinal Vital   | Normal      | Atenção     | Crítico     |
| ------------- | ----------- | ----------- | ----------- |
| **FC**        | 60-100 bpm  | <60 ou >100 | <50 ou >120 |
| **PA Sist.**  | 90-140 mmHg | >140        | >180        |
| **PA Diast.** | 60-90 mmHg  | >90         | >110        |
| **Temp.**     | 36-37.5°C   | >37.5       | >38.5       |
| **SpO2**      | ≥95%        | 90-94%      | <90%        |
| **FR**        | 12-20 irpm  | <12 ou >20  | <10 ou >24  |

---

## ⚙️ Configuração

### Variáveis de Ambiente:

```bash
# Model Path (BioMistral GGUF)
AI_MODEL_PATH=/path/to/biomistral-7b.gguf

# Cache Settings
REDIS_URL=redis://localhost:6379
AI_SUMMARY_CACHE_TTL=300  # 5 minutos

# Timeout
AI_SUMMARY_TIMEOUT=30  # segundos
```

### Django Settings:

```python
# openehrcore/settings.py

AI_SERVICE = {
    'MODEL_PATH': env('AI_MODEL_PATH', default=None),
    'CACHE_TTL': 300,
    'TIMEOUT': 30,
    'USE_FALLBACK': True,  # Usar fallback se LLM falhar
}
```

---

## 🔒 Segurança e Privacidade

### Autenticação:

- ✅ Keycloak Bearer Token obrigatório
- ✅ Validação de UUID do paciente
- ✅ Logs sanitizados (sem PHI em logs)

### Prevenção de Viés:

```python
Guardrails Implementados:
✅ NÃO fazer generalizações por raça/etnia
✅ NÃO considerar condição socioeconômica
✅ Recomendações SOMENTE baseadas em evidências clínicas
```

### Cache:

- TTL: 5 minutos (dados clínicos mudam frequentemente)
- Chave: `ai_summary:patient:{uuid}`
- Backend: Redis

---

## 🧪 Testes

### Executar Testes de Acurácia:

```bash
cd backend-django
python -m pytest tests/test_ai_summary_accuracy.py -v
```

**Cobertura**: 9 cenários clínicos validados ✅

### Demonstração Interativa:

```bash
python scripts/demo_ai_summary_improvements.py
```

Mostra 4 casos clínicos com resumos completos.

---

## 📈 Métricas de Qualidade

### KPIs Implementados:

1. **Completude**: Todas as seções sempre presentes
2. **Acurácia**: Faixas de referência validadas clinicamente
3. **Relevância**: Recomendações específicas por condição
4. **Segurança**: Alertas de riscos destacados
5. **Prevenção**: Rastreamento por idade/gênero

### Benchmarks:

| Métrica               | Antes      | Depois       | Ganho |
| --------------------- | ---------- | ------------ | ----- |
| Tamanho médio         | 3-5 linhas | 15-30 linhas | +400% |
| Seções estruturadas   | 0          | 7            | +700% |
| Alertas automatizados | 0          | 6 tipos      | ∞     |
| Recomendações         | Genéricas  | Específicas  | ✅    |
| Taxa de aprovação     | -          | 100% (9/9)   | ✅    |

---

## 🐛 Troubleshooting

### Problema: "Não foi possível gerar resumo"

**Soluções**:

1. Verificar se BioMistral está instalado: `ls $AI_MODEL_PATH`
2. Checar logs: `tail -f logs/ai_service.log`
3. Testar fallback: `USE_FALLBACK=True` (sempre funciona)

### Problema: "Timeout"

**Soluções**:

1. Aumentar timeout: `AI_SUMMARY_TIMEOUT=60`
2. Verificar performance do LLM (GPU disponível?)
3. Usar fallback temporariamente

### Problema: "Resumo muito genérico"

**Soluções**:

1. Verificar se dados FHIR estão completos
2. Adicionar mais observations: `_count=20`
3. Checar qualidade dos diagnósticos registrados

---

## 📞 Suporte

### Documentação Completa:

- [AI_SUMMARY_VALIDATION.md](./AI_SUMMARY_VALIDATION.md) - Validação clínica completa
- [FHIR_R4_COMPLIANCE.md](./FHIR_R4_COMPLIANCE.md) - Conformidade FHIR

### Código:

- Backend: `fhir_api/services/ai_service.py`
- View: `fhir_api/views_ai.py`
- Frontend: `frontend-pwa/src/components/clinical/AICopilot.tsx`
- Testes: `tests/test_ai_summary_accuracy.py`

### Logs:

```bash
# Django logs
tail -f logs/django.log

# AI Service logs
tail -f logs/ai_service.log
```

---

## ✅ Checklist Pré-Produção

- [x] LLM testado e funcional
- [x] Fallback implementado e validado
- [x] Testes automatizados (9/9 ✅)
- [x] Faixas de referência validadas
- [x] Guidelines clínicos implementados
- [x] Prevenção de viés ativa
- [x] Cache configurado
- [x] Timeout adequado
- [x] Autenticação obrigatória
- [x] Logs sanitizados
- [x] Frontend integrado
- [x] Documentação completa

---

**Versão**: 2.0  
**Última Atualização**: 2024  
**Status**: ✅ Produção-Ready
