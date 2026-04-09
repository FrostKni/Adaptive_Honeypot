"""
Cognitive-Behavioral Deception Framework - API Endpoints.

REST and WebSocket endpoints for cognitive profiling and deception management.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
import asyncio
import json

from fastapi import APIRouter, HTTPException, Depends, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from src.cognitive.profiler import CognitiveProfiler, CognitiveBiasType
from src.cognitive.engine import (
    CognitiveDeceptionEngine,
    DeceptionStrategyLibrary,
    DeceptionResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Cognitive Deception"])

# Global engine instance — shared with CognitiveIntegrationBridge
_engine: Optional[CognitiveDeceptionEngine] = None


def get_engine() -> CognitiveDeceptionEngine:
    """Get the shared CognitiveDeceptionEngine from the global bridge."""
    from src.collectors.cognitive_bridge import get_cognitive_bridge
    bridge = get_cognitive_bridge()
    if bridge is None:
        raise HTTPException(status_code=503, detail="Cognitive engine not available")
    return bridge.engine


# === Request/Response Models ===

class CognitiveProfileResponse(BaseModel):
    """Response model for cognitive profile."""
    session_id: str
    detected_biases: List[Dict[str, Any]]
    mental_model: Dict[str, Any]
    metrics: Dict[str, float]
    deception: Dict[str, Any]


class BiasListResponse(BaseModel):
    """Response model for bias list."""
    session_id: str
    biases: List[Dict[str, Any]]
    active_count: int


class StrategyResponse(BaseModel):
    """Response model for deception strategy."""
    name: str
    bias_type: str
    description: str
    effectiveness_score: float
    priority: int
    is_active: bool = True


class DeceptionEventResponse(BaseModel):
    """Response model for deception event."""
    id: int
    session_id: str
    bias_type: str
    strategy_name: str
    trigger_command: str
    response_type: str
    attacker_reacted: bool
    created_at: datetime


class CommandProcessRequest(BaseModel):
    """Request model for processing a command."""
    command: str
    session_id: str
    session_data: Optional[Dict[str, Any]] = None


class CommandProcessResponse(BaseModel):
    """Response model for processed command."""
    content: str
    response_type: str
    strategy_used: str
    bias_targeted: str
    metadata: Dict[str, Any]


class SessionAnalysisRequest(BaseModel):
    """Request model for session analysis."""
    session_id: str
    commands: List[str]
    events: Optional[List[Dict[str, Any]]] = None
    session_data: Optional[Dict[str, Any]] = None


class EffectivenessMetrics(BaseModel):
    """Response model for effectiveness metrics."""
    total_strategies: int
    total_applications: int
    overall_success_rate: float
    by_bias_type: Dict[str, Dict[str, float]]
    top_strategies: List[Dict[str, Any]]


# === API Endpoints ===

@router.get("/profiles/{session_id}", response_model=CognitiveProfileResponse)
async def get_cognitive_profile(
    session_id: str,
    engine: CognitiveDeceptionEngine = Depends(get_engine),
):
    """
    Get cognitive profile for a session.
    
    Returns the complete cognitive analysis including detected biases,
    mental model, and behavioral metrics.
    """
    profile = engine.get_profile(session_id)
    
    if not profile:
        raise HTTPException(
            status_code=404,
            detail=f"No cognitive profile found for session {session_id}"
        )
    
    return CognitiveProfileResponse(
        session_id=profile.session_id,
        detected_biases=[b.to_dict() for b in profile.detected_biases],
        mental_model=profile.mental_model.to_dict(),
        metrics={
            "overconfidence_score": profile.overconfidence_score,
            "persistence_score": profile.persistence_score,
            "tunnel_vision_score": profile.tunnel_vision_score,
            "curiosity_score": profile.curiosity_score,
            "exploration_diversity": profile.exploration_diversity,
            "error_tolerance": profile.error_tolerance,
            "learning_rate": profile.learning_rate,
        },
        deception={
            "total_applied": profile.total_deceptions_applied,
            "successful": profile.successful_deceptions,
            "success_rate": profile.deception_success_rate,
            "suspicion_level": profile.suspicion_level,
        },
    )


@router.get("/biases/{session_id}", response_model=BiasListResponse)
async def list_detected_biases(
    session_id: str,
    threshold: float = Query(0.5, ge=0.0, le=1.0),
    engine: CognitiveDeceptionEngine = Depends(get_engine),
):
    """
    List detected biases for a session.
    
    Returns all biases detected with their confidence scores.
    Optionally filter by confidence threshold.
    """
    profile = engine.get_profile(session_id)
    
    if not profile:
        raise HTTPException(
            status_code=404,
            detail=f"No cognitive profile found for session {session_id}"
        )
    
    active_biases = profile.get_active_biases(threshold)
    
    return BiasListResponse(
        session_id=session_id,
        biases=[b.to_dict() for b in profile.detected_biases],
        active_count=len(active_biases),
    )


@router.get("/mental-model/{session_id}")
async def get_mental_model(
    session_id: str,
    engine: CognitiveDeceptionEngine = Depends(get_engine),
):
    """
    Get inferred mental model of attacker.
    
    Returns beliefs, knowledge, and goals inferred from attacker behavior.
    """
    profile = engine.get_profile(session_id)
    
    if not profile:
        raise HTTPException(
            status_code=404,
            detail=f"No cognitive profile found for session {session_id}"
        )
    
    return {
        "session_id": session_id,
        "mental_model": profile.mental_model.to_dict(),
        "inferred_goals": profile.mental_model.goals,
        "beliefs": profile.mental_model.beliefs,
        "knowledge_gained": profile.mental_model.knowledge,
    }


@router.post("/analyze", response_model=Dict[str, Any])
async def analyze_session(
    request: SessionAnalysisRequest,
    engine: CognitiveDeceptionEngine = Depends(get_engine),
):
    """
    Perform full cognitive analysis of a session.
    
    Analyzes command sequence and events to build a complete
    cognitive profile with deception recommendations.
    """
    result = await engine.analyze_session(
        session_id=request.session_id,
        commands=request.commands,
        events=request.events or [],
        session_data=request.session_data or {},
    )
    
    return result


@router.post("/process-command", response_model=CommandProcessResponse)
async def process_command(
    request: CommandProcessRequest,
    engine: CognitiveDeceptionEngine = Depends(get_engine),
):
    """
    Process an attacker command through the cognitive deception pipeline.
    
    Returns a response that exploits detected cognitive biases.
    """
    response = await engine.process_command(
        session_id=request.session_id,
        command=request.command,
        session_data=request.session_data,
    )
    
    return CommandProcessResponse(
        content=response.content,
        response_type=response.response_type,
        strategy_used=response.strategy_used,
        bias_targeted=response.bias_targeted.value,
        metadata=response.metadata,
    )


# === Strategy Management Endpoints ===

strategy_router = APIRouter(prefix="/api/v1/deception", tags=["Deception Strategies"])


@strategy_router.get("/strategies", response_model=List[StrategyResponse])
async def list_deception_strategies(
    bias_type: Optional[str] = Query(None, description="Filter by bias type"),
    active_only: bool = Query(True, description="Only show active strategies"),
):
    """
    List all deception strategies.
    
    Optionally filter by bias type or active status.
    """
    library = DeceptionStrategyLibrary()
    
    strategies = []
    for name, strategy in library.strategies.items():
        if bias_type and strategy.bias_type.value != bias_type:
            continue
        if active_only and not strategy.can_use():
            continue
        
        strategies.append(StrategyResponse(
            name=strategy.name,
            bias_type=strategy.bias_type.value,
            description=strategy.description,
            effectiveness_score=strategy.effectiveness_score,
            priority=strategy.priority,
            is_active=strategy.can_use(),
        ))
    
    return sorted(strategies, key=lambda s: s.priority, reverse=True)


@strategy_router.get("/strategies/{strategy_name}", response_model=StrategyResponse)
async def get_strategy(strategy_name: str):
    """Get details of a specific deception strategy."""
    library = DeceptionStrategyLibrary()
    
    strategy = library.strategies.get(strategy_name)
    if not strategy:
        raise HTTPException(
            status_code=404,
            detail=f"Strategy '{strategy_name}' not found"
        )
    
    return StrategyResponse(
        name=strategy.name,
        bias_type=strategy.bias_type.value,
        description=strategy.description,
        effectiveness_score=strategy.effectiveness_score,
        priority=strategy.priority,
        is_active=strategy.can_use(),
    )


@strategy_router.get("/effectiveness", response_model=EffectivenessMetrics)
async def get_deception_effectiveness():
    """
    Get effectiveness metrics for all deception strategies.
    
    Returns success rates and usage statistics.
    """
    library = DeceptionStrategyLibrary()
    
    # Calculate metrics
    total_strategies = len(library.strategies)
    total_applications = sum(s.uses_this_session for s in library.strategies.values())
    
    by_bias = {}
    for strategy in library.strategies.values():
        bias = strategy.bias_type.value
        if bias not in by_bias:
            by_bias[bias] = {
                "count": 0,
                "total_effectiveness": 0.0,
            }
        by_bias[bias]["count"] += 1
        by_bias[bias]["total_effectiveness"] += strategy.effectiveness_score
    
    # Calculate averages
    for bias in by_bias:
        count = by_bias[bias]["count"]
        by_bias[bias]["avg_effectiveness"] = by_bias[bias]["total_effectiveness"] / count
    
    # Top strategies
    top = sorted(
        library.strategies.values(),
        key=lambda s: s.effectiveness_score,
        reverse=True
    )[:5]
    
    return EffectivenessMetrics(
        total_strategies=total_strategies,
        total_applications=total_applications,
        overall_success_rate=sum(s.effectiveness_score for s in library.strategies.values()) / total_strategies if total_strategies > 0 else 0,
        by_bias_type=by_bias,
        top_strategies=[
            {
                "name": s.name,
                "bias_type": s.bias_type.value,
                "effectiveness": s.effectiveness_score,
            }
            for s in top
        ],
    )


# === WebSocket for Real-time Updates ===

class CognitiveStreamManager:
    """Manages WebSocket connections for real-time cognitive updates."""
    
    def __init__(self):
        self._connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        if session_id not in self._connections:
            self._connections[session_id] = []
        self._connections[session_id].append(websocket)
        logger.info(f"WebSocket connected for session {session_id}")
    
    def disconnect(self, websocket: WebSocket, session_id: str):
        """Remove a WebSocket connection."""
        if session_id in self._connections:
            self._connections[session_id].remove(websocket)
            if not self._connections[session_id]:
                del self._connections[session_id]
        logger.info(f"WebSocket disconnected for session {session_id}")
    
    async def broadcast(self, session_id: str, message: dict):
        """Broadcast message to all connections for a session."""
        if session_id in self._connections:
            for connection in self._connections[session_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending WebSocket message: {e}")


stream_manager = CognitiveStreamManager()


@router.websocket("/stream/{session_id}")
async def cognitive_stream(
    websocket: WebSocket,
    session_id: str,
):
    """
    Real-time cognitive analysis stream.
    
    Sends updates as cognitive profile changes:
    - New biases detected
    - Mental model updates
    - Deception events
    """
    await stream_manager.connect(websocket, session_id)
    engine = get_engine()
    
    try:
        # Send initial profile if exists
        profile = engine.get_profile(session_id)
        if profile:
            await websocket.send_json({
                "type": "profile_update",
                "data": profile.to_dict(),
            })
        else:
            await websocket.send_json({
                "type": "waiting",
                "message": f"Waiting for session {session_id} to start...",
            })
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for any incoming messages (commands to process)
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0
                )
                
                # Parse message
                try:
                    message = json.loads(data)
                    
                    if message.get("type") == "command":
                        # Process command
                        command = message.get("command", "")
                        response = await engine.process_command(
                            session_id=session_id,
                            command=command,
                            session_data=message.get("session_data"),
                        )
                        
                        # Send response
                        await websocket.send_json({
                            "type": "command_response",
                            "data": response.to_dict(),
                        })
                        
                        # Send profile update
                        profile = engine.get_profile(session_id)
                        if profile:
                            await websocket.send_json({
                                "type": "profile_update",
                                "data": profile.to_dict(),
                            })
                    
                    elif message.get("type") == "ping":
                        await websocket.send_json({"type": "pong"})
                        
                except json.JSONDecodeError:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Invalid JSON message",
                    })
                    
            except asyncio.TimeoutError:
                # Send heartbeat
                await websocket.send_json({"type": "heartbeat"})
                
    except WebSocketDisconnect:
        stream_manager.disconnect(websocket, session_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        stream_manager.disconnect(websocket, session_id)


# === Bias Types Endpoint ===

@router.get("/bias-types")
async def list_bias_types():
    """
    List all supported cognitive bias types.
    
    Returns descriptions and common indicators for each bias.
    """
    return {
        "bias_types": [
            {
                "id": CognitiveBiasType.CONFIRMATION_BIAS.value,
                "name": "Confirmation Bias",
                "description": "Seeking information that confirms existing beliefs",
                "indicators": ["repeated_similar_commands", "ignoring_contradictory_output", "tunnel_vision"],
                "exploitation": "Show outputs confirming attacker's expected findings",
            },
            {
                "id": CognitiveBiasType.ANCHORING.value,
                "name": "Anchoring",
                "description": "First information heavily influences subsequent decisions",
                "indicators": ["early_session_focus", "persistent_initial_belief"],
                "exploitation": "Control first impressions to shape attacker beliefs",
            },
            {
                "id": CognitiveBiasType.SUNK_COST.value,
                "name": "Sunk Cost Fallacy",
                "description": "Continuing investment due to past investment",
                "indicators": ["long_session", "multiple_failures", "returning_to_same_path"],
                "exploitation": "Reward persistence to encourage continued engagement",
            },
            {
                "id": CognitiveBiasType.DUNNING_KRUGER.value,
                "name": "Dunning-Kruger Effect",
                "description": "Overestimating one's abilities",
                "indicators": ["no_reconnaissance", "immediate_exploitation", "complexity_mismatch"],
                "exploitation": "Show easy wins to maintain overconfidence",
            },
            {
                "id": CognitiveBiasType.CURIOSITY_GAP.value,
                "name": "Curiosity Gap",
                "description": "Drive to close information gaps",
                "indicators": ["exploring_hidden", "following_breadcrumbs", "enumeration"],
                "exploitation": "Hint at valuable hidden content",
            },
            {
                "id": CognitiveBiasType.LOSS_AVERSION.value,
                "name": "Loss Aversion",
                "description": "Fear of loss outweighs desire for gain",
                "indicators": ["protective_behavior", "careful_exploration"],
                "exploitation": "Create sense of what they'll miss",
            },
            {
                "id": CognitiveBiasType.AVAILABILITY_HEURISTIC.value,
                "name": "Availability Heuristic",
                "description": "Recent/vivid information weighted more heavily",
                "indicators": ["following_obvious_paths"],
                "exploitation": "Make certain attack paths seem more available",
            },
        ]
    }


# === Database Integration Endpoints ===

@router.get("/db/profiles/{session_id}")
async def get_stored_cognitive_profile(session_id: str):
    """
    Get stored cognitive profile from database.
    
    Returns the persisted cognitive analysis for a session.
    """
    try:
        from src.core.db import get_db
        from src.core.db.cognitive_repository import CognitiveProfileRepository
        
        async for db_session in get_db():
            repo = CognitiveProfileRepository(db_session)
            profile = await repo.get_latest_profile(session_id)
            
            if profile:
                return {
                    "session_id": session_id,
                    "detected_biases": profile.detected_biases,
                    "mental_model": {
                        "beliefs": profile.beliefs,
                        "knowledge": profile.knowledge,
                        "goals": profile.goals,
                        "expectations": profile.expectations,
                    },
                    "metrics": {
                        "overconfidence_score": profile.overconfidence_score,
                        "persistence_score": profile.persistence_score,
                        "tunnel_vision_score": profile.tunnel_vision_score,
                        "curiosity_score": profile.curiosity_score,
                        "exploration_diversity": profile.exploration_diversity,
                        "error_tolerance": profile.error_tolerance,
                        "learning_rate": profile.learning_rate,
                    },
                    "deception": {
                        "total_applied": profile.total_deceptions_applied,
                        "successful": profile.successful_deceptions,
                        "success_rate": profile.deception_success_rate,
                        "suspicion_level": profile.suspicion_level,
                    },
                    "is_final": profile.is_final,
                    "created_at": profile.created_at.isoformat(),
                    "updated_at": profile.updated_at.isoformat(),
                }
            
            raise HTTPException(
                status_code=404,
                detail=f"No stored cognitive profile found for session {session_id}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/db/events/{session_id}")
async def get_deception_events(session_id: str, limit: int = 50):
    """
    Get deception events for a session from database.
    
    Returns all deception strategies applied during the session.
    """
    try:
        from src.core.db import get_db
        from src.core.db.cognitive_repository import CognitiveProfileRepository
        
        async for db_session in get_db():
            repo = CognitiveProfileRepository(db_session)
            events = await repo.get_deception_events(session_id, limit)
            
            return {
                "session_id": session_id,
                "events": [
                    {
                        "id": e.id,
                        "bias_type": e.bias_type,
                        "strategy_name": e.strategy_name,
                        "trigger_command": e.trigger_command,
                        "response_type": e.response_type,
                        "attacker_reacted": e.attacker_reacted,
                        "effectiveness_score": e.effectiveness_score,
                        "created_at": e.created_at.isoformat(),
                    }
                    for e in events
                ],
                "total": len(events),
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/db/stats")
async def get_cognitive_stats():
    """
    Get overall cognitive deception statistics.
    
    Returns aggregate statistics across all sessions.
    """
    try:
        from src.core.db import get_db
        from src.core.db.cognitive_repository import CognitiveProfileRepository
        
        async for db_session in get_db():
            repo = CognitiveProfileRepository(db_session)
            stats = await repo.get_deception_effectiveness_stats()
            
            # Add additional metrics
            from src.core.db.session import get_db_context
            from src.core.db.models import CognitiveProfileDB, DeceptionEventDB
            from sqlalchemy import select, func
            
            async with get_db_context() as session:
                # Total sessions
                total_sessions = await session.execute(
                    select(func.count()).select_from(CognitiveProfileDB)
                )
                stats["total_sessions"] = total_sessions.scalar() or 0
                
                # Total deception events
                total_events = await session.execute(
                    select(func.count()).select_from(DeceptionEventDB)
                )
                stats["total_deception_events"] = total_events.scalar() or 0
                
                # Active sessions (not final)
                active_sessions = await session.execute(
                    select(func.count()).select_from(CognitiveProfileDB)
                    .where(CognitiveProfileDB.is_final == False)
                )
                stats["active_sessions"] = active_sessions.scalar() or 0
                
                # Average scores
                avg_overconfidence = await session.execute(
                    select(func.avg(CognitiveProfileDB.overconfidence_score))
                )
                stats["avg_overconfidence"] = round(float(avg_overconfidence.scalar() or 0), 3)
                
                avg_persistence = await session.execute(
                    select(func.avg(CognitiveProfileDB.persistence_score))
                )
                stats["avg_persistence"] = round(float(avg_persistence.scalar() or 0), 3)
                
                avg_curiosity = await session.execute(
                    select(func.avg(CognitiveProfileDB.curiosity_score))
                )
                stats["avg_curiosity"] = round(float(avg_curiosity.scalar() or 0), 3)
                
                # Recent activity (last 24 hours)
                from datetime import timedelta
                yesterday = datetime.utcnow() - timedelta(hours=24)
                recent_profiles = await session.execute(
                    select(func.count()).select_from(CognitiveProfileDB)
                    .where(CognitiveProfileDB.updated_at >= yesterday)
                )
                stats["profiles_last_24h"] = recent_profiles.scalar() or 0
            
            return stats
            
    except Exception as e:
        logger.error(f"Error getting cognitive stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/db/sessions/by-bias/{bias_type}")
async def get_sessions_by_bias(
    bias_type: str,
    min_confidence: float = Query(0.5, ge=0.0, le=1.0),
    limit: int = Query(50, ge=1, le=200),
):
    """
    Get sessions where a specific bias was detected.
    
    Returns sessions with the specified cognitive bias detected.
    """
    try:
        from src.core.db import get_db
        from src.core.db.cognitive_repository import CognitiveProfileRepository
        
        async for db_session in get_db():
            repo = CognitiveProfileRepository(db_session)
            sessions = await repo.get_sessions_with_bias(
                bias_type=bias_type,
                min_confidence=min_confidence,
                limit=limit,
            )
            
            return {
                "bias_type": bias_type,
                "min_confidence": min_confidence,
                "sessions": sessions,
                "total": len(sessions),
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# === Sessions List Endpoint ===

class SessionSummary(BaseModel):
    """Summary of a cognitive session."""
    session_id: str
    source_ip: str = ""
    started_at: str = ""
    last_activity: str = ""
    biases: List[Dict[str, Any]] = []
    mental_model: Dict[str, Any] = {}
    cognitive_metrics: Dict[str, float] = {}
    deception_metrics: Dict[str, Any] = {}
    commands: List[Dict[str, Any]] = []
    active: bool = True


@router.get("/sessions")
async def list_cognitive_sessions(
    limit: int = Query(50, ge=1, le=200),
    active_only: bool = Query(False),
):
    """
    List all cognitive sessions with profiles.
    
    Returns sessions that have been analyzed by the cognitive engine.
    Loads from database for persistence across restarts.
    """
    sessions = []
    
    # Try to load from database first
    try:
        from src.core.db import get_db
        from src.core.db.cognitive_repository import CognitiveProfileRepository
        
        async for db_session in get_db():
            repo = CognitiveProfileRepository(db_session)
            profiles = await repo.get_recent_profiles(limit=limit)
            
            for profile in profiles:
                # Get deception events for this session to build by_strategy and commands
                deception_events = await repo.get_deception_events(profile.session_id, limit=100)
                
                # Build by_strategy stats
                by_strategy = {}
                commands_list = []
                for event in deception_events:
                    # Build by_strategy
                    if event.strategy_name not in by_strategy:
                        by_strategy[event.strategy_name] = {
                            "applied": 0,
                            "successful": 0
                        }
                    by_strategy[event.strategy_name]["applied"] += 1
                    if event.attacker_reacted:
                        by_strategy[event.strategy_name]["successful"] += 1
                    
                    # Build commands list
                    commands_list.append({
                        "command": event.trigger_command,
                        "timestamp": event.created_at.isoformat() if event.created_at else "",
                        "deception_strategy": event.strategy_name,
                        "response_indicators": [event.response_type] if event.response_type else [],
                        "suspicion_change": 0,
                    })
                
                # Calculate success rates for by_strategy
                for strategy in by_strategy:
                    applied = by_strategy[strategy]["applied"]
                    successful = by_strategy[strategy]["successful"]
                    by_strategy[strategy]["rate"] = successful / applied if applied > 0 else 0
                
                # Parse beliefs to ensure they have confidence values
                beliefs = profile.beliefs or {}
                formatted_beliefs = {}
                for key, value in beliefs.items():
                    if isinstance(value, dict) and "confidence" in value:
                        formatted_beliefs[key] = value
                    elif isinstance(value, (int, float)):
                        formatted_beliefs[key] = {"confidence": float(value)}
                    else:
                        formatted_beliefs[key] = {"confidence": 0.5}
                
                session_data = {
                    "session_id": profile.session_id,
                    "source_ip": profile.source_ip or "",
                    "started_at": profile.created_at.isoformat() if profile.created_at else "",
                    "last_activity": profile.updated_at.isoformat() if profile.updated_at else "",
                    "biases": profile.detected_biases or [],
                    "mental_model": {
                        "beliefs": formatted_beliefs,
                        "knowledge": profile.knowledge or [],
                        "goals": profile.goals or [],
                        "expectations": profile.expectations or {},
                    },
                    "cognitive_metrics": {
                        "overconfidence_score": profile.overconfidence_score or 0,
                        "persistence_score": profile.persistence_score or 0,
                        "tunnel_vision_score": profile.tunnel_vision_score or 0,
                        "curiosity_score": profile.curiosity_score or 0,
                        "exploitation_potential": 0.5,
                        "adaptability_score": profile.learning_rate or 0,
                    },
                    "deception_metrics": {
                        "total_applied": profile.total_deceptions_applied or 0,
                        "successful": profile.successful_deceptions or 0,
                        "success_rate": profile.deception_success_rate or 0,
                        "suspicion_level": profile.suspicion_level or 0,
                        "by_strategy": by_strategy,
                    },
                    "commands": commands_list,
                    "active": not profile.is_final if profile.is_final is not None else True,
                }
                
                if active_only and not session_data["active"]:
                    continue
                    
                sessions.append(session_data)
            
            break  # Exit the async for loop after first iteration
            
    except Exception as e:
        logger.warning(f"Failed to load cognitive sessions from DB: {e}, falling back to in-memory")
        # Fall back to in-memory engine data
        engine = get_engine()
        
        for session_id, profile in engine._profiles.items():
            session_data = {
                "session_id": session_id,
                "source_ip": getattr(profile, 'source_ip', session_id.replace('attack-', '')),
                "started_at": profile.first_command_time.isoformat() if hasattr(profile, 'first_command_time') and profile.first_command_time else "",
                "last_activity": profile.last_command_time.isoformat() if hasattr(profile, 'last_command_time') and profile.last_command_time else "",
                "biases": [b.to_dict() for b in profile.detected_biases],
                "mental_model": profile.mental_model.to_dict() if profile.mental_model else {},
                "cognitive_metrics": {
                    "overconfidence_score": profile.overconfidence_score,
                    "persistence_score": profile.persistence_score,
                    "tunnel_vision_score": profile.tunnel_vision_score,
                    "curiosity_score": profile.curiosity_score,
                    "exploitation_potential": 0.5,
                    "adaptability_score": profile.learning_rate,
                },
                "deception_metrics": {
                    "total_applied": profile.total_deceptions_applied,
                    "successful": profile.successful_deceptions,
                    "success_rate": profile.deception_success_rate,
                    "suspicion_level": profile.suspicion_level,
                    "by_strategy": {},
                },
                "commands": [],
                "active": True,
            }
            
            if active_only and not session_data["active"]:
                continue
                
            sessions.append(session_data)
    
    return {"sessions": sessions[:limit], "total": len(sessions)}


# === WebSocket Endpoint ===

from fastapi import WebSocket

class ConnectionManager:
    """Manage WebSocket connections for cognitive updates."""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass


manager = ConnectionManager()


@router.websocket("/ws")
async def cognitive_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for real-time cognitive updates.
    
    Sends updates when:
    - New cognitive profiles are created
    - Biases are detected
    - Deception strategies are applied
    - Mental models are updated
    """
    await manager.connect(websocket)
    
    try:
        # Send initial status
        engine = get_engine()
        await websocket.send_json({
            "type": "connected",
            "data": {
                "active_sessions": len(engine._profiles),
                "message": "Connected to Cognitive Deception Engine"
            }
        })
        
        while True:
            # Wait for client messages (ping/pong or commands)
            data = await websocket.receive_json()
            
            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
            elif data.get("type") == "get_sessions":
                sessions = await list_cognitive_sessions()
                await websocket.send_json({
                    "type": "sessions_list",
                    "data": sessions
                })
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)