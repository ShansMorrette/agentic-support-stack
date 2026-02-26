# backend/app/application/embeddings_service.py
"""
Servicio para generación de embeddings con Gemini.

Proporciona funcionalidad para convertir textos en vectores numéricos
que pueden usarse para búsqueda semántica, clustering, etc.
"""

import logging
from typing import Any

import requests

logger = logging.getLogger(__name__)

# URL por defecto de la API de Gemini embeddings
DEFAULT_GEMINI_EMBEDDINGS_URL = "https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent"


# ----------------- EXCEPTIONS -----------------


class EmbeddingsError(Exception):
    """Excepción base para errores del servicio de embeddings."""
    pass


class EmbeddingsAPIError(EmbeddingsError):
    """Error de comunicación con la API de embeddings."""
    pass


class EmbeddingsValidationError(EmbeddingsError):
    """Error de validación de entrada."""
    pass


# ----------------- SERVICE -----------------


class EmbeddingsService:
    """
    Servicio para generar embeddings usando Gemini text-embedding-004.
    
    Attributes:
        api_key: API key de Gemini
        api_url: URL del endpoint de embeddings
        timeout: Timeout para requests en segundos
    """

    def __init__(
        self,
        api_key: str,
        api_url: str = DEFAULT_GEMINI_EMBEDDINGS_URL,
        timeout: int = 30,
    ):
        if not api_key:
            raise ValueError("API key es requerida")
        
        self.api_key = api_key
        self.api_url = api_url
        self.timeout = timeout

    def generate_embedding(self, text: str) -> list[float]:
        """
        Genera embedding para un texto.
        
        Args:
            text: Texto a convertir en embedding
            
        Returns:
            Vector de floats representando el embedding
            
        Raises:
            EmbeddingsValidationError: Si el texto está vacío
            EmbeddingsAPIError: Si falla la comunicación con la API
        """
        if not text or not text.strip():
            raise EmbeddingsValidationError("El texto no puede estar vacío")

        headers = {
            "Content-Type": "application/json",
        }

        payload = {
            "model": "models/text-embedding-004",
            "content": {"parts": [{"text": text}]},
        }

        try:
            response = requests.post(
                f"{self.api_url}?key={self.api_key}",
                headers=headers,
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            data: dict[str, Any] = response.json()
            
            # Extraer embedding de la respuesta de Gemini
            embedding = data.get("embedding", {}).get("values", [])
            if not embedding:
                logger.warning(f"Respuesta sin embedding: {data}")
                raise EmbeddingsAPIError("Respuesta de API sin embedding válido")
            
            return embedding
            
        except requests.Timeout:
            logger.error(f"Timeout al generar embedding (>{self.timeout}s)")
            raise EmbeddingsAPIError("Timeout al comunicarse con la API")
        except requests.HTTPError as e:
            logger.error(f"Error HTTP al generar embedding: {e.response.status_code}")
            raise EmbeddingsAPIError(f"Error HTTP: {e.response.status_code}")
        except requests.RequestException as e:
            logger.error(f"Error de red al generar embedding: {e}")
            raise EmbeddingsAPIError("Error de comunicación con la API")

    def batch_generate_embeddings(self, texts: list[str]) -> dict[str, list[float]]:
        """
        Genera embeddings para múltiples textos.
        
        Args:
            texts: Lista de textos
            
        Returns:
            Dict {texto: embedding}
        """
        embeddings: dict[str, list[float]] = {}
        for text in texts:
            try:
                embeddings[text] = self.generate_embedding(text)
            except EmbeddingsValidationError:
                embeddings[text] = []  # Texto vacío -> embedding vacío
        return embeddings

    def batch_generate_embeddings_list(self, texts: list[str]) -> list[list[float]]:
        """
        Genera embeddings para múltiples textos (retorna lista ordenada).
        
        Args:
            texts: Lista de textos
            
        Returns:
            Lista de embeddings en el mismo orden que los textos
            
        Raises:
            EmbeddingsAPIError: Si falla alguna llamada a la API
        """
        embeddings: list[list[float]] = []
        for text in texts:
            embedding = self.generate_embedding(text)
            embeddings.append(embedding)
        return embeddings


# Ejemplo mínimo de uso
if __name__ == "__main__":
    import os
    
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        print("⚠️ GEMINI_API_KEY no configurada")
    else:
        service = EmbeddingsService(api_key=api_key)
        test_text = "Hola, esto es una prueba de embedding."
        try:
            emb = service.generate_embedding(test_text)
            print(f"✅ Embedding para '{test_text}': {emb[:5]}... (len={len(emb)})")
        except EmbeddingsError as e:
            print(f"❌ Error: {e}")

