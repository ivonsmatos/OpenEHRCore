# Documentação OpenEHRCore

Bem-vindo à documentação completa do sistema OpenEHRCore - Plataforma de Saúde Digital com IA e conformidade FHIR R4.

---

## 📚 Índice de Documentação

### 🎯 **IA e Suporte à Decisão Clínica**

1. **[AI_IMPROVEMENTS_SUMMARY.md](./AI_IMPROVEMENTS_SUMMARY.md)** ⭐ **COMECE AQUI**

   - Resumo executivo das melhorias implementadas
   - Comparação antes vs. depois
   - Checklist de qualidade
   - **Leitura**: 5 minutos

2. **[AI_SUMMARY_VALIDATION.md](./AI_SUMMARY_VALIDATION.md)** 📊 **VALIDAÇÃO COMPLETA**

   - Validação clínica detalhada
   - Faixas de referência médicas
   - Testes automatizados
   - Impacto na decisão clínica
   - **Leitura**: 15 minutos

3. **[AI_SUMMARY_QUICK_GUIDE.md](./AI_SUMMARY_QUICK_GUIDE.md)** ⚡ **GUIA PRÁTICO**
   - Como usar a API
   - Configuração
   - Troubleshooting
   - Exemplos de código
   - **Leitura**: 10 minutos

---

### 🏥 **FHIR R4 e Interoperabilidade**

4. **[FHIR_R4_COMPLIANCE.md](./FHIR_R4_COMPLIANCE.md)** 📋 **CONFORMIDADE**
   - Recursos FHIR implementados
   - Testes de integração
   - Validação de conformidade
   - Exemplos de uso

---

### 📁 **Estrutura do Projeto**

5. **[PROJECT_STRUCTURE.md](./PROJECT_STRUCTURE.md)** 🗂️ **ORGANIZAÇÃO**
   - Árvore de diretórios
   - Descrição de cada pasta
   - Localização de arquivos importantes
   - Convenções de nomenclatura

---

## 🚀 Início Rápido

### Para Desenvolvedores:

1. Leia [AI_IMPROVEMENTS_SUMMARY.md](./AI_IMPROVEMENTS_SUMMARY.md) - 5 min
2. Execute os testes: `pytest tests/test_ai_summary_accuracy.py -v`
3. Veja a demo: `python scripts/demo_ai_summary_improvements.py`

### Para Profissionais de Saúde:

1. Leia [AI_SUMMARY_QUICK_GUIDE.md](./AI_SUMMARY_QUICK_GUIDE.md) - 10 min
2. Acesse o sistema: `http://localhost:5173`
3. Navegue até um paciente para ver o resumo clínico

### Para Validação Clínica:

1. Leia [AI_SUMMARY_VALIDATION.md](./AI_SUMMARY_VALIDATION.md) - 15 min
2. Revise as faixas de referência médicas
3. Valide as recomendações baseadas em guidelines

---

## 🎯 Principais Features Documentadas

### ✅ Sistema de IA para Resumos Clínicos

- **Modelo**: BioMistral 7B (LLM médico especializado)
- **Fallback**: Sistema inteligente baseado em regras clínicas
- **Dados**: Patient, Condition, MedicationRequest, Observation
- **Saída**: Resumo estruturado com 7 seções + alertas
- **Acurácia**: 100% nos testes (9/9 ✅)

### ✅ Análise de Sinais Vitais

- **6 tipos**: FC, PA, Temperatura, SpO2, FR
- **Faixas**: Normal, Atenção, Crítico
- **Alertas**: Visuais (✅ ⚠️ 🔴)
- **Interpretação**: Automática com ação clínica sugerida

### ✅ Alertas Clínicos Automatizados

- **Comorbidades**: ≥3 condições ativas
- **Polifarmácia**: ≥5 medicamentos (alerta), ≥8 (crítico)
- **Sinais Vitais**: Fora de faixa normal/crítica
- **Dados Faltantes**: Informações críticas ausentes

### ✅ Recomendações Baseadas em Evidências

- **Por Condição**: Diabetes, Hipertensão, IC, DRC
- **Preventivas**: Colonoscopia, Mamografia, Vacinas
- **Guidelines**: Metas terapêuticas específicas

---

## 📊 Métricas de Qualidade

| Métrica                       | Valor    | Status  |
| ----------------------------- | -------- | ------- |
| **Testes Automatizados**      | 9/9      | ✅ 100% |
| **Seções Estruturadas**       | 7        | ✅      |
| **Tipos de Alertas**          | 6        | ✅      |
| **Sinais Vitais Analisados**  | 6        | ✅      |
| **Condições com Guidelines**  | 4+       | ✅      |
| **Rastreamentos Preventivos** | 3+       | ✅      |
| **Prevenção de Viés**         | Ativa    | ✅      |
| **Documentação**              | Completa | ✅      |

---

## 🛠️ Arquivos de Código Relacionados

### Backend (Django):

```
backend-django/
├── fhir_api/
│   ├── services/
│   │   ├── ai_service.py              # ⭐ Serviço principal de IA
│   │   └── bias_prevention_service.py # Prevenção de viés
│   └── views_ai.py                    # Endpoint da API
├── tests/
│   └── test_ai_summary_accuracy.py    # Testes de acurácia
└── scripts/
    └── demo_ai_summary_improvements.py # Demonstração
```

### Frontend (React):

```
frontend-pwa/
└── src/
    └── components/
        └── clinical/
            └── AICopilot.tsx          # Componente de exibição
```

---

## 🔗 Links Úteis

### Documentação Externa:

- [FHIR R4 Specification](https://hl7.org/fhir/R4/)
- [BioMistral Model](https://huggingface.co/BioMistral/BioMistral-7B)
- [Django Documentation](https://docs.djangoproject.com/)
- [React Documentation](https://react.dev/)

### Repositórios:

- **Backend**: `backend-django/`
- **Frontend**: `frontend-pwa/`
- **Testes**: `backend-django/tests/`
- **Docs**: `docs/` (você está aqui)

---

## 📝 Changelog

### v2.0 (Atual) - Melhorias em IA

- ✅ Prompt reformulado para suporte à decisão clínica
- ✅ Sistema fallback aprimorado com análise completa
- ✅ Faixas de referência médicas implementadas
- ✅ 6 tipos de alertas automatizados
- ✅ Recomendações específicas por condição
- ✅ Rastreamento preventivo por idade/gênero
- ✅ 9 testes de acurácia (100% aprovação)
- ✅ Documentação completa

### v1.0 - Release Inicial

- ✅ Sistema FHIR R4 básico
- ✅ Recursos: Patient, Condition, Medication, Observation
- ✅ Frontend PWA com React
- ✅ Backend Django + PostgreSQL
- ✅ Autenticação Keycloak

---

## 🤝 Contribuindo

### Reportar Problemas:

1. Verifique a documentação relevante
2. Execute os testes automatizados
3. Crie um issue detalhado

### Adicionar Features:

1. Leia a documentação do módulo
2. Escreva testes primeiro (TDD)
3. Implemente a feature
4. Atualize a documentação
5. Submeta pull request

---

## 📞 Suporte

### Documentação:

- Leia os guias acima conforme sua necessidade

### Logs:

```bash
# Backend
tail -f backend-django/logs/django.log

# IA Service
tail -f backend-django/logs/ai_service.log
```

### Testes:

```bash
# Todos os testes
pytest

# Apenas IA
pytest tests/test_ai_summary_accuracy.py -v

# Com coverage
pytest --cov=fhir_api
```

---

## ✅ Checklist de Deploy

Antes de colocar em produção:

- [ ] Ler [AI_SUMMARY_VALIDATION.md](./AI_SUMMARY_VALIDATION.md)
- [ ] Executar todos os testes (`pytest -v`)
- [ ] Configurar variáveis de ambiente
- [ ] Verificar modelo BioMistral instalado
- [ ] Configurar Redis (cache)
- [ ] Configurar Keycloak (autenticação)
- [ ] Revisar faixas de referência médicas
- [ ] Validar guidelines clínicos
- [ ] Testar em ambiente de staging
- [ ] Monitorar logs em produção

---

**Versão**: 2.0  
**Última Atualização**: 2025  
**Status**: ✅ Produção-Ready

---

_Esta documentação é mantida pela equipe OpenEHRCore e está em constante evolução._
