#!/bin/bash

# Script de desarrollo local con UV
# Levanta backend y frontend en paralelo

echo "🚀 Iniciando Neural SaaS Platform en modo desarrollo..."

# Verificar que UV esté instalado
if ! command -v uv &> /dev/null; then
    echo "❌ UV no está instalado. Instalando..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
fi

# Verificar que .env existe
if [ ! -f .env ]; then
    echo "⚠️  Archivo .env no encontrado. Creando desde ejemplo..."
    cp .env.example .env 2>/dev/null || echo "❌ No se encontró .env.example"
    echo "📝 Por favor configura tu GEMINI_API_KEY en .env"
    exit 1
fi

# Sincronizar dependencias
echo "📦 Sincronizando dependencias con UV..."
uv sync

# Crear función para matar procesos al salir
cleanup() {
    echo ""
    echo "🛑 Deteniendo servicios..."
    kill $(jobs -p) 2>/dev/null
    exit 0
}

trap cleanup SIGINT SIGTERM

# Levantar backend en background
echo "📡 Levantando Backend FastAPI en http://localhost:8001..."
uv run uvicorn backend.app.main:app --reload --port 8001 &
BACKEND_PID=$!

# Esperar un poco para que el backend inicie
sleep 2

# Levantar frontend en background
echo "🎨 Levantando Frontend Streamlit en http://localhost:8502..."
uv run streamlit run frontend/app/main.py --server.port 8502 &
FRONTEND_PID=$!

echo ""
echo "✅ Servicios iniciados:"
echo "   - Backend:  http://localhost:8001"
echo "   - API Docs: http://localhost:8001/docs"
echo "   - Frontend: http://localhost:8502"
echo ""
echo "Presiona Ctrl+C para detener todos los servicios"

# Esperar a que terminen los procesos
wait
