# 📜 Scripts - Neural SaaS Platform

Esta carpeta contiene todos los scripts de utilidad del proyecto.

## 📋 Scripts Disponibles

### 🚀 `start.sh`
**Propósito**: Levantar backend (FastAPI) y frontend (Streamlit) en Docker.

**Uso**:
```bash
# Dentro de Docker (automático)
docker-compose up

# O directamente
./scripts/start.sh
```

**Qué hace**:
1. Levanta FastAPI en puerto 8000 (background)
2. Levanta Streamlit en puerto 8501 (foreground)
3. Si Streamlit termina, mata FastAPI también

---

### 💻 `dev.sh`
**Propósito**: Levantar backend y frontend en modo desarrollo local (sin Docker).

**Uso**:
```bash
# Directo
./scripts/dev.sh

# O con Makefile
make dev
```

**Qué hace**:
1. Verifica que UV esté instalado
2. Verifica que `.env` exista
3. Sincroniza dependencias con `uv sync`
4. Levanta backend en puerto 8000 (background)
5. Levanta frontend en puerto 8501 (background)
6. Muestra URLs de acceso
7. Espera Ctrl+C para detener ambos servicios

**Requisitos**:
- UV instalado
- Archivo `.env` configurado

---

### 🔍 `check-ports.sh`
**Propósito**: Verificar que los puertos necesarios estén disponibles antes de levantar servicios.

**Uso**:
```bash
# Directo
./scripts/check-ports.sh

# O con Makefile
make check-ports

# Automático al hacer
make docker-up
```

**Qué hace**:
1. Lee puertos del `.env`
2. Verifica si cada puerto está disponible
3. Si está en uso, muestra qué proceso lo usa
4. Sugiere puertos alternativos si hay conflictos
5. Retorna exit code 0 si todo OK, 1 si hay conflictos

**Puertos verificados**:
- PostgreSQL (default: 5433)
- Redis (default: 6380)
- FastAPI Backend (default: 8001)
- Streamlit Frontend (default: 8502)

---

## 🛠️ Crear Nuevos Scripts

### Convenciones

1. **Naming**: `nombre-descriptivo.sh` o `nombre_descriptivo.py`
2. **Permisos**: Siempre hacer ejecutable con `chmod +x`
3. **Shebang**: Siempre incluir en la primera línea
4. **Documentación**: Agregar comentarios al inicio del script

### Template para Bash

```bash
#!/bin/bash

# Nombre del Script
# Descripción: Qué hace este script
# Uso: ./scripts/nombre-script.sh [argumentos]

set -e  # Salir si hay error

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🚀 Iniciando script..."

# Tu código aquí

echo -e "${GREEN}✅ Script completado${NC}"
```

### Template para Python

```python
#!/usr/bin/env python3
"""
Nombre del Script

Descripción: Qué hace este script
Uso: python scripts/nombre_script.py [argumentos]
"""

import sys
from pathlib import Path

def main() -> int:
    """Función principal."""
    print("🚀 Iniciando script...")
    
    # Tu código aquí
    
    print("✅ Script completado")
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

---

## 📚 Scripts Futuros (Planeados)

### `validate-env.sh`
Validar que el `.env` tenga todas las variables necesarias.

### `generate-secrets.py`
Generar valores seguros para JWT_SECRET_KEY, POSTGRES_PASSWORD, etc.

### `backup-db.sh`
Hacer backup de la base de datos PostgreSQL.

### `restore-db.sh`
Restaurar backup de la base de datos.

### `deploy-orangepi.sh`
Automatizar deploy en OrangePi.

### `run-tests.sh`
Ejecutar todos los tests con cobertura y reportes.

### `lint-all.sh`
Ejecutar linting completo (ruff, black, mypy).

### `update-deps.sh`
Actualizar todas las dependencias y generar nuevo uv.lock.

---

## 🚨 Troubleshooting

### Script no ejecuta

```bash
# Dar permisos de ejecución
chmod +x scripts/nombre-script.sh

# Verificar shebang
head -1 scripts/nombre-script.sh
```

### Error: "command not found"

```bash
# Ejecutar desde raíz del proyecto
cd /path/to/project_saas
./scripts/nombre-script.sh

# O usar ruta absoluta
/path/to/project_saas/scripts/nombre-script.sh
```

### Error: ".env not found"

```bash
# Verificar que .env existe
ls -la .env

# Copiar desde ejemplo
cp .env.example .env
```

---

## ✅ Buenas Prácticas

### DO ✅

- Usar `set -e` en scripts bash (salir si hay error)
- Agregar colores para mejor UX
- Validar requisitos al inicio
- Mostrar mensajes claros de progreso
- Documentar cada script en este README
- Hacer scripts idempotentes (se pueden ejecutar múltiples veces)

### DON'T ❌

- No hardcodear valores (usar `.env`)
- No asumir que dependencias están instaladas
- No usar rutas relativas complejas
- No ignorar errores
- No crear scripts sin documentación

---

**Última actualización:** Enero 2025
