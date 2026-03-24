"""
Cognitive-Behavioral Deception Framework - Database Models.

Extends the existing database schema with cognitive profiling and deception tracking.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, JSON, Text,
    ForeignKey, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB

from src.core.db.models import Base, Session


class CognitiveBiasType(str, Enum):
    """Types of cognitive biases that can be exploited."""
    CONFIRMATION_BIAS = "confirmation_bias"
    ANCHORING = "anchoring"
    SUNK_COST = "sunk_cost"
    DUNNING_KRUGER = "dunning_kruger"
    AVAILABILITY_HEURISTIC = "availability_heuristic"
    LOSS_AVERSION = "loss_aversion"
    AUTHORITY_BIAS = "authority_bias"
    CURIOSITY_GAP = "curiosity_gap"
    RECENCY_BIAS = "recency_bias"
    GAMBLER_FALLACY = "gambler_fallacy"


class DeceptionResponseType(str, Enum):
    """Types of deception responses."""
    COMMAND_OUTPUT = "command_output"
    FILE_CONTENT = "file_content"
    DIRECTORY_LISTING = "directory_listing"
    NETWORK_RESPONSE = "network_response"
    ERROR_MESSAGE = "error_message"
    PROCESS_LISTING = "process_listing"
    USER_INFO = "user_info"
    SYSTEM_INFO = "system_info"


class DetectedBias(Base):
    """
    Detected cognitive bias in an attacker session.
    
    Tracks which biases the attacker is exhibiting with confidence scores.
    """
    __tablename__ = "detected_biases"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(100), ForeignKey("sessions.id", ondelete="CASCADE"))
    
    # Bias identification
    bias_type: Mapped[CognitiveBiasType] = mapped_column(String(50), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)  # 0.0 to 1.0
    
    # Detection signals
    signals_matched: Mapped[List[str]] = mapped_column(JSON, default=list)
    signal_scores: Mapped[Dict[str, float]] = mapped_column(JSON, default=dict)
    
    # When first detected and updates
    first_detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    last_updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    detection_count: Mapped[int] = mapped_column(Integer, default=1)  # How many times reinforced
    
    # Active status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Relationship
    session: Mapped["Session"] = relationship(back_populates="detected_biases")
    
    __table_args__ = (
        Index("ix_detected_biases_session", "session_id"),
        Index("ix_detected_biases_type", "bias_type"),
        UniqueConstraint("session_id", "bias_type", name="uq_session_bias"),
    )


class CognitiveProfile(Base):
    """
    Comprehensive cognitive profile for an attacker session.
    
    Tracks mental model, detected biases, and cognitive metrics.
    """
    __tablename__ = "cognitive_profiles"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(100), ForeignKey("sessions.id", ondelete="CASCADE"), unique=True)
    
    # === Mental Model Tracking ===
    # What attacker believes about the system
    attacker_beliefs: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    # Examples:
    # {
    #     "os_type": "Ubuntu 20.04",
    #     "security_level": "low",
    #     "has_firewall": False,
    #     "is_production": True,
    # }
    
    # What attacker has discovered (knowledge state)
    attacker_knowledge: Mapped[List[str]] = mapped_column(JSON, default=list)
    # Examples: ["/etc/passwd contents", "user 'admin' exists", "mysql running"]
    
    # Inferred attacker goals
    attacker_goals: Mapped[List[str]] = mapped_column(JSON, default=list)
    # Examples: ["privilege_escalation", "data_exfiltration", "persistence"]
    
    # Attacker expectations (what they're looking for)
    attacker_expectations: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    
    # === Cognitive Metrics ===
    # Dunning-Kruger: Overconfidence in abilities
    overconfidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Sunk Cost: Investment in current path
    persistence_score: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Confirmation Bias: Tunnel vision
    tunnel_vision_score: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Curiosity: Drive to explore
    curiosity_score: Mapped[float] = mapped_column(Float, default=0.0)
    
    # === Behavioral Metrics ===
    # Exploration diversity (0-1, higher = more diverse)
    exploration_diversity: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Error handling pattern
    error_tolerance: Mapped[float] = mapped_column(Float, default=0.5)
    
    # Learning rate (how quickly attacker adapts)
    learning_rate: Mapped[float] = mapped_column(Float, default=0.0)
    
    # === Deception Effectiveness ===
    total_deceptions_applied: Mapped[int] = mapped_column(Integer, default=0)
    successful_deceptions: Mapped[int] = mapped_column(Integer, default=0)
    deception_success_rate: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Detection suspicion level (how likely attacker suspects honeypot)
    suspicion_level: Mapped[float] = mapped_column(Float, default=0.0)
    
    # === Timestamps ===
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    session: Mapped["Session"] = relationship(back_populates="cognitive_profile")
    
    __table_args__ = (
        Index("ix_cognitive_profiles_session", "session_id"),
    )


class DeceptionEvent(Base):
    """
    Log of deception events applied during a session.
    
    Tracks what deception was applied, when, and its effectiveness.
    """
    __tablename__ = "deception_events"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(100), ForeignKey("sessions.id", ondelete="CASCADE"))
    
    # Deception details
    bias_type: Mapped[CognitiveBiasType] = mapped_column(String(50), nullable=False)
    strategy_name: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Trigger
    trigger_command: Mapped[str] = mapped_column(Text)
    trigger_context: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    
    # Response generated
    response_type: Mapped[DeceptionResponseType] = mapped_column(String(50), nullable=False)
    response_content: Mapped[str] = mapped_column(Text)
    response_metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    
    # Effectiveness tracking
    attacker_reacted: Mapped[bool] = mapped_column(Boolean, default=False)
    reaction_type: Mapped[Optional[str]] = mapped_column(String(50))  # continued, exited, changed_path
    engagement_change: Mapped[float] = mapped_column(Float, default=0.0)  # Positive = increased engagement
    detection_suspected: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Timing
    response_latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    
    # Timestamp
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    
    # Relationship
    session: Mapped["Session"] = relationship(back_populates="deception_events")
    
    __table_args__ = (
        Index("ix_deception_events_session", "session_id"),
        Index("ix_deception_events_bias", "bias_type"),
        Index("ix_deception_events_created", "created_at"),
    )


class DeceptionStrategy(Base):
    """
    Library of deception strategies.
    
    Defines how to exploit each cognitive bias with specific tactics.
    """
    __tablename__ = "deception_strategies"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Strategy identification
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    bias_type: Mapped[CognitiveBiasType] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(Text)
    
    # Trigger conditions (JSON with conditions for when to apply)
    trigger_conditions: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    # Example:
    # {
    #     "commands": ["ls", "cat", "find"],
    #     "min_confidence": 0.6,
    #     "session_min_duration": 60,
    # }
    
    # Response template
    response_template: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    # Example:
    # {
    #     "type": "command_output",
    #     "template": "total {total}\n{files}",
    #     "variables": {
    #         "total": "dynamic",
    #         "files": "generate_fake_files"
    #     }
    # }
    
    # Effectiveness tracking
    effectiveness_score: Mapped[float] = mapped_column(Float, default=0.0)
    times_applied: Mapped[int] = mapped_column(Integer, default=0)
    times_successful: Mapped[int] = mapped_column(Integer, default=0)
    
    # Configuration
    priority: Mapped[int] = mapped_column(Integer, default=0)  # Higher = more priority
    cooldown_seconds: Mapped[int] = mapped_column(Integer, default=60)  # Min time between uses
    max_uses_per_session: Mapped[int] = mapped_column(Integer, default=10)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index("ix_deception_strategies_bias", "bias_type"),
        Index("ix_deception_strategies_active", "is_active"),
    )


class MentalModelSnapshot(Base):
    """
    Snapshot of attacker's mental model at a point in time.
    
    Used to track how attacker's beliefs change during session.
    """
    __tablename__ = "mental_model_snapshots"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(100), ForeignKey("sessions.id", ondelete="CASCADE"))
    
    # Command that triggered snapshot
    trigger_command: Mapped[str] = mapped_column(Text)
    command_index: Mapped[int] = mapped_column(Integer)  # Position in command sequence
    
    # Mental model at this point
    beliefs: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    knowledge: Mapped[List[str]] = mapped_column(JSON, default=list)
    expectations: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    
    # Confidence in model
    model_confidence: Mapped[float] = mapped_column(Float, default=0.5)
    
    # Timestamp
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    
    # Relationship
    session: Mapped["Session"] = relationship(back_populates="mental_model_snapshots")
    
    __table_args__ = (
        Index("ix_mental_model_snapshots_session", "session_id"),
    )


class BiasSignal(Base):
    """
    Pre-defined signals that indicate specific cognitive biases.
    
    Used for rule-based bias detection.
    """
    __tablename__ = "bias_signals"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    bias_type: Mapped[CognitiveBiasType] = mapped_column(String(50), nullable=False)
    signal_name: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Signal definition
    description: Mapped[str] = mapped_column(Text)
    detection_function: Mapped[str] = mapped_column(Text)  # Python expression or function name
    
    # Weight in detection
    weight: Mapped[float] = mapped_column(Float, default=1.0)
    
    # Thresholds
    min_value: Mapped[float] = mapped_column(Float, default=0.0)
    max_value: Mapped[float] = mapped_column(Float, default=1.0)
    threshold: Mapped[float] = mapped_column(Float, default=0.5)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    
    __table_args__ = (
        Index("ix_bias_signals_bias", "bias_type"),
        UniqueConstraint("bias_type", "signal_name", name="uq_bias_signal"),
    )


# Update Session model with new relationships (add to existing model)
# These will be added via patch in the existing models.py
SESSION_COGNITIVE_RELATIONSHIPS = """
# Cognitive-Behavioral Deception relationships
detected_biases: Mapped[List["DetectedBias"]] = relationship(back_populates="session", cascade="all, delete-orphan")
cognitive_profile: Mapped[Optional["CognitiveProfile"]] = relationship(back_populates="session", uselist=False, cascade="all, delete-orphan")
deception_events: Mapped[List["DeceptionEvent"]] = relationship(back_populates="session", cascade="all, delete-orphan")
mental_model_snapshots: Mapped[List["MentalModelSnapshot"]] = relationship(back_populates="session", cascade="all, delete-orphan")
"""