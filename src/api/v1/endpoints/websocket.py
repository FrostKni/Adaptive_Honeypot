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
from src.api.v1.endpoints.broadcast import register_manager


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
        """Broadcast message to all connections or specific channel.
        
        Clients with no subscriptions receive all messages (subscribe-all default).
        Clients with subscriptions only receive messages for their channels.
        """
        disconnected = []

        for connection in self.active_connections:
            try:
                subs = self.subscriptions.get(connection, [])
                # Skip only if client has explicit subscriptions that don't include this channel
                if channel and subs and channel not in subs:
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

# Register manager with broadcast module to avoid circular dependencies
register_manager(manager)


@router.websocket("/")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await manager.connect(websocket)

    try:
        # Send welcome message
        await manager.send_to(
            websocket,
            {
                "type": "connected",
                "timestamp": datetime.utcnow().isoformat(),
                "message": "Connected to Adaptive Honeypot real-time feed",
            },
        )

        while True:
            # Receive messages from client
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
                await handle_client_message(websocket, message)
            except json.JSONDecodeError:
                await manager.send_to(
                    websocket,
                    {
                        "type": "error",
                        "message": "Invalid JSON",
                    },
                )

    except WebSocketDisconnect:
        manager.disconnect(websocket)


async def handle_client_message(websocket: WebSocket, message: dict):
    """Handle messages from WebSocket clients."""
    msg_type = message.get("type")

    if msg_type == "subscribe":
        # Subscribe to channels
        channels = message.get("channels", [])
        manager.subscribe(websocket, channels)
        await manager.send_to(
            websocket,
            {
                "type": "subscribed",
                "channels": channels,
            },
        )

    elif msg_type == "ping":
        # Heartbeat
        await manager.send_to(
            websocket,
            {
                "type": "pong",
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    elif msg_type == "get_status":
        # Get current status
        await manager.send_to(
            websocket,
            {
                "type": "status",
                "data": {
                    "active_honeypots": 0,  # TODO: Real data
                    "active_connections": len(manager.active_connections),
                },
            },
        )

    else:
        await manager.send_to(
            websocket,
            {
                "type": "error",
                "message": f"Unknown message type: {msg_type}",
            },
        )
