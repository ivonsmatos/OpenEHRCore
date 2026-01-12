# Keycloak Integration Guide — OpenEHRCore Phase 1

## 📋 Overview

Integração completa com Keycloak para autenticação e autorização:

- ✅ **Backend**: Django + KeycloakAuthentication (JWT validation)
- ✅ **Frontend**: React + AuthProvider + useAuth hook
- ✅ **Roles**: Médicos, Enfermeiros, Admin, Pacientes
- ✅ **Protected Routes**: Endpoints com role-based access control

---

## 🚀 Quick Setup (10 minutos)

### 1. Levantar Keycloak

```bash
cd docker
docker-compose up -d
```

Aguarde Keycloak ficar disponível (~30 segundos).

### 2. Executar script de setup

```bash
bash scripts/keycloak-setup.sh
```

Este script cria automaticamente:

- ✅ Realm `openehrcore`
- ✅ Cliente Django (secret OAuth2)
- ✅ Cliente React (público, PKCE)
- ✅ Roles: médico, enfermeiro, admin, paciente
- ✅ Usuário teste: `medico@example.com` / `senha123!@#`

**Output esperado:**

```
✅ Keycloak configurado com sucesso!

📝 Configurações para seus arquivos .env:

backend-django/.env:
  KEYCLOAK_CLIENT_ID=openehrcore-backend
  KEYCLOAK_CLIENT_SECRET=<secret>
  KEYCLOAK_REALM=openehrcore

frontend-pwa/.env.local:
  VITE_KEYCLOAK_CLIENT_ID=openehrcore-frontend
  VITE_KEYCLOAK_REALM=openehrcore
```

### 3. Configurar variáveis de ambiente

**backend-django/.env**

```env
# ... resto das configurações

KEYCLOAK_URL=http://localhost:8180
KEYCLOAK_REALM=openehrcore
KEYCLOAK_CLIENT_ID=openehrcore-backend
KEYCLOAK_CLIENT_SECRET=<copiar do script output>
```

**frontend-pwa/.env.local**

```env
VITE_API_URL=http://localhost:8000/api/v1
VITE_FHIR_SERVER=http://localhost:8080/fhir
VITE_KEYCLOAK_CLIENT_ID=openehrcore-frontend
VITE_KEYCLOAK_REALM=openehrcore
```

### 4. Iniciar aplicação

```bash
# Terminal 1: Backend
cd backend-django
python manage.py runserver

# Terminal 2: Frontend
cd frontend-pwa
npm install
npm run dev
```

### 5. Testar login

Abra http://localhost:5173 e use:

- **Email**: `medico@example.com`
- **Senha**: `senha123!@#`

---

## 🔐 Como Funciona

### Backend — Fluxo de Autenticação

```
1. Cliente faz POST /api/v1/auth/login/
   Body: { username, password }

2. Django chama Keycloak /token endpoint
   Valida credenciais contra Keycloak

3. Keycloak retorna access_token (JWT)

4. Django retorna token para cliente

5. Cliente armazena token no localStorage

6. Requisições incluem: Authorization: Bearer <token>

7. Django valida token via KeycloakAuthentication
   - Chama Keycloak /introspect endpoint
   - Valida signature e expiração
   - Extrai roles e claims

8. Se válido: requisição prossegue
   Se inválido: 401 Unauthorized
```

### Frontend — Fluxo de Login

```
AuthProvider (wraps app)
    ↓
useAuth hook (get login, logout, user, token)
    ↓
<Login /> component (form)
    ↓
POST /api/v1/auth/login/
    ↓
Salva token em localStorage
    ↓
Decodifica JWT (obtém user info, roles)
    ↓
Redireciona para Dashboard
    ↓
Todas requisições incluem Authorization header
```

---

## 📝 Código Principal

### 1. Backend — Autenticação (`backend-django/fhir_api/auth.py`)

```python
from .auth import KeycloakAuthentication, require_role

# Em qualquer view:
@api_view(['POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
@require_role('medico', 'admin')  # Validar roles
def create_patient(request):
    # user_info = request.user
    # user_info.roles → ['medico']
    pass
```

### 2. Frontend — Auth Hook (`frontend-pwa/src/hooks/useAuth.ts`)

```typescript
import { useAuth, AuthProvider, ProtectedRoute } from "./hooks/useAuth";

// Em App.tsx:
function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

// Em componentes:
const Dashboard = () => {
  const { user, logout, login } = useAuth();

  // user.roles → ['medico']
};
```

### 3. Frontend — Tela de Login (`frontend-pwa/src/components/Login.tsx`)

```typescript
const { login } = useAuth();

await login("medico@example.com", "senha123!@#");
// Token salvo automaticamente
// useAuth hook atualiza user state
```

---

## 🧪 Testar Endpoints

### 1. Obter token (login)

```bash
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "medico@example.com",
    "password": "senha123!@#"
  }'

# Resposta:
# {
#   "access_token": "eyJhbGciOiJIUzI1NiIs...",
#   "token_type": "Bearer"
# }
```

### 2. Usar token em requisição protegida

```bash
TOKEN="eyJhbGciOiJIUzI1NiIs..." # copiar do step anterior

curl -X POST http://localhost:8000/api/v1/patients/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "João",
    "last_name": "Silva",
    "birth_date": "1990-05-15",
    "cpf": "12345678901",
    "gender": "male"
  }'

# Resposta:
# {
#   "resourceType": "Patient",
#   "id": "patient-123",
#   "name": "João Silva",
#   "created_by": "medico@example.com"
# }
```

### 3. Sem token (deve falhar)

```bash
curl -X POST http://localhost:8000/api/v1/patients/ \
  -H "Content-Type: application/json" \
  -d '{"first_name": "João", ...}'

# Resposta: 401 Unauthorized
```

### 4. Com role insuficiente (deve falhar)

```bash
# Criar usuário 'paciente' (sem permissão para criar pacientes)
# Fazer login com paciente
# Tentar POST /patients/ → 403 Forbidden
```

---

## 🔑 Gerenciar Roles e Usuários

### 1. Acessar admin do Keycloak

```
URL: http://localhost:8180
Email: admin
Senha: admin_password_123
```

### 2. Criar novo usuário

```
1. Realms → openehrcore → Users
2. Add user
3. Username: enfermeiro@example.com
4. Email verified: ON
5. Credentials → Set password: senha123!@#
6. Temporary: OFF
7. Save
8. Role Mappings → Add Role → enfermeiro
```

### 3. Logout de usuário existente

```
1. Sessions → Sessions ativas
2. Clique em X para forçar logout
```

---

## 🛡️ Segurança

### Token Validation

- ✅ Assinatura JWT validada
- ✅ Expiração verificada
- ✅ Roles extraídas e validadas
- ✅ Introspect endpoint usado (servidor confiável)

### Best Practices

1. **Nunca** armazene senha em localStorage

   - ✅ Apenas token armazenado
   - ✅ Token refresh automático

2. **HTTPS** em produção

   - Todas requisições HTTPS/TLS
   - Secure flag no cookie

3. **CORS** configurado
   - Frontend: http://localhost:5173
   - Backend: http://localhost:8000
   - Keycloak: http://localhost:8180

---

## 🐛 Troubleshooting

### "Token inválido ou expirado"

```bash
# 1. Verificar if Keycloak está rodando
curl http://localhost:8180/health/ready

# 2. Verificar configuração no .env
cat backend-django/.env | grep KEYCLOAK

# 3. Fazer novo login
```

### "Role não encontrada"

```bash
# Verificar roles no Keycloak:
# 1. Admin → Realms → openehrcore → Roles
# 2. Criar role se não existir
```

### "CORS error"

```bash
# Verificar CORS_ALLOWED_ORIGINS em settings.py
# Deve incluir http://localhost:5173
```

---

## 📚 Próximos Passos

- [ ] Refresh tokens automático
- [ ] Remember me (longer token)
- [ ] Social login (Google, GitHub)
- [ ] MFA (2FA)
- [ ] Auditoria de login/logout
- [ ] Rate limiting no endpoint de login

---

**Status**: ✅ Phase 1 — Keycloak integration completo

**Próxima**: CRUD Encounter/Observation
