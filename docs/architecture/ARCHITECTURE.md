# Architecture Documentation

## System Overview

The Adaptive Honeypot System is built on a modern, cloud-native architecture designed for scalability, reliability, and security.

## Core Components

### 1. API Layer (FastAPI)

**Purpose**: REST API and WebSocket server for client communication.

**Key Features**:
- Async request handling
- OpenAPI documentation
- Request/response validation
- Rate limiting
- Authentication middleware

**Files**:
- `src/api/app.py` - Application factory
- `src/api/v1/` - API versioning
- `src/api/deps/` - Dependency injection

### 2. Core Layer

**Purpose**: Business logic and domain models.

**Components**:
- `orchestrator.py` - Main orchestration engine
- `config.py` - Configuration management
- `security.py` - Authentication and authorization
- `db/` - Database models and repositories

### 3. AI Layer

**Purpose**: Attack analysis and adaptation decisions.

**Components**:
- `analyzer.py` - Main AI analyzer
- `providers/` - Multi-provider support (OpenAI, Anthropic, Gemini)
- `models.py` - AI response models
- `prompts.py` - Prompt templates

### 4. Monitoring Layer

**Purpose**: Log processing and metrics collection.

**Components**:
- `log_processor.py` - Cowrie log parsing
- `resource_monitor.py` - System metrics
- `metrics.py` - Prometheus metrics

### 5. Alerting Layer

**Purpose**: Multi-channel alert distribution.

**Components**:
- `channels.py` - Alert channel implementations
- `manager.py` - Alert routing and rate limiting

## Data Models

### Honeypot
```python
class Honeypot:
    id: str
    name: str
    type: HoneypotType  # SSH, HTTP, FTP, etc.
    status: HoneypotStatus
    port: int
    container_id: str
    interaction_level: InteractionLevel
    config: dict
```

### Session
```python
class Session:
    id: str
    honeypot_id: str
    source_ip: str
    username: str
    commands: List[str]
    attack_type: AttackType
    severity: AttackSeverity
    threat_level: ThreatLevel
```

### Adaptation
```python
class Adaptation:
    id: int
    honeypot_id: str
    trigger_type: str
    ai_analysis: dict
    old_config: dict
    new_config: dict
    applied: bool
```

## Data Flow

### Attack Detection Flow

```
1. Attacker connects to honeypot
2. Honeypot logs activity to JSON
3. Log processor parses events
4. Events stored in database
5. Threshold check triggers analysis
6. AI analyzer processes events
7. Adaptation decision made
8. New config generated
9. Honeypot redeployed
10. Alert sent
```

### Adaptation Flow

```
┌─────────────┐
│   Attack    │
│  Detected   │
└──────┬──────┘
       │
       ▼
┌─────────────┐     No     ┌─────────────┐
│ Threshold?  ├────────────►│  Continue   │
└──────┬──────┘             │ Monitoring  │
       │ Yes                └─────────────┘
       ▼
┌─────────────┐
│ AI Analysis │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Generate   │
│   Config    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Validate   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Deploy    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Verify    │
└─────────────┘
```

## Database Schema

### Entity Relationship Diagram

```
┌──────────────┐       ┌──────────────┐
│  Honeypot    │       │   Session    │
├──────────────┤       ├──────────────┤
│ id (PK)      │◄──────│ honeypot_id  │
│ name         │       │ id (PK)      │
│ type         │       │ source_ip    │
│ status       │       │ username     │
│ port         │       │ commands     │
│ config       │       │ severity     │
└──────────────┘       └──────┬───────┘
       │                      │
       │               ┌──────▼───────┐
       │               │ AttackEvent  │
       │               ├──────────────┤
       │               │ id (PK)      │
       │               │ session_id   │
       │               │ event_type   │
       │               │ data         │
       │               └──────────────┘
       │
       │               ┌──────────────┐
       └──────────────►│ Adaptation   │
                       ├──────────────┤
                       │ id (PK)      │
                       │ honeypot_id  │
                       │ ai_analysis  │
                       │ old_config   │
                       │ new_config   │
                       └──────────────┘
```

## Security Architecture

### Authentication Flow

```
Client Request
      │
      ▼
┌─────────────────┐
│ Rate Limiting   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Auth Middleware │
├─────────────────┤
│ 1. Check JWT    │
│ 2. Check API Key│
│ 3. Validate     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Scope Check     │
└────────┬────────┘
         │
         ▼
   Route Handler
```

### Network Isolation

```
┌─────────────────────────────────────┐
│           Host Network              │
├─────────────────────────────────────┤
│  ┌─────────────────────────────┐    │
│  │   Application Network       │    │
│  │   (Backend, DB, Redis)      │    │
│  └─────────────────────────────┘    │
│                                     │
│  ┌─────────────────────────────┐    │
│  │   Honeypot Network          │    │
│  │   (Isolated Containers)     │    │
│  │   172.20.0.0/16             │    │
│  └─────────────────────────────┘    │
└─────────────────────────────────────┘
```

## Deployment Architecture

### Docker Compose (Development)

```yaml
services:
  orchestrator:
    - FastAPI backend
    - Port 8000
  
  frontend:
    - React dashboard
    - Port 3000
  
  postgres:
    - PostgreSQL 15
    - Port 5432
  
  redis:
    - Redis 7
    - Port 6379
```

### Kubernetes (Production)

```yaml
Deployments:
  - backend (2-10 replicas, HPA)
  - frontend (2-5 replicas, HPA)
  - redis (single replica)

StatefulSets:
  - postgresql (1 replica with PVC)

Services:
  - backend-svc (ClusterIP)
  - frontend-svc (ClusterIP)
  - postgres-svc (ClusterIP)
  - redis-svc (ClusterIP)

Ingress:
  - TLS via cert-manager
  - NGINX ingress controller
```

## Performance Considerations

### Database
- Connection pooling (10 connections, 20 overflow)
- Indexed queries on frequently accessed columns
- Async queries with SQLAlchemy

### Caching
- Redis for session caching
- AI response caching (1 hour TTL)
- API response caching

### Scaling
- Horizontal Pod Autoscaler
- Read replicas for PostgreSQL
- Redis clustering (optional)