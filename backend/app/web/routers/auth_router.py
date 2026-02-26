# backend/app/web/routers/auth_router.py
"""
Router de autenticación.

Endpoints:
- POST /api/auth/register - Registrar usuario
- POST /api/auth/login - Iniciar sesión
- GET /api/auth/me - Información del usuario
- POST /api/auth/logout - Cerrar sesión
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.auth_service import AuthService
from app.domain.models import User
from app.infrastructure.database import get_db
from app.web.schemas import (
    MessageResponse,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["Autenticación"])

# Security scheme para JWT
security = HTTPBearer(auto_error=False)


# ----------------- DEPENDENCIES -----------------


async def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    """Dependency para obtener AuthService (una instancia por request)."""
    return AuthService(db)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    auth_service: AuthService = Depends(get_auth_service),
) -> Optional[User]:
    """
    Dependency para obtener usuario actual desde JWT.
    Retorna None si no hay token (permite acceso anónimo).
    """
    if not credentials:
        return None

    token = credentials.credentials

    # Decodificar token
    payload = auth_service.decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Validar y extraer user_id del payload
    sub = payload.get("sub")
    if sub is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido: falta identificador de usuario",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        user_id = int(sub)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido: identificador de usuario malformado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Obtener usuario
    user = await auth_service.get_user_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario desactivado",
        )

    return user


async def require_auth(
    user: Optional[User] = Depends(get_current_user),
) -> User:
    """Dependency que REQUIERE autenticación."""
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autenticación requerida",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


# ----------------- ENDPOINTS -----------------


@router.post("/register", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: UserRegisterRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> MessageResponse:
    """
    Registrar nuevo usuario.

    - **email**: Email único del usuario
    - **password**: Mínimo 8 caracteres, 1 mayúscula, 1 minúscula, 1 número
    - **full_name**: Nombre completo (opcional)
    - **gemini_api_key**: API Key propia de Gemini (opcional, da acceso ilimitado)
    """
    user, error = await auth_service.register_user(
        email=request.email,
        password=request.password,
        full_name=request.full_name,
        gemini_api_key=request.gemini_api_key,
    )

    if error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    return MessageResponse(
        success=True,
        message="Usuario registrado exitosamente",
        data={"user_id": user.id, "email": user.email},
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    request: UserLoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """
    Iniciar sesión y obtener token JWT.

    El token debe enviarse en el header `Authorization: Bearer <token>`
    """
    token_data, error = await auth_service.login(
        email=request.email,
        password=request.password,
    )

    if error:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=error)

    # Usar datos reales del usuario (no hardcoded)
    user_data = token_data["user"]
    return TokenResponse(
        access_token=token_data["access_token"],
        token_type=token_data["token_type"],
        user=UserResponse(
            id=user_data["id"],
            email=user_data["email"],
            full_name=user_data["full_name"],
            role=user_data["role"],
            has_own_api_key=user_data["has_own_api_key"],
            analyses_today=user_data.get("analyses_today", 0),
            total_analyses=user_data.get("total_analyses", 0),
        ),
    )


@router.get("/me", response_model=UserResponse)
async def get_me(
    user: User = Depends(require_auth),
) -> UserResponse:
    """Obtener información del usuario autenticado."""
    # Usar from_attributes de Pydantic para mapeo automático
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role.name if user.role else "free",
        has_own_api_key=bool(user.gemini_api_key_encrypted),
        analyses_today=user.analyses_today or 0,
        total_analyses=user.total_analyses or 0,
    )


@router.post("/logout", response_model=MessageResponse)
async def logout(
    user: User = Depends(require_auth),
) -> MessageResponse:
    """
    Cerrar sesión.

    Nota: Con JWT stateless, el logout es del lado del cliente
    (eliminar el token). Este endpoint es para logging/auditoría.
    """
    # Log sin PII sensible - solo user_id
    logger.info(f"Usuario user_id={user.id} cerró sesión")
    return MessageResponse(success=True, message="Sesión cerrada exitosamente")
