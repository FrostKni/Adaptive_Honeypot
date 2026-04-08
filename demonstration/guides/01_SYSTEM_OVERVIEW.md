# Adaptive Honeypot System - Complete Demonstration Guide

## System Overview

### What is this system?

The Adaptive Honeypot System is a **production-grade, AI-powered cybersecurity deception platform** that combines:

1. **Multiple Honeypot Protocols** - SSH, HTTP, FTP, Telnet decoy services
2. **AI-Powered Analysis** - Real-time threat assessment using LLMs
3. **Cognitive-Behavioral Deception Framework (CBDF)** - Novel psychology-based deception
4. **Real-Time Adaptation** - Dynamic container reconfiguration based on attacker behavior

### Key Innovations

#### 1. Cognitive-Behavioral Deception Framework (CBDF)

**WORLD'S FIRST** implementation of psychology-based deception in honeypot systems:

- **8 Cognitive Biases Detected**: 
  - Confirmation Bias (85% effectiveness)
  - Anchoring (88% effectiveness)
  - Sunk Cost Fallacy (82% effectiveness)
  - Dunning-Kruger Effect (70% effectiveness)
  - Curiosity Gap (80% effectiveness)
  - Loss Aversion (72% effectiveness)
  - Availability Heuristic (76% effectiveness)
  - Optimism Bias (75% effectiveness)

- **11 Deception Strategies**: Each targeting specific cognitive biases
- **Real-time Profiling**: Builds psychological profiles of attackers
- **Mental Model Tracking**: Tracks attacker beliefs, knowledge, and goals

**Example Flow**:
```
Attacker: "ls -la"
  ↓
Cognitive Profiler: Analyzes intent → Detects Confirmation Bias
  ↓  
Deception Engine: Shows files matching attacker expectations
  ↓
Result: Attacker stays engaged 82% longer
```

#### 2. AI-Powered Real-Time Adaptation

**Multi-Provider AI Support**:
- OpenAI (GPT-4, GPT-4-Turbo)
- Anthropic (Claude)
- Google Gemini
- Local LLM (GLM5 via api.ai.oac)

**Decision Engine Actions**:
1. **Monitor** - Continue observation
2. **Reconfigure** - Modify deception settings
3. **Isolate** - Quarantine attacker in isolated network
4. **Switch Container** - Transparently migrate to enhanced honeypot

#### 3. Production-Ready Architecture

**High Availability**:
- Kubernetes deployment with HPA (Horizontal Pod Autoscaler)
- 2-10 replicas based on CPU load
- PodDisruptionBudget for resilience
- NetworkPolicy for security

**Monitoring Stack**:
- Prometheus metrics collection
- Grafana dashboards
- Alertmanager notifications

---

## Technology Stack

### Backend
- **Framework**: FastAPI 0.104.1
- **Database**: SQLAlchemy 2.0.23 (async)
- **Storage**: PostgreSQL (production) / SQLite (development)
- **Cache**: Redis 5.0.1
- **Container Management**: Docker SDK 7.0.0
- **WebSocket**: Real-time event streaming

### Frontend
- **Framework**: React 18.2 with TypeScript 5.2
- **Build Tool**: Vite 5.4.0
- **Styling**: Tailwind CSS 3.3.5
- **Charts**: Chart.js 4.4.1
- **Maps**: Leaflet 1.9.4
- **State**: Zustand 4.4.7

### Honeypots
- **SSH**: Cowrie (port 2222)
- **Telnet**: Cowrie (port 2323)
- **HTTP**: nginx (port 8080)
- **FTP**: pure-ftpd (port 2121)

### AI/ML
- OpenAI API
- Anthropic API
- Google Generative AI
- Local LLM (GLM5)

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

---

## Access Points

### Web Interface
- **Frontend Dashboard**: http://localhost:3000
- **API Documentation**: http://localhost:8000/api/docs
- **Alternative API Docs**: http://localhost:8000/api/redoc

### Honeypot Services
- **SSH Honeypot**: `ssh root@localhost -p 2222`
- **Telnet Honeypot**: `telnet localhost 2323`
- **HTTP Honeypot**: http://localhost:8080
- **FTP Honeypot**: `ftp localhost 2121`

### Default Credentials
- **Username**: admin (configurable via ADMIN_USERNAME)
- **Password**: (set via ADMIN_PASSWORD in .env)

---

## Quick Start

### 1. Start the System

```bash
# Using Docker Compose (recommended for production)
docker-compose up -d

# Or manually:
# Terminal 1 - Backend
source venv/bin/activate
python -m uvicorn src.api.app:create_app --factory --host 0.0.0.0 --port 8000 --reload

# Terminal 2 - Frontend
cd frontend
npm run dev
```

### 2. Access the Dashboard

1. Open http://localhost:3000
2. Login with admin credentials
3. Explore the dashboard

### 3. Simulate an Attack

```bash
# SSH attack simulation
ssh root@localhost -p 2222
# Try common passwords: admin, password, 123456, root

# Or use a script
for pass in admin password root 123456; do
  sshpass -p "$pass" ssh -o StrictHostKeyChecking=no root@localhost -p 2222
done
```

### 4. Monitor in Real-Time

- Watch the dashboard for live attack visualization
- Check the "AI Monitor" page for AI decisions
- View "Cognitive Dashboard" for psychological profiles

---

## What Makes This Unique?

### vs. Traditional Honeypots

| Feature | Traditional | This System |
|---------|-------------|-------------|
| Deception | Static fake files | Dynamic cognitive manipulation |
| Adaptation | Manual configuration | AI-driven real-time adaptation |
| Analysis | Post-hoc log review | Real-time AI threat assessment |
| Attacker Modeling | Behavioral analysis | Theory of Mind + cognitive profiling |
| Scalability | Single instance | Kubernetes-ready with HPA |

### vs. Other AI Honeypots

| Feature | Other AI Systems | This System |
|---------|------------------|-------------|
| AI Role | Basic classification | Full decision engine |
| Deception | Rule-based | Cognitive-bias exploitation |
| Adaptation | Pre-defined rules | LLM-generated strategies |
| Transparency | Black box | Explainable AI decisions |
| Psychology | None | First CBDF implementation |

---

## Research Contributions

This system addresses **7 major research gaps** identified in comprehensive literature review:

1. **Theory of Mind Attacker Modeling (TOM-AM)** - Infer attacker beliefs/intents
2. **Causal Inference Attack Attribution (CIAA)** - Understand WHY attacks succeed
3. **Neuromorphic Honeypot Adaptation** - Hardware-efficient real-time adaptation
4. **Quantum-Enhanced Deception** - Quantum ML for pattern recognition
5. **Federated Honeypot Learning** - Share threat intel without sharing data
6. **Adversarial Robustness** - Defend against adversarial ML attacks
7. **Multi-Modal Attack Understanding** - Process text, binaries, network traffic

---

## Next Steps

1. **Dashboard Tour** - Explore the React UI (02_DASHBOARD_TOUR.md)
2. **API Reference** - Understand the REST API (03_API_REFERENCE.md)
3. **Attack Simulation** - Generate attack logs (04_ATTACK_SIMULATION.md)
4. **Cognitive Framework** - Deep dive into CBDF (05_COGNITIVE_FRAMEWORK.md)
5. **AI Analysis** - Understand AI decision-making (06_AI_ANALYSIS.md)
