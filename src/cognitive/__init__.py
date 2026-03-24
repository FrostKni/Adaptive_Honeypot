"""
Cognitive-Behavioral Deception Framework (CBDF)

A novel approach to honeypot deception that exploits human cognitive biases.

This is the FIRST implementation of psychology-based deception in honeypot systems.

Key Components:
- CognitiveProfiler: Build psychological profiles of attackers
- BiasDetector: Detect cognitive biases from behavioral signals  
- DeceptionEngine: Orchestrate bias-exploiting responses
- ResponseGenerator: Generate deception that exploits specific biases

Supported Cognitive Biases:
- Confirmation Bias: Show expected findings
- Anchoring: Control first impressions
- Sunk Cost Fallacy: Reward persistence
- Dunning-Kruger Effect: Maintain overconfidence
- Curiosity Gap: Hint at hidden value
- Loss Aversion: Create FOMO
- Availability Heuristic: Highlight easy paths
- Authority Bias: Fake authority traces
"""

from src.cognitive.profiler import (
    CognitiveProfiler,
    CognitiveProfile,
    CognitiveBiasType,
    DetectedBias,
    MentalModel,
    BiasDetector,
)

from src.cognitive.engine import (
    CognitiveDeceptionEngine,
    DeceptionStrategy,
    DeceptionStrategyLibrary,
    DeceptionResponse,
    ResponseGenerator,
)

__all__ = [
    # Profiler
    "CognitiveProfiler",
    "CognitiveProfile",
    "CognitiveBiasType",
    "DetectedBias",
    "MentalModel",
    "BiasDetector",
    
    # Engine
    "CognitiveDeceptionEngine",
    "DeceptionStrategy",
    "DeceptionStrategyLibrary",
    "DeceptionResponse",
    "ResponseGenerator",
]