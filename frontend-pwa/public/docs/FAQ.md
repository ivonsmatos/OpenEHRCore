# FAQ Técnico - OpenEHR Core

## Índice

- [Instalação e Configuração](#instalação-e-configuração)
- [Desenvolvimento](#desenvolvimento)
- [Autenticação e Segurança](#autenticação-e-segurança)
- [Performance](#performance)
- [Troubleshooting](#troubleshooting)
- [Deploy e Produção](#deploy-e-produção)

---

## Instalação e Configuração

### ❓ Como instalar o projeto pela primeira vez?

**Resposta:**

```bash
# 1. Clone o repositório
git clone https://github.com/seu-org/OpenEHRCore.git
cd OpenEHRCore

# 2. Configure variáveis de ambiente
cp .env.example .env
# Edite .env com suas configurações

# 3. Suba os containers
docker-compose up -d

# 4. Execute migrations
docker-compose exec backend python manage.py migrate

# 5. Crie superusuário
docker-compose exec backend python manage.py createsuperuser

# 6. Acesse a aplicação
# Frontend: http://localhost:3000
# Backend Admin: http://localhost:8000/admin
```

📚 **Ver mais:** [Setup Guide completo](./SETUP.md)

---

### ❓ Quais são as portas utilizadas?

| Serviço          | Porta | Uso              |
| ---------------- | ----- | ---------------- |
| Frontend (Vite)  | 3000  | Interface web    |
| Backend (Django) | 8000  | API REST/FHIR    |
| PostgreSQL       | 5432  | Banco de dados   |
| Redis            | 6379  | Cache/Sessions   |
| Keycloak         | 8080  | SSO/Autenticação |

---

### ❓ Como configurar o Keycloak SSO?

**Resposta:**

1. Acesse `http://localhost:8080`
2. Faça login com credenciais admin
3. Crie um novo Realm: `openehr`
4. Configure Client ID: `openehr-frontend`
5. Adicione Redirect URIs: `http://localhost:3000/*`

📚 **Ver guia completo:** [Keycloak Setup](./KEYCLOAK_SETUP.md)

---

## Desenvolvimento

### ❓ Como adicionar uma nova página React?

**Resposta:**

```typescript
// 1. Crie o componente
// frontend-pwa/src/pages/MyNewPage.tsx
import React from "react";

const MyNewPage: React.FC = () => {
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold">Minha Nova Página</h1>
    </div>
  );
};

export default MyNewPage;

// 2. Adicione a rota
// frontend-pwa/src/routes.tsx
const MyNewPage = lazyLoad(() => import("./pages/MyNewPage"));

// Dentro de ProtectedRoutes:
<Route path="/mynewpage" element={<MyNewPage />} />;
```

---

### ❓ Como usar o Design System do projeto?

**Resposta:**

```typescript
import { colors, spacing, typography } from '@/theme/colors';

// Use as cores da paleta
<button className="bg-[#0468BF] text-white px-4 py-2">
  Botão Primário
</button>

// Ou via objeto colors
<div style={{ backgroundColor: colors.primary.medium }}>
  Conteúdo
</div>
```

📚 **Ver guia completo:** [Design System](./DESIGN_SYSTEM.md)

---

### ❓ Como criar um endpoint FHIR no backend?

**Resposta:**

```python
# backend-django/fhir_api/views_custom.py
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Patient

@api_view(['GET'])
def custom_patient_search(request):
    """
    Busca customizada de pacientes
    GET /fhir/Patient/custom-search?condition=diabetes
    """
    condition = request.query_params.get('condition')
    patients = Patient.objects.filter(
        conditions__icontains=condition
    )

    serializer = PatientSerializer(patients, many=True)
    return Response(serializer.data)

# Adicione em urls.py
path('fhir/Patient/custom-search', custom_patient_search),
```

---

## Autenticação e Segurança

### ❓ Como funciona a autenticação?

**Resposta:**

O sistema usa **Keycloak SSO** com OAuth2/OIDC:

1. Usuário acessa `/login`
2. Redirecionado para Keycloak
3. Após login, recebe tokens JWT (access + refresh)
4. Frontend armazena tokens no localStorage
5. Todas as requisições incluem: `Authorization: Bearer <token>`
6. Backend valida token com Keycloak

```typescript
// Exemplo de requisição autenticada
const token = localStorage.getItem("access_token");

fetch("/api/patients", {
  headers: {
    Authorization: `Bearer ${token}`,
    "Content-Type": "application/json",
  },
});
```

---

### ❓ Como implementar permissões RBAC?

**Resposta:**

```python
# Backend - Decorador de permissão
from rest_framework.permissions import BasePermission

class CanViewPatient(BasePermission):
    def has_permission(self, request, view):
        return request.user.has_perm('patients.view_patient')

# Use na view
class PatientViewSet(viewsets.ModelViewSet):
    permission_classes = [CanViewPatient]
```

```typescript
// Frontend - Componente de permissão
<PermissionGate permission="patients.view">
  <PatientList />
</PermissionGate>
```

---

## Performance

### ❓ Como otimizar queries do banco de dados?

**Resposta:**

```python
# ❌ Ruim - N+1 queries
patients = Patient.objects.all()
for patient in patients:
    print(patient.encounters.all())  # Query por paciente!

# ✅ Bom - Select related
patients = Patient.objects.prefetch_related('encounters').all()
for patient in patients:
    print(patient.encounters.all())  # Sem query adicional
```

---

### ❓ Como fazer lazy loading de rotas?

**Resposta:**

```typescript
// Já implementado! Use o padrão:
const MyPage = lazyLoad(() => import("./pages/MyPage"));

// Isso gera um bundle separado (code splitting)
// Carrega apenas quando o usuário navega para a rota
```

**Benefícios:**

- ✅ Initial bundle menor
- ✅ Faster First Contentful Paint
- ✅ Melhor Lighthouse score

---

### ❓ Como cachear dados no frontend?

**Resposta:**

```typescript
// Use Zustand com persist
import create from "zustand";
import { persist } from "zustand/middleware";

const usePatientStore = create(
  persist(
    (set) => ({
      patients: [],
      addPatient: (patient) =>
        set((state) => ({
          patients: [...state.patients, patient],
        })),
    }),
    { name: "patient-storage" } // LocalStorage key
  )
);
```

---

## Troubleshooting

### ❓ Erro: "CORS blocked" ao fazer requisição

**Solução:**

```python
# backend-django/openehrcore/settings.py

# Adicione o frontend às origens permitidas
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://seu-dominio.com"
]

# Permitir credenciais
CORS_ALLOW_CREDENTIALS = True
```

---

### ❓ Erro: "Token expirado" após algum tempo

**Solução:**

```typescript
// Implementar refresh token automático
import { useEffect } from "react";

useEffect(() => {
  const interval = setInterval(async () => {
    const refreshToken = localStorage.getItem("refresh_token");

    const response = await fetch("/auth/token/refresh", {
      method: "POST",
      body: JSON.stringify({ refresh: refreshToken }),
    });

    const { access } = await response.json();
    localStorage.setItem("access_token", access);
  }, 14 * 60 * 1000); // Renova a cada 14 minutos

  return () => clearInterval(interval);
}, []);
```

---

### ❓ Containers não sobem (erro de porta em uso)

**Solução:**

```bash
# Verificar o que está usando a porta
netstat -ano | findstr :8000

# Matar processo (Windows)
taskkill /PID <PID> /F

# Ou mudar porta no docker-compose.yml
ports:
  - "8001:8000"  # Host:Container
```

---

### ❓ Migrations falhando com erro de constraint

**Solução:**

```bash
# 1. Resete o banco (CUIDADO - apaga dados!)
docker-compose down -v
docker-compose up -d

# 2. Execute migrations do zero
docker-compose exec backend python manage.py migrate

# 3. Recrie fixtures
docker-compose exec backend python manage.py loaddata initial_data.json
```

---

## Deploy e Produção

### ❓ Como fazer deploy em produção?

**Resposta:**

```bash
# 1. Build da aplicação
docker-compose -f docker-compose.prod.yml build

# 2. Rode migrations
docker-compose -f docker-compose.prod.yml run backend python manage.py migrate

# 3. Collect static files
docker-compose -f docker-compose.prod.yml run backend python manage.py collectstatic --noinput

# 4. Suba os serviços
docker-compose -f docker-compose.prod.yml up -d

# 5. Configure Nginx como reverse proxy
```

📚 **Ver mais:** Deploy Guide (em construção)

---

### ❓ Como configurar HTTPS?

**Resposta:**

```nginx
# nginx.conf
server {
    listen 443 ssl http2;
    server_name seu-dominio.com;

    ssl_certificate /etc/letsencrypt/live/seu-dominio.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/seu-dominio.com/privkey.pem;

    location / {
        proxy_pass http://frontend:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api {
        proxy_pass http://backend:8000;
    }
}
```

---

### ❓ Como monitorar a aplicação em produção?

**Resposta:**

**Logs:**

```bash
# Ver logs em tempo real
docker-compose logs -f backend

# Logs de um serviço específico
docker-compose logs -f postgres
```

**Métricas:** (Planejado)

- Prometheus para coleta
- Grafana para dashboards
- Sentry para error tracking

---

## Perguntas Adicionais?

📧 **Email:** suporte@openehrcore.com  
💬 **Chat:** Entre no canal #dev no Slack  
📚 **Documentação:** [docs.openehrcore.com](/)  
🐛 **Issues:** [GitHub Issues](https://github.com/seu-org/OpenEHRCore/issues)

---

**Última atualização:** Dezembro 2025  
**Contribuidores:** Time OpenEHR Core
