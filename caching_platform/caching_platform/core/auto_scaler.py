"""Auto-scaling module for the caching platform."""

import asyncio
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import structlog

from .cache_manager import MultiTenantCacheManager
from ..config.settings import Settings
from ..config.schemas import ScalingDecision

logger = structlog.get_logger(__name__)


class AutoScaler:
    """Automatic scaling controller for the caching platform."""
    
    def __init__(self, cache_manager: MultiTenantCacheManager, settings: Settings):
        self.cache_manager = cache_manager
        self.settings = settings
        self.scaling_config = settings.scaling
        
        # Scaling state
        self.current_nodes = self.scaling_config.min_nodes
        self.last_scale_up = 0
        self.last_scale_down = 0
        self.scaling_decisions: List[ScalingDecision] = []
        
        # Performance tracking
        self.performance_history: List[Dict[str, Any]] = []
        self.scaling_predictions: Dict[str, Any] = {}
        
        # Scaling thresholds
        self.scale_up_threshold = self.scaling_config.scale_up_threshold
        self.scale_down_threshold = self.scaling_config.scale_down_threshold
        
        # Cooldown periods
        self.scale_up_cooldown = self.scaling_config.scale_up_cooldown
        self.scale_down_cooldown = self.scaling_config.scale_down_cooldown
    
    async def initialize(self) -> bool:
        """Initialize the auto scaler."""
        try:
            logger.info("Initializing auto scaler")
            
            # Set initial node count
            self.current_nodes = self.scaling_config.min_nodes
            
            # Start background monitoring
            asyncio.create_task(self._scaling_monitor())
            
            logger.info("Auto scaler initialized successfully")
            return True
            
        except Exception as e:
            logger.error("Failed to initialize auto scaler", error=str(e))
            return False
    
    async def start(self) -> bool:
        """Start the auto scaler."""
        try:
            logger.info("Starting auto scaler")
            return True
            
        except Exception as e:
            logger.error("Failed to start auto scaler", error=str(e))
            return False
    
    async def stop(self):
        """Stop the auto scaler."""
        logger.info("Stopping auto scaler")
    
    async def evaluate_scaling_needs(self, metrics: Dict[str, Any]) -> Optional[ScalingDecision]:
        """Evaluate if scaling is needed based on current metrics."""
        try:
            current_time = time.time()
            
            # Get current performance metrics
            cpu_usage = metrics.get("cpu_usage_percent", 0.0)
            memory_usage = metrics.get("memory_usage_percent", 0.0)
            request_rate = metrics.get("requests_per_second", 0.0)
            
            # Check if we're in cooldown period
            if current_time - self.last_scale_up < self.scale_up_cooldown:
                return None
            
            if current_time - self.last_scale_down < self.scale_down_cooldown:
                return None
            
            # Evaluate scaling conditions
            scale_up_needed = (
                cpu_usage > self.scale_up_threshold or
                memory_usage > self.scale_up_threshold or
                request_rate > self._get_request_rate_threshold()
            )
            
            scale_down_needed = (
                cpu_usage < self.scale_down_threshold and
                memory_usage < self.scale_down_threshold and
                request_rate < self._get_request_rate_threshold() * 0.5 and
                self.current_nodes > self.scaling_config.min_nodes
            )
            
            # Create scaling decision
            if scale_up_needed and self.current_nodes < self.scaling_config.max_nodes:
                decision = ScalingDecision(
                    id=f"scale_up_{int(current_time)}",
                    agent_id="scaling_agent",
                    decision_type="scale_up",
                    current_nodes=self.current_nodes,
                    target_nodes=min(self.current_nodes + 1, self.scaling_config.max_nodes),
                    reason=f"High resource usage - CPU: {cpu_usage:.1f}%, Memory: {memory_usage:.1f}%",
                    cpu_usage=cpu_usage,
                    memory_usage=memory_usage,
                    request_rate=request_rate,
                    created_at=datetime.utcnow()
                )
                
                logger.info(f"Scaling decision: {decision.decision_type} from {decision.current_nodes} to {decision.target_nodes}")
                return decision
            
            elif scale_down_needed:
                decision = ScalingDecision(
                    id=f"scale_down_{int(current_time)}",
                    agent_id="scaling_agent",
                    decision_type="scale_down",
                    current_nodes=self.current_nodes,
                    target_nodes=max(self.current_nodes - 1, self.scaling_config.min_nodes),
                    reason=f"Low resource usage - CPU: {cpu_usage:.1f}%, Memory: {memory_usage:.1f}%",
                    cpu_usage=cpu_usage,
                    memory_usage=memory_usage,
                    request_rate=request_rate,
                    created_at=datetime.utcnow()
                )
                
                logger.info(f"Scaling decision: {decision.decision_type} from {decision.current_nodes} to {decision.target_nodes}")
                return decision
            
            return None
            
        except Exception as e:
            logger.error("Error evaluating scaling needs", error=str(e))
            return None
    
    async def execute_scaling_decision(self, decision: ScalingDecision) -> bool:
        """Execute a scaling decision."""
        try:
            logger.info(f"Executing scaling decision: {decision.decision_type}")
            
            if decision.decision_type == "scale_up":
                success = await self._scale_up(decision.target_nodes)
            elif decision.decision_type == "scale_down":
                success = await self._scale_down(decision.target_nodes)
            else:
                logger.error(f"Unknown scaling decision type: {decision.decision_type}")
                return False
            
            # Update decision status
            decision.executed = True
            decision.executed_at = datetime.utcnow()
            decision.successful = success
            
            # Store decision
            self.scaling_decisions.append(decision)
            
            # Keep only last 100 decisions
            if len(self.scaling_decisions) > 100:
                self.scaling_decisions.pop(0)
            
            # Update cooldown timestamps
            current_time = time.time()
            if decision.decision_type == "scale_up":
                self.last_scale_up = current_time
            else:
                self.last_scale_down = current_time
            
            # Update current node count
            self.current_nodes = decision.target_nodes
            
            logger.info(f"Scaling decision executed successfully: {success}")
            return success
            
        except Exception as e:
            logger.error("Error executing scaling decision", error=str(e))
            return False
    
    async def _scale_up(self, target_nodes: int) -> bool:
        """Scale up the cluster."""
        try:
            logger.info(f"Scaling up from {self.current_nodes} to {target_nodes} nodes")
            
            # Implement actual scaling logic
            # 1. Provision new Redis nodes
            new_nodes = target_nodes - self.current_nodes
            for i in range(new_nodes):
                node_id = f"redis-node-{self.current_nodes + i + 1}"
                success = await self.cache_manager.add_node(node_id, f"redis-{node_id}", 6379)
                if not success:
                    logger.error(f"Failed to add node {node_id}")
                    return False
            
            # 2. Update cluster configuration
            await self.cache_manager.rebalance_cluster()
            
            # 3. Update load balancer
            await self.cache_manager.update_load_balancer_config()
            
            # 4. Verify cluster health
            health_check = await self.cache_manager.check_cluster_health()
            if not health_check.get("healthy", False):
                logger.error("Cluster health check failed after scaling")
                return False
            
            logger.info(f"Successfully scaled up to {target_nodes} nodes")
            return True
            
        except Exception as e:
            logger.error(f"Failed to scale up: {e}")
            return False
    
    async def _scale_down(self, target_nodes: int) -> bool:
        """Scale down the cluster."""
        try:
            logger.info(f"Scaling down from {self.current_nodes} to {target_nodes} nodes")
            
            # Implement actual scaling logic
            # 1. Identify nodes to remove
            nodes_to_remove = self.current_nodes - target_nodes
            if nodes_to_remove <= 0:
                return True
            
            # 2. Migrate data from nodes to be removed
            for i in range(nodes_to_remove):
                node_id = f"redis-node-{self.current_nodes - i}"
                success = await self.cache_manager.migrate_data_from_node(node_id)
                if not success:
                    logger.error(f"Failed to migrate data from node {node_id}")
                    return False
            
            # 3. Remove nodes from cluster
            for i in range(nodes_to_remove):
                node_id = f"redis-node-{self.current_nodes - i}"
                success = await self.cache_manager.remove_node(node_id)
                if not success:
                    logger.error(f"Failed to remove node {node_id}")
                    return False
            
            # 4. Update load balancer configuration
            await self.cache_manager.update_load_balancer_config()
            
            # 5. Verify cluster health
            health_check = await self.cache_manager.check_cluster_health()
            if not health_check.get("healthy", False):
                logger.error("Cluster health check failed after scaling")
                return False
            
            logger.info(f"Successfully scaled down to {target_nodes} nodes")
            return True
            
        except Exception as e:
            logger.error(f"Failed to scale down: {e}")
            return False
    
    async def _scaling_monitor(self):
        """Background task to monitor scaling performance."""
        while True:
            try:
                # Collect performance metrics
                metrics = await self.cache_manager.get_system_metrics()
                
                # Store performance history
                performance_data = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "nodes": self.current_nodes,
                    "cpu_usage": metrics.get("cpu_usage_percent", 0.0),
                    "memory_usage": metrics.get("memory_usage_percent", 0.0),
                    "request_rate": metrics.get("requests_per_second", 0.0),
                    "response_time": metrics.get("average_response_time_ms", 0.0)
                }
                
                self.performance_history.append(performance_data)
                
                # Keep only last 1000 entries
                if len(self.performance_history) > 1000:
                    self.performance_history.pop(0)
                
                # Update scaling predictions
                await self._update_scaling_predictions()
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error("Scaling monitor error", error=str(e))
                await asyncio.sleep(10)
    
    async def _update_scaling_predictions(self):
        """Update scaling predictions based on historical data."""
        try:
            if len(self.performance_history) < 10:
                return
            
            # Calculate average metrics over last hour
            recent_data = self.performance_history[-120:]  # Last 120 entries (1 hour)
            
            avg_cpu = sum(d["cpu_usage"] for d in recent_data) / len(recent_data)
            avg_memory = sum(d["memory_usage"] for d in recent_data) / len(recent_data)
            avg_request_rate = sum(d["request_rate"] for d in recent_data) / len(recent_data)
            
            # Predict scaling needs
            predicted_scaling = "none"
            confidence = 0.5
            
            if avg_cpu > 80 or avg_memory > 80:
                predicted_scaling = "scale_up"
                confidence = 0.8
            elif avg_cpu < 30 and avg_memory < 30:
                predicted_scaling = "scale_down"
                confidence = 0.7
            
            self.scaling_predictions = {
                "predicted_scaling": predicted_scaling,
                "confidence": confidence,
                "avg_cpu": avg_cpu,
                "avg_memory": avg_memory,
                "avg_request_rate": avg_request_rate,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error("Error updating scaling predictions", error=str(e))
    
    def _get_request_rate_threshold(self) -> float:
        """Get the request rate threshold for scaling."""
        # Base threshold on current node count
        base_threshold = 1000  # requests per second per node
        return base_threshold * self.current_nodes
    
    async def get_scaling_status(self) -> Dict[str, Any]:
        """Get current scaling status."""
        return {
            "current_nodes": self.current_nodes,
            "min_nodes": self.scaling_config.min_nodes,
            "max_nodes": self.scaling_config.max_nodes,
            "scale_up_threshold": self.scale_up_threshold,
            "scale_down_threshold": self.scale_down_threshold,
            "last_scale_up": self.last_scale_up,
            "last_scale_down": self.last_scale_down,
            "scale_up_cooldown": self.scale_up_cooldown,
            "scale_down_cooldown": self.scale_down_cooldown,
            "recent_decisions": [
                decision.dict() for decision in self.scaling_decisions[-10:]
            ],
            "predictions": self.scaling_predictions
        }
    
    async def update_predictions(self, predictions: Dict[str, Any]):
        """Update scaling predictions from external source."""
        try:
            self.scaling_predictions.update(predictions)
            logger.info("Updated scaling predictions")
            
        except Exception as e:
            logger.error("Error updating predictions", error=str(e))
    
    async def set_scaling_config(self, config: Dict[str, Any]) -> bool:
        """Update scaling configuration."""
        try:
            # Update configuration
            if "min_nodes" in config:
                self.scaling_config.min_nodes = config["min_nodes"]
            
            if "max_nodes" in config:
                self.scaling_config.max_nodes = config["max_nodes"]
            
            if "scale_up_threshold" in config:
                self.scale_up_threshold = config["scale_up_threshold"]
            
            if "scale_down_threshold" in config:
                self.scale_down_threshold = config["scale_down_threshold"]
            
            if "scale_up_cooldown" in config:
                self.scale_up_cooldown = config["scale_up_cooldown"]
            
            if "scale_down_cooldown" in config:
                self.scale_down_cooldown = config["scale_down_cooldown"]
            
            logger.info("Updated scaling configuration")
            return True
            
        except Exception as e:
            logger.error("Error updating scaling configuration", error=str(e))
            return False
    
    async def get_performance_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get performance history for the specified number of hours."""
        try:
            # Calculate cutoff time
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            # Filter history
            filtered_history = []
            for entry in self.performance_history:
                entry_time = datetime.fromisoformat(entry["timestamp"])
                if entry_time >= cutoff_time:
                    filtered_history.append(entry)
            
            return filtered_history
            
        except Exception as e:
            logger.error("Error getting performance history", error=str(e))
            return []
    
    async def force_scale(self, target_nodes: int) -> bool:
        """Force scaling to a specific number of nodes."""
        try:
            if target_nodes < self.scaling_config.min_nodes or target_nodes > self.scaling_config.max_nodes:
                logger.error(f"Target nodes {target_nodes} outside allowed range")
                return False
            
            current_time = time.time()
            
            if target_nodes > self.current_nodes:
                decision = ScalingDecision(
                    id=f"force_scale_up_{int(current_time)}",
                    agent_id="manual",
                    decision_type="scale_up",
                    current_nodes=self.current_nodes,
                    target_nodes=target_nodes,
                    reason="Manual force scale",
                    cpu_usage=0.0,
                    memory_usage=0.0,
                    request_rate=0.0,
                    created_at=datetime.utcnow()
                )
            else:
                decision = ScalingDecision(
                    id=f"force_scale_down_{int(current_time)}",
                    agent_id="manual",
                    decision_type="scale_down",
                    current_nodes=self.current_nodes,
                    target_nodes=target_nodes,
                    reason="Manual force scale",
                    cpu_usage=0.0,
                    memory_usage=0.0,
                    request_rate=0.0,
                    created_at=datetime.utcnow()
                )
            
            success = await self.execute_scaling_decision(decision)
            
            if success:
                logger.info(f"Force scaled to {target_nodes} nodes")
            else:
                logger.error(f"Failed to force scale to {target_nodes} nodes")
            
            return success
            
        except Exception as e:
            logger.error("Error during force scale", error=str(e))
            return False 