from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.infrastructure.database import get_db
from app.application.atencion_service import AtencionService
from app.domain.models import Client, Ticket
from app.web.routers.auth_router import get_current_user

router = APIRouter(prefix="/api", tags=["Atención"])

class AtencionRequest(BaseModel):
    text: str
    history: Optional[List[str]] = None

class AtencionResponse(BaseModel):
    reply: str
    success: bool

@router.post("/chat/atencion", response_model=AtencionResponse, status_code=status.HTTP_200_OK)
async def atender_chat(
    request: AtencionRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
) -> AtencionResponse:
    service = AtencionService(db=db)
    res = await service.atender(text=request.text, usuario_id=(current_user.id if current_user else None))
    if not res.get("success"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=res.get("error", "Error"))
    return AtencionResponse(reply=res.get("reply", ""), success=True)

@router.get("/atencion/prospects", response_model=List[Dict[str, Any]], status_code=status.HTTP_200_OK)
async def get_prospects(db: AsyncSession = Depends(get_db)) -> List[Dict[str, Any]]:
    result = await db.execute(select(Ticket).where(Ticket.category == "ventas").order_by(Ticket.created_at.desc()))
    tickets = result.scalars().all()
    items: List[Dict[str, Any]] = []
    for t in tickets:
        client_name = t.client.name if getattr(t, 'client', None) and t.client else None
        items.append({
            "id": t.id,
            "cliente": client_name,
            "category": t.category,
            "priority": t.priority,
            "status": t.status,
            "summary": t.summary,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        })
    return items

@router.get("/atencion/tickets", response_model=List[Dict[str, Any]], status_code=status.HTTP_200_OK)
async def get_tickets(status_param: Optional[str] = None, db: AsyncSession = Depends(get_db)) -> List[Dict[str, Any]]:
    filters = []
    if status_param:
        filters.append(Ticket.status == status_param)
    else:
        filters.append(Ticket.status == 'open')
    stmt = select(Ticket).where(*filters).order_by(Ticket.created_at.desc())
    result = await db.execute(stmt)
    tickets = result.scalars().all()
    items: List[Dict[str, Any]] = []
    for t in tickets:
        client_name = t.client.name if getattr(t, 'client', None) and t.client else None
        items.append({
            "id": t.id,
            "cliente": client_name,
            "category": t.category,
            "priority": t.priority,
            "status": t.status,
            "summary": t.summary,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        })
    return items
