# 🧠 Documentação de IA Multimodal (v2.2.0)

O **OpenEHRCore** v2.2.0 introduz uma poderosa camada de inteligência multimodal, centralizada no backend para garantir segurança, performance e consistência.

## 🌟 Visão Geral

A nova arquitetura **HealthStack AI** remove a dependência de processamento no cliente (navegador), movendo a inteligência para serviços dedicados no servidor.

| Recurso | Modelo de IA | Provedor | Função |
|---|---|---|---|
| **Visão Computacional** | **MedGemma 1.5** | Ollama (Local) | Análise de imagens médicas (RX, CT, MR), detecção de anomalias e laudos. |
| **Reconhecimento de Voz** | **Google MedASR** | Hugging Face | Transcrição de áudio clínico em tempo real com vocabulário médico especializado. |
| **Resumo Clínico** | MedGemma / Mistral | Backend Core | Geração de sumários de pacientes, SOAP notes e refinamento de texto. |

---

## 📸 Análise de Imagem (MedicalVisionService)

Processa imagens enviadas via API para extrair insights clínicos.

- **Endpoint:** `POST /api/ai/analyze-image/`
- **Segurança:** Autenticação Token/JWT Exigida.
- **Fluxo:**
  1. Upload da imagem (multipart/form-data).
  2. Pré-processamento e redimensionamento seguro.
  3. Inferência no modelo `medgemma` rodando no container Ollama.
  4. Retorno estruturado com achados clínicos.

### Exemplo de Uso (Frontend)

```typescript
const formData = new FormData();
formData.append('image', file);
formData.append('prompt', 'Descreva achados patológicos nesta radiografia de tórax.');

const response = await api.post('/ai/analyze-image/', formData);
console.log(response.data.analysis);
```

---

## 🎙️ Transcrição de Voz (MedicalVoiceService)

Converte áudio do médico (ditado ou consulta) em texto clínico estruturado.

- **Endpoint:** `POST /api/ai/transcribe/`
- **Modelos:**
  - Primário: `google/medasr` (Especializado)
  - Fallback: `openai/whisper-tiny` (Rápido/Generalista)
- **Funcionalidades:**
  - Suporte a `.wav`, `.mp3`, `.ogg`, `.webm`.
  - Refinamento automático de texto (correção gramatical e terminológica).

### Exemplo de Uso (Frontend)

Utilize o componente `AudioRecorder.tsx` que já integra a lógica de gravação e envio.

---

## 🧠 Resumo Inteligente (Migração Backend)

O antigo "Copiloto" que rodava no navegador agora é um serviço de backend robusto.

- **Endpoint:** `GET /api/ai/summary/{patient_id}/`
- **Vantagens:**
  - **Zero Configuração:** O usuário não precisa instalar Ollama localmente.
  - **Segurança:** Dados do paciente não saem do ambiente seguro do servidor para LLMs públicas.
  - **Consistência:** Todos os usuários acessam o mesmo modelo calibrado.

---

## ⚙️ Configuração (DevOps)

As configurações de IA são controladas via variáveis de ambiente no `settings.py` ou `.env`:

```python
# Backend AI Configuration
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "yenjia/medgemma-1.5-4b-it"
HF_CACHE_DIR = "/var/www/openehrcore/model_cache"
```

Certifique-se de que o serviço Ollama está rodando e o modelo foi baixado (`ollama pull yenjia/medgemma-1.5-4b-it`).
