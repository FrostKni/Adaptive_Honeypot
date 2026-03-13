"""
Multi-channel alerting system.
Supports email, webhooks, Slack, Discord, and custom integrations.
"""
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod
from datetime import datetime
import json
import logging
import asyncio
import aiohttp
from dataclasses import dataclass
from enum import Enum

from jinja2 import Template
from pydantic import BaseModel

from src.core.config import settings


logger = logging.getLogger(__name__)


# ==================== Models ====================

class AlertChannel(str, Enum):
    EMAIL = "email"
    WEBHOOK = "webhook"
    SLACK = "slack"
    DISCORD = "discord"
    TELEGRAM = "telegram"


class AlertPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Alert:
    """Alert data structure."""
    alert_type: str
    title: str
    message: str
    priority: AlertPriority
    honeypot_id: Optional[str] = None
    session_id: Optional[str] = None
    source_ip: Optional[str] = None
    timestamp: datetime = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
        if self.metadata is None:
            self.metadata = {}


class AlertChannelInterface(ABC):
    """Abstract base class for alert channels."""
    
    @abstractmethod
    async def send(self, alert: Alert) -> bool:
        """Send an alert through this channel."""
        pass
    
    @abstractmethod
    def is_configured(self) -> bool:
        """Check if the channel is properly configured."""
        pass


# ==================== Email Channel ====================

class EmailChannel(AlertChannelInterface):
    """Email alert channel."""
    
    def __init__(
        self,
        smtp_host: str = None,
        smtp_port: int = 587,
        smtp_user: str = None,
        smtp_password: str = None,
        recipients: List[str] = None,
    ):
        self.smtp_host = smtp_host or settings.alerting.smtp_host
        self.smtp_port = smtp_port or settings.alerting.smtp_port
        self.smtp_user = smtp_user or settings.alerting.smtp_user
        self.smtp_password = smtp_password or (
            settings.alerting.smtp_password.get_secret_value()
            if settings.alerting.smtp_password else None
        )
        self.recipients = recipients or settings.alerting.email_recipients
    
    def is_configured(self) -> bool:
        return all([self.smtp_host, self.smtp_user, self.recipients])
    
    async def send(self, alert: Alert) -> bool:
        if not self.is_configured():
            return False
        
        try:
            import aiosmtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            message = MIMEMultipart("alternative")
            message["Subject"] = f"[{alert.priority.value.upper()}] {alert.title}"
            message["From"] = self.smtp_user
            message["To"] = ", ".join(self.recipients)
            
            # Plain text
            text_content = self._format_text(alert)
            message.attach(MIMEText(text_content, "plain"))
            
            # HTML
            html_content = self._format_html(alert)
            message.attach(MIMEText(html_content, "html"))
            
            await aiosmtplib.send(
                message,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.smtp_user,
                password=self.smtp_password,
                start_tls=True,
            )
            
            logger.info(f"Email alert sent: {alert.title}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
            return False
    
    def _format_text(self, alert: Alert) -> str:
        return f"""
ALERT: {alert.title}
Priority: {alert.priority.value.upper()}
Type: {alert.alert_type}
Time: {alert.timestamp.isoformat()}

{alert.message}

Details:
- Honeypot: {alert.honeypot_id or 'N/A'}
- Session: {alert.session_id or 'N/A'}
- Source IP: {alert.source_ip or 'N/A'}

---
Adaptive Honeypot System
"""
    
    def _format_html(self, alert: Alert) -> str:
        priority_colors = {
            AlertPriority.LOW: "#10B981",
            AlertPriority.MEDIUM: "#F59E0B",
            AlertPriority.HIGH: "#EF4444",
            AlertPriority.CRITICAL: "#991B1B",
        }
        
        return f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: {priority_colors[alert.priority]}; color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
        .content {{ background: #f9f9f9; padding: 20px; border-radius: 0 0 8px 8px; }}
        .detail {{ margin: 10px 0; }}
        .label {{ font-weight: bold; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{alert.title}</h1>
            <p>Priority: {alert.priority.value.upper()}</p>
        </div>
        <div class="content">
            <p>{alert.message}</p>
            <div class="detail">
                <span class="label">Honeypot:</span> {alert.honeypot_id or 'N/A'}
            </div>
            <div class="detail">
                <span class="label">Session:</span> {alert.session_id or 'N/A'}
            </div>
            <div class="detail">
                <span class="label">Source IP:</span> {alert.source_ip or 'N/A'}
            </div>
            <div class="detail">
                <span class="label">Time:</span> {alert.timestamp.isoformat()}
            </div>
        </div>
    </div>
</body>
</html>
"""


# ==================== Webhook Channel ====================

class WebhookChannel(AlertChannelInterface):
    """Generic webhook alert channel."""
    
    def __init__(
        self,
        url: str = None,
        headers: Dict[str, str] = None,
        method: str = "POST",
    ):
        self.url = url or settings.alerting.webhook_url
        self.headers = headers or settings.alerting.webhook_headers
        self.method = method
    
    def is_configured(self) -> bool:
        return self.url is not None
    
    async def send(self, alert: Alert) -> bool:
        if not self.is_configured():
            return False
        
        try:
            payload = {
                "alert_type": alert.alert_type,
                "title": alert.title,
                "message": alert.message,
                "priority": alert.priority.value,
                "honeypot_id": alert.honeypot_id,
                "session_id": alert.session_id,
                "source_ip": alert.source_ip,
                "timestamp": alert.timestamp.isoformat(),
                "metadata": alert.metadata,
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method=self.method,
                    url=self.url,
                    json=payload,
                    headers=self.headers,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    if response.status < 400:
                        logger.info(f"Webhook alert sent: {alert.title}")
                        return True
                    else:
                        logger.error(f"Webhook returned status {response.status}")
                        return False
        
        except Exception as e:
            logger.error(f"Failed to send webhook alert: {e}")
            return False


# ==================== Slack Channel ====================

class SlackChannel(AlertChannelInterface):
    """Slack webhook alert channel."""
    
    def __init__(self, webhook_url: str = None):
        self.webhook_url = webhook_url or settings.alerting.slack_webhook_url
    
    def is_configured(self) -> bool:
        return self.webhook_url is not None
    
    async def send(self, alert: Alert) -> bool:
        if not self.is_configured():
            return False
        
        try:
            priority_colors = {
                AlertPriority.LOW: "#10B981",
                AlertPriority.MEDIUM: "#F59E0B",
                AlertPriority.HIGH: "#EF4444",
                AlertPriority.CRITICAL: "#991B1B",
            }
            
            payload = {
                "attachments": [{
                    "color": priority_colors[alert.priority],
                    "title": alert.title,
                    "text": alert.message,
                    "fields": [
                        {"title": "Priority", "value": alert.priority.value.upper(), "short": True},
                        {"title": "Type", "value": alert.alert_type, "short": True},
                        {"title": "Honeypot", "value": alert.honeypot_id or "N/A", "short": True},
                        {"title": "Source IP", "value": alert.source_ip or "N/A", "short": True},
                    ],
                    "footer": "Adaptive Honeypot System",
                    "ts": int(alert.timestamp.timestamp()),
                }]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    if response.status == 200:
                        logger.info(f"Slack alert sent: {alert.title}")
                        return True
                    else:
                        return False
        
        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")
            return False


# ==================== Discord Channel ====================

class DiscordChannel(AlertChannelInterface):
    """Discord webhook alert channel."""
    
    def __init__(self, webhook_url: str = None):
        self.webhook_url = webhook_url or settings.alerting.discord_webhook_url
    
    def is_configured(self) -> bool:
        return self.webhook_url is not None
    
    async def send(self, alert: Alert) -> bool:
        if not self.is_configured():
            return False
        
        try:
            priority_colors = {
                AlertPriority.LOW: 0x10B981,
                AlertPriority.MEDIUM: 0xF59E0B,
                AlertPriority.HIGH: 0xEF4444,
                AlertPriority.CRITICAL: 0x991B1B,
            }
            
            payload = {
                "embeds": [{
                    "title": alert.title,
                    "description": alert.message,
                    "color": priority_colors[alert.priority],
                    "fields": [
                        {"name": "Priority", "value": alert.priority.value.upper(), "inline": True},
                        {"name": "Type", "value": alert.alert_type, "inline": True},
                        {"name": "Honeypot", "value": alert.honeypot_id or "N/A", "inline": True},
                        {"name": "Source IP", "value": alert.source_ip or "N/A", "inline": True},
                    ],
                    "footer": {"text": "Adaptive Honeypot System"},
                    "timestamp": alert.timestamp.isoformat(),
                }]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    if response.status == 204:
                        logger.info(f"Discord alert sent: {alert.title}")
                        return True
                    else:
                        return False
        
        except Exception as e:
            logger.error(f"Failed to send Discord alert: {e}")
            return False


# ==================== Alert Manager ====================

class AlertManager:
    """
    Central alert management.
    Routes alerts to appropriate channels with rate limiting and batching.
    """
    
    def __init__(self):
        self.channels: Dict[str, AlertChannelInterface] = {}
        self.rate_limits: Dict[str, List[datetime]] = {}
        self.alert_history: List[Alert] = []
        self._init_channels()
    
    def _init_channels(self):
        """Initialize alert channels from config."""
        # Email
        email = EmailChannel()
        if email.is_configured():
            self.channels["email"] = email
        
        # Webhook
        webhook = WebhookChannel()
        if webhook.is_configured():
            self.channels["webhook"] = webhook
        
        # Slack
        slack = SlackChannel()
        if slack.is_configured():
            self.channels["slack"] = slack
        
        # Discord
        discord = DiscordChannel()
        if discord.is_configured():
            self.channels["discord"] = discord
        
        logger.info(f"Initialized {len(self.channels)} alert channels")
    
    def add_channel(self, name: str, channel: AlertChannelInterface):
        """Add a custom alert channel."""
        self.channels[name] = channel
    
    async def send_alert(
        self,
        alert: Alert,
        channels: List[str] = None,
        rate_limit_seconds: int = 300,
    ) -> Dict[str, bool]:
        """
        Send an alert through specified channels.
        
        Args:
            alert: The alert to send
            channels: Specific channels to use (None = all)
            rate_limit_seconds: Minimum seconds between same alerts
        
        Returns:
            Dict mapping channel names to success status
        """
        # Check rate limit
        alert_key = f"{alert.alert_type}:{alert.source_ip or 'any'}"
        if not self._check_rate_limit(alert_key, rate_limit_seconds):
            logger.info(f"Alert rate limited: {alert_key}")
            return {}
        
        # Store in history
        self.alert_history.append(alert)
        
        # Send to channels
        results = {}
        target_channels = channels or list(self.channels.keys())
        
        for channel_name in target_channels:
            if channel_name in self.channels:
                channel = self.channels[channel_name]
                try:
                    results[channel_name] = await channel.send(alert)
                except Exception as e:
                    logger.error(f"Channel {channel_name} failed: {e}")
                    results[channel_name] = False
        
        return results
    
    def _check_rate_limit(self, key: str, seconds: int) -> bool:
        """Check if alert is within rate limit."""
        now = datetime.utcnow()
        
        if key not in self.rate_limits:
            self.rate_limits[key] = [now]
            return True
        
        # Clean old entries
        self.rate_limits[key] = [
            t for t in self.rate_limits[key]
            if (now - t).total_seconds() < seconds
        ]
        
        if len(self.rate_limits[key]) >= 1:
            return False
        
        self.rate_limits[key].append(now)
        return True
    
    async def send_attack_alert(
        self,
        honeypot_id: str,
        source_ip: str,
        attack_type: str,
        severity: str,
        details: str,
    ):
        """Send an attack alert."""
        alert = Alert(
            alert_type="attack_detected",
            title=f"Attack Detected: {attack_type}",
            message=f"Attack from {source_ip} on honeypot {honeypot_id}.\n\n{details}",
            priority=AlertPriority(severity) if severity in [e.value for e in AlertPriority] else AlertPriority.MEDIUM,
            honeypot_id=honeypot_id,
            source_ip=source_ip,
            metadata={"attack_type": attack_type},
        )
        
        return await self.send_alert(alert)
    
    async def send_adaptation_alert(
        self,
        honeypot_id: str,
        reason: str,
        changes: Dict[str, Any],
    ):
        """Send an adaptation alert."""
        alert = Alert(
            alert_type="adaptation_applied",
            title=f"Adaptation Applied: {honeypot_id}",
            message=f"Honeypot {honeypot_id} has been adapted.\n\nReason: {reason}",
            priority=AlertPriority.LOW,
            honeypot_id=honeypot_id,
            metadata={"changes": changes},
        )
        
        return await self.send_alert(alert)
    
    async def send_critical_alert(
        self,
        title: str,
        message: str,
        honeypot_id: str = None,
        source_ip: str = None,
    ):
        """Send a critical alert to all channels."""
        alert = Alert(
            alert_type="critical",
            title=title,
            message=message,
            priority=AlertPriority.CRITICAL,
            honeypot_id=honeypot_id,
            source_ip=source_ip,
        )
        
        return await self.send_alert(alert)


# Global alert manager
alert_manager: Optional[AlertManager] = None


def get_alert_manager() -> AlertManager:
    """Get or create the global alert manager."""
    global alert_manager
    if alert_manager is None:
        alert_manager = AlertManager()
    return alert_manager