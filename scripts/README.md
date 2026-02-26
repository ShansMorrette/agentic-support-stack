# 📜 Scripts - Neural SaaS Platform & Smart Attention System

Esta carpeta contiene todos los scripts de utilidad del proyecto para facilitar el desarrollo, despliegue y verificación.

## 📋 Scripts Disponibles

### 🚀 `start.sh` (Producción/Docker)

**Propósito**: Levantar backend (FastAPI) y frontend (Streamlit) dentro del contenedor Docker.

**Uso**:

- Ejecutado automáticamente por `docker-compose up`.
- Comando manual interno: `./scripts/start.sh`

**Configuración de Puertos**:

- **Backend**: Puerto `8001`
- **Frontend**: Puerto `8502`

---

### 💻 `dev.sh` (Desarrollo Local)

**Propósito**: Levantar backend y frontend en modo desarrollo local utilizando `uv` (sin Docker).

**Uso**:

```bash
./scripts/dev.sh
```

**Qué hace**:

1. Verifica la instalación de **UV**.
2. Asegura la existencia de un archivo `.env`.
3. Sincroniza dependencias con `uv sync`.
4. Levanta backend en puerto `8001`.
5. Levanta frontend en puerto `8502`.
6. Monitorea ambos procesos y termina limpiamente con `Ctrl+C`.

---

### 🔍 `check-ports.sh`

**Propósito**: Verificar que los puertos necesarios estén disponibles antes de levantar la infraestructura.

**Uso**:

```bash
./scripts/check-ports.sh
```

**Puertos Validados**:

- **PostgreSQL**: `5433` (Host)
- **Redis**: `6380` (Host)
- **FastAPI**: `8001`
- **Streamlit**: `8502`

---

### 🧪 `weblan_sanity.py`

**Propósito**: Simulador de pruebas "Sanity" para verificar el flujo completo de atención (WebLanMasters).

**Uso**:

```bash
py scripts/weblan_sanity.py
```

**Qué hace**:

1. Simula mensajes de clientes (Ventas, Soporte, General).
2. Verifica la clasificación por IA (Gemini).
3. Confirma la creación de tickets y prospectos en la base de datos.
4. Valida la respuesta del orquestador.

---

## 🛠️ Convenciones y Mejores Prácticas

1. **Naming**: Usar `guiones-bajos` para Python y `guiones-medios` para Bash.
2. **Permisos**: Asegurar permisos de ejecución con `chmod +x scripts/*.sh`.
3. **Configuración**: NO hardcodear variables; usar siempre `source .env`.
4. **Idempotencia**: Los scripts deben poder ejecutarse varias veces sin causar efectos secundarios dañinos.

---

**Última actualización:** Febrero 2026
