import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging
import os
from core.deployment import DeploymentManager
from core.config_engine import ConfigEngine
from core.models import HoneypotConfig, AdaptationDecision, AttackEvent
from monitoring.log_processor import LogProcessor
from ai.analyzer import AIAnalyzer
from monitoring.resource_monitor import ResourceMonitor

logger = logging.getLogger(__name__)

class AdaptiveOrchestrator:
    def __init__(
        self,
        adaptation_threshold: int = 5,
        analysis_interval: int = 60,
        max_honeypots: int = 10
    ):
        self.deployment = DeploymentManager()
        self.config_engine = ConfigEngine()
        self.log_processor = LogProcessor()
        
        # Initialize AI analyzer with provider from environment
        ai_provider = os.getenv('AI_PROVIDER', 'openai')
        ai_model = os.getenv('AI_MODEL', 'gpt-4')
        self.ai_analyzer = AIAnalyzer(provider=ai_provider, model=ai_model)
        
        self.resource_monitor = ResourceMonitor()
        
        self.adaptation_threshold = adaptation_threshold
        self.analysis_interval = analysis_interval
        self.max_honeypots = max_honeypots
        
        self.active_honeypots: Dict[str, HoneypotConfig] = {}
        self.adaptation_history: List[AdaptationDecision] = []
        self.running = False
    
    async def start(self):
        """Start the orchestrator"""
        self.running = True
        logger.info("Adaptive Orchestrator started")
        
        # Start monitoring tasks
        tasks = [
            self.monitor_loop(),
            self.health_check_loop(),
            self.adaptation_loop()
        ]
        
        await asyncio.gather(*tasks)
    
    async def stop(self):
        """Stop the orchestrator"""
        self.running = False
        logger.info("Adaptive Orchestrator stopped")
    
    async def deploy_new_honeypot(self, name: str, port: int = 2222) -> Optional[str]:
        """Deploy a new honeypot"""
        if len(self.active_honeypots) >= self.max_honeypots:
            logger.warning("Max honeypots reached")
            return None
        
        honeypot_id = f"{name}_{int(datetime.now().timestamp())}"
        config = self.config_engine.generate_default_config(name, port)
        
        # Save configuration
        self.config_engine.save_config(config, honeypot_id)
        
        # Deploy container
        container_id = self.deployment.deploy_honeypot(config, honeypot_id)
        
        if container_id:
            self.active_honeypots[honeypot_id] = config
            logger.info(f"Deployed honeypot: {honeypot_id}")
            return honeypot_id
        
        return None
    
    async def remove_honeypot(self, honeypot_id: str) -> bool:
        """Remove a honeypot"""
        success = self.deployment.stop_honeypot(honeypot_id)
        if success:
            if honeypot_id in self.active_honeypots:
                del self.active_honeypots[honeypot_id]
            logger.info(f"Removed honeypot: {honeypot_id}")
        
        return success
    
    async def monitor_loop(self):
        """Monitor honeypot logs continuously"""
        while self.running:
            try:
                for honeypot_id in list(self.active_honeypots.keys()):
                    events = self.log_processor.watch_logs(honeypot_id)
                    
                    if len(events) >= self.adaptation_threshold:
                        await self.trigger_adaptation(honeypot_id, events)
                
                await asyncio.sleep(10)
                
            except Exception as e:
                logger.error(f"Monitor loop error: {e}")
                await asyncio.sleep(10)
    
    async def health_check_loop(self):
        """Check health of all honeypots"""
        while self.running:
            try:
                for honeypot_id in list(self.active_honeypots.keys()):
                    health = self.deployment.check_health(honeypot_id)
                    
                    if not health or health.status != "running":
                        logger.warning(f"Honeypot {honeypot_id} unhealthy, restarting")
                        self.deployment.restart_honeypot(honeypot_id)
                    
                    # Check resource usage
                    if health and health.cpu_percent > 80:
                        logger.warning(f"High CPU usage on {honeypot_id}")
                
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"Health check error: {e}")
                await asyncio.sleep(30)
    
    async def adaptation_loop(self):
        """Periodic adaptation analysis"""
        while self.running:
            try:
                await asyncio.sleep(self.analysis_interval)
                
                for honeypot_id in list(self.active_honeypots.keys()):
                    events = self.log_processor.watch_logs(honeypot_id)
                    
                    if events:
                        await self.analyze_and_adapt(honeypot_id, events)
                
            except Exception as e:
                logger.error(f"Adaptation loop error: {e}")
    
    async def trigger_adaptation(self, honeypot_id: str, events: List[AttackEvent]):
        """Trigger immediate adaptation based on events"""
        logger.info(f"Triggering adaptation for {honeypot_id}")
        
        current_config = self.active_honeypots[honeypot_id]
        
        # AI analysis
        analysis = self.ai_analyzer.analyze_attack_pattern(events)
        
        # Generate new configuration
        new_config = self.ai_analyzer.generate_adaptive_config(
            current_config, analysis, events
        )
        
        # Create adaptation decision
        decision = AdaptationDecision(
            honeypot_id=honeypot_id,
            reason=f"Threshold reached: {len(events)} events",
            old_config=current_config.model_dump(),
            new_config=new_config.model_dump(),
            timestamp=datetime.now(),
            applied=False
        )
        
        # Apply adaptation
        success = await self.apply_adaptation(honeypot_id, new_config)
        decision.applied = success
        
        self.adaptation_history.append(decision)
        logger.info(f"Adaptation {'applied' if success else 'failed'} for {honeypot_id}")
    
    async def analyze_and_adapt(self, honeypot_id: str, events: List[AttackEvent]):
        """Analyze and adapt honeypot configuration"""
        if not events:
            return
        
        current_config = self.active_honeypots[honeypot_id]
        
        # AI analysis
        analysis = self.ai_analyzer.analyze_attack_pattern(events)
        
        # Check if adaptation is needed
        if analysis.get('threat_level') in ['high', 'critical']:
            new_config = self.ai_analyzer.generate_adaptive_config(
                current_config, analysis, events
            )
            
            await self.apply_adaptation(honeypot_id, new_config)
    
    async def apply_adaptation(self, honeypot_id: str, new_config: HoneypotConfig) -> bool:
        """Apply new configuration to honeypot"""
        try:
            # Save new configuration
            self.config_engine.save_config(new_config, honeypot_id)
            
            # Restart honeypot with new config
            self.deployment.stop_honeypot(honeypot_id)
            await asyncio.sleep(2)
            
            container_id = self.deployment.deploy_honeypot(new_config, honeypot_id)
            
            if container_id:
                self.active_honeypots[honeypot_id] = new_config
                logger.info(f"Applied new config to {honeypot_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to apply adaptation: {e}")
            return False
    
    def get_status(self) -> Dict:
        """Get orchestrator status"""
        return {
            'running': self.running,
            'active_honeypots': len(self.active_honeypots),
            'total_adaptations': len(self.adaptation_history),
            'honeypots': [
                {
                    'id': hid,
                    'config': config.model_dump()
                }
                for hid, config in self.active_honeypots.items()
            ]
        }
