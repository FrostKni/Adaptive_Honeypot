# Fixes Applied - Connection & Delete Issues

## 🐛 Issues Fixed

### 1. ❌ DELETE Honeypot Returns 404
**Problem**: 
```
INFO: 172.25.0.1:55396 - "DELETE /honeypots/piyush_1773284143 HTTP/1.1" 404 Not Found
```

**Root Cause**: 
- Orchestrator stores active honeypots in memory (`active_honeypots` dict)
- When orchestrator restarts, this dict is empty
- Old code checked if honeypot exists in dict before deleting
- Containers were still running but not in the dict

**Fix Applied**:
```python
# OLD CODE (BROKEN)
async def remove_honeypot(self, honeypot_id: str) -> bool:
    if honeypot_id not in self.active_honeypots:  # ❌ Fails after restart
        return False
    success = self.deployment.stop_honeypot(honeypot_id)
    ...

# NEW CODE (FIXED)
async def remove_honeypot(self, honeypot_id: str) -> bool:
    success = self.deployment.stop_honeypot(honeypot_id)  # ✅ Delete directly
    if success:
        if honeypot_id in self.active_honeypots:
            del self.active_honeypots[honeypot_id]
    ...
```

**Result**: ✅ Can now delete honeypots even after orchestrator restart

---

### 2. ❌ SSH Connection Reset
**Problem**:
```bash
ssh -p 2223 root@127.0.0.1
kex_exchange_identification: read: Connection reset by peer
Connection reset by 127.0.0.1 port 2223
```

**Possible Causes**:
1. Cowrie container crashed
2. Cowrie service failed to start
3. Container out of memory/resources
4. Port mapping issue
5. Network configuration problem

**Diagnostic Tools Added**:

1. **Container logs endpoint**:
```bash
curl http://localhost:8000/honeypots/piyush_1773284143/container-logs
```

2. **Status script**:
```bash
sudo ./status.sh
```
Shows:
- Container status (running/stopped/crashed)
- Port mappings
- SSH connectivity test
- Recent error logs

3. **Check script**:
```bash
sudo ./check_honeypots.sh
```
Shows:
- All honeypot containers
- Full logs for each
- Network port status

4. **Fix script**:
```bash
sudo ./fix_system.sh
```
Automatically:
- Restarts orchestrator
- Finds crashed containers
- Restarts them
- Shows error logs

**How to Diagnose**:
```bash
# Step 1: Check overall status
sudo ./status.sh

# Step 2: If container shows as crashed/stopped
sudo ./fix_system.sh

# Step 3: Check specific container logs
sudo docker logs honeypot_piyush_1773284143

# Step 4: If still broken, remove and redeploy
curl -X DELETE http://localhost:8000/honeypots/piyush_1773284143
curl -X POST http://localhost:8000/honeypots/deploy \
  -H "Content-Type: application/json" \
  -d '{"name": "ssh-new", "port": 2223}'
```

---

## 📝 Code Changes Summary

### File: `core/orchestrator.py`
- ✅ Fixed `remove_honeypot()` to delete containers directly without checking in-memory dict

### File: `core/deployment.py`
- ✅ Added `get_container_logs()` method for debugging
- ✅ Modified `list_honeypots()` to include stopped containers (`all=True`)

### File: `api/main.py`
- ✅ Added `/honeypots/{id}/container-logs` endpoint
- ✅ Fixed WebSocket disconnection handling
- ✅ Added `/events/recent` endpoint for attack events

### File: `dashboard/index.html`
- ✅ Added `loadRecentEvents()` function
- ✅ Auto-refresh events every 5 seconds

---

## 🚀 How to Apply Fixes

```bash
# Apply all fixes
sudo ./fix_system.sh

# Or manually restart orchestrator
sudo ./restart_orchestrator.sh
```

---

## 🧪 Testing

### Test 1: Delete Honeypot
```bash
# Should work now even after restart
curl -X DELETE http://localhost:8000/honeypots/piyush_1773284143
```

### Test 2: Check Container Status
```bash
sudo ./status.sh
```

### Test 3: SSH Connection
```bash
# Port 2222 works
ssh -p 2222 root@127.0.0.1

# If 2223 doesn't work, check logs
sudo docker logs honeypot_piyush_1773284143
```

---

## 📊 New Diagnostic Commands

| Command | Purpose |
|---------|---------|
| `sudo ./status.sh` | Complete system status with health checks |
| `sudo ./check_honeypots.sh` | Detailed container logs |
| `sudo ./fix_system.sh` | Auto-fix crashed containers |
| `curl localhost:8000/honeypots/{id}/container-logs` | Get logs via API |
| `curl localhost:8000/events/recent` | Recent attack events |

---

## 🎯 Why Port 2222 Works But 2223 Doesn't

**Port 2222 (Working)**:
- ✅ Container running
- ✅ Cowrie started successfully
- ✅ Port mapped correctly
- ✅ No resource issues

**Port 2223 (Not Working)**:
- ❌ Container may be crashed
- ❌ Cowrie may have failed to start
- ❌ Check with: `sudo docker logs honeypot_piyush_1773284143`

**Quick Fix**:
```bash
sudo docker restart honeypot_piyush_1773284143
# Wait 10 seconds for Cowrie to start
ssh -p 2223 root@127.0.0.1
```

---

## 📚 Documentation Created

1. `TROUBLESHOOTING.md` - Detailed troubleshooting guide
2. `status.sh` - System status checker
3. `check_honeypots.sh` - Container diagnostics
4. `fix_system.sh` - Auto-fix script
5. `FIXES_APPLIED.md` - This document
