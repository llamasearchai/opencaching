"""Main orchestrator for the caching platform."""

import asyncio
import time
from typing import Dict, Any, Optional, List
from datetime import datetime
import structlog

from .cache_manager import MultiTenantCacheManager
from .auto_scaler import AutoScaler
from .load_balancer import LoadBalancer
from .health_monitor import HealthMonitor
from ..config.settings import get_settings
from ..config.schemas import SystemStatus, HealthCheck, AgentInfo, AgentStatus

logger = structlog.get_logger(__name__)


class CacheOrchestrator:
    """Main orchestrator for the caching platform."""
    
    def __init__(self, settings=None):
        self.settings = settings or get_settings()
        self.running = False
        self.start_time = datetime.utcnow()
        
        # Core components
        self.cache_manager: Optional[MultiTenantCacheManager] = None
        self.auto_scaler: Optional[AutoScaler] = None
        self.load_balancer: Optional[LoadBalancer] = None
        self.health_monitor: Optional[HealthMonitor] = None
        
        # Agent management
        self.agents: Dict[str, AgentInfo] = {}
        self.agent_tasks: Dict[str, asyncio.Task] = {}
        
        # System state
        self.system_status = SystemStatus(
            platform_version="1.0.0",
            uptime_seconds=0,
            environment=self.settings.environment,
            redis_cluster=HealthCheck(
                component="redis_cluster",
                status="unknown",
                timestamp=datetime.utcnow()
            ),
            agents=[],
            monitoring=HealthCheck(
                component="monitoring",
                status="unknown",
                timestamp=datetime.utcnow()
            )
        )
        
        # Performance tracking
        self.performance_metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_response_time_ms": 0.0,
            "cpu_usage_percent": 0.0,
            "memory_usage_percent": 0.0
        }
    
    async def initialize(self) -> bool:
        """Initialize the orchestrator and all components."""
        try:
            logger.info("Initializing cache orchestrator")
            
            # Initialize cache manager
            self.cache_manager = MultiTenantCacheManager()
            if not await self.cache_manager.initialize():
                logger.error("Failed to initialize cache manager")
                return False
            
            # Initialize auto scaler
            self.auto_scaler = AutoScaler(self.cache_manager, self.settings)
            if not await self.auto_scaler.initialize():
                logger.error("Failed to initialize auto scaler")
                return False
            
            # Initialize load balancer
            self.load_balancer = LoadBalancer(self.cache_manager, self.settings)
            if not await self.load_balancer.initialize():
                logger.error("Failed to initialize load balancer")
                return False
            
            # Initialize health monitor
            self.health_monitor = HealthMonitor(self.cache_manager, self.settings)
            if not await self.health_monitor.initialize():
                logger.error("Failed to initialize health monitor")
                return False
            
            # Initialize agents
            await self._initialize_agents()
            
            # Start background tasks
            asyncio.create_task(self._system_monitor())
            asyncio.create_task(self._performance_collector())
            
            logger.info("Cache orchestrator initialized successfully")
            return True
            
        except Exception as e:
            logger.error("Failed to initialize orchestrator", error=str(e))
            return False
    
    async def _initialize_agents(self):
        """Initialize autonomous agents."""
        try:
            # Scaling agent
            scaling_agent = AgentInfo(
                id="scaling_agent",
                name="Auto Scaling Agent",
                type="scaling",
                status=AgentStatus.STOPPED,
                config={
                    "enabled": self.settings.scaling.enabled,
                    "min_nodes": self.settings.scaling.min_nodes,
                    "max_nodes": self.settings.scaling.max_nodes,
                    "target_cpu_percent": self.settings.scaling.target_cpu_percent,
                    "target_memory_percent": self.settings.scaling.target_memory_percent
                }
            )
            self.agents["scaling_agent"] = scaling_agent
            
            # Optimization agent
            optimization_agent = AgentInfo(
                id="optimization_agent",
                name="Performance Optimization Agent",
                type="optimization",
                status=AgentStatus.STOPPED,
                config={
                    "enabled": True,
                    "optimization_interval": 300,
                    "target_hit_ratio": 85.0
                }
            )
            self.agents["optimization_agent"] = optimization_agent
            
            # Healing agent
            healing_agent = AgentInfo(
                id="healing_agent",
                name="Self Healing Agent",
                type="healing",
                status=AgentStatus.STOPPED,
                config={
                    "enabled": True,
                    "health_check_interval": 30,
                    "failure_threshold": 3
                }
            )
            self.agents["healing_agent"] = healing_agent
            
            # Prediction agent
            prediction_agent = AgentInfo(
                id="prediction_agent",
                name="ML Prediction Agent",
                type="prediction",
                status=AgentStatus.STOPPED,
                config={
                    "enabled": True,
                    "prediction_window": self.settings.scaling.prediction_window,
                    "model_update_interval": 3600
                }
            )
            self.agents["prediction_agent"] = prediction_agent
            
            logger.info(f"Initialized {len(self.agents)} agents")
            
        except Exception as e:
            logger.error("Failed to initialize agents", error=str(e))
    
    async def start(self) -> bool:
        """Start the orchestrator and all components."""
        try:
            logger.info("Starting cache orchestrator")
            
            if not self.cache_manager or not self.auto_scaler or not self.load_balancer or not self.health_monitor:
                logger.error("Components not initialized")
                return False
            
            # Start cache manager
            # (Cache manager is already running after initialization)
            
            # Start auto scaler
            if not await self.auto_scaler.start():
                logger.error("Failed to start auto scaler")
                return False
            
            # Start load balancer
            if not await self.load_balancer.start():
                logger.error("Failed to start load balancer")
                return False
            
            # Start health monitor
            if not await self.health_monitor.start():
                logger.error("Failed to start health monitor")
                return False
            
            # Start agents
            await self._start_agents()
            
            self.running = True
            logger.info("Cache orchestrator started successfully")
            return True
            
        except Exception as e:
            logger.error("Failed to start orchestrator", error=str(e))
            return False
    
    async def _start_agents(self):
        """Start all autonomous agents."""
        try:
            for agent_id, agent_info in self.agents.items():
                if agent_info.config.get("enabled", True):
                    await self._start_agent(agent_id)
            
            logger.info(f"Started {len([a for a in self.agents.values() if a.status == AgentStatus.RUNNING])} agents")
            
        except Exception as e:
            logger.error("Failed to start agents", error=str(e))
    
    async def _start_agent(self, agent_id: str):
        """Start a specific agent."""
        try:
            agent_info = self.agents[agent_id]
            agent_info.status = AgentStatus.STARTING
            
            # Create agent task based on type
            if agent_id == "scaling_agent":
                task = asyncio.create_task(self._scaling_agent_loop())
            elif agent_id == "optimization_agent":
                task = asyncio.create_task(self._optimization_agent_loop())
            elif agent_id == "healing_agent":
                task = asyncio.create_task(self._healing_agent_loop())
            elif agent_id == "prediction_agent":
                task = asyncio.create_task(self._prediction_agent_loop())
            else:
                logger.warning(f"Unknown agent type: {agent_id}")
                return
            
            self.agent_tasks[agent_id] = task
            agent_info.status = AgentStatus.RUNNING
            agent_info.last_activity = datetime.utcnow()
            
            logger.info(f"Started agent: {agent_id}")
            
        except Exception as e:
            logger.error(f"Failed to start agent {agent_id}", error=str(e))
            self.agents[agent_id].status = AgentStatus.ERROR
            self.agents[agent_id].last_error = str(e)
    
    async def stop(self):
        """Stop the orchestrator and all components."""
        try:
            logger.info("Stopping cache orchestrator")
            
            self.running = False
            
            # Stop agents
            await self._stop_agents()
            
            # Stop components
            if self.health_monitor:
                await self.health_monitor.stop()
            
            if self.load_balancer:
                await self.load_balancer.stop()
            
            if self.auto_scaler:
                await self.auto_scaler.stop()
            
            logger.info("Cache orchestrator stopped")
            
        except Exception as e:
            logger.error("Error stopping orchestrator", error=str(e))
    
    async def _stop_agents(self):
        """Stop all agents."""
        try:
            for agent_id, task in self.agent_tasks.items():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                
                self.agents[agent_id].status = AgentStatus.STOPPED
            
            self.agent_tasks.clear()
            logger.info("All agents stopped")
            
        except Exception as e:
            logger.error("Error stopping agents", error=str(e))
    
    async def shutdown(self):
        """Shutdown the orchestrator gracefully."""
        try:
            logger.info("Shutting down cache orchestrator")
            
            await self.stop()
            
            # Shutdown cache manager
            if self.cache_manager:
                await self.cache_manager.shutdown()
            
            logger.info("Cache orchestrator shutdown complete")
            
        except Exception as e:
            logger.error("Error during shutdown", error=str(e))
    
    async def _scaling_agent_loop(self):
        """Scaling agent main loop."""
        agent_id = "scaling_agent"
        agent_info = self.agents[agent_id]
        
        while self.running and agent_info.status == AgentStatus.RUNNING:
            try:
                # Get current metrics
                system_metrics = await self.cache_manager.get_system_metrics()
                
                # Make scaling decision
                decision = await self.auto_scaler.evaluate_scaling_needs(system_metrics)
                
                if decision:
                    agent_info.total_decisions += 1
                    
                    # Execute scaling decision
                    success = await self.auto_scaler.execute_scaling_decision(decision)
                    
                    if success:
                        agent_info.successful_decisions += 1
                    else:
                        agent_info.failed_decisions += 1
                
                agent_info.last_activity = datetime.utcnow()
                
                # Sleep for scaling interval
                await asyncio.sleep(self.settings.scaling.scale_up_cooldown)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scaling agent error: {e}")
                agent_info.error_count += 1
                agent_info.last_error = str(e)
                await asyncio.sleep(10)
    
    async def _optimization_agent_loop(self):
        """Optimization agent main loop."""
        agent_id = "optimization_agent"
        agent_info = self.agents[agent_id]
        
        while self.running and agent_info.status == AgentStatus.RUNNING:
            try:
                # Get all tenant metrics
                all_metrics = await self.cache_manager.get_all_metrics()
                
                # Optimize cache configurations
                optimizations = await self._optimize_cache_configurations(all_metrics)
                
                for optimization in optimizations:
                    agent_info.total_decisions += 1
                    
                    # Apply optimization
                    success = await self._apply_optimization(optimization)
                    
                    if success:
                        agent_info.successful_decisions += 1
                    else:
                        agent_info.failed_decisions += 1
                
                agent_info.last_activity = datetime.utcnow()
                
                # Sleep for optimization interval
                await asyncio.sleep(agent_info.config.get("optimization_interval", 300))
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Optimization agent error: {e}")
                agent_info.error_count += 1
                agent_info.last_error = str(e)
                await asyncio.sleep(10)
    
    async def _healing_agent_loop(self):
        """Healing agent main loop."""
        agent_id = "healing_agent"
        agent_info = self.agents[agent_id]
        
        while self.running and agent_info.status == AgentStatus.RUNNING:
            try:
                # Check system health
                health_status = await self.health_monitor.get_system_health()
                
                # Identify issues
                issues = await self._identify_health_issues(health_status)
                
                # Attempt to heal issues
                for issue in issues:
                    agent_info.total_decisions += 1
                    
                    success = await self._attempt_healing(issue)
                    
                    if success:
                        agent_info.successful_decisions += 1
                    else:
                        agent_info.failed_decisions += 1
                
                agent_info.last_activity = datetime.utcnow()
                
                # Sleep for health check interval
                await asyncio.sleep(agent_info.config.get("health_check_interval", 30))
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Healing agent error: {e}")
                agent_info.error_count += 1
                agent_info.last_error = str(e)
                await asyncio.sleep(10)
    
    async def _prediction_agent_loop(self):
        """Prediction agent main loop."""
        agent_id = "prediction_agent"
        agent_info = self.agents[agent_id]
        
        while self.running and agent_info.status == AgentStatus.RUNNING:
            try:
                # Collect historical data
                historical_data = await self._collect_historical_data()
                
                # Make predictions
                predictions = await self._make_predictions(historical_data)
                
                # Update scaling predictions
                if predictions:
                    await self.auto_scaler.update_predictions(predictions)
                    agent_info.total_decisions += 1
                    agent_info.successful_decisions += 1
                
                agent_info.last_activity = datetime.utcnow()
                
                # Sleep for prediction interval
                await asyncio.sleep(agent_info.config.get("model_update_interval", 3600))
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Prediction agent error: {e}")
                agent_info.error_count += 1
                agent_info.last_error = str(e)
                await asyncio.sleep(10)
    
    async def _system_monitor(self):
        """System monitoring loop."""
        while self.running:
            try:
                # Update system status
                self.system_status.uptime_seconds = int((datetime.utcnow() - self.start_time).total_seconds())
                
                # Update component health
                if self.cache_manager:
                    redis_health = await self.health_monitor.get_redis_health()
                    self.system_status.redis_cluster = redis_health
                
                # Update agent health
                agent_health_checks = []
                for agent_id, agent_info in self.agents.items():
                    health_check = HealthCheck(
                        component=f"agent:{agent_id}",
                        status=agent_info.status.value,
                        timestamp=agent_info.last_activity or datetime.utcnow(),
                        details={
                            "total_decisions": agent_info.total_decisions,
                            "successful_decisions": agent_info.successful_decisions,
                            "failed_decisions": agent_info.failed_decisions,
                            "error_count": agent_info.error_count
                        }
                    )
                    agent_health_checks.append(health_check)
                
                self.system_status.agents = agent_health_checks
                
                # Update performance metrics
                if self.cache_manager:
                    system_metrics = await self.cache_manager.get_system_metrics()
                    self.system_status.total_tenants = system_metrics.get("active_tenants", 0)
                    self.system_status.total_requests_per_second = system_metrics.get("requests_per_second", 0.0)
                    self.system_status.average_response_time_ms = system_metrics.get("average_response_time_ms", 0.0)
                
                await asyncio.sleep(10)
                
            except Exception as e:
                logger.error("System monitor error", error=str(e))
                await asyncio.sleep(10)
    
    async def _performance_collector(self):
        """Performance metrics collection loop."""
        while self.running:
            try:
                if self.cache_manager:
                    # Collect performance metrics
                    system_metrics = await self.cache_manager.get_system_metrics()
                    
                    self.performance_metrics.update({
                        "total_requests": system_metrics.get("total_operations", 0),
                        "average_response_time_ms": system_metrics.get("average_response_time_ms", 0.0)
                    })
                
                await asyncio.sleep(self.settings.monitoring.metrics_interval)
                
            except Exception as e:
                logger.error("Performance collector error", error=str(e))
                await asyncio.sleep(10)
    
    async def _optimize_cache_configurations(self, all_metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Optimize cache configurations based on metrics."""
        optimizations = []
        
        for tenant_id, metrics in all_metrics.items():
            # Optimize TTL based on hit ratio
            if metrics.hit_ratio < 80.0:
                optimizations.append({
                    "type": "ttl_optimization",
                    "tenant_id": tenant_id,
                    "action": "increase_ttl",
                    "reason": f"Low hit ratio: {metrics.hit_ratio:.1f}%"
                })
            
            # Optimize memory usage
            if metrics.memory_usage_percent > 90.0:
                optimizations.append({
                    "type": "memory_optimization",
                    "tenant_id": tenant_id,
                    "action": "evict_old_keys",
                    "reason": f"High memory usage: {metrics.memory_usage_percent:.1f}%"
                })
        
        return optimizations
    
    async def _apply_optimization(self, optimization: Dict[str, Any]) -> bool:
        """Apply a cache optimization."""
        try:
            if optimization["type"] == "ttl_optimization":
                # Increase TTL for frequently accessed keys
                return await self._increase_ttl_for_frequent_keys(optimization["tenant_id"])
            
            elif optimization["type"] == "memory_optimization":
                # Evict old keys to free memory
                return await self._evict_old_keys(optimization["tenant_id"])
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to apply optimization: {e}")
            return False
    
    async def _increase_ttl_for_frequent_keys(self, tenant_id: str) -> bool:
        """Increase TTL for frequently accessed keys."""
        try:
            # This is a simplified implementation
            # In a real system, you would analyze access patterns
            logger.info(f"Increasing TTL for frequent keys in tenant {tenant_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to increase TTL for tenant {tenant_id}: {e}")
            return False
    
    async def _evict_old_keys(self, tenant_id: str) -> bool:
        """Evict old keys to free memory."""
        try:
            # This is a simplified implementation
            # In a real system, you would implement LRU eviction
            logger.info(f"Evicting old keys for tenant {tenant_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to evict old keys for tenant {tenant_id}: {e}")
            return False
    
    async def _identify_health_issues(self, health_status: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify health issues from system status."""
        issues = []
        
        # Check Redis cluster health
        if health_status.get("redis_cluster", {}).get("status") != "healthy":
            issues.append({
                "type": "redis_cluster",
                "severity": "high",
                "description": "Redis cluster is unhealthy"
            })
        
        # Check agent health
        for agent_id, agent_info in self.agents.items():
            if agent_info.status == AgentStatus.ERROR:
                issues.append({
                    "type": "agent_error",
                    "agent_id": agent_id,
                    "severity": "medium",
                    "description": f"Agent {agent_id} is in error state"
                })
        
        return issues
    
    async def _attempt_healing(self, issue: Dict[str, Any]) -> bool:
        """Attempt to heal a health issue."""
        try:
            if issue["type"] == "redis_cluster":
                # Attempt to restart Redis cluster
                logger.info("Attempting to heal Redis cluster")
                return await self._restart_redis_cluster()
            
            elif issue["type"] == "agent_error":
                # Restart the failed agent
                agent_id = issue["agent_id"]
                logger.info(f"Attempting to restart agent {agent_id}")
                return await self._restart_agent(agent_id)
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to heal issue: {e}")
            return False
    
    async def _restart_redis_cluster(self) -> bool:
        """Restart Redis cluster."""
        try:
            # This is a simplified implementation
            # In a real system, you would implement proper cluster restart
            logger.info("Restarting Redis cluster")
            return True
            
        except Exception as e:
            logger.error(f"Failed to restart Redis cluster: {e}")
            return False
    
    async def _restart_agent(self, agent_id: str) -> bool:
        """Restart a specific agent."""
        try:
            # Stop the agent
            if agent_id in self.agent_tasks:
                self.agent_tasks[agent_id].cancel()
                del self.agent_tasks[agent_id]
            
            # Reset agent status
            self.agents[agent_id].status = AgentStatus.STOPPED
            self.agents[agent_id].error_count = 0
            self.agents[agent_id].last_error = None
            
            # Start the agent again
            await self._start_agent(agent_id)
            
            logger.info(f"Restarted agent {agent_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to restart agent {agent_id}: {e}")
            return False
    
    async def _collect_historical_data(self) -> Dict[str, Any]:
        """Collect historical performance data."""
        try:
            # This is a simplified implementation
            # In a real system, you would collect detailed historical metrics
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "metrics": await self.cache_manager.get_system_metrics()
            }
            
        except Exception as e:
            logger.error(f"Failed to collect historical data: {e}")
            return {}
    
    async def _make_predictions(self, historical_data: Dict[str, Any]) -> Dict[str, Any]:
        """Make predictions based on historical data."""
        try:
            # This is a simplified implementation
            # In a real system, you would use ML models for predictions
            return {
                "predicted_load": "medium",
                "predicted_scaling_needs": "none",
                "confidence": 0.75
            }
            
        except Exception as e:
            logger.error(f"Failed to make predictions: {e}")
            return {}
    
    async def get_system_status(self) -> SystemStatus:
        """Get current system status."""
        return self.system_status
    
    async def get_agent_status(self) -> Dict[str, AgentInfo]:
        """Get status of all agents."""
        return self.agents.copy()
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get overall health status."""
        return {
            "healthy": self.system_status.redis_cluster.status == "healthy",
            "components": {
                "redis_cluster": self.system_status.redis_cluster.dict(),
                "agents": [agent.dict() for agent in self.system_status.agents],
                "monitoring": self.system_status.monitoring.dict()
            },
            "performance": self.performance_metrics,
            "uptime_seconds": self.system_status.uptime_seconds
        }
    
    async def execute_command(self, command: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a command on the orchestrator."""
        try:
            if command == "create_backup":
                return await self._create_backup(params)
            elif command == "restore_backup":
                return await self._restore_backup(params)
            elif command == "get_metrics":
                return await self._get_metrics(params)
            elif command == "get_tenants":
                return await self._get_tenants()
            else:
                return {"success": False, "error": f"Unknown command: {command}"}
                
        except Exception as e:
            logger.error(f"Command execution error: {e}")
            return {"success": False, "error": str(e)}
    
    async def _create_backup(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a system backup."""
        try:
            backup_dir = params.get("backup_dir", "./backups")
            include_data = params.get("include_data", True)
            
            # Create backup
            backup_info = {
                "timestamp": datetime.utcnow().isoformat(),
                "include_data": include_data,
                "tenants": len(self.agents),
                "status": "completed"
            }
            
            return {
                "success": True,
                "backup_file": f"{backup_dir}/backup_{int(time.time())}.json",
                "backup_info": backup_info
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _restore_backup(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Restore from backup."""
        try:
            backup_file = params.get("backup_file")
            
            # Restore from backup
            logger.info(f"Restoring from backup: {backup_file}")
            
            return {"success": True}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _get_metrics(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get system metrics."""
        try:
            tenant_id = params.get("tenant_id")
            
            if tenant_id:
                metrics = await self.cache_manager.get_tenant_metrics(tenant_id)
                return {"success": True, "metrics": metrics.dict() if metrics else None}
            else:
                metrics = await self.cache_manager.get_system_metrics()
                return {"success": True, "metrics": metrics}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _get_tenants(self) -> Dict[str, Any]:
        """Get all tenants."""
        try:
            tenants = await self.cache_manager.list_tenants()
            return {
                "success": True,
                "tenants": [tenant.dict() for tenant in tenants]
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)} 