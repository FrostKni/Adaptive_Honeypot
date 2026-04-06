"""
Broadcast functions for WebSocket real-time updates.
Extracted to avoid circular dependencies between websocket.py and monitoring.py.
"""

from typing import Dict, Any, List
from datetime import datetime


# Global connection manager reference
# Will be set by websocket.py when it initializes
_manager = None


def register_manager(manager):
    """Register the WebSocket connection manager.

    This should be called by websocket.py during initialization
    to make broadcast functions available to other modules.
    """
    global _manager
    _manager = manager


def get_manager():
    """Get the registered connection manager."""
    return _manager


async def broadcast_attack_event(honeypot_id: str, event: dict):
    """Broadcast attack event to subscribers."""
    if _manager:
        await _manager.broadcast(
            {
                "type": "attack_event",
                "honeypot_id": honeypot_id,
                "data": event,
                "timestamp": datetime.utcnow().isoformat(),
            },
            channel="attacks",
        )


async def broadcast_adaptation(honeypot_id: str, adaptation: dict):
    """Broadcast adaptation event to subscribers."""
    if _manager:
        await _manager.broadcast(
            {
                "type": "adaptation",
                "honeypot_id": honeypot_id,
                "data": adaptation,
                "timestamp": datetime.utcnow().isoformat(),
            },
            channel="adaptations",
        )


async def broadcast_alert(alert: dict):
    """Broadcast alert to subscribers."""
    if _manager:
        await _manager.broadcast(
            {
                "type": "alert",
                "data": alert,
                "timestamp": datetime.utcnow().isoformat(),
            },
            channel="alerts",
        )


async def broadcast_honeypot_status(honeypot_id: str, status: str):
    """Broadcast honeypot status change."""
    if _manager:
        await _manager.broadcast(
            {
                "type": "honeypot_status",
                "honeypot_id": honeypot_id,
                "status": status,
                "timestamp": datetime.utcnow().isoformat(),
            },
            channel="honeypots",
        )


async def broadcast_new_attack(attack_data: dict):
    """Broadcast new attack detection for notifications."""
    if _manager:
        await _manager.broadcast(
            {
                "type": "new_attack",
                "data": attack_data,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )


async def broadcast_ai_decision(decision_data: dict):
    """Broadcast AI decision for notifications."""
    if _manager:
        await _manager.broadcast(
            {
                "type": "ai_decision",
                "data": decision_data,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )


async def broadcast_security_alert(alert_data: dict):
    """Broadcast security alert for notifications."""
    if _manager:
        await _manager.broadcast(
            {
                "type": "security_alert",
                "data": alert_data,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )


async def broadcast_execution_complete(execution_data: dict):
    """Broadcast execution completion for notifications."""
    if _manager:
        await _manager.broadcast(
            {
                "type": "execution_complete",
                "data": execution_data,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )


async def broadcast_cognitive_analysis(session_id: str, analysis: dict):
    """Broadcast cognitive analysis result."""
    if _manager:
        await _manager.broadcast(
            {
                "type": "cognitive_analysis",
                "session_id": session_id,
                "data": analysis,
                "timestamp": datetime.utcnow().isoformat(),
            },
            channel="cognitive",
        )


async def broadcast_deception_applied(session_id: str, deception: dict):
    """Broadcast when a deception strategy is applied."""
    if _manager:
        await _manager.broadcast(
            {
                "type": "deception_applied",
                "session_id": session_id,
                "data": deception,
                "timestamp": datetime.utcnow().isoformat(),
            },
            channel="deception",
        )


async def broadcast_bias_detected(session_id: str, bias: dict):
    """Broadcast when a cognitive bias is detected."""
    if _manager:
        await _manager.broadcast(
            {
                "type": "bias_detected",
                "session_id": session_id,
                "data": bias,
                "timestamp": datetime.utcnow().isoformat(),
            },
            channel="cognitive",
        )
