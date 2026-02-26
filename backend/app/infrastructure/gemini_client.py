# backend/app/infrastructure/gemini_client.py
"""Classification and Analysis client using Gemini."""

from __future__ import annotations

import json
import re
from typing import Dict, Any, Optional
import httpx

from app.core.config import settings

# Constants
GEMINI_API_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
DEFAULT_MODEL = "gemini-2.5-flash"

# System prompt to enforce JSON output for classification
CLASSIFICATION_SYSTEM_PROMPT = (
    "Eres el Asistente de WebLanMasters. Clasifica mensajes para enrutar al equipo correcto. "
    "Responde estrictamente en formato JSON con los siguientes campos: "
    "{\"category\": \"ventas\"|\"soporte\"|\"general\", \"priority\": 1-5, "
    "\"customer_name\": \"\", \"brief_summary\": \"\"}. No incluyas texto adicional."
)

CLASSIFICATION_CONFIG = {
    "temperature": 0.0,
    "maxOutputTokens": 512,
    "topP": 0.8,
    "topK": 10,
}


class GeminiClient:
    """Client for interacting with Google Gemini API."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or getattr(settings, 'GEMINI_API_KEY', '')

    def _extract_text_from_response(self, data: dict) -> str:
        candidates = data.get("candidates", [])
        if not candidates:
            return ""
        content = candidates[0].get("content", {}).get("parts", [])
        if content and isinstance(content[0], dict) and "text" in content[0]:
            return content[0]["text"].strip()
        return ""

    def _extract_json_block(self, raw: str) -> str:
        # Extract from markdown code fences first
        m = re.search(r"```json\s*(.*?)\s*```", raw, re.DOTALL)
        if m:
            return m.group(1).strip()
        # Fallback to finding first brace block
        m2 = re.search(r"\{.*\}", raw, re.DOTALL)
        if m2:
            return m2.group(0).strip()
        return raw

    async def _generate_content(self, prompt: str, config: dict, model: str = DEFAULT_MODEL) -> str:
        url = f"{GEMINI_API_BASE_URL}/models/{model}:generateContent?key={self.api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": config,
        }

        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=5.0)) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return self._extract_text_from_response(data)

    async def analyze_code(self, code: str, model: str = DEFAULT_MODEL) -> str:
        """Analyzes Python code for bugs and improvements."""
        prompt = f"Analiza el siguiente código Python y proporciona sugerencias de mejora:\n\n{code}"
        return await self._generate_content(prompt, {"temperature": 0.2}, model)

    async def classify_chat_message(self, text: str) -> Dict[str, Any]:
        """Classifies a chat message into categories (ventas, soporte, general)."""
        prompt = CLASSIFICATION_SYSTEM_PROMPT + f"\n\nUSER: {text}"
        raw_response = await self._generate_content(prompt, CLASSIFICATION_CONFIG)
        
        if not raw_response:
            return {"category": "general", "priority": 3, "customer_name": "", "brief_summary": text}

        classification_text = self._extract_json_block(raw_response)

        try:
            parsed = json.loads(classification_text)
            return {
                "category": parsed.get("category", "general"),
                "priority": int(parsed.get("priority", 3)),
                "customer_name": parsed.get("customer_name", ""),
                "brief_summary": parsed.get("brief_summary", parsed.get("briefSummary", text)),
            }
        except Exception:
            return {"category": "general", "priority": 3, "customer_name": "", "brief_summary": classification_text}


# Helper function for backward compatibility
async def classify_chat_message(text: str) -> Dict[str, Any]:
    client = GeminiClient()
    return await client.classify_chat_message(text)
