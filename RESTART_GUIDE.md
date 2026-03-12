# 🔄 Restart Adaptive Orchestrator Only

## Quick Commands

### Option 1: Using the restart script (Easiest)
```bash
./restart_orchestrator.sh
```

### Option 2: Using docker-compose (Recommended)
```bash
# Rebuild and restart only orchestrator (keeps other services running)
docker-compose up -d --build --no-deps orchestrator

# Check status
docker-compose ps orchestrator

# View logs
docker-compose logs -f orchestrator
```

### Option 3: Using docker commands directly
```bash
# Stop and remove old container
docker stop adaptive_orchestrator
docker rm adaptive_orchestrator

# Rebuild image
docker-compose build orchestrator

# Start new container
docker-compose up -d orchestrator
```

### Option 4: Quick restart without rebuild
```bash
# If you only need to restart (no code changes)
docker-compose restart orchestrator
```

## After Restart

### Check if it's running
```bash
docker-compose ps
# or
docker ps | grep adaptive_orchestrator
```

### View logs
```bash
docker-compose logs -f orchestrator
# or
docker logs -f adaptive_orchestrator
```

### Test API
```bash
curl http://localhost:8000/status
```

## Troubleshooting

### If container won't start
```bash
# Check logs for errors
docker-compose logs orchestrator

# Check if port is in use
netstat -tulpn | grep 8000

# Force recreate
docker-compose up -d --force-recreate orchestrator
```

### If you see "permission denied"
```bash
# Fix Docker socket permissions
sudo chmod 666 /var/run/docker.sock

# Or add user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

### If dependencies are outdated
```bash
# Update requirements in container
docker-compose exec orchestrator pip install -r requirements.txt --upgrade
```

## Notes

- The restart script preserves other running containers (Redis, Dashboard, Honeypots)
- Only the orchestrator service is rebuilt and restarted
- All data in volumes is preserved
- Active honeypots continue running during orchestrator restart
