"""
Session management endpoints.
"""
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from src.core.db import (
    get_db, Session, AttackSeverity, AttackType, ThreatLevel,
    SessionRepository,
)
from src.core.security import AuthContext, get_current_auth


router = APIRouter()


# ==================== Schemas ====================

class SessionResponse(BaseModel):
    """Session response schema."""
    id: str
    honeypot_id: str
    source_ip: str
    source_port: int
    source_country: Optional[str]
    username: Optional[str]
    auth_success: bool
    commands: List[str]
    attack_type: AttackType
    severity: AttackSeverity
    threat_level: ThreatLevel
    attacker_skill: Optional[str]
    started_at: datetime
    ended_at: Optional[datetime]
    duration_seconds: int
    
    class Config:
        from_attributes = True


class SessionListResponse(BaseModel):
    """Paginated session list."""
    items: List[SessionResponse]
    total: int
    page: int
    page_size: int


class SessionReplay(BaseModel):
    """Session replay data."""
    session_id: str
    terminal_log: Optional[str]
    commands: List[str]
    timestamps: List[str]


# ==================== Endpoints ====================

@router.get("", response_model=SessionListResponse)
async def list_sessions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    honeypot_id: Optional[str] = None,
    source_ip: Optional[str] = None,
    severity: Optional[AttackSeverity] = None,
    auth: AuthContext = Depends(get_current_auth),
):
    """List sessions with filtering and pagination."""
    async for session in get_db():
        repo = SessionRepository(session)
        
        skip = (page - 1) * page_size
        sessions = await repo.get_all(skip=skip, limit=page_size, order_by="started_at", descending=True)
        total = await repo.count()
        
        return SessionListResponse(
            items=[SessionResponse.model_validate(s) for s in sessions],
            total=total,
            page=page,
            page_size=page_size,
        )


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    auth: AuthContext = Depends(get_current_auth),
):
    """Get a specific session."""
    async for session in get_db():
        repo = SessionRepository(session)
        sess = await repo.get_by_id(session_id)
        
        if not sess:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return SessionResponse.model_validate(sess)


@router.get("/{session_id}/replay", response_model=SessionReplay)
async def get_session_replay(
    session_id: str,
    auth: AuthContext = Depends(get_current_auth),
):
    """Get session replay data."""
    async for session in get_db():
        repo = SessionRepository(session)
        sess = await repo.get_by_id(session_id)
        
        if not sess:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return SessionReplay(
            session_id=sess.id,
            terminal_log=sess.terminal_log,
            commands=sess.commands,
            timestamps=[],  # TODO: Extract from logs
        )


@router.get("/ip/{ip}", response_model=List[SessionResponse])
async def get_sessions_by_ip(
    ip: str,
    limit: int = Query(50, ge=1, le=200),
    auth: AuthContext = Depends(get_current_auth),
):
    """Get all sessions from a specific IP."""
    async for session in get_db():
        repo = SessionRepository(session)
        sessions = await repo.get_by_ip(ip, limit=limit)
        
        return [SessionResponse.model_validate(s) for s in sessions]