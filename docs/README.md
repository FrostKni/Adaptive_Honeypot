# Adaptive Honeypot System v2.0

Production-grade, AI-powered honeypot network with real-time adaptation and threat intelligence.

## Overview

The Adaptive Honeypot System is a sophisticated cybersecurity platform that deploys intelligent honeypots to detect, analyze, and respond to cyber attacks in real-time. Using advanced AI/LLM technology, the system automatically adapts its configuration based on attacker behavior to maximize intelligence gathering.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          PRESENTATION LAYER                          │
├─────────────────────────────────────────────────────────────────────┤
│  React Dashboard (Port 3000)     │     REST API + WebSocket (8000)  │
└───────────────────────┬─────────────────────────┬───────────────────┘
                        │                         │
┌───────────────────────▼─────────────────────────▼───────────────────┐
│                        APPLICATION LAYER                             │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │ Orchestrator │  │   AI Engine  │  │   Alerting   │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
└─────────────────────────────────────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────────────┐
│                          DATA LAYER                                  │
├─────────────────────────────────────────────────────────────────────┤
│  PostgreSQL (Primary DB)  │  Redis (Cache/Pub-Sub)                  │
└─────────────────────────────────────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────────────┐
│                        HONEYPOT LAYER                                │
├─────────────────────────────────────────────────────────────────────┤
│  SSH Honeypots  │  HTTP Honeypots  │  FTP Honeypots  │  Custom      │
│  (Cowrie)       │  (Custom)        │  (vsftpd)       │  (Docker)    │
└─────────────────────────────────────────────────────────────────────┘
```

## Features

### Core Capabilities
- **Multi-Protocol Support**: SSH, HTTP, FTP, Telnet honeypots
- **AI-Powered Analysis**: OpenAI, Anthropic, Gemini integration with fallback chains
- **Real-Time Adaptation**: Dynamic configuration changes based on attacker behavior
- **Session Replay**: Full terminal recording and playback
- **Threat Intelligence**: Built-in IOC database with RAG integration

### Security Features
- JWT + API Key authentication
- Role-based access control (RBAC)
- Rate limiting and DDoS protection
- Network isolation for honeypots
- Audit logging

### Monitoring & Alerting
- Prometheus metrics
- Grafana dashboards
- Multi-channel alerts (Email, Slack, Discord, Webhooks)
- Real-time WebSocket updates

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.11+
- Node.js 18+ (for frontend development)
- PostgreSQL 15+
- Redis 7+

### Installation

1. Clone and configure:
```bash
git clone https://github.com/FrostKni/Adaptive_Honeypot.git
cd Adaptive_Honeypot
cp .env.example .env
# Edit .env with your settings
```

2. Start with Docker:
```bash
docker-compose -f deploy/docker/docker-compose.prod.yml up -d
```

3. Access the dashboard:
- Dashboard: http://localhost:3000
- API Docs: http://localhost:8000/api/docs
- Grafana: http://localhost:3001

### Development Setup

Backend:
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn src.api.app:app --reload
```

Frontend:
```bash
cd frontend
npm install
npm run dev
```

## API Reference

### Authentication

```bash
# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin"}'

# Use token
curl http://localhost:8000/api/v1/honeypots \
  -H "Authorization: Bearer <token>"
```

### Honeypots

```bash
# List honeypots
GET /api/v1/honeypots

# Create honeypot
POST /api/v1/honeypots
{
  "name": "ssh-prod-1",
  "type": "ssh",
  "port": 2222,
  "interaction_level": "medium"
}

# Get honeypot
GET /api/v1/honeypots/{id}

# Delete honeypot
DELETE /api/v1/honeypots/{id}
```

### Sessions & Attacks

```bash
# List sessions
GET /api/v1/sessions

# Get session replay
GET /api/v1/sessions/{id}/replay

# List attack events
GET /api/v1/attacks

# Get analytics
GET /api/v1/analytics/dashboard
```

### WebSocket

```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/ws');

ws.send(JSON.stringify({
  type: 'subscribe',
  channels: ['attacks', 'alerts', 'honeypots']
}));

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data);
};
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `AI_PROVIDER` | AI provider (openai/anthropic/gemini) | openai |
| `AI_MODEL` | Model to use | gpt-4-turbo-preview |
| `DB_HOST` | PostgreSQL host | localhost |
| `REDIS_HOST` | Redis host | localhost |
| `HONEYPOT_MAX_INSTANCES` | Max honeypots | 20 |
| `ADAPTATION_THRESHOLD` | Events before adaptation | 5 |

### AI Configuration

```python
# Multi-provider with fallback
AI_PROVIDER=openai
AI_MODEL=gpt-4-turbo-preview
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=...
```

## Deployment

### Docker Compose

```bash
docker-compose -f deploy/docker/docker-compose.prod.yml up -d
```

### Kubernetes

```bash
kubectl apply -f deploy/k8s/namespace.yaml
kubectl apply -f deploy/k8s/
```

### Scaling

The system supports horizontal scaling:
- Backend: HPA configured for 2-10 replicas
- Frontend: HPA configured for 2-5 replicas
- PostgreSQL: StatefulSet with PVCs

## Monitoring

### Prometheus Metrics

- `honeypot_active_count`: Active honeypots
- `attack_events_total`: Total attack events
- `session_duration_seconds`: Session duration histogram
- `adaptation_count`: Adaptation events

### Grafana Dashboards

Pre-built dashboards for:
- Attack overview
- Honeypot health
- AI analysis metrics
- System resources

## Security Considerations

1. **Network Isolation**: Honeypots run in isolated Docker networks
2. **No Host Access**: Containers cannot access host filesystem
3. **Rate Limiting**: API endpoints are rate-limited
4. **Audit Logging**: All actions are logged
5. **Secrets Management**: Use Kubernetes secrets or vault

## License

MIT License - See LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `pytest`
5. Submit a pull request

## Support

- GitHub Issues: https://github.com/FrostKni/Adaptive_Honeypot/issues
- Documentation: /docs