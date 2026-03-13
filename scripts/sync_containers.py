#!/usr/bin/env python3
"""
Sync Docker containers with the database.

This script:
1. Finds all honeypot containers
2. Adds missing containers to the database
3. Removes orphaned database records
4. Updates container status
"""
import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import docker
from docker.errors import DockerException

from src.core.db import get_db, init_db, close_db
from src.core.db.models import Honeypot, HoneypotStatus, HoneypotType
from src.core.db.repositories import HoneypotRepository


LABEL_ID = "honeypot.id"
LABEL_NAME = "honeypot.name"
LABEL_TYPE = "honeypot.type"
LABEL_PORT = "honeypot.port"


async def sync_containers():
    """Sync containers with database."""
    print("Starting container sync...")
    
    # Initialize database
    await init_db()
    
    # Connect to Docker
    try:
        client = docker.from_env()
    except DockerException as e:
        print(f"ERROR: Failed to connect to Docker: {e}")
        return
    
    # Get all honeypot containers
    containers = client.containers.list(all=True, filters={"label": LABEL_ID})
    print(f"Found {len(containers)} honeypot containers")
    
    # Get all database honeypots
    async for session in get_db():
        repo = HoneypotRepository(session)
        db_honeypots = await repo.get_all(limit=1000)
        db_ids = {h.id: h for h in db_honeypots}
        
        print(f"Found {len(db_honeypots)} database records")
        
        # Track which IDs we've seen
        seen_ids = set()
        
        # Process containers
        for container in containers:
            labels = container.labels
            hp_id = labels.get(LABEL_ID)
            hp_name = labels.get(LABEL_NAME, "unknown")
            hp_type = labels.get(LABEL_TYPE, "ssh")
            hp_port = int(labels.get(LABEL_PORT, 2222))
            
            seen_ids.add(hp_id)
            
            # Check if in database
            if hp_id not in db_ids:
                print(f"Adding missing container to DB: {hp_name} ({hp_id})")
                
                # Determine status
                status = HoneypotStatus.RUNNING if container.status == "running" else HoneypotStatus.STOPPED
                
                # Create database record
                await repo.create(
                    id=hp_id,
                    name=hp_name,
                    type=HoneypotType(hp_type) if hp_type in ["ssh", "http", "ftp", "telnet"] else HoneypotType.SSH,
                    port=hp_port,
                    status=status,
                    container_id=container.id,
                    container_name=container.name,
                )
            else:
                # Update status
                hp = db_ids[hp_id]
                status = HoneypotStatus.RUNNING if container.status == "running" else HoneypotStatus.STOPPED
                
                if hp.status != status or hp.container_id != container.id:
                    print(f"Updating {hp_name}: status={status.value}, container_id={container.id[:12]}")
                    await repo.update(hp_id, status=status, container_id=container.id)
        
        # Find orphaned database records
        for hp in db_honeypots:
            if hp.id not in seen_ids:
                print(f"Orphaned database record: {hp.name} ({hp.id})")
                # Option: delete or keep
                # await repo.delete(hp.id)
        
        await session.commit()
    
    await close_db()
    print("Sync complete!")


if __name__ == "__main__":
    asyncio.run(sync_containers())