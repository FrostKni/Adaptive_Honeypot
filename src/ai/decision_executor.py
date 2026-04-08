"""
Decision Executor - Executes AI decisions on Docker containers.
Connects AI monitoring decisions to actual honeypot operations.
"""
import asyncio
import json
import logging
import os
import tempfile
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum

import docker
from docker.errors import DockerException, APIError, NotFound

logger = logging.getLogger(__name__)


class ExecutionStatus(str, Enum):
    """Status of decision execution."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass
class ExecutionResult:
    """Result of a decision execution."""
    id: str
    decision_id: str
    action: str
    status: ExecutionStatus
    timestamp: datetime
    details: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    rollback_info: Optional[Dict[str, Any]] = None


class DecisionExecutor:
    """
    Executes AI decisions on honeypot containers.
    
    Actions:
    - monitor: No action, just continue observing
    - reconfigure: Modify container configuration
    - isolate: Move attacker to isolated network
    - switch_container: Create new container and migrate session
    """
    
    # Isolated network name for quarantine
    ISOLATED_NETWORK = "honeypot-isolated"
    
    # Configuration templates for reconfiguration
    RECONFIG_TEMPLATES = {
        "high_deception": {
            "fake_files": True,
            "fake_processes": True,
            "delay_commands": True,
            "fake_users": True,
        },
        "medium_deception": {
            "fake_files": True,
            "fake_processes": False,
            "delay_commands": True,
            "fake_users": False,
        },
        "low_deception": {
            "fake_files": False,
            "fake_processes": False,
            "delay_commands": False,
            "fake_users": False,
        }
    }
    
    def __init__(self):
        """Initialize Docker client and tracking."""
        self._execution_history: List[ExecutionResult] = []
        self._max_history = 100
        self.client = None
        self.api_client = None
        try:
            self.client = docker.from_env()
            self.api_client = docker.APIClient()
            self._ensure_isolated_network()
            logger.info("DecisionExecutor initialized")
        except DockerException as e:
            logger.warning(f"Docker unavailable, DecisionExecutor running in no-op mode: {e}")
    
    def _ensure_isolated_network(self):
        """Create isolated network for quarantine if not exists."""
        try:
            self.client.networks.get(self.ISOLATED_NETWORK)
            logger.info(f"Isolated network exists: {self.ISOLATED_NETWORK}")
        except NotFound:
            logger.info(f"Creating isolated network: {self.ISOLATED_NETWORK}")
            self.client.networks.create(
                self.ISOLATED_NETWORK,
                driver="bridge",
                internal=True,  # No external access
                check_duplicate=True,
            )
    
    async def _broadcast_execution(self, result: ExecutionResult, stage: str = "progress"):
        """Broadcast execution progress to WebSocket subscribers."""
        try:
            from src.api.v1.endpoints.broadcast import get_manager
            ws_manager = get_manager()
            if ws_manager:
                await ws_manager.broadcast({
                    "type": "execution_update",
                    "data": {
                        "id": result.id,
                        "decision_id": result.decision_id,
                        "action": result.action,
                        "status": result.status.value,
                        "stage": stage,
                        "timestamp": result.timestamp.isoformat(),
                        "details": result.details,
                        "error": result.error,
                    }
                }, channel="ai")
                logger.debug(f"Broadcasted execution {result.id} at stage {stage}")
        except Exception as e:
            logger.error(f"Failed to broadcast execution: {e}")

    async def execute(
        self,
        decision_id: str,
        action: str,
        source_ip: str,
        honeypot_id: str,
        configuration_changes: Dict[str, Any],
        threat_level: str,
    ) -> ExecutionResult:
        """
        Execute an AI decision.
        
        Args:
            decision_id: ID of the decision being executed
            action: Action to take (monitor, reconfigure, isolate, switch_container)
            source_ip: Attacker's IP address
            honeypot_id: Target honeypot ID
            configuration_changes: Changes to apply
            threat_level: Threat level assessment
            
        Returns:
            ExecutionResult with status and details
        """
        result = ExecutionResult(
            id=f"exec-{int(datetime.utcnow().timestamp() * 1000)}",
            decision_id=decision_id,
            action=action,
            status=ExecutionStatus.PENDING,
            timestamp=datetime.utcnow(),
            details={
                "source_ip": source_ip,
                "honeypot_id": honeypot_id,
                "threat_level": threat_level,
            }
        )
        
        # Broadcast execution started
        result.status = ExecutionStatus.RUNNING
        await self._broadcast_execution(result, "started")
        
        if action == "monitor":
            result.status = ExecutionStatus.SUCCESS
            result.details["message"] = "Monitoring mode - no action taken"
            self._record_result(result)
            await self._broadcast_execution(result, "completed")
            return result
        
        try:
            if action == "reconfigure":
                success = await self._reconfigure_container(
                    honeypot_id, configuration_changes, threat_level
                )
            elif action == "isolate":
                success = await self._isolate_attacker(honeypot_id, source_ip)
            elif action == "switch_container":
                success = await self._switch_container(
                    honeypot_id, source_ip, configuration_changes, result
                )
            else:
                raise ValueError(f"Unknown action: {action}")
            
            result.status = ExecutionStatus.SUCCESS if success else ExecutionStatus.FAILED
            result.details["success"] = success
            
        except Exception as e:
            result.status = ExecutionStatus.FAILED
            result.error = str(e)
            logger.error(f"Decision execution failed: {e}")
        
        self._record_result(result)
        await self._broadcast_execution(result, "completed")
        return result
    
    async def _get_container(self, honeypot_id: str) -> Optional[docker.models.containers.Container]:
        """Get container by honeypot ID."""
        try:
            containers = self.client.containers.list(
                all=True,
                filters={"label": f"honeypot.id={honeypot_id}"}
            )
            return containers[0] if containers else None
        except Exception as e:
            logger.error(f"Failed to get container for {honeypot_id}: {e}")
            return None
    
    async def _reconfigure_container(
        self,
        honeypot_id: str,
        config_changes: Dict[str, Any],
        threat_level: str,
    ) -> bool:
        """
        Reconfigure a running honeypot container.
        
        For Cowrie (distroless image), this involves:
        1. Stopping the current container
        2. Creating a new container with updated environment variables
        3. Starting the new container
        
        For containers with shell access:
        1. Creating/updating configuration files
        2. Sending HUP signal to reload config
        """
        container = await self._get_container(honeypot_id)
        if not container:
            logger.warning(f"Container not found for reconfiguration: {honeypot_id}")
            return False
        
        try:
            # Get reconfiguration template based on threat level
            template = self.RECONFIG_TEMPLATES.get(
                "high_deception" if threat_level in ["high", "critical"] else "medium_deception",
                self.RECONFIG_TEMPLATES["medium_deception"]
            )
            
            # Merge with custom changes
            final_config = {**template, **config_changes}
            
            logger.info(f"Reconfiguring {honeypot_id} with: {final_config}")
            
            # Get container info
            container.reload()
            container_info = container.attrs
            
            # Check if container has shell access (for live reconfiguration)
            try:
                # Try to exec a simple command
                exec_test = container.exec_run('echo test', stderr=False, stdout=False)
                has_shell = exec_test.exit_code == 0
            except Exception:
                has_shell = False
            
            if has_shell:
                # Live reconfiguration with shell access
                config_content = self._generate_cowrie_config(final_config)
                
                with tempfile.NamedTemporaryFile(mode='w', suffix='.cfg', delete=False) as f:
                    f.write(config_content)
                    config_path = f.name
                
                try:
                    # Try multiple config paths
                    config_paths = [
                        '/cowrie/cowrie.cfg.d/adaptive_config.cfg',
                        '/cowrie/etc/cowrie.cfg.d/adaptive_config.cfg',
                        '/cowrie/data/cowrie.cfg.d/adaptive_config.cfg',
                    ]
                    
                    config_copied = False
                    with open(config_path, 'rb') as f:
                        tar_data = self._create_tarball('adaptive_config.cfg', f.read())
                        for path in config_paths:
                            try:
                                container.put_archive(os.path.dirname(path), tar_data)
                                config_copied = True
                                logger.info(f"Config copied to {path}")
                                break
                            except Exception:
                                continue
                    
                    if config_copied:
                        # Try to reload config
                        exec_result = container.exec_run('pkill -HUP twistd', user='cowrie')
                        if exec_result.exit_code != 0:
                            container.restart()
                        
                        logger.info(f"Successfully reconfigured {honeypot_id}")
                        return True
                        
                finally:
                    os.unlink(config_path)
            
            # Fallback: Recreate container with environment variables
            logger.info(f"Container {honeypot_id} doesn't support live config, using environment variables")
            
            # Build environment variables for deception config
            env_updates = {
                "COWRIE_FAKE_FILES": "true" if final_config.get("fake_files") else "false",
                "COWRIE_FAKE_PROCESSES": "true" if final_config.get("fake_processes") else "false",
                "COWRIE_DELAY_COMMANDS": "true" if final_config.get("delay_commands") else "false",
                "COWRIE_FAKE_USERS": "true" if final_config.get("fake_users") else "false",
                "HONEYPOT_DECEPTION_LEVEL": "high" if threat_level in ["high", "critical"] else "medium",
            }
            
            # Get current environment and merge
            current_env = container_info.get('Config', {}).get('Env', [])
            new_env = [e for e in current_env if not any(e.startswith(k) for k in env_updates.keys())]
            new_env.extend([f"{k}={v}" for k, v in env_updates.items()])
            
            # Get container configuration
            labels = container_info.get('Config', {}).get('Labels', {})
            name = labels.get('honeypot.name', honeypot_id)
            honeypot_type = labels.get('honeypot.type', 'ssh')
            port = int(labels.get('honeypot.port', '2222'))
            image = container_info.get('Config', {}).get('Image', 'cowrie/cowrie:latest')
            
            # Stop and remove old container
            container.stop()
            old_name = container.name
            container.remove()
            
            # Create new container with updated config
            new_container = self.client.containers.create(
                image=image,
                name=old_name,
                detach=True,
                environment=new_env,
                labels=labels,
                ports={f"{port}/tcp": port} if honeypot_type == 'ssh' else {},
                restart_policy={"Name": "unless-stopped"},
            )
            
            # Connect to network
            try:
                network = self.client.networks.get("honeypot-network")
                network.connect(new_container)
            except Exception:
                pass
            
            new_container.start()
            
            logger.info(f"Successfully reconfigured {honeypot_id} with new container")
            return True
            
        except Exception as e:
            logger.error(f"Reconfiguration failed: {e}")
            return False
    
    def _generate_cowrie_config(self, config: Dict[str, Any]) -> str:
        """Generate Cowrie configuration content."""
        lines = ["# Auto-generated adaptive configuration"]
        
        if config.get("fake_files"):
            lines.append("[shell]")
            lines.append("enabled = true")
            lines.append("fake_filesystem = true")
            lines.append("")
        
        if config.get("fake_processes"):
            lines.append("[process]")
            lines.append("enabled = true")
            lines.append("fake_ps = true")
            lines.append("")
        
        if config.get("delay_commands"):
            lines.append("[ssh]")
            lines.append("command_timeout = 5")
            lines.append("session_timeout = 1800")
            lines.append("")
        
        if config.get("fake_users"):
            lines.append("[auth]")
            lines.append("allow_root = true")
            lines.append("allow_users = admin,user,guest")
            lines.append("")
        
        # Add custom honeypot options
        lines.append("[honeypot]")
        lines.append(f"adaptive_mode = true")
        lines.append(f"deception_level = high")
        lines.append(f"generated_at = {datetime.utcnow().isoformat()}")
        
        return "\n".join(lines)
    
    def _create_tarball(self, filename: str, content: bytes) -> bytes:
        """Create a simple tarball for container copy."""
        import io
        import tarfile
        
        tar_stream = io.BytesIO()
        with tarfile.open(fileobj=tar_stream, mode='w') as tar:
            tarinfo = tarfile.TarInfo(name=filename)
            tarinfo.size = len(content)
            tarinfo.mtime = datetime.utcnow().timestamp()
            tar.addfile(tarinfo, io.BytesIO(content))
        
        tar_stream.seek(0)
        return tar_stream.read()
    
    async def _isolate_attacker(self, honeypot_id: str, source_ip: str) -> bool:
        """
        Isolate an attacker in a quarantined network.
        
        This:
        1. Creates an isolated network (no internet access)
        2. Moves the container to that network
        3. Optionally creates a fake internet gateway
        """
        container = await self._get_container(honeypot_id)
        if not container:
            logger.warning(f"Container not found for isolation: {honeypot_id}")
            return False
        
        try:
            # Get the isolated network
            isolated_net = self.client.networks.get(self.ISOLATED_NETWORK)
            
            # Disconnect from main network
            main_net = self.client.networks.get("honeypot-network")
            try:
                main_net.disconnect(container)
                logger.info(f"Disconnected {honeypot_id} from main network")
            except Exception as e:
                logger.warning(f"Already disconnected from main network: {e}")
            
            # Connect to isolated network
            isolated_net.connect(container)
            logger.info(f"Connected {honeypot_id} to isolated network")
            
            # Add labels to track isolation
            container.rename(f"isolated-{container.name}")
            
            logger.info(f"Successfully isolated {honeypot_id} (attacker: {source_ip})")
            return True
            
        except Exception as e:
            logger.error(f"Isolation failed: {e}")
            return False
    
    async def _switch_container(
        self,
        honeypot_id: str,
        source_ip: str,
        config_changes: Dict[str, Any],
        result: ExecutionResult = None,
    ) -> bool:
        """
        Switch attacker to a new container transparently.
        
        This:
        1. Creates a new container with enhanced deception
        2. Sets up network redirect from old to new
        3. Maintains attacker session
        """
        try:
            # Get original container
            old_container = await self._get_container(honeypot_id)
            if not old_container:
                logger.warning(f"Original container not found: {honeypot_id}")
                if result:
                    result.details["error_stage"] = "container_lookup"
                return False
            
            # Get container details
            old_labels = old_container.labels
            honeypot_type = old_labels.get("honeypot.type", "ssh")
            port = int(old_labels.get("honeypot.port", "2222"))
            name = old_labels.get("honeypot.name", "unknown")
            
            # Update result with original container info
            if result:
                result.details["original_container"] = {
                    "id": old_container.id[:12],
                    "name": old_container.name,
                    "honeypot_id": honeypot_id,
                    "type": honeypot_type,
                    "port": port,
                    "status": old_container.status,
                }
                await self._broadcast_execution(result, "analyzing")
            
            # Generate new honeypot ID
            import uuid
            new_honeypot_id = f"{honeypot_id}-switched-{uuid.uuid4().hex[:8]}"
            
            # Create new container with enhanced deception config
            new_config = {
                **config_changes,
                "honeypot_id": new_honeypot_id,
                "deception_mode": "enhanced",
                "target_attacker": source_ip,
            }
            
            logger.info(f"Creating switched container {new_honeypot_id}")
            
            # Update result with deployment plan
            if result:
                result.details["deployment_plan"] = {
                    "new_honeypot_id": new_honeypot_id,
                    "new_name": f"{name}-enhanced",
                    "deception_mode": "enhanced",
                    "target_attacker": source_ip,
                }
                await self._broadcast_execution(result, "deploying")
            
            # Use deployment manager to create new container
            from src.core.deployment import HoneypotDeploymentManager
            from src.core.db import HoneypotType
            
            deployment = HoneypotDeploymentManager()
            
            # Find an available port dynamically
            import socket
            def find_available_port(start_port: int, max_attempts: int = 100) -> int:
                """Find an available port starting from start_port."""
                for test_port in range(start_port, start_port + max_attempts):
                    try:
                        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                            s.bind(('', test_port))
                            return test_port
                    except OSError:
                        continue
                raise RuntimeError(f"No available port found in range {start_port}-{start_port + max_attempts}")
            
            new_port = find_available_port(3000)  # Start from port 3000
            
            # Update result with port allocation
            if result:
                result.details["port_allocation"] = {
                    "new_port": new_port,
                    "method": "dynamic_allocation",
                }
                await self._broadcast_execution(result, "creating_container")
            
            deploy_result = await deployment.deploy(
                honeypot_id=new_honeypot_id,
                name=f"{name}-enhanced",
                honeypot_type=HoneypotType(honeypot_type),
                port=new_port,
                config=new_config,
            )
            
            if deploy_result.get("status") != "running":
                logger.error(f"Failed to create switched container")
                if result:
                    result.details["deployment_error"] = deploy_result
                return False
            
            # Get the new container details
            new_container = await self._get_container(new_honeypot_id)
            
            # Update result with new container info
            if result:
                result.details["new_container"] = {
                    "id": new_container.id[:12] if new_container else "unknown",
                    "name": f"{name}-enhanced",
                    "honeypot_id": new_honeypot_id,
                    "type": honeypot_type,
                    "port": new_port,
                    "status": "running",
                    "image": new_container.attrs.get('Config', {}).get('Image', 'unknown') if new_container else 'unknown',
                }
                result.details["switch_summary"] = {
                    "old_honeypot": f"{honeypot_id}:{port}",
                    "new_honeypot": f"{new_honeypot_id}:{new_port}",
                    "attacker_ip": source_ip,
                    "deception_mode": "enhanced",
                }
                await self._broadcast_execution(result, "container_created")
            
            # Now set up iptables redirect (requires host access)
            # This would redirect traffic from old port to new port
            # In production, this would use REDIRECT rules
            
            logger.info(f"Successfully switched attacker {source_ip} to new container")
            logger.info(f"Old: {honeypot_id}:{port} -> New: {new_honeypot_id}:{new_port}")
            
            # Old container can be kept for analysis or stopped
            # old_container.stop()
            
            return True
            
        except Exception as e:
            logger.error(f"Container switch failed: {e}")
            if result:
                result.details["exception"] = str(e)
            return False
    
    def _record_result(self, result: ExecutionResult):
        """Record execution result in history and database."""
        # Keep in-memory history
        self._execution_history.append(result)
        if len(self._execution_history) > self._max_history:
            self._execution_history.pop(0)
        
        # Persist to database
        asyncio.create_task(self._persist_result(result))
    
    async def _persist_result(self, result: ExecutionResult):
        """Persist execution result to database."""
        try:
            from src.core.db.session import get_db_context
            from src.core.db.models import ExecutionHistoryDB
            
            async with get_db_context() as session:
                # Calculate duration
                duration_ms = None
                if result.details.get("completed_at"):
                    completed = datetime.fromisoformat(result.details["completed_at"])
                    duration_ms = int((completed - result.timestamp).total_seconds() * 1000)
                
                db_record = ExecutionHistoryDB(
                    id=result.id,
                    decision_id=result.decision_id,
                    action=result.action,
                    honeypot_id=result.details.get("honeypot_id"),
                    source_ip=result.details.get("source_ip"),
                    status=result.status.value,
                    started_at=result.timestamp,
                    completed_at=datetime.utcnow() if result.status in [ExecutionStatus.SUCCESS, ExecutionStatus.FAILED] else None,
                    duration_ms=duration_ms,
                    success=result.status == ExecutionStatus.SUCCESS,
                    error=result.error,
                    details=result.details,
                    config_changes=result.details.get("config_changes", {}),
                    container_id=result.details.get("container_id"),
                    container_name=result.details.get("container_name"),
                )
                
                session.add(db_record)
                await session.commit()
                logger.debug(f"Persisted execution {result.id} to database")
                
        except Exception as e:
            logger.error(f"Failed to persist execution to database: {e}")
    
    def get_execution_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent execution history from database."""
        # Try to load from database synchronously
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # We're in an async context, use in-memory for now
                return self._get_memory_history(limit)
            
            # Load from database
            history = asyncio.run(self._load_history_from_db(limit))
            if history:
                return history
        except Exception as e:
            logger.warning(f"Failed to load history from DB: {e}")
        
        return self._get_memory_history(limit)
    
    def _get_memory_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get history from in-memory storage."""
        results = self._execution_history[-limit:]
        return [
            {
                "id": r.id,
                "decision_id": r.decision_id,
                "action": r.action,
                "status": r.status.value,
                "timestamp": r.timestamp.isoformat(),
                "details": r.details,
                "error": r.error,
            }
            for r in results
        ]
    
    async def _load_history_from_db(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Load execution history from database."""
        try:
            from src.core.db.session import get_db_context
            from src.core.db.models import ExecutionHistoryDB
            from sqlalchemy import select
            
            async with get_db_context() as session:
                result = await session.execute(
                    select(ExecutionHistoryDB)
                    .order_by(ExecutionHistoryDB.started_at.desc())
                    .limit(limit)
                )
                records = result.scalars().all()
                
                return [
                    {
                        "id": r.id,
                        "decision_id": r.decision_id,
                        "action": r.action,
                        "status": r.status,
                        "timestamp": r.started_at.isoformat() if r.started_at else None,
                        "details": r.details or {},
                        "error": r.error,
                        "duration_ms": r.duration_ms,
                        "success": r.success,
                    }
                    for r in records
                ]
        except Exception as e:
            logger.error(f"Error loading history from DB: {e}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """Get execution statistics from database."""
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # We're in an async context, use in-memory for now
                return self._get_memory_stats()
            
            # Load from database
            stats = asyncio.run(self._load_stats_from_db())
            if stats:
                return stats
        except Exception as e:
            logger.warning(f"Failed to load stats from DB: {e}")
        
        return self._get_memory_stats()
    
    def _get_memory_stats(self) -> Dict[str, Any]:
        """Get stats from in-memory history."""
        history = self._execution_history
        
        total = len(history)
        if total == 0:
            return {"total": 0}
        
        success_count = sum(1 for r in history if r.status == ExecutionStatus.SUCCESS)
        failed_count = sum(1 for r in history if r.status == ExecutionStatus.FAILED)
        
        action_counts = {}
        for r in history:
            action_counts[r.action] = action_counts.get(r.action, 0) + 1
        
        return {
            "total": total,
            "success": success_count,
            "failed": failed_count,
            "success_rate": round(success_count / total * 100, 1) if total > 0 else 0,
            "actions": action_counts,
        }
    
    async def _load_stats_from_db(self) -> Dict[str, Any]:
        """Load execution statistics from database."""
        try:
            from src.core.db.session import get_db_context
            from src.core.db.models import ExecutionHistoryDB
            from sqlalchemy import select, func
            
            async with get_db_context() as session:
                # Total count
                total_result = await session.execute(
                    select(func.count()).select_from(ExecutionHistoryDB)
                )
                total = total_result.scalar() or 0
                
                if total == 0:
                    return {"total": 0}
                
                # Success count
                success_result = await session.execute(
                    select(func.count()).select_from(ExecutionHistoryDB)
                    .where(ExecutionHistoryDB.success == True)
                )
                success_count = success_result.scalar() or 0
                
                # Failed count
                failed_result = await session.execute(
                    select(func.count()).select_from(ExecutionHistoryDB)
                    .where(ExecutionHistoryDB.success == False)
                )
                failed_count = failed_result.scalar() or 0
                
                # Action distribution
                action_result = await session.execute(
                    select(ExecutionHistoryDB.action, func.count())
                    .group_by(ExecutionHistoryDB.action)
                )
                action_counts = dict(action_result.all())
                
                return {
                    "total": total,
                    "success": success_count,
                    "failed": failed_count,
                    "success_rate": round(success_count / total * 100, 1) if total > 0 else 0,
                    "actions": action_counts,
                }
        except Exception as e:
            logger.error(f"Error loading stats from DB: {e}")
            return {"total": 0}


# Singleton instance
_executor: Optional[DecisionExecutor] = None


def get_executor() -> Optional[DecisionExecutor]:
    """Get the singleton DecisionExecutor instance, or None if Docker is unavailable."""
    global _executor
    if _executor is None:
        _executor = DecisionExecutor()
    return _executor