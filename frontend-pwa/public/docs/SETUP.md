# Setup — OpenEHRCore (Guia Instalação)

## 📋 Pré-requisitos

### Sistema

- **OS**: Windows, macOS, Linux
- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **Git**: 2.30+

### Locais

- **Node.js**: 18+ (para frontend)
- **Python**: 3.10+ (para backend)
- **PostgreSQL**: 14+ (já incluído no Docker)

## 🚀 Quick Start (5 minutos)

### 1. Clonar repositório

```bash
git clone https://github.com/ivonsmatos/OpenEHRCore.git
cd OpenEHRCore
```

### 2. Levantar infraestrutura (Docker Compose)

```bash
cd docker
docker-compose up -d
```

**Validar stack:**

```bash
# HAPI FHIR - deve retornar CapabilityStatement
curl http://localhost:8080/fhir/metadata | jq .

# Keycloak - deve retornar 200 OK
curl http://localhost:8180/health/ready

# PostgreSQL - deve estar acessível
psql -h localhost -U fhir_user -d hapi_fhir
```

Credenciais padrão:

- **HAPI FHIR**: http://localhost:8080/fhir (sem auth)
- **Keycloak Admin**: http://localhost:8180 (admin / admin_password_123)
- **PostgreSQL**: fhir_user / fhir_secure_password_123

### 3. Setup Backend (Django)

```bash
cd backend-django

# Criar virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt

# Executar migrations (se houver)
python manage.py migrate

# Rodar servidor development
python manage.py runserver
```

Server será acessível em: http://localhost:8000

### 4. Setup Frontend (React)

```bash
cd frontend-pwa

# Instalar dependências
npm install

# Rodar dev server com hot reload
npm run dev
```

Server será acessível em: http://localhost:5173

### 5. Validar Stack Completa

```bash
# 1. Verificar health check (testa conexão com HAPI FHIR)
curl http://localhost:8000/api/v1/health/

# Resposta esperada:
# {
#   "status": "ok",
#   "fhir_server": "healthy",
#   "message": "HAPI FHIR and infrastructure are operational"
# }

# 2. Criar paciente de teste via backend
curl -X POST http://localhost:8000/api/v1/patients/ \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Test",
    "last_name": "Patient",
    "birth_date": "1990-01-01",
    "cpf": "12345678901",
    "gender": "male",
    "telecom": [
      {"system": "phone", "value": "(11) 98765-4321"}
    ]
  }'

# 3. Acessar frontend no navegador
# http://localhost:5173
# Você verá um exemplo de paciente renderizado com Design System
```

## 📁 Estrutura de Pastas

```
OpenEHRCore/
├── docker/                          # Orquestração de containers
│   └── docker-compose.yml
│
├── backend-django/                  # API REST (BFF)
│   ├── requirements.txt
│   ├── manage.py
│   ├── openehrcore/                 # Configuração Django
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   ├── fhir_api/                    # Aplicação FHIR
│   │   ├── views.py                 # Endpoints
│   │   ├── urls.py
│   │   └── services/
│   │       └── fhir_core.py         # Integração HAPI FHIR
│   └── venv/                        # Virtual environment
│
├── frontend-pwa/                    # UI (React + TypeScript)
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── src/
│   │   ├── theme/
│   │   │   └── colors.ts            # Design System tokens
│   │   ├── components/
│   │   │   ├── base/                # Componentes reutilizáveis
│   │   │   └── PatientDetail.tsx
│   │   ├── utils/
│   │   │   └── fhirParser.ts        # Parsing seguro FHIR
│   │   └── App.tsx
│   └── public/
│
└── docs/                            # Documentação
    ├── ARCHITECTURE.md
    ├── SETUP.md                     # Este arquivo
    └── DESIGN_SYSTEM.md
```

## 🔧 Configuração de Ambiente

### Backend (.env)

Crie arquivo `backend-django/.env`:

```env
# Django
DEBUG=True
DJANGO_SECRET_KEY=your-secret-key-change-in-production
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# Database
DB_NAME=openehr_db
DB_USER=postgres
DB_PASSWORD=password
DB_HOST=localhost
DB_PORT=5432

# FHIR Server
FHIR_SERVER_URL=http://localhost:8080/fhir
FHIR_SERVER_TIMEOUT=30

# Keycloak
KEYCLOAK_URL=http://localhost:8180
KEYCLOAK_REALM=master
KEYCLOAK_CLIENT_ID=openehrcore
KEYCLOAK_CLIENT_SECRET=your-client-secret

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000
```

### Frontend (.env)

Crie arquivo `frontend-pwa/.env.local`:

```env
VITE_API_URL=http://localhost:8000/api/v1
VITE_FHIR_SERVER=http://localhost:8080/fhir
VITE_KEYCLOAK_URL=http://localhost:8180
```

## 📚 Comandos Úteis

### Docker Compose

```bash
# Levantar todos os serviços em background
docker-compose up -d

# Ver logs em tempo real
docker-compose logs -f

# Ver logs de um serviço específico
docker-compose logs -f hapi-fhir

# Parar containers
docker-compose down

# Remover volumes (cuidado!)
docker-compose down -v

# Recriar containers
docker-compose up -d --force-recreate
```

### Backend Django

```bash
# Ativar virtual environment
source venv/bin/activate  # Windows: venv\Scripts\activate

# Instalar pacotes
pip install -r requirements.txt

# Atualizar requirements
pip freeze > requirements.txt

# Rodar servidor
python manage.py runserver

# Rodar servidor em IP/porta específica
python manage.py runserver 0.0.0.0:8000

# Criar migrations
python manage.py makemigrations

# Aplicar migrations
python manage.py migrate

# Shell interativo
python manage.py shell

# Criar superuser (admin)
python manage.py createsuperuser

# Testes
python manage.py test

# Linting
flake8 .

# Type checking
mypy .
```

### Frontend React

```bash
# Instalar dependências
npm install

# Rodar dev server (com hot reload)
npm run dev

# Build para produção
npm run build

# Preview da build
npm run preview

# Linting
npm run lint

# Type checking
npm run type-check

# Limpar node_modules
rm -rf node_modules && npm install
```

## 🐛 Troubleshooting

### HAPI FHIR não inicia

```bash
# Ver logs
docker-compose logs hapi-fhir

# Verificar se porta 8080 está em uso
netstat -an | grep 8080

# Reiniciar container
docker-compose restart hapi-fhir
```

### Django não conecta ao FHIR

```bash
# Verificar URL de conexão em settings.py
# FHIR_SERVER_URL deve estar correto

# Testar conectividade
curl http://localhost:8080/fhir/metadata

# Ver logs Django
tail -f backend-django/debug.log
```

### Frontend não conecta ao backend

```bash
# Verificar VITE_API_URL em .env.local
# Deve ser http://localhost:8000/api/v1

# Verificar CORS no Django settings.py
# CORS_ALLOWED_ORIGINS deve incluir http://localhost:5173

# Verificar console do navegador (F12) para erros
```

### PostgreSQL permission denied

```bash
# Resetar permissões do volume
docker-compose down
docker volume rm openehrcore_postgres_data
docker-compose up -d postgres

# Esperar alguns segundos para criar schema
sleep 10
docker-compose up -d
```

## 🔐 Segurança (Desenvolvimento)

⚠️ **As credenciais padrão são APENAS para desenvolvimento!**

Antes de deployar em produção:

1. Mudar `DJANGO_SECRET_KEY` em `.env`
2. Mudar senhas do PostgreSQL e Keycloak
3. Usar HTTPS/TLS
4. Configurar firewall
5. Usar gerenciador de secrets (Vault, AWS Secrets Manager, etc)

## 📝 Próximos Passos

1. **Integração com Keycloak** — OAuth2 flows completos
2. **Observações Clínicas** — Criar/visualizar Observation FHIR
3. **Offline-first** — Service workers + IndexedDB
4. **Auditoria** — Logging de acesso a dados sensíveis
5. **Testes** — Unit tests + E2E tests
6. **CI/CD** — GitHub Actions para deploy automático

## 📞 Suporte

- 📧 Issues: https://github.com/ivonsmatos/OpenEHRCore/issues
- 💬 Discussions: https://github.com/ivonsmatos/OpenEHRCore/discussions
- 📖 Docs: `/docs` neste repositório

---

**Last updated**: 3 de dezembro de 2025  
**Version**: 0.1.0 (Alpha)
