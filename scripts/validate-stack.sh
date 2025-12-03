#!/bin/bash
# validate-stack.sh - Valida se a stack OpenEHRCore está saudável

set -e

echo "🔍 Validando OpenEHRCore Stack..."
echo ""

# Cores para output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Função para validar endpoint HTTP
check_endpoint() {
    local url=$1
    local name=$2
    local expected_status=${3:-200}

    echo -n "  ⏳ Testando $name... "

    response=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "000")

    if [ "$response" = "$expected_status" ]; then
        echo -e "${GREEN}✓ OK (HTTP $response)${NC}"
        return 0
    else
        echo -e "${RED}✗ FAILED (HTTP $response, esperado $expected_status)${NC}"
        return 1
    fi
}

# Função para validar JSON response
check_json_endpoint() {
    local url=$1
    local name=$2

    echo -n "  ⏳ Testando $name... "

    response=$(curl -s "$url" 2>/dev/null)

    if echo "$response" | jq . > /dev/null 2>&1; then
        echo -e "${GREEN}✓ OK${NC}"
        return 0
    else
        echo -e "${RED}✗ FAILED (resposta não é JSON)${NC}"
        return 1
    fi
}

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📦 Infraestrutura (Docker Compose)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Verificar HAPI FHIR
check_endpoint "http://localhost:8080/fhir/metadata" "HAPI FHIR Server" || exit 1
check_json_endpoint "http://localhost:8080/fhir/metadata" "HAPI FHIR CapabilityStatement" || exit 1

# Verificar Keycloak
check_endpoint "http://localhost:8180/health/ready" "Keycloak" || exit 1

# Verificar PostgreSQL
echo -n "  ⏳ Testando PostgreSQL... "
if psql -h localhost -U fhir_user -d hapi_fhir -c "SELECT 1" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ OK${NC}"
else
    echo -e "${RED}✗ FAILED (não foi possível conectar)${NC}"
    exit 1
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🐍 Backend (Django)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Verificar Django health check
check_endpoint "http://localhost:8000/api/v1/health/" "Django Health Check" || exit 1
check_json_endpoint "http://localhost:8000/api/v1/health/" "Django FHIR Connection" || exit 1

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📱 Frontend (React)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Verificar Vite dev server
check_endpoint "http://localhost:5173/" "Vite Dev Server" || exit 1

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🧪 Teste de Integração"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo "  ⏳ Criando paciente de teste no FHIR..."

RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/patients/ \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Test",
    "last_name": "Integration",
    "birth_date": "1990-01-01",
    "cpf": "12345678901",
    "gender": "male"
  }')

PATIENT_ID=$(echo "$RESPONSE" | jq -r '.id' 2>/dev/null || echo "")

if [ -n "$PATIENT_ID" ] && [ "$PATIENT_ID" != "null" ]; then
    echo -e "  ${GREEN}✓ Paciente criado com sucesso: $PATIENT_ID${NC}"

    echo "  ⏳ Recuperando paciente do FHIR..."
    GET_RESPONSE=$(curl -s http://localhost:8080/fhir/Patient/$PATIENT_ID)

    if echo "$GET_RESPONSE" | jq . > /dev/null 2>&1; then
        NAME=$(echo "$GET_RESPONSE" | jq -r '.name[0].given[0]' 2>/dev/null || echo "")
        if [ -n "$NAME" ] && [ "$NAME" != "null" ]; then
            echo -e "  ${GREEN}✓ Paciente recuperado: $NAME${NC}"
        else
            echo -e "  ${YELLOW}⚠ Paciente recuperado mas nome não encontrado${NC}"
        fi
    else
        echo -e "  ${RED}✗ FAILED ao recuperar paciente${NC}"
        exit 1
    fi
else
    echo -e "  ${RED}✗ FAILED ao criar paciente${NC}"
    echo "  Resposta: $RESPONSE"
    exit 1
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}✅ Stack OpenEHRCore validado com sucesso!${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📚 Próximos passos:"
echo "  1. Acessar frontend em ${GREEN}http://localhost:5173${NC}"
echo "  2. Visualizar paciente criado em PatientDetail"
echo "  3. Explorar endpoints em ${GREEN}http://localhost:8000/api/v1${NC}"
echo "  4. Consultar docs em ${GREEN}./docs${NC}"
echo ""
