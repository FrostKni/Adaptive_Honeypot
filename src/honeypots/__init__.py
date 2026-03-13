"""
Honeypot implementations for various protocols.
"""
from .base import (
    SSHHoneypot,
    HTTPHoneypot,
    FTPHoneypot,
    TelnetHoneypot,
    get_honeypot_handler,
)

__all__ = [
    "SSHHoneypot",
    "HTTPHoneypot",
    "FTPHoneypot",
    "TelnetHoneypot",
    "get_honeypot_handler",
]