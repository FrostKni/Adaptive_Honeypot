"""
Admin endpoints.
"""
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from src.core.security import AuthContext, get_current_auth
from src.core.config import settings


router = APIRouter()


class SystemStatus(BaseModel):
    """System status response."""
    app_name: str
    version: str
    environment: str
    uptime_seconds: float
    database_connected: bool
    redis_connected: bool
    ai_provider: str
    active_honeypots: int
    active_sessions: int


class SystemConfig(BaseModel):
    """System configuration."""
    max_honeypots: int
    adaptation_threshold: int
    analysis_interval: int
    ai_provider: str
    ai_model: str


class SystemMetrics(BaseModel):
    """System resource metrics."""
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    network_in_mbps: float
    network_out_mbps: float


@router.get("/status", response_model=SystemStatus)
async def get_system_status(
    auth: AuthContext = Depends(get_current_auth),
):
    """Get system status."""
    auth.require_scope("admin")
    
    return SystemStatus(
        app_name=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
        uptime_seconds=0.0,  # TODO: Calculate
        database_connected=True,
        redis_connected=True,
        ai_provider=settings.ai.provider,
        active_honeypots=0,
        active_sessions=0,
    )


@router.get("/config", response_model=SystemConfig)
async def get_system_config(
    auth: AuthContext = Depends(get_current_auth),
):
    """Get system configuration."""
    auth.require_scope("admin")
    
    return SystemConfig(
        max_honeypots=settings.honeypot.max_instances,
        adaptation_threshold=settings.honeypot.adaptation_threshold,
        analysis_interval=settings.honeypot.analysis_interval,
        ai_provider=settings.ai.provider,
        ai_model=settings.ai.model,
    )


@router.get("/metrics", response_model=SystemMetrics)
async def get_system_metrics(
    auth: AuthContext = Depends(get_current_auth),
):
    """Get system resource metrics."""
    auth.require_scope("admin")
    
    # TODO: Get real metrics
    
    return SystemMetrics(
        cpu_percent=0.0,
        memory_percent=0.0,
        disk_percent=0.0,
        network_in_mbps=0.0,
        network_out_mbps=0.0,
    )


@router.post("/clear-cache")
async def clear_cache(auth: AuthContext = Depends(get_current_auth)):
    """Clear all caches."""
    auth.require_scope("admin")
    
    # TODO: Implement cache clearing
    
    return {"cleared": True}


@router.get("/audit-logs")
async def get_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    action: Optional[str] = None,
    auth: AuthContext = Depends(get_current_auth),
):
    """Get audit logs."""
    auth.require_scope("admin")
    
    # TODO: Get from database
    
    return {
        "items": [],
        "total": 0,
        "page": page,
        "page_size": page_size,
    }