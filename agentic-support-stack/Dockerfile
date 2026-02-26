# Dockerfile Unificado - Backend FastAPI + Frontend Streamlit
FROM python:3.12-slim

# Variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_HOME=/app \
    VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

# Crear directorio de trabajo
WORKDIR $APP_HOME

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Instalar UV usando pip
RUN pip install --no-cache-dir uv

# Copiar código de la aplicación
COPY . .

# Dar permisos a los scripts
RUN chmod +x scripts/*.sh

# Crear venv e instalar dependencias con UV
# uv sync crea el venv automáticamente y usa pyproject.toml + uv.lock
RUN uv sync --frozen

# Exponer puertos (FastAPI: 8000, Streamlit: 8501)
EXPOSE 8000 8501

# Comando por defecto
CMD ["/bin/bash", "./scripts/start.sh"]
