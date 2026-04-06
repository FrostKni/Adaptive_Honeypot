"""
AI Monitoring Service - Real-time AI workflow management.
Analyzes live events, processes logs, and dynamically reconfigures containers.
"""

import asyncio
import json
import logging
import time
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from collections import deque

import httpx

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


class LocalLLMClient:
    """Client for local LLM (api.ai.oac)."""

    def __init__(self, base_url: str = "https://api.ai.oac/v1", api_key: str = None):
        self.base_url = base_url
        self.api_key = api_key or os.environ.get("MY_API_KEY", "local")
        self.model = "DeepSeek"
        self.client = httpx.AsyncClient(timeout=30.0)

    async def generate(
        self,
        prompt: str,
        system_prompt: str = None,
        temperature: float = 0.3,
        max_tokens: int = 2000,
    ) -> Dict[str, Any]:
        """Generate response from local LLM."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            start_time = time.time()
            response = await self.client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
            )
            duration_ms = int((time.time() - start_time) * 1000)

            if response.status_code == 200:
                data = response.json()
                message = data["choices"][0]["message"]
                # Handle both 'content' and 'reasoning_content' (DeepSeek)
                content = message.get("content") or message.get("reasoning_content", "")
                return {
                    "content": content,
                    "tokens_used": data.get("usage", {}).get("total_tokens", 0),
                    "duration_ms": duration_ms,
                    "success": True,
                }
            else:
                logger.error(f"LLM error: {response.status_code} - {response.text}")
                return {
                    "content": "",
                    "error": response.text,
                    "duration_ms": duration_ms,
                    "success": False,
                }
        except Exception as e:
            logger.error(f"LLM request failed: {e}")
            return {"content": "", "error": str(e), "duration_ms": 0, "success": False}

    async def health_check(self) -> bool:
        """Check if LLM is available."""
        try:
            response = await self.client.get(f"{self.base_url}/health", timeout=5.0)
            return response.status_code == 200
        except:
            return False


class AIMonitoringService:
    """
    Central AI monitoring service.
    - Analyzes live events from all honeypots
    - Processes logs using AI/ML
    - Makes dynamic container reconfiguration decisions
    - Manages container switching without disconnecting attackers
    """

    def __init__(self):
        self.llm_client = LocalLLMClient()
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

        self.status = AIActivityStatus.ANALYZING

        try:
            # Build analysis prompt
            prompt = self._build_analysis_prompt(event)

            # Get AI analysis
            response = await self.llm_client.generate(
                prompt=prompt, system_prompt=self._get_system_prompt(), temperature=0.3
            )

            if response["success"]:
                # Parse AI response
                analysis = self._parse_analysis(response["content"])

                # Create decision
                decision = AIDecision(
                    id=f"dec-{int(time.time() * 1000)}",
                    timestamp=datetime.utcnow(),
                    source_ip=event.source_ip,
                    threat_level=ThreatLevel(analysis.get("threat_level", "low")),
                    threat_score=analysis.get("threat_score", 0.0),
                    reasoning=analysis.get("reasoning", ""),
                    action=self._determine_action(analysis),
                    configuration_changes=analysis.get("configuration_changes", {}),
                    confidence=analysis.get("confidence", 0.5),
                    mitre_attack_ids=analysis.get("mitre_attack_ids", []),
                )

                self.decisions.append(decision)

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
                    duration_ms=response["duration_ms"],
                )
                self.activities.append(decision_activity)
                await self._notify_subscribers(decision_activity)

                # Execute decision
                await self._execute_decision(decision, event)

            else:
                # Log error
                error_activity = AIActivity(
                    id=f"act-{int(time.time() * 1000)}",
                    timestamp=datetime.utcnow(),
                    status=AIActivityStatus.ERROR,
                    action="Analysis failed",
                    details={"error": response.get("error", "Unknown error")},
                    success=False,
                )
                self.activities.append(error_activity)
                await self._notify_subscribers(error_activity)

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
            # Just continue monitoring, no action needed
            activity = AIActivity(
                id=f"act-{int(time.time() * 1000)}",
                timestamp=datetime.utcnow(),
                status=AIActivityStatus.IDLE,
                action="Monitoring (no action needed)",
                details={
                    "source_ip": decision.source_ip,
                    "threat_score": decision.threat_score,
                },
            )
            self.activities.append(activity)
            await self._notify_subscribers(activity)
            return

        activity = AIActivity(
            id=f"act-{int(time.time() * 1000)}",
            timestamp=datetime.utcnow(),
            status=AIActivityStatus.RECONFIGURING,
            action=f"Executing: {decision.action}",
            details={
                "source_ip": decision.source_ip,
                "changes": decision.configuration_changes,
            },
        )
        self.activities.append(activity)
        await self._notify_subscribers(activity)

        self.status = AIActivityStatus.RECONFIGURING

        try:
            # Import and use the decision executor
            from src.ai.decision_executor import get_executor

            executor = get_executor()

            # Execute the decision
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

    def _build_analysis_prompt(self, event: AttackEvent) -> str:
        """Build analysis prompt for LLM."""
        return f"""Analyze this honeypot attack event and provide a threat assessment.

Event Details:
- Source IP: {event.source_ip}
- Honeypot: {event.honeypot_id}
- Attack Type: {event.attack_type}
- Severity: {event.severity}
- Timestamp: {event.timestamp.isoformat()}
- Commands: {json.dumps(event.commands[:10])}
- Credentials Tried: {len(event.credentials_tried)} attempts

Raw Log:
{event.raw_log[:1000]}

Provide analysis as JSON:
{{
  "threat_level": "low|medium|high|critical",
  "threat_score": 0.0-1.0,
  "attacker_skill": "script_kiddie|intermediate|advanced|expert",
  "attack_objectives": ["list of objectives"],
  "reasoning": "brief explanation",
  "confidence": 0.0-1.0,
  "mitre_attack_ids": ["Txxxx"],
  "recommended_action": "monitor|reconfigure|switch_container|isolate",
  "configuration_changes": {{}}
}}"""

    def _get_system_prompt(self) -> str:
        """Get system prompt for AI."""
        return """You are a cybersecurity AI analyzing honeypot attacks in real-time.
Your role is to:
1. Assess threat levels accurately
2. Identify attacker objectives and skill level
3. Recommend appropriate defensive actions
4. Suggest configuration changes to enhance deception

Always respond with valid JSON. Be concise and actionable."""

    def _parse_analysis(self, content: str) -> Dict:
        """Parse AI analysis response."""
        try:
            # Try to extract JSON from response
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            return json.loads(content.strip())
        except:
            return {
                "threat_level": "low",
                "threat_score": 0.3,
                "reasoning": "Failed to parse AI response",
                "confidence": 0.1,
                "recommended_action": "monitor",
            }

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
        return {
            "is_running": self.is_running,
            "status": self.status.value,
            "pending_events": len(self.pending_events),
            "total_activities": len(self.activities),
            "total_decisions": len(self.decisions),
            "active_sessions": len(self.active_sessions),
            "llm_available": True,  # Would check actual LLM status
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


# Global AI monitoring service instance
ai_service = AIMonitoringService()
