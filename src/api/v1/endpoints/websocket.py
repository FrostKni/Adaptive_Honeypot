"""
WebSocket endpoint for real-time updates.
"""
from typing import List, Dict, Any
from datetime import datetime
import json
import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from pydantic import BaseModel

from src.core.security import AuthContext


router = APIRouter()


class ConnectionManager:
    """WebSocket connection manager."""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.subscriptions: Dict[WebSocket, List[str]] = {}
    
    async def connect(self, websocket: WebSocket):
        """Accept a new connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.subscriptions[websocket] = []
    
    def disconnect(self, websocket: WebSocket):
        """Remove a connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if websocket in self.subscriptions:
            del self.subscriptions[websocket]
    
    def subscribe(self, websocket: WebSocket, channels: List[str]):
        """Subscribe a connection to channels."""
        self.subscriptions[websocket] = channels
    
    async def broadcast(self, message: dict, channel: str = None):
        """Broadcast message to all connections or specific channel."""
        disconnected = []
        
        for connection in self.active_connections:
            try:
                # Check channel subscription
                if channel and channel not in self.subscriptions.get(connection, []):
                    continue
                
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)
        
        for conn in disconnected:
            self.disconnect(conn)
    
    async def send_to(self, websocket: WebSocket, message: dict):
        """Send message to specific connection."""
        try:
            await websocket.send_json(message)
        except Exception:
            self.disconnect(websocket)


manager = ConnectionManager()


@router.websocket("/")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await manager.connect(websocket)
    
    try:
        # Send welcome message
        await manager.send_to(websocket, {
            "type": "connected",
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Connected to Adaptive Honeypot real-time feed",
        })
        
        while True:
            # Receive messages from client
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                await handle_client_message(websocket, message)
            except json.JSONDecodeError:
                await manager.send_to(websocket, {
                    "type": "error",
                    "message": "Invalid JSON",
                })
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)


async def handle_client_message(websocket: WebSocket, message: dict):
    """Handle messages from WebSocket clients."""
    msg_type = message.get("type")
    
    if msg_type == "subscribe":
        # Subscribe to channels
        channels = message.get("channels", [])
        manager.subscribe(websocket, channels)
        await manager.send_to(websocket, {
            "type": "subscribed",
            "channels": channels,
        })
    
    elif msg_type == "ping":
        # Heartbeat
        await manager.send_to(websocket, {
            "type": "pong",
            "timestamp": datetime.utcnow().isoformat(),
        })
    
    elif msg_type == "get_status":
        # Get current status
        await manager.send_to(websocket, {
            "type": "status",
            "data": {
                "active_honeypots": 0,  # TODO: Real data
                "active_connections": len(manager.active_connections),
            },
        })
    
    else:
        await manager.send_to(websocket, {
            "type": "error",
            "message": f"Unknown message type: {msg_type}",
        })


# ==================== Broadcast Functions ====================

async def broadcast_attack_event(honeypot_id: str, event: dict):
    """Broadcast attack event to subscribers."""
    await manager.broadcast({
        "type": "attack_event",
        "honeypot_id": honeypot_id,
        "data": event,
        "timestamp": datetime.utcnow().isoformat(),
    }, channel="attacks")


async def broadcast_adaptation(honeypot_id: str, adaptation: dict):
    """Broadcast adaptation event to subscribers."""
    await manager.broadcast({
        "type": "adaptation",
        "honeypot_id": honeypot_id,
        "data": adaptation,
        "timestamp": datetime.utcnow().isoformat(),
    }, channel="adaptations")


async def broadcast_alert(alert: dict):
    """Broadcast alert to subscribers."""
    await manager.broadcast({
        "type": "alert",
        "data": alert,
        "timestamp": datetime.utcnow().isoformat(),
    }, channel="alerts")


async def broadcast_honeypot_status(honeypot_id: str, status: str):
    """Broadcast honeypot status change."""
    await manager.broadcast({
        "type": "honeypot_status",
        "honeypot_id": honeypot_id,
        "status": status,
        "timestamp": datetime.utcnow().isoformat(),
    }, channel="honeypots")


async def broadcast_new_attack(attack_data: dict):
    """Broadcast new attack detection for notifications."""
    await manager.broadcast({
        "type": "new_attack",
        "data": attack_data,
        "timestamp": datetime.utcnow().isoformat(),
    })


async def broadcast_ai_decision(decision_data: dict):
    """Broadcast AI decision for notifications."""
    await manager.broadcast({
        "type": "ai_decision",
        "data": decision_data,
        "timestamp": datetime.utcnow().isoformat(),
    })


async def broadcast_security_alert(alert_data: dict):
    """Broadcast security alert for notifications."""
    await manager.broadcast({
        "type": "security_alert",
        "data": alert_data,
        "timestamp": datetime.utcnow().isoformat(),
    })


async def broadcast_execution_complete(execution_data: dict):
    """Broadcast execution completion for notifications."""
    await manager.broadcast({
        "type": "execution_complete",
        "data": execution_data,
        "timestamp": datetime.utcnow().isoformat(),
    })


async def broadcast_cognitive_analysis(session_id: str, analysis: dict):
    """Broadcast cognitive analysis result."""
    await manager.broadcast({
        "type": "cognitive_analysis",
        "session_id": session_id,
        "data": analysis,
        "timestamp": datetime.utcnow().isoformat(),
    }, channel="cognitive")


async def broadcast_deception_applied(session_id: str, deception: dict):
    """Broadcast when a deception strategy is applied."""
    await manager.broadcast({
        "type": "deception_applied",
        "session_id": session_id,
        "data": deception,
        "timestamp": datetime.utcnow().isoformat(),
    }, channel="deception")


async def broadcast_bias_detected(session_id: str, bias: dict):
    """Broadcast when a cognitive bias is detected."""
    await manager.broadcast({
        "type": "bias_detected",
        "session_id": session_id,
        "data": bias,
        "timestamp": datetime.utcnow().isoformat(),
    }, channel="cognitive")