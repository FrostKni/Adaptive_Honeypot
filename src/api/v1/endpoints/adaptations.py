"""
Adaptation endpoints.
"""
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from src.core.db import get_db, Adaptation, AdaptationRepository
from src.core.security import AuthContext, get_current_auth


router = APIRouter()


class AdaptationResponse(BaseModel):
    """Adaptation response schema."""
    id: int
    honeypot_id: str
    trigger_type: str
    trigger_data: dict
    ai_provider: str
    ai_model: str
    analysis_result: dict
    old_config: dict
    new_config: dict
    changes_summary: dict
    applied: bool
    success: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class AdaptationList(BaseModel):
    """Paginated adaptation list."""
    items: List[AdaptationResponse]
    total: int
    page: int
    page_size: int


@router.get("", response_model=AdaptationList)
async def list_adaptations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    honeypot_id: Optional[str] = None,
    auth: AuthContext = Depends(get_current_auth),
):
    """List adaptation history."""
    async for session in get_db():
        repo = AdaptationRepository(session)
        
        skip = (page - 1) * page_size
        adaptations = await repo.get_all(skip=skip, limit=page_size, order_by="created_at", descending=True)
        total = await repo.count()
        
        return AdaptationList(
            items=[AdaptationResponse.model_validate(a) for a in adaptations],
            total=total,
            page=page,
            page_size=page_size,
        )


@router.get("/{adaptation_id}", response_model=AdaptationResponse)
async def get_adaptation(
    adaptation_id: int,
    auth: AuthContext = Depends(get_current_auth),
):
    """Get a specific adaptation."""
    async for session in get_db():
        repo = AdaptationRepository(session)
        adaptation = await repo.get_by_id(adaptation_id)
        
        if not adaptation:
            raise HTTPException(status_code=404, detail="Adaptation not found")
        
        return AdaptationResponse.model_validate(adaptation)