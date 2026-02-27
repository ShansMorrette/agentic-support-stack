import os
import re

# Configuración
DOCKER_COMPOSE_PATH = r"d:\01-A L2 Projecto\Sas Agente\agentic-support-stack\docker-compose.yml"
SOP_PATH = r"d:\01-A L2 Projecto\Sas Agente\directivas\despliegue_produccion_SOP.md"
TIMEZONE = "America/Caracas"
LOCALTIME_VOLUME = "/etc/localtime:/etc/localtime:ro"

def update_docker_compose():
    if not os.path.exists(DOCKER_COMPOSE_PATH):
        print(f"Error: No se encontró {DOCKER_COMPOSE_PATH}")
        return

    with open(DOCKER_COMPOSE_PATH, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    new_content = []
    current_service = None
    
    # Este script reconstruye el docker-compose.yml para separar app en backend y frontend
    # y aplicar la configuración regional.
    
    # Estructura simplificada para la reconstrucción
    template = f"""
services:
  # PostgreSQL con pgvector
  db:
    image: ankane/pgvector:latest
    container_name: neural_postgres_db
    environment:
      POSTGRES_USER: ${{POSTGRES_USER}}
      POSTGRES_PASSWORD: ${{POSTGRES_PASSWORD}}
      POSTGRES_DB: ${{POSTGRES_DB}}
      TZ: {TIMEZONE}
    ports:
      - "5433:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
      - {LOCALTIME_VOLUME}
    networks:
      - saas_network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${{POSTGRES_USER}} -d ${{POSTGRES_DB}}"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  # Redis para Celery
  redis:
    image: redis:7-alpine
    container_name: neural_redis_cache
    ports:
      - "${{REDIS_PORT_HOST}}:6379"
    networks:
      - saas_network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  # Backend FastAPI
  app:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: neural_saas_backend
    command: /bin/bash -c "cd /app/backend && uvicorn app.main:app --host 0.0.0.0 --port 8001"
    env_file:
      - .env
    environment:
      - TZ={TIMEZONE}
    ports:
      - "8001:8001"
    volumes:
      - .:/app:cached
      - /app/.venv
      - {LOCALTIME_VOLUME}
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - saas_network
    restart: unless-stopped

  # Frontend Streamlit
  streamlit:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: neural_saas_frontend
    command: /bin/bash -c "cd /app && python3 -m streamlit run frontend/app/main.py --server.port 8502 --server.address 0.0.0.0 --server.headless true"
    env_file:
      - .env
    environment:
      - TZ={TIMEZONE}
    ports:
      - "8502:8502"
    volumes:
      - .:/app:cached
      - /app/.venv
      - {LOCALTIME_VOLUME}
    depends_on:
      app:
        condition: service_started
    networks:
      - saas_network
    restart: unless-stopped

networks:
  saas_network:
    driver: bridge

volumes:
  pgdata:
"""
    with open(DOCKER_COMPOSE_PATH, 'w', encoding='utf-8') as f:
        f.write(template.strip())
    print(f"Docker-compose actualizado exitosamente en {DOCKER_COMPOSE_PATH}")

def update_sop():
    if not os.path.exists(SOP_PATH):
        print(f"Error: No se encontró {SOP_PATH}")
        return

    with open(SOP_PATH, 'r', encoding='utf-8') as f:
        content = f.read()

    # Añadir nota de zona horaria si no existe
    tz_mention = f"\n- **Zona Horaria:** El sistema opera bajo `{TIMEZONE}` por defecto (sincronizado con el host via `/etc/localtime`)."
    
    if "Zona Horaria" not in content:
        # Insertar bajo especificaciones técnicas o similar
        if "## 2. Especificaciones Técnicas" in content:
            updated_content = content.replace("## 2. Especificaciones Técnicas", "## 2. Especificaciones Técnicas" + tz_mention)
        else:
            updated_content = content + "\n\n## 7. Configuración Regional\n" + tz_mention
        
        with open(SOP_PATH, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        print(f"SOP actualizado exitosamente en {SOP_PATH}")
    else:
        print("La mención de Zona Horaria ya existe en el SOP.")

if __name__ == "__main__":
    update_docker_compose()
    update_sop()
