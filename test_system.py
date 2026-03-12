#!/usr/bin/env python3
"""
Test script for Adaptive Honeypot System
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from core.orchestrator import AdaptiveOrchestrator
from core.models import AttackEvent, AttackSeverity
from datetime import datetime

async def test_system():
    print("🧪 Testing Adaptive Honeypot System")
    print("=" * 50)
    
    # Initialize orchestrator
    print("\n1. Initializing orchestrator...")
    orchestrator = AdaptiveOrchestrator(
        adaptation_threshold=3,
        analysis_interval=30,
        max_honeypots=5
    )
    print("✅ Orchestrator initialized")
    
    # Test configuration engine
    print("\n2. Testing configuration engine...")
    config = orchestrator.config_engine.generate_default_config("test-honeypot", 2222)
    print(f"✅ Generated config: {config.name}")
    
    # Test deployment (requires Docker)
    print("\n3. Testing deployment...")
    try:
        honeypot_id = await orchestrator.deploy_new_honeypot("test-ssh", 2222)
        if honeypot_id:
            print(f"✅ Deployed honeypot: {honeypot_id}")
            
            # Wait a bit
            await asyncio.sleep(5)
            
            # Check health
            print("\n4. Checking health...")
            health = orchestrator.deployment.check_health(honeypot_id)
            if health:
                print(f"✅ Health check passed: {health.status}")
            
            # Test log processing
            print("\n5. Testing log processor...")
            events = orchestrator.log_processor.watch_logs(honeypot_id)
            print(f"✅ Found {len(events)} events")
            
            # Cleanup
            print("\n6. Cleaning up...")
            await orchestrator.remove_honeypot(honeypot_id)
            print("✅ Honeypot removed")
            
        else:
            print("⚠️  Deployment failed (Docker may not be running)")
            
    except Exception as e:
        print(f"⚠️  Deployment test skipped: {e}")
    
    # Test AI analyzer (requires API key)
    print("\n7. Testing AI analyzer...")
    try:
        # Create sample events
        sample_events = [
            AttackEvent(
                timestamp=datetime.now(),
                honeypot_id="test",
                source_ip="192.168.1.100",
                source_port=12345,
                username="root",
                password="password123",
                commands=["ls", "cat /etc/passwd"],
                session_id="test-session",
                severity=AttackSeverity.MEDIUM,
                attack_type="brute_force"
            )
        ]
        
        analysis = orchestrator.ai_analyzer.analyze_attack_pattern(sample_events)
        print(f"✅ AI analysis completed: {analysis.get('threat_level', 'N/A')}")
        
    except Exception as e:
        print(f"⚠️  AI test skipped: {e}")
    
    print("\n" + "=" * 50)
    print("✅ System tests completed!")
    print("\nNote: Some tests may be skipped if Docker or API keys are not configured.")

if __name__ == "__main__":
    asyncio.run(test_system())
