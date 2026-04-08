"""
Attack event endpoints.
"""
from typing import List, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from src.core.db import get_db, get_db_context, AttackEvent, AttackSeverity, AttackEventRepository
from src.core.security import AuthContext, get_current_auth


router = APIRouter()


class AttackEventResponse(BaseModel):
    """Attack event response schema - matches frontend AttackEvent interface."""
    id: str
    honeypot_id: str
    honeypot_name: str
    type: str
    severity: str
    source_ip: str
    source_port: int
    protocol: str
    payload: str
    timestamp: datetime
    session_id: Optional[str]
    metadata: dict
    
    class Config:
        from_attributes = True


class AttackEventList(BaseModel):
    """Paginated attack event list."""
    items: List[AttackEventResponse]
    total: int
    page: int
    page_size: int


class AttackSummary(BaseModel):
    """Attack summary statistics."""
    total_events: int
    unique_ips: int
    unique_sessions: int
    severity_distribution: dict
    event_type_distribution: dict
    top_commands: List[dict]
    top_ips: List[dict]


@router.get("", response_model=AttackEventList)
async def list_events(
    page: int = Query(1, ge=1, le=200),
    page_size: int = Query(50, ge=1, le=200),
    hours: int = Query(24, ge=1, le=168),
    severity: Optional[AttackSeverity] = None,
    auth: AuthContext=Depends(get_current_auth),
):
    """List recent attack events."""
    async with get_db_context() as session:
        repo = AttackEventRepository(session)
        
        skip = (page - 1) * page_size
        events = await repo.get_recent(hours=hours, limit=page_size)
        total = len(events)
        
        # Transform events to match frontend schema
        items = []
        for e in events:
            # Extract honeypot_id from session_id (format: session-<honeypot_id>)
            # If session_id is NULL, extract from tags or use default
            if e.session_id:
                honeypot_id = e.session_id.replace("session-", "").split("-")[0] if e.session_id.startswith("session-") else e.session_id
            else:
                honeypot_id = "unknown"
            
            # Extract honeypot_name from tags (format: [event_type, "cowrie", "honeypot_name"])
            tags = e.tags or []
            honeypot_name = tags[2] if len(tags) > 2 else honeypot_id
            
            # Get data from event
            data = e.data or {}
            
            items.append(AttackEventResponse(
                id=str(e.id),
                honeypot_id=honeypot_id,
                honeypot_name=honeypot_name,
                type=e.event_type,  # Map event_type to type for frontend
                severity=e.severity.value if hasattr(e.severity, 'value') else str(e.severity),
                source_ip=data.get("source_ip", "0.0.0.0"),
                source_port=data.get("source_port", 0),
                protocol=data.get("protocol", "ssh"),  # Get from data or default to SSH
                payload=data.get("command", "") or data.get("username", "") or str(data),
                timestamp=e.timestamp,
                session_id=e.session_id,
                metadata=data,
            ))
        
        return AttackEventList(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
        )


@router.get("/summary", response_model=AttackSummary)
async def get_attack_summary(
    hours: int = Query(24, ge=1, le=168),
    auth: AuthContext = Depends(get_current_auth),
):
    """Get attack summary statistics."""
    # TODO: Calculate real stats from database
    
    return AttackSummary(
        total_events=0,
        unique_ips=0,
        unique_sessions=0,
        severity_distribution={"low": 0, "medium": 0, "high": 0, "critical": 0},
        event_type_distribution={},
        top_commands=[],
        top_ips=[],
    )