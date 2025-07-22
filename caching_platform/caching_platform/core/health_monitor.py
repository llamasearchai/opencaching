"""Health monitoring for the caching platform."""

import asyncio
import time
import psutil
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import structlog

from .cache_manager import MultiTenantCacheManager
from ..config.settings import Settings
from ..config.schemas import HealthCheck, Alert, AlertSeverity

logger = structlog.get_logger(__name__)


class HealthMonitor:
    """Health monitoring system for the caching platform."""
    
    def __init__(self, cache_manager: MultiTenantCacheManager, settings: Settings):
        self.cache_manager = cache_manager
        self.settings = settings
        self.monitoring_config = settings.monitoring
        
        # Health state
        self.system_health: Dict[str, HealthCheck] = {}
        self.alerts: List[Alert] = []
        self.health_history: List[Dict[str, Any]] = []
        
        # Monitoring thresholds
        self.thresholds = self.monitoring_config.alert_thresholds
        
        # Performance tracking
        self.performance_metrics = {
            "cpu_usage": [],
            "memory_usage": [],
            "response_time": [],
            "error_rate": []
        }
        
        # Health check intervals
        self.check_intervals = {
            "system": 30,      # System metrics every 30 seconds
            "redis": 10,       # Redis health every 10 seconds
            "agents": 60,      # Agent health every minute
            "network": 30      # Network health every 30 seconds
        }
    
    async def initialize(self) -> bool:
        """Initialize the health monitor."""
        try:
            logger.info("Initializing health monitor")
            
            # Initialize health checks
            await self._initialize_health_checks()
            
            # Start monitoring tasks
            asyncio.create_task(self._system_monitor())
            asyncio.create_task(self._redis_monitor())
            asyncio.create_task(self._alert_manager())
            
            logger.info("Health monitor initialized successfully")
            return True
            
        except Exception as e:
            logger.error("Failed to initialize health monitor", error=str(e))
            return False
    
    async def start(self) -> bool:
        """Start the health monitor."""
        try:
            logger.info("Starting health monitor")
            return True
            
        except Exception as e:
            logger.error("Failed to start health monitor", error=str(e))
            return False
    
    async def stop(self):
        """Stop the health monitor."""
        logger.info("Stopping health monitor")
    
    async def _initialize_health_checks(self):
        """Initialize health check components."""
        try:
            # System health check
            self.system_health["system"] = HealthCheck(
                component="system",
                status="unknown",
                timestamp=datetime.utcnow()
            )
            
            # Redis health check
            self.system_health["redis"] = HealthCheck(
                component="redis",
                status="unknown",
                timestamp=datetime.utcnow()
            )
            
            # Network health check
            self.system_health["network"] = HealthCheck(
                component="network",
                status="unknown",
                timestamp=datetime.utcnow()
            )
            
            # Cache manager health check
            self.system_health["cache_manager"] = HealthCheck(
                component="cache_manager",
                status="unknown",
                timestamp=datetime.utcnow()
            )
            
            logger.info("Initialized health checks")
            
        except Exception as e:
            logger.error("Failed to initialize health checks", error=str(e))
    
    async def _system_monitor(self):
        """Monitor system health metrics."""
        while True:
            try:
                # Collect system metrics
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                
                # Store metrics
                self.performance_metrics["cpu_usage"].append(cpu_percent)
                self.performance_metrics["memory_usage"].append(memory.percent)
                
                # Keep only last 1000 entries
                for metric_list in self.performance_metrics.values():
                    if len(metric_list) > 1000:
                        metric_list.pop(0)
                
                # Update system health
                system_healthy = (
                    cpu_percent < self.thresholds["cpu_usage"] and
                    memory.percent < self.thresholds["memory_usage"]
                )
                
                self.system_health["system"] = HealthCheck(
                    component="system",
                    status="healthy" if system_healthy else "unhealthy",
                    timestamp=datetime.utcnow(),
                    details={
                        "cpu_percent": cpu_percent,
                        "memory_percent": memory.percent,
                        "disk_percent": disk.percent,
                        "memory_available_gb": memory.available / (1024**3),
                        "disk_free_gb": disk.free / (1024**3)
                    },
                    response_time_ms=cpu_percent * 10  # Simulate response time
                )
                
                # Check for alerts
                await self._check_system_alerts(cpu_percent, memory.percent, disk.percent)
                
                await asyncio.sleep(self.check_intervals["system"])
                
            except Exception as e:
                logger.error("System monitor error", error=str(e))
                await asyncio.sleep(10)
    
    async def _redis_monitor(self):
        """Monitor Redis cluster health."""
        while True:
            try:
                # Check Redis connection
                redis_healthy = await self._check_redis_health()
                
                # Update Redis health
                self.system_health["redis"] = HealthCheck(
                    component="redis",
                    status="healthy" if redis_healthy else "unhealthy",
                    timestamp=datetime.utcnow(),
                    details={
                        "connection_ok": redis_healthy,
                        "host": self.settings.redis.host,
                        "port": self.settings.redis.port
                    }
                )
                
                # Check cache manager health
                cache_manager_healthy = await self._check_cache_manager_health()
                
                self.system_health["cache_manager"] = HealthCheck(
                    component="cache_manager",
                    status="healthy" if cache_manager_healthy else "unhealthy",
                    timestamp=datetime.utcnow(),
                    details={
                        "tenants_count": len(self.cache_manager.tenants) if self.cache_manager else 0,
                        "total_operations": self.cache_manager.total_operations if self.cache_manager else 0
                    }
                )
                
                await asyncio.sleep(self.check_intervals["redis"])
                
            except Exception as e:
                logger.error("Redis monitor error", error=str(e))
                await asyncio.sleep(10)
    
    async def _check_redis_health(self) -> bool:
        """Check Redis cluster health."""
        try:
            if not self.cache_manager or not self.cache_manager.redis_client:
                return False
            
            # Test Redis connection
            start_time = time.time()
            await self.cache_manager.redis_client.ping()
            response_time = (time.time() - start_time) * 1000
            
            # Consider healthy if response time is reasonable
            return response_time < 1000  # 1 second threshold
            
        except Exception as e:
            logger.error("Redis health check failed", error=str(e))
            return False
    
    async def _check_cache_manager_health(self) -> bool:
        """Check cache manager health."""
        try:
            if not self.cache_manager:
                return False
            
            # Check if cache manager is operational
            # This is a simplified check - in a real system you'd check more aspects
            return True
            
        except Exception as e:
            logger.error("Cache manager health check failed", error=str(e))
            return False
    
    async def _check_system_alerts(self, cpu_percent: float, memory_percent: float, disk_percent: float):
        """Check for system alerts."""
        try:
            # CPU usage alert
            if cpu_percent > self.thresholds["cpu_usage"]:
                await self._create_alert(
                    title="High CPU Usage",
                    message=f"CPU usage is {cpu_percent:.1f}% (threshold: {self.thresholds['cpu_usage']}%)",
                    severity=AlertSeverity.WARNING if cpu_percent < 95 else AlertSeverity.CRITICAL,
                    source="system_monitor",
                    category="performance"
                )
            
            # Memory usage alert
            if memory_percent > self.thresholds["memory_usage"]:
                await self._create_alert(
                    title="High Memory Usage",
                    message=f"Memory usage is {memory_percent:.1f}% (threshold: {self.thresholds['memory_usage']}%)",
                    severity=AlertSeverity.WARNING if memory_percent < 95 else AlertSeverity.CRITICAL,
                    source="system_monitor",
                    category="performance"
                )
            
            # Disk usage alert
            if disk_percent > 90:
                await self._create_alert(
                    title="High Disk Usage",
                    message=f"Disk usage is {disk_percent:.1f}%",
                    severity=AlertSeverity.WARNING,
                    source="system_monitor",
                    category="storage"
                )
            
        except Exception as e:
            logger.error("Error checking system alerts", error=str(e))
    
    async def _create_alert(self, title: str, message: str, severity: AlertSeverity, 
                          source: str, category: str, tenant_id: str = None, node_id: str = None):
        """Create a new alert."""
        try:
            alert = Alert(
                id=f"alert_{int(time.time())}",
                title=title,
                message=message,
                severity=severity,
                source=source,
                category=category,
                tenant_id=tenant_id,
                node_id=node_id,
                created_at=datetime.utcnow()
            )
            
            self.alerts.append(alert)
            
            # Keep only last 1000 alerts
            if len(self.alerts) > 1000:
                self.alerts.pop(0)
            
            logger.warning(f"Alert created: {title} - {message}")
            
        except Exception as e:
            logger.error("Error creating alert", error=str(e))
    
    async def _alert_manager(self):
        """Manage and process alerts."""
        while True:
            try:
                # Process unacknowledged alerts
                unacknowledged_alerts = [alert for alert in self.alerts if not alert.acknowledged]
                
                for alert in unacknowledged_alerts:
                    # Check if alert should be escalated
                    if alert.severity == AlertSeverity.CRITICAL:
                        await self._escalate_alert(alert)
                    
                    # Auto-resolve some alerts after time
                    if alert.severity == AlertSeverity.INFO:
                        time_since_creation = datetime.utcnow() - alert.created_at
                        if time_since_creation > timedelta(hours=1):
                            alert.resolved = True
                            alert.resolved_at = datetime.utcnow()
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error("Alert manager error", error=str(e))
                await asyncio.sleep(10)
    
    async def _escalate_alert(self, alert: Alert):
        """Escalate a critical alert."""
        try:
            # In a real system, this would:
            # 1. Send notifications (email, Slack, etc.)
            # 2. Create incident tickets
            # 3. Trigger automated responses
            
            logger.critical(f"ESCALATING ALERT: {alert.title} - {alert.message}")
            
        except Exception as e:
            logger.error("Error escalating alert", error=str(e))
    
    async def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health status."""
        try:
            # Calculate overall health
            healthy_components = sum(1 for check in self.system_health.values() if check.status == "healthy")
            total_components = len(self.system_health)
            
            overall_health = "healthy" if healthy_components == total_components else "degraded"
            if healthy_components == 0:
                overall_health = "unhealthy"
            
            # Get recent performance metrics
            recent_cpu = self.performance_metrics["cpu_usage"][-10:] if self.performance_metrics["cpu_usage"] else []
            recent_memory = self.performance_metrics["memory_usage"][-10:] if self.performance_metrics["memory_usage"] else []
            
            return {
                "overall_status": overall_health,
                "healthy_components": healthy_components,
                "total_components": total_components,
                "components": {
                    name: check.dict() for name, check in self.system_health.items()
                },
                "performance": {
                    "avg_cpu_usage": sum(recent_cpu) / len(recent_cpu) if recent_cpu else 0.0,
                    "avg_memory_usage": sum(recent_memory) / len(recent_memory) if recent_memory else 0.0,
                    "current_cpu_usage": recent_cpu[-1] if recent_cpu else 0.0,
                    "current_memory_usage": recent_memory[-1] if recent_memory else 0.0
                },
                "alerts": {
                    "total": len(self.alerts),
                    "unacknowledged": len([a for a in self.alerts if not a.acknowledged]),
                    "critical": len([a for a in self.alerts if a.severity == AlertSeverity.CRITICAL and not a.resolved])
                }
            }
            
        except Exception as e:
            logger.error("Error getting system health", error=str(e))
            return {"overall_status": "unknown", "error": str(e)}
    
    async def get_redis_health(self) -> HealthCheck:
        """Get Redis cluster health."""
        return self.system_health.get("redis", HealthCheck(
            component="redis",
            status="unknown",
            timestamp=datetime.utcnow()
        ))
    
    async def get_alerts(self, severity: Optional[AlertSeverity] = None, 
                        acknowledged: Optional[bool] = None, limit: int = 100) -> List[Alert]:
        """Get alerts with optional filtering."""
        try:
            filtered_alerts = self.alerts
            
            if severity:
                filtered_alerts = [a for a in filtered_alerts if a.severity == severity]
            
            if acknowledged is not None:
                filtered_alerts = [a for a in filtered_alerts if a.acknowledged == acknowledged]
            
            # Sort by creation time (newest first)
            filtered_alerts.sort(key=lambda x: x.created_at, reverse=True)
            
            return filtered_alerts[:limit]
            
        except Exception as e:
            logger.error("Error getting alerts", error=str(e))
            return []
    
    async def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert."""
        try:
            for alert in self.alerts:
                if alert.id == alert_id:
                    alert.acknowledged = True
                    alert.acknowledged_at = datetime.utcnow()
                    logger.info(f"Acknowledged alert: {alert.title}")
                    return True
            
            logger.warning(f"Alert {alert_id} not found")
            return False
            
        except Exception as e:
            logger.error("Error acknowledging alert", error=str(e))
            return False
    
    async def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert."""
        try:
            for alert in self.alerts:
                if alert.id == alert_id:
                    alert.resolved = True
                    alert.resolved_at = datetime.utcnow()
                    logger.info(f"Resolved alert: {alert.title}")
                    return True
            
            logger.warning(f"Alert {alert_id} not found")
            return False
            
        except Exception as e:
            logger.error("Error resolving alert", error=str(e))
            return False
    
    async def get_performance_metrics(self, hours: int = 24) -> Dict[str, Any]:
        """Get performance metrics for the specified number of hours."""
        try:
            # Calculate cutoff time
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            # Filter metrics (simplified - in real system you'd have timestamps)
            cpu_metrics = self.performance_metrics["cpu_usage"][-100:]  # Last 100 samples
            memory_metrics = self.performance_metrics["memory_usage"][-100:]
            
            return {
                "cpu_usage": {
                    "current": cpu_metrics[-1] if cpu_metrics else 0.0,
                    "average": sum(cpu_metrics) / len(cpu_metrics) if cpu_metrics else 0.0,
                    "max": max(cpu_metrics) if cpu_metrics else 0.0,
                    "min": min(cpu_metrics) if cpu_metrics else 0.0,
                    "samples": len(cpu_metrics)
                },
                "memory_usage": {
                    "current": memory_metrics[-1] if memory_metrics else 0.0,
                    "average": sum(memory_metrics) / len(memory_metrics) if memory_metrics else 0.0,
                    "max": max(memory_metrics) if memory_metrics else 0.0,
                    "min": min(memory_metrics) if memory_metrics else 0.0,
                    "samples": len(memory_metrics)
                },
                "period_hours": hours
            }
            
        except Exception as e:
            logger.error("Error getting performance metrics", error=str(e))
            return {}
    
    async def set_thresholds(self, thresholds: Dict[str, float]) -> bool:
        """Update monitoring thresholds."""
        try:
            for key, value in thresholds.items():
                if key in self.thresholds:
                    self.thresholds[key] = value
            
            logger.info("Updated monitoring thresholds")
            return True
            
        except Exception as e:
            logger.error("Error updating thresholds", error=str(e))
            return False
    
    async def run_health_check(self, component: str = None) -> Dict[str, Any]:
        """Run a manual health check."""
        try:
            if component:
                # Check specific component
                if component == "redis":
                    redis_healthy = await self._check_redis_health()
                    return {
                        "component": component,
                        "status": "healthy" if redis_healthy else "unhealthy",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                elif component == "system":
                    cpu_percent = psutil.cpu_percent(interval=1)
                    memory = psutil.virtual_memory()
                    return {
                        "component": component,
                        "status": "healthy" if cpu_percent < 90 and memory.percent < 90 else "unhealthy",
                        "timestamp": datetime.utcnow().isoformat(),
                        "details": {
                            "cpu_percent": cpu_percent,
                            "memory_percent": memory.percent
                        }
                    }
                else:
                    return {"error": f"Unknown component: {component}"}
            else:
                # Run all health checks
                results = {}
                for comp in self.system_health.keys():
                    results[comp] = await self.run_health_check(comp)
                return results
                
        except Exception as e:
            logger.error("Error running health check", error=str(e))
            return {"error": str(e)} 