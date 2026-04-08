"""
Cowrie-Cognitive Integration Bridge.

Routes real attacker commands through the Cognitive Deception Engine,
stores cognitive profiles, and broadcasts analysis via WebSocket.
"""
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict
import json

from src.cognitive.engine import CognitiveDeceptionEngine, DeceptionResponse
from src.cognitive.profiler import CognitiveProfile, CognitiveBiasType


logger = logging.getLogger(__name__)


@dataclass
class CognitiveAnalysisResult:
    """Result of cognitive analysis for a command."""
    session_id: str
    command: str
    deception_response: DeceptionResponse
    profile: Dict[str, Any]
    biases_detected: List[Dict[str, Any]]
    mental_model: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "command": self.command,
            "deception_response": self.deception_response.to_dict(),
            "profile": self.profile,
            "biases_detected": self.biases_detected,
            "mental_model": self.mental_model,
            "timestamp": self.timestamp.isoformat(),
        }


class CognitiveIntegrationBridge:
    """
    Bridge between Cowrie honeypot events and the Cognitive Deception Engine.
    
    Responsibilities:
    - Route commands through cognitive engine for analysis
    - Store cognitive profiles in database
    - Broadcast cognitive analysis via WebSocket
    - Track deception effectiveness
    """
    
    def __init__(self, engine: Optional[CognitiveDeceptionEngine] = None):
        """
        Initialize the cognitive integration bridge.
        
        Args:
            engine: Optional pre-configured CognitiveDeceptionEngine
        """
        self.engine = engine or CognitiveDeceptionEngine()
        self._session_commands: Dict[str, List[str]] = {}
        self._session_events: Dict[str, List[Dict[str, Any]]] = {}
        self._ws_manager = None
        self._db_session_factory = None
        logger.info("CognitiveIntegrationBridge initialized")
    
    def set_ws_manager(self, manager):
        """Set WebSocket manager for broadcasting cognitive events."""
        self._ws_manager = manager
    
    def set_db_session_factory(self, factory):
        """Set database session factory for profile persistence."""
        self._db_session_factory = factory
    
    async def process_command(
        self,
        session_id: str,
        command: str,
        source_ip: str,
        session_data: Optional[Dict[str, Any]] = None,
    ) -> CognitiveAnalysisResult:
        """
        Process a command through the cognitive deception pipeline.
        
        Args:
            session_id: Unique session identifier
            command: The attacker command to process
            source_ip: Source IP of the attacker
            session_data: Additional session context
            
        Returns:
            CognitiveAnalysisResult with deception response and profile
        """
        # Track commands for this session
        if session_id not in self._session_commands:
            self._session_commands[session_id] = []
        self._session_commands[session_id].append(command)
        
        # Build session data with accumulated context
        enriched_session_data = self._build_session_data(
            session_id=session_id,
            source_ip=source_ip,
            session_data=session_data,
        )
        
        # Process through cognitive engine
        try:
            deception_response = await self.engine.process_command(
                session_id=session_id,
                command=command,
                session_data=enriched_session_data,
            )
            
            # Get updated profile
            profile = self.engine.get_profile(session_id)
            
            # Create analysis result
            result = CognitiveAnalysisResult(
                session_id=session_id,
                command=command,
                deception_response=deception_response,
                profile=profile.to_dict() if profile else {},
                biases_detected=[b.to_dict() for b in profile.detected_biases] if profile else [],
                mental_model=profile.mental_model.to_dict() if profile else {},
            )
            
            # Store cognitive profile in database
            await self._store_cognitive_profile(session_id, profile, source_ip)
            
            # Store deception event
            await self._store_deception_event(
                session_id=session_id,
                command=command,
                response=deception_response,
            )
            
            # Broadcast via WebSocket
            await self._broadcast_cognitive_analysis(result)
            
            logger.info(
                f"Cognitive analysis for session {session_id}: "
                f"strategy={deception_response.strategy_used}, "
                f"bias={deception_response.bias_targeted.value}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error in cognitive processing: {e}")
            # Return fallback result
            return CognitiveAnalysisResult(
                session_id=session_id,
                command=command,
                deception_response=DeceptionResponse(
                    content="",
                    response_type="error",
                    strategy_used="fallback",
                    bias_targeted=CognitiveBiasType.CONFIRMATION_BIAS,
                    metadata={"error": str(e)},
                ),
                profile={},
                biases_detected=[],
                mental_model={},
            )
    
    async def record_event(
        self,
        session_id: str,
        event_type: str,
        event_data: Dict[str, Any],
    ):
        """
        Record a session event for cognitive profiling.
        
        Events like login attempts, errors, etc. inform the cognitive profile.
        
        Args:
            session_id: Unique session identifier
            event_type: Type of event (login, error, etc.)
            event_data: Event details
        """
        if session_id not in self._session_events:
            self._session_events[session_id] = []
        
        self._session_events[session_id].append({
            "event_type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            **event_data,
        })
        
        # Update profile if exists
        profile = self.engine.get_profile(session_id)
        if profile:
            # Update signals based on event
            if event_type == "error":
                profile.signals["error_count"] = profile.signals.get("error_count", 0) + 1
            elif event_type == "login_failed":
                profile.signals["failed_attempts"] = profile.signals.get("failed_attempts", 0) + 1
    
    async def end_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        End a session and finalize cognitive analysis.
        
        Args:
            session_id: Session to end
            
        Returns:
            Final cognitive profile summary
        """
        # Get final profile
        profile = self.engine.get_profile(session_id)
        
        if profile:
            # Calculate final metrics
            final_profile = profile.to_dict()
            
            # Add session summary
            commands = self._session_commands.get(session_id, [])
            events = self._session_events.get(session_id, [])
            
            summary = {
                "session_id": session_id,
                "total_commands": len(commands),
                "total_events": len(events),
                "final_profile": final_profile,
                "ended_at": datetime.utcnow().isoformat(),
            }
            
            # Store final profile
            await self._store_cognitive_profile(
                session_id=session_id,
                profile=profile,
                source_ip=profile.signals.get("source_ip", "unknown"),
                is_final=True,
            )
            
            # Broadcast session end
            await self._broadcast_session_end(session_id, summary)
            
            # Clean up
            self._session_commands.pop(session_id, None)
            self._session_events.pop(session_id, None)
            
            # End session in engine
            self.engine.end_session(session_id)
            
            logger.info(f"Session {session_id} ended with {len(commands)} commands")
            return summary
        
        return None
    
    def get_session_commands(self, session_id: str) -> List[str]:
        """Get all commands for a session."""
        return self._session_commands.get(session_id, [])
    
    def get_session_events(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all events for a session."""
        return self._session_events.get(session_id, [])
    
    def _build_session_data(
        self,
        session_id: str,
        source_ip: str,
        session_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Build enriched session data for cognitive analysis."""
        commands = self._session_commands.get(session_id, [])
        events = self._session_events.get(session_id, [])
        
        # Calculate session duration
        started_at = session_data.get("started_at") if session_data else None
        if started_at:
            if isinstance(started_at, str):
                started_at = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
            duration = (datetime.utcnow() - started_at.replace(tzinfo=None)).total_seconds()
        else:
            duration = 0
        
        return {
            "commands": commands,
            "events": events,
            "source_ip": source_ip,
            "duration_seconds": duration,
            **(session_data or {}),
        }
    
    async def _store_cognitive_profile(
        self,
        session_id: str,
        profile: Optional[CognitiveProfile],
        source_ip: str,
        is_final: bool = False,
    ):
        """Store cognitive profile in database."""
        if not profile:
            return
        
        try:
            from src.core.db.session import get_db_context
            from src.core.db.models import Session as DBSession
            from src.core.db.cognitive_repository import CognitiveProfileRepository

            async with get_db_context() as db_session:
                try:
                    repo = CognitiveProfileRepository(db_session)
                    await repo.store_profile(
                        session_id=session_id,
                        profile=profile,
                        is_final=is_final,
                    )

                    db_sess = await db_session.get(DBSession, session_id)
                    if db_sess and not db_sess.attacker_skill:
                        db_sess.attacker_skill = self._infer_skill_level(profile)
                        await db_session.commit()

                    logger.debug(f"Stored cognitive profile for session {session_id}")

                except Exception as e:
                    logger.error(f"Error storing cognitive profile: {e}")
                    await db_session.rollback()

        except Exception as e:
            logger.debug(f"Could not store cognitive profile: {e}")
    
    async def _store_deception_event(
        self,
        session_id: str,
        command: str,
        response: DeceptionResponse,
    ):
        """Store a deception event in the database."""
        try:
            from src.core.db.session import get_db_context
            from src.core.db.cognitive_repository import CognitiveProfileRepository

            async with get_db_context() as db_session:
                try:
                    repo = CognitiveProfileRepository(db_session)
                    await repo.store_deception_event(
                        session_id=session_id,
                        bias_type=response.bias_targeted.value,
                        strategy_name=response.strategy_used,
                        trigger_command=command,
                        response_type=response.response_type,
                        response_content=response.content[:1000] if response.content else None,
                        event_metadata=response.metadata,
                    )
                    logger.debug(f"Stored deception event for session {session_id}")
                except Exception as e:
                    logger.error(f"Error storing deception event: {e}")
                    await db_session.rollback()
        except Exception as e:
            logger.debug(f"Could not store deception event: {e}")
    
    def _infer_skill_level(self, profile: CognitiveProfile) -> str:
        """Infer attacker skill level from cognitive profile."""
        if profile.overconfidence_score > 0.7:
            return "novice"
        elif profile.learning_rate > 0.7:
            return "advanced"
        elif profile.exploration_diversity > 0.7:
            return "intermediate"
        elif profile.curiosity_score > 0.7:
            return "explorer"
        else:
            return "unknown"
    
    async def _broadcast_cognitive_analysis(self, result: CognitiveAnalysisResult):
        """Broadcast cognitive analysis via WebSocket."""
        if not self._ws_manager:
            # Try to import the websocket manager
            try:
                from src.api.v1.endpoints.websocket import manager as ws_manager
                from src.api.v1.endpoints.websocket import broadcast_ai_decision
                self._ws_manager = ws_manager
            except ImportError:
                logger.debug("WebSocket manager not available")
                return
        
        try:
            # Broadcast as AI decision
            message = {
                "type": "cognitive_analysis",
                "data": result.to_dict(),
                "timestamp": datetime.utcnow().isoformat(),
            }
            
            await self._ws_manager.broadcast(message)
            
            # Also broadcast to cognitive channel
            await self._ws_manager.broadcast(message, channel="cognitive")
            
            logger.debug(f"Broadcast cognitive analysis for session {result.session_id}")
            
        except Exception as e:
            logger.debug(f"Failed to broadcast cognitive analysis: {e}")
    
    async def _broadcast_session_end(
        self,
        session_id: str,
        summary: Dict[str, Any],
    ):
        """Broadcast session end with cognitive summary."""
        if not self._ws_manager:
            try:
                from src.api.v1.endpoints.websocket import manager as ws_manager
                self._ws_manager = ws_manager
            except ImportError:
                return
        
        try:
            await self._ws_manager.broadcast({
                "type": "cognitive_session_end",
                "session_id": session_id,
                "summary": summary,
                "timestamp": datetime.utcnow().isoformat(),
            }, channel="cognitive")
        except Exception as e:
            logger.debug(f"Failed to broadcast session end: {e}")


# Global bridge instance
_bridge: Optional[CognitiveIntegrationBridge] = None


def get_cognitive_bridge() -> CognitiveIntegrationBridge:
    """Get the global cognitive integration bridge instance."""
    global _bridge
    if _bridge is None:
        _bridge = CognitiveIntegrationBridge()
    return _bridge


async def process_command_cognitively(
    session_id: str,
    command: str,
    source_ip: str,
    session_data: Optional[Dict[str, Any]] = None,
) -> CognitiveAnalysisResult:
    """
    Convenience function to process a command through the cognitive bridge.
    
    Args:
        session_id: Unique session identifier
        command: The attacker command
        source_ip: Source IP of the attacker
        session_data: Additional session context
        
    Returns:
        CognitiveAnalysisResult with deception response
    """
    bridge = get_cognitive_bridge()
    return await bridge.process_command(
        session_id=session_id,
        command=command,
        source_ip=source_ip,
        session_data=session_data,
    )