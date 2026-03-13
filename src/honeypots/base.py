"""
SSH Honeypot - Cowrie-based implementation.
"""
import logging
import os
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class SSHHoneypot:
    """
    SSH Honeypot implementation using Cowrie.
    
    Cowrie is a medium interaction SSH honeypot that logs:
    - Brute force attempts
    - Executed commands
    - Downloaded files
    - SSH keys used
    """
    
    def __init__(self, honeypot_id: str, config: Dict[str, Any] = None):
        self.honeypot_id = honeypot_id
        self.config = config or {}
        self._sessions: Dict[str, Dict] = {}
    
    def get_container_config(self, port: int) -> Dict[str, Any]:
        """
        Get Docker container configuration for Cowrie.
        
        Returns:
            Dict with container configuration
        """
        return {
            "image": "cowrie/cowrie:latest",
            "environment": {
                # Cowrie configuration via environment
                "COWRIE_SSH_LISTEN_ENDPOINT": f"tcp:0.0.0.0:2222",
                "COWRIE_TELNET_LISTEN_ENDPOINT": f"tcp:0.0.0.0:2323",
                "COWRIE_SSH_VERSION": self.config.get("ssh_version", "SSH-2.0-OpenSSH_8.9p1 Ubuntu-3"),
                "COWRIE_HOSTNAME": self.config.get("hostname", "ubuntu-server"),
                "COWRIE_SFAUTHFILE": "data/userdb.txt",
            },
            "ports": {
                "2222/tcp": port,
            },
            "volumes": {
                f"cowrie-{self.honeypot_id}-data": {
                    "bind": "/cowrie/data",
                    "mode": "rw"
                },
                f"cowrie-{self.honeypot_id}-log": {
                    "bind": "/cowrie/var/log/cowrie",
                    "mode": "rw"
                },
                f"cowrie-{self.honeypot_id}-dl": {
                    "bind": "/cowrie/dl",
                    "mode": "rw"
                },
            },
            "labels": {
                "honeypot.id": self.honeypot_id,
                "honeypot.type": "ssh",
            },
        }
    
    def parse_logs(self, log_line: str) -> Optional[Dict[str, Any]]:
        """
        Parse Cowrie log lines to extract attack data.
        
        Args:
            log_line: Raw log line from Cowrie
            
        Returns:
            Parsed attack event or None
        """
        try:
            # Cowrie JSON log format
            import json
            if log_line.strip().startswith("{"):
                data = json.loads(log_line)
                
                event_type = data.get("eventid")
                
                if event_type == "cowrie.session.connect":
                    return {
                        "type": "connection",
                        "session_id": data.get("session"),
                        "source_ip": data.get("src_ip"),
                        "source_port": data.get("src_port"),
                        "protocol": "ssh",
                        "timestamp": data.get("timestamp"),
                    }
                
                elif event_type == "cowrie.login.failed":
                    return {
                        "type": "login_failed",
                        "session_id": data.get("session"),
                        "username": data.get("username"),
                        "password": data.get("password"),
                        "source_ip": data.get("src_ip"),
                        "timestamp": data.get("timestamp"),
                    }
                
                elif event_type == "cowrie.login.success":
                    return {
                        "type": "login_success",
                        "session_id": data.get("session"),
                        "username": data.get("username"),
                        "password": data.get("password"),
                        "source_ip": data.get("src_ip"),
                        "timestamp": data.get("timestamp"),
                    }
                
                elif event_type == "cowrie.command.input":
                    return {
                        "type": "command",
                        "session_id": data.get("session"),
                        "command": data.get("input"),
                        "source_ip": data.get("src_ip"),
                        "timestamp": data.get("timestamp"),
                    }
                
                elif event_type == "cowrie.session.file_download":
                    return {
                        "type": "download",
                        "session_id": data.get("session"),
                        "url": data.get("url"),
                        "outfile": data.get("outfile"),
                        "shasum": data.get("shasum"),
                        "source_ip": data.get("src_ip"),
                        "timestamp": data.get("timestamp"),
                    }
                
        except json.JSONDecodeError:
            pass
        except Exception as e:
            logger.debug(f"Failed to parse log line: {e}")
        
        return None


class HTTPHoneypot:
    """
    HTTP Honeypot - lightweight web server that logs requests.
    """
    
    def __init__(self, honeypot_id: str, config: Dict[str, Any] = None):
        self.honeypot_id = honeypot_id
        self.config = config or {}
    
    def get_container_config(self, port: int) -> Dict[str, Any]:
        """Get container configuration for HTTP honeypot."""
        return {
            "image": "nginx:alpine",
            "ports": {
                "80/tcp": port,
            },
            "environment": {
                "HONEYPOT_ID": self.honeypot_id,
            },
            "volumes": {
                f"http-{self.honeypot_id}-logs": {
                    "bind": "/var/log/nginx",
                    "mode": "rw"
                },
            },
            "labels": {
                "honeypot.id": self.honeypot_id,
                "honeypot.type": "http",
            },
        }


class FTPHoneypot:
    """
    FTP Honeypot - logs login attempts and file transfers.
    """
    
    def __init__(self, honeypot_id: str, config: Dict[str, Any] = None):
        self.honeypot_id = honeypot_id
        self.config = config or {}
    
    def get_container_config(self, port: int) -> Dict[str, Any]:
        """Get container configuration for FTP honeypot."""
        return {
            "image": "stilliard/pure-ftpd:latest",
            "ports": {
                "21/tcp": port,
            },
            "environment": {
                "PUBLICHOST": self.config.get("public_host", "0.0.0.0"),
                "ADDED_FLAGS": "--createhomedir --keepallfiles",
            },
            "volumes": {
                f"ftp-{self.honeypot_id}-data": {
                    "bind": "/home/ftpusers",
                    "mode": "rw"
                },
                f"ftp-{self.honeypot_id}-logs": {
                    "bind": "/var/log/pure-ftpd",
                    "mode": "rw"
                },
            },
            "labels": {
                "honeypot.id": self.honeypot_id,
                "honeypot.type": "ftp",
            },
        }


class TelnetHoneypot:
    """
    Telnet Honeypot - Cowrie also supports telnet.
    """
    
    def __init__(self, honeypot_id: str, config: Dict[str, Any] = None):
        self.honeypot_id = honeypot_id
        self.config = config or {}
    
    def get_container_config(self, port: int) -> Dict[str, Any]:
        """Get container configuration for Telnet honeypot."""
        return {
            "image": "cowrie/cowrie:latest",
            "ports": {
                "2323/tcp": port,
            },
            "environment": {
                "COWRIE_TELNET_LISTEN_ENDPOINT": f"tcp:0.0.0.0:2323",
                "COWRIE_HOSTNAME": self.config.get("hostname", "router"),
            },
            "volumes": {
                f"telnet-{self.honeypot_id}-data": {
                    "bind": "/cowrie/data",
                    "mode": "rw"
                },
                f"telnet-{self.honeypot_id}-log": {
                    "bind": "/cowrie/var/log/cowrie",
                    "mode": "rw"
                },
            },
            "labels": {
                "honeypot.id": self.honeypot_id,
                "honeypot.type": "telnet",
            },
        }


# Factory function
def get_honeypot_handler(honeypot_type: str, honeypot_id: str, config: Dict = None):
    """Get the appropriate honeypot handler."""
    from src.core.db import HoneypotType
    
    handlers = {
        HoneypotType.SSH: SSHHoneypot,
        HoneypotType.HTTP: HTTPHoneypot,
        HoneypotType.FTP: FTPHoneypot,
        HoneypotType.TELNET: TelnetHoneypot,
    }
    
    handler_class = handlers.get(honeypot_type)
    if handler_class:
        return handler_class(honeypot_id, config)
    
    raise ValueError(f"Unknown honeypot type: {honeypot_type}")