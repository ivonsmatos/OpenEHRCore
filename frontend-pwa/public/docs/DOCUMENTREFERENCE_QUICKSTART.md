# 🚀 Quick Start - DocumentReference API

## Upload de Documento

### cURL

```bash
curl -X POST https://api.openehrcore.com/api/v1/documents/upload/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@hemograma.pdf" \
  -F "patient_id=abc-123-def" \
  -F "type=lab-report" \
  -F "title=Hemograma Completo" \
  -F "security_label[]=N"
```

### Python

```python
import requests

url = "https://api.openehrcore.com/api/v1/documents/upload/"
headers = {"Authorization": "Bearer YOUR_TOKEN"}

files = {"file": open("hemograma.pdf", "rb")}
data = {
    "patient_id": "abc-123-def",
    "type": "lab-report",
    "title": "Hemograma Completo",
    "security_label": ["N"]
}

response = requests.post(url, headers=headers, files=files, data=data)
print(response.json())
```

### JavaScript/React

```tsx
const uploadDocument = async (file: File, patientId: string) => {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("patient_id", patientId);
  formData.append("type", "lab-report");
  formData.append("title", file.name);

  const response = await fetch("/api/v1/documents/upload/", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${localStorage.getItem("token")}`,
    },
    body: formData,
  });

  return response.json();
};
```

---

## Listar Documentos

### cURL

```bash
# Todos os documentos
curl -X GET https://api.openehrcore.com/api/v1/documents/ \
  -H "Authorization: Bearer YOUR_TOKEN"

# Documentos de um paciente específico
curl -X GET https://api.openehrcore.com/api/v1/documents/patient/abc-123-def/ \
  -H "Authorization: Bearer YOUR_TOKEN"

# Filtrar por tipo
curl -X GET "https://api.openehrcore.com/api/v1/documents/?type=lab-report" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Python

```python
import requests

url = "https://api.openehrcore.com/api/v1/documents/patient/abc-123-def/"
headers = {"Authorization": "Bearer YOUR_TOKEN"}

response = requests.get(url, headers=headers)
documents = response.json()

for doc in documents:
    print(f"{doc['type_display']} - {doc['date']}")
```

### JavaScript/React

```tsx
const loadDocuments = async (patientId: string) => {
  const response = await fetch(`/api/v1/documents/patient/${patientId}/`, {
    headers: {
      Authorization: `Bearer ${localStorage.getItem("token")}`,
    },
  });

  const data = await response.json();
  return data;
};
```

---

## Download de Documento

### cURL

```bash
curl -X GET "https://api.openehrcore.com/api/v1/documents/doc-id/download/?attachment_id=att-id" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  --output hemograma.pdf
```

### Python

```python
import requests

url = "https://api.openehrcore.com/api/v1/documents/doc-id/download/"
params = {"attachment_id": "att-id"}
headers = {"Authorization": "Bearer YOUR_TOKEN"}

response = requests.get(url, headers=headers, params=params)

with open("hemograma.pdf", "wb") as f:
    f.write(response.content)
```

### JavaScript/React

```tsx
const downloadDocument = async (docId: string, attachmentId: string) => {
  const response = await fetch(
    `/api/v1/documents/${docId}/download/?attachment_id=${attachmentId}`,
    {
      headers: {
        Authorization: `Bearer ${localStorage.getItem("token")}`,
      },
    }
  );

  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "documento.pdf";
  a.click();
  window.URL.revokeObjectURL(url);
};
```

---

## Criar DocumentReference (FHIR Completo)

### Python

```python
import requests

url = "https://api.openehrcore.com/api/v1/documents/"
headers = {
    "Authorization": "Bearer YOUR_TOKEN",
    "Content-Type": "application/json"
}

data = {
    "patient": "abc-123-def",
    "type": "lab-report",
    "doc_status": "final",
    "status": "current",
    "description": "Hemograma completo - resultado normal",
    "security_label": ["N"],
    "content": [{
        "attachment": {
            "contentType": "application/pdf",
            "url": "https://storage.com/file.pdf",
            "title": "Hemograma Completo",
            "creation": "2024-01-15T10:30:00Z"
        }
    }]
}

response = requests.post(url, headers=headers, json=data)
print(response.json())
```

---

## Tipos de Documentos Disponíveis

| Valor               | Label                  | Descrição                        |
| ------------------- | ---------------------- | -------------------------------- |
| `lab-report`        | Resultado Laboratorial | Exames de sangue, urina, etc.    |
| `imaging-report`    | Laudo de Imagem        | RX, TC, RM, US                   |
| `prescription`      | Prescrição             | Receitas médicas                 |
| `discharge-summary` | Sumário de Alta        | Relatório de alta hospitalar     |
| `progress-note`     | Nota de Evolução       | Evolução médica                  |
| `consent-form`      | Termo de Consentimento | TCLE, autorizações               |
| `referral`          | Encaminhamento         | Encaminhamento para especialista |
| `other`             | Outro                  | Outros tipos de documentos       |

---

## Security Labels

| Código | Descrição       | Permissões                 |
| ------ | --------------- | -------------------------- |
| `N`    | Normal          | Todos com permissão padrão |
| `R`    | Restricted      | Apenas equipe de cuidado   |
| `V`    | Very Restricted | Apenas admin e autor       |

---

## Exemplo de Response FHIR

```json
{
  "resourceType": "DocumentReference",
  "id": "abc-123-def",
  "meta": {
    "versionId": "1",
    "lastUpdated": "2024-01-15T10:30:00Z"
  },
  "status": "current",
  "docStatus": "final",
  "type": {
    "coding": [
      {
        "system": "http://loinc.org",
        "code": "11502-2",
        "display": "Resultado Laboratorial"
      }
    ],
    "text": "Resultado Laboratorial"
  },
  "category": [
    {
      "coding": [
        {
          "system": "http://hl7.org/fhir/us/core/CodeSystem/us-core-documentreference-category",
          "code": "clinical-note",
          "display": "Clinical Note"
        }
      ]
    }
  ],
  "subject": {
    "reference": "Patient/12345",
    "display": "João da Silva"
  },
  "date": "2024-01-15T10:30:00Z",
  "author": [
    {
      "reference": "Practitioner/67890",
      "display": "Dr. Maria Santos"
    }
  ],
  "description": "Hemograma completo - resultado normal",
  "securityLabel": [
    {
      "coding": [
        {
          "system": "http://terminology.hl7.org/CodeSystem/v3-Confidentiality",
          "code": "N",
          "display": "Normal"
        }
      ]
    }
  ],
  "content": [
    {
      "attachment": {
        "contentType": "application/pdf",
        "size": 245632,
        "hash": "ZTNiMGM0NDI5OGZjMWMxNDlhZmJmNGM4OTk2ZmI5MjQyN2FlNDFlNDY0OWI5MzRjYTQ5NTk5MWI3ODUyYjg1NQ==",
        "title": "hemograma_completo.pdf",
        "creation": "2024-01-15T10:30:00Z"
      }
    }
  ]
}
```

---

## Componente React Completo

```tsx
import React, { useState } from "react";
import DocumentManager from "./components/clinical/DocumentManager";

const PatientDocumentsPage: React.FC = () => {
  const patientId = "abc-123-def"; // Da rota ou props

  return (
    <div style={{ padding: "24px" }}>
      <DocumentManager
        patientId={patientId}
        onDocumentSelect={(doc) => {
          console.log("Documento selecionado:", doc);
          // Abrir modal de visualização, etc.
        }}
      />
    </div>
  );
};

export default PatientDocumentsPage;
```

---

## Permissões Necessárias

### Backend (Django)

```python
# settings.py
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ]
}
```

### Grupos de Usuários

- **Admin**: Acesso total (CRUD + estatísticas)
- **Practitioner**: CRUD nos próprios documentos + view de pacientes sob cuidado
- **Patient**: View dos próprios documentos (exceto Very Restricted)

---

## Troubleshooting

### Erro 413: Payload Too Large

```bash
# Aumentar limite no Nginx
client_max_body_size 50M;

# Aumentar no Django settings.py
DATA_UPLOAD_MAX_MEMORY_SIZE = 52428800  # 50MB
```

### Erro 403: Forbidden

- Verificar token JWT válido
- Verificar permissões do usuário
- Verificar security label do documento

### Erro 400: Tipo de arquivo não permitido

```python
# Extensões permitidas
ALLOWED_EXTENSIONS = ['.pdf', '.jpg', '.jpeg', '.png', '.tiff', '.dcm', '.doc', '.docx']
```

---

## Métricas de Performance

```bash
# Estatísticas gerais
curl -X GET https://api.openehrcore.com/api/v1/documents/statistics/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**

```json
{
  "total_documents": 15234,
  "by_type": {
    "lab-report": 8500,
    "imaging-report": 3200,
    "prescription": 2100,
    "other": 1434
  },
  "by_status": {
    "current": 14800,
    "superseded": 400,
    "entered-in-error": 34
  },
  "total_storage_mb": 12450.5,
  "cached_at": "2024-01-15T10:30:00Z"
}
```

---

## Links Úteis

- [Documentação Completa](./FHIR_DOCUMENTREFERENCE_IMPLEMENTATION.md)
- [FHIR R4 DocumentReference Spec](https://hl7.org/fhir/R4/documentreference.html)
- [API Reference (OpenAPI)](https://api.openehrcore.com/docs/openapi.json)
- [Guia de Segurança LGPD](./LGPD_COMPLIANCE.md)
