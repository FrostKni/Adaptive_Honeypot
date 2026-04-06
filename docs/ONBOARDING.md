# Adaptive Honeypot System - Developer Onboarding Guide

> Generated from knowledge graph analysis on 2026-03-25

## Project Overview

**Adaptive Honeypot System v2.0** is a production-grade, AI-powered honeypot network with real-time behavioral adaptation and a novel Cognitive-Behavioral Deception Framework (CBDF) for manipulating attacker decision-making.

### Key Technologies
- **Languages**: Python 3.11+, TypeScript
- **Frameworks**: FastAPI, React, SQLAlchemy, Docker, Vite
- **AI Providers**: OpenAI, Anthropic, Gemini (with automatic fallback)

### Core Capabilities
- Multi-protocol honeypots (SSH, HTTP, FTP, Telnet)
- AI-driven real-time adaptation
- Cognitive-behavioral deception (8 bias types, 11 strategies)
- Full session replay with terminal recording
- Multi-channel alerting (email, Slack, Discord, webhooks)

---

## Architecture Layers

The system is organized into 13 logical layers:

### Backend Layers

| Layer | Files | Description |
|-------|-------|-------------|
| **API Endpoints** | 14 | REST endpoints for honeypot management, attacks, sessions, cognitive data |
| **API Core** | 3 | FastAPI application setup, middleware, routing configuration |
| **AI Layer** | 6 | AI monitoring, decision execution, multi-provider LLM integration |
| **Cognitive Deception** | 4 | CBDF engine, profiler, bias detection, deception strategies |
| **Data Collectors** | 3 | Cowrie log collection, cognitive integration bridge |
| **Data Layer** | 5 | SQLAlchemy models, repositories, database session management |
| **Core Services** | 5 | Configuration, security, GeoIP lookup, deployment utilities |
| **Honeypot Handlers** | 2 | Base classes for SSH, HTTP, FTP, Telnet honeypots |
| **Alerting** | 2 | Multi-channel alerting (email, Slack, Discord, webhooks) |

### Frontend Layers

| Layer | Files | Description |
|-------|-------|-------------|
| **UI Components** | 18 | React components for dashboard, attack monitoring, cognitive viz |
| **State Management** | 4 | React hooks and context providers |
| **Type Definitions** | 1 | TypeScript interfaces and types |

---

## Guided Tour

### Step 1: Entry Point & Configuration
**Files**: `src/api/app.py`, `src/core/config.py`

Start with the FastAPI application setup. The `app.py` bootstraps the entire backend:
- Middleware stack (request ID, timing, error handling)
- Router aggregation for all API endpoints
- Database session management
- WebSocket endpoint mounting

The `config.py` uses Pydantic Settings for environment-based configuration with validation.

### Step 2: Database Models
**Files**: `src/core/db/models.py`, `src/core/db/session.py`

The data layer defines 14 SQLAlchemy models:
- **Core**: Honeypot, Session, AttackEvent, Adaptation, HealthRecord, Alert, ThreatIntelligence, APIKey, AuditLog
- **Cognitive**: CognitiveProfileDB, DeceptionEventDB, DetectedBias, MentalModelSnapshot, BiasSignal

Session management uses async SQLAlchemy with connection pooling.

### Step 3: Honeypot Infrastructure
**Files**: `src/honeypots/base.py`, `src/core/deployment.py`

Base classes define the contract for honeypot implementations:
- `BaseHoneypot` abstract class with protocol-specific subclasses
- Docker SDK integration for container lifecycle management
- Dynamic reconfiguration (ports, banners, difficulty)

### Step 4: Log Collection Pipeline
**Files**: `src/collectors/cowrie_collector.py`, `src/collectors/cognitive_bridge.py`

Data flow:
1. `CowrieLogCollector` tails JSON logs from Cowrie containers
2. Events are deduplicated and parsed
3. `CognitiveIntegrationBridge` routes events to the CBDF engine
4. WebSocket broadcast pushes real-time updates to clients

### Step 5: AI Monitoring Service
**Files**: `src/ai/monitoring.py`, `src/ai/decision_executor.py`, `src/ai/analyzer.py`

The AI layer provides:
- `AIMonitoringService`: Main orchestration for threat analysis
- `DecisionExecutor`: Docker API calls for reconfigure/isolate/switch
- `EnhancedAIAnalyzer`: Multi-provider LLM with fallback chain
- `LocalLLMClient`: Integration with local LLM APIs

### Step 6: Cognitive Deception Engine
**Files**: `src/cognitive/engine.py`, `src/cognitive/profiler.py`, `src/cognitive/models.py`

The CBDF (Cognitive-Behavioral Deception Framework):
- **Bias Detection**: 8 cognitive biases (confirmation, anchoring, sunk cost, Dunning-Kruger, availability, loss aversion, authority, curiosity)
- **Deception Strategies**: 11 strategies targeting specific biases
- **Profiling**: Real-time psychological profile building from behavioral signals

### Step 7: Alerting System
**Files**: `src/alerting/channels.py`

Multi-channel alerting with:
- `AlertManager`: Central routing with rate limiting
- Channel implementations: Email (SMTP), Slack, Discord, Webhook
- Priority-based formatting (critical, high, medium, low)

### Step 8: API Endpoints
**Files**: `src/api/v1/endpoints/honeypots.py`, `src/api/v1/endpoints/attacks.py`, `src/api/v1/endpoints/cognitive.py`

Key endpoint groups:
- **Honeypots**: CRUD operations, status, reconfiguration
- **Attacks**: Event listing, session replay, analytics
- **Cognitive**: Profile viewing, bias analysis, deception events
- **AI Monitoring**: Decision history, execution status
- **WebSocket**: Real-time event streaming

### Step 9: Frontend Dashboard
**Files**: `frontend/src/App.tsx`, `frontend/src/pages/Dashboard.tsx`, `frontend/src/pages/CognitiveDashboard.tsx`

React frontend structure:
- React Router with protected routes
- React Query for data fetching
- TailwindCSS for styling
- Real-time WebSocket updates

### Step 10: Real-time Data Flow
**Files**: `frontend/src/hooks/useWebSocket.ts`, `frontend/src/hooks/useApi.ts`, `frontend/src/contexts/AuthContext.tsx`

Data flow architecture:
- `useWebSocket`: Connection management with auto-reconnect
- `useApi`: React Query wrappers for all API calls
- `AuthProvider`: JWT token management and auth state

---

## Key Classes Reference

### AI Layer

```python
AIMonitoringService      # Main orchestration for threat analysis
DecisionExecutor         # Execute AI decisions on Docker containers
EnhancedAIAnalyzer       # Multi-provider LLM with caching
LocalLLMClient          # Local LLM API client
```

### Cognitive Deception

```python
CognitiveDeceptionEngine # Main CBDF orchestration
CognitiveProfiler        # Build psychological profiles from behavior
BiasDetector            # Detect 8 cognitive bias types
DeceptionStrategyLibrary # 11 bias-targeted strategies
ResponseGenerator       # Generate deception responses
```

### Data Collection

```python
CowrieLogCollector      # Tail and parse Cowrie JSON logs
CognitiveIntegrationBridge # Route events to CBDF engine
```

### Data Models

```python
Honeypot               # Honeypot instance configuration
Session                # Attacker session with replay data
AttackEvent            # Individual attack event
CognitiveProfileDB     # Psychological profile persistence
DeceptionEventDB       # Deception strategy application record
```

---

## Complexity Hotspots

These areas require careful attention:

| File | Lines | Complexity | Notes |
|------|-------|------------|-------|
| `src/cognitive/engine.py` | 1028 | complex | Core CBDF logic, many interacting components |
| `frontend/src/pages/Settings.tsx` | 1038 | complex | 5-tab settings UI with many forms |
| `src/cognitive/profiler.py` | 850 | complex | Profile building from behavioral signals |
| `src/api/v1/endpoints/cognitive.py` | 836 | moderate | Many cognitive API routes |
| `src/ai/monitoring.py` | 577 | complex | AI service orchestration |
| `src/ai/decision_executor.py` | 553 | moderate | Docker API interactions |
| `src/alerting/channels.py` | 541 | moderate | Multi-channel alerting logic |
| `src/core/db/models.py` | 517 | moderate | 14 SQLAlchemy models |

---

## Quick Start Commands

```bash
# Start development environment
bash start.sh

# Or manually with Docker Compose
docker-compose up -d

# Run tests
pytest tests/

# Check honeypot status
bash status.sh

# View API docs
open http://localhost:8000/api/docs

# Access React dashboard
open http://localhost:3000
```

---

## Key File Map by Layer

### API Layer
- `src/api/app.py` - FastAPI application entry point
- `src/api/v1/endpoints/honeypots.py` - Honeypot CRUD
- `src/api/v1/endpoints/attacks.py` - Attack monitoring
- `src/api/v1/endpoints/cognitive.py` - CBDF endpoints
- `src/api/v1/endpoints/websocket.py` - Real-time streaming

### AI Layer
- `src/ai/monitoring.py` - AI monitoring service
- `src/ai/decision_executor.py` - Docker actions
- `src/ai/analyzer.py` - Multi-provider LLM
- `src/ai/providers/base.py` - Provider abstraction

### Cognitive Layer
- `src/cognitive/engine.py` - CBDF engine
- `src/cognitive/profiler.py` - Psychological profiling
- `src/cognitive/models.py` - Data structures

### Data Layer
- `src/core/db/models.py` - SQLAlchemy models
- `src/core/db/repositories.py` - Data access layer
- `src/core/db/session.py` - Async session management

### Frontend
- `frontend/src/App.tsx` - React app entry
- `frontend/src/pages/Dashboard.tsx` - Main dashboard
- `frontend/src/pages/CognitiveDashboard.tsx` - CBDF visualization
- `frontend/src/hooks/useApi.ts` - API hooks
- `frontend/src/hooks/useWebSocket.ts` - WebSocket hooks

---

## Related Documentation

- `docs/COMPLETE_SYSTEM_DOCUMENTATION.md` - Full system docs
- `docs/CBDF_IMPLEMENTATION_DOCS.md` - CBDF framework details
- `docs/SYSTEM_FLOW_DIAGRAMS.md` - Architecture diagrams
- `docs/QUICK_REFERENCE.md` - Command reference

---

*This onboarding guide was auto-generated from the knowledge graph analysis.*