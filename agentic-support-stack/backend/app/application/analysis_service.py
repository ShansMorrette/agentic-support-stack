# backend/app/application/analysis_service.py
"""
Servicio de análisis de código Python con IA.

Responsabilidades:
- Orquestar análisis de código con Gemini
- Persistir resultados en base de datos
- Gestionar estadísticas e historial de usuarios
"""

import logging
import re
from datetime import date, datetime
from typing import Any, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.domain.models import Analysis, User
from app.infrastructure.gemini_client import GeminiClient

logger = logging.getLogger(__name__)


# ----------------- CONSTANTS -----------------

# Límites de código (también validados en frontend y router)
MAX_CODE_LENGTH = 40000
DEFAULT_DAILY_LIMIT = 5

# Expresiones regulares pre-compiladas para mejor rendimiento
_SCORE_PATTERN = re.compile(r"Score de Calidad:\s*(\d+)/100")
_IMPROVED_CODE_PATTERNS = [
    re.compile(r"##\s*✨\s*Código Mejorado.*?```python\s*(.*?)\s*```", re.DOTALL | re.IGNORECASE),
    re.compile(r"✨\s*Código Mejorado.*?```python\s*(.*?)\s*```", re.DOTALL | re.IGNORECASE),
    re.compile(r"Código Mejorado.*?```python\s*(.*?)\s*```", re.DOTALL | re.IGNORECASE),
]


# ----------------- EXCEPTIONS -----------------


class AnalysisError(Exception):
    """Excepción base para errores del servicio de análisis."""
    pass


class AnalysisValidationError(AnalysisError):
    """Error de validación de entrada."""
    pass


class AnalysisPersistenceError(AnalysisError):
    """Error al persistir datos en la base de datos."""
    pass


# ----------------- SERVICE -----------------


class AnalysisService:
    """
    Servicio de aplicación para análisis de código Python.
    Orquesta la lógica de negocio y coordina con la infraestructura.
    """

    def __init__(
        self,
        db: Optional[AsyncSession] = None,
        gemini_client: Optional[GeminiClient] = None,
    ):
        """
        Inicializa el servicio.

        Args:
            db: Sesión de base de datos (opcional)
            gemini_client: Cliente de Gemini (opcional)
        """
        self.db = db
        self.gemini_client = gemini_client or GeminiClient(api_key=settings.GEMINI_API_KEY)

    @staticmethod
    def _extract_score(analisis: str) -> Optional[int]:
        """Extraer score de calidad del análisis (usa regex pre-compilado)."""
        match = _SCORE_PATTERN.search(analisis)
        if match:
            return int(match.group(1))
        return None

    @staticmethod
    def _extract_improved_code(analisis: str) -> Optional[str]:
        """Extraer código mejorado del análisis (usa regex pre-compilados)."""
        for pattern in _IMPROVED_CODE_PATTERNS:
            match = pattern.search(analisis)
            if match:
                return match.group(1).strip()
        return None

    async def analizar_codigo(
        self,
        codigo: str,
        usuario_id: Optional[int] = None,
        user_api_key: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Analiza código Python y retorna sugerencias de mejora.

        Args:
            codigo: Código Python a analizar
            usuario_id: ID del usuario (opcional)
            user_api_key: API key propia del usuario (opcional)

        Returns:
            Diccionario con el análisis y metadatos
        """
        timestamp = datetime.now()
        
        # Validar código
        if not codigo or not codigo.strip():
            return {
                "success": False,
                "error": "El código no puede estar vacío",
                "codigo": codigo or "",
                "timestamp": timestamp,
            }

        if len(codigo) > MAX_CODE_LENGTH:
            return {
                "success": False,
                "error": f"El código es demasiado largo (máximo {MAX_CODE_LENGTH:,} caracteres)",
                "codigo": codigo[:100] + "...",
                "timestamp": timestamp,
            }

        try:
            logger.info(f"Analizando código para usuario_id={usuario_id}")

            # Usar API key del usuario si tiene, sino la del sistema
            client = GeminiClient(api_key=user_api_key) if user_api_key else self.gemini_client
            if user_api_key:
                logger.info("Usando API key del usuario")

            # Llamar a Gemini
            analisis = await client.analyze_code(code=codigo, model=settings.GEMINI_MODEL)

            # Extraer datos del análisis
            score = self._extract_score(analisis)
            codigo_mejorado = self._extract_improved_code(analisis)

            # Guardar en DB si hay usuario autenticado y DB disponible
            analysis_id = await self._persist_analysis(
                usuario_id=usuario_id,
                codigo=codigo,
                codigo_mejorado=codigo_mejorado,
                analisis=analisis,
                score=score,
            )

            return {
                "success": True,
                "analisis": analisis,
                "codigo": codigo,
                "usuario_id": usuario_id,
                "timestamp": timestamp,
                "modelo_usado": settings.GEMINI_MODEL,
                "analysis_id": analysis_id,
            }

        except Exception as e:
            logger.error(f"Error en análisis de código: {e}", exc_info=True)
            return {
                "success": False,
                "error": "Error al procesar el análisis. Intente nuevamente.",
                "codigo": codigo[:100] + "..." if len(codigo) > 100 else codigo,
                "timestamp": timestamp,
            }

    async def _persist_analysis(
        self,
        usuario_id: Optional[int],
        codigo: str,
        codigo_mejorado: Optional[str],
        analisis: str,
        score: Optional[int],
    ) -> Optional[int]:
        """
        Persiste el análisis y actualiza contadores de forma atómica.
        
        Args:
            usuario_id: ID del usuario
            codigo: Código original
            codigo_mejorado: Código mejorado extraído
            analisis: Resultado del análisis
            score: Score de calidad
            
        Returns:
            ID del análisis guardado o None si no se pudo guardar
            
        Raises:
            AnalysisPersistenceError: Si falla la persistencia (propaga el error)
        """
        if not self.db or not usuario_id:
            return None
        
        try:
            # Crear registro de análisis
            analysis_record = Analysis(
                user_id=usuario_id,
                code_original=codigo,
                code_improved=codigo_mejorado,
                analysis_result=analisis,
                quality_score=score,
                model_used=settings.GEMINI_MODEL,
            )
            self.db.add(analysis_record)
            await self.db.flush()
            analysis_id = analysis_record.id

            # Actualizar contadores del usuario (mismo transaction)
            await self._update_user_counters(usuario_id)

            logger.info(f"✅ Análisis guardado con ID={analysis_id}")
            return analysis_id
            
        except Exception as e:
            # Log del error pero NO suprimir - dejar que la transacción falle
            logger.error(f"Error al persistir análisis: {e}")
            # Nota: No hacemos rollback aquí, dejamos que el caller maneje la transacción
            raise AnalysisPersistenceError(f"No se pudo guardar el análisis: {e}") from e

    async def _update_user_counters(self, usuario_id: int) -> None:
        """Actualizar contadores de análisis del usuario."""
        if not self.db:
            return

        result = await self.db.execute(select(User).where(User.id == usuario_id))
        user = result.scalars().first()

        if not user:
            logger.warning(f"Usuario {usuario_id} no encontrado para actualizar contadores")
            return

        today = date.today()

        # Resetear contador diario si es nuevo día (comparación explícita date vs date)
        last_date = user.last_analysis_date.date() if user.last_analysis_date else None
        if last_date != today:
            user.analyses_today = 0

        user.analyses_today = (user.analyses_today or 0) + 1
        user.total_analyses = (user.total_analyses or 0) + 1
        user.last_analysis_date = datetime.now()

    async def obtener_estadisticas(self, usuario_id: int) -> dict[str, Any]:
        """Obtiene estadísticas de análisis para un usuario."""
        if not self.db:
            return {
                "total_analisis": 0,
                "analisis_hoy": 0,
                "score_promedio": 0.0,
                "limite_diario": DEFAULT_DAILY_LIMIT,
                "analisis_restantes": DEFAULT_DAILY_LIMIT,
            }

        # Obtener usuario
        result = await self.db.execute(select(User).where(User.id == usuario_id))
        user = result.scalars().first()

        if not user:
            raise AnalysisError(f"Usuario {usuario_id} no encontrado")

        # Calcular score promedio
        avg_result = await self.db.execute(
            select(func.avg(Analysis.quality_score)).where(
                Analysis.user_id == usuario_id, Analysis.quality_score.isnot(None)
            )
        )
        avg_score = avg_result.scalar() or 0.0

        # Obtener límite según rol (acceso seguro con getattr)
        limite_diario = getattr(user.role, "max_analyses_per_day", DEFAULT_DAILY_LIMIT) if user.role else DEFAULT_DAILY_LIMIT
        
        # Calcular análisis restantes
        analisis_hoy = user.analyses_today or 0
        analisis_restantes = max(0, limite_diario - analisis_hoy)

        return {
            "total_analisis": user.total_analyses or 0,
            "analisis_hoy": analisis_hoy,
            "score_promedio": round(float(avg_score), 1),
            "limite_diario": limite_diario,
            "analisis_restantes": analisis_restantes,
        }

    async def obtener_historial(
        self, usuario_id: int, limit: int = 10, offset: int = 0
    ) -> dict[str, Any]:
        """
        Obtiene historial de análisis de un usuario.
        
        Args:
            usuario_id: ID del usuario
            limit: Cantidad máxima de resultados
            offset: Desplazamiento para paginación
            
        Returns:
            Dict con items, total, limit y offset
        """
        if not self.db:
            return {"items": [], "total": 0, "limit": limit, "offset": offset}

        # Contar total
        count_result = await self.db.execute(
            select(func.count(Analysis.id)).where(Analysis.user_id == usuario_id)
        )
        total = count_result.scalar() or 0

        # Obtener análisis paginados
        result = await self.db.execute(
            select(Analysis)
            .where(Analysis.user_id == usuario_id)
            .order_by(Analysis.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        analyses = result.scalars().all()

        # Formatear items según schema HistoryItem del router
        items = [
            {
                "id": a.id,
                "codigo_snippet": (
                    a.code_original[:100] + "..."
                    if len(a.code_original) > 100
                    else a.code_original
                ),
                "score": a.quality_score,
                "created_at": a.created_at,  # datetime, no string
                "modelo_usado": a.model_used,
            }
            for a in analyses
        ]

        return {
            "items": items,
            "total": total,
            "limit": limit,
            "offset": offset,
        }
