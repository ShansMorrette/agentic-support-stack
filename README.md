# 🧠 Neural Code Analyzer & Smart Attention System

**Plataforma SaaS Dual: Análisis de código Python y Gestión Inteligente de Atención al Cliente**  
*Gemini 2.5 Flash · FastAPI · Streamlit · PostgreSQL*

---

## 🚀 Comenzar en 60 Segundos

```bash
# 1. Clonar y configurar
git clone https://github.com/ShansMorrette/agentic-support-stack.git
cd project_saas
cp .env.example .env

# 2. Configurar API Key (obtener en: https://aistudio.google.com/)
echo "GEMINI_API_KEY=tu_api_key_aqui" >> .env

# 3. Ejecutar
docker compose up -d

# 4. ¡Listo!
# 🌐 App: http://localhost:8502
# 📚 API Docs: http://localhost:8001/docs
```

## ✨ ¿Qué Puede Hacer?

### 🔍 Análisis Inteligente de Código

- **🐛 Bugs potenciales** - Detecta errores antes de producción.
- **👃 Code smells** - Identifica malas prácticas.
- **⚡ Optimizaciones** - Sugiere mejoras de rendimiento.
- **📊 Score 0-100** - Calificación automática de calidad.

### 🤖 Atención Inteligente (WebLanMasters)

- **🧠 Clasificación Automática** - Gemini clasifica mensajes en *Ventas*, *Soporte* o *General*.
- **� Gestión de Tickets** - Generación automática de tickets con prioridad y resumen.
- **👤 Perfiles de Clientes** - Identificación y registro automático de nuevos prospectos.
- **💬 Historial Centralizado** - Almacenamiento de conversaciones para seguimiento.

### � Dashboard Interactivo

- **� Métricas en tiempo real** - Estadísticas de uso y calidad de código.
- **🚀 Panel de Atención** - Vista dual de "Prospectos (Ventas)" y "Soporte (Tickets)".
- **🏆 Sistema de logros** - Gamificación para desarrolladores.
- **� Exportar datos** - CSV/JSON para análisis externo.

## 🏗️ Arquitectura

```text
project_saas/
├── backend/app/          # FastAPI + PostgreSQL
│   ├── core/            # Configuración y seguridad
│   ├── domain/          # Modelos de datos (User, Analysis, Client, Ticket, Conversation)
│   ├── application/     # Lógica (AnalysisService, AtencionService)
│   ├── infrastructure/  # Gemini Client, Database config
│   └── web/routers/     # Endpoints (analysis, auth, atencion)
├── frontend/app/        # Streamlit Dashboard
│   ├── main.py          # Aplicación principal y Vistas de Atención
│   └── pages/           # Vistas adicionales (login, dashboard de código)
├── deploy/              # Scripts de deployment
└── docker-compose.yml   # Orquestación containers
```

**Stack Tecnológico:** Python 3.12, FastAPI, Streamlit, Gemini 2.5 Flash, PostgreSQL, Redis, Docker.

## ⚙️ Configuración Rápida

### Variables Esenciales (.env)

```bash
# Obtener en: https://aistudio.google.com/
GEMINI_API_KEY=tu_clave_gemini_aqui

# Generar con: python -c "import secrets; print(secrets.token_urlsafe(64))"
JWT_SECRET_KEY=clave_jwt_super_secreta

# Base de datos (automático con Docker)
DATABASE_URL=postgresql+asyncpg://user:pass@db:5432/neuraldb
```

## 🔌 Uso de la API

### 1. Análisis de Código

```python
url = "http://localhost:8001/api/analysis"
headers = {"Authorization": "Bearer tu_jwt_token"}
data = {"code": "def ejemplo(): pass"}
response = requests.post(url, json=data, headers=headers)
```

### 2. Chat de Atención

```python
url = "http://localhost:8001/api/chat/atencion"
headers = {"Authorization": "Bearer tu_jwt_token"}
data = {"text": "Hola, necesito soporte con mi servidor"}
response = requests.post(url, json=data, headers=headers)
```

### Endpoints Principales

- `POST /api/analysis` - Analizar código Python.
- `POST /api/chat/atencion` - Procesar mensaje de atención.
- `GET /api/atencion/prospects` - Listar prospectos de ventas.
- `GET /api/atencion/tickets` - Listar tickets de soporte.
- `POST /api/auth/login` - Iniciar sesión.

## 🚀 Deployment

- **Desarrollo:** `docker compose up -d`
- **Producción:** `docker compose -f docker-compose.prod.yml up -d`

## 🛠️ Estado del Proyecto

✅ **v1.1.0 - Smart Attention Module Integrado**

- ✅ Análisis Python con Gemini 2.5
- ✅ Sistema de Tickets y Prospectos
- ✅ Dashboard Dual (Código + Atención)
- ✅ Auth JWT + Security

---
📄 **Licencia:** MIT License - Neural Code Analyzer & Smart Attention System  
¿Preguntas? ✉️ <gompatri@gmail.com>
