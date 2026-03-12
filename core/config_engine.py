import json
import yaml
from typing import Dict, Any, Optional
from jsonschema import validate, ValidationError
from pathlib import Path
from core.models import HoneypotConfig, InteractionLevel
import logging

logger = logging.getLogger(__name__)

class ConfigEngine:
    SCHEMA = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "type": {"type": "string", "enum": ["ssh", "telnet", "http"]},
            "port": {"type": "integer", "minimum": 1, "maximum": 65535},
            "interaction_level": {"type": "string", "enum": ["low", "medium", "high"]},
            "hostname": {"type": "string"},
            "banner": {"type": ["string", "null"]},
            "fake_users": {"type": "array"},
            "fake_files": {"type": "array"},
            "allowed_commands": {"type": "array"},
            "response_delay": {"type": "number", "minimum": 0},
            "max_sessions": {"type": "integer", "minimum": 1},
            "session_timeout": {"type": "integer", "minimum": 1},
            "custom_responses": {"type": "object"}
        },
        "required": ["name", "type", "port"]
    }
    
    def __init__(self, config_dir: str = "./honeypots/cowrie"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.version_history: Dict[str, list] = {}
        
    def validate_config(self, config: Dict[str, Any]) -> bool:
        try:
            validate(instance=config, schema=self.SCHEMA)
            return True
        except ValidationError as e:
            logger.error(f"Config validation failed: {e.message}")
            return False
    
    def generate_default_config(self, name: str, port: int = 2222) -> HoneypotConfig:
        return HoneypotConfig(
            name=name,
            type="ssh",
            port=port,
            interaction_level=InteractionLevel.LOW,
            hostname="ubuntu-server",
            banner="SSH-2.0-OpenSSH_8.2p1 Ubuntu-4ubuntu0.5",
            fake_users=[
                {"username": "root", "password": "toor"},
                {"username": "admin", "password": "admin"},
                {"username": "user", "password": "password"}
            ],
            fake_files=["/etc/passwd", "/etc/shadow", "/var/log/auth.log"],
            allowed_commands=["ls", "pwd", "whoami", "uname", "cat"],
            response_delay=0.1,
            max_sessions=5,
            session_timeout=300
        )
    
    def save_config(self, config: HoneypotConfig, honeypot_id: str) -> Path:
        config_dict = config.model_dump()
        
        # Save version history
        if honeypot_id not in self.version_history:
            self.version_history[honeypot_id] = []
        self.version_history[honeypot_id].append(config_dict)
        
        # Save to file
        config_path = self.config_dir / f"{honeypot_id}.json"
        with open(config_path, 'w') as f:
            json.dump(config_dict, f, indent=2)
        
        logger.info(f"Config saved for {honeypot_id}")
        return config_path
    
    def load_config(self, honeypot_id: str) -> Optional[HoneypotConfig]:
        config_path = self.config_dir / f"{honeypot_id}.json"
        if not config_path.exists():
            return None
        
        with open(config_path, 'r') as f:
            config_dict = json.load(f)
        
        return HoneypotConfig(**config_dict)
    
    def rollback_config(self, honeypot_id: str, version: int = -1) -> Optional[HoneypotConfig]:
        if honeypot_id not in self.version_history:
            logger.warning(f"No version history for {honeypot_id}")
            return None
        
        history = self.version_history[honeypot_id]
        if abs(version) > len(history):
            logger.error(f"Version {version} not found")
            return None
        
        config_dict = history[version]
        config = HoneypotConfig(**config_dict)
        self.save_config(config, honeypot_id)
        
        logger.info(f"Rolled back {honeypot_id} to version {version}")
        return config
    
    def merge_configs(self, base: HoneypotConfig, updates: Dict[str, Any]) -> HoneypotConfig:
        config_dict = base.model_dump()
        config_dict.update(updates)
        return HoneypotConfig(**config_dict)
