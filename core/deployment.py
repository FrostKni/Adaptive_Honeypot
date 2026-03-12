import docker
from docker.models.containers import Container
from docker.errors import DockerException, NotFound
from typing import Dict, Optional, List
import logging
from datetime import datetime
from core.models import HoneypotConfig, HoneypotStatus, ContainerHealth
import time

logger = logging.getLogger(__name__)

class DeploymentManager:
    def __init__(self, network_name: str = "honeypot_net"):
        try:
            self.client = docker.from_env()
            self.network_name = network_name
            self._ensure_network()
        except DockerException as e:
            logger.error(f"Docker connection failed: {e}")
            raise
    
    def _ensure_network(self):
        try:
            # Try to get existing network
            network = self.client.networks.get(self.network_name)
            logger.info(f"Using existing network: {self.network_name}")
        except NotFound:
            # Network doesn't exist, try to create it
            try:
                self.client.networks.create(
                    self.network_name,
                    driver="bridge",
                    check_duplicate=True
                )
                logger.info(f"Created network: {self.network_name}")
            except DockerException as e:
                # If creation fails due to subnet overlap, try without custom subnet
                if "overlaps" in str(e).lower():
                    logger.warning(f"Subnet overlap detected, creating network without custom subnet")
                    try:
                        self.client.networks.create(
                            self.network_name,
                            driver="bridge"
                        )
                        logger.info(f"Created network: {self.network_name} (auto subnet)")
                    except DockerException as e2:
                        logger.error(f"Failed to create network: {e2}")
                        # Use default bridge network as fallback
                        self.network_name = "bridge"
                        logger.warning(f"Falling back to default bridge network")
                else:
                    raise
    
    def deploy_honeypot(self, config: HoneypotConfig, honeypot_id: str) -> Optional[str]:
        try:
            # Get absolute path for logs from host perspective
            import os
            # If running in container, use /app/logs, otherwise use current directory
            if os.path.exists('/app'):
                log_path = f"/app/logs/{honeypot_id}"
            else:
                log_path = os.path.abspath(f"./logs/{honeypot_id}")
            
            os.makedirs(log_path, exist_ok=True)
            logger.info(f"Using log path: {log_path}")
            
            # Build Cowrie container
            container = self.client.containers.run(
                "cowrie/cowrie:latest",
                name=f"honeypot_{honeypot_id}",
                detach=True,
                network=self.network_name,
                ports={f'{config.port}/tcp': config.port},
                environment={
                    "COWRIE_HOSTNAME": config.hostname,
                    "COWRIE_SSH_ENABLED": "yes",
                    "COWRIE_TELNET_ENABLED": "no" if config.type == "ssh" else "yes",
                    "COWRIE_LOG_PATH": "/cowrie/var/log/cowrie"
                },
                volumes={
                    log_path: {"bind": "/cowrie/var/log/cowrie", "mode": "rw"}
                },
                restart_policy={"Name": "unless-stopped"},
                labels={
                    "honeypot.id": honeypot_id,
                    "honeypot.type": config.type,
                    "honeypot.interaction": config.interaction_level
                }
            )
            
            logger.info(f"Deployed honeypot {honeypot_id}: {container.id[:12]}")
            return container.id
            
        except DockerException as e:
            logger.error(f"Deployment failed for {honeypot_id}: {e}")
            return None
    
    def stop_honeypot(self, honeypot_id: str) -> bool:
        try:
            container = self.client.containers.get(f"honeypot_{honeypot_id}")
            container.stop(timeout=10)
            container.remove()
            logger.info(f"Stopped honeypot {honeypot_id}")
            return True
        except NotFound:
            logger.warning(f"Container not found: {honeypot_id}")
            return False
        except DockerException as e:
            logger.error(f"Failed to stop {honeypot_id}: {e}")
            return False
    
    def restart_honeypot(self, honeypot_id: str) -> bool:
        try:
            container = self.client.containers.get(f"honeypot_{honeypot_id}")
            container.restart(timeout=10)
            logger.info(f"Restarted honeypot {honeypot_id}")
            return True
        except Exception as e:
            logger.error(f"Restart failed for {honeypot_id}: {e}")
            return False
    
    def check_health(self, honeypot_id: str) -> Optional[ContainerHealth]:
        try:
            container = self.client.containers.get(f"honeypot_{honeypot_id}")
            stats = container.stats(stream=False)
            
            # Calculate CPU percentage
            cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - \
                       stats['precpu_stats']['cpu_usage']['total_usage']
            system_delta = stats['cpu_stats']['system_cpu_usage'] - \
                          stats['precpu_stats']['system_cpu_usage']
            cpu_percent = (cpu_delta / system_delta) * 100.0 if system_delta > 0 else 0.0
            
            # Memory usage
            memory_mb = stats['memory_stats']['usage'] / (1024 * 1024)
            
            # Uptime
            started_at = datetime.fromisoformat(container.attrs['State']['StartedAt'].replace('Z', '+00:00'))
            uptime = (datetime.now(started_at.tzinfo) - started_at).total_seconds()
            
            status_map = {
                'running': HoneypotStatus.RUNNING,
                'exited': HoneypotStatus.STOPPED,
                'dead': HoneypotStatus.ERROR
            }
            
            return ContainerHealth(
                container_id=container.id[:12],
                status=status_map.get(container.status, HoneypotStatus.ERROR),
                cpu_percent=round(cpu_percent, 2),
                memory_mb=round(memory_mb, 2),
                uptime_seconds=int(uptime),
                last_check=datetime.now()
            )
            
        except NotFound:
            return None
        except Exception as e:
            logger.error(f"Health check failed for {honeypot_id}: {e}")
            return None
    
    def list_honeypots(self) -> List[Dict]:
        containers = self.client.containers.list(
            filters={"label": "honeypot.id"},
            all=True  # Include stopped containers
        )
        
        return [{
            "id": c.labels.get("honeypot.id"),
            "container_id": c.id[:12],
            "status": c.status,
            "type": c.labels.get("honeypot.type"),
            "interaction": c.labels.get("honeypot.interaction")
        } for c in containers]
    
    def migrate_session(self, old_id: str, new_id: str, session_data: Dict) -> bool:
        """Preserve session during honeypot migration"""
        try:
            # Export session from old container
            old_container = self.client.containers.get(f"honeypot_{old_id}")
            
            # Copy session files
            session_path = f"/cowrie/var/lib/cowrie/tty/{session_data['session_id']}"
            archive, _ = old_container.get_archive(session_path)
            
            # Import to new container
            new_container = self.client.containers.get(f"honeypot_{new_id}")
            new_container.put_archive("/cowrie/var/lib/cowrie/tty/", archive)
            
            logger.info(f"Migrated session from {old_id} to {new_id}")
            return True
            
        except Exception as e:
            logger.error(f"Session migration failed: {e}")
            return False
    
    def get_container_logs(self, honeypot_id: str, tail: int = 50) -> str:
        """Get container logs for debugging"""
        try:
            container = self.client.containers.get(f"honeypot_{honeypot_id}")
            logs = container.logs(tail=tail, timestamps=True).decode('utf-8')
            return logs
        except NotFound:
            return f"Container not found: {honeypot_id}"
        except Exception as e:
            return f"Error getting logs: {e}"
