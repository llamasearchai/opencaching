"""Load balancer for the caching platform."""

import asyncio
import time
import hashlib
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import structlog

from .cache_manager import MultiTenantCacheManager
from ..config.settings import Settings

logger = structlog.get_logger(__name__)


class LoadBalancer:
    """Load balancer for distributing requests across cache nodes."""
    
    def __init__(self, cache_manager: MultiTenantCacheManager, settings: Settings):
        self.cache_manager = cache_manager
        self.settings = settings
        
        # Load balancing configuration
        self.algorithm = "consistent_hash"  # Options: round_robin, least_connections, consistent_hash
        self.health_check_interval = 30
        self.connection_timeout = 5.0
        
        # Node management
        self.nodes: Dict[str, Dict[str, Any]] = {}
        self.node_weights: Dict[str, float] = {}
        self.node_health: Dict[str, bool] = {}
        
        # Connection pooling
        self.connection_pools: Dict[str, List[Any]] = {}
        self.max_connections_per_node = 100
        self.min_connections_per_node = 10
        
        # Request tracking
        self.request_counters: Dict[str, int] = {}
        self.response_times: Dict[str, List[float]] = {}
        
        # Load balancing state
        self.current_node_index = 0
        self.virtual_nodes = 150  # For consistent hashing
        
    async def initialize(self) -> bool:
        """Initialize the load balancer."""
        try:
            logger.info("Initializing load balancer")
            
            # Initialize default nodes
            await self._initialize_nodes()
            
            # Start health monitoring
            asyncio.create_task(self._health_monitor())
            
            # Start connection pool management
            asyncio.create_task(self._connection_pool_manager())
            
            logger.info("Load balancer initialized successfully")
            return True
            
        except Exception as e:
            logger.error("Failed to initialize load balancer", error=str(e))
            return False
    
    async def start(self) -> bool:
        """Start the load balancer."""
        try:
            logger.info("Starting load balancer")
            return True
            
        except Exception as e:
            logger.error("Failed to start load balancer", error=str(e))
            return False
    
    async def stop(self):
        """Stop the load balancer."""
        logger.info("Stopping load balancer")
    
    async def _initialize_nodes(self):
        """Initialize default nodes."""
        try:
            # Add default Redis node
            default_node = {
                "id": "redis-1",
                "host": self.settings.redis.host,
                "port": self.settings.redis.port,
                "weight": 1.0,
                "max_connections": self.max_connections_per_node,
                "current_connections": 0,
                "status": "online"
            }
            
            self.nodes["redis-1"] = default_node
            self.node_weights["redis-1"] = 1.0
            self.node_health["redis-1"] = True
            self.request_counters["redis-1"] = 0
            
            logger.info("Initialized default Redis node")
            
        except Exception as e:
            logger.error("Failed to initialize nodes", error=str(e))
    
    async def add_node(self, node_id: str, host: str, port: int, weight: float = 1.0) -> bool:
        """Add a new node to the load balancer."""
        try:
            if node_id in self.nodes:
                logger.warning(f"Node {node_id} already exists")
                return False
            
            node = {
                "id": node_id,
                "host": host,
                "port": port,
                "weight": weight,
                "max_connections": self.max_connections_per_node,
                "current_connections": 0,
                "status": "online"
            }
            
            self.nodes[node_id] = node
            self.node_weights[node_id] = weight
            self.node_health[node_id] = True
            self.request_counters[node_id] = 0
            self.response_times[node_id] = []
            
            logger.info(f"Added node {node_id} ({host}:{port})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add node {node_id}", error=str(e))
            return False
    
    async def remove_node(self, node_id: str) -> bool:
        """Remove a node from the load balancer."""
        try:
            if node_id not in self.nodes:
                logger.warning(f"Node {node_id} does not exist")
                return False
            
            # Drain connections
            await self._drain_node_connections(node_id)
            
            # Remove node
            del self.nodes[node_id]
            del self.node_weights[node_id]
            del self.node_health[node_id]
            del self.request_counters[node_id]
            del self.response_times[node_id]
            
            logger.info(f"Removed node {node_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove node {node_id}", error=str(e))
            return False
    
    async def _drain_node_connections(self, node_id: str):
        """Drain connections from a node before removal."""
        try:
            # Wait for existing connections to complete
            max_wait_time = 30  # seconds
            start_time = time.time()
            
            while self.nodes[node_id]["current_connections"] > 0 and time.time() - start_time < max_wait_time:
                await asyncio.sleep(1)
            
            logger.info(f"Drained connections from node {node_id}")
            
        except Exception as e:
            logger.error(f"Error draining connections from node {node_id}", error=str(e))
    
    async def get_node(self, tenant_id: str, key: str = None) -> Optional[str]:
        """Get the appropriate node for a request."""
        try:
            available_nodes = [node_id for node_id, healthy in self.node_health.items() if healthy]
            
            if not available_nodes:
                logger.error("No healthy nodes available")
                return None
            
            if self.algorithm == "round_robin":
                return await self._round_robin_select(available_nodes)
            elif self.algorithm == "least_connections":
                return await self._least_connections_select(available_nodes)
            elif self.algorithm == "consistent_hash":
                return await self._consistent_hash_select(available_nodes, tenant_id, key)
            else:
                logger.warning(f"Unknown load balancing algorithm: {self.algorithm}")
                return available_nodes[0]
                
        except Exception as e:
            logger.error("Error selecting node", error=str(e))
            return None
    
    async def _round_robin_select(self, available_nodes: List[str]) -> str:
        """Round-robin node selection."""
        if not available_nodes:
            return None
        
        node = available_nodes[self.current_node_index % len(available_nodes)]
        self.current_node_index = (self.current_node_index + 1) % len(available_nodes)
        return node
    
    async def _least_connections_select(self, available_nodes: List[str]) -> str:
        """Least connections node selection."""
        if not available_nodes:
            return None
        
        min_connections = float('inf')
        selected_node = None
        
        for node_id in available_nodes:
            connections = self.nodes[node_id]["current_connections"]
            if connections < min_connections:
                min_connections = connections
                selected_node = node_id
        
        return selected_node
    
    async def _consistent_hash_select(self, available_nodes: List[str], tenant_id: str, key: str = None) -> str:
        """Consistent hash node selection."""
        if not available_nodes:
            return None
        
        # Create hash key from tenant and key
        hash_key = f"{tenant_id}:{key}" if key else tenant_id
        hash_value = int(hashlib.md5(hash_key.encode()).hexdigest(), 16)
        
        # Simple consistent hashing
        node_index = hash_value % len(available_nodes)
        return available_nodes[node_index]
    
    async def record_request(self, node_id: str, response_time: float, success: bool):
        """Record request metrics for a node."""
        try:
            if node_id not in self.nodes:
                return
            
            # Update request counter
            self.request_counters[node_id] += 1
            
            # Update response times
            if node_id not in self.response_times:
                self.response_times[node_id] = []
            
            self.response_times[node_id].append(response_time)
            
            # Keep only last 1000 response times
            if len(self.response_times[node_id]) > 1000:
                self.response_times[node_id] = self.response_times[node_id][-1000:]
            
            # Update connection count
            if success:
                self.nodes[node_id]["current_connections"] = max(0, self.nodes[node_id]["current_connections"] - 1)
            
        except Exception as e:
            logger.error(f"Error recording request for node {node_id}", error=str(e))
    
    async def acquire_connection(self, node_id: str) -> bool:
        """Acquire a connection to a node."""
        try:
            if node_id not in self.nodes:
                return False
            
            node = self.nodes[node_id]
            
            if node["current_connections"] >= node["max_connections"]:
                logger.warning(f"Node {node_id} at maximum connections")
                return False
            
            node["current_connections"] += 1
            return True
            
        except Exception as e:
            logger.error(f"Error acquiring connection for node {node_id}", error=str(e))
            return False
    
    async def release_connection(self, node_id: str):
        """Release a connection to a node."""
        try:
            if node_id not in self.nodes:
                return
            
            self.nodes[node_id]["current_connections"] = max(0, self.nodes[node_id]["current_connections"] - 1)
            
        except Exception as e:
            logger.error(f"Error releasing connection for node {node_id}", error=str(e))
    
    async def _health_monitor(self):
        """Background task to monitor node health."""
        while True:
            try:
                for node_id in list(self.nodes.keys()):
                    is_healthy = await self._check_node_health(node_id)
                    self.node_health[node_id] = is_healthy
                    
                    if not is_healthy:
                        logger.warning(f"Node {node_id} is unhealthy")
                    else:
                        logger.debug(f"Node {node_id} is healthy")
                
                await asyncio.sleep(self.health_check_interval)
                
            except Exception as e:
                logger.error("Health monitor error", error=str(e))
                await asyncio.sleep(10)
    
    async def _check_node_health(self, node_id: str) -> bool:
        """Check if a node is healthy."""
        try:
            node = self.nodes[node_id]
            
            # Simple health check - try to connect to Redis
            # In a real implementation, this would be more sophisticated
            start_time = time.time()
            
            # Simulate health check
            await asyncio.sleep(0.1)
            
            response_time = (time.time() - start_time) * 1000
            
            # Consider node healthy if response time is reasonable
            is_healthy = response_time < 1000  # 1 second threshold
            
            # Update node status
            node["status"] = "online" if is_healthy else "offline"
            
            return is_healthy
            
        except Exception as e:
            logger.error(f"Health check failed for node {node_id}", error=str(e))
            self.nodes[node_id]["status"] = "offline"
            return False
    
    async def _connection_pool_manager(self):
        """Background task to manage connection pools."""
        while True:
            try:
                for node_id in self.nodes:
                    await self._manage_node_connections(node_id)
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error("Connection pool manager error", error=str(e))
                await asyncio.sleep(10)
    
    async def _manage_node_connections(self, node_id: str):
        """Manage connections for a specific node."""
        try:
            node = self.nodes[node_id]
            current_connections = node["current_connections"]
            
            # Adjust max connections based on load
            if current_connections > self.max_connections_per_node * 0.8:
                # High load - increase max connections
                node["max_connections"] = min(
                    self.max_connections_per_node * 2,
                    node["max_connections"] + 10
                )
            elif current_connections < self.min_connections_per_node:
                # Low load - decrease max connections
                node["max_connections"] = max(
                    self.min_connections_per_node,
                    node["max_connections"] - 5
                )
            
        except Exception as e:
            logger.error(f"Error managing connections for node {node_id}", error=str(e))
    
    async def get_load_balancer_status(self) -> Dict[str, Any]:
        """Get load balancer status."""
        try:
            node_status = {}
            for node_id, node in self.nodes.items():
                avg_response_time = 0.0
                if self.response_times.get(node_id):
                    avg_response_time = sum(self.response_times[node_id]) / len(self.response_times[node_id])
                
                node_status[node_id] = {
                    "host": node["host"],
                    "port": node["port"],
                    "status": node["status"],
                    "health": self.node_health.get(node_id, False),
                    "weight": self.node_weights.get(node_id, 1.0),
                    "current_connections": node["current_connections"],
                    "max_connections": node["max_connections"],
                    "total_requests": self.request_counters.get(node_id, 0),
                    "avg_response_time_ms": avg_response_time
                }
            
            return {
                "algorithm": self.algorithm,
                "total_nodes": len(self.nodes),
                "healthy_nodes": sum(1 for healthy in self.node_health.values() if healthy),
                "nodes": node_status,
                "total_requests": sum(self.request_counters.values()),
                "total_connections": sum(node["current_connections"] for node in self.nodes.values())
            }
            
        except Exception as e:
            logger.error("Error getting load balancer status", error=str(e))
            return {}
    
    async def set_algorithm(self, algorithm: str) -> bool:
        """Set the load balancing algorithm."""
        try:
            valid_algorithms = ["round_robin", "least_connections", "consistent_hash"]
            
            if algorithm not in valid_algorithms:
                logger.error(f"Invalid algorithm: {algorithm}")
                return False
            
            self.algorithm = algorithm
            logger.info(f"Set load balancing algorithm to: {algorithm}")
            return True
            
        except Exception as e:
            logger.error("Error setting algorithm", error=str(e))
            return False
    
    async def set_node_weight(self, node_id: str, weight: float) -> bool:
        """Set the weight for a node."""
        try:
            if node_id not in self.nodes:
                logger.error(f"Node {node_id} does not exist")
                return False
            
            if weight <= 0:
                logger.error("Weight must be positive")
                return False
            
            self.node_weights[node_id] = weight
            self.nodes[node_id]["weight"] = weight
            
            logger.info(f"Set weight for node {node_id} to {weight}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting weight for node {node_id}", error=str(e))
            return False
    
    async def get_node_metrics(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed metrics for a specific node."""
        try:
            if node_id not in self.nodes:
                return None
            
            node = self.nodes[node_id]
            response_times = self.response_times.get(node_id, [])
            
            metrics = {
                "node_id": node_id,
                "host": node["host"],
                "port": node["port"],
                "status": node["status"],
                "health": self.node_health.get(node_id, False),
                "weight": self.node_weights.get(node_id, 1.0),
                "current_connections": node["current_connections"],
                "max_connections": node["max_connections"],
                "total_requests": self.request_counters.get(node_id, 0),
                "avg_response_time_ms": sum(response_times) / len(response_times) if response_times else 0.0,
                "min_response_time_ms": min(response_times) if response_times else 0.0,
                "max_response_time_ms": max(response_times) if response_times else 0.0,
                "response_time_samples": len(response_times)
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting metrics for node {node_id}", error=str(e))
            return None
    
    async def rebalance_connections(self) -> bool:
        """Rebalance connections across nodes."""
        try:
            logger.info("Rebalancing connections")
            
            # Get current connection distribution
            total_connections = sum(node["current_connections"] for node in self.nodes.values())
            healthy_nodes = [node_id for node_id, healthy in self.node_health.items() if healthy]
            
            if not healthy_nodes:
                logger.error("No healthy nodes for rebalancing")
                return False
            
            # Calculate target connections per node
            target_connections_per_node = total_connections // len(healthy_nodes)
            
            # Redistribute connections
            for node_id in healthy_nodes:
                current = self.nodes[node_id]["current_connections"]
                target = target_connections_per_node
                
                if current != target:
                    logger.info(f"Rebalancing node {node_id}: {current} -> {target} connections")
                    self.nodes[node_id]["current_connections"] = target
            
            logger.info("Connection rebalancing completed")
            return True
            
        except Exception as e:
            logger.error("Error rebalancing connections", error=str(e))
            return False 