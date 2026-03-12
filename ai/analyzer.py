import os
from typing import List, Dict, Optional
from openai import OpenAI
from anthropic import Anthropic
import google.generativeai as genai
from core.models import AttackEvent, HoneypotConfig, AdaptationDecision
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)

class AIAnalyzer:
    def __init__(self, provider: str = "openai", model: str = "gpt-4"):
        self.provider = provider.lower()
        self.model = model
        self.client = None
        
        try:
            if self.provider == "openai":
                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    logger.warning("OpenAI API key not found, AI analysis will use fallback")
                else:
                    self.client = OpenAI(api_key=api_key)
                    
            elif self.provider == "anthropic":
                api_key = os.getenv("ANTHROPIC_API_KEY")
                if not api_key:
                    logger.warning("Anthropic API key not found, AI analysis will use fallback")
                else:
                    self.client = Anthropic(api_key=api_key)
                    
            elif self.provider == "gemini":
                api_key = os.getenv("GEMINI_API_KEY")
                if not api_key:
                    logger.warning("Gemini API key not found, AI analysis will use fallback")
                else:
                    genai.configure(api_key=api_key)
                    self.client = genai.GenerativeModel(model)
            else:
                logger.warning(f"Unknown AI provider: {provider}, using fallback analysis")
                
        except Exception as e:
            logger.error(f"Failed to initialize AI client: {e}")
            self.client = None
    
    def analyze_attack_pattern(self, events: List[AttackEvent]) -> Dict:
        """Analyze attack patterns using AI"""
        
        # If no AI client available, use fallback immediately
        if not self.client:
            logger.info("No AI client available, using fallback analysis")
            return self._fallback_analysis(events)
        
        # Prepare attack summary
        summary = self._prepare_attack_summary(events)
        
        prompt = f"""Analyze the following honeypot attack data and provide insights:

Attack Summary:
{json.dumps(summary, indent=2)}

Provide analysis in JSON format with:
1. attack_sophistication: (low/medium/high)
2. attacker_skill_level: (script_kiddie/intermediate/advanced/expert)
3. attack_objectives: list of likely objectives
4. threat_level: (low/medium/high/critical)
5. recommended_interaction_level: (low/medium/high)
6. deception_strategies: list of recommended deception tactics
7. configuration_changes: specific honeypot config modifications

Return only valid JSON."""

        try:
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a cybersecurity expert analyzing honeypot data."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3
                )
                analysis = json.loads(response.choices[0].message.content)
            
            elif self.provider == "anthropic":
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=2000,
                    messages=[{"role": "user", "content": prompt}]
                )
                analysis = json.loads(response.content[0].text)
            
            elif self.provider == "gemini":
                # Gemini API call
                full_prompt = f"""You are a cybersecurity expert analyzing honeypot data.

{prompt}"""
                response = self.client.generate_content(
                    full_prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.3,
                        max_output_tokens=2000,
                    )
                )
                # Extract JSON from response
                response_text = response.text
                # Try to extract JSON if wrapped in markdown code blocks
                if "```json" in response_text:
                    response_text = response_text.split("```json")[1].split("```")[0].strip()
                elif "```" in response_text:
                    response_text = response_text.split("```")[1].split("```")[0].strip()
                analysis = json.loads(response_text)
            
            logger.info("AI analysis completed")
            return analysis
            
        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            return self._fallback_analysis(events)
    
    def generate_adaptive_config(
        self, 
        current_config: HoneypotConfig, 
        analysis: Dict,
        events: List[AttackEvent]
    ) -> HoneypotConfig:
        """Generate adaptive configuration based on analysis"""
        
        config_dict = current_config.model_dump()
        
        # Apply AI recommendations
        if 'configuration_changes' in analysis:
            changes = analysis['configuration_changes']
            
            # Update interaction level
            if 'interaction_level' in changes:
                config_dict['interaction_level'] = changes['interaction_level']
            
            # Add fake users based on attempted credentials
            attempted_users = set()
            for event in events:
                if event.username:
                    attempted_users.add(event.username)
            
            for username in attempted_users:
                if not any(u['username'] == username for u in config_dict['fake_users']):
                    config_dict['fake_users'].append({
                        'username': username,
                        'password': 'honeypot123'
                    })
            
            # Add response delay for sophisticated attacks
            if analysis.get('attack_sophistication') == 'high':
                config_dict['response_delay'] = 0.5
            
            # Expand allowed commands
            if 'allowed_commands' in changes:
                config_dict['allowed_commands'].extend(changes['allowed_commands'])
                config_dict['allowed_commands'] = list(set(config_dict['allowed_commands']))
            
            # Add custom responses for common commands
            common_commands = self._extract_common_commands(events)
            for cmd in common_commands[:5]:
                if cmd not in config_dict['custom_responses']:
                    config_dict['custom_responses'][cmd] = self._generate_fake_response(cmd)
        
        return HoneypotConfig(**config_dict)
    
    def _prepare_attack_summary(self, events: List[AttackEvent]) -> Dict:
        return {
            'total_events': len(events),
            'unique_ips': len(set(e.source_ip for e in events)),
            'attack_types': list(set(e.attack_type for e in events if e.attack_type)),
            'commands_used': [cmd for e in events for cmd in e.commands],
            'credentials_tried': [
                {'user': e.username, 'pass': e.password} 
                for e in events if e.username
            ][:20],
            'severity_counts': {
                'low': sum(1 for e in events if e.severity == 'low'),
                'medium': sum(1 for e in events if e.severity == 'medium'),
                'high': sum(1 for e in events if e.severity == 'high'),
            }
        }
    
    def _fallback_analysis(self, events: List[AttackEvent]) -> Dict:
        """Rule-based fallback when AI is unavailable"""
        high_severity_count = sum(1 for e in events if e.severity in ['high', 'critical'])
        
        if high_severity_count > 10:
            threat_level = 'high'
            interaction_level = 'high'
        elif high_severity_count > 5:
            threat_level = 'medium'
            interaction_level = 'medium'
        else:
            threat_level = 'low'
            interaction_level = 'low'
        
        return {
            'attack_sophistication': 'medium',
            'attacker_skill_level': 'intermediate',
            'attack_objectives': ['reconnaissance', 'exploitation'],
            'threat_level': threat_level,
            'recommended_interaction_level': interaction_level,
            'deception_strategies': ['fake_files', 'delayed_responses'],
            'configuration_changes': {
                'interaction_level': interaction_level,
                'allowed_commands': ['ls', 'cat', 'wget', 'curl']
            }
        }
    
    def _extract_common_commands(self, events: List[AttackEvent]) -> List[str]:
        cmd_count = {}
        for event in events:
            for cmd in event.commands:
                cmd_count[cmd] = cmd_count.get(cmd, 0) + 1
        
        return sorted(cmd_count.keys(), key=lambda x: cmd_count[x], reverse=True)
    
    def _generate_fake_response(self, command: str) -> str:
        responses = {
            'ls': 'total 48\ndrwxr-xr-x 2 root root 4096 Jan 1 12:00 bin\ndrwxr-xr-x 3 root root 4096 Jan 1 12:00 etc',
            'pwd': '/home/user',
            'whoami': 'user',
            'uname': 'Linux ubuntu 5.4.0-42-generic x86_64',
            'cat /etc/passwd': 'root:x:0:0:root:/root:/bin/bash\nuser:x:1000:1000::/home/user:/bin/bash'
        }
        return responses.get(command, f'Command output for: {command}')
