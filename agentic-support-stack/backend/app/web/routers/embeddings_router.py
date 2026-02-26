# backend/app/web/routers/embeddings_router.py
"""
Router para generación de embeddings con Gemini.

Endpoints:
- POST /embeddings/ - Generar embeddings para textos
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.application.embeddings_service import EmbeddingsService, EmbeddingsError
from app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/embeddings", tags=["Embeddings"])


# ----------------- DEPENDENCIES -----------------


def get_embeddings_service(
    settings: Annotated[Settings, Depends(get_settings)],
) -> EmbeddingsService:
    """Dependency para obtener EmbeddingsService (inyección de dependencias)."""
    return EmbeddingsService(api_key=settings.GEMINI_API_KEY)


# ----------------- SCHEMAS -----------------


class EmbeddingRequest(BaseModel):
    """Request para generar embeddings."""
    
    texts: list[str] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Lista de textos para generar embeddings (máx 100)",
    )

    class Config:
        json_schema_extra = {
            "example": {"texts": ["Hola mundo", "Python es genial"]}
        }


class EmbeddingResponse(BaseModel):
    """Response con embeddings generados."""
    
    embeddings: list[list[float]]
    count: int = Field(description="Cantidad de embeddings generados")


# ----------------- ENDPOINTS -----------------


@router.post("/", response_model=EmbeddingResponse)
async def generate_embeddings(
    request: EmbeddingRequest,
    service: Annotated[EmbeddingsService, Depends(get_embeddings_service)],
) -> EmbeddingResponse:
    """
    Genera embeddings para una lista de textos usando Gemini.
    
    - **texts**: Lista de textos (1-100 elementos)
    
    Retorna vectores de embeddings para cada texto.
    """
    try:
        embeddings = service.batch_generate_embeddings_list(request.texts)
        return EmbeddingResponse(
            embeddings=embeddings,
            count=len(embeddings),
        )
    except EmbeddingsError as e:
        # Error específico del servicio - log interno, mensaje genérico al cliente
        logger.error(f"Error en embeddings: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Error al comunicarse con el servicio de embeddings",
        )
    except ValueError as e:
        # Error de validación (textos vacíos, etc.)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

