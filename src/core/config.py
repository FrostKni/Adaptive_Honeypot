"""
Configuration management using Pydantic Settings.
Supports environment variables, .env files, and validation.
"""
from typing import Optional, List, Literal
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class DatabaseSettings(BaseSettings):
    """Database configuration."""
    model_config = SettingsConfigDict(env_prefix="DB_")
    
    host: str = "localhost"
    port: int = 5432
    user: str = "honeypot"
    password: SecretStr = SecretStr("honeypot_secret")
    name: str = "adaptive_honeypot"
    pool_size: int = 10
    max_overflow: int = 20
    echo: bool = False
    
    @property
    def async_url(self) -> str:
        # Default to SQLite for local development
        return f"sqlite+aiosqlite:///./honeypot.db"
    
    @property
    def sync_url(self) -> str:
        return f"sqlite:///./honeypot.db"


class RedisSettings(BaseSettings):
    """Redis configuration."""
    model_config = SettingsConfigDict(env_prefix="REDIS_")
    
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[SecretStr] = None
    
    @property
    def url(self) -> str:
        if self.password:
            return f"redis://:{self.password.get_secret_value()}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"


class AISettings(BaseSettings):
    """AI provider configuration."""
    model_config = SettingsConfigDict(env_prefix="AI_")
    
    provider: Literal["openai", "anthropic", "gemini", "local"] = "openai"
    model: str = "gpt-4-turbo-preview"
    fallback_provider: Optional[str] = None
    max_tokens: int = 2000
    temperature: float = 0.3
    cache_ttl: int = 3600
    enable_streaming: bool = True
    
    openai_api_key: Optional[SecretStr] = None
    anthropic_api_key: Optional[SecretStr] = None
    gemini_api_key: Optional[SecretStr] = None
    
    requests_per_minute: int = 60
    tokens_per_day: int = 100000


class HoneypotSettings(BaseSettings):
    """Honeypot configuration."""
    model_config = SettingsConfigDict(env_prefix="HONEYPOT_")
    
    network_name: str = "honeypot_net"
    subnet: str = "172.20.0.0/16"
    max_instances: int = 10
    default_port_range_start: int = 2222
    default_port_range_end: int = 2300
    
    adaptation_threshold: int = 5
    analysis_interval: int = 60
    max_adaptations_per_hour: int = 10
    
    session_timeout: int = 3600
    max_sessions_per_honeypot: int = 50


class SecuritySettings(BaseSettings):
    """Security configuration."""
    model_config = SettingsConfigDict(env_prefix="SECURITY_")
    
    jwt_secret: SecretStr = SecretStr("change-me-in-production")
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60
    
    api_key_header: str = "X-API-Key"
    api_key_length: int = 32
    
    rate_limit_requests: int = 100
    rate_limit_window: int = 60
    
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    cors_allow_credentials: bool = True


class MonitoringSettings(BaseSettings):
    """Monitoring configuration."""
    model_config = SettingsConfigDict(env_prefix="MONITORING_")
    
    prometheus_port: int = 9090
    enable_metrics: bool = True
    log_level: str = "INFO"
    
    health_check_interval: int = 30
    alert_cooldown: int = 300
    max_alerts_per_hour: int = 100


class AlertingSettings(BaseSettings):
    """Alerting configuration."""
    model_config = SettingsConfigDict(env_prefix="ALERT_")
    
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[SecretStr] = None
    email_recipients: List[str] = []
    
    webhook_url: Optional[str] = None
    webhook_headers: dict = {}
    
    slack_webhook_url: Optional[str] = None
    discord_webhook_url: Optional[str] = None


class AppSettings(BaseSettings):
    """Main application settings."""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    app_name: str = "Adaptive Honeypot System"
    app_version: str = "2.0.0"
    debug: bool = False
    environment: Literal["development", "staging", "production"] = "development"
    
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    db: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    ai: AISettings = Field(default_factory=AISettings)
    honeypot: HoneypotSettings = Field(default_factory=HoneypotSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    monitoring: MonitoringSettings = Field(default_factory=MonitoringSettings)
    alerting: AlertingSettings = Field(default_factory=AlertingSettings)


@lru_cache()
def get_settings() -> AppSettings:
    """Get cached application settings."""
    return AppSettings()


settings = get_settings()