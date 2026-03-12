from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, List, Any
from enum import Enum
from datetime import datetime

class HoneypotType(str, Enum):
    SSH = "ssh"
    TELNET = "telnet"
    HTTP = "http"

class InteractionLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class HoneypotStatus(str, Enum):
    STARTING = "starting"
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"
    MIGRATING = "migrating"

class AttackSeverity(str, Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class HoneypotConfig(BaseModel):
    name: str
    type: HoneypotType = HoneypotType.SSH
    port: int = 2222
    interaction_level: InteractionLevel = InteractionLevel.LOW
    hostname: str = "server01"
    banner: Optional[str] = None
    fake_users: List[Dict[str, str]] = Field(default_factory=list)
    fake_files: List[str] = Field(default_factory=list)
    allowed_commands: List[str] = Field(default_factory=list)
    response_delay: float = 0.0
    max_sessions: int = 10
    session_timeout: int = 300
    custom_responses: Dict[str, str] = Field(default_factory=dict)
    
    class Config:
        use_enum_values = True

class AttackEvent(BaseModel):
    timestamp: datetime
    honeypot_id: str
    source_ip: str
    source_port: int
    username: Optional[str] = None
    password: Optional[str] = None
    commands: List[str] = Field(default_factory=list)
    session_id: str
    severity: AttackSeverity = AttackSeverity.INFO
    attack_type: Optional[str] = None
    
class AdaptationDecision(BaseModel):
    honeypot_id: str
    reason: str
    old_config: Dict[str, Any]
    new_config: Dict[str, Any]
    timestamp: datetime
    applied: bool = False
    
class ContainerHealth(BaseModel):
    container_id: str
    status: HoneypotStatus
    cpu_percent: float
    memory_mb: float
    uptime_seconds: int
    last_check: datetime
