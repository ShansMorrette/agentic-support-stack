.PHONY: help install dev docker-build docker-up docker-down test lint format clean

help: ## Mostrar esta ayuda
	@echo "Comandos disponibles:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Instalar dependencias con UV
	@echo "📦 Instalando dependencias..."
	uv sync

install-dev: ## Instalar dependencias de desarrollo
	@echo "📦 Instalando dependencias de desarrollo..."
	uv sync --extra dev

dev: ## Levantar en modo desarrollo (backend + frontend)
	@echo "🚀 Iniciando modo desarrollo..."
	./scripts/dev.sh

backend: ## Levantar solo backend
	@echo "📡 Levantando backend..."
	uv run uvicorn backend.app.main:app --reload --port 8001

frontend: ## Levantar solo frontend
	@echo "🎨 Levantando frontend..."
	uv run streamlit run frontend/app/main.py --server.port 8502

docker-build: ## Construir imagen Docker
	@echo "🐳 Construyendo imagen Docker..."
	docker build -t neural-saas .

check-ports: ## Verificar puertos disponibles
	@echo "🔍 Verificando puertos..."
	./scripts/check-ports.sh

docker-up: check-ports ## Levantar con Docker Compose
	@echo "🐳 Levantando servicios con Docker Compose..."
	docker-compose up --build

docker-down: ## Detener Docker Compose
	@echo "🛑 Deteniendo servicios..."
	docker-compose down

docker-logs: ## Ver logs de Docker Compose
	docker-compose logs -f

test: ## Ejecutar tests
	@echo "🧪 Ejecutando tests..."
	uv run pytest tests/ -v

test-cov: ## Ejecutar tests con cobertura
	@echo "🧪 Ejecutando tests con cobertura..."
	uv run pytest tests/ --cov=backend --cov=frontend --cov-report=html

lint: ## Ejecutar linting (Ruff)
	@echo "🔍 Ejecutando linting..."
	uv run ruff check .

format: ## Formatear código (Black + Ruff)
	@echo "✨ Formateando código..."
	uv run black .
	uv run ruff check --fix .

typecheck: ## Verificar tipos (mypy)
	@echo "🔎 Verificando tipos..."
	uv run mypy backend/ frontend/

clean: ## Limpiar archivos temporales
	@echo "🧹 Limpiando archivos temporales..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.log" -delete
	rm -rf htmlcov/ .coverage

lock: ## Actualizar uv.lock
	@echo "🔒 Actualizando uv.lock..."
	uv lock

add: ## Agregar dependencia (uso: make add PKG=nombre-paquete)
	@echo "➕ Agregando $(PKG)..."
	uv add $(PKG)

add-dev: ## Agregar dependencia de desarrollo (uso: make add-dev PKG=nombre-paquete)
	@echo "➕ Agregando $(PKG) como dev..."
	uv add --dev $(PKG)

update: ## Actualizar todas las dependencias
	@echo "⬆️  Actualizando dependencias..."
	uv lock --upgrade

orangepi: ## Preparar para deploy en OrangePi
	@echo "🍊 Preparando para OrangePi..."
	@echo "1. Asegúrate de tener Docker instalado en OrangePi"
	@echo "2. Copia el proyecto: scp -r . user@orangepi-ip:/home/user/neural-saas"
	@echo "3. SSH a OrangePi: ssh user@orangepi-ip"
	@echo "4. Ejecuta: cd neural-saas && docker-compose up --build"
