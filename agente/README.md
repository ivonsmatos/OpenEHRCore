# OpenEHRCore Agent

Este diretório contém o código para o agente on-premise que atua como ponte entre HL7/MLLP, DICOM e o sistema OpenEHRCore.

## Funcionalidades

- **HL7/MLLP:** Processamento de mensagens HL7 v2.x.
- **DICOM:** Integração com sistemas de imagens médicas.
- **FHIR:** Conversão de dados para recursos FHIR e envio ao backend.

## Estrutura do Projeto

```
agente/
├── hl7/                # Processamento de mensagens HL7
├── dicom/              # Integração com DICOM
├── fhir/               # Conversão e validação de recursos FHIR
├── utils/              # Funções utilitárias
└── main.py             # Ponto de entrada do agente
```

## Como Executar

1. Certifique-se de que as dependências estão instaladas:

   ```bash
   pip install -r requirements.txt
   ```

2. Execute o agente:
   ```bash
   python main.py
   ```

## Dependências

- `hl7` para parsing de mensagens HL7.
- `pydicom` para manipulação de arquivos DICOM.
- `fhir.resources` para validação de recursos FHIR.

## Próximos Passos

- Implementar o processamento de mensagens HL7.
- Adicionar suporte a DICOM.
- Integrar com o backend FHIR-Native.
