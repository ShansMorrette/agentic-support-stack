# backend/app/web/schemas/auth_schemas.py
"""
Schemas de autenticación para validación de requests y responses.

Centraliza la validación de email con tipo personalizado para evitar duplicación.
"""

import re
from typing import Annotated, Any, Optional

from pydantic import AfterValidator, BaseModel, Field


# ----------------- CUSTOM TYPES -----------------


# Patrón de email pre-compilado (más eficiente que compilar en cada validación)
_EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


def _validate_and_normalize_email(value: str) -> str:
    """
    Valida formato de email y normaliza a minúsculas.
    
    Raises:
        ValueError: Si el email no tiene formato válido
    """
    if not _EMAIL_PATTERN.match(value):
        raise ValueError("Email inválido")
    return value.lower()


# Tipo personalizado: email validado y normalizado
EmailLowerStr = Annotated[str, AfterValidator(_validate_and_normalize_email)]


# ----------------- REQUEST SCHEMAS -----------------


class UserRegisterRequest(BaseModel):
    """Schema para registro de usuario."""

    email: EmailLowerStr = Field(..., max_length=120)
    password: str = Field(..., min_length=8, max_length=128)
    full_name: Optional[str] = Field(None, max_length=100)
    gemini_api_key: Optional[str] = Field(None, description="API Key propia de Gemini (opcional)")

    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "usuario@ejemplo.com",
                "password": "MiPassword123",
                "full_name": "Juan Pérez",
                "gemini_api_key": None,
            }
        }
    }


class UserLoginRequest(BaseModel):
    """Schema para login de usuario."""

    email: EmailLowerStr
    password: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "usuario@ejemplo.com",
                "password": "MiPassword123",
            }
        }
    }


# ----------------- RESPONSE SCHEMAS -----------------


class UserResponse(BaseModel):
    """Schema de respuesta para usuario."""

    id: int
    email: str
    full_name: Optional[str]
    role: str
    has_own_api_key: bool
    analyses_today: int
    total_analyses: int

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """Schema de respuesta para token."""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class MessageResponse(BaseModel):
    """Schema genérico para mensajes."""

    success: bool
    message: str
    data: Optional[dict[str, Any]] = None
