# backend/app/infrastructure/gemini_client.py
"""Classification client for WebLanMasters using Gemini.

Exposes a single function:
- classify_chat_message(text) -> Dict[str, Any]
  Returns a JSON-compatible dict with keys:
   - category: 'ventas' | 'soporte' | 'general'
  1-5 priority
  customer_name
  brief_summary
"""

from __future__ import annotations

import json
import re
from typing import Dict, Any
import httpx

from app.core.config import settings

# Constants
GEMINI_API_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
DEFAULT_MODEL = "gemini-2.5-flash"

# System prompt to enforce JSON output only
SYSTEM_PROMPT = (
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


def _extract_classification_text_for_json(data: dict) -> str:
    candidates = data.get("candidates", [])
    if not candidates:
        return ""
    text = candidates[0].get("content", {}).get("parts", [])
    if text and isinstance(text[0], dict) and "text" in text[0]:
        raw = text[0]["text"].strip()
    else:
        raw = ""
    # Si contiene un bloque JSON envuelto en Markdown code fences, extraer el JSON entre ```json ... ```
    if raw:
        m = re.search(r"```json\s*(.*?)\s*```", raw, re.DOTALL)
        if m:
            return m.group(1).strip()
        # Si contiene un bloque JSON directo, extraerlo si es válido
        m2 = re.search(r"\{.*\}", raw, re.DOTALL)
        if m2:
            block = m2.group(0).strip()
            return block
    return raw


async def classify_chat_message(text: str) -> Dict[str, Any]:
    """Clasifica un mensaje de chat y devuelve JSON con category, priority, customer_name y brief_summary."""
    prompt = SYSTEM_PROMPT + f"\n\nUSER: {text}"
    model = DEFAULT_MODEL
    url = f"{GEMINI_API_BASE_URL}/models/{model}:generateContent?key={getattr(settings, 'GEMINI_API_KEY', '')}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": CLASSIFICATION_CONFIG,
    }

    async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=5.0)) as client:
        resp = await client.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()
        classification_text = _extract_classification_text_for_json(data)

    if not classification_text:
        return {"category": "general", "priority": 3, "customer_name": "", "brief_summary": text}

    try:
        parsed = json.loads(classification_text)
        category = parsed.get("category", "general")
        priority = int(parsed.get("priority", parsed.get("priority", 3)))
        customer_name = parsed.get("customer_name", "")
        brief_summary = parsed.get("brief_summary", parsed.get("briefSummary", text))
        return {
            "category": category,
            "priority": priority,
            "customer_name": customer_name,
            "brief_summary": brief_summary,
        }
    except Exception:
        return {"category": "general", "priority": 3, "customer_name": "", "brief_summary": classification_text}
