"""
AI Monitoring API Endpoints.
Real-time AI workflow visualization and control.
"""
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
    """Get recent AI activities."""
    return {
        "activities": ai_service.get_recent_activities(limit),
        "total": len(ai_service.activities)
    }


@router.get("/decisions")
async def get_decisions(
    limit: int = 10,
    current_user = Depends(get_current_user)
):
    """Get recent AI decisions."""
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


@router.websocket("/ws")
async def ai_monitoring_websocket(websocket: WebSocket):
    """WebSocket for real-time AI activity updates."""
    await websocket.accept()
    
    async def send_activity(activity: AIActivity):
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
        except:
            pass
    
    # Subscribe to updates
    ai_service.subscribe(send_activity)
    
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
                
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        # Unsubscribe
        if send_activity in ai_service.subscribers:
            ai_service.subscribers.remove(send_activity)


@router.get("/metrics")
async def get_ai_metrics(current_user = Depends(get_current_user)):
    """Get AI performance metrics."""
    activities = list(ai_service.activities)
    decisions = list(ai_service.decisions)
    
    # Calculate metrics
    total_activities = len(activities)
    successful = sum(1 for a in activities if a.success)
    failed = total_activities - successful
    
    # Count by status
    status_counts = {}
    for activity in activities:
        status = activity.status.value
        status_counts[status] = status_counts.get(status, 0) + 1
    
    # Count decisions by action
    action_counts = {}
    for decision in decisions:
        action = decision.action
        action_counts[action] = action_counts.get(action, 0) + 1
    
    # Average threat score
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
    return {
        "status": "healthy" if ai_service.is_running else "stopped",
        "llm_available": await ai_service.llm_client.health_check(),
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
    return {
        "executions": executor.get_execution_history(limit),
        "stats": executor.get_stats()
    }


@router.get("/executions/stats")
async def get_execution_stats(current_user = Depends(get_current_user)):
    """Get execution statistics."""
    from src.ai.decision_executor import get_executor
    
    executor = get_executor()
    return executor.get_stats()


@router.get("/executions/{execution_id}")
async def get_execution(
    execution_id: str,
    current_user = Depends(get_current_user)
):
    """Get details of a specific execution."""
    from src.ai.decision_executor import get_executor
    
    executor = get_executor()
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
    
    action_type = action.get("action")
    honeypot_id = action.get("honeypot_id")
    source_ip = action.get("source_ip", "manual")
    config_changes = action.get("config_changes", {})
    
    if action_type not in ["monitor", "reconfigure", "isolate", "switch_container"]:
        raise HTTPException(status_code=400, detail="Invalid action type")
    
    if not honeypot_id:
        raise HTTPException(status_code=400, detail="honeypot_id required")
    
    executor = get_executor()
    
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