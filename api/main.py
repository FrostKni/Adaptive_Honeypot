from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from typing import List, Dict
import asyncio
import logging
from datetime import datetime
from core.orchestrator import AdaptiveOrchestrator
from core.models import HoneypotConfig
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Adaptive Honeypot API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global orchestrator instance
orchestrator = AdaptiveOrchestrator()

# WebSocket connections
active_connections: List[WebSocket] = []

class DeployRequest(BaseModel):
    name: str
    port: int = 2222

class ConfigUpdateRequest(BaseModel):
    honeypot_id: str
    config: Dict

@app.on_event("startup")
async def startup_event():
    """Start orchestrator on API startup"""
    asyncio.create_task(orchestrator.start())
    logger.info("API started")

@app.on_event("shutdown")
async def shutdown_event():
    """Stop orchestrator on API shutdown"""
    await orchestrator.stop()
    logger.info("API stopped")

@app.get("/")
async def root():
    return {"message": "Adaptive Honeypot API", "status": "running"}

@app.get("/status")
async def get_status():
    """Get orchestrator status"""
    return orchestrator.get_status()

@app.post("/honeypots/deploy")
async def deploy_honeypot(request: DeployRequest):
    """Deploy a new honeypot"""
    honeypot_id = await orchestrator.deploy_new_honeypot(request.name, request.port)
    
    if honeypot_id:
        await broadcast_update({
            "type": "honeypot_deployed",
            "honeypot_id": honeypot_id,
            "timestamp": datetime.now().isoformat()
        })
        return {"success": True, "honeypot_id": honeypot_id}
    
    raise HTTPException(status_code=500, detail="Deployment failed")

@app.delete("/honeypots/{honeypot_id}")
async def remove_honeypot(honeypot_id: str):
    """Remove a honeypot"""
    success = await orchestrator.remove_honeypot(honeypot_id)
    
    if success:
        await broadcast_update({
            "type": "honeypot_removed",
            "honeypot_id": honeypot_id,
            "timestamp": datetime.now().isoformat()
        })
        return {"success": True}
    
    raise HTTPException(status_code=404, detail="Honeypot not found")

@app.get("/honeypots")
async def list_honeypots():
    """List all active honeypots"""
    return orchestrator.deployment.list_honeypots()

@app.get("/honeypots/{honeypot_id}/health")
async def get_honeypot_health(honeypot_id: str):
    """Get honeypot health status"""
    health = orchestrator.deployment.check_health(honeypot_id)
    
    if health:
        return health.model_dump()
    
    raise HTTPException(status_code=404, detail="Honeypot not found")

@app.get("/honeypots/{honeypot_id}/logs")
async def get_honeypot_logs(honeypot_id: str, limit: int = 100):
    """Get honeypot logs"""
    events = orchestrator.log_processor.watch_logs(honeypot_id)
    return [event.model_dump() for event in events[-limit:]]

@app.get("/honeypots/{honeypot_id}/stats")
async def get_honeypot_stats(honeypot_id: str):
    """Get honeypot statistics"""
    events = orchestrator.log_processor.watch_logs(honeypot_id)
    stats = orchestrator.log_processor.aggregate_events(events)
    return stats

@app.get("/adaptations")
async def get_adaptations():
    """Get adaptation history"""
    return [decision.model_dump() for decision in orchestrator.adaptation_history]

@app.post("/honeypots/{honeypot_id}/restart")
async def restart_honeypot(honeypot_id: str):
    """Restart a honeypot"""
    success = orchestrator.deployment.restart_honeypot(honeypot_id)
    
    if success:
        return {"success": True}
    
    raise HTTPException(status_code=500, detail="Restart failed")

@app.get("/resources")
async def get_resources():
    """Get system resource usage"""
    return orchestrator.resource_monitor.get_system_stats()

@app.get("/events/recent")
async def get_recent_events(limit: int = 50):
    """Get recent attack events from all honeypots"""
    all_events = []
    honeypots = orchestrator.deployment.list_honeypots()
    
    for hp in honeypots:
        events = orchestrator.log_processor.watch_logs(hp['id'])
        all_events.extend(events)
    
    # Sort by timestamp descending
    all_events.sort(key=lambda x: x.timestamp, reverse=True)
    
    return [event.model_dump() for event in all_events[:limit]]

@app.get("/honeypots/{honeypot_id}/container-logs")
async def get_container_logs(honeypot_id: str, tail: int = 100):
    """Get container logs for debugging"""
    logs = orchestrator.deployment.get_container_logs(honeypot_id, tail)
    return {"logs": logs}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        while True:
            # Send periodic updates
            status = orchestrator.get_status()
            await websocket.send_json({
                "type": "status_update",
                "data": status,
                "timestamp": datetime.now().isoformat()
            })
            
            await asyncio.sleep(5)
            
    except (WebSocketDisconnect, Exception) as e:
        if websocket in active_connections:
            active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected: {e}")

async def broadcast_update(message: Dict):
    """Broadcast message to all connected WebSocket clients"""
    disconnected = []
    for connection in active_connections:
        try:
            await connection.send_json(message)
        except Exception:
            disconnected.append(connection)
    
    for conn in disconnected:
        if conn in active_connections:
            active_connections.remove(conn)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
