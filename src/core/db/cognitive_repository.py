"""
Repository for storing and retrieving cognitive profiles from the database.
"""
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db.models import (
    CognitiveProfileDB,
    DeceptionEventDB,
    Session as DBSession,
)
from src.cognitive.profiler import CognitiveProfile, DetectedBias


logger = logging.getLogger(__name__)


class CognitiveProfileRepository:
    """
    Repository for managing cognitive profiles in the database.
    
    Provides methods to store, retrieve, and update cognitive profiles
    and deception events for attacker sessions.
    """
    
    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session.
        
        Args:
            session: SQLAlchemy async session
        """
        self.session = session
    
    async def store_profile(
        self,
        session_id: str,
        profile: CognitiveProfile,
        is_final: bool = False,
    ) -> Optional[CognitiveProfileDB]:
        """
        Store or update a cognitive profile in the database.
        
        Args:
            session_id: Session identifier
            profile: CognitiveProfile to store
            is_final: Whether this is the final profile for the session
            
        Returns:
            Stored CognitiveProfileDB instance or None on error
        """
        try:
            # Check if profile already exists for this session
            existing = await self.get_latest_profile(session_id)
            
            if existing:
                # Update existing profile
                existing.detected_biases = [b.to_dict() for b in profile.detected_biases]
                existing.beliefs = profile.mental_model.beliefs
                existing.knowledge = profile.mental_model.knowledge
                existing.goals = profile.mental_model.goals
                existing.expectations = profile.mental_model.expectations
                existing.overconfidence_score = profile.overconfidence_score
                existing.persistence_score = profile.persistence_score
                existing.tunnel_vision_score = profile.tunnel_vision_score
                existing.curiosity_score = profile.curiosity_score
                existing.exploration_diversity = profile.exploration_diversity
                existing.error_tolerance = profile.error_tolerance
                existing.learning_rate = profile.learning_rate
                existing.total_deceptions_applied = profile.total_deceptions_applied
                existing.successful_deceptions = profile.successful_deceptions
                existing.deception_success_rate = profile.deception_success_rate
                existing.suspicion_level = profile.suspicion_level
                existing.signals = profile.signals
                existing.updated_at = datetime.utcnow()
                existing.is_final = is_final
                
                await self.session.commit()
                logger.debug(f"Updated cognitive profile for session {session_id}")
                return existing
            else:
                # Create new profile
                new_profile = CognitiveProfileDB(
                    session_id=session_id,
                    detected_biases=[b.to_dict() for b in profile.detected_biases],
                    beliefs=profile.mental_model.beliefs,
                    knowledge=profile.mental_model.knowledge,
                    goals=profile.mental_model.goals,
                    expectations=profile.mental_model.expectations,
                    overconfidence_score=profile.overconfidence_score,
                    persistence_score=profile.persistence_score,
                    tunnel_vision_score=profile.tunnel_vision_score,
                    curiosity_score=profile.curiosity_score,
                    exploration_diversity=profile.exploration_diversity,
                    error_tolerance=profile.error_tolerance,
                    learning_rate=profile.learning_rate,
                    total_deceptions_applied=profile.total_deceptions_applied,
                    successful_deceptions=profile.successful_deceptions,
                    deception_success_rate=profile.deception_success_rate,
                    suspicion_level=profile.suspicion_level,
                    signals=profile.signals,
                    is_final=is_final,
                )
                
                self.session.add(new_profile)
                await self.session.commit()
                logger.debug(f"Created cognitive profile for session {session_id}")
                return new_profile
                
        except Exception as e:
            logger.error(f"Error storing cognitive profile: {e}")
            await self.session.rollback()
            return None
    
    async def get_latest_profile(self, session_id: str) -> Optional[CognitiveProfileDB]:
        """
        Get the latest cognitive profile for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Latest CognitiveProfileDB or None
        """
        try:
            stmt = select(CognitiveProfileDB).where(
                CognitiveProfileDB.session_id == session_id
            ).order_by(CognitiveProfileDB.updated_at.desc()).limit(1)
            
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting cognitive profile: {e}")
            return None
    
    async def get_recent_profiles(self, limit: int = 50) -> List[CognitiveProfileDB]:
        """
        Get recent cognitive profiles across all sessions.
        
        Args:
            limit: Maximum number of profiles to return
            
        Returns:
            List of CognitiveProfileDB instances, most recent first
        """
        try:
            # Get the latest profile for each session
            stmt = select(CognitiveProfileDB).order_by(
                CognitiveProfileDB.updated_at.desc()
            ).limit(limit)
            
            result = await self.session.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error getting recent profiles: {e}")
            return []
    
    async def store_deception_event(
        self,
        session_id: str,
        bias_type: str,
        strategy_name: str,
        trigger_command: str,
        response_type: str,
        response_content: Optional[str] = None,
        event_metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[DeceptionEventDB]:
        """
        Store a deception event in the database.
        
        Args:
            session_id: Session identifier
            bias_type: Type of bias targeted
            strategy_name: Name of strategy used
            trigger_command: Command that triggered the deception
            response_type: Type of response generated
            response_content: Actual response content
            event_metadata: Additional metadata
            
        Returns:
            Stored DeceptionEventDB instance or None on error
        """
        try:
            event = DeceptionEventDB(
                session_id=session_id,
                bias_type=bias_type,
                strategy_name=strategy_name,
                trigger_command=trigger_command,
                response_type=response_type,
                response_content=response_content,
                event_metadata=event_metadata or {},
            )
            
            self.session.add(event)
            await self.session.commit()
            logger.debug(f"Stored deception event for session {session_id}")
            return event
            
        except Exception as e:
            logger.error(f"Error storing deception event: {e}")
            await self.session.rollback()
            return None
    
    async def get_deception_events(
        self,
        session_id: str,
        limit: int = 100,
    ) -> List[DeceptionEventDB]:
        """
        Get deception events for a session.
        
        Args:
            session_id: Session identifier
            limit: Maximum number of events to return
            
        Returns:
            List of DeceptionEventDB instances
        """
        try:
            stmt = select(DeceptionEventDB).where(
                DeceptionEventDB.session_id == session_id
            ).order_by(DeceptionEventDB.created_at.desc()).limit(limit)
            
            result = await self.session.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error getting deception events: {e}")
            return []
    
    async def mark_deception_effective(
        self,
        event_id: int,
        reaction_type: Optional[str] = None,
        effectiveness_score: Optional[float] = None,
    ):
        """
        Mark a deception event as effective (attacker reacted).
        
        Args:
            event_id: Deception event ID
            reaction_type: Type of attacker reaction
            effectiveness_score: Calculated effectiveness score
        """
        try:
            stmt = select(DeceptionEventDB).where(DeceptionEventDB.id == event_id)
            result = await self.session.execute(stmt)
            event = result.scalar_one_or_none()
            
            if event:
                event.attacker_reacted = True
                event.reaction_type = reaction_type
                event.effectiveness_score = effectiveness_score
                await self.session.commit()
                logger.debug(f"Marked deception event {event_id} as effective")
                
        except Exception as e:
            logger.error(f"Error marking deception effective: {e}")
            await self.session.rollback()
    
    async def get_sessions_with_bias(
        self,
        bias_type: str,
        min_confidence: float = 0.5,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Get sessions where a specific bias was detected.
        
        Args:
            bias_type: Type of bias to search for
            min_confidence: Minimum confidence threshold
            limit: Maximum number of sessions to return
            
        Returns:
            List of session data with bias information
        """
        try:
            # This is a simplified query - in production would use JSON contains
            stmt = select(CognitiveProfileDB).order_by(
                CognitiveProfileDB.created_at.desc()
            ).limit(limit * 2)  # Get more to filter
            
            result = await self.session.execute(stmt)
            profiles = result.scalars().all()
            
            # Filter by bias type and confidence
            matching = []
            for profile in profiles:
                for bias in profile.detected_biases:
                    if (bias.get("bias_type") == bias_type and 
                        bias.get("confidence", 0) >= min_confidence):
                        matching.append({
                            "session_id": profile.session_id,
                            "bias": bias,
                            "created_at": profile.created_at.isoformat(),
                        })
                        break
                
                if len(matching) >= limit:
                    break
            
            return matching
            
        except Exception as e:
            logger.error(f"Error getting sessions with bias: {e}")
            return []
    
    async def get_deception_effectiveness_stats(self) -> Dict[str, Any]:
        """
        Get overall deception effectiveness statistics.
        
        Returns:
            Dictionary with effectiveness stats
        """
        try:
            # Get all profiles
            stmt = select(CognitiveProfileDB)
            result = await self.session.execute(stmt)
            profiles = result.scalars().all()
            
            total_deceptions = 0
            successful_deceptions = 0
            bias_counts = {}
            
            for profile in profiles:
                total_deceptions += profile.total_deceptions_applied
                successful_deceptions += profile.successful_deceptions
                
                # Count bias occurrences
                for bias in profile.detected_biases:
                    bias_type = bias.get("bias_type", "unknown")
                    bias_counts[bias_type] = bias_counts.get(bias_type, 0) + 1
            
            return {
                "total_sessions_profiled": len(profiles),
                "total_deceptions_applied": total_deceptions,
                "successful_deceptions": successful_deceptions,
                "overall_success_rate": successful_deceptions / total_deceptions if total_deceptions > 0 else 0,
                "bias_distribution": bias_counts,
            }
            
        except Exception as e:
            logger.error(f"Error getting effectiveness stats: {e}")
            return {}