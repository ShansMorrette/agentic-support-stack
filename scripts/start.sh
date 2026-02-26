#!/bin/bash

echo "🚀 Iniciando Neural SaaS Platform..."


# Levantar FastAPI en background
echo "📡 Levantando Backend FastAPI en puerto 8001..."
cd /app/backend && uvicorn app.main:app --host 0.0.0.0 --port 8001 &

# Esperar un poco para que FastAPI inicie
sleep 5

# Levantar Streamlit en foreground
echo "🎨 Levantando Frontend Streamlit en puerto 8502..."
cd /app && streamlit run frontend/app/main.py --server.port 8502 --server.address 0.0.0.0 --server.headless true

# Si Streamlit termina, matar FastAPI también
kill $(jobs -p)
