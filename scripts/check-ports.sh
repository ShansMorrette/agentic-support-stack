#!/bin/bash

# Script para verificar puertos disponibles antes de levantar Docker

echo "🔍 Verificando puertos para Neural SaaS Platform..."
echo ""

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Función para verificar puerto
check_port() {
    local port=$1
    local service=$2
    
    if ss -tuln | grep -q ":$port "; then
        echo -e "${RED}❌ Puerto $port ($service) está EN USO${NC}"
        
        # Intentar mostrar qué proceso lo usa
        local pid=$(ss -tulnp 2>/dev/null | grep ":$port " | grep -oP 'pid=\K[0-9]+' | head -1)
        if [ -n "$pid" ]; then
            local process=$(ps -p $pid -o comm= 2>/dev/null)
            echo -e "   Usado por: ${YELLOW}$process (PID: $pid)${NC}"
        fi
        return 1
    else
        echo -e "${GREEN}✅ Puerto $port ($service) está DISPONIBLE${NC}"
        return 0
    fi
}

# Leer puertos del .env
if [ -f .env ]; then
    source .env
else
    echo -e "${YELLOW}⚠️  Archivo .env no encontrado, usando puertos por defecto${NC}"
    POSTGRES_PORT_HOST=5433
    REDIS_PORT_HOST=6380
    BACKEND_PORT_HOST=8001
    FRONTEND_PORT_HOST=8502
fi

echo "📋 Puertos configurados:"
echo "   PostgreSQL: $POSTGRES_PORT_HOST"
echo "   Redis: $REDIS_PORT_HOST"
echo "   Backend (FastAPI): $BACKEND_PORT_HOST"
echo "   Frontend (Streamlit): $FRONTEND_PORT_HOST"
echo ""

# Verificar cada puerto
all_available=true

check_port $POSTGRES_PORT_HOST "PostgreSQL" || all_available=false
check_port $REDIS_PORT_HOST "Redis" || all_available=false
check_port $BACKEND_PORT_HOST "FastAPI" || all_available=false
check_port $FRONTEND_PORT_HOST "Streamlit" || all_available=false

echo ""

if [ "$all_available" = true ]; then
    echo -e "${GREEN}✅ Todos los puertos están disponibles!${NC}"
    echo ""
    echo "Puedes levantar el proyecto con:"
    echo "  docker-compose up --build"
    echo ""
    echo "Acceso:"
    echo "  Frontend: http://127.0.0.1:$FRONTEND_PORT_HOST"
    echo "  Backend API: http://127.0.0.1:$BACKEND_PORT_HOST/docs"
    echo "  PostgreSQL: 127.0.0.1:$POSTGRES_PORT_HOST"
    echo "  Redis: 127.0.0.1:$REDIS_PORT_HOST"
    exit 0
else
    echo -e "${RED}❌ Algunos puertos están en uso${NC}"
    echo ""
    echo "Opciones:"
    echo "  1. Detener los servicios que usan esos puertos"
    echo "  2. Cambiar los puertos en .env"
    echo ""
    echo "Para cambiar puertos, edita .env:"
    echo "  nano .env"
    echo ""
    echo "Puertos alternativos disponibles:"
    
    # Sugerir puertos alternativos
    for port in 5434 5435 5436; do
        if ! ss -tuln | grep -q ":$port "; then
            echo "  PostgreSQL: $port"
            break
        fi
    done
    
    for port in 6381 6382 6383; do
        if ! ss -tuln | grep -q ":$port "; then
            echo "  Redis: $port"
            break
        fi
    done
    
    for port in 8002 8003 8004; do
        if ! ss -tuln | grep -q ":$port "; then
            echo "  FastAPI: $port"
            break
        fi
    done
    
    for port in 8503 8504 8505; do
        if ! ss -tuln | grep -q ":$port "; then
            echo "  Streamlit: $port"
            break
        fi
    done
    
    exit 1
fi
