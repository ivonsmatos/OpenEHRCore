# 🤖 Automações (Bots)

O módulo de Automações do OpenEHRCore permite criar fluxos de trabalho automatizados que executam em resposta a eventos do sistema. Estes "bots" são funções serverless que processam dados FHIR e podem enviar notificações, criar recursos, ou integrar com sistemas externos.

---

## Tipos de Gatilhos

| Gatilho | Descrição |
|---------|-----------|
| `resource-create` | Executa quando um recurso FHIR é criado |
| `resource-update` | Executa quando um recurso FHIR é atualizado |
| `resource-delete` | Executa quando um recurso FHIR é excluído |
| `schedule` | Executa em horários programados (cron) |
| `webhook` | Executa quando recebe requisição externa |
| `manual` | Executa apenas quando acionado manualmente |

---

## Bots Pré-configurados

### 1. 🎉 Welcome Patient

**Objetivo:** Envia uma mensagem de boas-vindas quando um novo paciente é cadastrado no sistema.

| Propriedade | Valor |
|-------------|-------|
| **ID** | `welcome-patient` |
| **Gatilho** | `resource-create` |
| **Recurso** | `Patient` |
| **Ação** | Envia notificação ao Mattermost |

**O que faz:**

1. Detecta quando um novo recurso `Patient` é criado no HAPI FHIR
2. Extrai o nome do paciente do recurso
3. Envia mensagem para o canal configurado: "🎉 Novo paciente cadastrado: [Nome]"

**Código:**

```python
def execute(ctx):
    patient = ctx.trigger_data.get('resource', {})
    name = patient.get('name', [{}])[0].get('given', [''])[0]
    ctx.log(f"New patient registered: {name}")
    ctx.send_notification('mattermost', f"🎉 Novo paciente cadastrado: {name}")
    return {"status": "welcomed", "patient": name}
```

---

### 2. ⚠️ Critical Vital Signs Alert

**Objetivo:** Alerta a equipe médica quando sinais vitais estão fora da faixa normal, indicando possível urgência.

| Propriedade | Valor |
|-------------|-------|
| **ID** | `critical-vital-alert` |
| **Gatilho** | `resource-create` |
| **Recurso** | `Observation` (categoria: vital-signs) |
| **Ação** | Envia alerta ao Mattermost |

**Limites Críticos Monitorados:**

| Sinal Vital | Código LOINC | Alerta se... |
|-------------|--------------|--------------|
| Frequência Cardíaca | `8867-4` | < 50 bpm OU > 120 bpm |
| Pressão Sistólica | `8480-6` | > 180 mmHg |
| Temperatura | `8310-5` | > 39°C |

**O que faz:**

1. Detecta criação de nova observação de sinais vitais
2. Verifica se o valor está fora dos limites normais
3. Se crítico, envia alerta imediato:
   - "⚠️ Frequência cardíaca crítica: 135 bpm"
   - "🚨 Pressão sistólica muito alta: 190 mmHg"
   - "🌡️ Febre alta: 39.5°C"

**Código:**

```python
def execute(ctx):
    obs = ctx.trigger_data.get('resource', {})
    code = obs.get('code', {}).get('coding', [{}])[0].get('code', '')
    value = obs.get('valueQuantity', {}).get('value', 0)
    
    alerts = []
    if code == '8867-4' and (value > 120 or value < 50):  # Heart rate
        alerts.append(f"⚠️ Frequência cardíaca crítica: {value} bpm")
    if code == '8480-6' and value > 180:  # Systolic BP
        alerts.append(f"🚨 Pressão sistólica muito alta: {value} mmHg")
    if code == '8310-5' and value > 39:  # Temperature
        alerts.append(f"🌡️ Febre alta: {value}°C")
    
    if alerts:
        ctx.send_notification('mattermost', '\n'.join(alerts))
    return {"alerts": alerts}
```

---

### 3. 📊 Daily Clinical Summary

**Objetivo:** Gera um resumo diário das atividades clínicas para gestão hospitalar.

| Propriedade | Valor |
|-------------|-------|
| **ID** | `daily-summary` |
| **Gatilho** | `schedule` |
| **Agendamento** | Diariamente às 18:00 |
| **Ação** | Gera relatório e envia ao Mattermost |

**O que faz:**

1. Executa automaticamente às 18h todos os dias
2. Busca todos os Encounters (atendimentos) do dia
3. Conta o total de atendimentos realizados
4. Envia resumo para o canal:
   - "📊 Resumo do dia 2026-01-13"
   - "Total de atendimentos: 45"

**Código:**

```python
def execute(ctx):
    from datetime import datetime
    today = datetime.now().strftime('%Y-%m-%d')
    
    encounters = ctx.search_resources('Encounter', {
        'date': f'ge{today}',
        '_count': '100'
    })
    
    summary = f"📊 Resumo do dia {today}\n"
    summary += f"Total de atendimentos: {len(encounters)}\n"
    
    ctx.send_notification('mattermost', summary)
    return {"date": today, "encounters_count": len(encounters)}
```

---

### 4. 🔬 Lab Result Notifier

**Objetivo:** Notifica a equipe quando novos resultados de exames laboratoriais estão disponíveis.

| Propriedade | Valor |
|-------------|-------|
| **ID** | `lab-result-notifier` |
| **Gatilho** | `resource-create` |
| **Recurso** | `DiagnosticReport` |
| **Ação** | Envia notificação ao Mattermost |

**O que faz:**

1. Detecta quando um novo relatório diagnóstico é criado
2. Verifica se o status é "final" (resultado concluído)
3. Envia notificação:
   - "🔬 Novo resultado de exame disponível para Patient/123"

**Código:**

```python
def execute(ctx):
    report = ctx.trigger_data.get('resource', {})
    patient_ref = report.get('subject', {}).get('reference', '')
    status = report.get('status', 'final')
    
    if status == 'final':
        ctx.send_notification('mattermost', 
            f"🔬 Novo resultado de exame disponível para {patient_ref}")
    return {"patient": patient_ref, "status": status}
```

---

## API de Automações

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/api/v1/bots/` | GET | Lista todos os bots |
| `/api/v1/bots/{id}/` | GET | Detalhes de um bot |
| `/api/v1/bots/{id}/` | PUT | Atualiza um bot |
| `/api/v1/bots/{id}/execute/` | POST | Executa um bot manualmente |
| `/api/v1/bots/history/` | GET | Histórico de execuções |
| `/api/v1/bots/{id}/history/` | GET | Histórico de um bot específico |

---

## Contexto de Execução

Durante a execução, cada bot tem acesso a um contexto (`ctx`) com os seguintes métodos:

| Método | Descrição |
|--------|-----------|
| `ctx.log(message)` | Registra mensagem no log |
| `ctx.send_notification(channel, message)` | Envia notificação |
| `ctx.create_resource(type, data)` | Cria recurso FHIR |
| `ctx.search_resources(type, params)` | Busca recursos FHIR |
| `ctx.update_resource(type, id, data)` | Atualiza recurso FHIR |
| `ctx.generate_ai_summary(data)` | Gera resumo com IA |

---

## Status dos Bots

| Status | Descrição |
|--------|-----------|
| `idle` | Bot aguardando gatilho |
| `running` | Bot em execução |
| `completed` | Última execução bem-sucedida |
| `failed` | Última execução falhou |
| `disabled` | Bot desabilitado |

---

## Segurança

- Bots executam em sandbox isolado
- Apenas funções seguras disponíveis (len, str, int, float, etc.)
- Sem acesso a sistema de arquivos ou rede direta
- Logs de todas as execuções são armazenados
