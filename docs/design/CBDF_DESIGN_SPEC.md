# Cognitive-Behavioral Deception Framework (CBDF)
## Design Specification Document v1.0

---

## 1. Executive Summary

The Cognitive-Behavioral Deception Framework (CBDF) is a novel approach to honeypot deception that exploits human cognitive biases rather than relying solely on technical deception. This is the **first implementation** of psychology-based deception in honeypot systems.

### Key Innovation
```
TRADITIONAL: Fake files → Attacker may detect → Leaves
CBDF:        Exploit cognitive bias → Attacker sees what they expect → Stays engaged
```

---

## 2. System Architecture

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    COGNITIVE-BEHAVIORAL DECEPTION FRAMEWORK                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐    ┌─────────────────┐    ┌─────────────────────────────┐ │
│  │   ATTACKER  │───▶│  COGNITIVE      │───▶│  DECEPTION                  │ │
│  │   SESSION   │    │  PROFILER       │    │  ENGINE                     │ │
│  └─────────────┘    └─────────────────┘    └─────────────────────────────┘ │
│         │                   │                           │                   │
│         │                   ▼                           ▼                   │
│         │          ┌─────────────────┐    ┌─────────────────────────────┐ │
│         │          │  BIAS           │    │  RESPONSE                   │ │
│         │          │  DETECTOR       │    │  GENERATOR                  │ │
│         │          └─────────────────┘    └─────────────────────────────┘ │
│         │                   │                           │                   │
│         │                   ▼                           ▼                   │
│         │          ┌─────────────────┐    ┌─────────────────────────────┐ │
│         │          │  MENTAL         │    │  DECEPTION                  │ │
│         │          │  MODEL          │    │  STRATEGIES                 │ │
│         │          │  TRACKER        │    │  LIBRARY                    │ │
│         │          └─────────────────┘    └─────────────────────────────┘ │
│         │                                                             │      │
│         └─────────────────────────────────────────────────────────────┘      │
│                                        │                                    │
│                                        ▼                                    │
│                            ┌─────────────────────┐                          │
│                            │  ADAPTED RESPONSE   │                          │
│                            │  (To Attacker)      │                          │
│                            └─────────────────────┘                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Component Overview

| Component | Responsibility |
|-----------|----------------|
| **Cognitive Profiler** | Build psychological profile of attacker |
| **Bias Detector** | Identify which cognitive bias attacker is exhibiting |
| **Mental Model Tracker** | Track what attacker believes/knows/wants |
| **Deception Engine** | Orchestrate deception based on profile |
| **Response Generator** | Generate bias-exploiting responses |
| **Deception Strategy Library** | Database of cognitive deception tactics |

---

## 3. Cognitive Biases Implementation

### 3.1 Implemented Biases

| Bias | Description | Deception Tactic | Implementation |
|------|-------------|------------------|----------------|
| **Confirmation Bias** | Seek info confirming beliefs | Show expected outputs | `ConfirmationBiasStrategy` |
| **Anchoring** | First info shapes decisions | Control initial perception | `AnchoringStrategy` |
| **Sunk Cost Fallacy** | Continue due to past investment | Reward persistence | `SunkCostStrategy` |
| **Dunning-Kruger** | Overconfidence in abilities | Let them "succeed" initially | `DunningKrugerStrategy` |
| **Availability Heuristic** | Recent/vivid info weighted more | Make certain paths seem easier | `AvailabilityStrategy` |
| **Loss Aversion** | Fear loss > desire gain | Create potential "loss" scenario | `LossAversionStrategy` |
| **Authority Bias** | Trust perceived authorities | Fake system admin traces | `AuthorityBiasStrategy` |
| **Curiosity Gap** | Need to close information gaps | Tease valuable info | `CuriosityGapStrategy` |

### 3.2 Bias Detection Signals

```python
BIAS_DETECTION_SIGNALS = {
    "confirmation_bias": {
        "indicators": [
            "repeated_similar_commands",      # Looking for specific thing
            "ignoring_contradictory_output",  # Not checking other paths
            "tunnel_vision_exploration",      # Single-minded focus
        ],
        "threshold": 0.7,  # Confidence threshold
    },
    "sunk_cost": {
        "indicators": [
            "session_duration_gt_30min",
            "multiple_failed_attempts",
            "returning_to_same_directory",
            "increasing_command_frequency",
        ],
        "threshold": 0.6,
    },
    "dunning_kruger": {
        "indicators": [
            "complex_commands_with_errors",
            "no_information_gathering",
            "immediate_exploitation_attempts",
            "ignoring_error_messages",
        ],
        "threshold": 0.65,
    },
    # ... more bias definitions
}
```

---

## 4. Database Schema Extensions

### 4.1 New Models

```sql
-- Cognitive Profile for each attacker/session
CREATE TABLE cognitive_profiles (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(100) REFERENCES sessions(id),
    
    -- Detected biases (JSON array with confidence scores)
    detected_biases JSONB DEFAULT '[]',
    
    -- Mental model tracking
    attacker_beliefs JSONB DEFAULT '{}',      -- What they believe about system
    attacker_knowledge JSONB DEFAULT '[]',    -- What they've discovered
    attacker_goals JSONB DEFAULT '[]',        -- Inferred objectives
    
    -- Cognitive metrics
    overconfidence_score FLOAT DEFAULT 0.0,   -- Dunning-Kruger indicator
    persistence_score FLOAT DEFAULT 0.0,      -- Sunk cost indicator
    tunnel_vision_score FLOAT DEFAULT 0.0,    -- Confirmation bias indicator
    
    -- Deception effectiveness
    deception_success_rate FLOAT DEFAULT 0.0,
    total_deceptions_applied INTEGER DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Deception events log
CREATE TABLE deception_events (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(100) REFERENCES sessions(id),
    
    -- Deception applied
    bias_type VARCHAR(50),                    -- Which bias exploited
    strategy_name VARCHAR(100),               -- Strategy used
    trigger_command TEXT,                     -- Command that triggered deception
    
    -- Response generated
    response_type VARCHAR(50),                -- file, command_output, network, etc.
    response_content TEXT,                    -- What was shown to attacker
    
    -- Effectiveness tracking
    attacker_reacted BOOLEAN,                 -- Did attacker respond as expected?
    engagement_change FLOAT,                  -- Change in engagement after deception
    detection_suspected BOOLEAN DEFAULT FALSE,-- Did attacker seem suspicious?
    
    created_at TIMESTAMP DEFAULT NOW()
);

-- Deception strategy library
CREATE TABLE deception_strategies (
    id SERIAL PRIMARY KEY,
    
    -- Strategy metadata
    name VARCHAR(100) UNIQUE NOT NULL,
    bias_type VARCHAR(50) NOT NULL,
    description TEXT,
    
    -- Implementation
    trigger_conditions JSONB,                 -- When to apply
    response_template JSONB,                  -- How to respond
    effectiveness_score FLOAT DEFAULT 0.0,
    
    -- Usage tracking
    times_applied INTEGER DEFAULT 0,
    times_successful INTEGER DEFAULT 0,
    
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 5. Core Components Implementation

### 5.1 Cognitive Profiler

```python
class CognitiveProfiler:
    """
    Build psychological profile of attacker based on behavior.
    
    Uses multiple signals to detect cognitive biases and mental state.
    """
    
    def __init__(self):
        self.bias_detector = BiasDetector()
        self.mental_model_tracker = MentalModelTracker()
        
    async def profile_session(self, session: Session) -> CognitiveProfile:
        """
        Build cognitive profile from session data.
        
        Analyzes:
        - Command patterns for bias indicators
        - Timing for engagement metrics
        - Exploration patterns for mental model
        """
        profile = CognitiveProfile(session_id=session.id)
        
        # Analyze command sequence
        commands = session.commands
        for i, cmd in enumerate(commands):
            self._analyze_command(cmd, profile, context=commands[:i])
            
        # Detect active biases
        detected_biases = await self.bias_detector.detect(profile.signals)
        profile.detected_biases = detected_biases
        
        # Update mental model
        profile.mental_model = self.mental_model_tracker.infer(commands)
        
        return profile
```

### 5.2 Bias Detector

```python
class BiasDetector:
    """
    Detect which cognitive biases the attacker is exhibiting.
    
    Uses rule-based and ML-based detection.
    """
    
    BIAS_SIGNALS = {
        "confirmation_bias": {
            "signals": [
                lambda cmds: _count_similar_commands(cmds) > 3,
                lambda cmds: _exploration_diversity(cmds) < 0.3,
                lambda cmds: _ignoring_errors(cmds),
            ],
            "weight": 0.8,
        },
        "sunk_cost": {
            "signals": [
                lambda cmds: _session_duration(cmds) > 1800,  # 30 min
                lambda cmds: _failed_attempts(cmds) > 5,
                lambda cmds: _return_rate(cmds) > 0.4,
            ],
            "weight": 0.7,
        },
        "dunning_kruger": {
            "signals": [
                lambda cmds: _complexity_mismatch(cmds) > 0.5,
                lambda cmds: _no_reconnaissance(cmds),
                lambda cmds: _immediate_exploitation(cmds),
            ],
            "weight": 0.75,
        },
        # ... more biases
    }
    
    async def detect(self, signals: Dict) -> List[DetectedBias]:
        """
        Detect active biases from behavioral signals.
        
        Returns list of biases with confidence scores.
        """
        detected = []
        for bias_name, config in self.BIAS_SIGNALS.items():
            score = self._calculate_bias_score(signals, config)
            if score >= config.get("threshold", 0.6):
                detected.append(DetectedBias(
                    bias_type=bias_name,
                    confidence=score,
                    signals_matched=self._get_matched_signals(signals, config),
                ))
        return sorted(detected, key=lambda x: x.confidence, reverse=True)
```

### 5.3 Deception Engine

```python
class CognitiveDeceptionEngine:
    """
    Main orchestration engine for cognitive deception.
    
    Coordinates profiling, bias detection, and response generation.
    """
    
    def __init__(self):
        self.profiler = CognitiveProfiler()
        self.strategy_library = DeceptionStrategyLibrary()
        self.response_generator = ResponseGenerator()
        
    async def process_command(
        self, 
        command: str, 
        session: Session,
        profile: Optional[CognitiveProfile] = None
    ) -> DeceptionResponse:
        """
        Process attacker command through cognitive deception pipeline.
        
        1. Update cognitive profile
        2. Detect active biases
        3. Select appropriate deception strategy
        4. Generate response exploiting bias
        5. Log deception event
        """
        # Get or create profile
        if not profile:
            profile = await self.profiler.profile_session(session)
            
        # Update profile with new command
        profile = await self.profiler.update(profile, command)
        
        # Get applicable strategies
        strategies = self.strategy_library.get_strategies(
            biases=profile.detected_biases,
            command=command,
            context=profile.mental_model,
        )
        
        # Select best strategy
        strategy = self._select_strategy(strategies, profile)
        
        # Generate response
        response = await self.response_generator.generate(
            strategy=strategy,
            command=command,
            profile=profile,
        )
        
        # Log deception event
        await self._log_deception(session.id, strategy, command, response)
        
        return response
```

### 5.4 Response Generator

```python
class ResponseGenerator:
    """
    Generate responses that exploit detected cognitive biases.
    
    Customizes output based on attacker's mental model and active biases.
    """
    
    async def generate(
        self,
        strategy: DeceptionStrategy,
        command: str,
        profile: CognitiveProfile,
    ) -> DeceptionResponse:
        """
        Generate response exploiting the target bias.
        """
        bias_type = strategy.bias_type
        
        if bias_type == "confirmation_bias":
            return await self._confirmation_bias_response(command, profile)
        elif bias_type == "sunk_cost":
            return await self._sunk_cost_response(command, profile)
        elif bias_type == "dunning_kruger":
            return await self._dunning_kruger_response(command, profile)
        # ... more bias handlers
        
    async def _confirmation_bias_response(
        self,
        command: str,
        profile: CognitiveProfile,
    ) -> DeceptionResponse:
        """
        Generate response confirming attacker's expected findings.
        
        If attacker expects to find config files, show them.
        If attacker expects weak security, demonstrate it.
        """
        # What does attacker expect to find?
        expected = profile.mental_model.get("expectations", {})
        
        # Generate output matching expectations
        if "config_files" in expected:
            return self._show_fake_config(command, expected["config_files"])
        elif "weak_users" in expected:
            return self._show_weak_users(command, expected["weak_users"])
        elif "vulnerabilities" in expected:
            return self._show_vulnerability(command, expected["vulnerabilities"])
            
        # Default: show expected Linux output
        return self._generate_expected_output(command)
        
    async def _sunk_cost_response(
        self,
        command: str,
        profile: CognitiveProfile,
    ) -> DeceptionResponse:
        """
        Reward persistence to encourage continued engagement.
        
        Show "almost there" indicators to keep attacker invested.
        """
        # Add small reward for persistence
        response = self._generate_base_response(command)
        
        # Add "promising" indicators
        if random.random() < 0.3:  # 30% chance
            response.add_hint("Interesting file found: /var/backups/.hidden_config")
            
        # Show progress indicators
        if profile.session_duration > 600:  # 10 min
            response.add_progress_indicator("Access level elevated")
            
        return response
```

---

## 6. Deception Strategy Library

### 6.1 Strategy Definitions

```python
DECEPTION_STRATEGIES = {
    # Confirmation Bias Strategies
    "confirm_expected_files": {
        "bias": "confirmation_bias",
        "trigger": "ls|cat|find|grep",
        "action": "show_expected_files",
        "effectiveness": 0.85,
    },
    "confirm_vulnerability": {
        "bias": "confirmation_bias", 
        "trigger": "nmap|nikto|exploit",
        "action": "show_vulnerable_service",
        "effectiveness": 0.78,
    },
    
    # Sunk Cost Strategies
    "reward_persistence": {
        "bias": "sunk_cost",
        "trigger": "session_duration > 600",
        "action": "show_promising_findings",
        "effectiveness": 0.82,
    },
    "near_miss_hint": {
        "bias": "sunk_cost",
        "trigger": "failed_attempts > 3",
        "action": "show_almost_success",
        "effectiveness": 0.75,
    },
    
    # Dunning-Kruger Strategies
    "false_confidence": {
        "bias": "dunning_kruger",
        "trigger": "complex_command_error",
        "action": "show_minor_success",
        "effectiveness": 0.70,
    },
    "overestimate_ability": {
        "bias": "dunning_kruger",
        "trigger": "immediate_exploit_attempt",
        "action": "partial_success_feedback",
        "effectiveness": 0.68,
    },
    
    # Anchoring Strategies
    "strong_first_impression": {
        "bias": "anchoring",
        "trigger": "first_commands",
        "action": "show_weak_security_posture",
        "effectiveness": 0.88,
    },
    
    # Curiosity Gap Strategies  
    "tease_hidden_value": {
        "bias": "curiosity_gap",
        "trigger": "exploration_commands",
        "action": "hint_at_valuable_content",
        "effectiveness": 0.80,
    },
    
    # Loss Aversion Strategies
    "create_fomo": {
        "bias": "loss_aversion",
        "trigger": "exit_attempt_signals",
        "action": "show_what_theyll_miss",
        "effectiveness": 0.72,
    },
}
```

### 6.2 Strategy Selection Algorithm

```python
def select_best_strategy(
    strategies: List[DeceptionStrategy],
    profile: CognitiveProfile,
) -> DeceptionStrategy:
    """
    Select optimal strategy based on:
    1. Bias confidence (how strongly attacker exhibits bias)
    2. Strategy effectiveness (historical success rate)
    3. Context match (how well strategy fits current command)
    4. Avoidance of repetition (don't use same strategy too often)
    """
    scored_strategies = []
    
    for strategy in strategies:
        # Get bias confidence
        bias_confidence = profile.get_bias_confidence(strategy.bias_type)
        
        # Get historical effectiveness
        effectiveness = strategy.effectiveness_score
        
        # Context match score
        context_score = calculate_context_match(strategy, profile.current_context)
        
        # Repetition penalty
        repetition_penalty = profile.get_strategy_usage_penalty(strategy.name)
        
        # Combined score
        score = (
            bias_confidence * 0.4 +
            effectiveness * 0.3 +
            context_score * 0.2 -
            repetition_penalty * 0.1
        )
        
        scored_strategies.append((strategy, score))
        
    # Return highest scored strategy
    return max(scored_strategies, key=lambda x: x[1])[0]
```

---

## 7. API Endpoints

### 7.1 New Endpoints

```python
# Cognitive Profile Endpoints
@router.get("/api/v1/cognitive/profiles/{session_id}")
async def get_cognitive_profile(session_id: str):
    """Get cognitive profile for a session."""
    
@router.get("/api/v1/cognitive/biases")
async def list_detected_biases(session_id: str):
    """List detected biases for a session."""
    
@router.get("/api/v1/cognitive/mental-model/{session_id}")
async def get_mental_model(session_id: str):
    """Get inferred mental model of attacker."""

# Deception Management Endpoints
@router.get("/api/v1/deception/strategies")
async def list_deception_strategies():
    """List all deception strategies."""
    
@router.post("/api/v1/deception/strategies")
async def create_deception_strategy(strategy: StrategyCreate):
    """Create custom deception strategy."""
    
@router.get("/api/v1/deception/events")
async def list_deception_events(session_id: Optional[str] = None):
    """List deception events with optional filtering."""
    
@router.get("/api/v1/deception/effectiveness")
async def get_deception_effectiveness():
    """Get effectiveness metrics for all strategies."""

# Real-time Endpoints
@router.websocket("/api/v1/cognitive/stream")
async def cognitive_stream(websocket: WebSocket):
    """Real-time cognitive analysis stream."""
```

---

## 8. Frontend Dashboard Components

### 8.1 Cognitive Profile Panel

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  🧠 COGNITIVE PROFILE                              Session: abc123          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────┐  ┌─────────────────────────────────┐  │
│  │  DETECTED BIASES                │  │  MENTAL MODEL                   │  │
│  │                                 │  │                                 │  │
│  │  ████████████ Confirmation 85%  │  │  Believes:                      │  │
│  │  █████████░░░ Sunk Cost   72%   │  │  • System is Ubuntu 20.04      │  │
│  │  ██████░░░░░░ Dunning-Kruger 45%│  │  • Weak SSH config             │  │
│  │  ████░░░░░░░░ Anchoring    38%  │  │  • No firewall active          │  │
│  │                                 │  │                                 │  │
│  │  Active Strategy: Confirm Files │  │  Knows:                         │  │
│  │                                 │  │  • /etc/passwd contents        │  │
│  │  [View Details] [Adjust]        │  │  • User 'admin' exists         │  │
│  └─────────────────────────────────┘  │                                 │  │
│                                       │  Goals:                          │  │
│  ┌─────────────────────────────────┐  │  • Privilege escalation        │  │
│  │  ENGAGEMENT METRICS              │  │  • Data exfiltration           │  │
│  │                                 │  │                                 │  │
│  │  Duration: 47 min               │  └─────────────────────────────────┘  │
│  │  Commands: 156                                                   │  │
│  │  Deceptions Applied: 23                                          │  │
│  │  Effectiveness: 78%                                              │
│  │                                                                 │  │
│  │  ████████████████████░░░░░░░░░░░░██████████████████████████░░░░░  │  │
│  │  Engagement Over Time (↑ after deception at 23 min)             │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 8.2 Deception Strategy Dashboard

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  🎭 DECEPTION STRATEGIES                                   [ + New ]        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Strategy          │ Bias              │ Effectiveness │ Uses │ Status│   │
│  ├───────────────────┼───────────────────┼───────────────┼──────┼───────┤   │
│  │ Confirm Files     │ Confirmation      │     85%       │ 234  │   ✓   │   │
│  │ Reward Persistence│ Sunk Cost         │     82%       │ 156  │   ✓   │   │
│  │ First Impression  │ Anchoring         │     88%       │ 89   │   ✓   │   │
│  │ Tease Hidden      │ Curiosity Gap     │     80%       │ 67   │   ✓   │   │
│  │ False Confidence  │ Dunning-Kruger    │     70%       │ 45   │   ✓   │   │
│  │ Near Miss Hint    │ Sunk Cost         │     75%       │ 34   │   ✓   │   │
│  │ Create FOMO       │ Loss Aversion     │     72%       │ 23   │   ✓   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  TOP PERFORMING STRATEGIES (Last 24h)                               │   │
│  │                                                                      │   │
│  │  ████████████████████████████████████████ Confirm Files (85%)       │   │
│  │  █████████████████████████████████████░░░░ First Impression (88%)   │   │
│  │  ███████████████████████████████████░░░░░░ Reward Persistence (82%) │   │
│  │  ████████████████████████████████░░░░░░░░░░ Tease Hidden (80%)      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 9. Implementation Plan

### Phase 1: Core Engine (Week 1)
- [ ] Create database models and migrations
- [ ] Implement CognitiveProfiler
- [ ] Implement BiasDetector
- [ ] Implement MentalModelTracker
- [ ] Create unit tests

### Phase 2: Deception Engine (Week 2)
- [ ] Implement DeceptionStrategyLibrary
- [ ] Implement ResponseGenerator
- [ ] Implement CognitiveDeceptionEngine
- [ ] Create deception strategy templates
- [ ] Integration tests

### Phase 3: API & Integration (Week 3)
- [ ] Create API endpoints
- [ ] Integrate with existing AI analyzer
- [ ] Integrate with decision executor
- [ ] WebSocket for real-time updates
- [ ] API documentation

### Phase 4: Frontend Dashboard (Week 4)
- [ ] Cognitive Profile panel component
- [ ] Deception Strategy dashboard
- [ ] Real-time updates integration
- [ ] Mental model visualization
- [ ] Effectiveness charts

---

## 10. Success Metrics

### Key Performance Indicators

| Metric | Target | Measurement |
|--------|--------|-------------|
| Engagement Duration | +50% | Compare sessions with/without CBDF |
| Detection Rate | < 20% | Attacker realizes deception |
| Strategy Effectiveness | > 75% | Deception leads to expected behavior |
| False Positive Rate | < 10% | Incorrect bias detection |
| Response Latency | < 100ms | Additional processing time |

---

## 11. Security Considerations

### Risk Mitigation

1. **Don't Over-Reveal**: Deception should not expose real system details
2. **Consistency Check**: All fake data must be internally consistent
3. **Escape Hatch**: Ability to disable CBDF if attacker detects it
4. **Audit Trail**: All deception decisions logged for analysis
5. **Rate Limiting**: Prevent attackers from gaming the system

---

*Document Version: 1.0*
*Created: 2026-03-13*
*Author: CBDF Implementation Team*