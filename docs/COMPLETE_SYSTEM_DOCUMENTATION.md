# Adaptive Honeypot System - Complete Documentation

## Executive Summary

The Adaptive Honeypot System is a production-grade, AI-powered cybersecurity deception platform that dynamically adapts its behavior based on attacker interactions. It combines multiple honeypot protocols (SSH, HTTP, FTP, Telnet) with real-time AI analysis and a cognitive-behavioral deception framework to maximize intelligence gathering while keeping attackers engaged.

---

## Table of Contents

1. [System Architecture Overview](#1-system-architecture-overview)
2. [Core Components](#2-core-components)
3. [Data Flow Diagrams](#3-data-flow-diagrams)
4. [AI-Powered Analysis System](#4-ai-powered-analysis-system)
5. [Cognitive-Behavioral Deception Framework](#5-cognitive-behavioral-deception-framework)
6. [Deployment System](#6-deployment-system)
7. [Database Schema](#7-database-schema)
8. [API Reference](#8-api-reference)
9. [Real-Time Communication](#9-real-time-communication)
10. [Alerting System](#10-alerting-system)
11. [Frontend Dashboard](#11-frontend-dashboard)
12. [Configuration](#12-configuration)
13. [Security Considerations](#13-security-considerations)
14. [Deployment Guide](#14-deployment-guide)

---

## 1. System Architecture Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          ADAPTIVE HONEYPOT SYSTEM                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐ │
│  │   ATTACKER  │───▶│   HONEYPOT  │───▶│   LOG       │───▶│    AI       │ │
│  │   (Internet)│    │  CONTAINERS │    │  COLLECTOR  │    │  ANALYZER   │ │
│  └─────────────┘    └─────────────┘    └─────────────┘    └──────┬──────┘ │
│                                                                  │         │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐          │         │
│  │  FRONTEND   │◀──▶│   FASTAPI   │◀──▶│  DATABASE   │◀─────────┤         │
│  │ (React/TS)  │    │   BACKEND   │    │  (SQLite/   │          │         │
│  └─────────────┘    └──────┬──────┘    │  PostgreSQL)│          │         │
│                            │           └─────────────┘          │         │
│                            │                                    │         │
│  ┌─────────────┐           │           ┌─────────────┐          │         │
│  │  WEBSOCKET  │◀──────────┴──────────▶│  COGNITIVE  │◀─────────┘         │
│  │  REAL-TIME  │                       │   ENGINE    │                    │
│  └─────────────┘                       └─────────────┘                    │
│                                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                    │
│  │   ALERT     │◀───│  DECISION   │◀───│  THREAT     │                    │
│  │  MANAGER    │    │  EXECUTOR   │    │  INTEL      │                    │
│  └─────────────┘    └─────────────┘    └─────────────┘                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Component Interaction Flow

```
Attacker connects → Honeypot Container → Log Collector → AI Analysis
                                                           ↓
WebSocket Broadcast ← FastAPI Backend ← Database ← Cognitive Profiler
                                                           ↓
                                    Decision Executor → Container Adaptation
                                                           ↓
                                         Alert Manager → Notifications
```

---

## 2. Core Components

### 2.1 Honeypot Containers (Docker-Based)

The system uses Docker containers for honeypot isolation and management:

| Type   | Image                   | Port  | Purpose                          |
|--------|-------------------------|-------|----------------------------------|
| SSH    | cowrie/cowrie:latest    | 2222  | SSH brute force, command capture |
| HTTP   | nginx:alpine            | 8080  | Web attack monitoring            |
| FTP    | stilliard/pure-ftpd     | 2121  | FTP credential capture           |
| Telnet | cowrie/cowrie:latest    | 2323  | IoT/router attack monitoring     |

**Implementation:** `src/honeypots/base.py`

```python
class SSHHoneypot:
    """SSH Honeypot using Cowrie - captures:
    - Brute force attempts
    - Executed commands
    - Downloaded files
    - SSH keys used
    """
```

### 2.2 FastAPI Backend

The central orchestration layer providing:

- **REST API:** Full CRUD operations for honeypots, sessions, attacks
- **WebSocket Server:** Real-time event streaming to frontend
- **Middleware Stack:** Request ID, Timing, Error Handling, CORS, GZip
- **Authentication:** JWT tokens + API Key support

**Entry Point:** `src/api/app.py`

### 2.3 Log Collector

Real-time log ingestion from Docker containers:

- Polls container logs every 2 seconds
- Parses Cowrie JSON log format
- Extracts source IPs, commands, credentials
- Routes events to AI analysis and WebSocket broadcast

**Implementation:** `src/collectors/cowrie_collector.py`

### 2.4 AI Monitoring Service

Central AI orchestration:

- **Event Queue:** Processes attack events asynchronously
- **LLM Client:** Connects to local GLM5 or external providers
- **Decision Engine:** Generates threat assessments and actions
- **Activity Tracking:** Maintains history of AI decisions

**Implementation:** `src/ai/monitoring.py`

### 2.5 Decision Executor

Translates AI decisions into Docker actions:

| Action          | Description                                    |
|-----------------|------------------------------------------------|
| `monitor`       | Continue observation without changes           |
| `reconfigure`   | Modify container deception settings            |
| `isolate`       | Move attacker to quarantined network           |
| `switch_container` | Transparently migrate to enhanced honeypot  |

**Implementation:** `src/ai/decision_executor.py`

### 2.6 Cognitive Deception Engine

Advanced psychological profiling:

- **Cognitive Profiler:** Builds psychological profiles from behavior
- **Bias Detector:** Identifies exploitable cognitive biases
- **Strategy Library:** Pre-defined deception tactics
- **Response Generator:** Creates deceptive outputs

**Implementation:** `src/cognitive/engine.py`, `src/cognitive/profiler.py`

---

## 3. Data Flow Diagrams

### 3.1 Attack Ingestion Flow

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│ Attacker │────▶│ Honeypot │────▶│   Log    │────▶│  Event   │
│   SSH    │     │Container │     │Collector │     │  Parser  │
└──────────┘     └──────────┘     └──────────┘     └────┬─────┘
                                                       │
                    ┌──────────────────────────────────┼──────────────────┐
                    │                                  │                  │
                    ▼                                  ▼                  ▼
            ┌──────────┐                      ┌──────────┐       ┌──────────┐
            │ Database │                      │    AI    │       │WebSocket │
            │  Store   │                      │ Analysis │       │ Broadcast│
            └──────────┘                      └──────────┘       └──────────┘
```

### 3.2 AI Decision Flow

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ Attack Event │────▶│  LLM Prompt  │────▶│  AI Response │
│   (Queued)   │     │  Builder     │     │   Parser     │
└──────────────┘     └──────────────┘     └──────┬───────┘
                                                   │
                    ┌──────────────────────────────┼──────────────────┐
                    │                              │                  │
                    ▼                              ▼                  ▼
            ┌──────────────┐              ┌──────────────┐   ┌──────────────┐
            │   Decision   │              │   Threat     │   │   Activity   │
            │   Executor   │              │   Level      │   │    Log       │
            └──────────────┘              └──────────────┘   └──────────────┘
                    │
    ┌───────────────┼───────────────┐
    │               │               │
    ▼               ▼               ▼
┌────────┐   ┌────────────┐   ┌────────┐
│Monitor │   │Reconfigure │   │Isolate │
└────────┘   └────────────┘   └────────┘
```

### 3.3 Cognitive Deception Flow

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Command    │────▶│   Signal     │────▶│    Bias      │
│   Received   │     │  Extraction  │     │  Detection   │
└──────────────┘     └──────────────┘     └──────┬───────┘
                                                   │
                    ┌──────────────────────────────┼──────────────────┐
                    │                              │                  │
                    ▼                              ▼                  ▼
            ┌──────────────┐              ┌──────────────┐   ┌──────────────┐
            │   Strategy   │              │   Mental     │   │  Cognitive   │
            │  Selection   │              │   Model      │   │   Profile    │
            └──────┬───────┘              └──────────────┘   └──────────────┘
                   │
                   ▼
           ┌──────────────┐
           │   Deceptive  │
           │   Response   │
           └──────────────┘
```

---

## 4. AI-Powered Analysis System

### 4.1 Multi-Provider Support

The system supports multiple AI providers with automatic fallback:

```
Primary Provider (OpenAI/Anthropic/Gemini/Local)
         ↓ (if fails)
    Fallback Providers
         ↓ (if all fail)
   Rule-Based Analyzer (guaranteed)
```

### 4.2 Analysis Schema

The AI generates structured analysis with:

```json
{
  "attack_sophistication": "low|medium|high",
  "attacker_skill_level": "script_kiddie|intermediate|advanced|expert",
  "attack_objectives": ["reconnaissance", "exploitation", "data_theft"],
  "threat_level": "low|medium|high|critical",
  "recommended_interaction_level": "low|medium|high",
  "deception_strategies": ["fake_files", "delayed_responses", "fake_users"],
  "configuration_changes": {},
  "confidence": 0.85,
  "reasoning": "Brief explanation",
  "mitre_attack_ids": ["T1110", "T1059"]
}
```

### 4.3 Local LLM Integration

The system integrates with local LLM via `api.ai.oac`:

```python
class LocalLLMClient:
    base_url = "https://api.ai.oac/v1"
    model = "GLM5"
    
    async def generate(prompt, system_prompt, temperature, max_tokens):
        # Returns structured analysis
```

### 4.4 Rule-Based Fallback

When AI providers are unavailable:

```python
class RuleBasedAnalyzer:
    def analyze(events):
        # Pattern detection
        has_downloads = any("wget" in c or "curl" in c for c in commands)
        has_exploit = any("chmod" in c or "bash" in c for c in commands)
        
        # Threat classification
        if has_exploit or high_severity > 5:
            sophistication = "high"
            action = "reconfigure"
```

---

## 5. Cognitive-Behavioral Deception Framework

### 5.1 Cognitive Biases Detected

| Bias Type               | Detection Signals                              |
|-------------------------|-----------------------------------------------|
| Confirmation Bias       | Repeated similar commands, low exploration    |
| Sunk Cost               | Long sessions, multiple failed attempts       |
| Dunning-Kruger          | Complexity mismatch, no reconnaissance       |
| Anchoring               | Early session command influence               |
| Curiosity Gap           | Hidden file exploration, breadcrumb following |
| Loss Aversion           | Protective behavior, backup creation          |
| Availability Heuristic  | Following obvious paths                       |

### 5.2 Deception Strategies

Each strategy targets specific biases:

```python
DeceptionStrategy(
    name="confirm_expected_files",
    bias_type=CognitiveBiasType.CONFIRMATION_BIAS,
    trigger_commands=["ls", "cat", "find", "grep"],
    effectiveness_score=0.85,
    response_template={
        "type": "confirm_expectations",
        "add_expected_files": True,
        "match_attacker_beliefs": True,
    }
)
```

### 5.3 Response Generation

Deceptive responses are generated based on:

- **Attacker's Mental Model:** Beliefs, knowledge, goals
- **Active Biases:** Detected cognitive vulnerabilities
- **Session Context:** Commands executed, duration, errors
- **Deception History:** Previous tactics used

Example fake file templates:

```python
FILE_TEMPLATES = {
    "passwd": "root:x:0:0:root:/root:/bin/bash\nadmin:x:1000:1000:Admin...",
    "interesting_file": "# Database Configuration\nDB_PASS=Sup3rS3cr3t...",
    "bash_history": "ls -la\ncat /etc/shadow\nsudo -l...",
}
```

### 5.4 Cognitive Metrics

The profiler tracks:

| Metric                | Calculation Method                    |
|-----------------------|--------------------------------------|
| Overconfidence Score  | Command complexity vs skill evidence |
| Persistence Score     | Session duration, failed attempts    |
| Tunnel Vision Score   | Single directory focus               |
| Curiosity Score       | Exploration diversity                |
| Error Tolerance       | Commands after errors                |
| Learning Rate         | Behavior change over time            |

---

## 6. Deployment System

### 6.1 Docker Container Management

```python
class HoneypotDeploymentManager:
    # Container lifecycle
    async def deploy(honeypot_id, name, honeypot_type, port, config)
    async def stop(honeypot_id)
    async def start(honeypot_id)
    async def remove(honeypot_id)
    async def restart(honeypot_id)
    async def get_status(honeypot_id)
    async def get_logs(honeypot_id, lines)
```

### 6.2 Container Labels

All containers are tagged with:

```yaml
labels:
  honeypot.id: "honeypot-abc123"
  honeypot.name: "SSH Honeypot 1"
  honeypot.type: "ssh"
  honeypot.port: "2222"
```

### 6.3 Network Architecture

```
┌─────────────────────────────────────────┐
│          honeypot-network               │
│        (Bridge Driver)                  │
├─────────────────────────────────────────┤
│  ┌─────────┐  ┌─────────┐  ┌─────────┐ │
│  │  SSH    │  │  HTTP   │  │   FTP   │ │
│  │Container│  │Container│  │Container│ │
│  └─────────┘  └─────────┘  └─────────┘ │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│       honeypot-isolated                 │
│      (Internal Only - Quarantine)       │
├─────────────────────────────────────────┤
│  ┌─────────────────────────────────────┐│
│  │  Isolated Attacker Containers       ││
│  │  (No external network access)       ││
│  └─────────────────────────────────────┘│
└─────────────────────────────────────────┘
```

---

## 7. Database Schema

### 7.1 Core Tables

```
┌─────────────────┐     ┌─────────────────┐
│   honeypots     │────<│    sessions     │
├─────────────────┤     ├─────────────────┤
│ id (PK)         │     │ id (PK)         │
│ name            │     │ honeypot_id(FK) │
│ type            │     │ source_ip       │
│ status          │     │ username        │
│ port            │     │ commands (JSON) │
│ container_id    │     │ attack_type     │
│ config (JSON)   │     │ severity        │
│ total_sessions  │     │ threat_level    │
└─────────────────┘     └────────┬────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        │                        │                        │
        ▼                        ▼                        ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ attack_events   │     │cognitive_profiles│    │ deception_events│
├─────────────────┤     ├─────────────────┤     ├─────────────────┤
│ id (PK)         │     │ id (PK)         │     │ id (PK)         │
│ session_id (FK) │     │ session_id (FK) │     │ session_id (FK) │
│ event_type      │     │ detected_biases │     │ bias_type       │
│ timestamp       │     │ mental_model    │     │ strategy_name   │
│ data (JSON)     │     │ overconfidence  │     │ trigger_command │
│ severity        │     │ deception_rate  │     │ effectiveness   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

### 7.2 Key Models

**Honeypot Model:**
```python
class Honeypot(Base):
    id: str
    name: str
    type: HoneypotType  # SSH, HTTP, FTP, TELNET
    status: HoneypotStatus  # RUNNING, STOPPED, ADAPTING
    port: int
    container_id: str
    config: Dict[str, Any]
    interaction_level: InteractionLevel
```

**Session Model:**
```python
class Session(Base):
    id: str
    honeypot_id: str
    source_ip: str
    source_country: str
    username: str
    commands: List[str]
    attack_type: AttackType
    severity: AttackSeverity
    threat_level: ThreatLevel
    terminal_log: str  # Session replay
```

---

## 8. API Reference

### 8.1 Honeypot Endpoints

| Method | Endpoint              | Description                    |
|--------|----------------------|--------------------------------|
| GET    | /api/v1/honeypots    | List all honeypots (paginated) |
| POST   | /api/v1/honeypots    | Deploy new honeypot            |
| GET    | /api/v1/honeypots/{id}| Get specific honeypot         |
| DELETE | /api/v1/honeypots/{id}| Remove honeypot              |
| POST   | /api/v1/honeypots/{id}/restart| Restart container     |
| GET    | /api/v1/honeypots/{id}/health| Health metrics       |
| GET    | /api/v1/honeypots/{id}/logs| Container logs          |

### 8.2 Attack Endpoints

| Method | Endpoint              | Description                    |
|--------|----------------------|--------------------------------|
| GET    | /api/v1/sessions     | List attack sessions           |
| GET    | /api/v1/sessions/{id}| Get session details            |
| GET    | /api/v1/sessions/{id}/replay| Terminal replay           |
| GET    | /api/v1/attacks      | Attack event feed              |

### 8.3 Analytics Endpoints

| Method | Endpoint                    | Description                |
|--------|----------------------------|----------------------------|
| GET    | /api/v1/analytics/dashboard| Dashboard statistics       |
| GET    | /api/v1/analytics/timeline | Attack timeline            |
| GET    | /api/v1/analytics/attackers| Top attacker IPs           |

### 8.4 Cognitive Endpoints

| Method | Endpoint                      | Description              |
|--------|------------------------------|--------------------------|
| GET    | /api/v1/cognitive/{session_id}| Cognitive profile       |
| GET    | /api/v1/cognitive/{session_id}/biases| Detected biases |

### 8.5 AI Monitoring Endpoints

| Method | Endpoint                    | Description              |
|--------|----------------------------|--------------------------|
| GET    | /api/v1/ai-monitoring/status| AI service status       |
| GET    | /api/v1/ai-monitoring/activities| Recent activities   |
| GET    | /api/v1/ai-monitoring/decisions| AI decisions log     |

---

## 9. Real-Time Communication

### 9.1 WebSocket Connection

```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/ws');

// Connection flow
ws.onopen → Send: {"type": "subscribe", "channels": ["attacks", "ai_decisions"]}
ws.onmessage → Receive: {"type": "attack_event", "data": {...}}
```

### 9.2 Event Types

| Type              | Description                        |
|-------------------|-----------------------------------|
| `attack_event`    | New attack detected               |
| `session_start`   | Attacker connected                |
| `session_end`     | Attacker disconnected             |
| `ai_decision`     | AI analysis completed             |
| `adaptation`      | Honeypot reconfigured             |
| `alert`           | Security alert triggered          |

### 9.3 Channel Subscriptions

```javascript
// Subscribe to specific honeypot events
{"type": "subscribe", "channel": "honeypot:abc123"}

// Subscribe to AI decisions
{"type": "subscribe", "channel": "ai_decisions"}

// Subscribe to all attacks
{"type": "subscribe", "channel": "attacks"}
```

---

## 10. Alerting System

### 10.1 Supported Channels

| Channel | Configuration Required                    |
|---------|------------------------------------------|
| Email   | SMTP host, user, password, recipients    |
| Slack   | Webhook URL                              |
| Discord | Webhook URL                              |
| Webhook | Custom endpoint URL, optional headers    |

### 10.2 Alert Types

```python
class Alert:
    alert_type: str  # "attack_detected", "adaptation", "critical"
    title: str
    message: str
    priority: AlertPriority  # LOW, MEDIUM, HIGH, CRITICAL
    honeypot_id: str
    source_ip: str
    timestamp: datetime
    metadata: Dict[str, Any]
```

### 10.3 Rate Limiting

Alerts are rate-limited to prevent spam:

```python
# Default: 1 alert per key per 5 minutes
rate_limit_seconds = 300

# Key format: "{alert_type}:{source_ip}"
alert_key = f"attack_detected:192.168.1.100"
```

---

## 11. Frontend Dashboard

### 11.1 Technology Stack

- **React 18** with TypeScript
- **Vite** for build tooling
- **Tailwind CSS** for styling
- **Recharts** for visualizations
- **WebSocket** for real-time updates

### 11.2 Page Structure

```
/frontend/src/
├── pages/
│   ├── Dashboard.tsx      # Main overview
│   ├── Honeypots.tsx      # Honeypot management
│   ├── Sessions.tsx       # Attack sessions
│   ├── Analytics.tsx      # Statistics & trends
│   ├── AIActivity.tsx     # AI monitoring
│   └── Settings.tsx       # Configuration
├── components/
│   ├── AttackFeed.tsx     # Real-time attack stream
│   ├── SessionReplay.tsx  # Terminal playback
│   ├── ThreatMap.tsx      # Geographic visualization
│   └── AIMonitor.tsx      # AI decision display
└── hooks/
    ├── useWebSocket.ts    # WebSocket connection
    └── useApi.ts          # REST API client
```

### 11.3 Real-Time Updates

```typescript
// WebSocket hook
const { events, isConnected } = useWebSocket('/api/v1/ws');

// Real-time attack feed
events.map(event => (
  <AttackCard 
    key={event.id}
    type={event.event_type}
    source={event.source_ip}
    timestamp={event.timestamp}
  />
));
```

---

## 12. Configuration

### 12.1 Environment Variables

Core configuration categories:

```bash
# Application
APP_NAME=Adaptive Honeypot System
APP_VERSION=2.0.0
ENVIRONMENT=development|production
DEBUG=true|false

# Database
DB_HOST=localhost
DB_PORT=5432
DB_USER=honeypot
DB_PASSWORD=secret
DB_NAME=adaptive_honeypot

# AI Providers
AI_PROVIDER=openai|anthropic|gemini|local
AI_MODEL=gpt-4-turbo-preview
OPENAI_API_KEY=sk-...

# Security
SECURITY_JWT_SECRET=your-secret-key
SECURITY_JWT_EXPIRE_MINUTES=60

# Honeypot Limits
HONEYPOT_MAX_INSTANCES=20
HONEYPOT_ADAPTATION_THRESHOLD=5
HONEYPOT_SESSION_TIMEOUT=3600

# Alerting
ALERT_SMTP_HOST=smtp.example.com
ALERT_SLACK_WEBHOOK_URL=https://hooks.slack.com/...
```

### 12.2 Pydantic Settings

```python
class AppSettings(BaseSettings):
    app_name: str = "Adaptive Honeypot System"
    app_version: str = "2.0.0"
    environment: str = "development"
    debug: bool = True
    
    # Nested settings
    database: DatabaseSettings
    redis: RedisSettings
    ai: AISettings
    security: SecuritySettings
    honeypot: HoneypotSettings
    alerting: AlertingSettings
```

---

## 13. Security Considerations

### 13.1 Authentication

Two authentication methods:

1. **JWT Bearer Token:**
```python
# Login endpoint returns token
POST /api/v1/auth/login
→ {"access_token": "eyJ...", "token_type": "bearer"}

# Use in requests
Authorization: Bearer eyJ...
```

2. **API Key:**
```python
# Admin-created API keys
X-API-Key: hp_live_abc123...
```

### 13.2 Authorization Scopes

| Scope             | Access                          |
|-------------------|---------------------------------|
| `honeypots:read`  | View honeypots                  |
| `honeypots:write` | Create, modify, delete honeypots|
| `sessions:read`   | View attack sessions            |
| `analytics:read`  | View analytics                  |
| `admin`           | Full access                     |

### 13.3 Rate Limiting

```python
# Default limits
rate_limit_requests = 100
rate_limit_window = 60  # seconds

# API key specific
api_key.rate_limit = 1000  # requests per window
```

### 13.4 Container Isolation

- All honeypots run in isolated Docker network
- Quarantine network has no external access
- Resource limits per container (CPU, memory)

---

## 14. Deployment Guide

### 14.1 Quick Start (Docker Compose)

```bash
# Clone and configure
git clone https://github.com/FrostKni/Adaptive_Honeypot.git
cd Adaptive_Honeypot
cp .env.example .env
# Edit .env with your settings

# Start all services
docker-compose up -d

# Access
# Dashboard: http://localhost:3000
# API Docs: http://localhost:8000/api/docs
```

### 14.2 Production Deployment (Kubernetes)

```bash
# Apply Kubernetes manifests
kubectl apply -f deploy/k8s/namespace.yaml
kubectl apply -f deploy/k8s/secrets.yaml
kubectl apply -f deploy/k8s/configmap.yaml
kubectl apply -f deploy/k8s/backend.yaml
kubectl apply -f deploy/k8s/frontend.yaml
kubectl apply -f deploy/k8s/ingress.yaml
```

### 14.3 Health Checks

```bash
# API health
curl http://localhost:8000/health

# Readiness check
curl http://localhost:8000/ready

# Container status
docker ps --filter label=honeypot.id
```

### 14.4 Monitoring Integration

Prometheus metrics available at `/metrics`:

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'honeypot'
    static_configs:
      - targets: ['backend:8000']
```

Grafana dashboards available in `deploy/monitoring/grafana/`.

---

## Appendix A: File Structure

```
Adaptive_Honeypot/
├── src/                          # Backend source
│   ├── ai/                       # AI analysis system
│   │   ├── analyzer.py           # Multi-provider AI analyzer
│   │   ├── monitoring.py         # Real-time AI service
│   │   ├── decision_executor.py  # Docker action executor
│   │   └── providers/            # AI provider implementations
│   ├── alerting/                 # Multi-channel alerts
│   │   └── channels.py           # Email, Slack, Discord, Webhook
│   ├── api/                      # FastAPI application
│   │   ├── app.py                # Application factory
│   │   └── v1/endpoints/         # API routes
│   ├── cognitive/                # Deception framework
│   │   ├── engine.py             # Deception orchestration
│   │   ├── profiler.py           # Cognitive profiling
│   │   └── models.py             # Data models
│   ├── collectors/               # Log collection
│   │   ├── cowrie_collector.py   # SSH honeypot logs
│   │   └── cognitive_bridge.py   # Cognitive integration
│   ├── core/                     # Core infrastructure
│   │   ├── config.py             # Settings management
│   │   ├── deployment.py         # Docker orchestration
│   │   ├── security.py           # Auth & authorization
│   │   ├── geoip.py              # IP geolocation
│   │   └── db/                   # Database layer
│   │       ├── models.py         # SQLAlchemy models
│   │       ├── repositories.py   # Data access
│   │       └── session.py        # Session management
│   └── honeypots/                # Honeypot implementations
│       └── base.py               # SSH, HTTP, FTP, Telnet
├── frontend/                     # React dashboard
│   └── src/
│       ├── pages/                # Page components
│       ├── components/           # UI components
│       ├── hooks/                # Custom hooks
│       └── types/                # TypeScript types
├── deploy/                       # Deployment configs
│   ├── docker/                   # Docker Compose & Dockerfiles
│   ├── k8s/                      # Kubernetes manifests
│   └── monitoring/               # Prometheus & Grafana
├── tests/                        # Test suite
├── docs/                         # Documentation
├── data/                         # Data storage
├── logs/                         # Log files
├── .env.example                  # Environment template
├── requirements.txt              # Python dependencies
└── docker-compose.yml            # Local development
```

---

## Appendix B: Key Commands

```bash
# Development
python -m uvicorn src.api.app:app --reload --port 8000

# Run tests
pytest tests/ -v --cov=src

# Database migrations
alembic revision --autogenerate -m "description"
alembic upgrade head

# Docker operations
docker-compose up -d
docker-compose logs -f backend
docker-compose down

# Kubernetes
kubectl get pods -n honeypot
kubectl logs -f deployment/backend -n honeypot
kubectl scale deployment backend --replicas=3 -n honeypot
```

---

## Appendix C: Troubleshooting

| Issue                          | Solution                                      |
|--------------------------------|-----------------------------------------------|
| Container won't start          | Check Docker logs, verify port availability   |
| AI analysis failing            | Verify API keys, check LLM endpoint          |
| WebSocket not connecting       | Check CORS settings, verify proxy config     |
| Database errors                | Run migrations, check connection string      |
| Alerts not sending             | Verify channel config, check rate limits     |
| High memory usage              | Adjust container limits, check log retention |

---

*Documentation Version: 2.0.0*
*Last Updated: March 2026*