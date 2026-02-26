# backend/app/web/routers/analysis_router.py
"""
Router para análisis de código Python con IA.

Endpoints:
- POST /api/analysis/ - Analizar código
- GET /api/analysis/stats - Estadísticas del usuario
- GET /api/analysis/history - Historial de análisis
"""

import logging
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.analysis_service import AnalysisService
from app.domain.models import User
from app.infrastructure.database import get_db
from app.infrastructure.encryption import get_encryption_service
from app.web.routers.auth_router import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analysis", tags=["Análisis de Código"])


# ----------------- HELPERS -----------------


def _get_user_api_key(user: Optional[User]) -> Optional[str]:
    """
    Obtiene y desencripta la API key del usuario si existe.
    
    Args:
        user: Usuario autenticado o None
        
    Returns:
        API key desencriptada o None (usará key del sistema)
    """
    if not user or not user.gemini_api_key_encrypted:
        return None
    
    try:
        encryption = get_encryption_service()
        api_key = encryption.decrypt(user.gemini_api_key_encrypted)
        # Log sin PII - solo user_id, no email
        logger.info(f"🔓 API key desencriptada para user_id: {user.id}")
        return api_key
    except Exception as e:
        logger.error(f"Error al desencriptar API key para user_id {user.id}: {e}")
        # Fallback a key del sistema (manejado por AnalysisService)
        return None


# ----------------- SCHEMAS -----------------


class AnalysisRequest(BaseModel):
    """Request para análisis de código."""

    codigo: str = Field(..., description="Código Python a analizar", min_length=1, max_length=40000)

    class Config:
        json_schema_extra = {"example": {"codigo": "def suma(a, b):\n    return a + b"}}


class AnalysisResponse(BaseModel):
    """Response del análisis de código."""

    success: bool
    analisis: Optional[str] = None
    error: Optional[str] = None
    codigo: str
    usuario_id: Optional[int] = None
    timestamp: datetime  # Cambiado de str a datetime para mejor serialización
    modelo_usado: Optional[str] = None
    analysis_id: Optional[int] = None

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class StatsResponse(BaseModel):
    """Response de estadísticas del usuario."""

    total_analisis: int
    analisis_hoy: int
    score_promedio: float
    limite_diario: int
    analisis_restantes: int


class HistoryItem(BaseModel):
    """Item del historial de análisis."""

    id: int
    codigo_snippet: str
    score: Optional[int] = None
    created_at: datetime
    modelo_usado: Optional[str] = None

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class HistoryResponse(BaseModel):
    """Response del historial de análisis."""

    items: List[HistoryItem]
    total: int
    limit: int
    offset: int


# ----------------- ENDPOINTS -----------------


@router.post("/", response_model=AnalysisResponse, status_code=status.HTTP_200_OK)
async def analizar_codigo(
    request: AnalysisRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
) -> AnalysisResponse:
    """
    Analiza código Python y retorna sugerencias de mejora.

    - **Autenticado**: Guarda análisis en historial, usa API key del usuario si tiene
    - **Anónimo**: Análisis sin guardar (limitado)

    Retorna:
    - Bugs potenciales
    - Code smells
    - Mejoras de rendimiento
    - Score de calidad (0-100)
    - Código mejorado
    """
    service = AnalysisService(db=db)
    user_id = current_user.id if current_user else None

    # Obtener API key del usuario (desencriptar si existe)
    user_api_key = _get_user_api_key(current_user)

    resultado = await service.analizar_codigo(
        codigo=request.codigo,
        usuario_id=user_id,
        user_api_key=user_api_key,
    )

    if not resultado["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=resultado.get("error", "Error desconocido"),
        )

    return AnalysisResponse(**resultado)


@router.get("/stats", response_model=StatsResponse, status_code=status.HTTP_200_OK)
async def obtener_estadisticas(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StatsResponse:
    """
    Obtiene estadísticas de análisis del usuario autenticado.

    Retorna:
    - Total de análisis realizados
    - Análisis realizados hoy
    - Score promedio
    - Límite diario según plan
    """
    # Nota: get_current_user ya garantiza autenticación (lanza 401 si falla)
    service = AnalysisService(db=db)
    stats = await service.obtener_estadisticas(current_user.id)
    return StatsResponse(**stats)


@router.get("/history", response_model=HistoryResponse, status_code=status.HTTP_200_OK)
async def obtener_historial(
    limit: int = Query(default=10, ge=1, le=50, description="Cantidad de resultados"),
    offset: int = Query(default=0, ge=0, description="Desplazamiento para paginación"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> HistoryResponse:
    """
    Obtiene historial de análisis del usuario autenticado.

    - **limit**: Cantidad de resultados (1-50, default: 10)
    - **offset**: Desplazamiento para paginación
    """
    # Nota: get_current_user ya garantiza autenticación (lanza 401 si falla)
    service = AnalysisService(db=db)
    history = await service.obtener_historial(current_user.id, limit, offset)
    return HistoryResponse(**history)


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check() -> dict[str, str]:
    """Health check del servicio de análisis."""
    return {
        "status": "healthy",
        "service": "analysis",
        "message": "Servicio de análisis operativo",
    }
