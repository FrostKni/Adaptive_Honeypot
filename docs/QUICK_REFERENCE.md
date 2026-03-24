# Adaptive Honeypot System - Quick Reference

## Project Overview

**Type:** AI-Powered Cybersecurity Deception Platform  
**Version:** 2.0.0  
**Primary Language:** Python 3.11+ (Backend) / TypeScript (Frontend)  
**Architecture:** Microservices with Docker containers

---

## Quick Start

```bash
# 1. Clone and configure
git clone https://github.com/FrostKni/Adaptive_Honeypot.git
cd Adaptive_Honeypot
cp .env.example .env
# Edit .env with your API keys

# 2. Start services
docker-compose up -d

# 3. Access
# Dashboard: http://localhost:3000
# API: http://localhost:8000/api/docs
# SSH Honeypot: ssh -p 2222 user@localhost
```

---

## Project Structure

```
src/
├── ai/                    # AI analysis & decision execution
│   ├── analyzer.py        # Multi-provider AI analyzer
│   ├── monitoring.py      # Real-time AI service
│   └── decision_executor.py  # Docker actions
├── cognitive/             # Deception framework
│   ├── engine.py          # Strategy orchestration
│   └── profiler.py        # Cognitive bias detection
├── collectors/            # Log ingestion
│   └── cowrie_collector.py   # SSH honeypot logs
├── api/                   # FastAPI backend
│   ├── app.py             # Application factory
│   └── v1/endpoints/      # REST endpoints
├── core/                  # Infrastructure
│   ├── config.py          # Settings
│   ├── deployment.py      # Docker management
│   └── db/                # Database layer
├── alerting/              # Multi-channel alerts
└── honeypots/             # Honeypot implementations
```

---

## Key Components

### 1. Honeypot Types
| Type   | Port  | Technology          |
|--------|-------|---------------------|
| SSH    | 2222  | Cowrie              |
| HTTP   | 8080  | Nginx               |
| FTP    | 2121  | Pure-FTPd           |
| Telnet | 2323  | Cowrie              |

### 2. AI Providers
- **Primary:** OpenAI, Anthropic, Gemini
- **Fallback:** Local DeepSeek (api.ai.oac)
- **Guaranteed:** Rule-based analyzer

### 3. Decision Actions
- `monitor` - Continue observation
- `reconfigure` - Modify deception settings
- `isolate` - Quarantine attacker
- `switch_container` - Transparent migration

### 4. Cognitive Biases Targeted
- Confirmation Bias
- Sunk Cost
- Dunning-Kruger
- Anchoring
- Curiosity Gap
- Loss Aversion

---

## API Endpoints Quick Reference

### Honeypots
```
GET    /api/v1/honeypots           # List all
POST   /api/v1/honeypots           # Deploy new
GET    /api/v1/honeypots/{id}      # Get details
DELETE /api/v1/honeypots/{id}      # Remove
POST   /api/v1/honeypots/{id}/restart  # Restart
GET    /api/v1/honeypots/{id}/health   # Health
GET    /api/v1/honeypots/{id}/logs     # Logs
```

### Sessions & Attacks
```
GET    /api/v1/sessions            # List sessions
GET    /api/v1/sessions/{id}       # Session details
GET    /api/v1/sessions/{id}/replay # Terminal replay
GET    /api/v1/attacks             # Attack feed
```

### Analytics
```
GET    /api/v1/analytics/dashboard # Stats
GET    /api/v1/analytics/timeline  # Timeline
```

### AI & Cognitive
```
GET    /api/v1/ai-monitoring/status    # AI status
GET    /api/v1/ai-monitoring/decisions # Decisions
GET    /api/v1/cognitive/{session_id}  # Profile
```

### WebSocket
```
WS     /api/v1/ws                   # Real-time feed
```

---

## Database Models

### Core Tables
```
honeypots          - Honeypot instances
sessions           - Attack sessions
attack_events      - Individual events
adaptations        - Config changes
alerts             - Security alerts
cognitive_profiles - Psychological profiles
deception_events   - Deception records
threat_intelligence - IOC database
```

---

## Configuration

### Required Environment Variables
```bash
# AI
AI_PROVIDER=openai
OPENAI_API_KEY=sk-...

# Security
SECURITY_JWT_SECRET=your-secret

# Database (optional, defaults to SQLite)
DB_HOST=localhost
DB_PASSWORD=secret
```

### Important Defaults
```bash
HONEYPOT_MAX_INSTANCES=20
HONEYPOT_SESSION_TIMEOUT=3600
SECURITY_JWT_EXPIRE_MINUTES=60
SECURITY_RATE_LIMIT_REQUESTS=100
```

---

## Common Commands

```bash
# Development
uvicorn src.api.app:app --reload --port 8000

# Tests
pytest tests/ -v --cov=src

# Docker
docker-compose up -d
docker-compose logs -f backend
docker ps --filter label=honeypot.id

# Database
alembic upgrade head
```

---

## Troubleshooting

| Issue                  | Solution                           |
|------------------------|------------------------------------|
| Container won't start  | Check port availability            |
| AI analysis failing    | Verify API key, check endpoint     |
| WebSocket disconnects  | Check CORS, proxy configuration    |
| High memory            | Adjust container limits            |

---

## Key Files

| File                              | Purpose                    |
|-----------------------------------|----------------------------|
| `src/api/app.py`                  | FastAPI application        |
| `src/ai/monitoring.py`            | AI service                 |
| `src/ai/analyzer.py`              | Attack analysis            |
| `src/cognitive/engine.py`         | Deception orchestration    |
| `src/collectors/cowrie_collector.py` | Log ingestion          |
| `src/core/deployment.py`          | Docker management          |
| `src/core/db/models.py`           | Database schema            |

---

## Data Flow Summary

```
Attacker → Honeypot Container → Log Collector → AI Analysis
                                                           ↓
WebSocket ← FastAPI ← Database ← Cognitive Engine ← Decision
                                      ↓
                            Deception Response
```

---

## Architecture Layers

1. **Presentation:** React Dashboard + WebSocket
2. **API:** FastAPI REST endpoints
3. **Business Logic:** AI, Cognitive Engine, Alerting
4. **Data:** SQLAlchemy ORM + SQLite/PostgreSQL
5. **Infrastructure:** Docker containers + Networks

---

*Quick Reference v2.0*