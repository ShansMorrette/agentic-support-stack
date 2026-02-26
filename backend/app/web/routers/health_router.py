# backend/app/web/routers/health_router.py
"""
Router de health checks para monitoreo.

Endpoints:
- GET /health/ - Estado básico de la API
"""

from pydantic import BaseModel

from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["Health"])


# ----------------- SCHEMAS -----------------


class HealthResponse(BaseModel):
    """Response del health check."""
    
    status: str
    service: str = "neural-saas-api"


# ----------------- ENDPOINTS -----------------


@router.get("/", response_model=HealthResponse, summary="Check API health")
async def health_check() -> HealthResponse:
    """
    Endpoint de salud de la API.
    
    Usado por:
    - Docker healthcheck
    - Load balancers
    - Monitoreo externo (UptimeRobot, etc.)
    """
    return HealthResponse(status="ok")

