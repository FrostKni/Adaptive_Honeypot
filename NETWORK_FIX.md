# 🔧 Network Conflict Fix

## Error Explanation

**Error**: `Pool overlaps with other one on this address space`

This means the subnet `172.20.0.0/16` is already in use by another Docker network on your system.

## What Was Fixed

1. **Updated deployment.py**:
   - Now handles existing networks gracefully
   - Falls back to auto-assigned subnet if conflict occurs
   - Uses default bridge network as last resort

2. **Updated docker-compose.yml**:
   - Changed subnet from `172.20.0.0/16` to `172.25.0.0/16`
   - Reduces chance of conflicts

3. **Created fix_network.sh**:
   - Automated script to resolve conflicts
   - Safely removes old network
   - Restarts with new configuration

## Quick Fix

### Option 1: Use the Fix Script (Easiest)
```bash
./fix_network.sh
```

### Option 2: Manual Fix
```bash
# Stop all services
docker-compose down

# Remove old network (if exists)
docker network rm honeypot_net

# Restart with new configuration
docker-compose up -d --build orchestrator
```

### Option 3: Find and Remove Conflicting Network
```bash
# Find networks using 172.20.0.0/16
docker network ls -q | xargs docker network inspect | grep -B 5 "172.20.0.0/16"

# Remove the conflicting network (replace NETWORK_NAME)
docker network rm NETWORK_NAME

# Restart
docker-compose up -d orchestrator
```

## Verify Fix

```bash
# Check network was created
docker network ls | grep honeypot

# Check orchestrator is running
docker-compose ps orchestrator

# Check logs
docker-compose logs orchestrator
```

## Understanding the Fix

### Before (Caused Conflict)
```yaml
networks:
  honeypot_net:
    ipam:
      config:
        - subnet: 172.20.0.0/16  # ❌ Conflicted
```

### After (No Conflict)
```yaml
networks:
  honeypot_net:
    ipam:
      config:
        - subnet: 172.25.0.0/16  # ✅ Different subnet
```

### Code Fix (deployment.py)
```python
# Now handles conflicts gracefully:
try:
    # Try to use existing network
    network = self.client.networks.get(self.network_name)
except NotFound:
    try:
        # Try to create with custom subnet
        self.client.networks.create(...)
    except DockerException as e:
        if "overlaps" in str(e):
            # Create without custom subnet (auto-assign)
            self.client.networks.create(name, driver="bridge")
        else:
            # Fall back to default bridge
            self.network_name = "bridge"
```

## Common Scenarios

### Scenario 1: Docker Compose Network Exists
```bash
# The network was created by docker-compose
docker network inspect honeypot_net

# Solution: Just restart
docker-compose restart orchestrator
```

### Scenario 2: Conflicting Network from Another Project
```bash
# Find the conflicting network
docker network ls

# Check what's using it
docker network inspect NETWORK_NAME

# If safe, remove it
docker network rm NETWORK_NAME
```

### Scenario 3: System Default Network Conflict
```bash
# Some systems have 172.20.x.x reserved
# Solution: Use different subnet (already done - 172.25.0.0/16)
```

## Prevention

To avoid this in future:

1. **Use unique subnets** for each project
2. **Check existing networks** before creating:
   ```bash
   docker network ls
   ```
3. **Clean up unused networks**:
   ```bash
   docker network prune
   ```

## Troubleshooting

### Still Getting Errors?

1. **Check all Docker networks**:
   ```bash
   docker network ls
   docker network inspect $(docker network ls -q)
   ```

2. **Remove all unused networks**:
   ```bash
   docker network prune -f
   ```

3. **Use a completely different subnet**:
   Edit `docker-compose.yml`:
   ```yaml
   subnet: 172.30.0.0/16  # Or any unused range
   ```

4. **Let Docker auto-assign**:
   Remove the ipam section entirely:
   ```yaml
   networks:
     honeypot_net:
       driver: bridge
       # No ipam config - Docker will auto-assign
   ```

## Summary

The error is now fixed with:
- ✅ Graceful network handling in code
- ✅ Different subnet in docker-compose (172.25.0.0/16)
- ✅ Automated fix script
- ✅ Fallback to default bridge if needed

Run `./fix_network.sh` to apply the fix!
