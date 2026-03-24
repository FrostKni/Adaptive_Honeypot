"""
Cognitive-Behavioral Deception Framework - Cognitive Profiler.

Builds psychological profiles of attackers based on behavioral signals.
"""
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import re
import logging
import asyncio
from collections import Counter

logger = logging.getLogger(__name__)


class CognitiveBiasType(str, Enum):
    """Types of cognitive biases that can be exploited."""
    CONFIRMATION_BIAS = "confirmation_bias"
    ANCHORING = "anchoring"
    SUNK_COST = "sunk_cost"
    DUNNING_KRUGER = "dunning_kruger"
    AVAILABILITY_HEURISTIC = "availability_heuristic"
    LOSS_AVERSION = "loss_aversion"
    AUTHORITY_BIAS = "authority_bias"
    CURIOSITY_GAP = "curiosity_gap"


@dataclass
class DetectedBias:
    """A detected cognitive bias with confidence score."""
    bias_type: CognitiveBiasType
    confidence: float
    signals_matched: List[str] = field(default_factory=list)
    signal_scores: Dict[str, float] = field(default_factory=dict)
    first_detected_at: datetime = field(default_factory=datetime.utcnow)
    detection_count: int = 1
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "bias_type": self.bias_type.value,
            "confidence": self.confidence,
            "signals_matched": self.signals_matched,
            "signal_scores": self.signal_scores,
            "first_detected_at": self.first_detected_at.isoformat(),
            "detection_count": self.detection_count,
        }


@dataclass
class MentalModel:
    """Represents attacker's mental model of the system."""
    beliefs: Dict[str, Any] = field(default_factory=dict)
    knowledge: List[str] = field(default_factory=list)
    goals: List[str] = field(default_factory=list)
    expectations: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.5
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "beliefs": self.beliefs,
            "knowledge": self.knowledge,
            "goals": self.goals,
            "expectations": self.expectations,
            "confidence": self.confidence,
        }


@dataclass
class CognitiveProfile:
    """Complete cognitive profile of an attacker session."""
    session_id: str
    detected_biases: List[DetectedBias] = field(default_factory=list)
    mental_model: MentalModel = field(default_factory=MentalModel)
    
    # Cognitive metrics
    overconfidence_score: float = 0.0
    persistence_score: float = 0.0
    tunnel_vision_score: float = 0.0
    curiosity_score: float = 0.0
    
    # Behavioral metrics
    exploration_diversity: float = 0.0
    error_tolerance: float = 0.5
    learning_rate: float = 0.0
    
    # Deception metrics
    total_deceptions_applied: int = 0
    successful_deceptions: int = 0
    deception_success_rate: float = 0.0
    suspicion_level: float = 0.0
    
    # Behavioral signals collected
    signals: Dict[str, Any] = field(default_factory=dict)
    
    def get_bias_confidence(self, bias_type: CognitiveBiasType) -> float:
        """Get confidence score for a specific bias."""
        for bias in self.detected_biases:
            if bias.bias_type == bias_type:
                return bias.confidence
        return 0.0
    
    def get_active_biases(self, threshold: float = 0.5) -> List[DetectedBias]:
        """Get biases above confidence threshold."""
        return [b for b in self.detected_biases if b.confidence >= threshold]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "detected_biases": [b.to_dict() for b in self.detected_biases],
            "mental_model": self.mental_model.to_dict(),
            "metrics": {
                "overconfidence_score": self.overconfidence_score,
                "persistence_score": self.persistence_score,
                "tunnel_vision_score": self.tunnel_vision_score,
                "curiosity_score": self.curiosity_score,
                "exploration_diversity": self.exploration_diversity,
                "error_tolerance": self.error_tolerance,
                "learning_rate": self.learning_rate,
            },
            "deception": {
                "total_applied": self.total_deceptions_applied,
                "successful": self.successful_deceptions,
                "success_rate": self.deception_success_rate,
                "suspicion_level": self.suspicion_level,
            },
        }


class BiasDetector:
    """
    Detect cognitive biases from attacker behavior.
    
    Uses multiple signals to identify which biases the attacker is exhibiting.
    """
    
    # Bias detection signals and thresholds
    BIAS_CONFIG = {
        CognitiveBiasType.CONFIRMATION_BIAS: {
            "signals": {
                "repeated_similar_commands": {"weight": 0.8, "threshold": 3},
                "low_exploration_diversity": {"weight": 0.7, "threshold": 0.3},
                "ignoring_error_messages": {"weight": 0.6, "threshold": 2},
                "single_directory_focus": {"weight": 0.7, "threshold": 0.6},
                "seeking_expected_pattern": {"weight": 0.9, "threshold": 0.5},
            },
            "min_confidence": 0.5,
        },
        CognitiveBiasType.SUNK_COST: {
            "signals": {
                "long_session_duration": {"weight": 0.7, "threshold": 1800},  # 30 min
                "multiple_failed_attempts": {"weight": 0.8, "threshold": 5},
                "returning_to_same_path": {"weight": 0.75, "threshold": 0.4},
                "increasing_command_frequency": {"weight": 0.65, "threshold": 1.2},
                "ignoring_exit_signals": {"weight": 0.6, "threshold": 2},
            },
            "min_confidence": 0.5,
        },
        CognitiveBiasType.DUNNING_KRUGER: {
            "signals": {
                "complexity_mismatch": {"weight": 0.85, "threshold": 0.5},
                "no_reconnaissance_phase": {"weight": 0.8, "threshold": 1},
                "immediate_exploitation_attempt": {"weight": 0.9, "threshold": 1},
                "ignoring_complex_errors": {"weight": 0.7, "threshold": 2},
                "overestimating_ability": {"weight": 0.75, "threshold": 0.6},
            },
            "min_confidence": 0.55,
        },
        CognitiveBiasType.ANCHORING: {
            "signals": {
                "early_session_commands": {"weight": 0.8, "threshold": 5},
                "persistent_initial_belief": {"weight": 0.85, "threshold": 0.7},
                "reference_to_early_info": {"weight": 0.75, "threshold": 2},
            },
            "min_confidence": 0.5,
        },
        CognitiveBiasType.CURIOSITY_GAP: {
            "signals": {
                "exploring_hidden_files": {"weight": 0.8, "threshold": 2},
                "seeking_configuration": {"weight": 0.7, "threshold": 3},
                "enumeration_behavior": {"weight": 0.75, "threshold": 5},
                "following_breadcrumbs": {"weight": 0.85, "threshold": 1},
            },
            "min_confidence": 0.5,
        },
        CognitiveBiasType.LOSS_AVERSION: {
            "signals": {
                "protective_behavior": {"weight": 0.7, "threshold": 2},
                "backup_creation": {"weight": 0.8, "threshold": 1},
                "careful_exploration": {"weight": 0.6, "threshold": 0.5},
            },
            "min_confidence": 0.5,
        },
    }
    
    def __init__(self):
        self._signal_calculators = {
            "repeated_similar_commands": self._calc_repeated_similar_commands,
            "low_exploration_diversity": self._calc_exploration_diversity,
            "ignoring_error_messages": self._calc_ignoring_errors,
            "single_directory_focus": self._calc_single_directory_focus,
            "seeking_expected_pattern": self._calc_seeking_expected_pattern,
            "long_session_duration": self._calc_session_duration,
            "multiple_failed_attempts": self._calc_failed_attempts,
            "returning_to_same_path": self._calc_returning_path,
            "increasing_command_frequency": self._calc_command_frequency,
            "ignoring_exit_signals": self._calc_ignoring_exit_signals,
            "complexity_mismatch": self._calc_complexity_mismatch,
            "no_reconnaissance_phase": self._calc_no_reconnaissance,
            "immediate_exploitation_attempt": self._calc_immediate_exploitation,
            "ignoring_complex_errors": self._calc_ignoring_complex_errors,
            "overestimating_ability": self._calc_overestimating_ability,
            "early_session_commands": self._calc_early_session_commands,
            "persistent_initial_belief": self._calc_persistent_belief,
            "reference_to_early_info": self._calc_reference_early_info,
            "exploring_hidden_files": self._calc_exploring_hidden_files,
            "seeking_configuration": self._calc_seeking_configuration,
            "enumeration_behavior": self._calc_enumeration_behavior,
            "following_breadcrumbs": self._calc_following_breadcrumbs,
            "protective_behavior": self._calc_protective_behavior,
            "backup_creation": self._calc_backup_creation,
            "careful_exploration": self._calc_careful_exploration,
        }
    
    async def detect(self, profile: CognitiveProfile) -> List[DetectedBias]:
        """
        Detect cognitive biases from profile signals.
        
        Returns list of detected biases with confidence scores.
        """
        detected = []
        
        for bias_type, config in self.BIAS_CONFIG.items():
            bias_result = await self._detect_single_bias(profile, bias_type, config)
            if bias_result and bias_result.confidence >= config.get("min_confidence", 0.5):
                detected.append(bias_result)
        
        return sorted(detected, key=lambda x: x.confidence, reverse=True)
    
    async def _detect_single_bias(
        self, 
        profile: CognitiveProfile,
        bias_type: CognitiveBiasType,
        config: Dict[str, Any],
    ) -> Optional[DetectedBias]:
        """Detect a single bias type."""
        signals_matched = []
        signal_scores = {}
        total_weight = 0
        weighted_score = 0
        
        for signal_name, signal_config in config["signals"].items():
            calculator = self._signal_calculators.get(signal_name)
            if calculator:
                score = calculator(profile)
                signal_scores[signal_name] = score
                
                threshold = signal_config.get("threshold", 0.5)
                weight = signal_config.get("weight", 1.0)
                
                if score >= threshold:
                    signals_matched.append(signal_name)
                    weighted_score += weight * score
                    total_weight += weight
        
        if total_weight == 0:
            return None
            
        confidence = weighted_score / total_weight if total_weight > 0 else 0
        
        return DetectedBias(
            bias_type=bias_type,
            confidence=min(confidence, 1.0),
            signals_matched=signals_matched,
            signal_scores=signal_scores,
        )
    
    # === Signal Calculators ===
    
    def _calc_repeated_similar_commands(self, profile: CognitiveProfile) -> float:
        """Calculate if attacker is repeating similar commands."""
        commands = profile.signals.get("commands", [])
        if len(commands) < 3:
            return 0.0
        
        # Group similar commands
        base_commands = [cmd.split()[0] if cmd else "" for cmd in commands]
        counter = Counter(base_commands)
        
        # If any command repeated more than 3 times
        max_repeat = max(counter.values()) if counter else 0
        return min(max_repeat / 5, 1.0)
    
    def _calc_exploration_diversity(self, profile: CognitiveProfile) -> float:
        """Calculate exploration diversity (inverse for low diversity)."""
        diversity = profile.signals.get("exploration_diversity", 1.0)
        # Return inverse - low diversity = high signal
        return 1.0 - diversity
    
    def _calc_ignoring_errors(self, profile: CognitiveProfile) -> float:
        """Calculate if attacker ignores error messages."""
        error_count = profile.signals.get("error_count", 0)
        commands_after_error = profile.signals.get("commands_after_error", 0)
        
        if error_count == 0:
            return 0.0
        
        # High ratio of continuing despite errors
        ratio = commands_after_error / error_count if error_count > 0 else 0
        return min(ratio / 3, 1.0)
    
    def _calc_single_directory_focus(self, profile: CognitiveProfile) -> float:
        """Calculate focus on single directory."""
        directories = profile.signals.get("directories_visited", set())
        if not directories:
            return 0.0
        
        commands = profile.signals.get("commands", [])
        dir_mentions = Counter()
        
        for cmd in commands:
            for d in directories:
                if d in cmd:
                    dir_mentions[d] += 1
        
        if not dir_mentions:
            return 0.0
        
        # High if one directory dominates
        max_count = max(dir_mentions.values())
        total = sum(dir_mentions.values())
        return max_count / total if total > 0 else 0.0
    
    def _calc_seeking_expected_pattern(self, profile: CognitiveProfile) -> float:
        """Calculate if seeking expected patterns."""
        expected_patterns = profile.mental_model.expectations.get("patterns_sought", [])
        return min(len(expected_patterns) / 3, 1.0)
    
    def _calc_session_duration(self, profile: CognitiveProfile) -> float:
        """Calculate session duration signal."""
        duration = profile.signals.get("session_duration_seconds", 0)
        return min(duration / 3600, 1.0)  # Normalize to 1 hour
    
    def _calc_failed_attempts(self, profile: CognitiveProfile) -> float:
        """Calculate failed attempts."""
        failed = profile.signals.get("failed_attempts", 0)
        return min(failed / 10, 1.0)
    
    def _calc_returning_path(self, profile: CognitiveProfile) -> float:
        """Calculate return rate to same path."""
        return profile.signals.get("path_return_rate", 0.0)
    
    def _calc_command_frequency(self, profile: CognitiveProfile) -> float:
        """Calculate if command frequency is increasing."""
        return profile.signals.get("command_frequency_increase", 0.0)
    
    def _calc_ignoring_exit_signals(self, profile: CognitiveProfile) -> float:
        """Calculate ignoring signals to exit."""
        return profile.signals.get("exit_signals_ignored", 0.0)
    
    def _calc_complexity_mismatch(self, profile: CognitiveProfile) -> float:
        """Calculate mismatch between command complexity and skill."""
        command_complexity = profile.signals.get("avg_command_complexity", 0)
        skill_evidence = profile.signals.get("skill_evidence", 0.5)
        
        # High mismatch = high complexity commands with low skill evidence
        return max(0, command_complexity - skill_evidence)
    
    def _calc_no_reconnaissance(self, profile: CognitiveProfile) -> float:
        """Calculate lack of reconnaissance phase."""
        has_recon = profile.signals.get("has_reconnaissance_phase", True)
        return 0.0 if has_recon else 1.0
    
    def _calc_immediate_exploitation(self, profile: CognitiveProfile) -> float:
        """Calculate immediate exploitation attempts."""
        first_exploit_index = profile.signals.get("first_exploit_command_index", -1)
        if first_exploit_index == -1:
            return 0.0
        # Earlier = higher score
        return max(0, 1 - (first_exploit_index / 10))
    
    def _calc_ignoring_complex_errors(self, profile: CognitiveProfile) -> float:
        """Calculate ignoring complex error messages."""
        return profile.signals.get("complex_errors_ignored", 0.0)
    
    def _calc_overestimating_ability(self, profile: CognitiveProfile) -> float:
        """Calculate overestimation of ability."""
        return profile.overconfidence_score
    
    def _calc_early_session_commands(self, profile: CognitiveProfile) -> float:
        """Calculate anchoring from early commands."""
        first_commands = profile.signals.get("first_5_commands", [])
        return 1.0 if len(first_commands) <= 5 else 0.5
    
    def _calc_persistent_belief(self, profile: CognitiveProfile) -> float:
        """Calculate persistence of initial belief."""
        return profile.signals.get("belief_persistence", 0.0)
    
    def _calc_reference_early_info(self, profile: CognitiveProfile) -> float:
        """Calculate references to early information."""
        return profile.signals.get("early_info_references", 0.0)
    
    def _calc_exploring_hidden_files(self, profile: CognitiveProfile) -> float:
        """Calculate exploration of hidden files."""
        hidden_accessed = profile.signals.get("hidden_files_accessed", 0)
        return min(hidden_accessed / 5, 1.0)
    
    def _calc_seeking_configuration(self, profile: CognitiveProfile) -> float:
        """Calculate seeking configuration files."""
        config_accessed = profile.signals.get("config_files_accessed", 0)
        return min(config_accessed / 5, 1.0)
    
    def _calc_enumeration_behavior(self, profile: CognitiveProfile) -> float:
        """Calculate enumeration behavior."""
        enum_commands = profile.signals.get("enumeration_commands", 0)
        return min(enum_commands / 10, 1.0)
    
    def _calc_following_breadcrumbs(self, profile: CognitiveProfile) -> float:
        """Calculate following breadcrumbs (hints)."""
        breadcrumbs_followed = profile.signals.get("breadcrumbs_followed", 0)
        return min(breadcrumbs_followed / 3, 1.0)
    
    def _calc_protective_behavior(self, profile: CognitiveProfile) -> float:
        """Calculate protective behavior."""
        return profile.signals.get("protective_actions", 0.0)
    
    def _calc_backup_creation(self, profile: CognitiveProfile) -> float:
        """Calculate backup creation attempts."""
        backup_cmds = profile.signals.get("backup_commands", 0)
        return min(backup_cmds / 2, 1.0)
    
    def _calc_careful_exploration(self, profile: CognitiveProfile) -> float:
        """Calculate careful exploration pattern."""
        return profile.signals.get("carefulness_score", 0.0)


class CognitiveProfiler:
    """
    Build psychological profile of attacker based on behavior.
    
    Main entry point for cognitive analysis.
    """
    
    def __init__(self):
        self.bias_detector = BiasDetector()
        self._command_analyzers = []
    
    async def profile_session(
        self, 
        session_id: str,
        commands: List[str],
        events: List[Dict[str, Any]],
        session_data: Dict[str, Any],
    ) -> CognitiveProfile:
        """
        Build complete cognitive profile from session data.
        
        Args:
            session_id: Unique session identifier
            commands: List of commands executed
            events: List of session events
            session_data: Additional session metadata
            
        Returns:
            CognitiveProfile with biases and mental model
        """
        profile = CognitiveProfile(session_id=session_id)
        
        # Extract signals from commands and events
        profile.signals = self._extract_signals(commands, events, session_data)
        
        # Calculate behavioral metrics
        profile.overconfidence_score = self._calc_overconfidence(profile.signals)
        profile.persistence_score = self._calc_persistence(profile.signals)
        profile.tunnel_vision_score = self._calc_tunnel_vision(profile.signals)
        profile.curiosity_score = self._calc_curiosity(profile.signals)
        profile.exploration_diversity = self._calc_diversity(profile.signals)
        profile.error_tolerance = self._calc_error_tolerance(profile.signals)
        profile.learning_rate = self._calc_learning_rate(profile.signals)
        
        # Detect cognitive biases
        profile.detected_biases = await self.bias_detector.detect(profile)
        
        # Build mental model
        profile.mental_model = self._infer_mental_model(commands, events, profile.signals)
        
        return profile
    
    async def update(
        self,
        profile: CognitiveProfile,
        new_command: str,
        event: Optional[Dict[str, Any]] = None,
    ) -> CognitiveProfile:
        """
        Update profile with new command.
        
        Incremental update for real-time profiling.
        """
        # Add command to signals
        if "commands" not in profile.signals:
            profile.signals["commands"] = []
        profile.signals["commands"].append(new_command)
        
        # Update command count
        profile.signals["total_commands"] = profile.signals.get("total_commands", 0) + 1
        
        # Re-detect biases
        new_biases = await self.bias_detector.detect(profile)
        
        # Merge with existing biases
        for new_bias in new_biases:
            existing = next(
                (b for b in profile.detected_biases if b.bias_type == new_bias.bias_type),
                None
            )
            if existing:
                existing.confidence = (existing.confidence + new_bias.confidence) / 2
                existing.detection_count += 1
                existing.signals_matched = list(set(existing.signals_matched + new_bias.signals_matched))
            else:
                profile.detected_biases.append(new_bias)
        
        # Update mental model
        self._update_mental_model(profile.mental_model, new_command)
        
        return profile
    
    def _extract_signals(
        self,
        commands: List[str],
        events: List[Dict[str, Any]],
        session_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Extract behavioral signals from session data."""
        signals = {
            "commands": commands,
            "total_commands": len(commands),
            "session_duration_seconds": session_data.get("duration_seconds", 0),
            "failed_attempts": 0,
            "error_count": 0,
            "commands_after_error": 0,
            "directories_visited": set(),
            "files_accessed": set(),
            "hidden_files_accessed": 0,
            "config_files_accessed": 0,
            "enumeration_commands": 0,
            "exploitation_commands": 0,
            "first_5_commands": commands[:5] if commands else [],
            "first_exploit_command_index": -1,
            "has_reconnaissance_phase": False,
            "exploration_diversity": 0.0,
            "path_return_rate": 0.0,
            "command_frequency_increase": 0.0,
        }
        
        error_encountered = False
        path_sequence = []
        recon_commands = {"whoami", "id", "uname", "hostname", "pwd", "ls", "cat"}
        exploit_indicators = {"wget", "curl", "chmod +x", "bash -i", "nc -", "/dev/tcp"}
        
        for i, cmd in enumerate(commands):
            cmd_lower = cmd.lower() if cmd else ""
            base_cmd = cmd_lower.split()[0] if cmd_lower else ""
            
            # Track reconnaissance
            if base_cmd in recon_commands:
                signals["has_reconnaissance_phase"] = True
            
            # Track exploitation
            for indicator in exploit_indicators:
                if indicator in cmd_lower:
                    if signals["first_exploit_command_index"] == -1:
                        signals["first_exploit_command_index"] = i
                    signals["exploitation_commands"] += 1
            
            # Track directories
            dir_match = re.findall(r'(?:cd|ls|cat|find|grep)\s+([^\s;&|]+)', cmd_lower)
            for d in dir_match:
                signals["directories_visited"].add(d)
            
            # Track hidden files
            if '.' in cmd_lower and ('.' in cmd_lower.split()[-1] or '/.' in cmd_lower):
                signals["hidden_files_accessed"] += 1
            
            # Track config files
            config_patterns = ['config', 'passwd', 'shadow', 'ssh', 'hosts', 'crontab']
            for pattern in config_patterns:
                if pattern in cmd_lower:
                    signals["config_files_accessed"] += 1
            
            # Track enumeration
            if base_cmd in {'find', 'grep', 'awk', 'sed', 'xargs'}:
                signals["enumeration_commands"] += 1
            
            # Track path sequence
            if 'cd ' in cmd_lower:
                path = cmd_lower.split('cd ')[1].split()[0] if 'cd ' in cmd_lower else ""
                path_sequence.append(path)
            
            # Track after-error behavior
            if signals["error_count"] > 0 and not error_encountered:
                error_encountered = True
            
            if error_encountered:
                signals["commands_after_error"] += 1
        
        # Calculate derived signals
        if path_sequence and len(path_sequence) > 1:
            # Calculate return rate
            unique_paths = len(set(path_sequence))
            total_cd = len(path_sequence)
            signals["path_return_rate"] = 1 - (unique_paths / total_cd) if total_cd > 0 else 0
        
        # Convert set to list for JSON serialization
        signals["directories_visited"] = list(signals["directories_visited"])
        signals["files_accessed"] = list(signals["files_accessed"])
        
        # Calculate exploration diversity
        if commands:
            unique_base_cmds = len(set(cmd.split()[0] if cmd else "" for cmd in commands))
            signals["exploration_diversity"] = unique_base_cmds / len(commands)
        
        # Calculate command frequency increase
        if len(commands) >= 10:
            first_half = len(commands[:len(commands)//2])
            second_half = len(commands[len(commands)//2:])
            # This would need timestamps for proper calculation
            signals["command_frequency_increase"] = 0.0
        
        # Extract from events
        for event in events:
            if event.get("event_type") == "error":
                signals["error_count"] += 1
            elif event.get("event_type") == "login_failed":
                signals["failed_attempts"] += 1
        
        return signals
    
    def _infer_mental_model(
        self,
        commands: List[str],
        events: List[Dict[str, Any]],
        signals: Dict[str, Any],
    ) -> MentalModel:
        """Infer attacker's mental model from behavior."""
        model = MentalModel()
        
        # Infer beliefs about system
        model.beliefs = {
            "os_type": self._infer_os_belief(commands),
            "security_level": self._infer_security_belief(commands),
            "is_production": self._infer_production_belief(commands),
        }
        
        # Infer knowledge gained
        model.knowledge = self._infer_knowledge(commands, events)
        
        # Infer goals
        model.goals = self._infer_goals(commands, signals)
        
        # Infer expectations
        model.expectations = self._infer_expectations(commands)
        
        return model
    
    def _infer_os_belief(self, commands: List[str]) -> str:
        """Infer what attacker believes about OS."""
        for cmd in commands:
            cmd_lower = cmd.lower() if cmd else ""
            if "uname" in cmd_lower:
                return "Linux (discovered)"
            if "ver" in cmd_lower or "systeminfo" in cmd_lower:
                return "Windows (discovered)"
        return "Linux (assumed)"
    
    def _infer_security_belief(self, commands: List[str]) -> str:
        """Infer what attacker believes about security level."""
        for cmd in commands:
            cmd_lower = cmd.lower() if cmd else ""
            if "iptables" in cmd_lower or "firewall" in cmd_lower:
                return "Checking security"
            if "selinux" in cmd_lower or "apparmor" in cmd_lower:
                return "Checking hardening"
        return "Unknown"
    
    def _infer_production_belief(self, commands: List[str]) -> bool:
        """Infer if attacker believes this is production."""
        for cmd in commands:
            cmd_lower = cmd.lower() if cmd else ""
            if "www" in cmd_lower or "var/log" in cmd_lower:
                return True
        return False
    
    def _infer_knowledge(self, commands: List[str], events: List[Dict[str, Any]]) -> List[str]:
        """Infer what attacker has learned."""
        knowledge = []
        
        for cmd in commands:
            cmd_lower = cmd.lower() if cmd else ""
            
            if "whoami" in cmd_lower:
                knowledge.append("current_user")
            if "id" in cmd_lower:
                knowledge.append("user_groups")
            if "cat /etc/passwd" in cmd_lower:
                knowledge.append("user_list")
            if "ifconfig" in cmd_lower or "ip addr" in cmd_lower:
                knowledge.append("network_config")
            if "netstat" in cmd_lower or "ss" in cmd_lower:
                knowledge.append("network_connections")
            if "ps aux" in cmd_lower or "ps -ef" in cmd_lower:
                knowledge.append("running_processes")
        
        return list(set(knowledge))
    
    def _infer_goals(self, commands: List[str], signals: Dict[str, Any]) -> List[str]:
        """Infer attacker objectives."""
        goals = []
        
        # Check for exploitation
        if signals.get("exploitation_commands", 0) > 0:
            goals.append("exploitation")
        
        # Check for data exfiltration
        for cmd in commands:
            cmd_lower = cmd.lower() if cmd else ""
            if any(x in cmd_lower for x in ["tar", "zip", "scp", "rsync", "base64"]):
                goals.append("data_exfiltration")
                break
        
        # Check for privilege escalation
        for cmd in commands:
            cmd_lower = cmd.lower() if cmd else ""
            if "sudo" in cmd_lower or "su " in cmd_lower:
                goals.append("privilege_escalation")
                break
        
        # Check for persistence
        for cmd in commands:
            cmd_lower = cmd.lower() if cmd else ""
            if any(x in cmd_lower for x in ["crontab", "systemctl", "/etc/rc", "ssh-key"]):
                goals.append("persistence")
                break
        
        return goals if goals else ["reconnaissance"]
    
    def _infer_expectations(self, commands: List[str]) -> Dict[str, Any]:
        """Infer what attacker expects to find."""
        expectations = {}
        
        for cmd in commands:
            cmd_lower = cmd.lower() if cmd else ""
            
            if "config" in cmd_lower:
                expectations["config_files"] = True
            if "password" in cmd_lower or "passwd" in cmd_lower:
                expectations["credentials"] = True
            if "backup" in cmd_lower:
                expectations["backups"] = True
            if "database" in cmd_lower or "mysql" in cmd_lower or "postgres" in cmd_lower:
                expectations["databases"] = True
        
        return expectations
    
    def _update_mental_model(self, model: MentalModel, new_command: str) -> None:
        """Update mental model with new command."""
        cmd_lower = new_command.lower()
        
        # Update knowledge
        if "whoami" in cmd_lower:
            if "current_user" not in model.knowledge:
                model.knowledge.append("current_user")
        
        # Update goals
        if "wget" in cmd_lower or "curl" in cmd_lower:
            if "exploitation" not in model.goals:
                model.goals.append("exploitation")
    
    # === Metric Calculators ===
    
    def _calc_overconfidence(self, signals: Dict[str, Any]) -> float:
        """Calculate overconfidence score."""
        # High if no recon but immediate exploitation
        has_recon = signals.get("has_reconnaissance_phase", False)
        immediate_exploit = signals.get("first_exploit_command_index", -1)
        
        score = 0.0
        if not has_recon:
            score += 0.3
        if immediate_exploit >= 0 and immediate_exploit < 5:
            score += 0.4
        
        return min(score, 1.0)
    
    def _calc_persistence(self, signals: Dict[str, Any]) -> float:
        """Calculate persistence score."""
        duration = signals.get("session_duration_seconds", 0)
        failed = signals.get("failed_attempts", 0)
        
        score = 0.0
        if duration > 600:  # 10 min
            score += 0.3
        if duration > 1800:  # 30 min
            score += 0.3
        if failed > 5:
            score += 0.2
        
        return min(score, 1.0)
    
    def _calc_tunnel_vision(self, signals: Dict[str, Any]) -> float:
        """Calculate tunnel vision score."""
        diversity = signals.get("exploration_diversity", 1.0)
        return 1.0 - diversity
    
    def _calc_curiosity(self, signals: Dict[str, Any]) -> float:
        """Calculate curiosity score."""
        hidden = signals.get("hidden_files_accessed", 0)
        config = signals.get("config_files_accessed", 0)
        enum = signals.get("enumeration_commands", 0)
        
        score = 0.0
        if hidden > 0:
            score += 0.3
        if config > 0:
            score += 0.3
        if enum > 5:
            score += 0.4
        
        return min(score, 1.0)
    
    def _calc_diversity(self, signals: Dict[str, Any]) -> float:
        """Calculate exploration diversity."""
        return signals.get("exploration_diversity", 0.5)
    
    def _calc_error_tolerance(self, signals: Dict[str, Any]) -> float:
        """Calculate error tolerance."""
        errors = signals.get("error_count", 0)
        after_error = signals.get("commands_after_error", 0)
        
        if errors == 0:
            return 0.5  # Neutral
        
        # High tolerance = continuing despite errors
        return min(after_error / (errors * 3), 1.0)
    
    def _calc_learning_rate(self, signals: Dict[str, Any]) -> float:
        """Calculate learning rate."""
        # Would need more complex analysis
        return 0.5  # Neutral for now