# IA open-source, self-hosted e conforme LGPD — guia de arquitetura

> Decisão: a IA do OpenEHRCore é **apoio à decisão** (o profissional decide) e roda
> **no ambiente controlado** (Brasil/on-prem) via servidor **compatível com a API
> da OpenAI**. Assim os dados de saúde **não saem** do ambiente — eliminando a
> transferência internacional (Art. 33 da LGPD) e maximizando a conformidade.
>
> ⚠️ Este documento é orientação técnica, **não parecer jurídico**. Valide com o DPO/jurídico e faça um RIPD antes de produção com dados reais.

## Por que open-source self-hosted (e não API externa)

| Critério | API externa (ex.: Groq/OpenAI, EUA) | **Self-hosted no Brasil (escolhido)** |
|---|---|---|
| Transferência internacional (Art. 33) | Exige cláusulas-padrão/salvaguardas | **Não ocorre** |
| Controle do dado | Depende de contrato do fornecedor | **Total** |
| "Treina nos seus dados" | Precisa garantir opt-out contratual | **Não há** |
| Custo recorrente por token | Sim | Não (custo de GPU) |
| Latência/disponibilidade | Depende de terceiro | Sob seu controle |

## Stack recomendada

| Camada | Recomendação | Licença/observação |
|---|---|---|
| **Servir LLM** | **vLLM** (produção) — expõe `/v1/chat/completions` | OpenAI-compatible; alta vazão |
| **LLM (geração)** | **Qwen2.5-32B-Instruct** ou **Llama 3.3 70B** | Qwen = Apache 2.0 (mais limpa); forte em PT-BR |
| **Dev local** | **Ollama** + `qwen2.5:7b-instruct` | troca só por `LLM_BASE_URL` |
| **Visão** | modelo multimodal (`qwen2.5vl`) — laudo de imagem como apoio | médico interpreta |
| **ASR (voz)** | **faster-whisper-server** / whisper.cpp (`/v1/audio/transcriptions`) | self-hosted |
| **RAG** | **pgvector** (Postgres) + embeddings **BGE-m3** + citação de fonte | fundamenta nas suas fontes |

> **Cuidado com LLMs "médicos" prontos** (Meditron, OpenBioLLM, BioMistral): muitos têm licença
> *"research only / not for clinical use"*. Em produção clínica, prefira um **modelo geral forte +
> RAG nos seus manuais validados** + decisão do profissional.

## Como o código está organizado

- **`core/services/llm_client.py`** — cliente único compatível com OpenAI:
  - `chat(messages, ...)` → geração de texto
  - `transcribe(file)` → transcrição de áudio
  - `redact_pii(text)` → remove CPF/CNPJ/CNS/telefone/email/CEP **antes** do envio
  - `DEFAULT_CLINICAL_SYSTEM` → prompt que impõe "apoio à decisão, cite fontes, não invente"
- Serviços que usam o cliente: `ai_service.py` (resumo), `ai_summary_service.py`,
  `ai_vision_service.py` (visão), `ai_voice_service.py` (voz), `clinical_parser_service.py` (NLP→FHIR).
- Troca de provedor/modelo é **só configuração** (`.env`): `LLM_BASE_URL`, `LLM_MODEL`, `ASR_BASE_URL`.

## RAG do manual clínico (próximo passo)

1. **Ingestão**: dividir os manuais em trechos (chunks) com metadados (fonte, seção, versão).
2. **Embeddings**: gerar vetores com **BGE-m3** (multilíngue, forte em PT).
3. **Armazenar**: tabela com **pgvector** no Postgres.
4. **Consulta**: recuperar top-k trechos relevantes → injetar no prompt → o LLM responde
   **citando a fonte** (página/seção). Sempre como apoio; o profissional decide.
5. **Guardrails**: se não houver fonte suficiente, responder "sem evidência no manual".

## Checklist de conformidade (resumo)

- [x] Modelo roda no ambiente controlado (sem transferência internacional)
- [x] PII redigida antes do envio ao modelo (`redact_pii`)
- [x] Prompt de sistema: IA é apoio à decisão (CFM) — não diagnostica/prescreve sozinha
- [ ] Contrato de operador com as clínicas (controlador) e RIPD do uso de IA
- [ ] Auditoria de cada inferência (quem, quando, sobre qual paciente) no audit log
- [ ] Se a IA influenciar diagnóstico/terapêutica → avaliar enquadramento ANVISA (SaMD, RDC 657/2022)
- [ ] Transparência/base legal (Art. 7º/11) para o paciente

## vLLM em produção (Brasil / GPU)

**Princípio LGPD:** a GPU/instância deve ficar **no Brasil** (ou on-prem no hospital)
para o dado não sair do ambiente controlado.

### Onde hospedar (região BR)
- **AWS** `sa-east-1` (São Paulo): G5/G6 (A10G/L4 24 GB), p4d/p5 (A100/H100)
- **Azure** *Brazil South*: séries NC (T4/A100)
- **On-prem** no datacenter do hospital
- Provedores nacionais (ex.: Magalu Cloud)

### GPU por modelo (estimativa)
| Modelo | Quantização | GPU mínima |
|--------|-------------|------------|
| Qwen2.5-7B / 14B (dev/leve) | — / AWQ | 1× L4/A10G 24 GB |
| **Qwen2.5-32B-Instruct** | AWQ 4-bit | 1× A100 40 GB (ou 2× L4) |
| **Llama 3.3 70B** | AWQ 4-bit | 1× A100 80 GB / 1× H100 |

### Subir o vLLM (OpenAI-compatible)
```bash
docker run --gpus all -p 8000:8000 \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  --ipc=host vllm/vllm-openai:latest \
  --model Qwen/Qwen2.5-32B-Instruct-AWQ \
  --quantization awq --max-model-len 8192 \
  --served-model-name qwen2.5-32b \
  --api-key SUA_CHAVE_INTERNA
```

### Embeddings (RAG) e ASR (voz)
```bash
# embeddings (bge-m3)
docker run --gpus all -p 8001:8000 vllm/vllm-openai:latest \
  --model BAAI/bge-m3 --served-model-name bge-m3 --task embed
# transcrição de voz
docker run --gpus all -p 8002:8000 fedirz/faster-whisper-server:latest-cuda
```

### .env de produção (backend aponta para o vLLM)
```env
LLM_BASE_URL=http://<ip-gpu>:8000/v1
LLM_MODEL=qwen2.5-32b
LLM_API_KEY=SUA_CHAVE_INTERNA
EMBEDDINGS_MODEL=bge-m3
ASR_BASE_URL=http://<ip-asr>:8002/v1
RAG_ENABLED=True
```

### Segurança
- vLLM em **rede privada/VPC**, nunca exposto publicamente; TLS via nginx.
- Proteja com `--api-key` (igual em `LLM_API_KEY`).
- Licenças: **Qwen = Apache 2.0** (mais limpa); Llama = community license.

## Variáveis de ambiente

```env
LLM_BASE_URL=http://localhost:11434/v1     # Ollama (dev) / http://vllm:8000/v1 (prod)
LLM_MODEL=qwen2.5:7b-instruct              # prod: llama3.3:70b ou qwen2.5:32b-instruct
LLM_VISION_MODEL=qwen2.5vl:7b
LLM_API_KEY=                               # se o endpoint exigir
ASR_BASE_URL=http://localhost:8001/v1      # faster-whisper-server
ASR_MODEL=Systran/faster-whisper-large-v3
RAG_ENABLED=False
EMBEDDINGS_MODEL=BAAI/bge-m3
```
