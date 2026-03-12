# 🍯 Adaptive Honeypot System

An intelligent, self-adapting honeypot network that uses AI to analyze attacks and automatically reconfigure defenses in real-time.

## 🌟 Features

### Core Capabilities
- **🤖 AI-Powered Analysis**: Automatically analyzes attack patterns using OpenAI/Anthropic/Gemini LLMs
- **🔄 Real-time Adaptation**: Dynamically reconfigures honeypots based on detected threats
- **🎯 SSH Honeypot Support**: Cowrie-based SSH honeypots
- **📊 Live Dashboard**: Real-time monitoring with WebSocket updates
- **🐳 Container-Based**: Fully containerized with Docker
- **📈 Scalable Architecture**: Supports multiple honeypot instances

### Adaptive Features
- **Pattern Recognition**: AI-based attack classification
- **Configuration Generation**: Automatic honeypot reconfiguration
- **Session Preservation**: Maintains attacker sessions during migrations
- **Deception Strategies**: Dynamic fake users, files, and responses
- **Threat Escalation**: Adjusts interaction levels based on attacker sophistication

## 📋 Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  Adaptive Orchestrator                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  Deployment  │  │    Config    │  │      AI      │  │
│  │   Manager    │  │    Engine    │  │   Analyzer   │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │     Log      │  │   Resource   │  │   Session    │  │
│  │  Processor   │  │   Monitor    │  │   Manager    │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
   ┌────▼────┐       ┌────▼────┐       ┌────▼────┐
   │Honeypot1│       │Honeypot2│       │Honeypot3│
   │ (Cowrie)│       │ (Cowrie)│       │ (Cowrie)│
   └─────────┘       └─────────┘       └─────────┘
```

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.11+
- OpenAI, Anthropic, or Google Gemini API key

### Installation

1. **Clone the repository**
```bash
cd /path/to/Adaptive_Honeypot
```

2. **Configure environment**
```bash
cp .env.example .env
# Edit .env and add your API keys
nano .env
```

3. **Build and start services**
```bash
docker-compose up -d
```

4. **Access the dashboard**
```
http://localhost:3000
```

5. **API documentation**
```
http://localhost:8000/docs
```

## 📦 Module Structure

```
adaptive_honeypot/
├── core/
│   ├── orchestrator.py          # Main orchestration engine
│   ├── deployment.py            # Container deployment & health
│   ├── config_engine.py         # Configuration generation & validation
│   └── models.py                # Data models
├── monitoring/
│   ├── log_processor.py         # Log parsing & structuring
│   └── resource_monitor.py      # CPU/RAM/Disk monitoring
├── ai/
│   └── analyzer.py              # AI-based attack analysis
├── api/
│   └── main.py                  # FastAPI application
├── dashboard/
│   └── index.html               # Web dashboard
├── docker/
│   ├── Dockerfile.orchestrator
│   └── docker-compose.yml
└── requirements.txt
```

## 🔧 Configuration

### Environment Variables

```bash
# AI Configuration (Choose one provider)
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
GEMINI_API_KEY=your_gemini_key_here

# AI Provider Selection
AI_PROVIDER=gemini  # Options: openai, anthropic, gemini
AI_MODEL=gemini-1.5-pro  # Model depends on provider

# Model Options by Provider:
# OpenAI: gpt-4, gpt-4-turbo, gpt-3.5-turbo
# Anthropic: claude-3-opus-20240229, claude-3-sonnet-20240229, claude-3-haiku-20240307
# Gemini: gemini-pro, gemini-1.5-pro, gemini-1.5-flash

# Adaptive Settings
ADAPTATION_THRESHOLD=5           # Events before triggering adaptation
ANALYSIS_INTERVAL=60             # Seconds between periodic analysis
MAX_HONEYPOTS=10                 # Maximum concurrent honeypots

# Network
HONEYPOT_NETWORK=honeypot_net
HONEYPOT_SUBNET=172.20.0.0/16
```

### Honeypot Configuration Schema

```json
{
  "name": "ssh-honeypot",
  "type": "ssh",
  "port": 2222,
  "interaction_level": "low",
  "hostname": "ubuntu-server",
  "banner": "SSH-2.0-OpenSSH_8.2p1",
  "fake_users": [
    {"username": "root", "password": "toor"}
  ],
  "fake_files": ["/etc/passwd", "/var/log/auth.log"],
  "allowed_commands": ["ls", "pwd", "whoami"],
  "response_delay": 0.1,
  "max_sessions": 5,
  "session_timeout": 300
}
```

## 🎯 API Endpoints

### Honeypot Management
- `POST /honeypots/deploy` - Deploy new honeypot
- `DELETE /honeypots/{id}` - Remove honeypot
- `GET /honeypots` - List all honeypots
- `GET /honeypots/{id}/health` - Get health status
- `POST /honeypots/{id}/restart` - Restart honeypot

### Monitoring
- `GET /honeypots/{id}/logs` - Get attack logs
- `GET /honeypots/{id}/stats` - Get statistics
- `GET /adaptations` - Get adaptation history
- `GET /resources` - Get system resources
- `GET /status` - Get orchestrator status

### WebSocket
- `WS /ws` - Real-time updates

## 🤖 AI Adaptation Logic

### Analysis Process
1. **Event Collection**: Gather attack events from honeypot logs
2. **Pattern Analysis**: AI analyzes commands, credentials, behavior
3. **Threat Classification**: Categorize attacker skill level and objectives
4. **Configuration Generation**: Create adaptive honeypot configuration
5. **Deployment**: Apply new configuration with session preservation

### Adaptation Triggers
- **Threshold-based**: Triggered after N attack events
- **Periodic**: Scheduled analysis every M seconds
- **Threat-based**: Immediate response to high-severity attacks

### AI Analysis Output
```json
{
  "attack_sophistication": "high",
  "attacker_skill_level": "advanced",
  "attack_objectives": ["reconnaissance", "exploitation"],
  "threat_level": "high",
  "recommended_interaction_level": "high",
  "deception_strategies": ["fake_files", "delayed_responses"],
  "configuration_changes": {
    "interaction_level": "high",
    "allowed_commands": ["ls", "cat", "wget", "curl"]
  }
}
```

## 📊 Dashboard Features

- **Real-time Monitoring**: Live attack feed and honeypot status
- **Deployment Controls**: Deploy/remove honeypots on-demand
- **Attack Statistics**: Visualize attack patterns and trends
- **Adaptation History**: View AI recommendations and applied changes
- **Resource Monitoring**: Track CPU, memory, and disk usage

## 🔒 Security Considerations

### Network Isolation
- Honeypots run in isolated Docker network
- No direct access to host system
- Controlled port exposure

### Data Protection
- Logs stored in isolated volumes
- No sensitive data in honeypots
- Automatic log rotation

### Resource Limits
- CPU and memory limits per container
- Automatic restart on failure
- Resource threshold monitoring

## 🧪 Testing

### Deploy Test Honeypot
```bash
curl -X POST http://localhost:8000/honeypots/deploy \
  -H "Content-Type: application/json" \
  -d '{"name": "test-ssh", "port": 2222}'
```

### Simulate Attack
```bash
ssh root@localhost -p 2222
# Try various commands and credentials
```

### Check Logs
```bash
curl http://localhost:8000/honeypots/{id}/logs
```

## 📈 Performance

### Resource Requirements
- **Minimum**: 2 CPU cores, 4GB RAM, 10GB storage
- **Recommended**: 4 CPU cores, 8GB RAM, 50GB storage
- **Per Honeypot**: ~100MB RAM, 5% CPU

### Scaling
- Horizontal: Deploy multiple orchestrator instances
- Vertical: Increase container resources
- Distributed: Use external databases

## 🐛 Troubleshooting

### Docker Connection Issues
```bash
# Check Docker daemon
sudo systemctl status docker

# Verify Docker socket permissions
sudo chmod 666 /var/run/docker.sock
```

### Honeypot Not Starting
```bash
# Check logs
docker logs honeypot_{id}

# Verify network
docker network ls | grep honeypot_net
```

### AI Analysis Failing
```bash
# For OpenAI - Verify API key
echo $OPENAI_API_KEY
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# For Gemini - Verify API key
echo $GEMINI_API_KEY
curl "https://generativelanguage.googleapis.com/v1/models?key=$GEMINI_API_KEY"

# For Anthropic - Check API key in .env
grep ANTHROPIC_API_KEY .env
```

## 🛠️ Development

### Run Locally
```bash
# Install dependencies
pip install -r requirements.txt

# Start orchestrator
python -m uvicorn api.main:app --reload

# Open dashboard
open dashboard/index.html
```

### Add New Honeypot Type
1. Create honeypot template in `honeypots/`
2. Update `HoneypotType` enum in `models.py`
3. Implement deployment logic in `deployment.py`
4. Add configuration schema in `config_engine.py`

## 📝 License

MIT License - See LICENSE file for details

## 🤝 Contributing

Contributions welcome! Please read CONTRIBUTING.md first.

## 📧 Support

For issues and questions:
- GitHub Issues: [Create Issue]
- Documentation: [Wiki]

## 🙏 Acknowledgments

- Cowrie Honeypot Project
- Docker Community
- OpenAI, Anthropic & Google Gemini

---

**⚠️ Warning**: This system is designed for research and defensive security purposes only. Ensure compliance with local laws and regulations when deploying honeypots.
