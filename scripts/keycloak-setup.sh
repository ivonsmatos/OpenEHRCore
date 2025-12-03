#!/bin/bash
# keycloak-setup.sh - Configura Keycloak automaticamente para OpenEHRCore

set -e

echo "🔐 Configurando Keycloak para OpenEHRCore..."
echo ""

# Cores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Variáveis
KEYCLOAK_URL="http://localhost:8180"
ADMIN_USER="admin"
ADMIN_PASSWORD="admin_password_123"
REALM_NAME="openehrcore"
CLIENT_ID_DJANGO="openehrcore-backend"
CLIENT_ID_REACT="openehrcore-frontend"
REDIRECT_URI_DJANGO="http://localhost:8000/auth/callback"
REDIRECT_URI_REACT="http://localhost:5173/auth/callback"

echo -e "${BLUE}📋 Aguardando Keycloak ficar disponível...${NC}"
max_attempts=30
attempt=0
until curl -s "$KEYCLOAK_URL/health/ready" > /dev/null 2>&1; do
    attempt=$((attempt+1))
    if [ $attempt -ge $max_attempts ]; then
        echo -e "${YELLOW}⚠️ Keycloak não respondeu após 30 tentativas${NC}"
        exit 1
    fi
    echo "  ⏳ Tentativa $attempt/30..."
    sleep 1
done
echo -e "${GREEN}✓ Keycloak disponível${NC}"

echo ""
echo -e "${BLUE}🔑 Obtendo token de admin...${NC}"

TOKEN=$(curl -s -X POST \
  "$KEYCLOAK_URL/auth/realms/master/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=admin-cli" \
  -d "username=$ADMIN_USER" \
  -d "password=$ADMIN_PASSWORD" \
  -d "grant_type=password" | jq -r '.access_token')

if [ -z "$TOKEN" ] || [ "$TOKEN" = "null" ]; then
    echo -e "${YELLOW}⚠️ Falha ao obter token${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Token obtido${NC}"

echo ""
echo -e "${BLUE}🏢 Criando realm '$REALM_NAME'...${NC}"

# Criar realm
curl -s -X POST \
  "$KEYCLOAK_URL/auth/admin/realms" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "realm": "'$REALM_NAME'",
    "enabled": true,
    "displayName": "OpenEHRCore - Sistema de Prontuários",
    "accessTokenLifespan": 3600,
    "refreshTokenLifespan": 86400
  }' > /dev/null 2>&1

echo -e "${GREEN}✓ Realm criado${NC}"

echo ""
echo -e "${BLUE}👤 Criando cliente Django (BFF)...${NC}"

# Criar cliente Django
DJANGO_CLIENT_RESPONSE=$(curl -s -X POST \
  "$KEYCLOAK_URL/auth/admin/realms/$REALM_NAME/clients" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "clientId": "'$CLIENT_ID_DJANGO'",
    "name": "OpenEHRCore Backend (Django)",
    "enabled": true,
    "publicClient": false,
    "standardFlowEnabled": true,
    "implicitFlowEnabled": false,
    "directAccessGrantsEnabled": true,
    "serviceAccountsEnabled": true,
    "redirectUris": ["'$REDIRECT_URI_DJANGO'"],
    "webOrigins": ["http://localhost:8000"]
  }')

DJANGO_CLIENT_ID=$(echo "$DJANGO_CLIENT_RESPONSE" | jq -r '.id')
echo -e "${GREEN}✓ Cliente Django criado (ID: $DJANGO_CLIENT_ID)${NC}"

# Obter secret do cliente Django
DJANGO_CLIENT_SECRET=$(curl -s -X GET \
  "$KEYCLOAK_URL/auth/admin/realms/$REALM_NAME/clients/$DJANGO_CLIENT_ID/client-secret" \
  -H "Authorization: Bearer $TOKEN" | jq -r '.value')

echo -e "${GREEN}✓ Secret Django: $DJANGO_CLIENT_SECRET${NC}"

echo ""
echo -e "${BLUE}🌐 Criando cliente React (Frontend)...${NC}"

# Criar cliente React
REACT_CLIENT_RESPONSE=$(curl -s -X POST \
  "$KEYCLOAK_URL/auth/admin/realms/$REALM_NAME/clients" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "clientId": "'$CLIENT_ID_REACT'",
    "name": "OpenEHRCore Frontend (React)",
    "enabled": true,
    "publicClient": true,
    "standardFlowEnabled": true,
    "implicitFlowEnabled": true,
    "redirectUris": ["'$REDIRECT_URI_REACT'", "http://localhost:5173/*"],
    "webOrigins": ["http://localhost:5173"],
    "protocol": "openid-connect"
  }')

REACT_CLIENT_ID=$(echo "$REACT_CLIENT_RESPONSE" | jq -r '.id')
echo -e "${GREEN}✓ Cliente React criado (ID: $REACT_CLIENT_ID)${NC}"

echo ""
echo -e "${BLUE}👨‍⚕️ Criando roles FHIR...${NC}"

# Criar roles
for ROLE in "medico" "enfermeiro" "admin" "paciente"; do
    curl -s -X POST \
      "$KEYCLOAK_URL/auth/admin/realms/$REALM_NAME/roles" \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "name": "'$ROLE'",
        "description": "Role para '$ROLE' no OpenEHRCore"
      }' > /dev/null 2>&1
    echo -e "  ${GREEN}✓ Role '$ROLE' criado${NC}"
done

echo ""
echo -e "${BLUE}👤 Criando usuário de teste (contato@ivonmatos.com.br)...${NC}"

# Criar usuário teste
TEST_USER_RESPONSE=$(curl -s -X POST \
  "$KEYCLOAK_URL/auth/admin/realms/$REALM_NAME/users" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "contato@ivonmatos.com.br",
    "email": "contato@ivonmatos.com.br",
    "enabled": true,
    "emailVerified": true,
    "firstName": "Ivon",
    "lastName": "Matos",
    "credentials": [{
      "type": "password",
      "value": "Protonsysdba@1986",
      "temporary": false
    }]
  }')

TEST_USER_ID=$(echo "$TEST_USER_RESPONSE" | jq -r '.id')
echo -e "${GREEN}✓ Usuário criado: contato@ivonmatos.com.br / Protonsysdba@1986${NC}"

# Atribuir role ao usuário
curl -s -X POST \
  "$KEYCLOAK_URL/auth/admin/realms/$REALM_NAME/users/$TEST_USER_ID/role-mappings/realm" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '[{
    "name": "medico"
  }]' > /dev/null 2>&1

echo -e "${GREEN}✓ Role 'medico' atribuída${NC}"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}✅ Keycloak configurado com sucesso!${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${BLUE}📝 Configurações para seus arquivos .env:${NC}"
echo ""
echo "backend-django/.env:"
echo -e "  ${YELLOW}KEYCLOAK_CLIENT_ID=${CLIENT_ID_DJANGO}${NC}"
echo -e "  ${YELLOW}KEYCLOAK_CLIENT_SECRET=${DJANGO_CLIENT_SECRET}${NC}"
echo -e "  ${YELLOW}KEYCLOAK_REALM=${REALM_NAME}${NC}"
echo ""
echo "frontend-pwa/.env.local:"
echo -e "  ${YELLOW}VITE_KEYCLOAK_CLIENT_ID=${CLIENT_ID_REACT}${NC}"
echo -e "  ${YELLOW}VITE_KEYCLOAK_REALM=${REALM_NAME}${NC}"
echo ""
echo -e "${BLUE}🧪 Testar login:${NC}"
echo -e "  Email: ${YELLOW}medico@example.com${NC}"
echo -e "  Senha: ${YELLOW}senha123!@#${NC}"
echo ""
echo -e "${BLUE}🔐 Admin Keycloak:${NC}"
echo -e "  URL: ${YELLOW}${KEYCLOAK_URL}${NC}"
echo -e "  Email: ${YELLOW}${ADMIN_USER}${NC}"
echo -e "  Senha: ${YELLOW}${ADMIN_PASSWORD}${NC}"
echo ""
