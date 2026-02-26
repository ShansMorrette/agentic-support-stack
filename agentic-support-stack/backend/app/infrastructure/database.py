# backend/app/infrastructure/database.py
"""
Configuración de base de datos PostgreSQL con SQLAlchemy async.

Proporciona:
- Engine y session factory
- Dependency para FastAPI
- Inicialización de tablas y datos por defecto
"""

import logging
from enum import IntEnum
from typing import AsyncGenerator, TypedDict

from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings, Environment
from app.domain.models import Base, Role

logger = logging.getLogger(__name__)


# ----------------- ROLE DEFINITIONS -----------------


class RoleID(IntEnum):
    """IDs de roles del sistema (evita magic numbers)."""
    FREE = 1
    PRO = 2
    CUSTOM = 3
    ADMIN = 4


class RoleName:
    """Nombres de roles del sistema (evita magic strings)."""
    FREE = "free"
    PRO = "pro"
    CUSTOM = "custom"
    ADMIN = "admin"


class DefaultRoleData(TypedDict):
    """Definición de tipo para los datos de rol por defecto."""
    id: RoleID
    name: str
    description: str
    max_analyses_per_day: int


# Configuración de roles por defecto
DEFAULT_ROLES: list[DefaultRoleData] = [
    {"id": RoleID.FREE, "name": RoleName.FREE, "description": "Plan gratuito", "max_analyses_per_day": 5},
    {"id": RoleID.PRO, "name": RoleName.PRO, "description": "Plan profesional", "max_analyses_per_day": 100},
    {"id": RoleID.CUSTOM, "name": RoleName.CUSTOM, "description": "Plan con API key propia", "max_analyses_per_day": 0},
    {"id": RoleID.ADMIN, "name": RoleName.ADMIN, "description": "Administrador", "max_analyses_per_day": 0},
]


# ----------------- POOL CONFIG -----------------


# Pool de conexiones configurable según entorno
_POOL_SIZE = 10 if settings.ENVIRONMENT == Environment.PRODUCTION else 5
_MAX_OVERFLOW = 20 if settings.ENVIRONMENT == Environment.PRODUCTION else 10


# ----------------- ENGINE -----------------


engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_size=_POOL_SIZE,
    max_overflow=_MAX_OVERFLOW,
    future=True,  # SQLAlchemy 2.0 style
)


# ----------------- SESSION FACTORY -----------------


AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


# ----------------- DEPENDENCY -----------------


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency para obtener sesión de DB.
    
    Uso:
        @router.get("/")
        async def endpoint(db: AsyncSession = Depends(get_db)):
            ...
    
    El context manager maneja automáticamente:
    - Commit en caso de éxito
    - Rollback en caso de excepción (con logging)
    - Cierre de sesión al finalizar
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            logger.error(f"Database transaction failed: {type(e).__name__}: {e}")
            await session.rollback()
            raise


# ----------------- INIT DB -----------------


async def init_db() -> None:
    """Crear todas las tablas en la base de datos."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("✅ Base de datos inicializada")


async def create_default_roles(session: AsyncSession) -> None:
    """
    Crear roles por defecto si no existen, usando UPSERT (ON CONFLICT DO NOTHING).
    
    Los IDs son fijos intencionalmente para mantener consistencia
    entre entornos y permitir referencias directas (ej: RoleID.FREE).
    Esta función es idempotente: puede ejecutarse múltiples veces sin efectos secundarios
    y solo insertará los roles que no existan.
    """
    # Preparar los datos para la inserción, convirtiendo RoleID enum a valor entero
    roles_to_insert = [
        {
            "id": role_data["id"].value,
            "name": role_data["name"],
            "description": role_data["description"],
            "max_analyses_per_day": role_data["max_analyses_per_day"],
        }
        for role_data in DEFAULT_ROLES
    ]

    # UPSERT: INSERT ... ON CONFLICT DO NOTHING (idempotente)
    stmt = insert(Role).values(roles_to_insert).on_conflict_do_nothing(index_elements=["id"])
    result = await session.execute(stmt)

    inserted_count = result.rowcount
    if inserted_count > 0:
        await session.commit()
        logger.info(f"✅ {inserted_count} roles por defecto creados")
    else:
        logger.debug("Todos los roles por defecto ya existen, saltando creación")

