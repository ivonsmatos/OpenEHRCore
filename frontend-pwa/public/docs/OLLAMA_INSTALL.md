# Guia de Instalação: Ollama + IA Médica

## 📋 O que é Ollama?

Ollama é uma plataforma que permite rodar modelos de IA (LLMs) localmente no seu computador, **sem enviar dados para nuvem**. Ideal para sistemas de saúde que precisam cumprir LGPD e manter privacidade total dos pacientes.

## 🔒 Segurança e Privacidade

- ✅ **100% Local**: Dados nunca saem do servidor
- ✅ **LGPD Compliant**: Sem transferência internacional
- ✅ **HL7 FHIR**: Compatível com padrões de saúde
- ✅ **Open Source**: Código auditável

## 🚀 Instalação no Windows

### Passo 1: Baixar Ollama

1. Acesse: https://ollama.ai/download
2. Clique em "Download for Windows"
3. Execute o instalador `OllamaSetup.exe`
4. Siga os passos da instalação (Next → Install → Finish)

### Passo 2: Verificar Instalação

Abra **PowerShell** ou **Terminal** e execute:

```powershell
ollama --version
```

Deve retornar algo como: `ollama version 0.1.x`

### Passo 3: Instalar Modelo de IA

Escolha **UM** dos modelos abaixo:

#### Opção 1: Mistral (Recomendado para uso geral)

```powershell
ollama pull mistral
```

- **Tamanho**: ~4GB
- **Velocidade**: Rápido
- **Qualidade**: Muito boa para resumos clínicos

#### Opção 2: Medllama2 (Especializado em medicina)

```powershell
ollama pull medllama2
```

- **Tamanho**: ~3.8GB
- **Velocidade**: Rápido
- **Qualidade**: Otimizado para textos médicos

#### Opção 3: Llama 3.2 (Mais avançado)

```powershell
ollama pull llama3.2
```

- **Tamanho**: ~2GB
- **Velocidade**: Muito rápido
- **Qualidade**: Excelente

**Aguarde o download** (pode levar 5-15 minutos dependendo da internet).

### Passo 4: Verificar Modelos Instalados

```powershell
ollama list
```

Deve mostrar o modelo que você baixou:

```
NAME              ID              SIZE      MODIFIED
mistral:latest    abc123...       4.1 GB    2 minutes ago
```

### Passo 5: Iniciar Ollama (Automático no Windows)

Ollama inicia automaticamente após a instalação. Para verificar:

1. Abra **Gerenciador de Tarefas** (Ctrl+Shift+Esc)
2. Procure por "ollama" nos processos em segundo plano
3. Ou verifique a bandeja do sistema (ícone de lhama 🦙)

**Caso não esteja rodando**, execute:

```powershell
ollama serve
```

### Passo 6: Testar Conexão

No PowerShell:

```powershell
curl http://localhost:11434/api/tags
```

Deve retornar JSON com a lista de modelos:

```json
{"models":[{"name":"mistral:latest",...}]}
```

## ⚙️ Configuração no OpenEHRCore

### Configurar Modelo no Backend

Edite `backend-django/openehrcore/settings.py` e adicione:

```python
# AI Configuration (Ollama)
OLLAMA_BASE_URL = 'http://localhost:11434'
OLLAMA_MODEL = 'mistral'  # ou 'medllama2' ou 'llama3.2'
```

### Reiniciar Django

```powershell
cd backend-django
python manage.py runserver
```

### Testar Resumo de IA

1. Acesse o sistema: http://localhost:5173
2. Abra um paciente
3. O resumo de IA aparecerá no topo com indicador "Ollama Ativo" 🟢

## 🧪 Teste Manual via API

```powershell
$headers = @{ 'Authorization' = 'Bearer dev-token-bypass' }
Invoke-RestMethod http://localhost:8000/api/v1/ai/summary/860/ -Headers $headers | Select-Object -ExpandProperty summary
```

Deve retornar um resumo clínico gerado por IA.

## ❗ Solução de Problemas

### "Ollama não conectou"

**Causa**: Ollama não está rodando.

**Solução**:

1. Abra o aplicativo Ollama (ícone de lhama na bandeja)
2. Ou execute: `ollama serve`

### "Modelo 'mistral' não encontrado"

**Causa**: Modelo não foi baixado.

**Solução**:

```powershell
ollama pull mistral
ollama list  # Verificar se aparece
```

### "Timeout ao gerar resumo"

**Causa**: Modelo muito grande para CPU.

**Solução**: Use um modelo menor:

```powershell
ollama pull llama3.2  # Apenas 2GB, mais rápido
```

E atualize `settings.py`:

```python
OLLAMA_MODEL = 'llama3.2'
```

### "Resumo com erros de português"

**Causa**: Modelo em inglês.

**Solução**: Adicione instrução mais clara no prompt (já configurado no código).

## 📊 Recursos de Hardware

| Modelo    | RAM Mínima | RAM Recomendada | CPU      |
| --------- | ---------- | --------------- | -------- |
| llama3.2  | 4GB        | 8GB             | Qualquer |
| mistral   | 8GB        | 16GB            | 4+ cores |
| medllama2 | 8GB        | 16GB            | 4+ cores |

**Dica**: Para produção com múltiplos usuários, considere:

- 16GB+ RAM
- SSD (melhora tempo de carregamento)
- CPU moderna (Intel i5/Ryzen 5+)

## 🔧 Comandos Úteis

```powershell
# Listar modelos instalados
ollama list

# Remover modelo (liberar espaço)
ollama rm mistral

# Ver logs do Ollama
ollama logs

# Parar Ollama
Stop-Process -Name ollama

# Iniciar Ollama
ollama serve

# Testar modelo diretamente
ollama run mistral "Resuma: Paciente diabético tipo 2, hipertenso"
```

## 🌐 Instalação em Linux/Mac

### Ubuntu/Debian

```bash
curl -fsSL https://ollama.ai/install.sh | sh
ollama pull mistral
```

### macOS

```bash
brew install ollama
ollama pull mistral
```

## 📚 Próximos Passos

Após instalar Ollama:

1. ✅ Reinicie Django
2. ✅ Acesse um paciente no sistema
3. ✅ Verifique o indicador "Ollama Ativo" no resumo
4. ✅ O resumo será gerado por IA em vez do fallback estruturado

**Pronto!** Agora o sistema usa IA local com total privacidade e segurança.

---

## 🆘 Suporte

- Documentação Ollama: https://github.com/ollama/ollama
- Issues: Abra ticket no GitHub do projeto
- Discord Ollama: https://discord.gg/ollama
