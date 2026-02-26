# Dockerfile Unificado - Backend FastAPI + Frontend Streamlit
FROM python:3.12-slim

# Variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_HOME=/app

# Crear directorio de trabajo
WORKDIR $APP_HOME

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias usando pip
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código de la aplicación
COPY . .

# Dar permisos a los scripts
RUN chmod +x scripts/*.sh

# Exponer puertos (FastAPI: 8001, Streamlit: 8502)
EXPOSE 8001 8502

# Comando por defecto
CMD ["/bin/bash", "./scripts/start.sh"]
