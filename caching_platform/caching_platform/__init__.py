"""
OpenAI-Style Multi-Tenant Caching Infrastructure Platform

Enterprise-grade distributed caching platform with autonomous management,
multi-tenant support, and intelligent scaling capabilities.

Features:
- Autonomous AI agents for scaling, optimization, and healing
- Multi-tenant isolation with resource quotas
- Auto-scaling with ML-based predictions
- High availability Redis clustering
- Enterprise security and audit logging
- Rich CLI interface and monitoring

Author: Nik Jois
Email: nikjois@llamasearch.ai
"""

import time

from .core.orchestrator import CacheOrchestrator
from .core.cache_manager import MultiTenantCacheManager
from .core.auto_scaler import AutoScaler
from .core.health_monitor import HealthMonitor
from .core.load_balancer import LoadBalancer

from .agents import (
    ScalingAgent,
    OptimizationAgent,
    HealingAgent,
    PredictionAgent
)

from .config.settings import get_settings, Settings
from .config.schemas import (
    Tenant,
    CacheMetrics,
    AgentInfo,
    ScalingDecision,
    AlertSeverity
)

from .cli.interface import cli
from .cli.menu_system import MenuSystem

__version__ = "1.0.0"
__author__ = "Nik Jois"
__email__ = "nikjois@llamasearch.ai"

__all__ = [
    # Core components
    "CacheOrchestrator",
    "MultiTenantCacheManager", 
    "AutoScaler",
    "HealthMonitor",
    "LoadBalancer",
    
    # Autonomous agents
    "ScalingAgent",
    "OptimizationAgent",
    "HealingAgent", 
    "PredictionAgent",
    
    # Configuration
    "get_settings",
    "Settings",
    
    # Schemas
    "Tenant",
    "CacheMetrics",
    "AgentInfo",
    "ScalingDecision",
    "AlertSeverity",
    
    # CLI
    "cli",
    "MenuSystem"
]

# OpenAI Agents SDK Integration
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
except ImportError:
    OPENAI_AVAILABLE = False

class OpenAIAgentManager:
    """
    OpenAI Agents SDK integration for managing the caching platform.
    
    This class provides AI-powered management capabilities using OpenAI's
    Agents SDK to control and monitor the caching platform.
    """
    
    def __init__(self, api_key: str = None, orchestrator: CacheOrchestrator = None):
        """Initialize OpenAI Agent Manager."""
        self.orchestrator = orchestrator
        self.client = None
        
        if OPENAI_AVAILABLE and api_key:
            self.client = OpenAI(api_key=api_key)
    
    async def initialize_ai_management(self):
        """Initialize AI-powered management capabilities."""
        if not self.client:
            return False
            
        # Create AI agents for platform management
        self.management_agent = await self._create_management_agent()
        self.monitoring_agent = await self._create_monitoring_agent()
        self.optimization_agent = await self._create_optimization_agent()
        
        return True
    
    async def _create_management_agent(self):
        """Create AI agent for platform management."""
        if not self.client:
            return None
            
        instructions = """
        You are an AI agent responsible for managing an enterprise caching platform.
        
        Your capabilities include:
        - Monitoring system health and performance
        - Making scaling decisions based on load patterns
        - Optimizing cache configurations
        - Detecting and resolving issues
        - Providing recommendations for improvements
        
        Always prioritize system stability and performance.
        """
        
        return {
            "role": "management",
            "instructions": instructions,
            "capabilities": [
                "system_monitoring",
                "scaling_decisions", 
                "issue_resolution",
                "performance_optimization"
            ]
        }
    
    async def _create_monitoring_agent(self):
        """Create AI agent for system monitoring."""
        if not self.client:
            return None
            
        instructions = """
        You are an AI agent responsible for monitoring a caching platform.
        
        Your responsibilities:
        - Monitor system metrics and performance
        - Detect anomalies and potential issues
        - Generate alerts and notifications
        - Provide health status reports
        - Track SLA compliance
        
        Be proactive in identifying potential problems.
        """
        
        return {
            "role": "monitoring",
            "instructions": instructions,
            "capabilities": [
                "metrics_analysis",
                "anomaly_detection",
                "alert_generation",
                "health_reporting"
            ]
        }
    
    async def _create_optimization_agent(self):
        """Create AI agent for system optimization.""" 
        if not self.client:
            return None
            
        instructions = """
        You are an AI agent responsible for optimizing caching platform performance.
        
        Your focus areas:
        - Cache hit ratio optimization
        - Memory usage optimization
        - Response time improvements
        - Resource allocation efficiency
        - Configuration tuning
        
        Always consider the impact on system stability.
        """
        
        return {
            "role": "optimization",
            "instructions": instructions,
            "capabilities": [
                "performance_tuning",
                "resource_optimization",
                "configuration_analysis",
                "efficiency_improvements"
            ]
        }
    
    async def get_ai_recommendations(self, context: dict) -> dict:
        """Get AI-powered recommendations for platform management."""
        if not self.client:
            return {"error": "OpenAI client not available"}
        
        try:
            # Analyze current system state
            system_metrics = await self.orchestrator.get_system_status()
            
            # Generate AI recommendations
            prompt = f"""
            Based on the current caching platform metrics:
            {system_metrics}
            
            Context: {context}
            
            Please provide recommendations for:
            1. Performance optimization
            2. Scaling decisions
            3. Configuration improvements
            4. Issue resolution
            
            Format as JSON with specific actionable recommendations.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            return {
                "success": True,
                "recommendations": response.choices[0].message.content,
                "timestamp": time.time()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

# Global instance for easy access
_ai_manager = None

def get_ai_manager(api_key: str = None, orchestrator: CacheOrchestrator = None) -> OpenAIAgentManager:
    """Get or create the global AI manager instance."""
    global _ai_manager
    
    if _ai_manager is None:
        _ai_manager = OpenAIAgentManager(api_key=api_key, orchestrator=orchestrator)
    
    return _ai_manager 