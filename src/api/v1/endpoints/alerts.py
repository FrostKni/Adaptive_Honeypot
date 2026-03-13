"""
Alert management endpoints.
"""
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from src.core.db import get_db, Alert, AlertStatus, AttackSeverity, AlertRepository
from src.core.security import AuthContext, get_current_auth


router = APIRouter()


class AlertResponse(BaseModel):
    """Alert response schema."""
    id: int
    alert_type: str
    severity: AttackSeverity
    title: str
    message: str
    honeypot_id: Optional[str]
    session_id: Optional[str]
    source_ip: Optional[str]
    status: AlertStatus
    created_at: datetime
    
    class Config:
        from_attributes = True


class AlertList(BaseModel):
    """Paginated alert list."""
    items: List[AlertResponse]
    total: int
    page: int
    page_size: int


class AlertAcknowledge(BaseModel):
    """Alert acknowledgment schema."""
    acknowledged_by: str


@router.get("", response_model=AlertList)
async def list_alerts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[AlertStatus] = None,
    severity: Optional[AttackSeverity] = None,
    auth: AuthContext = Depends(get_current_auth),
):
    """List alerts with filtering."""
    async for session in get_db():
        repo = AlertRepository(session)
        
        skip = (page - 1) * page_size
        alerts = await repo.get_all(skip=skip, limit=page_size, order_by="created_at", descending=True)
        total = await repo.count()
        
        return AlertList(
            items=[AlertResponse.model_validate(a) for a in alerts],
            total=total,
            page=page,
            page_size=page_size,
        )


@router.get("/pending", response_model=List[AlertResponse])
async def get_pending_alerts(
    limit: int = Query(50, ge=1, le=200),
    auth: AuthContext = Depends(get_current_auth),
):
    """Get all pending alerts."""
    async for session in get_db():
        repo = AlertRepository(session)
        alerts = await repo.get_pending(limit=limit)
        
        return [AlertResponse.model_validate(a) for a in alerts]


@router.post("/{alert_id}/acknowledge", response_model=AlertResponse)
async def acknowledge_alert(
    alert_id: int,
    data: AlertAcknowledge,
    auth: AuthContext = Depends(get_current_auth),
):
    """Acknowledge an alert."""
    auth.require_scope("alerts:write")
    
    async for session in get_db():
        repo = AlertRepository(session)
        alert = await repo.update(
            alert_id,
            status=AlertStatus.ACKNOWLEDGED,
            acknowledged_at=datetime.utcnow(),
            acknowledged_by=data.acknowledged_by,
        )
        
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        return AlertResponse.model_validate(alert)


@router.post("/{alert_id}/resolve", response_model=AlertResponse)
async def resolve_alert(
    alert_id: int,
    auth: AuthContext = Depends(get_current_auth),
):
    """Resolve an alert."""
    auth.require_scope("alerts:write")
    
    async for session in get_db():
        repo = AlertRepository(session)
        alert = await repo.update(alert_id, status=AlertStatus.RESOLVED)
        
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        return AlertResponse.model_validate(alert)