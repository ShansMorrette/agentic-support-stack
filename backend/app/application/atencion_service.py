# backend/app/application/atencion_service.py
"""Servicio de atención: clasificación con Gemini y persistencia (Cliente, Ticket, Conversación)."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, Any, Dict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.models import Client, Ticket, Conversation
from app.infrastructure.gemini_client import classify_chat_message


class AtencionService:
    def __init__(self, db: Optional[AsyncSession] = None):
        self.db = db

    async def atender(self, text: str, usuario_id: Optional[int] = None) -> Dict[str, Any]:
        if not self.db:
            return {"success": False, "error": "Base de datos no disponible"}

        classification = await classify_chat_message(text)
        category = classification.get("category", "general")
        priority = int(classification.get("priority", 3))
        customer_name = classification.get("customer_name", "")
        brief_summary = classification.get("brief_summary", "")

        # Cliente: buscar o crear por nombre
        client = None
        if customer_name:
            result = await self.db.execute(select(Client).where(Client.name == customer_name))
            client = result.scalars().first()
        if not client and customer_name:
            client = Client(name=customer_name)
            self.db.add(client)
            await self.db.flush()

        if not client:
            client = Client(name="Unknown")
            self.db.add(client)
            await self.db.flush()

        # Ticket
        ticket = Ticket(client_id=client.id, category=category, priority=priority, status="open", summary=brief_summary)
        self.db.add(ticket)
        await self.db.flush()

        # Conversación (historial)
        conv = Conversation(ticket_id=ticket.id, sender="user", message=text, timestamp=datetime.now(timezone.utc))
        self.db.add(conv)
        await self.db.flush()

        await self.db.commit()

        reply_text = f"Ticket creado para {client.name}. Categoría: {category}, Prioridad: {priority}. Resumen: {brief_summary}"
        return {"success": True, "ticket_id": ticket.id, "client_id": client.id, "reply": reply_text}
