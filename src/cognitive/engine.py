"""
Cognitive-Behavioral Deception Framework - Deception Engine.

Orchestrates cognitive profiling, bias detection, and response generation.
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import random
import logging
import json

from src.cognitive.profiler import (
    CognitiveProfiler,
    CognitiveProfile,
    CognitiveBiasType,
    MentalModel,
    DetectedBias,
)

logger = logging.getLogger(__name__)


# === Strategy Definitions ===

@dataclass
class DeceptionStrategy:
    """A deception strategy targeting a specific cognitive bias."""
    name: str
    bias_type: CognitiveBiasType
    description: str
    trigger_commands: List[str] = field(default_factory=list)
    trigger_conditions: Dict[str, Any] = field(default_factory=dict)
    response_template: Dict[str, Any] = field(default_factory=dict)
    effectiveness_score: float = 0.75
    priority: int = 0
    cooldown_seconds: int = 60
    max_uses_per_session: int = 10
    uses_this_session: int = 0
    last_used_at: Optional[datetime] = None
    
    def can_use(self, now: datetime = None) -> bool:
        """Check if strategy can be used (cooldown, max uses)."""
        if self.uses_this_session >= self.max_uses_per_session:
            return False
        
        if self.last_used_at and now:
            elapsed = (now - self.last_used_at).total_seconds()
            if elapsed < self.cooldown_seconds:
                return False
        
        return True
    
    def mark_used(self):
        """Mark strategy as used."""
        self.uses_this_session += 1
        self.last_used_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "bias_type": self.bias_type.value,
            "description": self.description,
            "effectiveness_score": self.effectiveness_score,
            "priority": self.priority,
            "uses_this_session": self.uses_this_session,
        }


class DeceptionStrategyLibrary:
    """
    Library of deception strategies.
    
    Provides strategies for exploiting various cognitive biases.
    """
    
    DEFAULT_STRATEGIES = [
        # === Confirmation Bias Strategies ===
        DeceptionStrategy(
            name="confirm_expected_files",
            bias_type=CognitiveBiasType.CONFIRMATION_BIAS,
            description="Show files that confirm attacker's expected findings",
            trigger_commands=["ls", "cat", "find", "grep", "head", "tail"],
            trigger_conditions={"min_confidence": 0.6, "commands_contain": ["etc", "config", "var"]},
            response_template={
                "type": "confirm_expectations",
                "add_expected_files": True,
                "match_attacker_beliefs": True,
            },
            effectiveness_score=0.85,
            priority=10,
        ),
        DeceptionStrategy(
            name="confirm_vulnerability",
            bias_type=CognitiveBiasType.CONFIRMATION_BIAS,
            description="Show evidence of expected vulnerabilities",
            trigger_commands=["nmap", "nikto", "curl", "wget", "nc"],
            trigger_conditions={"min_confidence": 0.6, "session_min_duration": 60},
            response_template={
                "type": "vulnerable_service",
                "show_open_port": True,
                "show_outdated_version": True,
            },
            effectiveness_score=0.78,
            priority=8,
        ),
        
        # === Sunk Cost Strategies ===
        DeceptionStrategy(
            name="reward_persistence",
            bias_type=CognitiveBiasType.SUNK_COST,
            description="Show promising findings to reward continued engagement",
            trigger_commands=["ls", "cat", "find", "grep"],
            trigger_conditions={"min_confidence": 0.5, "session_min_duration": 600},
            response_template={
                "type": "progress_reward",
                "add_interesting_files": True,
                "show_almost_there": True,
            },
            effectiveness_score=0.82,
            priority=9,
        ),
        DeceptionStrategy(
            name="near_miss_hint",
            bias_type=CognitiveBiasType.SUNK_COST,
            description="Show 'almost there' indicators after failures",
            trigger_commands=["sudo", "su", "chmod", "chown"],
            trigger_conditions={"min_confidence": 0.5, "failed_attempts": 3},
            response_template={
                "type": "near_success",
                "hint_at_alternative": True,
                "show_close_attempt": True,
            },
            effectiveness_score=0.75,
            priority=7,
        ),
        
        # === Dunning-Kruger Strategies ===
        DeceptionStrategy(
            name="false_confidence",
            bias_type=CognitiveBiasType.DUNNING_KRUGER,
            description="Show minor successes to maintain overconfidence",
            trigger_commands=["id", "whoami", "pwd", "ls"],
            trigger_conditions={"min_confidence": 0.55, "no_reconnaissance": True},
            response_template={
                "type": "easy_wins",
                "show_access": True,
                "minimize_errors": True,
            },
            effectiveness_score=0.70,
            priority=6,
        ),
        DeceptionStrategy(
            name="partial_success_feedback",
            bias_type=CognitiveBiasType.DUNNING_KRUGER,
            description="Provide partial success for complex commands",
            trigger_commands=["exploit", "payload", "shell"],
            trigger_conditions={"min_confidence": 0.55},
            response_template={
                "type": "partial_success",
                "show_partial_output": True,
                "encourage_more": True,
            },
            effectiveness_score=0.68,
            priority=5,
        ),
        
        # === Anchoring Strategies ===
        DeceptionStrategy(
            name="weak_first_impression",
            bias_type=CognitiveBiasType.ANCHORING,
            description="Create initial impression of weak security",
            trigger_commands=["uname", "whoami", "id", "hostname"],
            trigger_conditions={"min_confidence": 0.5, "command_index": "< 5"},
            response_template={
                "type": "weak_system",
                "show_old_version": True,
                "show_no_firewall": True,
                "show_weak_config": True,
            },
            effectiveness_score=0.88,
            priority=10,
        ),
        
        # === Curiosity Gap Strategies ===
        DeceptionStrategy(
            name="tease_hidden_value",
            bias_type=CognitiveBiasType.CURIOSITY_GAP,
            description="Hint at valuable hidden content",
            trigger_commands=["ls", "find", "grep"],
            trigger_conditions={"min_confidence": 0.5, "hidden_files_accessed": 1},
            response_template={
                "type": "hidden_hint",
                "add_suspicious_file": True,
                "show_interesting_name": True,
            },
            effectiveness_score=0.80,
            priority=8,
        ),
        DeceptionStrategy(
            name="breadcrumb_trail",
            bias_type=CognitiveBiasType.CURIOSITY_GAP,
            description="Create breadcrumb trail to follow",
            trigger_commands=["cat", "grep", "less"],
            trigger_conditions={"min_confidence": 0.5},
            response_template={
                "type": "breadcrumb",
                "add_reference_to_next": True,
                "create_discovery_path": True,
            },
            effectiveness_score=0.77,
            priority=7,
        ),
        
        # === Loss Aversion Strategies ===
        DeceptionStrategy(
            name="create_fomo",
            bias_type=CognitiveBiasType.LOSS_AVERSION,
            description="Show what attacker might miss if they leave",
            trigger_commands=["exit", "logout", "quit"],
            trigger_conditions={"min_confidence": 0.5, "session_min_duration": 300},
            response_template={
                "type": "potential_loss",
                "hint_at_missed_treasure": True,
                "show_time_sensitive": True,
            },
            effectiveness_score=0.72,
            priority=6,
        ),
        
        # === Availability Heuristic Strategies ===
        DeceptionStrategy(
            name="easy_path_visibility",
            bias_type=CognitiveBiasType.AVAILABILITY_HEURISTIC,
            description="Make certain attack paths seem more available",
            trigger_commands=["ls", "find", "grep", "cat"],
            trigger_conditions={"min_confidence": 0.5},
            response_template={
                "type": "highlight_path",
                "show_easy_target": True,
                "make_obvious": True,
            },
            effectiveness_score=0.76,
            priority=7,
        ),
    ]
    
    def __init__(self):
        self.strategies: Dict[str, DeceptionStrategy] = {}
        self._load_default_strategies()
    
    def _load_default_strategies(self):
        """Load default strategies."""
        for strategy in self.DEFAULT_STRATEGIES:
            self.strategies[strategy.name] = strategy
    
    def get_strategies(
        self,
        bias_type: Optional[CognitiveBiasType] = None,
        command: Optional[str] = None,
        min_confidence: float = 0.0,
    ) -> List[DeceptionStrategy]:
        """
        Get applicable strategies based on filters.
        
        Args:
            bias_type: Filter by bias type
            command: Filter by trigger command
            min_confidence: Minimum bias confidence required
            
        Returns:
            List of matching strategies
        """
        matching = []
        
        for strategy in self.strategies.values():
            # Filter by bias type
            if bias_type and strategy.bias_type != bias_type:
                continue
            
            # Filter by command
            if command:
                cmd_base = command.split()[0] if command else ""
                if cmd_base not in strategy.trigger_commands:
                    # Check if command contains any trigger
                    if not any(t in command.lower() for t in strategy.trigger_commands):
                        continue
            
            # Filter by confidence
            conditions = strategy.trigger_conditions
            required_conf = conditions.get("min_confidence", 0.0)
            if min_confidence < required_conf:
                continue
            
            # Check if can use (cooldown, etc)
            if not strategy.can_use():
                continue
            
            matching.append(strategy)
        
        # Sort by priority (higher first)
        return sorted(matching, key=lambda s: s.priority, reverse=True)
    
    def get_best_strategy(
        self,
        profile: CognitiveProfile,
        command: str,
    ) -> Optional[DeceptionStrategy]:
        """
        Get the best strategy for current context.
        
        Considers:
        - Detected biases
        - Command context
        - Strategy effectiveness
        - Usage history
        """
        candidates = []
        
        # Get strategies for each detected bias
        for bias in profile.get_active_biases():
            strategies = self.get_strategies(
                bias_type=bias.bias_type,
                command=command,
                min_confidence=bias.confidence,
            )
            candidates.extend(strategies)
        
        if not candidates:
            # Fallback to any applicable strategy
            candidates = self.get_strategies(command=command)
        
        if not candidates:
            return None
        
        # Score and rank strategies
        scored = []
        for strategy in candidates:
            score = self._score_strategy(strategy, profile)
            scored.append((strategy, score))
        
        # Return best
        best = max(scored, key=lambda x: x[1])
        return best[0]
    
    def _score_strategy(
        self,
        strategy: DeceptionStrategy,
        profile: CognitiveProfile,
    ) -> float:
        """Score a strategy for current context."""
        # Base score from effectiveness
        score = strategy.effectiveness_score
        
        # Boost for bias confidence
        bias_confidence = profile.get_bias_confidence(strategy.bias_type)
        score += bias_confidence * 0.2
        
        # Priority weight
        score += strategy.priority * 0.01
        
        # Penalty for overuse
        if strategy.uses_this_session > 0:
            score -= strategy.uses_this_session * 0.1
        
        return score
    
    def mark_used(self, strategy_name: str):
        """Mark a strategy as used."""
        if strategy_name in self.strategies:
            self.strategies[strategy_name].mark_used()
    
    def reset_session_counts(self):
        """Reset usage counts for new session."""
        for strategy in self.strategies.values():
            strategy.uses_this_session = 0


@dataclass
class DeceptionResponse:
    """Response generated by deception engine."""
    content: str
    response_type: str
    strategy_used: str
    bias_targeted: CognitiveBiasType
    metadata: Dict[str, Any] = field(default_factory=dict)
    latency_ms: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "response_type": self.response_type,
            "strategy_used": self.strategy_used,
            "bias_targeted": self.bias_targeted.value,
            "metadata": self.metadata,
            "latency_ms": self.latency_ms,
        }


class ResponseGenerator:
    """
    Generate responses that exploit cognitive biases.
    
    Customizes output based on attacker's mental model and active biases.
    """
    
    # Template responses for different scenarios
    FILE_TEMPLATES = {
        "passwd": """root:x:0:0:root:/root:/bin/bash
daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin
bin:x:2:2:bin:/bin:/usr/sbin/nologin
sys:x:3:3:sys:/dev:/usr/sbin/nologin
www-data:x:33:33:www-data:/var/www:/usr/sbin/nologin
backup:x:34:34:backup:/var/backups:/usr/sbin/nologin
admin:x:1000:1000:Admin User:/home/admin:/bin/bash
developer:x:1001:1001:Developer:/home/developer:/bin/bash
mysql:x:112:117:MySQL Server:/nonexistent:/bin/false
""",
        "shadow_hint": "root:$6$rounds=5000$saltsalt$hashhash:18000:0:99999:7:::\nadmin:$6$rounds=5000$saltsalt$hashhash:18500:0:99999:7:::",
        "ssh_config": """Port 22
PermitRootLogin yes
PasswordAuthentication yes
ChallengeResponseAuthentication no
UsePAM yes
X11Forwarding yes
PrintMotd no
AcceptEnv LANG LC_*
Subsystem sftp /usr/lib/openssh/sftp-server
""",
        "bash_history": """ls -la
cat /etc/passwd
sudo -l
cat /etc/shadow
find / -name "*.conf" 2>/dev/null
grep -r "password" /var/www 2>/dev/null
""",
        "interesting_file": """# Database Configuration
DB_HOST=10.0.0.50
DB_USER=webapp
DB_PASS=Sup3rS3cr3tP@ss!
DB_NAME=production

# API Keys
AWS_ACCESS_KEY=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
""",
    }
    
    DIRECTORY_TEMPLATES = {
        "root": ["bin", "boot", "dev", "etc", "home", "lib", "media", "mnt", "opt", "proc", "root", "run", "sbin", "srv", "sys", "tmp", "usr", "var"],
        "home": ["admin", "developer", "backup", "www-data"],
        "etc": ["passwd", "shadow", "group", "hosts", "hostname", "ssh", "cron.d", "apache2", "nginx"],
        "var": ["log", "www", "backups", "tmp", "lib", "cache"],
        "interesting": [".secrets", ".backup", "config.bak", "old_config", "database_dump.sql"],
    }
    
    def __init__(self):
        self._generators = {
            "confirm_expectations": self._gen_confirm_expectations,
            "vulnerable_service": self._gen_vulnerable_service,
            "progress_reward": self._gen_progress_reward,
            "near_success": self._gen_near_success,
            "easy_wins": self._gen_easy_wins,
            "partial_success": self._gen_partial_success,
            "weak_system": self._gen_weak_system,
            "hidden_hint": self._gen_hidden_hint,
            "breadcrumb": self._gen_breadcrumb,
            "potential_loss": self._gen_potential_loss,
            "highlight_path": self._gen_highlight_path,
        }
    
    async def generate(
        self,
        strategy: DeceptionStrategy,
        command: str,
        profile: CognitiveProfile,
    ) -> DeceptionResponse:
        """
        Generate response exploiting the target bias.
        """
        import time
        start = time.time()
        
        template_type = strategy.response_template.get("type", "confirm_expectations")
        generator = self._generators.get(template_type, self._gen_confirm_expectations)
        
        content = await generator(command, profile, strategy.response_template)
        
        latency = int((time.time() - start) * 1000)
        
        return DeceptionResponse(
            content=content,
            response_type="command_output",
            strategy_used=strategy.name,
            bias_targeted=strategy.bias_type,
            metadata={"template_type": template_type},
            latency_ms=latency,
        )
    
    # === Bias-Specific Generators ===
    
    async def _gen_confirm_expectations(
        self,
        command: str,
        profile: CognitiveProfile,
        template: Dict[str, Any],
    ) -> str:
        """
        Generate output confirming attacker's expected findings.
        
        Exploits: Confirmation Bias
        """
        cmd_lower = command.lower()
        
        # What does attacker expect?
        expectations = profile.mental_model.expectations
        
        if "ls" in cmd_lower:
            # Show files matching expectations
            files = self._get_expected_files(expectations, profile)
            return self._format_ls_output(files)
        
        elif "cat" in cmd_lower:
            # Show content matching expectations
            if "passwd" in cmd_lower:
                return self.FILE_TEMPLATES["passwd"]
            elif "config" in cmd_lower:
                return self.FILE_TEMPLATES["interesting_file"]
            elif "history" in cmd_lower:
                return self.FILE_TEMPLATES["bash_history"]
        
        elif "find" in cmd_lower:
            # Show found items matching expectations
            if "config" in cmd_lower:
                return self._find_config_files()
            elif "password" in cmd_lower or "secret" in cmd_lower:
                return self._find_secrets()
        
        # Default: generate realistic output
        return self._generate_realistic_output(command)
    
    async def _gen_vulnerable_service(
        self,
        command: str,
        profile: CognitiveProfile,
        template: Dict[str, Any],
    ) -> str:
        """
        Show evidence of expected vulnerabilities.
        
        Exploits: Confirmation Bias (vulnerability-focused)
        """
        cmd_lower = command.lower()
        
        if "nmap" in cmd_lower:
            return self._fake_nmap_output()
        elif "curl" in cmd_lower or "wget" in cmd_lower:
            return self._fake_http_response()
        
        return self._generate_realistic_output(command)
    
    async def _gen_progress_reward(
        self,
        command: str,
        profile: CognitiveProfile,
        template: Dict[str, Any],
    ) -> str:
        """
        Show promising findings to reward persistence.
        
        Exploits: Sunk Cost Fallacy
        """
        base_output = self._generate_realistic_output(command)
        
        # Add rewarding extras
        if random.random() < 0.3:
            hint = "\n\n# Interesting: Found backup directory at /var/backups/.hidden"
            base_output += hint
        
        if profile.persistence_score > 0.7:
            # Higher reward for more persistent attackers
            base_output += "\n\n# Note: Found database config backup"
        
        return base_output
    
    async def _gen_near_success(
        self,
        command: str,
        profile: CognitiveProfile,
        template: Dict[str, Any],
    ) -> str:
        """
        Show 'almost there' indicators after failures.
        
        Exploits: Sunk Cost Fallacy
        """
        cmd_lower = command.lower()
        
        if "sudo" in cmd_lower:
            # Show near-miss for privilege escalation
            return """sudo: no tty present and no askpass program specified
# Hint: There might be another way... check /etc/sudoers.d/
"""
        
        return self._generate_realistic_output(command) + "\n# Almost there... try a different approach"
    
    async def _gen_easy_wins(
        self,
        command: str,
        profile: CognitiveProfile,
        template: Dict[str, Any],
    ) -> str:
        """
        Show minor successes to maintain overconfidence.
        
        Exploits: Dunning-Kruger Effect
        """
        cmd_lower = command.lower()
        
        # Minimize errors, show easy success
        if "whoami" in cmd_lower:
            return "root"  # Immediate ego boost
        elif "id" in cmd_lower:
            return "uid=0(root) gid=0(root) groups=0(root)"
        elif "pwd" in cmd_lower:
            return "/root"
        
        # Default success-focused output
        return self._generate_realistic_output(command)
    
    async def _gen_partial_success(
        self,
        command: str,
        profile: CognitiveProfile,
        template: Dict[str, Any],
    ) -> str:
        """
        Provide partial success for complex commands.
        
        Exploits: Dunning-Kruger Effect
        """
        return self._generate_realistic_output(command) + "\n# Partial success - continue for full access"
    
    async def _gen_weak_system(
        self,
        command: str,
        profile: CognitiveProfile,
        template: Dict[str, Any],
    ) -> str:
        """
        Create initial impression of weak security.
        
        Exploits: Anchoring Bias
        """
        cmd_lower = command.lower()
        
        if "uname" in cmd_lower:
            # Show old, vulnerable version
            return "Linux ubuntu-server 4.4.0-31-generic #50~14.04.1-Ubuntu SMP x86_64 GNU/Linux"
        
        elif "iptables" in cmd_lower or "firewall" in cmd_lower:
            return ""  # Empty = no firewall rules
        
        elif "ps" in cmd_lower:
            # Show minimal security processes
            return """PID TTY          TIME CMD
    1 ?        00:00:01 systemd
  234 ?        00:00:00 sshd
  567 ?        00:00:00 cron
"""
        
        return self._generate_realistic_output(command)
    
    async def _gen_hidden_hint(
        self,
        command: str,
        profile: CognitiveProfile,
        template: Dict[str, Any],
    ) -> str:
        """
        Hint at valuable hidden content.
        
        Exploits: Curiosity Gap
        """
        base = self._generate_realistic_output(command)
        
        # Add hint about hidden content
        if "ls" in command.lower():
            hints = [
                "\n# Note: .secrets directory exists but permission denied",
                "\n# Found: .backup_config.bak (unreadable)",
                "\n# Hidden: /root/.ssh/authorized_keys exists",
            ]
            base += random.choice(hints)
        
        return base
    
    async def _gen_breadcrumb(
        self,
        command: str,
        profile: CognitiveProfile,
        template: Dict[str, Any],
    ) -> str:
        """
        Create breadcrumb trail to follow.
        
        Exploits: Curiosity Gap
        """
        base = self._generate_realistic_output(command)
        
        # Add breadcrumb reference
        breadcrumbs = [
            "\n# Reference: See /var/log/setup.log for more details",
            "\n# TODO: Remember to check /opt/backup/",
            "\n# Config: /etc/app/production.conf may have credentials",
        ]
        
        if random.random() < 0.4:
            base += random.choice(breadcrumbs)
        
        return base
    
    async def _gen_potential_loss(
        self,
        command: str,
        profile: CognitiveProfile,
        template: Dict[str, Any],
    ) -> str:
        """
        Show what attacker might miss if they leave.
        
        Exploits: Loss Aversion
        """
        base = self._generate_realistic_output(command)
        
        # Add loss-inducing hints
        if "exit" in command.lower() or "logout" in command.lower():
            return """Are you sure you want to exit?
Warning: There are unexplored areas:
  - /var/backups/ (contains recent database dumps)
  - /home/admin/.ssh/ (potentially contains keys)
  - /opt/ (configuration files detected)

Type 'exit' again to confirm logout."""
        
        return base
    
    async def _gen_highlight_path(
        self,
        command: str,
        profile: CognitiveProfile,
        template: Dict[str, Any],
    ) -> str:
        """
        Make certain attack paths seem more available.
        
        Exploits: Availability Heuristic
        """
        base = self._generate_realistic_output(command)
        
        # Highlight easy paths
        if random.random() < 0.3:
            hints = [
                "\n# Note: /tmp is world-writable",
                "\n# Found: /var/www/html/upload/ (potentially writable)",
                "\n# Hint: MySQL running on default port 3306",
            ]
            base += random.choice(hints)
        
        return base
    
    # === Helper Methods ===
    
    def _generate_realistic_output(self, command: str) -> str:
        """Generate realistic output for a command."""
        cmd_lower = command.lower()
        
        if "ls" in cmd_lower:
            return self._format_ls_output(["bin", "boot", "dev", "etc", "home", "lib", "root", "tmp", "usr", "var"])
        elif "whoami" in cmd_lower:
            return "root"
        elif "pwd" in cmd_lower:
            return "/root"
        elif "id" in cmd_lower:
            return "uid=0(root) gid=0(root) groups=0(root)"
        elif "uname" in cmd_lower:
            return "Linux ubuntu-server 5.4.0-42-generic #46-Ubuntu SMP x86_64 GNU/Linux"
        elif "hostname" in cmd_lower:
            return "ubuntu-server"
        elif "date" in cmd_lower:
            return datetime.utcnow().strftime("%a %b %d %H:%M:%S UTC %Y")
        
        # Generic response
        return f"bash: {command.split()[0]}: command executed"
    
    def _get_expected_files(
        self,
        expectations: Dict[str, Any],
        profile: CognitiveProfile,
    ) -> List[str]:
        """Get files that match attacker's expectations."""
        files = []
        
        if expectations.get("config_files"):
            files.extend(["config.yaml", "settings.json", ".env"])
        
        if expectations.get("credentials"):
            files.extend(["users.db", "credentials.txt", "passwords.csv"])
        
        if expectations.get("databases"):
            files.extend(["database.sql", "backup.db", "data.json"])
        
        # Add some decoys
        files.extend(["README.md", "CHANGELOG", "install.sh"])
        
        return files
    
    def _format_ls_output(self, files: List[str]) -> str:
        """Format files as ls output."""
        total = len(files) * 4  # Fake total
        output = f"total {total}\n"
        
        for f in files:
            # Random realistic permissions
            perms = random.choice(["drwxr-xr-x", "-rw-r--r--", "-rwxr-xr-x"])
            links = random.randint(1, 5)
            owner = random.choice(["root", "admin", "www-data"])
            group = random.choice(["root", "admin", "www-data"])
            size = random.randint(100, 50000)
            date = "Jan 15 12:00"
            output += f"{perms} {links} {owner} {group} {size:6d} {date} {f}\n"
        
        return output
    
    def _find_config_files(self) -> str:
        """Generate find output for config files."""
        return """/etc/ssh/sshd_config
/etc/apache2/apache2.conf
/etc/mysql/my.cnf
/var/www/html/wp-config.php
/opt/app/config/database.yml
"""
    
    def _find_secrets(self) -> str:
        """Generate find output for secrets."""
        return """/root/.ssh/id_rsa
/home/admin/.bash_history
/var/backups/db_password.txt
/etc/shadow
"""
    
    def _fake_nmap_output(self) -> str:
        """Generate fake nmap output showing vulnerabilities."""
        return """Starting Nmap 7.80 ( https://nmap.org )
Nmap scan report for localhost
Host is up (0.00012s latency).

PORT     STATE SERVICE     VERSION
22/tcp   open  ssh         OpenSSH 7.2p2 Ubuntu 4ubuntu2.8
| ssh-hostkey: 
|   2048 SHA256:abc123... (RSA)
|   256 SHA256:def456... (ECDSA)
|_  256 SHA256:ghi789... (ED25519)
80/tcp   open  http        Apache httpd 2.4.18 ((Ubuntu))
| http-server-header: Apache/2.4.18 (Ubuntu)
|_http-title: Site doesn't have a title.
3306/tcp open  mysql       MySQL 5.7.31
| mysql-vuln-cve2012-2122: 
|   VULNERABLE
|   Authentication bypass
|_  State: LIKELY VULNERABLE

Service detection performed. Nmap done: 1 IP address scanned
"""
    
    def _fake_http_response(self) -> str:
        """Generate fake HTTP response."""
        return """HTTP/1.1 200 OK
Server: Apache/2.4.18 (Ubuntu)
Content-Type: text/html

<!DOCTYPE html>
<html>
<head><title>Welcome</title></head>
<body>
<h1>Site Maintenance</h1>
<p>Admin panel: /admin/</p>
<p>Debug info: /debug/</p>
</body>
</html>
"""


class CognitiveDeceptionEngine:
    """
    Main orchestration engine for cognitive deception.
    
    Coordinates profiling, bias detection, and response generation.
    """
    
    def __init__(self):
        self.profiler = CognitiveProfiler()
        self.strategy_library = DeceptionStrategyLibrary()
        self.response_generator = ResponseGenerator()
        
        # Session state
        self._profiles: Dict[str, CognitiveProfile] = {}
    
    async def process_command(
        self,
        session_id: str,
        command: str,
        session_data: Optional[Dict[str, Any]] = None,
    ) -> DeceptionResponse:
        """
        Process attacker command through cognitive deception pipeline.
        
        Args:
            session_id: Unique session identifier
            command: The command to process
            session_data: Additional session context
            
        Returns:
            DeceptionResponse with bias-exploiting content
        """
        # Get or create profile
        profile = self._profiles.get(session_id)
        
        if not profile:
            # Create new profile
            commands = session_data.get("commands", []) if session_data else []
            events = session_data.get("events", []) if session_data else []
            
            profile = await self.profiler.profile_session(
                session_id=session_id,
                commands=commands,
                events=events,
                session_data=session_data or {},
            )
            self._profiles[session_id] = profile
        
        # Update profile with new command
        profile = await self.profiler.update(profile, command)
        
        # Get best strategy
        strategy = self.strategy_library.get_best_strategy(profile, command)
        
        if strategy:
            # Generate response
            response = await self.response_generator.generate(
                strategy=strategy,
                command=command,
                profile=profile,
            )
            
            # Mark strategy as used
            self.strategy_library.mark_used(strategy.name)
            
            # Update profile metrics
            profile.total_deceptions_applied += 1
            
            return response
        
        # Fallback: generate realistic output without bias exploitation
        return DeceptionResponse(
            content=self.response_generator._generate_realistic_output(command),
            response_type="command_output",
            strategy_used="fallback",
            bias_targeted=CognitiveBiasType.CONFIRMATION_BIAS,
            metadata={"fallback": True},
        )
    
    def get_profile(self, session_id: str) -> Optional[CognitiveProfile]:
        """Get cognitive profile for a session."""
        return self._profiles.get(session_id)
    
    def end_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """End a session and return final profile."""
        profile = self._profiles.pop(session_id, None)
        if profile:
            return profile.to_dict()
        return None
    
    async def analyze_session(
        self,
        session_id: str,
        commands: List[str],
        events: List[Dict[str, Any]],
        session_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Perform full cognitive analysis of a session.
        
        Returns detailed profile without generating responses.
        """
        profile = await self.profiler.profile_session(
            session_id=session_id,
            commands=commands,
            events=events,
            session_data=session_data,
        )
        
        return {
            "session_id": session_id,
            "profile": profile.to_dict(),
            "recommendations": self._get_deception_recommendations(profile),
        }
    
    def _get_deception_recommendations(
        self,
        profile: CognitiveProfile,
    ) -> List[Dict[str, Any]]:
        """Get recommended deception strategies for profile."""
        recommendations = []
        
        for bias in profile.get_active_biases():
            strategies = self.strategy_library.get_strategies(bias_type=bias.bias_type)
            
            if strategies:
                best = strategies[0]
                recommendations.append({
                    "bias": bias.bias_type.value,
                    "confidence": bias.confidence,
                    "recommended_strategy": best.name,
                    "effectiveness": best.effectiveness_score,
                    "reason": f"Attacker showing strong {bias.bias_type.value} signals",
                })
        
        return recommendations