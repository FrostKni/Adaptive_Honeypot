"""
AI Monitoring Service - Real-time AI workflow management.
Analyzes live events, processes logs, and dynamically reconfigures containers.
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from collections import deque

from src.core.config import settings

logger = logging.getLogger(__name__)


class AIActivityStatus(str, Enum):
    IDLE = "idle"
    ANALYZING = "analyzing"
    PROCESSING = "processing"
    RECONFIGURING = "reconfiguring"
    DECISION = "decision"
    ERROR = "error"


class ThreatLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AIActivity:
    """Single AI activity event."""

    id: str
    timestamp: datetime
    status: AIActivityStatus
    action: str
    details: Dict[str, Any]
    duration_ms: int = 0
    success: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AttackEvent:
    """Attack event for analysis."""

    id: str
    source_ip: str
    honeypot_id: str
    attack_type: str
    timestamp: datetime
    severity: str
    raw_log: str
    session_id: Optional[str] = None
    commands: List[str] = field(default_factory=list)
    credentials_tried: List[Dict] = field(default_factory=list)


@dataclass
class AIDecision:
    """AI-generated decision for container reconfiguration."""

    id: str
    timestamp: datetime
    source_ip: str
    threat_level: ThreatLevel
    threat_score: float
    reasoning: str
    action: str  # 'switch_container', 'reconfigure', 'isolate', 'monitor'
    configuration_changes: Dict[str, Any]
    confidence: float
    mitre_attack_ids: List[str] = field(default_factory=list)





class AIMonitoringService:
    """
    Central AI monitoring service.
    - Analyzes live events from all honeypots
    - Processes logs using AI/ML
    - Makes dynamic container reconfiguration decisions
    - Manages container switching without disconnecting attackers
    """

    def __init__(self):
        # Use EnhancedAIAnalyzer with full provider fallback chain
        from src.ai.analyzer import get_analyzer
        self.analyzer = get_analyzer()
        self.is_running = False
        self.status = AIActivityStatus.IDLE
        self.activities: deque = deque(maxlen=100)  # Last 100 activities
        self.decisions: deque = deque(maxlen=50)  # Last 50 decisions
        self.pending_events: deque = deque(maxlen=200)
        self.attack_thresholds = {
            "low": 10,  # events per minute
            "medium": 30,
            "high": 60,
            "critical": 100,
        }
        self.container_configs: Dict[str, Dict] = {}
        self.active_sessions: Dict[str, Dict] = {}
        self.subscribers: List = []
        self.decision_subscribers: List = []  # Subscribers for decision updates
        
        # Initialize cognitive bridge for real-time cognitive profiling
        self._cognitive_bridge = None
        self._init_cognitive_bridge()
    
    def _init_cognitive_bridge(self):
        """Initialize the cognitive integration bridge using the global singleton."""
        try:
            from src.collectors.cognitive_bridge import get_cognitive_bridge
            self._cognitive_bridge = get_cognitive_bridge()
            logger.info("Cognitive bridge initialized for AI monitoring (using global singleton)")
        except Exception as e:
            logger.warning(f"Failed to initialize cognitive bridge: {e}")
            self._cognitive_bridge = None

    async def start(self):
        """Start the AI monitoring service."""
        self.is_running = True
        logger.info("AI Monitoring Service started")

        # Start background tasks
        asyncio.create_task(self._process_event_queue())
        asyncio.create_task(self._periodic_analysis())

    async def stop(self):
        """Stop the AI monitoring service."""
        self.is_running = False
        logger.info("AI Monitoring Service stopped")

    def subscribe(self, callback):
        """Subscribe to AI activity updates."""
        self.subscribers.append(callback)

    async def _notify_subscribers(self, activity: AIActivity):
        """Notify all subscribers of new activity."""
        for callback in self.subscribers:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(activity)
                else:
                    callback(activity)
            except Exception as e:
                logger.error(f"Subscriber notification failed: {e}")

    async def _notify_decision_subscribers(self, decision: AIDecision):
        """Notify all decision subscribers of new decision."""
        for callback in self.decision_subscribers:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(decision)
                else:
                    callback(decision)
            except Exception as e:
                logger.error(f"Decision subscriber notification failed: {e}")

    def add_event(self, event: AttackEvent):
        """Add attack event to processing queue."""
        self.pending_events.append(event)
        logger.debug(f"Added event from {event.source_ip} to queue")

    async def _process_event_queue(self):
        """Process pending attack events."""
        while self.is_running:
            if self.pending_events:
                event = self.pending_events.popleft()
                await self._analyze_event(event)
            await asyncio.sleep(0.1)

    async def _periodic_analysis(self):
        """Periodic analysis of attack patterns."""
        while self.is_running:
            await asyncio.sleep(30)  # Every 30 seconds
            if len(self.active_sessions) > 0:
                await self._analyze_patterns()

    async def _broadcast_thought(self, chunk: str, full_content: str, source_ip: str):
        """Broadcast LLM thought chunk to WebSocket subscribers."""
        try:
            from src.api.v1.endpoints.broadcast import get_manager
            ws_manager = get_manager()
            if ws_manager:
                logger.debug(f"Broadcasting LLM thought to {len(ws_manager.active_connections)} connections")
                await ws_manager.broadcast({
                    "type": "llm_thought",
                    "data": {
                        "chunk": chunk,
                        "content": full_content,
                        "source_ip": source_ip,
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                }, channel="ai")
            else:
                logger.warning("WebSocket manager not available for broadcasting thoughts")
        except Exception as e:
            logger.error(f"Failed to broadcast thought: {e}")

    async def _analyze_event(self, event: AttackEvent):
        """Analyze single attack event."""
        activity_id = f"act-{int(time.time() * 1000)}"

        # Log analysis start
        activity = AIActivity(
            id=activity_id,
            timestamp=datetime.utcnow(),
            status=AIActivityStatus.ANALYZING,
            action=f"Analyzing attack from {event.source_ip}",
            details={
                "attack_type": event.attack_type,
                "honeypot_id": event.honeypot_id,
                "severity": event.severity,
            },
        )
        self.activities.append(activity)
        await self._notify_subscribers(activity)

        # Push activity to AI WebSocket channel in real-time
        try:
            from src.api.v1.endpoints.broadcast import get_manager
            ws_manager = get_manager()
            if ws_manager:
                await ws_manager.broadcast({
                    "type": "activity",
                    "data": {
                        "id": activity.id,
                        "timestamp": activity.timestamp.isoformat(),
                        "status": activity.status.value,
                        "action": activity.action,
                        "details": activity.details,
                        "duration_ms": activity.duration_ms,
                        "success": activity.success,
                    }
                }, channel="ai")
        except Exception as e:
            logger.debug(f"Failed to broadcast activity: {e}")

        self.status = AIActivityStatus.ANALYZING

        try:
            # Build event dict for EnhancedAIAnalyzer
            event_dict = {
                "source_ip": event.source_ip,
                "honeypot_id": event.honeypot_id,
                "attack_type": event.attack_type,
                "severity": event.severity,
                "timestamp": event.timestamp.isoformat(),
                "commands": event.commands,
                "credentials_tried": event.credentials_tried,
                "raw_log": event.raw_log,
            }

            start_ms = int(time.time() * 1000)
            
            # Create thought callback for streaming
            async def thought_callback(chunk: str, full_content: str):
                await self._broadcast_thought(chunk, full_content, event.source_ip)
            
            # Use EnhancedAIAnalyzer with streaming for real-time thoughts
            result = await self.analyzer.analyze_attack(
                events=[event_dict],
                context={"honeypot_id": event.honeypot_id},
                thought_callback=thought_callback,
            )
            duration_ms = int(time.time() * 1000) - start_ms

            # Map AIAnalysisResult → internal analysis dict
            analysis = {
                "threat_level": result.threat_level,
                "threat_score": {"low": 0.2, "medium": 0.5, "high": 0.75, "critical": 0.95}.get(result.threat_level, 0.2),
                "attacker_skill": result.attacker_skill_level,
                "attack_objectives": result.attack_objectives,
                "reasoning": result.reasoning,
                "confidence": result.confidence,
                "mitre_attack_ids": result.mitre_attack_ids,
                "recommended_action": result.deception_strategies[0] if result.deception_strategies else "monitor",
                "configuration_changes": result.configuration_changes,
            }

            # Create decision
            decision = AIDecision(
                id=f"dec-{int(time.time() * 1000)}",
                timestamp=datetime.utcnow(),
                source_ip=event.source_ip,
                threat_level=ThreatLevel(analysis["threat_level"]),
                threat_score=analysis["threat_score"],
                reasoning=analysis["reasoning"],
                action=self._determine_action(analysis),
                configuration_changes=analysis["configuration_changes"],
                confidence=analysis["confidence"],
                mitre_attack_ids=analysis["mitre_attack_ids"],
            )

            self.decisions.append(decision)

            # Save decision to database for persistence
            await self.save_decision_to_db(decision, event, analysis)

            # Notify decision subscribers
            await self._notify_decision_subscribers(decision)

            # Push decision to AI WebSocket channel in real-time
            try:
                from src.api.v1.endpoints.broadcast import get_manager
                ws_manager = get_manager()
                if ws_manager:
                    await ws_manager.broadcast({
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
                    }, channel="ai")
            except Exception as e:
                logger.debug(f"Failed to broadcast decision: {e}")

            # Log decision
            decision_activity = AIActivity(
                id=f"act-{int(time.time() * 1000)}",
                timestamp=datetime.utcnow(),
                status=AIActivityStatus.DECISION,
                action=f"Decision: {decision.action}",
                details={
                    "threat_level": decision.threat_level.value,
                    "threat_score": decision.threat_score,
                    "confidence": decision.confidence,
                    "reasoning": decision.reasoning[:200],
                },
                duration_ms=duration_ms,
            )
            self.activities.append(decision_activity)
            await self._notify_subscribers(decision_activity)

            # Execute decision
            await self._execute_decision(decision, event)
            
            # Process through cognitive bridge for real-time cognitive profiling
            await self._process_cognitive_analysis(event, decision, analysis)

        except Exception as e:
            logger.error(f"Event analysis failed: {e}")
            error_activity = AIActivity(
                id=f"act-{int(time.time() * 1000)}",
                timestamp=datetime.utcnow(),
                status=AIActivityStatus.ERROR,
                action="Analysis exception",
                details={"error": str(e)},
                success=False,
            )
            self.activities.append(error_activity)
            await self._notify_subscribers(error_activity)

        finally:
            self.status = AIActivityStatus.IDLE

    async def _analyze_patterns(self):
        """Analyze attack patterns across sessions."""
        activity = AIActivity(
            id=f"act-{int(time.time() * 1000)}",
            timestamp=datetime.utcnow(),
            status=AIActivityStatus.PROCESSING,
            action="Analyzing attack patterns",
            details={"active_sessions": len(self.active_sessions)},
        )
        self.activities.append(activity)
        await self._notify_subscribers(activity)

        self.status = AIActivityStatus.PROCESSING

        # Pattern analysis logic here
        await asyncio.sleep(1)  # Simulate processing

        self.status = AIActivityStatus.IDLE

    async def _execute_decision(self, decision: AIDecision, event: AttackEvent):
        """Execute AI decision - reconfigure or switch container."""
        # Import broadcast functions from broadcast module to avoid circular imports
        from src.api.v1.endpoints.broadcast import (
            broadcast_ai_decision,
            broadcast_execution_complete,
        )

        # Broadcast AI decision for notifications
        try:
            await broadcast_ai_decision(
                {
                    "action": decision.action,
                    "source_ip": decision.source_ip,
                    "threat_level": decision.threat_level.value,
                    "threat_score": decision.threat_score,
                    "reasoning": decision.reasoning[:100] if decision.reasoning else "",
                    "honeypot_id": event.honeypot_id,
                }
            )
        except Exception as e:
            logger.warning(f"Failed to broadcast AI decision: {e}")

        if decision.action == "monitor":
            activity = AIActivity(
                id=f"act-{int(time.time() * 1000)}",
                timestamp=datetime.utcnow(),
                status=AIActivityStatus.IDLE,
                action="Monitoring (no action needed)",
                details={"source_ip": decision.source_ip, "threat_score": decision.threat_score},
            )
            self.activities.append(activity)
            await self._notify_subscribers(activity)
            # Still record in executor for execution history

        else:
            activity = AIActivity(
                id=f"act-{int(time.time() * 1000)}",
                timestamp=datetime.utcnow(),
                status=AIActivityStatus.RECONFIGURING,
                action=f"Executing: {decision.action}",
                details={"source_ip": decision.source_ip, "changes": decision.configuration_changes},
            )
            self.activities.append(activity)
            await self._notify_subscribers(activity)
            self.status = AIActivityStatus.RECONFIGURING

        try:
            from src.ai.decision_executor import get_executor
            executor = get_executor()

            # Skip Docker actions when Docker is unavailable
            if executor.client is None and decision.action != "monitor":
                logger.warning("Docker unavailable — skipping execution of action: %s", decision.action)
                activity.details["skipped"] = "Docker unavailable"
                return

            result = await executor.execute(
                decision_id=decision.id,
                action=decision.action,
                source_ip=decision.source_ip,
                honeypot_id=event.honeypot_id,
                configuration_changes=decision.configuration_changes,
                threat_level=decision.threat_level.value,
            )

            # Update activity with result
            activity.details["execution_id"] = result.id
            activity.details["execution_status"] = result.status.value
            activity.details["success"] = result.status.value == "success"

            if result.error:
                activity.details["error"] = result.error
                logger.error(f"Decision execution failed: {result.error}")
            else:
                logger.info(
                    f"Decision executed successfully: {decision.action} for {decision.source_ip}"
                )

            # Broadcast execution complete for notifications
            try:
                await broadcast_execution_complete(
                    {
                        "action": decision.action,
                        "success": result.status.value == "success",
                        "honeypot_id": event.honeypot_id,
                        "source_ip": decision.source_ip,
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to broadcast execution complete: {e}")

        except Exception as e:
            logger.error(f"Decision execution failed: {e}")
            activity.details["error"] = str(e)

        self.status = AIActivityStatus.IDLE


    def _determine_action(self, analysis: Dict) -> str:
        """Determine action based on analysis."""
        threat_score = analysis.get("threat_score", 0)
        recommended = analysis.get("recommended_action", "monitor")

        # Honour AI recommendation when threat_score is high enough
        if threat_score >= 0.8:
            return (
                recommended
                if recommended in ("isolate", "switch_container")
                else "isolate"
            )
        elif threat_score >= 0.6:
            return (
                recommended
                if recommended in ("switch_container", "reconfigure")
                else "switch_container"
            )
        elif threat_score >= 0.4:
            return recommended if recommended == "reconfigure" else "reconfigure"
        return "monitor"

    def get_status(self) -> Dict[str, Any]:
        """Get current AI status."""
        provider = settings.ai.provider
        api_key = None
        if provider == "openai" and settings.ai.openai_api_key:
            api_key = settings.ai.openai_api_key.get_secret_value()
        elif provider == "anthropic" and settings.ai.anthropic_api_key:
            api_key = settings.ai.anthropic_api_key.get_secret_value()
        elif provider == "gemini" and settings.ai.gemini_api_key:
            api_key = settings.ai.gemini_api_key.get_secret_value()
        elif provider == "custom" and settings.ai.custom_api_key:
            api_key = settings.ai.custom_api_key.get_secret_value()

        return {
            "is_running": self.is_running,
            "status": self.status.value,
            "pending_events": len(self.pending_events),
            "total_activities": len(self.activities),
            "total_decisions": len(self.decisions),
            "active_sessions": len(self.active_sessions),
            "llm_available": True,
            "ai_provider": provider,
            "ai_model": settings.ai.model,
            "ai_base_url": settings.ai.base_url if provider == "custom" else None,
            "api_key_configured": bool(api_key),
        }

    def get_recent_activities(self, limit: int = 20) -> List[Dict]:
        """Get recent AI activities."""
        return [
            {
                "id": a.id,
                "timestamp": a.timestamp.isoformat(),
                "status": a.status.value,
                "action": a.action,
                "details": a.details,
                "duration_ms": a.duration_ms,
                "success": a.success,
            }
            for a in list(self.activities)[-limit:]
        ]

    def get_recent_decisions(self, limit: int = 10) -> List[Dict]:
        """Get recent AI decisions."""
        return [
            {
                "id": d.id,
                "timestamp": d.timestamp.isoformat(),
                "source_ip": d.source_ip,
                "threat_level": d.threat_level.value,
                "threat_score": d.threat_score,
                "reasoning": d.reasoning,
                "action": d.action,
                "confidence": d.confidence,
                "mitre_attack_ids": d.mitre_attack_ids,
            }
            for d in list(self.decisions)[-limit:]
        ]

    async def save_decision_to_db(self, decision: AIDecision, event: AttackEvent, analysis: Dict):
        """Save AI decision to database for persistence."""
        try:
            from src.core.db.session import get_db_context
            from src.core.db.repositories import AIDecisionRepository

            async with get_db_context() as session:
                repo = AIDecisionRepository(session)
                # AIDecisionDB has no session_id FK — do not pass it
                await repo.create(
                    id=decision.id,
                    source_ip=decision.source_ip,
                    honeypot_id=event.honeypot_id,
                    threat_level=decision.threat_level.value,
                    threat_score=decision.threat_score,
                    confidence=decision.confidence,
                    action=decision.action,
                    reasoning=decision.reasoning,
                    configuration_changes=decision.configuration_changes,
                    mitre_attack_ids=decision.mitre_attack_ids,
                    attacker_skill=analysis.get("attacker_skill"),
                    attack_objectives=analysis.get("attack_objectives", []),
                )
                logger.info(f"Saved decision {decision.id} to database")
        except Exception as e:
            logger.error(f"Failed to save decision to database: {e}")
    
    async def _process_cognitive_analysis(self, event: AttackEvent, decision: AIDecision, analysis: Dict):
        """
        Process attack event through cognitive bridge for real-time cognitive profiling.
        This creates cognitive profiles that appear in the Cognitive Dashboard.
        """
        if not self._cognitive_bridge:
            logger.debug("Cognitive bridge not available, skipping cognitive analysis")
            return
        
        try:
            # Use session_id from event or create one from source_ip
            session_id = event.session_id or f"session-{event.source_ip}-{int(event.timestamp.timestamp())}"
            
            # Process each command through cognitive bridge
            if event.commands:
                for command in event.commands:
                    try:
                        result = await self._cognitive_bridge.process_command(
                            session_id=session_id,
                            command=command,
                            source_ip=event.source_ip,
                            session_data={
                                "honeypot_id": event.honeypot_id,
                                "attack_type": event.attack_type,
                                "threat_level": decision.threat_level.value,
                                "threat_score": decision.threat_score,
                                "attacker_skill": analysis.get("attacker_skill"),
                                "attack_objectives": analysis.get("attack_objectives", []),
                            }
                        )
                        logger.info(f"Cognitive analysis completed for session {session_id}: {len(result.biases_detected)} biases detected")
                    except Exception as e:
                        logger.warning(f"Failed to process command through cognitive bridge: {e}")
            else:
                # Process the raw log as a single command for cognitive profiling
                if event.raw_log:
                    try:
                        result = await self._cognitive_bridge.process_command(
                            session_id=session_id,
                            command=event.raw_log[:500],  # Limit length
                            source_ip=event.source_ip,
                            session_data={
                                "honeypot_id": event.honeypot_id,
                                "attack_type": event.attack_type,
                                "threat_level": decision.threat_level.value,
                                "threat_score": decision.threat_score,
                                "attacker_skill": analysis.get("attacker_skill"),
                                "attack_objectives": analysis.get("attack_objectives", []),
                            }
                        )
                        logger.info(f"Cognitive analysis completed for session {session_id}: {len(result.biases_detected)} biases detected")
                    except Exception as e:
                        logger.warning(f"Failed to process raw log through cognitive bridge: {e}")
            
            # Update active sessions for tracking
            if session_id not in self.active_sessions:
                self.active_sessions[session_id] = {
                    "source_ip": event.source_ip,
                    "honeypot_id": event.honeypot_id,
                    "first_seen": event.timestamp.isoformat(),
                    "last_activity": datetime.utcnow().isoformat(),
                    "threat_score": decision.threat_score,
                    "threat_level": decision.threat_level.value,
                }
            else:
                self.active_sessions[session_id]["last_activity"] = datetime.utcnow().isoformat()
                self.active_sessions[session_id]["threat_score"] = decision.threat_score
                
        except Exception as e:
            logger.error(f"Cognitive analysis failed: {e}")


# Global AI monitoring service instance
ai_service = AIMonitoringService()
