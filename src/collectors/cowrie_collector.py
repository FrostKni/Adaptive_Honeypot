"""
Cowrie log collector - ingests Cowrie honeypot logs into the database.
Extracts real IPs, session tracking, and broadcasts via WebSocket.
Integrates with Cognitive Deception Engine for real-time command analysis.
"""
import asyncio
import json
import re
import logging
from datetime import datetime
from typing import Optional, Dict, Any, Set
from uuid import uuid4

import docker
from docker.errors import DockerException

from src.core.db.models import Session, AttackEvent, AttackSeverity, AttackType, ThreatLevel
from src.collectors.cognitive_bridge import (
    get_cognitive_bridge,
    CognitiveIntegrationBridge,
    CognitiveAnalysisResult,
)


logger = logging.getLogger(__name__)


class CowrieLogCollector:
    """
    Collects and parses logs from Cowrie honeypot containers.
    
    Parses events like:
    - New connections with source IP/port
    - Login attempts (success/failure)
    - Commands executed
    - Connection close
    """
    
    # Regex patterns for parsing Cowrie logs
    PATTERNS = {
        # New connection: "New connection: 172.18.0.1:57728 (172.18.0.2:2222) [session: 58edcf031f6a]"
        "new_connection": re.compile(
            r"New connection: ([\d.]+):(\d+) \([\d.]+:\d+\) \[session: ([a-f0-9]+)\]"
        ),
        # Login attempt: "[HoneyPotSSHTransport,2,172.18.0.1] login attempt [b'root'/b''] succeeded"
        "login_attempt": re.compile(
            r"\[HoneyPotSSHTransport,\d+,([\d.]+)\] login attempt \[b?'([^']+)'/b?'([^']*)'\] (succeeded|failed)"
        ),
        # Command: "[HoneyPotSSHTransport,2,172.18.0.1] CMD: ls"
        "command": re.compile(
            r"\[HoneyPotSSHTransport,\d+,([\d.]+)\] CMD: (.+)"
        ),
        # Connection lost: "[HoneyPotSSHTransport,2,172.18.0.1] Connection lost after 225.0 seconds"
        "connection_lost": re.compile(
            r"\[HoneyPotSSHTransport,\d+,([\d.]+)\] Connection lost after ([\d.]+) seconds"
        ),
        # Authenticated: "[HoneyPotSSHTransport,2,172.18.0.1] b'root' authenticated with b'password'"
        "authenticated": re.compile(
            r"\[HoneyPotSSHTransport,\d+,([\d.]+)\] b?'([^']+)' authenticated with b?'([^']+)'"
        ),
        # Generic IP extraction from log line
        "transport_ip": re.compile(
            r"\[HoneyPotSSHTransport,\d+,([\d.]+)\]"
        ),
    }
    
    def __init__(self):
        """Initialize Docker client and cognitive integration."""
        try:
            self.client = docker.from_env()
            self._running = False
            # Track active sessions: {cowrie_session_id: {ip, port, honeypot_id, db_session_id}}
            self._active_sessions: Dict[str, Dict[str, Any]] = {}
            # Track processed log lines to avoid duplicates
            self._processed_lines: Set[str] = set()
            # WebSocket manager reference
            self._ws_manager = None
            # Cognitive integration bridge
            self._cognitive_bridge: Optional[CognitiveIntegrationBridge] = None
            # Store cognitive analysis results for sessions
            self._cognitive_results: Dict[str, CognitiveAnalysisResult] = {}
        except DockerException as e:
            logger.error(f"Failed to connect to Docker: {e}")
            raise
    
    def set_ws_manager(self, manager):
        """Set WebSocket manager for broadcasting events."""
        self._ws_manager = manager
        # Also set on cognitive bridge if initialized
        if self._cognitive_bridge:
            self._cognitive_bridge.set_ws_manager(manager)
    
    def _get_cognitive_bridge(self) -> CognitiveIntegrationBridge:
        """Get or initialize the cognitive bridge."""
        if self._cognitive_bridge is None:
            self._cognitive_bridge = get_cognitive_bridge()
            if self._ws_manager:
                self._cognitive_bridge.set_ws_manager(self._ws_manager)
        return self._cognitive_bridge
    
    async def start(self, poll_interval: int = 2):
        """
        Start collecting logs from all Cowrie containers.
        
        Args:
            poll_interval: Seconds between log polls
        """
        self._running = True
        logger.info("Starting Cowrie log collector...")
        
        while self._running:
            try:
                await self._collect_logs()
            except Exception as e:
                logger.error(f"Error collecting logs: {e}")
            
            await asyncio.sleep(poll_interval)
    
    def stop(self):
        """Stop the collector."""
        self._running = False
        logger.info("Cowrie log collector stopped")
    
    async def _collect_logs(self):
        """Collect logs from all honeypot containers."""
        try:
            containers = self.client.containers.list(
                filters={"label": "honeypot.id"}
            )
            
            for container in containers:
                try:
                    await self._process_container_logs(container)
                except Exception as e:
                    logger.error(f"Error processing container {container.id[:12]}: {e}")
                    
        except DockerException as e:
            logger.error(f"Docker error: {e}")
    
    async def _process_container_logs(self, container):
        """Process logs from a single container."""
        labels = container.labels
        honeypot_id = labels.get("honeypot.id")
        honeypot_name = labels.get("honeypot.name", "unknown")
        
        if not honeypot_id:
            return
        
        try:
            # Get recent logs with timestamps
            logs = container.logs(tail=200, timestamps=True).decode("utf-8")
        except Exception as e:
            logger.error(f"Failed to get logs: {e}")
            return
        
        for line in logs.strip().split("\n"):
            if not line:
                continue
            
            # Create a stable hash to track processed lines (hash() is
            # process-local and not collision-safe for dedup purposes)
            import hashlib
            line_hash = hashlib.md5(line.encode(), usedforsecurity=False).hexdigest()
            if line_hash in self._processed_lines:
                continue
            self._processed_lines.add(line_hash)
            
            # Limit the set size
            if len(self._processed_lines) > 10000:
                self._processed_lines = set(list(self._processed_lines)[-5000:])
            
            try:
                await self._process_log_line(line, honeypot_id, honeypot_name)
            except Exception as e:
                logger.debug(f"Error parsing line: {e}")
    
    async def _process_log_line(self, line: str, honeypot_id: str, honeypot_name: str):
        """Process a single log line and create database records."""
        # Docker adds its own timestamp, format: "2026-03-12T11:45:10.119351326Z 2026-03-12T11:45:10+0000 ..."
        # We need to handle both Docker timestamp and Cowrie timestamp
        
        # Try to extract timestamps
        # Docker format: YYYY-MM-DDTHH:MM:SS.ffffffZ
        docker_ts_match = re.match(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z)\s+(.+)$", line)
        if docker_ts_match:
            timestamp_str = docker_ts_match.group(1)
            rest = docker_ts_match.group(2)
            try:
                # Parse Docker timestamp (UTC)
                timestamp = datetime.strptime(timestamp_str[:19], "%Y-%m-%dT%H:%M:%S")
            except ValueError:
                timestamp = datetime.utcnow()
            
            # Check if there's a Cowrie timestamp in the rest
            cowrie_match = re.match(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{4})\s+(.+)$", rest)
            if cowrie_match:
                log_content = cowrie_match.group(2)
            else:
                log_content = rest
        else:
            # Try Cowrie timestamp only
            timestamp_match = re.match(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{4})\s+(.+)$", line)
            if timestamp_match:
                timestamp_str = timestamp_match.group(1)
                log_content = timestamp_match.group(2)
                try:
                    timestamp = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S%z")
                except ValueError:
                    timestamp = datetime.utcnow()
            else:
                log_content = line
                timestamp = datetime.utcnow()
        
        # 1. New connection - captures real IP and session ID
        new_conn_match = self.PATTERNS["new_connection"].search(log_content)
        if new_conn_match:
            source_ip = new_conn_match.group(1)
            source_port = int(new_conn_match.group(2))
            cowrie_session = new_conn_match.group(3)
            
            # Store session info
            self._active_sessions[cowrie_session] = {
                "ip": source_ip,
                "port": source_port,
                "honeypot_id": honeypot_id,
                "db_session_id": None,
                "started_at": timestamp,
            }
            
            logger.info(f"New connection from {source_ip}:{source_port} session={cowrie_session}")
            return
        
        # 2. Login attempt
        login_match = self.PATTERNS["login_attempt"].search(log_content)
        if login_match:
            source_ip = login_match.group(1)
            username = login_match.group(2)
            password = login_match.group(3) if login_match.group(3) else ""
            success = login_match.group(4) == "succeeded"
            
            await self._create_attack_event(
                honeypot_id=honeypot_id,
                honeypot_name=honeypot_name,
                event_type="login_attempt",
                source_ip=source_ip,
                source_port=0,
                data={
                    "username": username,
                    "password": "***" if password else "",
                    "success": success,
                },
                timestamp=timestamp,
                severity="high" if success else "medium",
            )
            
            # Create session on successful login
            if success:
                db_session_id = f"session-{uuid4().hex[:12]}"
                await self._create_session(
                    session_id=db_session_id,
                    honeypot_id=honeypot_id,
                    source_ip=source_ip,
                    username=username,
                    timestamp=timestamp,
                )
                # Update active sessions with the db_session_id
                for sess_id, sess_data in self._active_sessions.items():
                    if sess_data.get("ip") == source_ip and sess_data.get("honeypot_id") == honeypot_id:
                        sess_data["db_session_id"] = db_session_id
                        break
            
            return
        
        # 3. Command execution
        cmd_match = self.PATTERNS["command"].search(log_content)
        if cmd_match:
            source_ip = cmd_match.group(1)
            command = cmd_match.group(2).strip()
            
            # Find session ID for this source IP
            session_id = self._find_session_id(source_ip, honeypot_id)
            
            # Process command through cognitive deception engine
            cognitive_result = await self._process_command_cognitively(
                session_id=session_id,
                source_ip=source_ip,
                command=command,
                honeypot_id=honeypot_id,
                timestamp=timestamp,
            )
            
            # Create attack event with cognitive data
            await self._create_attack_event(
                honeypot_id=honeypot_id,
                honeypot_name=honeypot_name,
                event_type="command",
                source_ip=source_ip,
                source_port=0,
                data={
                    "command": command,
                    "cognitive_analysis": cognitive_result.to_dict() if cognitive_result else None,
                },
                timestamp=timestamp,
                severity="info",
                session_id=session_id,
            )
            return
        
        # 4. Connection lost
        conn_lost_match = self.PATTERNS["connection_lost"].search(log_content)
        if conn_lost_match:
            source_ip = conn_lost_match.group(1)
            duration = float(conn_lost_match.group(2))
            
            # Find and end cognitive session
            session_id = self._find_session_id(source_ip, honeypot_id)
            if session_id:
                await self._end_cognitive_session(session_id)
            
            await self._create_attack_event(
                honeypot_id=honeypot_id,
                honeypot_name=honeypot_name,
                event_type="session_end",
                source_ip=source_ip,
                source_port=0,
                data={"duration_seconds": duration},
                timestamp=timestamp,
                severity="info",
                session_id=session_id,
            )
            return
        
        # 5. Authenticated
        auth_match = self.PATTERNS["authenticated"].search(log_content)
        if auth_match:
            source_ip = auth_match.group(1)
            username = auth_match.group(2)
            auth_method = auth_match.group(3)
            
            await self._create_attack_event(
                honeypot_id=honeypot_id,
                honeypot_name=honeypot_name,
                event_type="authenticated",
                source_ip=source_ip,
                source_port=0,
                data={
                    "username": username,
                    "method": auth_method,
                },
                timestamp=timestamp,
                severity="high",
            )
            return
    
    async def _create_session(
        self,
        session_id: str,
        honeypot_id: str,
        source_ip: str,
        username: str,
        timestamp: datetime,
    ):
        """Create a new session record."""
        from src.core.db.session import get_db_context
        async with get_db_context() as session:
            try:
                new_session = Session(
                    id=session_id,
                    honeypot_id=honeypot_id,
                    source_ip=source_ip,
                    source_port=0,
                    username=username,
                    auth_success=True,
                    attack_type=AttackType.BRUTE_FORCE,
                    severity=AttackSeverity.HIGH,
                    threat_level=ThreatLevel.SUSPICIOUS,
                    started_at=timestamp,
                    commands=[],
                )
                session.add(new_session)
                await session.commit()
                logger.info(f"Created session {session_id} from {source_ip}")
            except Exception as e:
                logger.error(f"Failed to create session: {e}")
                await session.rollback()
    
    async def _create_attack_event(
        self,
        honeypot_id: str,
        honeypot_name: str,
        event_type: str,
        source_ip: str,
        source_port: int,
        data: Dict[str, Any],
        timestamp: datetime,
        severity: str = "info",
        session_id: str = None,
    ):
        """Create an attack event, broadcast via WebSocket, and send to AI for analysis."""
        severity_map = {
            "info": AttackSeverity.INFO,
            "low": AttackSeverity.LOW,
            "medium": AttackSeverity.MEDIUM,
            "high": AttackSeverity.HIGH,
            "critical": AttackSeverity.CRITICAL,
        }

        from src.core.db.session import get_db_context
        async with get_db_context() as session:
            try:
                event = AttackEvent(
                    session_id=session_id,
                    event_type=event_type,
                    timestamp=timestamp,
                    data={"source_ip": source_ip, **data},
                    severity=severity_map.get(severity, AttackSeverity.INFO),
                    tags=[event_type, "cowrie", honeypot_name],
                )
                session.add(event)
                await session.commit()

                logger.info(f"Event: {event_type} from {source_ip} on {honeypot_name}")

                await self._send_to_ai(
                    honeypot_id=honeypot_id,
                    honeypot_name=honeypot_name,
                    event_type=event_type,
                    source_ip=source_ip,
                    severity=severity,
                    timestamp=timestamp,
                    data=data,
                )

                await self._broadcast_event(
                    honeypot_id=honeypot_id,
                    honeypot_name=honeypot_name,
                    event_type=event_type,
                    source_ip=source_ip,
                    source_port=source_port,
                    severity=severity,
                    timestamp=timestamp.isoformat() if timestamp else None,
                    data=data,
                )

            except Exception as e:
                logger.error(f"Failed to create event: {e}")
                await session.rollback()
    
    async def _broadcast_event(self, **kwargs):
        """Broadcast event to WebSocket clients."""
        try:
            from src.api.v1.endpoints.websocket import broadcast_attack_event

            # broadcast_attack_event already sends to all subscribers on the
            # "attacks" channel — do NOT also call ws_manager.broadcast() or
            # every event would be delivered twice.
            await broadcast_attack_event(
                honeypot_id=kwargs.get('honeypot_id', ''),
                event=kwargs
            )

            logger.debug(f"Broadcasted {kwargs.get('event_type')} event")
        except Exception as e:
            logger.debug(f"Failed to broadcast: {e}")
    
    async def _send_to_ai(
        self,
        honeypot_id: str,
        honeypot_name: str,
        event_type: str,
        source_ip: str,
        severity: str,
        timestamp: datetime,
        data: Dict[str, Any],
    ):
        """Send attack event to AI monitoring service for analysis."""
        try:
            from src.ai.monitoring import ai_service, AttackEvent as AIAttackEvent
            
            # Only send significant events to AI (not every info event)
            if severity in ["high", "critical"] or event_type in ["login_attempt", "command"]:
                ai_event = AIAttackEvent(
                    id=f"evt-{timestamp.timestamp():.0f}-{honeypot_id[:8]}",
                    source_ip=source_ip,
                    honeypot_id=honeypot_id,
                    attack_type=event_type,
                    timestamp=timestamp,
                    severity=severity,
                    raw_log=json.dumps(data),
                    commands=[data.get("command", "")] if data.get("command") else [],
                    credentials_tried=[{"username": data.get("username", ""), "password": "***"}] if data.get("username") else [],
                )
                
                ai_service.add_event(ai_event)
                logger.debug(f"Sent {event_type} from {source_ip} to AI for analysis")
                
        except Exception as e:
            logger.debug(f"Failed to send to AI: {e}")
    
    def _find_session_id(self, source_ip: str, honeypot_id: str) -> Optional[str]:
        """
        Find the database session ID for a source IP and honeypot.
        
        Args:
            source_ip: Source IP address
            honeypot_id: Honeypot identifier
            
        Returns:
            Session ID if found, None otherwise
        """
        for sess_id, sess_data in self._active_sessions.items():
            if (sess_data.get("ip") == source_ip and 
                sess_data.get("honeypot_id") == honeypot_id):
                return sess_data.get("db_session_id")
        return None
    
    async def _process_command_cognitively(
        self,
        session_id: Optional[str],
        source_ip: str,
        command: str,
        honeypot_id: str,
        timestamp: datetime,
    ) -> Optional[CognitiveAnalysisResult]:
        """
        Process a command through the Cognitive Deception Engine.
        
        Routes the command through cognitive analysis to generate
        a deceptive response and update the attacker's profile.
        
        Args:
            session_id: Database session ID (may be None)
            source_ip: Source IP of the attacker
            command: The command to process
            honeypot_id: Honeypot identifier
            timestamp: Command timestamp
            
        Returns:
            CognitiveAnalysisResult if processing succeeded
        """
        try:
            # Get cognitive bridge
            bridge = self._get_cognitive_bridge()
            
            # Use IP-based session ID if no db_session_id
            effective_session_id = session_id or f"cog-{source_ip}-{honeypot_id[:8]}"
            
            # Build session data
            session_data = {
                "honeypot_id": honeypot_id,
                "source_ip": source_ip,
                "started_at": timestamp.isoformat(),
            }
            
            # Process through cognitive engine
            result = await bridge.process_command(
                session_id=effective_session_id,
                command=command,
                source_ip=source_ip,
                session_data=session_data,
            )
            
            # Store result for later retrieval
            self._cognitive_results[effective_session_id] = result
            
            logger.info(
                f"Cognitive analysis: session={effective_session_id}, "
                f"command='{command[:30]}...', strategy={result.deception_response.strategy_used}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error in cognitive processing: {e}")
            return None
    
    async def _end_cognitive_session(self, session_id: str):
        """
        End a cognitive profiling session.
        
        Finalizes the cognitive profile and stores the final analysis.
        
        Args:
            session_id: Session to end
        """
        try:
            bridge = self._get_cognitive_bridge()
            summary = await bridge.end_session(session_id)
            
            if summary:
                logger.info(
                    f"Cognitive session ended: {session_id}, "
                    f"commands={summary.get('total_commands', 0)}, "
                    f"biases={len(summary.get('final_profile', {}).get('detected_biases', []))}"
                )
                
                # Broadcast final profile
                if self._ws_manager:
                    await self._ws_manager.broadcast({
                        "type": "cognitive_session_summary",
                        "session_id": session_id,
                        "summary": summary,
                    })
            
            # Clean up stored result
            self._cognitive_results.pop(session_id, None)
            
        except Exception as e:
            logger.error(f"Error ending cognitive session: {e}")
    
    def get_cognitive_result(self, session_id: str) -> Optional[CognitiveAnalysisResult]:
        """
        Get the latest cognitive analysis result for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Latest CognitiveAnalysisResult or None
        """
        return self._cognitive_results.get(session_id)
    
    async def get_cognitive_profile(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the cognitive profile for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Cognitive profile dictionary or None
        """
        try:
            bridge = self._get_cognitive_bridge()
            profile = bridge.engine.get_profile(session_id)
            return profile.to_dict() if profile else None
        except Exception as e:
            logger.error(f"Error getting cognitive profile: {e}")
            return None


# Global collector instance
_collector: Optional[CowrieLogCollector] = None


def get_collector() -> CowrieLogCollector:
    """Get the global collector instance."""
    global _collector
    if _collector is None:
        _collector = CowrieLogCollector()
    return _collector


async def run_collector():
    """Run the log collector as a standalone service."""
    collector = get_collector()
    await collector.start(poll_interval=2)


if __name__ == "__main__":
    asyncio.run(run_collector())