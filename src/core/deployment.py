"""
Deployment Manager - Docker container orchestration for honeypots.
"""

import asyncio
import logging
import os
import tempfile
from typing import Optional, Dict, Any, List
from datetime import datetime

import docker
from docker.errors import DockerException, APIError, NotFound

from src.core.config import settings
from src.core.db import HoneypotStatus, HoneypotType
from src.core.exceptions import DeploymentError

logger = logging.getLogger(__name__)


class HoneypotDeploymentManager:
    """
    Manages Docker container lifecycle for honeypots.

    Supports:
    - SSH honeypots (Cowrie-based)
    - HTTP honeypots (Custom Python)
    - FTP honeypots (PyFTPDlib)
    - Telnet honeypots (Custom)
    """

    # Container labels for tracking
    LABEL_PREFIX = "honeypot."
    LABEL_ID = "honeypot.id"
    LABEL_NAME = "honeypot.name"
    LABEL_TYPE = "honeypot.type"
    LABEL_PORT = "honeypot.port"

    # Image names
    IMAGES = {
        HoneypotType.SSH: "cowrie/cowrie:latest",
        HoneypotType.HTTP: "nginx:alpine",  # We'll customize this
        HoneypotType.FTP: "stilliard/pure-ftpd:latest",
        HoneypotType.TELNET: "cowrie/cowrie:latest",  # Cowrie supports telnet too
    }

    # Default ports (host side)
    DEFAULT_PORTS = {
        HoneypotType.SSH: 2222,
        HoneypotType.HTTP: 8080,
        HoneypotType.FTP: 2121,
        HoneypotType.TELNET: 2323,
    }

    def __init__(self):
        """Initialize Docker client."""
        try:
            self.client = docker.from_env()
            self.api_client = docker.APIClient()
            self._network_name = "honeypot-network"
            self._ensure_network()
        except DockerException as e:
            logger.error(f"Failed to connect to Docker: {e}")
            raise DeploymentError(f"Docker not available: {e}")

    def _ensure_network(self):
        """Ensure the honeypot network exists."""
        try:
            self.client.networks.get(self._network_name)
        except NotFound:
            logger.info(f"Creating network: {self._network_name}")
            self.client.networks.create(
                self._network_name,
                driver="bridge",
                check_duplicate=True,
            )

    async def deploy(
        self,
        honeypot_id: str,
        name: str,
        honeypot_type: HoneypotType,
        port: int,
        config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Deploy a new honeypot container.

        Args:
            honeypot_id: Unique identifier for the honeypot
            name: Human-readable name
            honeypot_type: Type of honeypot (SSH, HTTP, FTP, Telnet)
            port: Host port to expose
            config: Additional configuration options

        Returns:
            Dict with container_id, status, and deployment info
        """
        config = config or {}

        try:
            # Pull image if needed
            image = self.IMAGES.get(honeypot_type)
            if not image:
                raise DeploymentError(f"Unknown honeypot type: {honeypot_type}")

            logger.info(f"Pulling image: {image}")
            await asyncio.to_thread(self.client.images.pull, image)

            # Build container configuration
            container_config = self._build_container_config(
                honeypot_id=honeypot_id,
                name=name,
                honeypot_type=honeypot_type,
                port=port,
                config=config,
            )

            # Create and start container
            logger.info(f"Creating container for {name} ({honeypot_type.value})")
            container = await asyncio.to_thread(
                self.client.containers.create, image=image, **container_config
            )

            # Connect to network
            network = self.client.networks.get(self._network_name)
            network.connect(container)

            # Start container
            container.start()

            # Refresh to get current state
            container.reload()

            logger.info(f"Deployed {name} as {container.id[:12]}")

            return {
                "container_id": container.id,
                "status": HoneypotStatus.RUNNING,
                "port": port,
                "image": image,
                "started_at": datetime.utcnow(),
            }

        except (DockerException, APIError) as e:
            logger.error(f"Failed to deploy {name}: {e}")
            raise DeploymentError(f"Deployment failed: {e}")

    def _build_container_config(
        self,
        honeypot_id: str,
        name: str,
        honeypot_type: HoneypotType,
        port: int,
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Build Docker container configuration."""

        # Base configuration
        base_config = {
            "name": f"honeypot-{honeypot_id}",
            "detach": True,
            "labels": {
                self.LABEL_ID: honeypot_id,
                self.LABEL_NAME: name,
                self.LABEL_TYPE: honeypot_type.value,
                self.LABEL_PORT: str(port),
            },
            "environment": self._get_environment(honeypot_type, config),
            "ports": self._get_port_mappings(honeypot_type, port),
            "network": self._network_name,
            "restart_policy": {"Name": "unless-stopped"},
            "mem_limit": config.get("memory_limit", "256m"),
            "cpu_quota": config.get("cpu_quota", 50000),  # 50% CPU
        }

        # Type-specific configuration
        if honeypot_type == HoneypotType.SSH:
            base_config.update(self._get_ssh_config(config))
        elif honeypot_type == HoneypotType.HTTP:
            base_config.update(self._get_http_config(config))
        elif honeypot_type == HoneypotType.FTP:
            base_config.update(self._get_ftp_config(config))
        elif honeypot_type == HoneypotType.TELNET:
            base_config.update(self._get_telnet_config(config))

        return base_config

    def _get_environment(
        self, honeypot_type: HoneypotType, config: Dict
    ) -> Dict[str, str]:
        """Get environment variables for the container."""
        env = {
            "HONEYPOT_ID": config.get("honeypot_id", ""),
            "HONEYPOT_NAME": config.get("name", ""),
            "LOG_LEVEL": config.get("log_level", "INFO"),
        }

        if honeypot_type == HoneypotType.SSH:
            env.update(
                {
                    "COWRIE_SSH_PORT": "2222",
                    "COWRIE_TELNET_PORT": "2323",
                }
            )

        return env

    def _get_port_mappings(
        self, honeypot_type: HoneypotType, host_port: int
    ) -> Dict[str, Any]:
        """Get port mappings for the container."""
        if honeypot_type == HoneypotType.SSH:
            return {"2222/tcp": host_port}
        elif honeypot_type == HoneypotType.HTTP:
            return {"80/tcp": host_port}
        elif honeypot_type == HoneypotType.FTP:
            return {"21/tcp": host_port}
        elif honeypot_type == HoneypotType.TELNET:
            return {"2323/tcp": host_port}
        return {}

    def _get_ssh_config(self, config: Dict) -> Dict[str, Any]:
        """SSH honeypot specific configuration."""
        return {
            "volumes": {
                f"honeypot-{config.get('honeypot_id', 'default')}-data": {
                    "bind": "/cowrie/data",
                    "mode": "rw",
                },
                f"honeypot-{config.get('honeypot_id', 'default')}-logs": {
                    "bind": "/cowrie/var/log/cowrie",
                    "mode": "rw",
                },
            },
        }

    def _get_http_config(self, config: Dict) -> Dict[str, Any]:
        """HTTP honeypot specific configuration."""
        return {
            "volumes": {
                f"honeypot-{config.get('honeypot_id', 'default')}-logs": {
                    "bind": "/var/log/nginx",
                    "mode": "rw",
                },
            },
        }

    def _get_ftp_config(self, config: Dict) -> Dict[str, Any]:
        """FTP honeypot specific configuration."""
        return {
            "environment": {
                "PUBLICHOST": config.get("public_host", "0.0.0.0"),
            },
        }

    def _get_telnet_config(self, config: Dict) -> Dict[str, Any]:
        """Telnet honeypot specific configuration."""
        return self._get_ssh_config(config)  # Cowrie handles both

    async def stop(self, honeypot_id: str) -> bool:
        """
        Stop a running honeypot container.

        Args:
            honeypot_id: The honeypot ID to stop

        Returns:
            True if stopped successfully
        """
        try:
            container = await self._get_container(honeypot_id)
            if container:
                container.stop()
                logger.info(f"Stopped container for {honeypot_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to stop {honeypot_id}: {e}")
            return False

    async def start(self, honeypot_id: str) -> bool:
        """
        Start a stopped honeypot container.

        Args:
            honeypot_id: The honeypot ID to start

        Returns:
            True if started successfully
        """
        try:
            container = await self._get_container(honeypot_id)
            if container:
                container.start()
                logger.info(f"Started container for {honeypot_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to start {honeypot_id}: {e}")
            return False

    async def remove(self, honeypot_id: str) -> bool:
        """
        Remove a honeypot container completely.

        Args:
            honeypot_id: The honeypot ID to remove

        Returns:
            True if removed successfully
        """
        try:
            container = await self._get_container(honeypot_id)
            if container:
                container.stop()
                container.remove()
                logger.info(f"Removed container for {honeypot_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to remove {honeypot_id}: {e}")
            return False

    async def restart(self, honeypot_id: str) -> bool:
        """
        Restart a honeypot container.

        Args:
            honeypot_id: The honeypot ID to restart

        Returns:
            True if restarted successfully
        """
        try:
            container = await self._get_container(honeypot_id)
            if container:
                container.restart()
                logger.info(f"Restarted container for {honeypot_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to restart {honeypot_id}: {e}")
            return False

    async def get_status(self, honeypot_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the current status of a honeypot container.

        Args:
            honeypot_id: The honeypot ID to check

        Returns:
            Dict with status info or None if not found
        """
        try:
            container = await self._get_container(honeypot_id)
            if container:
                container.reload()
                stats = container.stats(stream=False)

                return {
                    "status": self._map_docker_status(container.status),
                    "container_id": container.id,
                    "image": container.image.tags[0]
                    if container.image.tags
                    else "unknown",
                    "started_at": container.attrs.get("State", {}).get("StartedAt"),
                    "cpu_percent": self._calculate_cpu_percent(stats),
                    "memory_usage": stats.get("memory_stats", {}).get("usage", 0),
                    "network_rx": self._get_network_stats(stats, "rx_bytes"),
                    "network_tx": self._get_network_stats(stats, "tx_bytes"),
                }
            return None
        except Exception as e:
            logger.error(f"Failed to get status for {honeypot_id}: {e}")
            return None

    async def get_logs(self, honeypot_id: str, lines: int = 100) -> List[str]:
        """
        Get logs from a honeypot container.

        Args:
            honeypot_id: The honeypot ID
            lines: Number of log lines to retrieve

        Returns:
            List of log lines
        """
        try:
            container = await self._get_container(honeypot_id)
            if container:
                logs = container.logs(tail=lines).decode("utf-8")
                return logs.split("\n")
            return []
        except Exception as e:
            logger.error(f"Failed to get logs for {honeypot_id}: {e}")
            return []

    async def list_containers(self) -> List[Dict[str, Any]]:
        """
        List all honeypot containers.

        Returns:
            List of container info dicts
        """
        try:
            containers = self.client.containers.list(
                all=True, filters={"label": self.LABEL_ID}
            )

            result = []
            for container in containers:
                labels = container.labels
                result.append(
                    {
                        "id": labels.get(self.LABEL_ID),
                        "name": labels.get(self.LABEL_NAME),
                        "type": labels.get(self.LABEL_TYPE),
                        "port": int(labels.get(self.LABEL_PORT, 0)),
                        "container_id": container.id,
                        "status": self._map_docker_status(container.status),
                    }
                )

            return result

        except Exception as e:
            logger.error(f"Failed to list containers: {e}")
            return []

    async def _get_container(self, honeypot_id: str):
        """Get a container by honeypot ID."""
        try:
            containers = self.client.containers.list(
                all=True, filters={"label": f"{self.LABEL_ID}={honeypot_id}"}
            )
            return containers[0] if containers else None
        except Exception:
            return None

    def _map_docker_status(self, docker_status: str) -> HoneypotStatus:
        """Map Docker status to HoneypotStatus."""
        mapping = {
            "running": HoneypotStatus.RUNNING,
            "exited": HoneypotStatus.STOPPED,
            "paused": HoneypotStatus.STOPPED,
            "restarting": HoneypotStatus.STARTING,
            "created": HoneypotStatus.STARTING,
        }
        return mapping.get(docker_status.lower(), HoneypotStatus.ERROR)

    def _calculate_cpu_percent(self, stats: Dict) -> float:
        """Calculate CPU percentage from stats."""
        try:
            cpu_stats = stats.get("cpu_stats", {})
            precpu_stats = stats.get("precpu_stats", {})

            cpu_delta = cpu_stats.get("cpu_usage", {}).get(
                "total_usage", 0
            ) - precpu_stats.get("cpu_usage", {}).get("total_usage", 0)

            system_delta = cpu_stats.get("system_cpu_usage", 0) - precpu_stats.get(
                "system_cpu_usage", 0
            )

            if system_delta > 0 and cpu_delta > 0:
                return (cpu_delta / system_delta) * 100.0
        except Exception:
            pass
        return 0.0

    def _get_network_stats(self, stats: Dict, metric: str) -> int:
        """Get network statistics."""
        try:
            networks = stats.get("networks", {})
            return sum(net.get(metric, 0) for net in networks.values())
        except Exception:
            return 0


# Global deployment manager instance
_deployment_manager: Optional[HoneypotDeploymentManager] = None


def get_deployment_manager() -> Optional[HoneypotDeploymentManager]:
    """Get the global deployment manager instance. Returns None if Docker is unavailable."""
    global _deployment_manager
    if _deployment_manager is None:
        try:
            _deployment_manager = HoneypotDeploymentManager()
        except DeploymentError as e:
            logger.warning(
                f"Docker unavailable, deployment manager not initialized: {e}"
            )
            return None
    return _deployment_manager
