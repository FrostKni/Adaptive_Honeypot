# Adaptive Honeypot System v2.0

A production-grade, AI-powered honeypot network with real-time behavioral adaptation and a novel Cognitive-Behavioral Deception Framework (CBDF) for manipulating attacker decision-making.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [API Reference](#api-reference)
- [Deployment](#deployment)
- [Monitoring](#monitoring)
- [Testing](#testing)
- [Project Structure](#project-structure)
- [Documentation](#documentation)
- [License](#license)

---

## Overview

The Adaptive Honeypot System deploys and manages decoy services (SSH, HTTP, FTP, Telnet) that lure attackers, record their behavior, and autonomously adapt in real time using AI analysis. A secondary cognitive layer profiles attacker psychology and applies targeted deception strategies to extend engagement and extract threat intelligence.

**Key differentiators:**
- AI-driven adaptation loop: attacker events → LLM analysis → Docker reconfiguration, all without human intervention
- CBDF: detects 8 cognitive biases in attacker behavior and applies 11 bias-specific deception strategies
- Multi-provider AI with automatic fallback (OpenAI → Anthropic → Gemini → rule-based)
- Full session replay with terminal recording

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Attackers                            │
└──────┬──────────────┬──────────────┬──────────────┬─────────┘
       │ SSH :2222    │ Telnet :2323 │ HTTP :8080   │ FTP :2121
┌──────▼──────────────▼──────────────▼──────────────▼─────────┐
│              Docker-Managed Honeypot Containers              │
│         (Cowrie SSH/Telnet · nginx HTTP · pure-ftpd)         │
└──────────────────────────┬──────────────────────────────────┘
                           │ Cowrie JSON logs
┌──────────────────────────▼──────────────────────────────────┐
│                   CowrieLogCollector                         │
│              (tail logs · dedup · parse events)              │
└──────────┬────────────────────────────┬─────────────────────┘
           │                            │
┌──────────▼──────────┐    ┌────────────▼──────────────────────┐
│  AIMonitoringService │    │    CognitiveIntegrationBridge      │
│  (LocalLLMClient /  │    │  (routes commands to CBDF engine)  │
│   GLM5)         │    └────────────┬──────────────────────┘
└──────────┬──────────┘                 │
           │ recommended_action         │ CognitiveProfile
┌──────────▼──────────┐    ┌────────────▼──────────────────────┐
│  DecisionExecutor   │    │    CognitiveDeceptionEngine        │
│  (Docker API calls) │    │  (BiasDetector · StrategyLibrary · │
└─────────────────────┘    │   ResponseGenerator)               │
                           └───────────────────────────────────┘
           │                            │
┌──────────▼────────────────────────────▼─────────────────────┐
│              FastAPI Backend  :8000                          │
│   REST API · WebSocket · JWT + API Key Auth · Rate Limiting  │
└──────────────────────────┬──────────────────────────────────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
   ┌──────▼──────┐  ┌──────▼──────┐  ┌─────▼──────┐
   │  SQLite/    │  │    Redis    │  │  React UI  │
   │  PostgreSQL │  │   (cache)   │  │   :3000    │
   └─────────────┘  └─────────────┘  └────────────┘
```

**Data flow summary:**
1. Attacker connects to a honeypot container
2. Cowrie logs events as JSON; `CowrieLogCollector` tails and deduplicates them
3. Events are sent to `AIMonitoringService` for threat scoring and action recommendation
4. `DecisionExecutor` applies the action (monitor / reconfigure / isolate / switch container) via Docker SDK
5. In parallel, commands are routed through `CognitiveIntegrationBridge` → `CognitiveDeceptionEngine`, which builds a cognitive profile and generates bias-targeted responses
6. All events, profiles, and decisions are persisted to the database and broadcast over WebSocket to the React dashboard

---

## Features

| Category | Details |
|---|---|
| Honeypot protocols | SSH (Cowrie), Telnet (Cowrie), HTTP (nginx), FTP (pure-ftpd) |
| AI providers | OpenAI, Anthropic, Gemini — automatic fallback chain + rule-based fallback |
| Cognitive deception | 8 bias types detected, 11 deception strategies, real-time profile building |
| Adaptation actions | monitor, reconfigure, isolate, switch_container |
| Session recording | Full terminal replay via Cowrie asciicast |
| Alerting | Email (SMTP), Slack, Discord, generic webhook |
| Auth | JWT + API key dual auth, rate limiting |
| Observability | Prometheus metrics, Grafana dashboards, Alertmanager |
| Deployment | Docker Compose (dev + prod), Kubernetes (HPA, PDB, NetworkPolicy) |

---

## Prerequisites

- Docker ≥ 24 and Docker Compose v2
- Python 3.11+ (for local dev only)
- Node.js 18+ (for frontend dev only)
- At least one AI provider API key (OpenAI, Anthropic, or Gemini)

---

## Quick Start

```bash
git clone https://github.com/FrostKni/Adaptive_Honeypot.git
cd Adaptive_Honeypot

# Configure environment
cp .env.example .env
# Edit .env — set OPENAI_API_KEY (or another provider), SECURITY_JWT_SECRET, DB_PASSWORD

# Start everything (dev mode — SQLite, no external DB required)
bash start.sh

# Or manually
docker-compose up -d
```

Services after startup:

| Service | URL |
|---|---|
| React Dashboard | http://localhost:3000 |
| API + Swagger UI | http://localhost:8000/api/docs |
| SSH Honeypot | localhost:2222 |
| Telnet Honeypot | localhost:2323 |
| HTTP Honeypot | http://localhost:8080 |
| FTP Honeypot | localhost:2121 |

Default login: set via `ADMIN_USERNAME` / `ADMIN_PASSWORD` in `.env`.

---

## Configuration

All configuration is driven by environment variables. Copy `.env.example` to `.env` and edit:

```bash
# ── Application ──────────────────────────────────────────────
ENVIRONMENT=development          # development | production
DEBUG=true

# ── Database ─────────────────────────────────────────────────
# Dev: leave blank to use SQLite (honeypot.db)
# Prod: set all DB_* vars to use PostgreSQL
DB_HOST=localhost
DB_PORT=5432
DB_USER=honeypot
DB_PASSWORD=change_me_in_production
DB_NAME=adaptive_honeypot

# ── AI Provider ───────────────────────────────────────────────
AI_PROVIDER=openai               # openai | anthropic | gemini
AI_MODEL=gpt-4-turbo-preview
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=...

# ── Security ──────────────────────────────────────────────────
SECURITY_JWT_SECRET=change-me-to-secure-random-string
ADMIN_USERNAME=admin
ADMIN_PASSWORD=change_me

# ── Alerting ──────────────────────────────────────────────────
ALERT_SLACK_WEBHOOK_URL=https://hooks.slack.com/...
ALERT_DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
ALERT_SMTP_HOST=smtp.example.com
ALERT_EMAIL_RECIPIENTS=security@example.com
```

See `.env.example` for the full list of variables including Redis, honeypot tuning, rate limiting, and monitoring options.

---

## API Reference

Base URL: `http://localhost:8000/api/v1`

Interactive docs: `http://localhost:8000/api/docs` (Swagger UI) · `http://localhost:8000/api/redoc`

### Core Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/auth/login` | Obtain JWT token |
| `POST` | `/auth/api-keys` | Create API key |
| `GET` | `/honeypots` | List all honeypots |
| `POST` | `/honeypots` | Deploy a new honeypot |
| `DELETE` | `/honeypots/{id}` | Remove a honeypot |
| `GET` | `/sessions` | List attack sessions |
| `GET` | `/sessions/{id}` | Session detail + replay data |
| `GET` | `/attacks` | Attack event feed |
| `GET` | `/attacks/{id}` | Single attack event |
| `GET` | `/adaptations` | Adaptation history |
| `GET` | `/alerts` | Alert history |
| `GET` | `/threat-intel` | IOC database |
| `GET` | `/analytics/dashboard` | Aggregated dashboard stats |

### AI Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/ai/status` | AI service status + provider info |
| `GET` | `/ai/activities` | Recent AI analysis activities |
| `GET` | `/ai/decisions` | Decision execution history |
| `POST` | `/ai/start` | Start AI monitoring service |
| `POST` | `/ai/stop` | Stop AI monitoring service |
| `POST` | `/ai/trigger` | Manually trigger analysis |
| `WS` | `/ai/ws` | Real-time AI event stream |

### Cognitive Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/cognitive/profiles` | All attacker cognitive profiles |
| `GET` | `/cognitive/profiles/{session_id}` | Profile for a session |
| `GET` | `/cognitive/biases` | Detected bias breakdown |
| `GET` | `/cognitive/mental-model` | Attacker mental model state |
| `GET` | `/cognitive/strategies` | Active deception strategies |
| `GET` | `/cognitive/effectiveness` | Strategy effectiveness metrics |
| `WS` | `/cognitive/ws` | Real-time cognitive event stream |

### WebSocket

```
ws://localhost:8000/api/v1/ws?token=<jwt>
```

Broadcasts: `attack_event`, `adaptation`, `alert`, `ai_decision`, `cognitive_update`

---

## Deployment

### Docker Compose — Development

Uses SQLite, no external dependencies:

```bash
docker-compose up -d
```

### Docker Compose — Production

Uses PostgreSQL 16, Redis 7, Prometheus, Grafana, Alertmanager:

```bash
# Set production env vars first
cp .env.example .env
# Edit .env: ENVIRONMENT=production, DB_*, REDIS_*, SECURITY_JWT_SECRET

docker-compose -f deploy/docker/docker-compose.prod.yml up -d
```

Production service ports:

| Service | Port |
|---|---|
| Backend API | 8000 |
| Frontend | 3000 |
| PostgreSQL | 5432 |
| Redis | 6379 |
| Prometheus | 9090 |
| Grafana | 3001 |
| Alertmanager | 9093 |

### Kubernetes — Production

Full manifests in `deploy/k8s/`. Includes HPA (2–10 replicas), PodDisruptionBudget, NetworkPolicy, and init containers that wait for PostgreSQL and Redis readiness.

```bash
# Create namespace and secrets first
kubectl apply -f deploy/k8s/namespace.yaml
kubectl apply -f deploy/k8s/secrets.yaml
kubectl apply -f deploy/k8s/configmap.yaml

# Deploy all services
kubectl apply -f deploy/k8s/

# Check rollout
kubectl rollout status deployment/adaptive-honeypot-backend -n honeypot
```

Key K8s resources:

| Resource | Details |
|---|---|
| `backend.yaml` | Deployment + HPA (CPU 70%) + PDB (minAvailable: 1) + NetworkPolicy |
| `postgres.yaml` | StatefulSet + PVC |
| `redis.yaml` | Deployment + ClusterIP |
| `prometheus.yaml` | Deployment + ConfigMap |
| `grafana.yaml` | Deployment + PVC |
| `ingress.yaml` | NGINX ingress for backend + frontend |

---

## Monitoring

Prometheus scrapes metrics from the backend (`/metrics`), Redis, PostgreSQL, and Kubernetes node/pod exporters. A pre-built Grafana dashboard (`deploy/monitoring/grafana-dashboard.json`) covers:

- Active honeypot count and session rate
- Attack events per minute by protocol
- AI decision latency and action distribution
- Cognitive bias detection frequency
- API request rate and error rate
- Container resource usage

Import the dashboard: Grafana → Dashboards → Import → upload `deploy/monitoring/grafana-dashboard.json`.

Alertmanager rules are in `deploy/monitoring/alertmanager.yml`. Default alerts fire on high attack rate, AI service down, and honeypot container crash.

---

## Testing

```bash
# Install dev dependencies
pip install -r requirements.txt

# Run all tests
pytest

# With coverage
pytest --cov=src --cov-report=html

# Specific suites
pytest tests/unit/
pytest tests/integration/
pytest tests/test_cognitive.py
pytest tests/test_ai_monitoring.py
```

Test files:

| File | Coverage |
|---|---|
| `tests/unit/test_ai.py` | AI analyzer, provider fallback, cache |
| `tests/unit/test_core.py` | Config, security, DB session |
| `tests/unit/test_alerting.py` | Alert channel dispatch |
| `tests/integration/test_api.py` | Full API endpoint integration |
| `tests/test_cognitive.py` | CBDF engine, bias detection, strategies |
| `tests/test_ai_monitoring.py` | AI monitoring service loop |
| `tests/test_decision_executor.py` | Docker action execution |
| `tests/test_cowrie_collector.py` | Log parsing and dedup |
| `tests/test_system.py` | End-to-end system flow |

---

## Project Structure

```
Adaptive_Honeypot/
├── src/
│   ├── ai/
│   │   ├── providers/base.py        # OpenAI, Anthropic, Gemini providers + factory
│   │   ├── analyzer.py              # EnhancedAIAnalyzer with fallback chain + cache
│   │   ├── decision_executor.py     # Executes AI decisions via Docker SDK
│   │   └── monitoring.py            # AIMonitoringService + LocalLLMClient
│   ├── alerting/
│   │   └── channels.py              # Email, Slack, Discord, webhook alert channels
│   ├── api/
│   │   ├── app.py                   # FastAPI app factory + middleware stack + lifespan
│   │   └── v1/
│   │       ├── __init__.py          # 12 router registrations
│   │       └── endpoints/           # auth, honeypots, sessions, attacks, adaptations,
│   │                                # alerts, threat-intel, analytics, admin, settings,
│   │                                # ai_monitoring, cognitive
│   ├── cognitive/
│   │   ├── engine.py                # CognitiveDeceptionEngine orchestrator
│   │   ├── profiler.py              # CognitiveProfiler + BiasDetector (8 bias types)
│   │   └── models.py                # CognitiveProfile, CognitiveBiasType, Strategy models
│   ├── collectors/
│   │   ├── cowrie_collector.py      # Tails Cowrie JSON logs, deduplicates, dispatches
│   │   └── cognitive_bridge.py      # Routes commands to CBDF, stores profiles, broadcasts
│   ├── core/
│   │   ├── config.py                # Pydantic Settings with nested config classes
│   │   ├── db/
│   │   │   ├── models.py            # SQLAlchemy async models (11 tables)
│   │   │   ├── repositories.py      # Generic BaseRepository + specialized repos
│   │   │   ├── cognitive_repository.py  # CognitiveProfile + DeceptionEvent repos
│   │   │   └── session.py           # Async engine, get_db(), get_db_context()
│   │   ├── deployment.py            # Docker-based honeypot deployment manager
│   │   ├── geoip.py                 # GeoIP lookup for attacker IPs
│   │   └── security.py              # JWT, API key auth, RateLimiter
│   └── honeypots/
│       └── base.py                  # SSHHoneypot, HTTPHoneypot, FTPHoneypot, TelnetHoneypot
├── frontend/
│   └── src/
│       ├── pages/                   # Dashboard, Honeypots, Attacks, AIMonitor,
│       │                            # CognitiveDashboard, Settings, Login
│       ├── components/              # AI/, Attacks/, cognitive/, Dashboard/, Honeypots/
│       ├── hooks/                   # useApi.ts, useWebSocket.ts
│       └── contexts/                # AuthContext, NotificationContext
├── deploy/
│   ├── docker/                      # Dockerfiles, nginx configs, docker-compose.prod.yml
│   ├── k8s/                         # Full Kubernetes manifests (10 files)
│   └── monitoring/                  # prometheus.yml, alertmanager.yml, grafana dashboard
├── tests/                           # Unit, integration, and system tests
├── docs/                            # Architecture, deployment, CBDF design, thesis
├── docker-compose.yml               # Dev compose (SQLite, no external services)
├── requirements.txt
├── .env.example
└── start.sh
```

---

## Documentation

| Document | Path |
|---|---|
| Architecture deep-dive | `docs/architecture/ARCHITECTURE.md` |
| Deployment guide | `docs/deployment/DEPLOYMENT.md` |
| CBDF design specification | `docs/design/CBDF_DESIGN_SPEC.md` |
| Adaptive deception strategy | `docs/deception/ADAPTIVE_DECEPTION_STRATEGY.md` |
| CBDF implementation docs | `docs/CBDF_IMPLEMENTATION_DOCS.md` |
| Complete system documentation | `docs/COMPLETE_SYSTEM_DOCUMENTATION.md` |
| System flow diagrams | `docs/SYSTEM_FLOW_DIAGRAMS.md` |
| Quick reference | `docs/QUICK_REFERENCE.md` |
| Novel research gaps analysis | `docs/research/NOVEL_RESEARCH_GAPS_ANALYSIS.md` |

---

## License

MIT License — see [LICENSE](LICENSE) for details.
