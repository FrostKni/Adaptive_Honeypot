# Adaptive Honeypot - Technical Documentation

## System Architecture

### Overview
The Adaptive Honeypot is a fully autonomous system that deploys, monitors, and adapts honeypots based on real-time attack analysis using AI/LLM technology.

### Core Components

#### 1. Adaptive Orchestrator
**Location**: `core/orchestrator.py`

The central brain of the system that coordinates all operations:
- Manages honeypot lifecycle (deploy, monitor, adapt, remove)
- Runs three concurrent loops:
  - **Monitor Loop**: Watches logs and triggers adaptations
  - **Health Check Loop**: Ensures honeypots are running properly
  - **Adaptation Loop**: Periodic analysis and configuration updates

**Key Methods**:
- `deploy_new_honeypot()`: Creates and starts a new honeypot
- `trigger_adaptation()`: Immediate adaptation based on threshold
- `analyze_and_adapt()`: Periodic AI-driven analysis
- `apply_adaptation()`: Applies new configuration to honeypot

#### 2. Deployment Manager
**Location**: `core/deployment.py`

Handles Docker container orchestration:
- Creates isolated Docker network for honeypots
- Deploys Cowrie containers with custom configurations
- Monitors container health (CPU, memory, uptime)
- Manages session migration between containers

**Key Features**:
- Automatic network creation
- Health monitoring with resource metrics
- Container restart on failure
- Session preservation during migration

#### 3. Configuration Engine
**Location**: `core/config_engine.py`

Manages honeypot configurations:
- Validates configurations against JSON schema
- Generates default configurations
- Maintains version history for rollback
- Merges configuration updates

**Configuration Schema**:
```python
{
    "name": str,
    "type": "ssh" | "telnet" | "http",
    "port": int (1-65535),
    "interaction_level": "low" | "medium" | "high",
    "hostname": str,
    "banner": str,
    "fake_users": [{"username": str, "password": str}],
    "fake_files": [str],
    "allowed_commands": [str],
    "response_delay": float,
    "max_sessions": int,
    "session_timeout": int,
    "custom_responses": {str: str}
}
```

#### 4. Log Processor
**Location**: `monitoring/log_processor.py`

Parses and analyzes honeypot logs:
- Reads Cowrie JSON logs
- Extracts attack events (logins, commands, connections)
- Classifies command severity
- Aggregates statistics (IPs, attack types, commands)

**Event Types**:
- `cowrie.login.failed`: Failed login attempts
- `cowrie.command.input`: Executed commands
- `cowrie.session.connect`: New connections

#### 5. AI Analyzer
**Location**: `ai/analyzer.py`

Uses LLMs to analyze attacks and generate configurations:
- Supports OpenAI (GPT-4) and Anthropic (Claude)
- Analyzes attack sophistication and attacker skill level
- Recommends interaction levels and deception strategies
- Generates adaptive configurations

**Analysis Output**:
```python
{
    "attack_sophistication": "low" | "medium" | "high",
    "attacker_skill_level": "script_kiddie" | "intermediate" | "advanced" | "expert",
    "attack_objectives": [str],
    "threat_level": "low" | "medium" | "high" | "critical",
    "recommended_interaction_level": "low" | "medium" | "high",
    "deception_strategies": [str],
    "configuration_changes": {dict}
}
```

#### 6. Resource Monitor
**Location**: `monitoring/resource_monitor.py`

Tracks system resources:
- CPU usage and core count
- Memory usage (total, used, percent)
- Disk usage
- Threshold checking for alerts

### Data Models

**Location**: `core/models.py`

Pydantic models for type safety and validation:
- `HoneypotConfig`: Honeypot configuration
- `AttackEvent`: Individual attack event
- `AdaptationDecision`: Configuration change record
- `ContainerHealth`: Container health metrics

### API Layer

**Location**: `api/main.py`

FastAPI application providing:
- RESTful endpoints for honeypot management
- WebSocket for real-time updates
- Automatic API documentation (Swagger/OpenAPI)

**Endpoints**:
- `POST /honeypots/deploy`: Deploy new honeypot
- `DELETE /honeypots/{id}`: Remove honeypot
- `GET /honeypots`: List all honeypots
- `GET /honeypots/{id}/health`: Health status
- `GET /honeypots/{id}/logs`: Attack logs
- `GET /honeypots/{id}/stats`: Statistics
- `GET /adaptations`: Adaptation history
- `WS /ws`: WebSocket connection

## Adaptation Logic

### Trigger Mechanisms

1. **Threshold-Based**
   - Triggered when event count reaches threshold (default: 5)
   - Immediate response to active attacks
   - Prevents overwhelming the system

2. **Periodic Analysis**
   - Runs every N seconds (default: 60)
   - Analyzes accumulated events
   - Proactive adaptation

3. **Threat-Based**
   - Immediate response to high/critical severity
   - Escalates interaction level
   - Deploys advanced deception

### Adaptation Process

```
1. Event Collection
   ↓
2. AI Analysis
   - Pattern recognition
   - Skill assessment
   - Objective identification
   ↓
3. Configuration Generation
   - Adjust interaction level
   - Add fake users/files
   - Modify allowed commands
   - Set response delays
   ↓
4. Validation
   - Schema validation
   - Resource check
   ↓
5. Deployment
   - Save configuration
   - Stop old container
   - Start new container
   - Migrate sessions
   ↓
6. Verification
   - Health check
   - Log monitoring
```

### Deception Strategies

1. **Fake Credentials**
   - Add attempted usernames to fake users
   - Use honeypot passwords
   - Create realistic user accounts

2. **Fake Files**
   - Add commonly targeted files
   - Create fake sensitive data
   - Simulate realistic filesystem

3. **Command Responses**
   - Generate fake command outputs
   - Simulate realistic system behavior
   - Add delays for realism

4. **Interaction Escalation**
   - Low: Basic responses, limited commands
   - Medium: More commands, fake files
   - High: Full interaction, complex deception

## Deployment

### Docker Architecture

```
┌─────────────────────────────────────┐
│     Docker Host                      │
│  ┌────────────────────────────────┐ │
│  │  honeypot_net (172.20.0.0/16)  │ │
│  │  ┌──────────┐  ┌──────────┐   │ │
│  │  │Orchestr. │  │  Redis   │   │ │
│  │  └──────────┘  └──────────┘   │ │
│  │  ┌──────────┐  ┌──────────┐   │ │
│  │  │Honeypot1 │  │Honeypot2 │   │ │
│  │  └──────────┘  └──────────┘   │ │
│  └────────────────────────────────┘ │
└─────────────────────────────────────┘
```

### Volume Mounts

- `/var/run/docker.sock`: Docker API access
- `./logs`: Honeypot logs
- `./honeypots`: Configuration files
- `./.env`: Environment variables

### Network Isolation

- Honeypots run in isolated bridge network
- Only exposed ports are accessible
- No direct host access
- Controlled communication

## Security Considerations

### Isolation
- Containers run with limited privileges
- No host network access
- Separate network namespace
- Resource limits enforced

### Data Protection
- Logs stored in isolated volumes
- No sensitive data in honeypots
- Automatic log rotation
- Encrypted API communication (HTTPS recommended)

### Monitoring
- Real-time health checks
- Resource usage monitoring
- Automatic restart on failure
- Alert on threshold breach

## Performance Optimization

### Resource Management
- CPU limits per container
- Memory limits per container
- Disk I/O throttling
- Connection limits

### Scaling Strategies
1. **Vertical**: Increase container resources
2. **Horizontal**: Deploy multiple orchestrators
3. **Distributed**: External database and queue

### Optimization Tips
- Use SSD for logs
- Increase analysis interval for lower load
- Limit max honeypots based on resources
- Use local LLM for faster analysis

## Troubleshooting

### Common Issues

1. **Docker Connection Failed**
   - Check Docker daemon: `systemctl status docker`
   - Verify socket permissions: `ls -l /var/run/docker.sock`
   - Add user to docker group: `usermod -aG docker $USER`

2. **Honeypot Won't Start**
   - Check port availability: `netstat -tulpn | grep PORT`
   - Verify Docker network: `docker network ls`
   - Check logs: `docker logs honeypot_ID`

3. **AI Analysis Failing**
   - Verify API key in .env
   - Check API connectivity
   - Review rate limits
   - Use fallback analysis

4. **High Resource Usage**
   - Reduce max_honeypots
   - Increase analysis_interval
   - Add resource limits to containers
   - Check for log file growth

### Debug Mode

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Log Locations
- Orchestrator: `docker logs adaptive_orchestrator`
- Honeypots: `./logs/{honeypot_id}/cowrie.json`
- API: `docker logs adaptive_orchestrator`

## Future Enhancements

### Planned Features
1. Multiple honeypot types (HTTP, FTP, SMB)
2. Machine learning for pattern detection
3. Distributed deployment across multiple hosts
4. Advanced session recording and playback
5. Integration with SIEM systems
6. Automated threat intelligence sharing
7. Custom deception modules
8. Advanced analytics dashboard

### Extensibility
- Plugin system for new honeypot types
- Custom AI analyzers
- Webhook integrations
- Custom deception strategies

## References

- Cowrie Honeypot: https://github.com/cowrie/cowrie
- Docker SDK: https://docker-py.readthedocs.io/
- FastAPI: https://fastapi.tiangolo.com/
- OpenAI API: https://platform.openai.com/docs/
