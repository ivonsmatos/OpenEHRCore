#!/bin/bash
# quick-start.sh - Iniciar OpenEHRCore completo em um comando

echo "🚀 OpenEHRCore Quick Start"
echo ""

# Cores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}📦 Passo 1: Infraestrutura (Docker Compose)${NC}"
echo "  → Iniciando HAPI FHIR, PostgreSQL e Keycloak..."
cd docker
docker-compose up -d > /dev/null 2>&1
cd ..
echo -e "  ${GREEN}✓ Aguardando serviços ficarem saudáveis (30s)...${NC}"
sleep 30

echo ""
echo -e "${BLUE}🐍 Passo 2: Backend Django${NC}"
echo "  → Instalando dependências Python..."
cd backend-django
python -m venv venv > /dev/null 2>&1
source venv/bin/activate 2>/dev/null || venv\Scripts\activate.bat
pip install -r requirements.txt > /dev/null 2>&1
echo "  → Iniciando servidor Django (porta 8000)..."
python manage.py runserver &
DJANGO_PID=$!
cd ..
sleep 5

echo ""
echo -e "${BLUE}📱 Passo 3: Frontend React${NC}"
echo "  → Instalando dependências Node.js..."
cd frontend-pwa
npm install > /dev/null 2>&1
echo "  → Iniciando Vite dev server (porta 5173)..."
npm run dev &
VITE_PID=$!
cd ..

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}✅ OpenEHRCore iniciado com sucesso!${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📍 URLs:"
echo "  • Frontend:   ${GREEN}http://localhost:5173${NC}"
echo "  • Backend:    ${GREEN}http://localhost:8000${NC}"
echo "  • HAPI FHIR:  ${GREEN}http://localhost:8080/fhir${NC}"
echo "  • Keycloak:   ${GREEN}http://localhost:8180${NC}"
echo ""
echo "📚 Documentação:"
echo "  • Setup:      ./docs/SETUP.md"
echo "  • Arquitetura: ./docs/ARCHITECTURE.md"
echo "  • Design:     ./docs/DESIGN_SYSTEM.md"
echo ""
echo "🧪 Validar stack:"
echo "  $ bash scripts/validate-stack.sh"
echo ""
echo "Press Ctrl+C para parar"
wait
