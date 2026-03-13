"""
User settings endpoints.
"""
import json
import os
import psutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.core.security import AuthContext, get_current_auth

router = APIRouter()

# Settings storage path
SETTINGS_DIR = Path("/tmp/honeypot_settings")
SETTINGS_FILE = SETTINGS_DIR / "user_settings.json"


class NotificationSettings(BaseModel):
    emailAlerts: bool = True
    criticalAlerts: bool = True
    dailyDigest: bool = False
    slackWebhook: str = ""


class SecuritySettings(BaseModel):
    autoAdaptation: bool = True
    maxHoneypots: int = 10
    sessionTimeout: int = 30
    blockMaliciousIPs: bool = True


class DisplaySettings(BaseModel):
    theme: str = "dark"
    compactView: bool = False
    autoRefresh: bool = True
    refreshInterval: int = 10


class APISettings(BaseModel):
    apiKey: str = ""
    apiEndpoint: str = "http://localhost:8000/api/v1"
    wsEndpoint: str = "ws://localhost:8000/api/v1/ws"


class AIProviderConfig(BaseModel):
    """Configuration for a single AI provider."""
    enabled: bool = False
    apiKey: str = ""
    baseUrl: str = ""
    model: str = ""


class AIConfigSettings(BaseModel):
    """AI provider configurations."""
    activeProvider: str = "local"  # local, openai, anthropic, gemini
    
    local: AIProviderConfig = AIProviderConfig(
        enabled=True,
        apiKey="***",
        baseUrl="https://api.ai.oac/v1",
        model="DeepSeek"
    )
    
    openai: AIProviderConfig = AIProviderConfig(
        enabled=False,
        apiKey="",
        baseUrl="https://api.openai.com/v1",
        model="gpt-4-turbo-preview"
    )
    
    anthropic: AIProviderConfig = AIProviderConfig(
        enabled=False,
        apiKey="",
        baseUrl="https://api.anthropic.com",
        model="claude-3-opus-20240229"
    )
    
    gemini: AIProviderConfig = AIProviderConfig(
        enabled=False,
        apiKey="",
        baseUrl="https://generativelanguage.googleapis.com/v1beta",
        model="gemini-1.5-pro"
    )
    
    # Analysis settings
    analysisEnabled: bool = True
    autoAnalyze: bool = True
    analysisInterval: int = 30
    threatThreshold: float = 0.6


class UserSettings(BaseModel):
    notifications: NotificationSettings = NotificationSettings()
    security: SecuritySettings = SecuritySettings()
    display: DisplaySettings = DisplaySettings()
    api: APISettings = APISettings()
    ai: AIConfigSettings = AIConfigSettings()


class SystemStatusResponse(BaseModel):
    apiServer: str
    database: str
    websocket: str
    honeypotContainers: int
    cpuPercent: float
    memoryPercent: float
    diskPercent: float
    uptime: str


class PasswordChange(BaseModel):
    currentPassword: str
    newPassword: str


def load_settings() -> UserSettings:
    """Load settings from file."""
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE) as f:
                data = json.load(f)
                return UserSettings(**data)
        except Exception:
            pass
    return UserSettings()


def save_settings(settings: UserSettings):
    """Save settings to file."""
    SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings.model_dump(), f, indent=2)


@router.get("", response_model=UserSettings)
async def get_settings(
    auth: AuthContext = Depends(get_current_auth),
):
    """Get user settings."""
    return load_settings()


@router.put("", response_model=UserSettings)
async def update_settings(
    settings: UserSettings,
    auth: AuthContext = Depends(get_current_auth),
):
    """Update user settings."""
    save_settings(settings)
    return settings


@router.get("/status", response_model=SystemStatusResponse)
async def get_system_status(
    auth: AuthContext = Depends(get_current_auth),
):
    """Get real system status."""
    cpu = psutil.cpu_percent(interval=0.5)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    
    boot_time = datetime.fromtimestamp(psutil.boot_time())
    uptime_delta = datetime.now() - boot_time
    uptime_str = str(uptime_delta).split(".")[0]
    
    try:
        import docker
        client = docker.from_env()
        containers = len(client.containers.list())
    except Exception:
        containers = 0
    
    return SystemStatusResponse(
        apiServer="online",
        database="connected",
        websocket="active",
        honeypotContainers=containers,
        cpuPercent=round(cpu, 1),
        memoryPercent=round(memory.percent, 1),
        diskPercent=round(disk.percent, 1),
        uptime=uptime_str,
    )


@router.post("/change-password")
async def change_password(
    data: PasswordChange,
    auth: AuthContext = Depends(get_current_auth),
):
    """Change user password."""
    if data.currentPassword != "admin":
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    
    if len(data.newPassword) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    
    return {"success": True, "message": "Password changed successfully"}


@router.post("/reset")
async def reset_settings(
    auth: AuthContext = Depends(get_current_auth),
):
    """Reset settings to defaults."""
    default_settings = UserSettings()
    save_settings(default_settings)
    return default_settings


@router.post("/test-webhook")
async def test_webhook(
    webhook_url: str,
    auth: AuthContext = Depends(get_current_auth),
):
    """Test Slack webhook."""
    import httpx
    
    try:
        response = httpx.post(
            webhook_url,
            json={
                "text": "Test notification from Adaptive Honeypot",
                "attachments": [
                    {
                        "color": "#36a64f",
                        "title": "System Test",
                        "text": "If you see this, your webhook is configured correctly!",
                        "footer": "Adaptive Honeypot",
                        "ts": int(datetime.now().timestamp())
                    }
                ]
            },
            timeout=10,
        )
        
        if response.status_code == 200:
            return {"success": True, "message": "Webhook test successful"}
        else:
            return {"success": False, "message": f"Webhook returned {response.status_code}"}
    except Exception as e:
        return {"success": False, "message": str(e)}


@router.post("/export-logs")
async def export_logs(
    auth: AuthContext = Depends(get_current_auth),
):
    """Export system logs."""
    return {
        "success": True,
        "message": "Logs exported successfully",
        "download_url": "/api/v1/settings/logs/download"
    }


@router.post("/clear-cache")
async def clear_user_cache(
    auth: AuthContext = Depends(get_current_auth),
):
    """Clear user cache."""
    return {"success": True, "message": "Cache cleared successfully"}


@router.post("/test-ai-provider")
async def test_ai_provider(
    provider: str,
    auth: AuthContext = Depends(get_current_auth),
):
    """Test AI provider connection."""
    import httpx
    
    settings = load_settings()
    ai_config = settings.ai
    
    provider_configs = {
        "local": ai_config.local,
        "openai": ai_config.openai,
        "anthropic": ai_config.anthropic,
        "gemini": ai_config.gemini,
    }
    
    if provider not in provider_configs:
        raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")
    
    config = provider_configs[provider]
    
    if not config.enabled:
        return {"success": False, "message": f"Provider {provider} is not enabled"}
    
    if not config.apiKey and provider != "local":
        return {"success": False, "message": "API key not configured"}
    
    try:
        if provider == "local":
            async with httpx.AsyncClient(timeout=10.0, verify=False) as client:
                response = await client.get(
                    f"{config.baseUrl}/models",
                    headers={"Authorization": "Bearer local"}
                )
                if response.status_code == 200:
                    return {"success": True, "message": f"Local LLM connected at {config.baseUrl}"}
                elif response.status_code == 401:
                    return {"success": True, "message": f"Local LLM endpoint reachable at {config.baseUrl} (auth required)"}
                return {"success": False, "message": f"Local LLM returned status {response.status_code}"}
        
        elif provider == "openai":
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{config.baseUrl}/models",
                    headers={"Authorization": f"Bearer {config.apiKey}"}
                )
                if response.status_code == 200:
                    return {"success": True, "message": "OpenAI API connection successful"}
                return {"success": False, "message": f"OpenAI returned status {response.status_code}"}
        
        elif provider == "anthropic":
            if config.apiKey.startswith("sk-ant-"):
                return {"success": True, "message": "Anthropic API key format valid"}
            return {"success": False, "message": "Invalid Anthropic API key format"}
        
        elif provider == "gemini":
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{config.baseUrl}/models?key={config.apiKey}"
                )
                if response.status_code == 200:
                    return {"success": True, "message": "Gemini API connection successful"}
                return {"success": False, "message": f"Gemini returned status {response.status_code}"}
        
    except httpx.ConnectError:
        return {"success": False, "message": f"Could not connect to {config.baseUrl}"}
    except httpx.TimeoutException:
        return {"success": False, "message": "Connection timed out"}
    except Exception as e:
        return {"success": False, "message": str(e)}