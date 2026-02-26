# backend/app/infrastructure/gemini_client.py
"""Classification and Analysis client using OpenRouter (OpenAI-compatible)."""

from __future__ import annotations

import json
import logging
from typing import Dict, Any, Optional
from openai import AsyncOpenAI

from app.core.config import settings

logger = logging.getLogger(__name__)

# Constants
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "google/gemini-flash-1.5"

# System prompt to enforce JSON output for classification
CLASSIFICATION_SYSTEM_PROMPT = (
    "Eres el Asistente de WebLanMasters. Clasifica mensajes para enrutar al equipo correcto. "
    "Responde estrictamente en formato JSON con los siguientes campos: "
    "{\"category\": \"ventas\"|\"soporte\"|\"general\", \"priority\": 1-5, "
    "\"customer_name\": \"\", \"brief_summary\": \"\"}. No incluyas texto adicional."
)

class GeminiClient:
    """Client for interacting with OpenRouter API (OpenAI compatible)."""

    def __init__(self, api_key: Optional[str] = None):
        api_key = api_key or getattr(settings, 'GEMINI_API_KEY', '')
        # Base client configuration for OpenRouter
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=OPENROUTER_BASE_URL,
            default_headers={
                "HTTP-Referer": "https://weblanmasters.com",  # Required by OpenRouter
                "X-Title": "Neural SaaS Platform",           # Required by OpenRouter
            }
        )
        self.model = getattr(settings, 'GEMINI_MODEL', DEFAULT_MODEL)

    async def analyze_code(self, code: str, model: Optional[str] = None) -> str:
        """Analyzes Python code for bugs and improvements."""
        target_model = model or self.model
        try:
            response = await self.client.chat.completions.create(
                model=target_model,
                messages=[
                    {"role": "user", "content": f"Analiza el siguiente código Python y proporciona sugerencias de mejora:\n\n{code}"}
                ],
                temperature=0.2
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error(f"Error in OpenRouter analyze_code: {e}")
            return f"Error en el análisis: {str(e)}"

    async def classify_chat_message(self, text: str) -> Dict[str, Any]:
        """Classifies a chat message using OpenRouter."""
        target_model = self.model
        try:
            response = await self.client.chat.completions.create(
                model=target_model,
                messages=[
                    {"role": "system", "content": CLASSIFICATION_SYSTEM_PROMPT},
                    {"role": "user", "content": text}
                ],
                response_format={"type": "json_object"},
                temperature=0.0
            )
            
            raw_content = response.choices[0].message.content or "{}"
            parsed = json.loads(raw_content)
            
            return {
                "category": parsed.get("category", "general"),
                "priority": int(parsed.get("priority", 3)),
                "customer_name": parsed.get("customer_name", ""),
                "brief_summary": parsed.get("brief_summary", parsed.get("briefSummary", text)),
            }
        except Exception as e:
            logger.error(f"Error in OpenRouter classify_chat_message: {e}")
            return {
                "category": "general",
                "priority": 3,
                "customer_name": "",
                "brief_summary": f"Error de clasificación: {str(e)}"
            }

# Helper function for backward compatibility
async def classify_chat_message(text: str) -> Dict[str, Any]:
    """Helper function to maintain compatibility with existing code."""
    try:
        client = GeminiClient()
        return await client.classify_chat_message(text)
    except Exception as e:
        logger.error(f"Failed to initialize GeminiClient for classification: {e}")
        return {
            "category": "general",
            "priority": 3,
            "customer_name": "",
            "brief_summary": f"Error crítico: {str(e)}"
        }
