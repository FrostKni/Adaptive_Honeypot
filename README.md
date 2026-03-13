# Adaptive Honeypot System v2.0

Production-grade, AI-powered honeypot network with real-time adaptation and threat intelligence.

## Features

- **Multi-Protocol Support**: SSH, HTTP, FTP, Telnet honeypots
- **AI-Powered Analysis**: OpenAI, Anthropic, Gemini integration with fallback chains
- **Real-Time Adaptation**: Dynamic configuration changes based on attacker behavior
- **Session Replay**: Full terminal recording and playback
- **Threat Intelligence**: Built-in IOC database with RAG integration
- **Multi-Channel Alerting**: Email, Slack, Discord, Webhooks
- **Production Ready**: Docker, Kubernetes, Prometheus, Grafana

## Quick Start

```bash
# Clone and configure
git clone https://github.com/FrostKni/Adaptive_Honeypot.git
cd Adaptive_Honeypot
cp .env.example .env
# Edit .env with your API keys

# Start with Docker
docker-compose -f deploy/docker/docker-compose.prod.yml up -d

# Access
# Dashboard: http://localhost:3000
# API Docs: http://localhost:8000/api/docs
```

## Project Structure

```
├── src/                    # Backend source code
│   ├── ai/                 # AI analyzer with multi-provider support
│   ├── alerting/           # Multi-channel alert system
│   ├── api/                # FastAPI REST + WebSocket
│   ├── core/               # Config, database, security
│   └── honeypots/          # Honeypot implementations
├── frontend/               # React dashboard
├── deploy/                 # Deployment configurations
│   ├── docker/             # Docker Compose + Dockerfiles
│   ├── k8s/                # Kubernetes manifests
│   └── monitoring/         # Prometheus + Grafana
├── tests/                  # Test suite
└── docs/                   # Documentation
```

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/honeypots` | List all honeypots |
| `POST /api/v1/honeypots` | Deploy new honeypot |
| `GET /api/v1/sessions` | List attack sessions |
| `GET /api/v1/attacks` | Attack event feed |
| `GET /api/v1/analytics/dashboard` | Dashboard statistics |
| `WS /api/v1/ws` | Real-time updates |

## Configuration

Key environment variables (see `.env.example`):

```bash
AI_PROVIDER=openai          # openai, anthropic, gemini
OPENAI_API_KEY=sk-...       # Your API key
DB_PASSWORD=secure_pass     # PostgreSQL password
SECURITY_JWT_SECRET=secret  # JWT signing secret
```

## Deployment

### Docker Compose (Development)
```bash
docker-compose -f deploy/docker/docker-compose.prod.yml up -d
```

### Kubernetes (Production)
```bash
kubectl apply -f deploy/k8s/
```

## Documentation

- [Architecture](docs/architecture/ARCHITECTURE.md)
- [Deployment Guide](docs/deployment/DEPLOYMENT.md)

## License

MIT License