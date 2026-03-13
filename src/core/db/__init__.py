"""
Database package initialization.
"""
from src.core.db.session import (
    engine,
    async_session_factory,
    get_db,
    get_db_context,
    init_db,
    close_db,
)
from src.core.db.models import (
    Base,
    Honeypot,
    Session,
    AttackEvent,
    Adaptation,
    HealthRecord,
    Alert,
    ThreatIntelligence,
    APIKey,
    AuditLog,
    HoneypotType,
    HoneypotStatus,
    InteractionLevel,
    AttackSeverity,
    AttackType,
    ThreatLevel,
    AlertStatus,
)
from src.core.db.repositories import (
    BaseRepository,
    HoneypotRepository,
    SessionRepository,
    AttackEventRepository,
    AdaptationRepository,
    AlertRepository,
    ThreatIntelRepository,
    APIKeyRepository,
)

__all__ = [
    # Session management
    "engine",
    "async_session_factory",
    "get_db",
    "get_db_context",
    "init_db",
    "close_db",
    # Models
    "Base",
    "Honeypot",
    "Session",
    "AttackEvent",
    "Adaptation",
    "HealthRecord",
    "Alert",
    "ThreatIntelligence",
    "APIKey",
    "AuditLog",
    # Enums
    "HoneypotType",
    "HoneypotStatus",
    "InteractionLevel",
    "AttackSeverity",
    "AttackType",
    "ThreatLevel",
    "AlertStatus",
    # Repositories
    "BaseRepository",
    "HoneypotRepository",
    "SessionRepository",
    "AttackEventRepository",
    "AdaptationRepository",
    "AlertRepository",
    "ThreatIntelRepository",
    "APIKeyRepository",
]