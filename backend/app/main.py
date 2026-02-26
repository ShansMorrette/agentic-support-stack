# backend/app/main.py
"""
Punto de entrada principal del backend FastAPI.

Configura la aplicación, middlewares, routers y eventos de ciclo de vida.
"""

import logging
import sys
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings, Environment
from app.core.logger import setup_logging
from app.infrastructure.database import AsyncSessionLocal, create_default_roles, init_db
from app.web.routers import analysis_router, auth_router, embeddings_router, health_router, atencion_router

# Inicializar logging
setup_logging()
logger = logging.getLogger(__name__)


# ----------------- CORS CONFIG -----------------


# En desarrollo: permisivo para facilitar pruebas
# En producción: restrictivo por seguridad
_is_production = settings.ENVIRONMENT == Environment.PRODUCTION

_ALLOWED_METHODS = (
    ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]
    if _is_production
    else ["*"]
)

_ALLOWED_HEADERS = (
    ["Content-Type", "Authorization", "Accept"]
    if _is_production
    else ["*"]
)


# ----------------- LIFESPAN -----------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Maneja el ciclo de vida de la aplicación (startup/shutdown).
    
    Reemplaza los decoradores @app.on_event deprecados en FastAPI.
    """
    # --- STARTUP ---
    logger.info(f"🚀 Iniciando {settings.PROJECT_NAME} v{settings.PROJECT_VERSION}...")
    logger.info(f"   Entorno: {settings.ENVIRONMENT.value}")
    
    try:
        await init_db()
        
        async with AsyncSessionLocal() as session:
            await create_default_roles(session)
        
        logger.info("✅ Base de datos lista")
    except Exception as e:
        logger.error(f"❌ Error crítico de base de datos: {e}", exc_info=True)
        
        if _is_production:
            logger.critical("🛑 No se puede iniciar sin base de datos en producción")
            sys.exit(1)
        else:
            logger.warning("⚠️ Continuando sin DB - las rutas que requieren DB fallarán")
    
    logger.info(f"✅ {settings.PROJECT_NAME} iniciado correctamente")
    
    yield  # La aplicación corre aquí
    
    # --- SHUTDOWN ---
    logger.info(f"🛑 {settings.PROJECT_NAME} detenido")


# ----------------- APP -----------------


app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.PROJECT_VERSION,
    docs_url=None if _is_production else "/docs",
    redoc_url=None if _is_production else "/redoc",
    lifespan=lifespan,
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=_ALLOWED_METHODS,
    allow_headers=_ALLOWED_HEADERS,
)

# Incluir routers
app.include_router(health_router.router)
app.include_router(atencion_router.router)
app.include_router(auth_router.router)
app.include_router(analysis_router.router)
app.include_router(embeddings_router.router)


# ----------------- ENTRYPOINT -----------------


if __name__ == "__main__":
    is_dev = settings.ENVIRONMENT == Environment.DEVELOPMENT
    
    uvicorn.run(
        "app.main:app",
        host=getattr(settings, "HOST", "0.0.0.0"),
        port=settings.PORT,
        reload=is_dev,
        log_level="debug" if is_dev else "info",
    )
