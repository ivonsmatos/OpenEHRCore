# Manuais clínicos — base de conhecimento (RAG)

Coloque aqui os documentos (`.txt`, `.md`, `.pdf`) que alimentarão o assistente
clínico. Depois rode:

```bash
python manage.py ingest_knowledge
```

> Lembre: isto **não treina** o modelo. Os documentos viram uma base
> **pesquisável**; a IA cita a fonte e o **profissional decide**.
> ⚠️ Os arquivos reais **não** são versionados (ver `.gitignore`) — podem ser
> grandes e/ou ter direitos autorais.

## ✅ Documentos recomendados para subir

### Públicos / governamentais (uso livre)
- **PCDT** — Protocolos Clínicos e Diretrizes Terapêuticas (Ministério da Saúde / CONITEC)
- **RENAME** — Relação Nacional de Medicamentos Essenciais
- **RENASES** — Relação Nacional de Ações e Serviços de Saúde
- **Cadernos de Atenção Básica (CAB)** — Ministério da Saúde
- **Protocolos da Atenção Básica** (hipertensão, diabetes, saúde da mulher, da criança, do idoso)
- **PNI** — Manual de Normas e Calendário Nacional de Vacinação
- **Notificação compulsória / SINAN** — listas e fichas
- **Bulário / RDCs da ANVISA** relevantes
- **CID-10 / CIAP-2** — referências de codificação

### Sociedades médicas (verifique a licença de uso)
- Diretrizes **SBC** (cardiologia), **SBD** (diabetes), **SBPT** (pneumologia), **SBN** (nefrologia) etc.
- **Protocolo de Manchester** (classificação de risco) — se a licença permitir

### Institucionais — os mais valiosos (são seus)
- **POPs** (Procedimentos Operacionais Padrão) da clínica/hospital
- **Protocolos clínicos institucionais** (antibioticoterapia, sepse, dor, TEV…)
- **Protocolos de enfermagem** e fluxos de triagem/atendimento
- **Manual do usuário** do próprio sistema (para suporte)

## ⚠️ Direitos autorais / LGPD
- Use **apenas** documentos que você tem direito de utilizar. Prefira fontes
  públicas (gov.br/MS/CONITEC) e seus **protocolos institucionais**.
- **Não** inclua dados de pacientes nos manuais — esta base é de conhecimento
  clínico, não de prontuários.
- Evite conteúdo licenciado de terceiros (ex.: UpToDate) sem autorização.
