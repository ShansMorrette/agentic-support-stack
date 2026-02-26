# backend/app/infrastructure/encryption.py
"""
Servicio de encriptación para datos sensibles (API keys).

Usa Fernet (AES-128-CBC con HMAC) para encriptación simétrica reversible.
La clave se deriva usando PBKDF2-HMAC-SHA256 con 310,000 iteraciones.
"""

import base64
import logging
import secrets
from functools import lru_cache
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.core.config import settings, Environment

logger = logging.getLogger(__name__)


# ----------------- CONSTANTS -----------------


PBKDF2_ITERATIONS = 310_000  # OWASP 2023 recommendation
SALT_LENGTH_BYTES = 16
DERIVED_KEY_LENGTH_BYTES = 32  # AES-256 key size
FERNET_TOKEN_MIN_LENGTH = 100  # Tokens Fernet reales son ~100-140+ chars (base64 encoded)
FERNET_HEADER_PREFIX = "gAAAAA"  # Base64 de versión Fernet (0x80)


# ----------------- EXCEPTIONS -----------------


class EncryptionError(Exception):
    """Error durante encriptación."""
    pass


class DecryptionError(Exception):
    """Error durante desencriptación."""
    pass


class ConfigurationError(Exception):
    """Error de configuración de encriptación."""
    pass


# ----------------- SERVICE -----------------


class EncryptionService:
    """
    Servicio para encriptar/desencriptar datos sensibles.
    
    Características:
    - Fernet (AES-128-CBC + HMAC-SHA256)
    - Clave derivada con PBKDF2 (310k iteraciones)
    - En desarrollo: genera claves aleatorias si no están configuradas
    - En producción: requiere ENCRYPTION_KEY y ENCRYPTION_SALT obligatorios
    """

    __slots__ = ("_fernet", "_is_production")

    def __init__(
        self, 
        encryption_key: Optional[str] = None, 
        encryption_salt: Optional[str] = None,
    ) -> None:
        self._is_production = settings.ENVIRONMENT == Environment.PRODUCTION
        
        base_key = self._get_or_generate_secret(
            env_var="ENCRYPTION_KEY",
            arg_value=encryption_key,
            generator=lambda: secrets.token_urlsafe(DERIVED_KEY_LENGTH_BYTES),
            secret_name="clave base",
        )
        salt_str = self._get_or_generate_secret(
            env_var="ENCRYPTION_SALT",
            arg_value=encryption_salt,
            generator=lambda: secrets.token_hex(SALT_LENGTH_BYTES),
            secret_name="salt",
        )
        
        self._fernet = self._create_fernet(base_key, salt_str.encode())

    def _get_or_generate_secret(
        self,
        env_var: str,
        arg_value: Optional[str],
        generator: callable,
        secret_name: str,
    ) -> str:
        """
        Obtiene un secreto del argumento, del entorno, o lo genera en desarrollo.
        Fuerza su existencia en producción.
        """
        source_value = arg_value or getattr(settings, env_var, None)
        
        if not source_value:
            if self._is_production:
                logger.critical(f"❌ {env_var} no configurada. OBLIGATORIA en producción.")
                raise ConfigurationError(f"{env_var} es obligatoria en producción")
            source_value = generator()
            logger.warning(f"⚠️ {env_var} no configurada. Generando {secret_name} aleatorio (SOLO DESARROLLO)")
        
        # Validar que no sea cadena vacía
        if not source_value.strip():
            logger.critical(f"❌ {env_var} configurada como cadena vacía. No es válida.")
            raise ConfigurationError(f"{env_var} no puede ser una cadena vacía")
        
        return source_value

    def _create_fernet(self, base_key: str, salt: bytes) -> Fernet:
        """Crea instancia Fernet con clave derivada usando PBKDF2."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=DERIVED_KEY_LENGTH_BYTES,
            salt=salt,
            iterations=PBKDF2_ITERATIONS,
        )
        derived_key = base64.urlsafe_b64encode(kdf.derive(base_key.encode()))
        return Fernet(derived_key)

    def encrypt(self, plaintext: str) -> str:
        """
        Encripta un texto plano.
        
        Args:
            plaintext: Texto a encriptar (puede ser cadena vacía)
            
        Returns:
            Token Fernet en base64
            
        Raises:
            EncryptionError: Si falla la encriptación
        """
        try:
            encrypted = self._fernet.encrypt(plaintext.encode())
            return encrypted.decode()
        except Exception as e:
            logger.error(f"Encryption failed: {type(e).__name__}: {e}", exc_info=True)
            raise EncryptionError("Error de encriptación") from e

    def decrypt(self, ciphertext: str) -> str:
        """
        Desencripta un token Fernet.
        
        Args:
            ciphertext: Token Fernet en base64
            
        Returns:
            Texto plano original
            
        Raises:
            DecryptionError: Si el token es inválido o la clave incorrecta
        """
        if not ciphertext:
            return ""
        
        try:
            decrypted = self._fernet.decrypt(ciphertext.encode())
            return decrypted.decode()
        except InvalidToken:
            logger.warning("Decryption failed: invalid token or wrong key")
            raise DecryptionError("Token inválido o clave incorrecta")
        except Exception as e:
            logger.error(f"Decryption failed: {type(e).__name__}: {e}", exc_info=True)
            raise DecryptionError("Error de desencriptación") from e

    def is_encrypted(self, text: Optional[str]) -> bool:
        """
        Verifica si un texto parece ser un token Fernet válido.
        
        Heurística:
        - Prefijo característico de Fernet (versión 0x80 en base64)
        - Longitud mínima de 121 chars (token Fernet con payload vacío)
        - Caracteres válidos de base64 URL-safe
        """
        if not text or len(text) < FERNET_TOKEN_MIN_LENGTH:
            return False
        
        if not text.startswith(FERNET_HEADER_PREFIX):
            return False
        
        # Verificar que es base64 válido
        try:
            base64.urlsafe_b64decode(text)
            return True
        except (ValueError, Exception):
            return False


# ----------------- SINGLETON -----------------


@lru_cache(maxsize=1)
def get_encryption_service() -> EncryptionService:
    """Obtiene la instancia singleton del servicio de encriptación (thread-safe)."""
    return EncryptionService()
