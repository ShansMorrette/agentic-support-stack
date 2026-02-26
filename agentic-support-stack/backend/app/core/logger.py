# backend/app/core/logger.py
"""
Configuración centralizada de logging para la aplicación.

Características:
- Nivel de log configurable desde settings
- Formato estructurado con timestamp ISO 8601
- Salida a stdout (Docker-friendly)
- Opcionalmente a archivo en producción
- Idempotente (puede llamarse múltiples veces)
"""

import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from app.core.config import settings, Environment, LogLevel, BASE_DIR


# ----------------- CONSTANTS -----------------


# Formato de log estructurado
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S%z"

# Directorio de logs (solo para producción)
LOG_DIR = BASE_DIR / "logs"


# ----------------- CUSTOM FORMATTER -----------------


class UTCFormatter(logging.Formatter):
    """Formatter que usa UTC para timestamps consistentes."""
    
    converter = datetime.fromtimestamp
    
    def formatTime(self, record: logging.LogRecord, datefmt: Optional[str] = None) -> str:
        """Formatear timestamp en UTC ISO 8601."""
        ct = datetime.fromtimestamp(record.created, tz=timezone.utc)
        if datefmt:
            return ct.strftime(datefmt)
        return ct.isoformat()


# ----------------- SETUP FUNCTIONS -----------------


def _get_log_level() -> int:
    """Obtener nivel de log desde settings."""
    level_map = {
        LogLevel.DEBUG: logging.DEBUG,
        LogLevel.INFO: logging.INFO,
        LogLevel.WARNING: logging.WARNING,
        LogLevel.ERROR: logging.ERROR,
        LogLevel.CRITICAL: logging.CRITICAL,
    }
    return level_map.get(settings.LOG_LEVEL, logging.INFO)


def _create_console_handler() -> logging.StreamHandler:
    """Crear handler para salida a consola (stdout)."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(UTCFormatter(LOG_FORMAT, LOG_DATE_FORMAT))
    return handler


def _create_file_handler() -> Optional[logging.FileHandler]:
    """
    Crear handler para archivo de logs (solo en producción).
    
    Returns:
        FileHandler o None si no es producción
    """
    if settings.ENVIRONMENT != Environment.PRODUCTION:
        return None
    
    # Crear directorio de logs si no existe
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    # Nombre de archivo con fecha
    log_file = LOG_DIR / f"neural_saas_{datetime.now(timezone.utc).strftime('%Y%m%d')}.log"
    
    handler = logging.FileHandler(log_file, encoding="utf-8")
    handler.setFormatter(UTCFormatter(LOG_FORMAT, LOG_DATE_FORMAT))
    return handler


_logging_configured = False


def setup_logging(force: bool = False) -> None:
    """
    Configurar logging para la aplicación.
    
    Args:
        force: Si True, reconfigura aunque ya esté configurado
        
    Características:
    - Usa nivel de log desde settings.LOG_LEVEL
    - Timestamps en UTC (consistente en cualquier servidor)
    - En producción, también escribe a archivo
    - Idempotente por defecto (solo configura una vez)
    """
    global _logging_configured
    
    if _logging_configured and not force:
        return
    
    # Obtener root logger
    root_logger = logging.getLogger()
    
    # Limpiar handlers existentes (permite reconfiguración)
    root_logger.handlers.clear()
    
    # Configurar nivel
    log_level = _get_log_level()
    root_logger.setLevel(log_level)
    
    # Agregar handler de consola (siempre)
    root_logger.addHandler(_create_console_handler())
    
    # Agregar handler de archivo (solo producción)
    file_handler = _create_file_handler()
    if file_handler:
        root_logger.addHandler(file_handler)
    
    # Reducir verbosidad de librerías externas
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    
    _logging_configured = True
    
    # Log inicial
    logger = logging.getLogger(__name__)
    logger.info(
        f"Logging configurado: level={settings.LOG_LEVEL.value}, "
        f"env={settings.ENVIRONMENT.value}, "
        f"file={'enabled' if file_handler else 'disabled'}"
    )


def get_logger(name: str) -> logging.Logger:
    """
    Obtener logger con nombre específico.
    
    Uso:
        logger = get_logger(__name__)
        logger.info("Mensaje")
    
    Args:
        name: Nombre del logger (típicamente __name__)
        
    Returns:
        Logger configurado
    """
    return logging.getLogger(name)

