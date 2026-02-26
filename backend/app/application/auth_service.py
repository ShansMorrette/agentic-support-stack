# backend/app/application/auth_service.py
"""
Servicio de autenticación y gestión de usuarios.

Responsabilidades:
- Hashing de passwords con Argon2id
- Generación y validación de tokens JWT
- Registro y autenticación de usuarios
"""

import logging
import re
from datetime import datetime, timedelta, timezone
from enum import IntEnum
from typing import Optional

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.domain.models import User
from app.infrastructure.encryption import get_encryption_service

logger = logging.getLogger(__name__)


# ----------------- CONSTANTS -----------------


class RoleID(IntEnum):
    """IDs de roles del sistema (evita números mágicos)."""
    FREE = 1
    PRO = 2
    CUSTOM = 3  # Usuario con su propia API key


# Configuración de validación de password
MIN_PASSWORD_LENGTH = 8

# Regex pre-compilados para validaciones
_EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
_UPPERCASE_PATTERN = re.compile(r"[A-Z]")
_LOWERCASE_PATTERN = re.compile(r"[a-z]")
_DIGIT_PATTERN = re.compile(r"\d")


# ----------------- PASSWORD HASHER -----------------


# Hasher Argon2 con configuración segura (OWASP recomendado)
_password_hasher = PasswordHasher(
    time_cost=3,        # Iteraciones
    memory_cost=65536,  # 64MB de memoria
    parallelism=4,      # Hilos paralelos
)


# ----------------- SERVICE -----------------


class AuthService:
    """Servicio de autenticación con JWT y Argon2."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ----------------- PASSWORD -----------------

    @staticmethod
    def hash_password(password: str) -> str:
        """Hashear password con Argon2id (más seguro que bcrypt)."""
        return _password_hasher.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verificar password contra hash Argon2.
        
        Returns:
            True si el password es correcto, False en caso contrario.
        """
        try:
            _password_hasher.verify(hashed_password, plain_password)
            return True
        except VerifyMismatchError:
            # Password incorrecto
            return False
        except InvalidHashError:
            # Hash corrupto o inválido
            logger.warning("Hash de password inválido detectado")
            return False

    # ----------------- JWT -----------------

    @staticmethod
    def create_access_token(user_id: int, email: str, expires_delta: Optional[timedelta] = None) -> str:
        """
        Crear token JWT.
        
        Args:
            user_id: ID del usuario
            email: Email del usuario
            expires_delta: Tiempo de expiración personalizado (opcional)
            
        Returns:
            Token JWT codificado
        """
        # Usar datetime con timezone (mejor práctica que utcnow())
        now = datetime.now(timezone.utc)
        expire = now + (expires_delta or timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES))
        
        to_encode = {
            "sub": str(user_id),
            "email": email,
            "exp": expire,
            "iat": now,  # Issued at
            "type": "access",
        }
        return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    @staticmethod
    def decode_token(token: str) -> Optional[dict]:
        """Decodificar y validar token JWT."""
        try:
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            return payload
        except JWTError as e:
            logger.warning(f"Error decodificando token: {e}")
            return None

    # ----------------- VALIDACIONES -----------------

    @staticmethod
    def validate_email(email: str) -> bool:
        """Validar formato de email (usa regex pre-compilado)."""
        return bool(_EMAIL_PATTERN.match(email))

    @staticmethod
    def validate_password(password: str) -> tuple[bool, str]:
        """
        Validar fortaleza de password.
        
        Requisitos:
        - Mínimo 8 caracteres
        - Al menos una mayúscula
        - Al menos una minúscula
        - Al menos un número
        
        Returns:
            Tupla (is_valid, error_message)
        """
        if len(password) < MIN_PASSWORD_LENGTH:
            return False, f"La contraseña debe tener al menos {MIN_PASSWORD_LENGTH} caracteres"
        if not _UPPERCASE_PATTERN.search(password):
            return False, "La contraseña debe tener al menos una mayúscula"
        if not _LOWERCASE_PATTERN.search(password):
            return False, "La contraseña debe tener al menos una minúscula"
        if not _DIGIT_PATTERN.search(password):
            return False, "La contraseña debe tener al menos un número"
        return True, ""

    # ----------------- USER OPERATIONS -----------------

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Obtener usuario por email con su role cargado."""
        result = await self.db.execute(
            select(User)
            .options(selectinload(User.role))
            .where(User.email == email.lower())
        )
        return result.scalars().first()

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Obtener usuario por ID con su role cargado."""
        result = await self.db.execute(
            select(User)
            .options(selectinload(User.role))
            .where(User.id == user_id)
        )
        return result.scalars().first()

    async def register_user(
        self,
        email: str,
        password: str,
        full_name: Optional[str] = None,
        gemini_api_key: Optional[str] = None,
    ) -> tuple[Optional[User], str]:
        """
        Registrar nuevo usuario.
        Returns: (user, error_message)
        """
        # Validar email
        if not self.validate_email(email):
            return None, "Formato de email inválido"

        # Validar password
        is_valid, error = self.validate_password(password)
        if not is_valid:
            return None, error

        # Verificar si ya existe
        existing = await self.get_user_by_email(email)
        if existing:
            return None, "El email ya está registrado"

        # Determinar rol (custom si tiene API key propia)
        role_id = RoleID.CUSTOM if gemini_api_key else RoleID.FREE

        # Encriptar API key si se proporciona
        encrypted_api_key = None
        if gemini_api_key:
            encryption = get_encryption_service()
            encrypted_api_key = encryption.encrypt(gemini_api_key)
            logger.info(f"🔐 API key encriptada para usuario: {email}")

        # Crear usuario
        user = User(
            email=email.lower(),
            hashed_password=self.hash_password(password),
            full_name=full_name,
            gemini_api_key_encrypted=encrypted_api_key,
            role_id=role_id,
            is_active=True,
        )

        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        logger.info(f"✅ Usuario registrado: user_id={user.id}")
        return user, ""

    async def authenticate_user(self, email: str, password: str) -> tuple[Optional[User], str]:
        """
        Autenticar usuario.
        Returns: (user, error_message)
        """
        user = await self.get_user_by_email(email)

        if not user:
            return None, "Email o contraseña incorrectos"

        if not self.verify_password(password, user.hashed_password):
            return None, "Email o contraseña incorrectos"

        if not user.is_active:
            return None, "Usuario desactivado"

        logger.info(f"✅ Usuario autenticado: user_id={user.id}")
        return user, ""

    async def login(self, email: str, password: str) -> tuple[Optional[dict], str]:
        """
        Login completo: autenticar + generar token.
        Returns: (token_data, error_message)
        """
        user, error = await self.authenticate_user(email, password)
        if not user:
            return None, error

        # Generar token
        access_token = self.create_access_token(user.id, user.email)

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role.name if user.role else "free",
                "has_own_api_key": bool(user.gemini_api_key_encrypted),
                "analyses_today": user.analyses_today or 0,
                "total_analyses": user.total_analyses or 0,
            },
        }, ""


# ----------------- DEPENDENCY -----------------


def get_auth_service(db: AsyncSession) -> AuthService:
    """Factory para AuthService."""
    return AuthService(db)
