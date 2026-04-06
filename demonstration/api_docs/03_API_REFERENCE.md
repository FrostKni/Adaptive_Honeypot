# API Reference - Complete Endpoint Documentation

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

### JWT Token Authentication

Most endpoints require authentication via JWT token.

**Obtain Token**:
```bash
POST /auth/login
Content-Type: application/x-www-form-urlencoded

username=admin&password=your_password
```

**Response**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

**Use Token**:
```bash
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### API Key Authentication

Alternative authentication for automation:

**Create API Key**:
```bash
POST /auth/api-keys
Authorization: Bearer {jwt_token}

{
  "name": "Automation Key",
  "expires_in_days": 365
}
```

**Response**:
```json
{
  "key": "ak_live_1234567890abcdef...",
  "name": "Automation Key",
  "created_at": "2026-04-04T10:00:00Z",
  "expires_at": "2027-04-04T10:00:00Z"
}
```

**Use API Key**:
```bash
X-API-Key: ak_live_1234567890abcdef...
```

---

## Authentication Endpoints

### Login
```http
POST /auth/login
```

**Request Body**:
```json
{
  "username": "admin",
  "password": "your_password"
}
```

**Response**: `200 OK`
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

**Error**: `401 Unauthorized`
```json
{
  "detail": "Incorrect username or password"
}
```

### List API Keys
```http
GET /auth/api-keys
Authorization: Bearer {token}
```

**Response**: `200 OK`
```json
{
  "api_keys": [
    {
      "id": "key-123",
      "name": "Automation Key",
      "created_at": "2026-04-04T10:00:00Z",
      "last_used": "2026-04-04T12:00:00Z",
      "expires_at": "2027-04-04T10:00:00Z"
    }
  ]
}
```

### Revoke API Key
```http
DELETE /auth/api-keys/{key_id}
Authorization: Bearer {token}
```

---

## Honeypot Endpoints

### List All Honeypots
```http
GET /honeypots
Authorization: Bearer {token}
```

**Response**: `200 OK`
```json
{
  "honeypots": [
    {
      "id": "honeypot-ssh-01",
      "name": "SSH Honeypot 1",
      "type": "ssh",
      "status": "running",
      "port": 2222,
      "container_id": "abc123...",
      "container_name": "honeypot-cowrie-ssh",
      "interaction_level": "medium",
      "total_sessions": 127,
      "total_attacks": 89,
      "last_attack": "2026-04-04T09:30:00Z",
      "created_at": "2026-03-01T00:00:00Z",
      "started_at": "2026-03-01T00:01:00Z"
    }
  ],
  "total": 1
}
```

### Get Single Honeypot
```http
GET /honeypots/{honeypot_id}
Authorization: Bearer {token}
```

### Deploy New Honeypot
```http
POST /honeypots
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "SSH Honeypot 2",
  "type": "ssh",
  "port": 2223,
  "interaction_level": "high",
  "config": {
    "hostname": "production-server",
    "banner": "Ubuntu 20.04 LTS"
  }
}
```

**Response**: `201 Created`
```json
{
  "id": "honeypot-ssh-02",
  "name": "SSH Honeypot 2",
  "type": "ssh",
  "status": "starting",
  "port": 2223,
  "container_id": null,
  "created_at": "2026-04-04T10:00:00Z"
}
```

### Update Honeypot Configuration
```http
PATCH /honeypots/{honeypot_id}
Authorization: Bearer {token}
Content-Type: application/json

{
  "interaction_level": "aggressive",
  "config": {
    "hostname": "critical-server"
  }
}
```

### Stop Honeypot
```http
POST /honeypots/{honeypot_id}/stop
Authorization: Bearer {token}
```

### Start Honeypot
```http
POST /honeypots/{honeypot_id}/start
Authorization: Bearer {token}
```

### Delete Honeypot
```http
DELETE /honeypots/{honeypot_id}
Authorization: Bearer {token}
```

---

## Session Endpoints

### List Sessions
```http
GET /sessions?honeypot_id={id}&status=active&limit=50&offset=0
Authorization: Bearer {token}
```

**Query Parameters**:
- `honeypot_id`: Filter by honeypot
- `status`: Filter by status (active/closed)
- `source_ip`: Filter by source IP
- `start_date`: ISO date string
- `end_date`: ISO date string
- `limit`: Results per page (default: 50)
- `offset`: Pagination offset

**Response**: `200 OK`
```json
{
  "sessions": [
    {
      "id": "session-123",
      "honeypot_id": "honeypot-ssh-01",
      "source_ip": "192.168.1.100",
      "source_port": 54321,
      "source_country": "US",
      "source_asn": 12345,
      "username": "root",
      "auth_success": true,
      "duration_seconds": 1800,
      "commands_count": 47,
      "status": "closed",
      "started_at": "2026-04-04T08:00:00Z",
      "ended_at": "2026-04-04T08:30:00Z"
    }
  ],
  "total": 127,
  "limit": 50,
  "offset": 0
}
```

### Get Session Details
```http
GET /sessions/{session_id}
Authorization: Bearer {token}
```

**Response**: `200 OK`
```json
{
  "id": "session-123",
  "honeypot_id": "honeypot-ssh-01",
  "source_ip": "192.168.1.100",
  "source_country": "US",
  "source_asn": 12345,
  "source_asn_name": "Example ISP",
  "username": "root",
  "password": "toor",
  "auth_success": true,
  "duration_seconds": 1800,
  "commands_count": 47,
  "status": "closed",
  "started_at": "2026-04-04T08:00:00Z",
  "ended_at": "2026-04-04T08:30:00Z",
  "commands": [
    {
      "command": "whoami",
      "timestamp": "2026-04-04T08:01:00Z"
    },
    {
      "command": "ls -la",
      "timestamp": "2026-04-04T08:01:30Z"
    },
    {
      "command": "cat /etc/passwd",
      "timestamp": "2026-04-04T08:02:00Z"
    }
  ],
  "credentials_tried": [
    {"username": "admin", "password": "admin"},
    {"username": "root", "password": "toor"}
  ]
}
```

### Get Session Replay
```http
GET /sessions/{session_id}/replay
Authorization: Bearer {token}
```

**Response**: `200 OK`
```json
{
  "session_id": "session-123",
  "asciicast": {
    "version": 2,
    "width": 80,
    "height": 24,
    "timestamp": 1712232000,
    "env": {"SHELL": "/bin/bash"},
    "stdout": [
      [0.0, "Last login: Thu Apr  4 08:00:00 2026 from 192.168.1.100\r\n"],
      [0.5, "root@server:~# "],
      [1.0, "whoami\r\n"],
      [1.1, "root\r\n"],
      [1.2, "root@server:~# "],
      [2.0, "ls -la\r\n"],
      [2.5, "total 48\r\ndrwxr-xr-x 6 root root 4096 Apr  4 08:00 .\r\n..."]
    ]
  }
}
```

---

## Attack Endpoints

### List Attacks
```http
GET /attacks?honeypot_type=ssh&severity=high&limit=100
Authorization: Bearer {token}
```

**Query Parameters**:
- `honeypot_type`: Filter by type
- `attack_type`: Filter by attack type
- `severity`: Filter by severity (info/low/medium/high/critical)
- `source_ip`: Filter by IP
- `start_date`: ISO date string
- `end_date`: ISO date string
- `limit`: Results per page
- `offset`: Pagination offset

**Response**: `200 OK`
```json
{
  "attacks": [
    {
      "id": "attack-456",
      "session_id": "session-123",
      "honeypot_id": "honeypot-ssh-01",
      "source_ip": "192.168.1.100",
      "attack_type": "brute_force",
      "severity": "high",
      "timestamp": "2026-04-04T08:00:30Z",
      "details": {
        "username": "root",
        "attempts": 47,
        "success": true
      }
    }
  ],
  "total": 89
}
```

### Get Attack Details
```http
GET /attacks/{attack_id}
Authorization: Bearer {token}
```

---

## Adaptation Endpoints

### List Adaptations
```http
GET /adaptations?honeypot_id={id}&limit=50
Authorization: Bearer {token}
```

**Response**: `200 OK`
```json
{
  "adaptations": [
    {
      "id": "adaptation-789",
      "honeypot_id": "honeypot-ssh-01",
      "action": "reconfigure",
      "reason": "High threat level detected",
      "changes": {
        "interaction_level": "aggressive",
        "filesystem": "enhanced_deception"
      },
      "ai_decision_id": "decision-123",
      "triggered_at": "2026-04-04T08:30:00Z",
      "completed_at": "2026-04-04T08:30:05Z",
      "success": true
    }
  ]
}
```

---

## Alert Endpoints

### List Alerts
```http
GET /alerts?status=pending&limit=50
Authorization: Bearer {token}
```

**Response**: `200 OK`
```json
{
  "alerts": [
    {
      "id": "alert-101",
      "type": "high_threat",
      "severity": "critical",
      "title": "Critical Threat Detected",
      "message": "Session session-123 shows advanced exploitation techniques",
      "status": "pending",
      "channels": ["slack", "email"],
      "created_at": "2026-04-04T08:35:00Z",
      "sent_at": null
    }
  ]
}
```

### Acknowledge Alert
```http
POST /alerts/{alert_id}/acknowledge
Authorization: Bearer {token}

{
  "note": "Investigating the attack"
}
```

---

## AI Monitoring Endpoints

### Get AI Service Status
```http
GET /ai/status
Authorization: Bearer {token}
```

**Response**: `200 OK`
```json
{
  "status": "running",
  "provider": "openai",
  "model": "gpt-4-turbo-preview",
  "uptime_seconds": 86400,
  "queue_length": 3,
  "total_decisions": 1247,
  "last_decision": "2026-04-04T10:00:00Z"
}
```

### List AI Activities
```http
GET /ai/activities?limit=100
Authorization: Bearer {token}
```

**Response**: `200 OK`
```json
{
  "activities": [
    {
      "id": "activity-234",
      "timestamp": "2026-04-04T09:45:00Z",
      "status": "decision",
      "action": "analyze_attack",
      "details": {
        "source_ip": "192.168.1.100",
        "threat_level": "high",
        "recommended_action": "reconfigure"
      },
      "duration_ms": 1234,
      "success": true
    }
  ]
}
```

### List AI Decisions
```http
GET /ai/decisions?limit=50
Authorization: Bearer {token}
```

**Response**: `200 OK`
```json
{
  "decisions": [
    {
      "id": "decision-123",
      "timestamp": "2026-04-04T08:30:00Z",
      "source_ip": "192.168.1.100",
      "threat_level": "high",
      "threat_score": 0.85,
      "reasoning": "Multiple indicators suggest advanced persistent threat...",
      "action": "reconfigure",
      "configuration_changes": {
        "interaction_level": "aggressive",
        "deception_mode": "enhanced"
      },
      "confidence": 0.92,
      "mitre_attack_ids": ["T1110", "T1059"],
      "duration_ms": 2345
    }
  ]
}
```

### Start AI Service
```http
POST /ai/start
Authorization: Bearer {token}
```

### Stop AI Service
```http
POST /ai/stop
Authorization: Bearer {token}
```

### Trigger Manual Analysis
```http
POST /ai/trigger
Authorization: Bearer {token}

{
  "honeypot_id": "honeypot-ssh-01",
  "session_id": "session-123"
}
```

---

## Cognitive Endpoints

### List Cognitive Profiles
```http
GET /cognitive/profiles?limit=50
Authorization: Bearer {token}
```

**Response**: `200 OK`
```json
{
  "profiles": [
    {
      "session_id": "session-123",
      "source_ip": "192.168.1.100",
      "biases_detected": [
        {
          "bias_type": "confirmation_bias",
          "confidence": 0.85,
          "evidence": ["Repeated ls commands", "Seeking expected files"]
        },
        {
          "bias_type": "sunk_cost_fallacy",
          "confidence": 0.72,
          "evidence": ["Extended session duration", "Multiple failed attempts"]
        }
      ],
      "mental_model": {
        "beliefs": ["System is production Ubuntu server", "User has root access"],
        "knowledge": ["Basic Linux commands", "System structure"],
        "goals": ["Exfiltrate data", "Establish persistence"],
        "confidence": 0.78
      },
      "engagement_duration": 1800,
      "deception_strategies_applied": ["confirm_expected_files", "reward_persistence"],
      "effectiveness_score": 0.85
    }
  ]
}
```

### Get Cognitive Profile
```http
GET /cognitive/profiles/{session_id}
Authorization: Bearer {token}
```

### Get Bias Breakdown
```http
GET /cognitive/biases?threshold=0.5
Authorization: Bearer {token}
```

**Response**: `200 OK`
```json
{
  "total_profiles": 127,
  "bias_distribution": {
    "confirmation_bias": {
      "count": 35,
      "percentage": 27.6,
      "avg_confidence": 0.82
    },
    "sunk_cost_fallacy": {
      "count": 28,
      "percentage": 22.0,
      "avg_confidence": 0.78
    },
    "dunning_kruger": {
      "count": 21,
      "percentage": 16.5,
      "avg_confidence": 0.71
    },
    "anchoring": {
      "count": 15,
      "percentage": 11.8,
      "avg_confidence": 0.85
    }
  }
}
```

### Get Mental Model
```http
GET /cognitive/mental-model/{session_id}
Authorization: Bearer {token}
```

### Get Active Strategies
```http
GET /cognitive/strategies
Authorization: Bearer {token}
```

### Get Strategy Effectiveness
```http
GET /cognitive/effectiveness
Authorization: Bearer {token}
```

**Response**: `200 OK`
```json
{
  "strategies": [
    {
      "name": "confirm_expected_files",
      "bias_type": "confirmation_bias",
      "times_used": 156,
      "effectiveness_score": 0.85,
      "avg_engagement_increase": 0.42
    },
    {
      "name": "reward_persistence",
      "bias_type": "sunk_cost_fallacy",
      "times_used": 98,
      "effectiveness_score": 0.82,
      "avg_engagement_increase": 0.38
    }
  ]
}
```

---

## Threat Intel Endpoints

### List IOCs
```http
GET /threat-intel?type=ip&limit=100
Authorization: Bearer {token}
```

**Response**: `200 OK`
```json
{
  "iocs": [
    {
      "id": "ioc-123",
      "type": "ip",
      "value": "192.168.1.100",
      "threat_level": "high",
      "first_seen": "2026-03-01T00:00:00Z",
      "last_seen": "2026-04-04T10:00:00Z",
      "attack_count": 127,
      "tags": ["brute_force", "scanner"],
      "asn": 12345,
      "country": "US"
    }
  ]
}
```

---

## Analytics Endpoints

### Dashboard Stats
```http
GET /analytics/dashboard
Authorization: Bearer {token}
```

**Response**: `200 OK`
```json
{
  "active_honeypots": 4,
  "active_sessions": 12,
  "attacks_today": 89,
  "threat_level": "medium",
  "attacks_by_type": {
    "brute_force": 45,
    "command_injection": 23,
    "reconnaissance": 21
  },
  "attacks_by_protocol": {
    "ssh": 67,
    "http": 15,
    "ftp": 7
  },
  "top_attackers": [
    {
      "ip": "192.168.1.100",
      "attack_count": 23,
      "country": "US"
    }
  ],
  "timeline": [
    {"timestamp": "2026-04-04T00:00:00Z", "count": 5},
    {"timestamp": "2026-04-04T01:00:00Z", "count": 8}
  ]
}
```

---

## WebSocket Endpoint

### Connect
```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/ws?token=YOUR_JWT_TOKEN');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Event:', data.type, data);
};
```

### Event Types

**Attack Event**:
```json
{
  "type": "attack_event",
  "data": {
    "id": "attack-456",
    "source_ip": "192.168.1.100",
    "attack_type": "brute_force",
    "severity": "high"
  }
}
```

**Honeypot Update**:
```json
{
  "type": "honeypot_update",
  "data": {
    "id": "honeypot-ssh-01",
    "status": "running",
    "sessions": 12
  }
}
```

**AI Decision**:
```json
{
  "type": "ai_decision",
  "data": {
    "id": "decision-123",
    "threat_level": "high",
    "action": "reconfigure"
  }
}
```

**Cognitive Update**:
```json
{
  "type": "cognitive_update",
  "data": {
    "session_id": "session-123",
    "biases_detected": ["confirmation_bias"]
  }
}
```

---

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Invalid port number: must be between 1024 and 65535"
}
```

### 401 Unauthorized
```json
{
  "detail": "Could not validate credentials"
}
```

### 403 Forbidden
```json
{
  "detail": "Not enough permissions"
}
```

### 404 Not Found
```json
{
  "detail": "Honeypot not found"
}
```

### 429 Too Many Requests
```json
{
  "detail": "Rate limit exceeded: 100 requests per minute"
}
```

### 500 Internal Server Error
```json
{
  "detail": "An error occurred while processing your request",
  "request_id": "req-abc123"
}
```

---

## Rate Limiting

Default limits:
- **API Endpoints**: 100 requests per minute
- **WebSocket**: 1 connection per user
- **AI Endpoints**: 60 requests per minute

Headers:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1712232300
```
