"""
Production-grade database models using SQLAlchemy async.
Includes full schema for honeypots, attacks, adaptations, and analytics.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from uuid import uuid4
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, JSON, Text,
    ForeignKey, Enum as SQLEnum, Index, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY, INET
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncAttrs


class Base(AsyncAttrs, DeclarativeBase):
    """Base class for all models."""
    pass


# ==================== Enums ====================

class HoneypotType(str, Enum):
    SSH = "ssh"
    TELNET = "telnet"
    HTTP = "http"
    HTTPS = "https"
    FTP = "ftp"
    SMTP = "smtp"
    MYSQL = "mysql"
    POSTGRES = "postgres"


class HoneypotStatus(str, Enum):
    STARTING = "starting"
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"
    MIGRATING = "migrating"
    ADAPTING = "adapting"


class InteractionLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    AGGRESSIVE = "aggressive"


class AttackSeverity(str, Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AttackType(str, Enum):
    BRUTE_FORCE = "brute_force"
    COMMAND_INJECTION = "command_injection"
    MALWARE_DOWNLOAD = "malware_download"
    RECONNAISSANCE = "reconnaissance"
    EXPLOITATION = "exploitation"
    DATA_EXFILTRATION = "data_exfiltration"
    LATERAL_MOVEMENT = "lateral_movement"
    PERSISTENCE = "persistence"
    UNKNOWN = "unknown"


class ThreatLevel(str, Enum):
    BENIGN = "benign"
    SUSPICIOUS = "suspicious"
    MALICIOUS = "malicious"
    APT = "apt"


class AlertStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    FAILED = "failed"


# ==================== Models ====================

class Honeypot(Base):
    """Honeypot instance model."""
    __tablename__ = "honeypots"
    
    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    type: Mapped[HoneypotType] = mapped_column(SQLEnum(HoneypotType), default=HoneypotType.SSH)
    status: Mapped[HoneypotStatus] = mapped_column(SQLEnum(HoneypotStatus), default=HoneypotStatus.STARTING)
    
    # Network configuration
    port: Mapped[int] = mapped_column(Integer, nullable=False)
    container_id: Mapped[Optional[str]] = mapped_column(String(64))
    container_name: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Configuration
    interaction_level: Mapped[InteractionLevel] = mapped_column(
        SQLEnum(InteractionLevel), default=InteractionLevel.LOW
    )
    hostname: Mapped[str] = mapped_column(String(100), default="ubuntu-server")
    banner: Mapped[Optional[str]] = mapped_column(String(200))
    config: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    
    # Stats
    total_sessions: Mapped[int] = mapped_column(Integer, default=0)
    total_attacks: Mapped[int] = mapped_column(Integer, default=0)
    last_attack: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    stopped_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Relationships
    sessions: Mapped[List["Session"]] = relationship(back_populates="honeypot", cascade="all, delete-orphan")
    adaptations: Mapped[List["Adaptation"]] = relationship(back_populates="honeypot", cascade="all, delete-orphan")
    health_records: Mapped[List["HealthRecord"]] = relationship(back_populates="honeypot", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("ix_honeypots_status", "status"),
        Index("ix_honeypots_type", "type"),
    )


class Session(Base):
    """Attack session model."""
    __tablename__ = "sessions"
    
    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    honeypot_id: Mapped[str] = mapped_column(String(100), ForeignKey("honeypots.id", ondelete="CASCADE"))
    
    # Connection info
    source_ip: Mapped[str] = mapped_column(String(45), nullable=False)  # IPv6 compatible
    source_port: Mapped[int] = mapped_column(Integer, nullable=False)
    source_country: Mapped[Optional[str]] = mapped_column(String(2))  # ISO country code
    source_asn: Mapped[Optional[int]] = mapped_column(Integer)
    source_asn_name: Mapped[Optional[str]] = mapped_column(String(200))
    
    # Authentication
    username: Mapped[Optional[str]] = mapped_column(String(100))
    password: Mapped[Optional[str]] = mapped_column(String(200))
    auth_success: Mapped[bool] = mapped_column(Boolean, default=False)
    auth_attempts: Mapped[int] = mapped_column(Integer, default=0)
    credentials_tried: Mapped[List[Dict]] = mapped_column(JSON, default=list)
    
    # Session data
    commands: Mapped[List[str]] = mapped_column(JSON, default=list)
    downloads: Mapped[List[Dict]] = mapped_column(JSON, default=list)
    uploads: Mapped[List[Dict]] = mapped_column(JSON, default=list)
    files_accessed: Mapped[List[str]] = mapped_column(JSON, default=list)
    
    # Analysis
    attack_type: Mapped[AttackType] = mapped_column(SQLEnum(AttackType), default=AttackType.UNKNOWN)
    severity: Mapped[AttackSeverity] = mapped_column(SQLEnum(AttackSeverity), default=AttackSeverity.INFO)
    threat_level: Mapped[ThreatLevel] = mapped_column(SQLEnum(ThreatLevel), default=ThreatLevel.SUSPICIOUS)
    attacker_skill: Mapped[Optional[str]] = mapped_column(String(50))
    attack_objectives: Mapped[List[str]] = mapped_column(JSON, default=list)
    
    # Session replay
    terminal_log: Mapped[Optional[str]] = mapped_column(Text)
    replay_file: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Timestamps
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0)
    
    # Relationships
    honeypot: Mapped["Honeypot"] = relationship(back_populates="sessions")
    events: Mapped[List["AttackEvent"]] = relationship(back_populates="session", cascade="all, delete-orphan")
    cognitive_profiles: Mapped[List["CognitiveProfileDB"]] = relationship(back_populates="session", cascade="all, delete-orphan")
    deception_events: Mapped[List["DeceptionEventDB"]] = relationship(back_populates="session", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("ix_sessions_source_ip", "source_ip"),
        Index("ix_sessions_started_at", "started_at"),
        Index("ix_sessions_honeypot_started", "honeypot_id", "started_at"),
    )


class AttackEvent(Base):
    """Individual attack event."""
    __tablename__ = "attack_events"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[Optional[str]] = mapped_column(String(100), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=True)
    
    # Event data
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)  # login, command, download, etc.
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    
    # Event details
    data: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    raw_log: Mapped[Optional[str]] = mapped_column(Text)
    
    # Classification
    severity: Mapped[AttackSeverity] = mapped_column(SQLEnum(AttackSeverity), default=AttackSeverity.INFO)
    tags: Mapped[List[str]] = mapped_column(JSON, default=list)
    
    # Relationships
    session: Mapped[Optional["Session"]] = relationship(back_populates="events")
    
    __table_args__ = (
        Index("ix_attack_events_timestamp", "timestamp"),
        Index("ix_attack_events_type", "event_type"),
    )


class Adaptation(Base):
    """Honeypot adaptation record."""
    __tablename__ = "adaptations"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    honeypot_id: Mapped[str] = mapped_column(String(100), ForeignKey("honeypots.id", ondelete="CASCADE"))
    
    # Trigger info
    trigger_type: Mapped[str] = mapped_column(String(50))  # threshold, periodic, threat
    trigger_data: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    
    # AI Analysis
    ai_provider: Mapped[str] = mapped_column(String(50))
    ai_model: Mapped[str] = mapped_column(String(100))
    analysis_result: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    analysis_tokens: Mapped[int] = mapped_column(Integer, default=0)
    analysis_duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    
    # Configuration changes
    old_config: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    new_config: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    changes_summary: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    
    # Execution
    applied: Mapped[bool] = mapped_column(Boolean, default=False)
    applied_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    success: Mapped[bool] = mapped_column(Boolean, default=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    
    # Impact tracking
    sessions_before: Mapped[int] = mapped_column(Integer, default=0)
    sessions_after: Mapped[int] = mapped_column(Integer, default=0)
    effectiveness_score: Mapped[Optional[float]] = mapped_column(Float)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    
    # Relationships
    honeypot: Mapped["Honeypot"] = relationship(back_populates="adaptations")
    
    __table_args__ = (
        Index("ix_adaptations_created_at", "created_at"),
        Index("ix_adaptations_honeypot", "honeypot_id"),
    )


class HealthRecord(Base):
    """Honeypot health metrics."""
    __tablename__ = "health_records"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    honeypot_id: Mapped[str] = mapped_column(String(100), ForeignKey("honeypots.id", ondelete="CASCADE"))
    
    # Metrics
    cpu_percent: Mapped[float] = mapped_column(Float, default=0.0)
    memory_mb: Mapped[float] = mapped_column(Float, default=0.0)
    network_in_bytes: Mapped[int] = mapped_column(Integer, default=0)
    network_out_bytes: Mapped[int] = mapped_column(Integer, default=0)
    disk_read_bytes: Mapped[int] = mapped_column(Integer, default=0)
    disk_write_bytes: Mapped[int] = mapped_column(Integer, default=0)
    
    # Status
    status: Mapped[HoneypotStatus] = mapped_column(SQLEnum(HoneypotStatus))
    uptime_seconds: Mapped[int] = mapped_column(Integer, default=0)
    
    # Timestamp
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    
    # Relationships
    honeypot: Mapped["Honeypot"] = relationship(back_populates="health_records")
    
    __table_args__ = (
        Index("ix_health_records_recorded_at", "recorded_at"),
    )


class Alert(Base):
    """Security alert."""
    __tablename__ = "alerts"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Alert info
    alert_type: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[AttackSeverity] = mapped_column(SQLEnum(AttackSeverity), default=AttackSeverity.MEDIUM)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Related entities
    honeypot_id: Mapped[Optional[str]] = mapped_column(String(100))
    session_id: Mapped[Optional[str]] = mapped_column(String(100))
    source_ip: Mapped[Optional[str]] = mapped_column(String(45))
    
    # Additional data
    alert_metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    
    # Status
    status: Mapped[AlertStatus] = mapped_column(SQLEnum(AlertStatus), default=AlertStatus.PENDING)
    
    # Notification tracking
    channels_sent: Mapped[List[str]] = mapped_column(JSON, default=list)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    acknowledged_by: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    
    __table_args__ = (
        Index("ix_alerts_created_at", "created_at"),
        Index("ix_alerts_severity", "severity"),
        Index("ix_alerts_status", "status"),
    )


class ThreatIntelligence(Base):
    """Threat intelligence database."""
    __tablename__ = "threat_intelligence"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Indicator
    indicator_type: Mapped[str] = mapped_column(String(50))  # ip, domain, hash, url
    indicator_value: Mapped[str] = mapped_column(String(500), nullable=False)
    
    # Classification
    threat_type: Mapped[str] = mapped_column(String(100))
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    severity: Mapped[AttackSeverity] = mapped_column(SQLEnum(AttackSeverity), default=AttackSeverity.MEDIUM)
    
    # Intelligence data
    tags: Mapped[List[str]] = mapped_column(JSON, default=list)
    malware_families: Mapped[List[str]] = mapped_column(JSON, default=list)
    attack_patterns: Mapped[List[str]] = mapped_column(JSON, default=list)
    references: Mapped[List[str]] = mapped_column(JSON, default=list)
    intel_metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    
    # Source
    source: Mapped[str] = mapped_column(String(100))
    source_url: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Timestamps
    first_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    __table_args__ = (
        Index("ix_threat_intel_indicator", "indicator_type", "indicator_value"),
        UniqueConstraint("indicator_type", "indicator_value", name="uq_threat_intel_indicator"),
    )


class APIKey(Base):
    """API Key for authentication."""
    __tablename__ = "api_keys"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key_hash: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    key_prefix: Mapped[str] = mapped_column(String(8), nullable=False)  # For identification
    
    # Metadata
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Permissions
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    scopes: Mapped[List[str]] = mapped_column(JSON, default=list)
    rate_limit: Mapped[int] = mapped_column(Integer, default=100)
    
    # Usage tracking
    last_used: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    total_requests: Mapped[int] = mapped_column(Integer, default=0)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_by: Mapped[Optional[str]] = mapped_column(String(100))
    
    __table_args__ = (
        Index("ix_api_keys_prefix", "key_prefix"),
    )


class AuditLog(Base):
    """Audit log for compliance and security."""
    __tablename__ = "audit_logs"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Action info
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False)
    resource_id: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Actor info
    actor_type: Mapped[str] = mapped_column(String(50))  # user, api_key, system
    actor_id: Mapped[Optional[str]] = mapped_column(String(100))
    actor_ip: Mapped[Optional[str]] = mapped_column(String(45))
    
    # Changes
    old_values: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    new_values: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    
    # Request info
    request_id: Mapped[Optional[str]] = mapped_column(String(100))
    request_method: Mapped[Optional[str]] = mapped_column(String(10))
    request_path: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Timestamp
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    
    __table_args__ = (
        Index("ix_audit_logs_action", "action"),
        Index("ix_audit_logs_created_at", "created_at"),
        Index("ix_audit_logs_resource", "resource_type", "resource_id"),
    )


class CognitiveProfileDB(Base):
    """Cognitive profile of attacker sessions for deception tracking."""
    __tablename__ = "cognitive_profiles"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(100), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    
    # Detected biases (JSON array of bias objects)
    detected_biases: Mapped[List[Dict]] = mapped_column(JSON, default=list)
    
    # Mental model
    beliefs: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    knowledge: Mapped[List[str]] = mapped_column(JSON, default=list)
    goals: Mapped[List[str]] = mapped_column(JSON, default=list)
    expectations: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    
    # Cognitive metrics
    overconfidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    persistence_score: Mapped[float] = mapped_column(Float, default=0.0)
    tunnel_vision_score: Mapped[float] = mapped_column(Float, default=0.0)
    curiosity_score: Mapped[float] = mapped_column(Float, default=0.0)
    exploration_diversity: Mapped[float] = mapped_column(Float, default=0.0)
    error_tolerance: Mapped[float] = mapped_column(Float, default=0.5)
    learning_rate: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Deception metrics
    total_deceptions_applied: Mapped[int] = mapped_column(Integer, default=0)
    successful_deceptions: Mapped[int] = mapped_column(Integer, default=0)
    deception_success_rate: Mapped[float] = mapped_column(Float, default=0.0)
    suspicion_level: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Behavioral signals (raw data for analysis)
    signals: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    is_final: Mapped[bool] = mapped_column(Boolean, default=False)  # True when session ends
    
    # Relationships
    session: Mapped["Session"] = relationship(back_populates="cognitive_profiles")
    
    __table_args__ = (
        Index("ix_cognitive_profiles_session_id", "session_id"),
        Index("ix_cognitive_profiles_updated_at", "updated_at"),
    )


class DeceptionEventDB(Base):
    """Record of deception events applied during sessions."""
    __tablename__ = "deception_events"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(100), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    
    # Deception details
    bias_type: Mapped[str] = mapped_column(String(50), nullable=False)  # Which bias was targeted
    strategy_name: Mapped[str] = mapped_column(String(100), nullable=False)  # Strategy used
    trigger_command: Mapped[str] = mapped_column(Text, nullable=False)  # Command that triggered
    
    # Response
    response_type: Mapped[str] = mapped_column(String(50))  # Type of response generated
    response_content: Mapped[Optional[str]] = mapped_column(Text)  # Actual response (optional)
    
    # Effectiveness tracking
    attacker_reacted: Mapped[bool] = mapped_column(Boolean, default=False)  # Did attacker respond?
    reaction_type: Mapped[Optional[str]] = mapped_column(String(50))  # Type of reaction
    effectiveness_score: Mapped[Optional[float]] = mapped_column(Float)  # Calculated effectiveness
    
    # Metadata
    event_metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    
    # Relationships
    session: Mapped["Session"] = relationship(back_populates="deception_events")
    
    __table_args__ = (
        Index("ix_deception_events_session_id", "session_id"),
        Index("ix_deception_events_bias_type", "bias_type"),
        Index("ix_deception_events_created_at", "created_at"),
    )