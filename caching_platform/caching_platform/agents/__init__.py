"""
OpenAI-Style Caching Platform - Autonomous Agents

This package contains autonomous agents that manage and optimize the caching platform:

- ScalingAgent: Handles automatic scaling decisions based on load patterns
- OptimizationAgent: Optimizes cache performance and configurations  
- HealingAgent: Detects and resolves system issues automatically
- PredictionAgent: Provides usage forecasting and anomaly detection

Author: Nik Jois
Email: nikjois@llamasearch.ai
"""

from .scaling_agent import ScalingAgent
from .optimization_agent import OptimizationAgent
from .healing_agent import HealingAgent
from .prediction_agent import PredictionAgent

__all__ = [
    "ScalingAgent",
    "OptimizationAgent", 
    "HealingAgent",
    "PredictionAgent"
]

__version__ = "1.0.0"
__author__ = "Nik Jois"
__email__ = "nikjois@llamasearch.ai" 