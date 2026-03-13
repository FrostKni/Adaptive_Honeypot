"""
Threat intelligence endpoints.
"""
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from src.core.db import get_db, ThreatIntelligence, AttackSeverity, ThreatIntelRepository
from src.core.security import AuthContext, get_current_auth


router = APIRouter()


class ThreatIntelCreate(BaseModel):
    """Schema for creating threat intelligence."""
    indicator_type: str = Field(..., pattern="^(ip|domain|hash|url|email)$")
    indicator_value: str
    threat_type: Optional[str] = None
    confidence: float = Field(0.5, ge=0.0, le=1.0)
    severity: AttackSeverity = AttackSeverity.MEDIUM
    tags: List[str] = []
    malware_families: List[str] = []
    source: str = "manual"


class ThreatIntelResponse(BaseModel):
    """Threat intelligence response schema."""
    id: int
    indicator_type: str
    indicator_value: str
    threat_type: Optional[str]
    confidence: float
    severity: AttackSeverity
    tags: List[str]
    malware_families: List[str]
    source: str
    first_seen: datetime
    last_seen: datetime
    
    class Config:
        from_attributes = True


class ThreatIntelLookup(BaseModel):
    """Threat intelligence lookup result."""
    indicator: str
    indicator_type: str
    found: bool
    intelligence: Optional[ThreatIntelResponse]


@router.post("", response_model=ThreatIntelResponse)
async def add_threat_intel(
    data: ThreatIntelCreate,
    auth: AuthContext = Depends(get_current_auth),
):
    """Add threat intelligence."""
    auth.require_scope("threat_intel:write")
    
    async for session in get_db():
        repo = ThreatIntelRepository(session)
        intel = await repo.add_indicator(
            indicator_type=data.indicator_type,
            indicator_value=data.indicator_value,
            threat_type=data.threat_type,
            confidence=data.confidence,
            severity=data.severity,
            tags=data.tags,
            malware_families=data.malware_families,
            source=data.source,
        )
        
        return ThreatIntelResponse.model_validate(intel)


@router.get("/lookup/{indicator}", response_model=ThreatIntelLookup)
async def lookup_indicator(
    indicator: str,
    indicator_type: str = Query("ip"),
    auth: AuthContext = Depends(get_current_auth),
):
    """Look up threat intelligence for an indicator."""
    async for session in get_db():
        repo = ThreatIntelRepository(session)
        
        if indicator_type == "ip":
            intel = await repo.lookup_ip(indicator)
        else:
            intel = await repo.get_by_field("indicator_value", indicator)
        
        return ThreatIntelLookup(
            indicator=indicator,
            indicator_type=indicator_type,
            found=intel is not None,
            intelligence=ThreatIntelResponse.model_validate(intel) if intel else None,
        )


@router.get("", response_model=List[ThreatIntelResponse])
async def list_threat_intel(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    indicator_type: Optional[str] = None,
    auth: AuthContext = Depends(get_current_auth),
):
    """List threat intelligence entries."""
    async for session in get_db():
        repo = ThreatIntelRepository(session)
        
        skip = (page - 1) * page_size
        intel = await repo.get_all(skip=skip, limit=page_size)
        
        return [ThreatIntelResponse.model_validate(i) for i in intel]


@router.delete("/{intel_id}")
async def delete_threat_intel(
    intel_id: int,
    auth: AuthContext = Depends(get_current_auth),
):
    """Delete threat intelligence."""
    auth.require_scope("threat_intel:write")
    
    async for session in get_db():
        repo = ThreatIntelRepository(session)
        deleted = await repo.delete(intel_id)
        
        if not deleted:
            raise HTTPException(status_code=404, detail="Threat intelligence not found")
        
        return {"deleted": True}