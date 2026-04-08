"""
Enhanced AI Analyzer for attack analysis.
Multi-provider support with fallback chains, caching, and structured output.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import logging
import asyncio

from pydantic import BaseModel

from src.core.config import settings
from src.ai.providers.base import (
    AIProvider,
    AIProviderInterface,
    AIResponse,
    AIAnalysisResult,
    AnalysisCache,
    create_provider,
)


logger = logging.getLogger(__name__)


# ==================== Prompts ====================

ATTACK_ANALYSIS_PROMPT = """Analyze the following honeypot attack data and provide structured insights.

Attack Data:
{attack_summary}

Provide your analysis as a JSON object with these fields:
{schema}

Important:
- Be specific and actionable in your recommendations
- Consider MITRE ATT&CK framework for classification
- Provide confidence scores based on available evidence
- Consider both immediate threats and long-term patterns
"""

ATTACK_ANALYSIS_SCHEMA = {
    "attack_sophistication": "One of: low, medium, high (technical complexity of attacks)",
    "attacker_skill_level": "One of: script_kiddie, intermediate, advanced, expert",
    "attack_objectives": "List of attacker goals (e.g., reconnaissance, exploitation, data_theft)",
    "threat_level": "One of: low, medium, high, critical",
    "recommended_interaction_level": "One of: low, medium, high (how much to engage)",
    "deception_strategies": "List of deception tactics to employ",
    "configuration_changes": "Object with specific honeypot config modifications",
    "confidence": "Float between 0 and 1 indicating confidence in analysis",
    "reasoning": "Brief explanation of the analysis",
    "mitre_attack_ids": "List of relevant MITRE ATT&CK technique IDs"
}

ADAPTATION_PROMPT = """Based on the AI analysis and current configuration, generate specific adaptation recommendations.

Current Configuration:
{current_config}

Analysis Result:
{analysis}

Generate updated configuration changes that:
1. Increase engagement for sophisticated attackers
2. Deploy appropriate deception strategies
3. Adjust interaction level based on threat
4. Add relevant fake data based on attacker interests

Output as JSON object with specific configuration changes.
"""


class EnhancedAIAnalyzer:
    """
    Production-grade AI analyzer with:
    - Multi-provider support
    - Automatic fallback chains
    - Response caching
    - Structured output parsing
    - Streaming support
    """
    
    def __init__(
        self,
        primary_provider: str = None,
        fallback_providers: List[str] = None,
        cache_ttl: int = 3600,
    ):
        self.primary_provider = primary_provider or settings.ai.provider
        self.fallback_providers = fallback_providers or []
        self.cache = AnalysisCache(ttl_seconds=cache_ttl)
        
        # Initialize providers
        self.providers: Dict[str, AIProviderInterface] = {}
        self._init_providers()
    
    def _init_providers(self):
        """Initialize AI providers."""
        # Primary provider
        self.providers[self.primary_provider] = self._create_provider(self.primary_provider)
        
        # Fallback providers
        for provider in self.fallback_providers:
            if provider not in self.providers:
                self.providers[provider] = self._create_provider(provider)
        
        # Always add rule-based fallback
        self.rule_based_analyzer = RuleBasedAnalyzer()
    
    def _create_provider(self, provider: str) -> Optional[AIProviderInterface]:
        """Create a provider instance."""
        try:
            if provider == "openai":
                return create_provider(
                    "openai",
                    model=settings.ai.model,
                    api_key=settings.ai.openai_api_key.get_secret_value() if settings.ai.openai_api_key else None,
                )
            elif provider == "anthropic":
                return create_provider(
                    "anthropic",
                    model=settings.ai.model,
                    api_key=settings.ai.anthropic_api_key.get_secret_value() if settings.ai.anthropic_api_key else None,
                )
            elif provider == "gemini":
                return create_provider(
                    "gemini",
                    model=settings.ai.model,
                    api_key=settings.ai.gemini_api_key.get_secret_value() if settings.ai.gemini_api_key else None,
                )
            elif provider == "custom":
                return create_provider(
                    "custom",
                    model=settings.ai.model,
                    api_key=settings.ai.custom_api_key.get_secret_value() if settings.ai.custom_api_key else None,
                    base_url=settings.ai.base_url,
                )
        except Exception as e:
            logger.error(f"Failed to initialize {provider} provider: {e}")
        return None
    
    async def analyze_attack(
        self,
        events: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None,
        thought_callback: Optional[callable] = None,
    ) -> AIAnalysisResult:
        """
        Analyze attack events using AI.
        
        Args:
            events: List of attack events
            context: Additional context (honeypot config, history, etc.)
            thought_callback: Optional async callback for streaming thoughts (chunk, full_content)
        
        Returns:
            AIAnalysisResult with structured analysis
        """
        # Prepare attack summary
        summary = self._prepare_attack_summary(events)
        
        # Check cache (skip cache if streaming - we want live thoughts)
        cache_key = self.cache._hash_key(json.dumps(summary, sort_keys=True))
        cached = self.cache.get(cache_key)
        
        if cached and not thought_callback:
            logger.info("Using cached analysis result")
            return AIAnalysisResult(**json.loads(cached.content))
        
        # Try providers in order
        providers_order = [self.primary_provider] + self.fallback_providers
        
        for provider_name in providers_order:
            provider = self.providers.get(provider_name)
            
            if provider and provider.is_available():
                try:
                    response = await self._analyze_with_provider(
                        provider, summary, context, thought_callback
                    )
                    
                    # Parse and validate result
                    result = self._parse_analysis_result(response.content)
                    
                    # Cache successful result
                    self.cache.set(cache_key, response.content, response.tokens_used)
                    
                    logger.info(f"AI analysis completed using {provider_name}")
                    return result
                    
                except Exception as e:
                    logger.warning(f"{provider_name} analysis failed: {e}")
                    continue
        
        # Fall back to rule-based analysis
        logger.warning("All AI providers failed, using rule-based analysis")
        return self.rule_based_analyzer.analyze(events)
    
    async def _analyze_with_provider(
        self,
        provider: AIProviderInterface,
        summary: Dict[str, Any],
        context: Optional[Dict[str, Any]],
        thought_callback: Optional[callable] = None,
    ) -> AIResponse:
        """Perform analysis with a specific provider.
        
        Args:
            provider: AI provider to use
            summary: Attack summary dict
            context: Additional context
            thought_callback: Optional async callback for streaming thoughts
        """
        prompt = ATTACK_ANALYSIS_PROMPT.format(
            attack_summary=json.dumps(summary, indent=2),
            schema=json.dumps(ATTACK_ANALYSIS_SCHEMA, indent=2),
        )
        
        system_prompt = """You are an expert cybersecurity analyst specializing in honeypot defense and attacker behavior analysis.
Provide detailed, actionable analysis that helps optimize honeypot effectiveness.
Always respond with valid JSON matching the requested schema."""
        
        # Use streaming if callback provided and provider supports it
        if thought_callback and hasattr(provider, 'generate_stream'):
            return await self._analyze_with_streaming(
                provider, prompt, system_prompt, thought_callback
            )
        
        return await provider.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=settings.ai.temperature,
            max_tokens=settings.ai.max_tokens,
            json_mode=True,
        )
    
    async def _analyze_with_streaming(
        self,
        provider: AIProviderInterface,
        prompt: str,
        system_prompt: str,
        thought_callback: callable,
    ) -> AIResponse:
        """Perform streaming analysis, calling thought_callback for each chunk."""
        import time
        start = time.time()
        
        full_content = ""
        tokens_used = 0
        
        try:
            async for chunk in provider.generate_stream(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=settings.ai.temperature,
                max_tokens=settings.ai.max_tokens,
            ):
                full_content += chunk
                tokens_used += 1
                
                # Call the thought callback with the accumulated content
                if thought_callback:
                    try:
                        await thought_callback(chunk, full_content)
                    except Exception as e:
                        logger.debug(f"Thought callback error: {e}")
            
            duration_ms = int((time.time() - start) * 1000)
            
            return AIResponse(
                content=full_content,
                provider=provider.__class__.__name__.replace('Provider', '').lower(),
                model=getattr(provider, 'model', 'unknown'),
                tokens_used=tokens_used,
                duration_ms=duration_ms,
            )
        except Exception as e:
            logger.error(f"Streaming analysis failed: {e}")
            raise
    
    def _prepare_attack_summary(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Prepare attack summary for AI analysis."""
        if not events:
            return {"total_events": 0}
        
        # Extract key metrics
        commands = []
        credentials = []
        ips = set()
        attack_types = set()
        severities = {}
        
        for event in events:
            ips.add(event.get("source_ip", "unknown"))
            
            if event.get("commands"):
                commands.extend(event["commands"])
            
            if event.get("username"):
                credentials.append({
                    "username": event.get("username"),
                    "password": event.get("password"),
                })
            
            attack_type = event.get("attack_type")
            if attack_type:
                attack_types.add(attack_type)
            
            severity = event.get("severity", "unknown")
            severities[severity] = severities.get(severity, 0) + 1
        
        # Command frequency
        cmd_freq = {}
        for cmd in commands:
            base_cmd = cmd.split()[0] if cmd else ""
            if base_cmd:
                cmd_freq[base_cmd] = cmd_freq.get(base_cmd, 0) + 1
        
        top_commands = sorted(cmd_freq.items(), key=lambda x: -x[1])[:10]
        
        return {
            "total_events": len(events),
            "unique_ips": len(ips),
            "attack_types": list(attack_types),
            "commands_used": commands[:50],  # Limit for prompt size
            "top_commands": top_commands,
            "credentials_tried": credentials[:20],
            "severity_distribution": severities,
            "time_span": {
                "start": min(e.get("timestamp", "") for e in events),
                "end": max(e.get("timestamp", "") for e in events),
            },
        }
    
    def _parse_analysis_result(self, content: str) -> AIAnalysisResult:
        """Parse AI response into structured result."""
        try:
            # Handle markdown code blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            data = json.loads(content)
            
            return AIAnalysisResult(
                attack_sophistication=data.get("attack_sophistication", "medium"),
                attacker_skill_level=data.get("attacker_skill_level", "intermediate"),
                attack_objectives=data.get("attack_objectives", []),
                threat_level=data.get("threat_level", "medium"),
                recommended_interaction_level=data.get("recommended_interaction_level", "medium"),
                deception_strategies=data.get("deception_strategies", []),
                configuration_changes=data.get("configuration_changes", {}),
                confidence=data.get("confidence", 0.5),
                reasoning=data.get("reasoning", ""),
                mitre_attack_ids=data.get("mitre_attack_ids", []),
            )
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response: {e}")
            logger.debug(f"Raw response content (first 500 chars): {content[:500] if content else 'empty'}")
            # Return default result
            return AIAnalysisResult(
                attack_sophistication="medium",
                attacker_skill_level="intermediate",
                attack_objectives=["unknown"],
                threat_level="medium",
                recommended_interaction_level="medium",
                deception_strategies=["fake_files"],
                configuration_changes={},
                confidence=0.3,
                reasoning="Failed to parse AI response",
            )
    
    async def generate_adaptation(
        self,
        analysis: AIAnalysisResult,
        current_config: Dict[str, Any],
        events: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Generate adaptation configuration based on analysis."""
        # Start with current config
        new_config = current_config.copy()
        
        # Apply analysis recommendations
        if analysis.configuration_changes:
            for key, value in analysis.configuration_changes.items():
                if key in new_config:
                    if isinstance(new_config[key], list) and isinstance(value, list):
                        # Merge lists
                        new_config[key] = list(set(new_config[key] + value))
                    else:
                        new_config[key] = value
        
        # Apply deception strategies
        deception = analysis.deception_strategies
        
        if "fake_users" in deception:
            # Add fake users based on attempted credentials
            attempted_users = {e.get("username") for e in events if e.get("username")}
            existing_users = {u.get("username") for u in new_config.get("fake_users", [])}
            
            for username in attempted_users - existing_users:
                new_config.setdefault("fake_users", []).append({
                    "username": username,
                    "password": "honeypot123",
                })
        
        if "delayed_responses" in deception:
            new_config["response_delay"] = 0.5
        
        if "fake_files" in deception:
            # Add common sensitive file paths
            fake_files = new_config.get("fake_files", [])
            additional_files = [
                "/etc/shadow",
                "/etc/ssh/sshd_config",
                "/var/log/auth.log",
                "/root/.bash_history",
                "/var/www/config.php",
            ]
            new_config["fake_files"] = list(set(fake_files + additional_files))
        
        # Adjust interaction level
        new_config["interaction_level"] = analysis.recommended_interaction_level
        
        # Add command responses for common attacks
        common_cmds = ["ls", "pwd", "whoami", "uname", "cat", "wget", "curl"]
        for cmd in common_cmds:
            if cmd not in new_config.get("custom_responses", {}):
                new_config.setdefault("custom_responses", {})[cmd] = self._generate_fake_response(cmd)
        
        return new_config
    
    def _generate_fake_response(self, command: str) -> str:
        """Generate fake command response."""
        responses = {
            "ls": "total 48\ndrwxr-xr-x 2 root root 4096 Jan 1 12:00 bin\ndrwxr-xr-x 3 root root 4096 Jan 1 12:00 etc\ndrwxr-xr-x 2 root root 4096 Jan 1 12:00 var",
            "pwd": "/home/admin",
            "whoami": "root",
            "uname": "Linux server01 5.4.0-42-generic #46-Ubuntu SMP x86_64 GNU/Linux",
            "cat /etc/passwd": "root:x:0:0:root:/root:/bin/bash\nwww-data:x:33:33:www-data:/var/www:/usr/sbin/nologin\nmysql:x:112:117:MySQL Server:/nonexistent:/bin/false",
            "wget": "Connecting to ... failed: Connection refused.",
            "curl": "curl: (7) Failed to connect to port 80: Connection refused",
        }
        return responses.get(command, f"bash: {command}: command not found")


class RuleBasedAnalyzer:
    """Rule-based fallback analyzer."""
    
    def analyze(self, events: List[Dict[str, Any]]) -> AIAnalysisResult:
        """Analyze attacks using rules."""
        if not events:
            return AIAnalysisResult(
                attack_sophistication="low",
                attacker_skill_level="script_kiddie",
                attack_objectives=["reconnaissance"],
                threat_level="low",
                recommended_interaction_level="low",
                deception_strategies=["fake_files"],
                configuration_changes={},
                confidence=0.5,
                reasoning="No events to analyze",
            )
        
        # Count high severity events
        high_severity = sum(1 for e in events if e.get("severity") in ["high", "critical"])
        
        # Detect attack patterns
        commands = [e.get("commands", []) for e in events]
        commands = [cmd for sublist in commands for cmd in sublist]
        
        has_downloads = any("wget" in c or "curl" in c for c in commands)
        has_recon = any(c in ["ls", "pwd", "whoami", "uname"] for c in commands)
        has_exploit = any("chmod" in c or "bash" in c or "/bin/sh" in c for c in commands)
        
        # Determine sophistication
        if has_exploit or high_severity > 5:
            sophistication = "high"
            skill = "advanced"
            threat = "high"
            interaction = "high"
        elif has_downloads or high_severity > 2:
            sophistication = "medium"
            skill = "intermediate"
            threat = "medium"
            interaction = "medium"
        else:
            sophistication = "low"
            skill = "script_kiddie"
            threat = "low"
            interaction = "low"
        
        # Build objectives
        objectives = []
        if has_recon:
            objectives.append("reconnaissance")
        if has_downloads:
            objectives.append("malware_deployment")
        if has_exploit:
            objectives.append("exploitation")
        if not objectives:
            objectives.append("unknown")
        
        return AIAnalysisResult(
            attack_sophistication=sophistication,
            attacker_skill_level=skill,
            attack_objectives=objectives,
            threat_level=threat,
            recommended_interaction_level=interaction,
            deception_strategies=["fake_files", "delayed_responses"] if sophistication == "high" else ["fake_files"],
            configuration_changes={
                "interaction_level": interaction,
                "allowed_commands": ["ls", "pwd", "whoami", "cat"],
            },
            confidence=0.7,
            reasoning="Rule-based analysis based on attack patterns",
        )


# Global analyzer instance
analyzer: Optional[EnhancedAIAnalyzer] = None


def get_analyzer() -> EnhancedAIAnalyzer:
    """Get or create the global analyzer instance."""
    global analyzer
    if analyzer is None:
        analyzer = EnhancedAIAnalyzer()
    return analyzer