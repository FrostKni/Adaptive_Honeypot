# Honeypot Troubleshooting Guide

## Issue 1: Cannot Delete Honeypot (404 Error)

**Problem**: Dashboard shows honeypot but delete returns 404

**Cause**: Orchestrator restarted and lost in-memory state, but containers still running

**Fix**: ✅ FIXED - Now deletes containers directly without checking in-memory dict

**Test**:
```bash
curl -X DELETE http://localhost:8000/honeypots/piyush_1773284143
```

---

## Issue 2: SSH Connection Reset

**Problem**: `Connection reset by peer` when connecting to honeypot

**Possible Causes**:
1. Container crashed or not fully started
2. Cowrie service failed to start
3. Port mapping issue
4. Container out of memory

**Diagnosis**:
```bash
# Check container status
sudo ./check_honeypots.sh

# Check specific container logs
sudo docker logs honeypot_piyush_1773284143

# Check if port is listening
sudo netstat -tlnp | grep 2223
```

**Common Fixes**:

### Fix 1: Restart crashed containers
```bash
sudo ./fix_system.sh
```

### Fix 2: Check container logs via API
```bash
curl http://localhost:8000/honeypots/piyush_1773284143/container-logs
```

### Fix 3: Manually restart container
```bash
sudo docker restart honeypot_piyush_1773284143
```

### Fix 4: Remove and redeploy
```bash
# Remove broken honeypot
curl -X DELETE http://localhost:8000/honeypots/piyush_1773284143

# Deploy new one
curl -X POST http://localhost:8000/honeypots/deploy \
  -H "Content-Type: application/json" \
  -d '{"name": "ssh-test", "port": 2223}'
```

---

## Issue 3: Port Already in Use

**Problem**: Cannot deploy honeypot on specific port

**Fix**:
```bash
# Find what's using the port
sudo netstat -tlnp | grep 2223

# Kill the process or use different port
curl -X POST http://localhost:8000/honeypots/deploy \
  -H "Content-Type: application/json" \
  -d '{"name": "ssh-test", "port": 2224}'
```

---

## Checking Honeypot Health

### Via API
```bash
# List all honeypots
curl http://localhost:8000/honeypots

# Check specific health
curl http://localhost:8000/honeypots/piyush_1773284143/health

# Get container logs
curl http://localhost:8000/honeypots/piyush_1773284143/container-logs
```

### Via Docker
```bash
# List containers
sudo docker ps -a --filter "label=honeypot.id"

# Check logs
sudo docker logs honeypot_piyush_1773284143

# Inspect container
sudo docker inspect honeypot_piyush_1773284143
```

---

## Working SSH Connection Example

Port 2222 works because:
1. Container is running
2. Cowrie service started successfully
3. Port mapping is correct
4. No resource issues

```bash
ssh -p 2222 root@127.0.0.1
# Password: any password works (it's a honeypot!)
```

---

## Quick Commands

```bash
# Fix everything
sudo ./fix_system.sh

# Check status
sudo ./check_honeypots.sh

# Restart orchestrator
sudo ./restart_orchestrator.sh

# View orchestrator logs
sudo docker logs -f orchestrator

# Remove all honeypots
for id in $(sudo docker ps -a --filter "label=honeypot.id" --format "{{.Names}}"); do
    sudo docker rm -f "$id"
done
```
