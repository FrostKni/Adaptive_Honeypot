# 🔧 Volume Path Fix - Complete Guide

## Problem
Docker was rejecting volume mounts with error:
```
"./logs/honeypot_id" includes invalid characters for a local volume name
```

## Root Cause
Docker requires **absolute paths** for volume mounts, not relative paths like `./logs/...`

## Solution Applied
Updated `core/deployment.py` to use absolute paths:
- When running in Docker container: `/app/logs/{honeypot_id}`
- When running on host: `os.path.abspath("./logs/{honeypot_id}")`

## How to Apply the Fix

### Method 1: Complete Fix Script (Recommended)
```bash
sudo ./complete_fix.sh
```

This script will:
1. Stop orchestrator
2. Remove old container
3. Remove old image
4. Clear Docker build cache
5. Rebuild with --no-cache
6. Start new container

### Method 2: Manual Steps
```bash
# Stop and remove
sudo docker-compose stop orchestrator
sudo docker-compose rm -f orchestrator

# Remove old image
sudo docker rmi adaptive_honeypot-orchestrator

# Clear cache
sudo docker builder prune -f

# Rebuild without cache
sudo docker-compose build --no-cache orchestrator

# Start
sudo docker-compose up -d orchestrator
```

### Method 3: Quick Rebuild (if cache is not an issue)
```bash
sudo docker-compose up -d --build --force-recreate orchestrator
```

## Verify the Fix

### 1. Check logs for correct path
```bash
docker-compose logs orchestrator | grep "log path"
```

Should see:
```
INFO: Using log path: /app/logs/honeypot_id
```

NOT:
```
ERROR: create ./logs/honeypot_id
```

### 2. Test deployment
```bash
curl -X POST http://localhost:8000/honeypots/deploy \
  -H 'Content-Type: application/json' \
  -d '{"name": "test", "port": 2222}'
```

Should return:
```json
{"success": true, "honeypot_id": "test_..."}
```

### 3. Check container was created
```bash
docker ps | grep honeypot_test
```

## Troubleshooting

### Issue: Still seeing "./logs/" error
**Cause**: Old code is cached in Docker image

**Solution**: Force rebuild without cache
```bash
sudo ./complete_fix.sh
```

### Issue: Permission denied
**Cause**: Need Docker permissions

**Solution**: Run with sudo or fix permissions
```bash
sudo chmod 666 /var/run/docker.sock
# OR
sudo usermod -aG docker $USER
newgrp docker
```

### Issue: Container starts but deployment still fails
**Cause**: Code not updated in container

**Solution**: Check what code is running
```bash
sudo docker exec adaptive_orchestrator cat /app/core/deployment.py | grep "log_path"
```

Should see:
```python
log_path = f"/app/logs/{honeypot_id}"
```

If not, rebuild with --no-cache.

## What Changed in the Code

### Before (Broken)
```python
def deploy_honeypot(self, config: HoneypotConfig, honeypot_id: str):
    volumes = {
        f"./logs/{honeypot_id}": {"bind": "/cowrie/var/log/cowrie", "mode": "rw"}
    }
```

### After (Fixed)
```python
def deploy_honeypot(self, config: HoneypotConfig, honeypot_id: str):
    import os
    if os.path.exists('/app'):
        log_path = f"/app/logs/{honeypot_id}"
    else:
        log_path = os.path.abspath(f"./logs/{honeypot_id}")
    
    os.makedirs(log_path, exist_ok=True)
    logger.info(f"Using log path: {log_path}")
    
    volumes = {
        log_path: {"bind": "/cowrie/var/log/cowrie", "mode": "rw"}
    }
```

## Why This Fix Works

1. **Detects environment**: Checks if running in container (`/app` exists)
2. **Uses correct path**: 
   - Container: `/app/logs/` (absolute path inside container)
   - Host: Full absolute path from `os.path.abspath()`
3. **Creates directory**: Ensures log directory exists before mounting
4. **Logs the path**: Makes debugging easier

## Expected Behavior After Fix

1. Deploy honeypot via API or dashboard
2. See log: `INFO: Using log path: /app/logs/honeypot_id`
3. See log: `INFO: Deployed honeypot honeypot_id: abc123`
4. Container appears in `docker ps`
5. Logs appear in `/app/logs/honeypot_id/` inside orchestrator container
6. Logs appear in `./logs/honeypot_id/` on host

## Quick Commands

```bash
# Apply fix
sudo ./complete_fix.sh

# Check status
docker-compose ps

# View logs
docker-compose logs -f orchestrator

# Test deployment
curl -X POST http://localhost:8000/honeypots/deploy \
  -H 'Content-Type: application/json' \
  -d '{"name": "test", "port": 2222}'

# List honeypots
curl http://localhost:8000/honeypots

# Check deployed containers
docker ps | grep honeypot
```

## Summary

✅ Code is fixed in `core/deployment.py`
✅ Uses absolute paths for Docker volumes
✅ Creates log directories automatically
✅ Works both in container and on host

**To apply: Run `sudo ./complete_fix.sh`**
