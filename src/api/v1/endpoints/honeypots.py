"""
Honeypot management endpoints - with REAL Docker deployment.
"""

from typing import List, Optional
from datetime import datetime
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status, BackgroundTasks
from pydantic import BaseModel, Field

from src.core.db import (
    get_db,
    Honeypot,
    HoneypotStatus,
    HoneypotType,
    InteractionLevel,
    HoneypotRepository,
)
from src.core.security import AuthContext, get_current_auth
from src.core.config import settings
from src.core.deployment import get_deployment_manager
from src.core.exceptions import DeploymentError

logger = logging.getLogger(__name__)


router = APIRouter()


# ==================== Schemas ====================


class HoneypotCreate(BaseModel):
    """Schema for creating a honeypot."""

    name: str = Field(..., min_length=1, max_length=100)
    type: str = Field("ssh")
    port: Optional[int] = Field(None, ge=1, le=65535)
    config: Optional[dict] = None


class HoneypotResponse(BaseModel):
    """Schema for honeypot response."""

    id: str
    name: str
    type: str
    status: str
    port: int
    container_id: Optional[str]
    interaction_level: str = "low"
    hostname: str = "server"
    total_sessions: int = 0
    total_attacks: int = 0
    last_attack: Optional[datetime] = None
    created_at: datetime
    started_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class HoneypotListResponse(BaseModel):
    """Paginated honeypot list."""

    items: List[HoneypotResponse]
    total: int
    page: int
    page_size: int
    pages: int


class HoneypotHealth(BaseModel):
    """Honeypot health metrics."""

    container_id: str
    status: str
    cpu_percent: float
    memory_usage: int
    network_rx: int
    network_tx: int


# ==================== Helper Functions ====================


def get_type_enum(type_str: str) -> HoneypotType:
    """Convert string to HoneypotType enum."""
    type_map = {
        "ssh": HoneypotType.SSH,
        "http": HoneypotType.HTTP,
        "ftp": HoneypotType.FTP,
        "telnet": HoneypotType.TELNET,
    }
    return type_map.get(type_str.lower(), HoneypotType.SSH)


async def deploy_honeypot_container(
    honeypot_id: str, name: str, honeypot_type: HoneypotType, port: int, config: dict
):
    """Background task to deploy container."""
    try:
        manager = get_deployment_manager()
        result = await manager.deploy(
            honeypot_id=honeypot_id,
            name=name,
            honeypot_type=honeypot_type,
            port=port,
            config=config or {},
        )
        logger.info(f"Deployed container for {name}: {result}")
    except Exception as e:
        logger.error(f"Failed to deploy container for {name}: {e}")


# ==================== Endpoints ====================


@router.get("", response_model=HoneypotListResponse)
async def list_honeypots(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    auth: AuthContext = Depends(get_current_auth),
    db=Depends(get_db),
):
    """List all honeypots with pagination."""
    repo = HoneypotRepository(db)

    total = await repo.count()
    skip = (page - 1) * page_size
    honeypots = await repo.get_all(
        skip=skip, limit=page_size, order_by="created_at", descending=True
    )

    # Also get container status
    manager = get_deployment_manager()
    containers = await manager.list_containers() if manager else []
    container_map = {c["id"]: c for c in containers}

    items = []
    for h in honeypots:
        container_info = container_map.get(h.id, {})
        items.append(
            HoneypotResponse(
                id=h.id,
                name=h.name,
                type=h.type.value,
                status=container_info.get("status", h.status.value),
                port=h.port,
                container_id=h.container_id,
                interaction_level=h.interaction_level.value
                if hasattr(h.interaction_level, "value")
                else str(h.interaction_level),
                hostname=h.hostname or "server",
                total_sessions=h.total_sessions,
                total_attacks=h.total_attacks,
                last_attack=h.last_attack,
                created_at=h.created_at,
                started_at=h.started_at,
            )
        )

    return HoneypotListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size if total > 0 else 0,
    )


@router.post("", response_model=HoneypotResponse, status_code=status.HTTP_201_CREATED)
async def create_honeypot(
    data: HoneypotCreate,
    background_tasks: BackgroundTasks,
    auth: AuthContext = Depends(get_current_auth),
    db=Depends(get_db),
):
    """Deploy a new honeypot - creates database record AND spawns Docker container."""
    auth.require_scope("honeypots:write")

    repo = HoneypotRepository(db)

    # Check max honeypots
    active_count = await repo.count({"status": HoneypotStatus.RUNNING})
    if active_count >= settings.honeypot.max_instances:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum honeypots ({settings.honeypot.max_instances}) reached",
        )

    # Find available port
    import uuid

    port = data.port
    if not port:
        existing = await repo.get_all()
        used_ports = {h.port for h in existing}
        for p in range(2222, 2300):
            if p not in used_ports:
                port = p
                break
        if not port:
            raise HTTPException(status_code=400, detail="No available ports")

    # Create honeypot ID
    honeypot_id = f"{data.name.lower().replace(' ', '-')}-{uuid.uuid4().hex[:8]}"
    honeypot_type = get_type_enum(data.type)

    # Create database record first
    honeypot = await repo.create(
        id=honeypot_id,
        name=data.name,
        type=honeypot_type,
        port=port,
        status=HoneypotStatus.STARTING,
        interaction_level=InteractionLevel.LOW,
        hostname="honeypot-server",
        banner=None,
        config=data.config or {},
    )

    # Deploy container in background
    manager = get_deployment_manager()
    if not manager:
        raise HTTPException(status_code=503, detail="Docker is unavailable")

    background_tasks.add_task(
        deploy_honeypot_container,
        honeypot_id=honeypot_id,
        name=data.name,
        honeypot_type=honeypot_type,
        port=port,
        config=data.config or {},
    )

    return HoneypotResponse(
        id=honeypot.id,
        name=honeypot.name,
        type=honeypot.type.value,
        status=honeypot.status.value,
        port=honeypot.port,
        container_id=honeypot.container_id,
        interaction_level=honeypot.interaction_level.value,
        hostname=honeypot.hostname or "server",
        total_sessions=honeypot.total_sessions,
        total_attacks=honeypot.total_attacks,
        last_attack=honeypot.last_attack,
        created_at=honeypot.created_at,
        started_at=honeypot.started_at,
    )


@router.get("/{honeypot_id}", response_model=HoneypotResponse)
async def get_honeypot(
    honeypot_id: str,
    auth: AuthContext = Depends(get_current_auth),
    db=Depends(get_db),
):
    """Get a specific honeypot."""
    repo = HoneypotRepository(db)
    honeypot = await repo.get_by_id(honeypot_id)

    if not honeypot:
        raise HTTPException(status_code=404, detail="Honeypot not found")

    # Get real container status
    manager = get_deployment_manager()
    container_status = await manager.get_status(honeypot_id) if manager else None

    status = honeypot.status.value
    if container_status:
        status = container_status.get("status", status)

    return HoneypotResponse(
        id=honeypot.id,
        name=honeypot.name,
        type=honeypot.type.value,
        status=status,
        port=honeypot.port,
        container_id=honeypot.container_id,
        interaction_level=honeypot.interaction_level.value,
        hostname=honeypot.hostname or "server",
        total_sessions=honeypot.total_sessions,
        total_attacks=honeypot.total_attacks,
        last_attack=honeypot.last_attack,
        created_at=honeypot.created_at,
        started_at=honeypot.started_at,
    )


@router.delete("/{honeypot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_honeypot(
    honeypot_id: str,
    auth: AuthContext = Depends(get_current_auth),
    db=Depends(get_db),
):
    """Stop and remove a honeypot - deletes container AND database record."""
    auth.require_scope("honeypots:write")

    repo = HoneypotRepository(db)
    honeypot = await repo.get_by_id(honeypot_id)

    if not honeypot:
        raise HTTPException(status_code=404, detail="Honeypot not found")

    # Stop and remove Docker container
    manager = get_deployment_manager()
    await manager.remove(honeypot_id) if manager else None

    # Delete from database
    await repo.delete(honeypot_id)


@router.post("/{honeypot_id}/restart", response_model=HoneypotResponse)
async def restart_honeypot(
    honeypot_id: str,
    auth: AuthContext = Depends(get_current_auth),
    db=Depends(get_db),
):
    """Restart a honeypot container."""
    auth.require_scope("honeypots:write")

    repo = HoneypotRepository(db)
    honeypot = await repo.get_by_id(honeypot_id)

    if not honeypot:
        raise HTTPException(status_code=404, detail="Honeypot not found")

    manager = get_deployment_manager()
    await manager.restart(honeypot_id) if manager else None

    await repo.update(honeypot_id, status=HoneypotStatus.RUNNING)
    await db.refresh(honeypot)

    return HoneypotResponse(
        id=honeypot.id,
        name=honeypot.name,
        type=honeypot.type.value,
        status=HoneypotStatus.RUNNING.value,
        port=honeypot.port,
        container_id=honeypot.container_id,
        interaction_level=honeypot.interaction_level.value,
        hostname=honeypot.hostname or "server",
        total_sessions=honeypot.total_sessions,
        total_attacks=honeypot.total_attacks,
        last_attack=honeypot.last_attack,
        created_at=honeypot.created_at,
        started_at=datetime.utcnow(),
    )


@router.get("/{honeypot_id}/health", response_model=HoneypotHealth)
async def get_honeypot_health(
    honeypot_id: str,
    auth: AuthContext = Depends(get_current_auth),
    db=Depends(get_db),
):
    """Get honeypot container health metrics."""
    repo = HoneypotRepository(db)
    honeypot = await repo.get_by_id(honeypot_id)

    if not honeypot:
        raise HTTPException(status_code=404, detail="Honeypot not found")

    manager = get_deployment_manager()
    status = await manager.get_status(honeypot_id) if manager else None

    if not status:
        raise HTTPException(status_code=503, detail="Container not running")

    return HoneypotHealth(
        honeypot_id=honeypot_id,
        container_id=status.get("container_id", "N/A"),
        status=status.get("status", "unknown"),
        cpu_percent=status.get("cpu_percent", 0.0),
        memory_usage=status.get("memory_usage", 0),
        network_rx=status.get("network_rx", 0),
        network_tx=status.get("network_tx", 0),
    )


@router.get("/{honeypot_id}/logs")
async def get_honeypot_logs(
    honeypot_id: str,
    limit: int = Query(100, ge=1, le=1000),
    auth: AuthContext = Depends(get_current_auth),
    db=Depends(get_db),
):
    """Get honeypot container logs."""
    repo = HoneypotRepository(db)
    honeypot = await repo.get_by_id(honeypot_id)

    if not honeypot:
        raise HTTPException(status_code=404, detail="Honeypot not found")

    manager = get_deployment_manager()
    logs = await manager.get_logs(honeypot_id, limit) if manager else []

    return {
        "honeypot_id": honeypot_id,
        "logs": logs,
        "limit": limit,
    }
