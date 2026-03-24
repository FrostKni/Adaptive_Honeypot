# Adaptive Honeypot - Detailed System Flow

This document provides step-by-step flows for all major system operations.

---

## Flow 1: Attacker Connection and Session Handling

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        ATTACKER CONNECTION FLOW                              │
└─────────────────────────────────────────────────────────────────────────────┘

Step 1: Initial Connection
━━━━━━━━━━━━━━━━━━━━━━━━━
Attacker                 Cowrie Container              Log Collector
   │                          │                              │
   │──── SSH Connect ────────▶│                              │
   │     (Port 2222)          │                              │
   │                          │──── Log: "New connection" ──▶│
   │                          │     [session: abc123]        │
   │                          │                              │
   │                          │                      ┌───────┴───────┐
   │                          │                      │ Parse Source IP│
   │                          │                      │ Create Session │
   │                          │                      │ Track in Memory│
   │                          │                      └───────┬───────┘
   │                          │                              │

Step 2: Brute Force Attempt
━━━━━━━━━━━━━━━━━━━━━━━━━━━
Attacker                 Cowrie Container              Log Collector
   │                          │                              │
   │──── SSH Auth ───────────▶│                              │
   │     root:password123     │                              │
   │                          │──── Log: "login failed" ────▶│
   │                          │                              │
   │                          │                      ┌───────┴───────┐
   │                          │                      │ Create Event  │
   │                          │                      │ Store Creds   │
   │                          │                      │ Broadcast WS  │
   │                          │                      │ Send to AI    │
   │                          │                      └───────┬───────┘
   │                          │                              │
   │                          │                              │
   │                          │                      ┌───────┴───────┐
   │                          │                      │ AI Analysis   │
   │                          │                      │ Threat: LOW   │
   │                          │                      │ Action: Monitor│
   │                          │                      └───────┬───────┘
   │                          │                              │

Step 3: Successful Login
━━━━━━━━━━━━━━━━━━━━━━━━
Attacker                 Cowrie Container              Log Collector
   │                          │                              │
   │──── SSH Auth ───────────▶│                              │
   │     admin:admin          │                              │
   │                          │──── Log: "login success" ──▶│
   │                          │                              │
   │                          │                      ┌───────┴───────┐
   │                          │                      │ Create Session│
   │                          │                      │ in Database   │
   │                          │                      │ Link to IP    │
   │                          │                      └───────┬───────┘
   │◀─── Shell Access ────────│                              │
   │                          │                              │

Step 4: Command Execution
━━━━━━━━━━━━━━━━━━━━━━━━━
Attacker                 Cowrie Container              Log Collector
   │                          │                              │
   │──── Command: "ls" ──────▶│                              │
   │                          │──── Log: "CMD: ls" ────────▶│
   │                          │                              │
   │                          │                      ┌───────┴───────┐
   │                          │                      │ Parse Command │
   │                          │                      │ Update Session│
   │                          │                      │ Broadcast WS  │
   │                          │                      └───────┬───────┘
   │                          │                              │
   │                          │                      ┌───────┴───────┐
   │                          │                      │ Cognitive     │
   │                          │                      │ Analysis      │
   │                          │                      └───────┬───────┘
   │                          │                              │
   │                          │                      ┌───────┴───────┐
   │                          │                      │ Bias Detection│
   │                          │                      │ Deception Gen │
   │                          │                      └───────┬───────┘
   │                          │                              │
   │◀─── Fake Output ─────────│                              │
   │     "bin etc var..."     │                              │
```

---

## Flow 2: AI Analysis Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         AI ANALYSIS PIPELINE                                 │
└─────────────────────────────────────────────────────────────────────────────┘

Event Queue Processing
━━━━━━━━━━━━━━━━━━━━━━
                         AI Monitoring Service
                                │
                    ┌───────────┴───────────┐
                    │   Event Queue         │
                    │   [evt1, evt2, ...]   │
                    └───────────┬───────────┘
                                │
                    ┌───────────┴───────────┐
                    │   Pop Event           │
                    │   (FIFO, async)       │
                    └───────────┬───────────┘
                                │
                    ┌───────────┴───────────┐
                    │   Build Prompt        │
                    │   - Event details     │
                    │   - Session context   │
                    │   - Attack patterns   │
                    └───────────┬───────────┘
                                │
                                ▼
        ┌───────────────────────┴───────────────────────┐
        │                                               │
        ▼                                               ▼
┌───────────────┐                             ┌───────────────┐
│  Local LLM    │                             │  Fallback     │
│  (DeepSeek)   │                             │  (OpenAI)     │
└───────┬───────┘                             └───────┬───────┘
        │                                               │
        │◀────────── Try First ─────────────────────────│
        │                                               │
        ▼                                               │
┌───────────────┐                                       │
│  Parse JSON   │                                       │
│  Response     │                                       │
└───────┬───────┘                                       │
        │                                               │
        │◀────────── On Failure ────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────────────────┐
│                    AIAnalysisResult                       │
├───────────────────────────────────────────────────────────┤
│  threat_level: "medium"                                   │
│  threat_score: 0.65                                       │
│  attacker_skill: "intermediate"                           │
│  attack_objectives: ["reconnaissance", "persistence"]     │
│  confidence: 0.75                                         │
│  reasoning: "Pattern suggests..."                         │
│  mitre_attack_ids: ["T1110", "T1059.004"]                 │
│  recommended_action: "reconfigure"                        │
│  configuration_changes: {                                 │
│    "interaction_level": "high",                           │
│    "fake_files": true,                                    │
│    "delay_responses": true                                │
│  }                                                        │
└───────────────────────────────────────────────────────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │   Decision Created    │
                    │   ID: dec-12345       │
                    │   Action: reconfigure │
                    └───────────┬───────────┘
                                │
                    ┌───────────┴───────────┐
                    │   Broadcast via       │
                    │   WebSocket           │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │   Decision Executor   │
                    └───────────────────────┘
```

---

## Flow 3: Decision Execution

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       DECISION EXECUTION FLOW                                │
└─────────────────────────────────────────────────────────────────────────────┘

Action Selection
━━━━━━━━━━━━━━━━
                         Decision Executor
                                │
                    ┌───────────┴───────────┐
                    │   Analyze Threat       │
                    │   Level & Confidence   │
                    └───────────┬───────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
        ▼                       ▼                       ▼
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│  MONITOR      │     │  RECONFIGURE  │     │  ISOLATE      │
│  (Low threat) │     │  (Med/High)   │     │  (Critical)   │
└───────────────┘     └───────┬───────┘     └───────┬───────┘
        │                     │                     │
        ▼                     │                     │
┌───────────────┐             │                     │
│  No action    │             │                     │
│  Continue     │             │                     │
│  observation  │             │                     │
└───────────────┘             │                     │
                              │                     │
                              ▼                     │
                    ┌─────────────────┐             │
                    │  Get Container  │             │
                    │  by Label       │             │
                    └────────┬────────┘             │
                             │                      │
                    ┌────────┴────────┐             │
                    │  Check if       │             │
                    │  Shell Access   │             │
                    └────────┬────────┘             │
                             │                      │
              ┌──────────────┼──────────────┐       │
              │              │              │       │
              ▼              ▼              │       │
        ┌──────────┐  ┌──────────┐          │       │
        │ Has Shell│  │ No Shell │          │       │
        └────┬─────┘  └────┬─────┘          │       │
             │             │                │       │
             ▼             ▼                │       │
    ┌────────────────┐ ┌────────────────┐   │       │
    │ Put Config     │ │ Recreate with  │   │       │
    │ File in        │ │ New ENV vars   │   │       │
    │ Container      │ └────────────────┘   │       │
    └───────┬────────┘                      │       │
            │                               │       │
            ▼                               │       │
    ┌────────────────┐                      │       │
    │ Send HUP       │                      │       │
    │ Signal         │                      │       │
    └───────┬────────┘                      │       │
            │                               │       │
            ▼                               │       │
    ┌────────────────┐                      │       │
    │ Config Applied │                      │       │
    │ Deception ON   │                      │       │
    └────────────────┘                      │       │
                                            │       │
                                            │       ▼
                                    ┌───────┴───────┐
                                    │ Get Isolated  │
                                    │ Network       │
                                    └───────┬───────┘
                                            │
                                            ▼
                                    ┌───────────────┐
                                    │ Disconnect    │
                                    │ from Main     │
                                    │ Network       │
                                    └───────┬───────┘
                                            │
                                            ▼
                                    ┌───────────────┐
                                    │ Connect to    │
                                    │ Quarantine    │
                                    │ Network       │
                                    └───────┬───────┘
                                            │
                                            ▼
                                    ┌───────────────┐
                                    │ Attacker      │
                                    │ Isolated      │
                                    │ (No Internet) │
                                    └───────────────┘
```

---

## Flow 4: Cognitive Deception Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    COGNITIVE DECEPTION PIPELINE                              │
└─────────────────────────────────────────────────────────────────────────────┘

Command Analysis
━━━━━━━━━━━━━━━
Input Command ─────────────────────────────────────────────────────────────────▶
                                                                              │
                                                                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           SIGNAL EXTRACTION                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│  Input: "cat /etc/shadow"                                                    │
│                                                                              │
│  Extracted Signals:                                                          │
│  ├─ command_type: "file_read"                                               │
│  ├─ target_path: "/etc/shadow"                                              │
│  ├─ sensitivity: "high"                                                     │
│  ├─ privilege_required: True                                                │
│  └─ command_index: 5 (in session)                                           │
└─────────────────────────────────────────────────────────────────────────────┘
                                                                              │
                                                                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           BIAS DETECTION                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│  Session Signals:                                                            │
│  ├─ commands: ["ls", "whoami", "cat /etc/passwd", "cat /etc/shadow"]        │
│  ├─ session_duration: 120 seconds                                           │
│  ├─ directories_visited: {"/etc", "/home"}                                  │
│  ├─ failed_attempts: 2                                                      │
│  └─ hidden_files_accessed: 1                                                │
│                                                                              │
│  Detected Biases:                                                            │
│  ├─ CONFIRMATION_BIAS (0.72)                                                │
│  │   └─ Signals: single_directory_focus, seeking_expected_pattern           │
│  ├─ CURIOSITY_GAP (0.65)                                                    │
│  │   └─ Signals: exploring_hidden_files, seeking_configuration              │
│  └─ SUNK_COST (0.55)                                                        │
│      └─ Signals: returning_to_same_path                                     │
└─────────────────────────────────────────────────────────────────────────────┘
                                                                              │
                                                                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       STRATEGY SELECTION                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│  Input:                                                                      │
│  ├─ Command: "cat /etc/shadow"                                              │
│  ├─ Biases: [CONFIRMATION_BIAS, CURIOSITY_GAP, SUNK_COST]                   │
│  └─ Profile: CognitiveProfile(session_id="sess-123")                        │
│                                                                              │
│  Candidate Strategies:                                                       │
│  ├─ confirm_expected_files (priority: 10, effectiveness: 0.85)              │
│  ├─ tease_hidden_value (priority: 8, effectiveness: 0.80)                   │
│  └─ reward_persistence (priority: 9, effectiveness: 0.82)                   │
│                                                                              │
│  Scoring:                                                                    │
│  ├─ confirm_expected_files: 0.85 + 0.14 (bias boost) = 0.99                 │
│  ├─ tease_hidden_value: 0.80 + 0.13 = 0.93                                  │
│  └─ reward_persistence: 0.82 + 0.11 = 0.93                                  │
│                                                                              │
│  Selected: confirm_expected_files                                           │
└─────────────────────────────────────────────────────────────────────────────┘
                                                                              │
                                                                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       RESPONSE GENERATION                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│  Strategy: confirm_expected_files                                            │
│  Target Bias: CONFIRMATION_BIAS                                             │
│                                                                              │
│  Template:                                                                   │
│  {                                                                           │
│    "type": "confirm_expectations",                                          │
│    "add_expected_files": true,                                              │
│    "match_attacker_beliefs": true                                           │
│  }                                                                           │
│                                                                              │
│  Generated Response:                                                         │
│  root:$6$rounds=5000$saltsalt$hashhash:18000:0:99999:7:::                   │
│  admin:$6$rounds=5000$saltsalt$hashhash:18500:0:99999:7:::                  │
│  developer:$6$rounds=5000$saltsalt$hashhash:19000:0:99999:7:::              │
│  ...                                                                         │
│                                                                              │
│  Metadata:                                                                   │
│  ├─ strategy_used: "confirm_expected_files"                                 │
│  ├─ bias_targeted: "confirmation_bias"                                      │
│  ├─ latency_ms: 15                                                          │
│  └─ deception_applied: true                                                 │
└─────────────────────────────────────────────────────────────────────────────┘
                                                                              │
                                                                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       EFFECTIVENESS TRACKING                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│  Record Deception Event:                                                     │
│  ├─ session_id: "sess-123"                                                  │
│  ├─ bias_type: "confirmation_bias"                                          │
│  ├─ strategy_name: "confirm_expected_files"                                 │
│  ├─ trigger_command: "cat /etc/shadow"                                      │
│  └─ timestamp: 2026-03-13T10:00:00Z                                         │
│                                                                              │
│  Update Cognitive Profile:                                                   │
│  ├─ total_deceptions_applied: +1                                            │
│  └─ deception_success_rate: recalculated                                    │
│                                                                              │
│  Watch for Follow-up:                                                        │
│  └─ If attacker continues in same direction → deception successful          │
└─────────────────────────────────────────────────────────────────────────────┘
                                                                              │
                                                                              ▼
Output: Fake shadow file content ─────────────────────────────────────────────▶
```

---

## Flow 5: WebSocket Real-Time Updates

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      WEBSOCKET REAL-TIME FLOW                                │
└─────────────────────────────────────────────────────────────────────────────┘

Client Connection
━━━━━━━━━━━━━━━━━
Frontend                  WebSocket Manager              Backend
   │                            │                            │
   │──── Connect ──────────────▶│                            │
   │    ws://localhost:8000/api/v1/ws                       │
   │                            │                            │
   │◀─── Welcome Message ───────│                            │
   │    {"type": "connected"}   │                            │
   │                            │                            │
   │──── Subscribe ────────────▶│                            │
   │    {"type": "subscribe",   │                            │
   │     "channels": ["attacks", "ai_decisions"]}           │
   │                            │                            │
   │◀─── Subscription Conf ─────│                            │
   │    {"type": "subscribed"}  │                            │

Event Broadcasting
━━━━━━━━━━━━━━━━━
Log Collector              WebSocket Manager              Frontend
   │                            │                            │
   │──── Attack Event ─────────▶│                            │
   │    {                       │                            │
   │      "type": "command",    │                            │
   │      "source_ip": "1.2.3.4",                           │
   │      "command": "whoami"   │                            │
   │    }                       │                            │
   │                            │                            │
   │                            │──── Broadcast ────────────▶│
   │                            │    {"type": "attack_event",│
   │                            │     "data": {...}}         │
   │                            │                            │
   │                            │                            ▼
   │                            │                     ┌──────────────┐
   │                            │                     │ UI Update    │
   │                            │                     │ Attack Feed  │
   │                            │                     │ Highlight IP │
   │                            │                     └──────────────┘

AI Decision Notification
━━━━━━━━━━━━━━━━━━━━━━
AI Service                 WebSocket Manager              Frontend
   │                            │                            │
   │──── Decision Made ────────▶│                            │
   │    {                       │                            │
   │      "action": "reconfigure",                          │
   │      "threat": "high",      │                           │
   │      "confidence": 0.85     │                           │
   │    }                       │                            │
   │                            │                            │
   │                            │──── Broadcast ────────────▶│
   │                            │    {"type": "ai_decision",│
   │                            │     "data": {...}}         │
   │                            │                            │
   │                            │                            ▼
   │                            │                     ┌──────────────┐
   │                            │                     │ AI Monitor   │
   │                            │                     │ Show Decision│
   │                            │                     │ Update Stats │
   │                            │                     └──────────────┘
```

---

## Flow 6: Alert Triggering

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        ALERT TRIGGERING FLOW                                 │
└─────────────────────────────────────────────────────────────────────────────┘

Trigger Conditions
━━━━━━━━━━━━━━━━━
                         Alert Manager
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
        ▼                       ▼                       ▼
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│ Critical      │     │ Threshold     │     │ Pattern       │
│ Attack Event  │     │ Exceeded      │     │ Match         │
└───────┬───────┘     └───────┬───────┘     └───────┬───────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              │
                              ▼
                    ┌───────────────────┐
                    │ Create Alert      │
                    │ Object            │
                    └─────────┬─────────┘
                              │
                              ▼
                    ┌───────────────────┐
                    │ Check Rate Limit  │
                    │ (5 min window)    │
                    └─────────┬─────────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
              ▼               ▼               ▼
        ┌──────────┐   ┌──────────┐   ┌──────────┐
        │ Allowed  │   │ Limited  │   │ Cooldown │
        └────┬─────┘   │ (skip)   │   │ Active   │
             │         └──────────┘   └──────────┘
             │
             ▼
    ┌────────────────────────────────────────────────────────────────┐
    │                    SEND TO CHANNELS                            │
    ├────────────────────────────────────────────────────────────────┤
    │                                                                 │
    │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
    │  │   Email     │  │   Slack     │  │   Discord   │            │
    │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘            │
    │         │                │                │                    │
    │         ▼                ▼                ▼                    │
    │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
    │  │ SMTP Server │  │ Webhook URL │  │ Webhook URL │            │
    │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘            │
    │         │                │                │                    │
    │         ▼                ▼                ▼                    │
    │  ┌─────────────────────────────────────────────────────────┐  │
    │  │                    NOTIFICATION SENT                     │  │
    │  │                                                          │  │
    │  │  Subject: [HIGH] Attack Detected: brute_force            │  │
    │  │                                                          │  │
    │  │  Attack from 192.168.1.100 on honeypot SSH-01           │  │
    │  │                                                          │  │
    │  │  Details:                                                │  │
    │  │  - Attack Type: brute_force                             │  │
    │  │  - Severity: HIGH                                       │  │
    │  │  - Session: sess-abc123                                 │  │
    │  │  - Timestamp: 2026-03-13T10:00:00Z                      │  │
    │  └─────────────────────────────────────────────────────────┘  │
    │                                                                 │
    └────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌───────────────────┐
                    │ Store in Database │
                    │ (alert_history)   │
                    └───────────────────┘
```

---

## Flow 7: Honeypot Deployment

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      HONEYPOT DEPLOYMENT FLOW                                │
└─────────────────────────────────────────────────────────────────────────────┘

API Request
━━━━━━━━━━
Client                    FastAPI Backend            Deployment Manager
   │                            │                            │
   │──── POST /api/v1/honeypots │                            │
   │    {                       │                            │
   │      "name": "SSH-01",     │                            │
   │      "type": "ssh",        │                            │
   │      "port": 2222          │                            │
   │    }                       │                            │
   │                            │                            │
   │                            │──── Validate Request ─────▶│
   │                            │                            │
   │                            │◀─── Port Available ────────│
   │                            │                            │
   │                            │──── Create DB Record ─────▶│
   │                            │                            │
   │                            │◀─── Honeypot ID ───────────│
   │                            │                            │
   │                            │──── Deploy Container ─────▶│
   │                            │     (Background Task)      │
   │                            │                            │
   │◀─── Response (201) ────────│                            │
   │    {                       │                            │
   │      "id": "ssh-01-abc",   │                            │
   │      "status": "starting"  │                            │
   │    }                       │                            │
   │                            │                            │

Container Creation (Background)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Deployment Manager           Docker Engine
   │                            │
   │──── Pull Image ───────────▶│
   │    cowrie/cowrie:latest    │
   │                            │
   │◀─── Image Pulled ──────────│
   │                            │
   │──── Create Container ─────▶│
   │    {                       │
   │      "name": "honeypot-ssh-01-abc",
   │      "image": "cowrie/cowrie:latest",
   │      "labels": {           │
   │        "honeypot.id": "ssh-01-abc",
   │        "honeypot.type": "ssh",
   │        "honeypot.port": "2222"
   │      },                    │
   │      "ports": {            │
   │        "2222/tcp": 2222    │
   │      }                     │
   │    }                       │
   │                            │
   │◀─── Container ID ──────────│
   │                            │
   │──── Connect to Network ───▶│
   │    honeypot-network        │
   │                            │
   │──── Start Container ──────▶│
   │                            │
   │◀─── Running ───────────────│
   │                            │
   │──── Update DB Status ─────▶│
   │    status: RUNNING         │
   │    container_id: abc...    │
   │                            │

Verification
━━━━━━━━━━━
   │                            │
   │──── GET /api/v1/honeypots/{id} ─────────────────────────▶│
   │                            │                            │
   │◀─── Response ──────────────│                            │
   │    {                       │                            │
   │      "id": "ssh-01-abc",   │                            │
   │      "status": "running",  │                            │
   │      "container_id": "abc123...",
   │      "port": 2222          │                            │
   │    }                       │                            │
```

---

## Summary of Integration Points

| Component          | Input                          | Output                        |
|--------------------|--------------------------------|-------------------------------|
| Log Collector      | Docker container logs          | Parsed events to DB/AI/WS     |
| AI Analyzer        | Attack events                  | Threat assessment, decisions  |
| Decision Executor  | AI decisions                   | Container modifications       |
| Cognitive Engine   | Commands, session context      | Deceptive responses           |
| Alert Manager      | Events exceeding thresholds    | Email/Slack/Discord alerts    |
| WebSocket Server   | All events                     | Real-time frontend updates    |
| Deployment Manager | API requests                   | Docker containers             |

---

*Flow Documentation v1.0*