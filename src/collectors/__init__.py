"""
Collectors package for honeypot log ingestion.

Includes:
- Cowrie collector for SSH honeypot logs
- Cognitive bridge for integrating with deception engine
"""
# Import cognitive bridge first (no external dependencies)
from src.collectors.cognitive_bridge import (
    CognitiveIntegrationBridge,
    CognitiveAnalysisResult,
    get_cognitive_bridge,
    process_command_cognitively,
)

# Cowrie collector requires docker - import conditionally
try:
    from src.collectors.cowrie_collector import (
        CowrieLogCollector,
        get_collector,
        run_collector,
    )
except ImportError:
    # Docker not installed
    CowrieLogCollector = None
    get_collector = None
    run_collector = None

__all__ = [
    "CowrieLogCollector",
    "get_collector",
    "run_collector",
    "CognitiveIntegrationBridge",
    "CognitiveAnalysisResult",
    "get_cognitive_bridge",
    "process_command_cognitively",
]