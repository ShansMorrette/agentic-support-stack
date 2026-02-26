# backend/app/core/config.py
"""
Configuración central de la aplicación.

Carga variables de entorno desde .env y proporciona valores por defecto.
Usa pydantic-settings para validación automática de tipos.
"""

from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# ----------------- CONSTANTS -----------------


BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent  # project_saas/


class Environment(str, Enum):
    """Entornos válidos de la aplicación."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class LogLevel(str, Enum):
    """Niveles de log válidos."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


# ----------------- SETTINGS -----------------


class Settings(BaseSettings):
    """
    Configuración central de la aplicación SaaS.
    
    Todas las variables se cargan desde .env o variables de entorno.
    Los campos con `...` son obligatorios.
    """

    # --- Proyecto ---
    PROJECT_NAME: str = "Neural SaaS Platform"
    PROJECT_DESCRIPTION: str = "Plataforma SaaS de Agentes de IA para Python"
    PROJECT_VERSION: str = "0.1.0"
    ENVIRONMENT: Environment = Environment.DEVELOPMENT

    # --- FastAPI ---
    HOST: str = "0.0.0.0"
    PORT: int = 8001
    DEBUG: bool = True

    # --- Database ---
    DATABASE_URL: str = Field(..., description="URL de conexión a PostgreSQL")
    POSTGRES_USER: str = Field(default="neural_user")
    POSTGRES_PASSWORD: str = Field(..., description="Password de PostgreSQL")
    POSTGRES_DB: str = Field(default="neural_saas_db")
    POSTGRES_HOST: str = Field(default="db")
    POSTGRES_PORT: int = Field(default=5432)

    # --- Seguridad JWT ---
    JWT_SECRET_KEY: str = Field(..., description="Clave secreta para JWT")
    JWT_ALGORITHM: str = Field(default="HS256")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60)

    # --- API Keys ---
    GEMINI_API_KEY: str = Field(..., description="API Key de Gemini")
    GEMINI_MODEL: str = Field(default="gemini-2.5-flash")

    # --- Redis ---
    REDIS_HOST: str = Field(default="redis")
    REDIS_PORT: int = Field(default=6379)
    
    @property
    def REDIS_URL(self) -> str:
        """URL de Redis construida dinámicamente desde host y puerto."""
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"

    # --- Celery ---
    @property
    def CELERY_BROKER_URL(self) -> str:
        """URL del broker de Celery (usa Redis)."""
        return self.REDIS_URL
    
    @property
    def CELERY_RESULT_BACKEND(self) -> str:
        """URL del backend de resultados de Celery (usa Redis)."""
        return self.REDIS_URL

    # --- CORS ---
    ALLOWED_ORIGINS: str = Field(
        default="http://localhost:8501,http://localhost:8502,http://localhost:3000",
        description="Orígenes permitidos para CORS (separados por coma)",
    )
    
    @property
    def allowed_origins_list(self) -> List[str]:
        """Lista de orígenes permitidos para CORS."""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]

    # --- Rate Limiting ---
    RATE_LIMIT_PER_MINUTE: int = 60

    # --- Logging ---
    LOG_LEVEL: LogLevel = LogLevel.INFO

    # --- Embeddings / Vector DB ---
    VECTOR_DIM: int = 768  # Gemini embedding dimension
    
    @property
    def VECTOR_INDEX_PATH(self) -> str:
        """Ruta al índice de vectores."""
        return str(BASE_DIR / "data" / "vector_index.pkl")

    # --- Validadores ---
    @field_validator("ENVIRONMENT", mode="before")
    @classmethod
    def validate_environment(cls, v: str) -> Environment:
        """Validar y convertir string a Environment enum."""
        if isinstance(v, Environment):
            return v
        try:
            return Environment(v.lower())
        except ValueError:
            valid = [e.value for e in Environment]
            raise ValueError(f"ENVIRONMENT debe ser uno de: {valid}")

    @field_validator("LOG_LEVEL", mode="before")
    @classmethod
    def validate_log_level(cls, v: str) -> LogLevel:
        """Validar y convertir string a LogLevel enum."""
        if isinstance(v, LogLevel):
            return v
        try:
            return LogLevel(v.upper())
        except ValueError:
            valid = [e.value for e in LogLevel]
            raise ValueError(f"LOG_LEVEL debe ser uno de: {valid}")

    # --- Pydantic Config ---
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


# ----------------- SINGLETON -----------------


@lru_cache
def get_settings() -> Settings:
    """
    Obtener instancia de Settings (singleton con caché).
    
    Usar esta función en lugar de acceder a `settings` directamente
    permite mejor testabilidad y lazy loading.
    """
    return Settings()


# Instancia global para compatibilidad con código existente
settings = get_settings()

