# 🚀 Quick Start Guide

## Prerequisites Check

```bash
# Check Docker
docker --version
# Should show: Docker version 20.x or higher

# Check Docker Compose
docker-compose --version
# Should show: docker-compose version 1.29.x or higher

# Check Python (for local development)
python3 --version
# Should show: Python 3.11 or higher
```

## Installation (5 Minutes)

### Step 1: Configure Environment
```bash
# Copy environment template
cp .env.example .env

# Edit and add your API key (choose one provider)
nano .env

# Option 1: Google Gemini (Recommended - Free tier available)
# Add: GEMINI_API_KEY=your-gemini-key-here
# Set: AI_PROVIDER=gemini
# Set: AI_MODEL=gemini-1.5-pro

# Option 2: OpenAI
# Add: OPENAI_API_KEY=sk-your-key-here
# Set: AI_PROVIDER=openai
# Set: AI_MODEL=gpt-4

# Option 3: Anthropic
# Add: ANTHROPIC_API_KEY=sk-ant-your-key-here
# Set: AI_PROVIDER=anthropic
# Set: AI_MODEL=claude-3-sonnet-20240229

# See AI_PROVIDER_GUIDE.md for detailed configuration
```

### Step 2: Start System
```bash
# Make startup script executable
chmod +x start.sh

# Run startup script
./start.sh
```

### Step 3: Verify Installation
```bash
# Check running containers
docker ps

# Should see:
# - adaptive_orchestrator
# - honeypot_redis
# - honeypot_dashboard
```

## First Honeypot Deployment

### Option 1: Using Dashboard (Easiest)
1. Open browser: http://localhost:3000
2. Enter honeypot name: `my-first-honeypot`
3. Enter port: `2222`
4. Click "Deploy"
5. Watch it appear in "Active Honeypots" section

### Option 2: Using API
```bash
curl -X POST http://localhost:8000/honeypots/deploy \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-first-honeypot",
    "port": 2222
  }'
```

### Option 3: Using Python
```python
import requests

response = requests.post(
    'http://localhost:8000/honeypots/deploy',
    json={'name': 'my-first-honeypot', 'port': 2222}
)
print(response.json())
```

## Testing Your Honeypot

### Simulate SSH Attack
```bash
# Try to connect (will fail, that's expected)
ssh root@localhost -p 2222

# Try some credentials
# Username: root
# Password: password123

# Try some commands after login
ls
pwd
whoami
cat /etc/passwd
```

### View Attack Logs
```bash
# Using API
curl http://localhost:8000/honeypots/{honeypot_id}/logs

# Using Dashboard
# Go to http://localhost:3000
# Scroll to "Recent Attack Events"
```

## Monitoring

### Real-time Dashboard
- URL: http://localhost:3000
- Shows: Active honeypots, attacks, adaptations
- Updates: Every 5 seconds via WebSocket

### API Documentation
- URL: http://localhost:8000/docs
- Interactive Swagger UI
- Test all endpoints

### View Logs
```bash
# Orchestrator logs
docker logs -f adaptive_orchestrator

# Specific honeypot logs
docker logs -f honeypot_{honeypot_id}

# All logs
docker-compose logs -f
```

## Common Operations

### Deploy Multiple Honeypots
```bash
# Deploy on different ports
curl -X POST http://localhost:8000/honeypots/deploy \
  -H "Content-Type: application/json" \
  -d '{"name": "ssh-honeypot-1", "port": 2222}'

curl -X POST http://localhost:8000/honeypots/deploy \
  -H "Content-Type: application/json" \
  -d '{"name": "ssh-honeypot-2", "port": 2223}'
```

### Check Honeypot Health
```bash
curl http://localhost:8000/honeypots/{honeypot_id}/health
```

### View Statistics
```bash
curl http://localhost:8000/honeypots/{honeypot_id}/stats
```

### View Adaptations
```bash
curl http://localhost:8000/adaptations
```

### Remove Honeypot
```bash
curl -X DELETE http://localhost:8000/honeypots/{honeypot_id}
```

## System Management

### Stop System
```bash
docker-compose down
```

### Restart System
```bash
docker-compose restart
```

### Update System
```bash
# Pull latest changes
git pull

# Rebuild containers
docker-compose up -d --build
```

### View Resource Usage
```bash
# System resources
curl http://localhost:8000/resources

# Docker stats
docker stats
```

## Troubleshooting

### Honeypot Won't Deploy
```bash
# Check if port is available
netstat -tulpn | grep 2222

# Check Docker network
docker network ls | grep honeypot_net

# Check orchestrator logs
docker logs adaptive_orchestrator
```

### Dashboard Not Loading
```bash
# Check if dashboard container is running
docker ps | grep dashboard

# Restart dashboard
docker-compose restart dashboard
```

### AI Analysis Not Working
```bash
# For Gemini
grep GEMINI_API_KEY .env
curl "https://generativelanguage.googleapis.com/v1/models?key=YOUR_KEY"

# For OpenAI
grep OPENAI_API_KEY .env
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer YOUR_KEY"

# For Anthropic
grep ANTHROPIC_API_KEY .env

# Check orchestrator logs for errors
docker logs adaptive_orchestrator | grep -i error

# See AI_PROVIDER_GUIDE.md for detailed troubleshooting
```

### High CPU Usage
```bash
# Check resource usage
docker stats

# Reduce max honeypots in .env
nano .env
# Set: MAX_HONEYPOTS=3

# Restart
docker-compose restart
```

## Advanced Usage

### Custom Configuration
```python
import requests

custom_config = {
    "name": "advanced-honeypot",
    "type": "ssh",
    "port": 2222,
    "interaction_level": "high",
    "hostname": "production-server",
    "banner": "SSH-2.0-OpenSSH_8.9p1",
    "fake_users": [
        {"username": "admin", "password": "admin123"},
        {"username": "root", "password": "toor"}
    ],
    "fake_files": [
        "/etc/passwd",
        "/var/www/html/config.php",
        "/home/admin/.ssh/id_rsa"
    ],
    "allowed_commands": [
        "ls", "pwd", "whoami", "cat", "wget", "curl"
    ],
    "response_delay": 0.5,
    "max_sessions": 10
}

response = requests.post(
    'http://localhost:8000/honeypots/deploy',
    json=custom_config
)
```

### WebSocket Connection
```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Update:', data);
};
```

### Automated Testing
```bash
# Run system tests
python test_system.py
```

## Next Steps

1. **Monitor Attacks**: Watch the dashboard for incoming attacks
2. **Analyze Adaptations**: Check how the system adapts to different attack patterns
3. **Customize Configurations**: Experiment with different honeypot settings
4. **Scale Up**: Deploy multiple honeypots on different ports
5. **Integrate**: Connect to your SIEM or logging system

## Getting Help

- **Documentation**: See DOCUMENTATION.md for technical details
- **API Reference**: http://localhost:8000/docs
- **Logs**: `docker-compose logs -f`
- **Issues**: Check GitHub issues or create new one

## Security Reminder

⚠️ **Important**: 
- Only deploy on isolated networks or test environments
- Never expose honeypots directly to the internet without proper firewall rules
- Regularly review logs for unexpected behavior
- Keep API keys secure and never commit them to version control

---

**Happy Honeypotting! 🍯**
