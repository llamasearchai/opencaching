"""Metrics collection and monitoring for the caching platform."""

import asyncio
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import structlog
from prometheus_client import Counter, Gauge, Histogram, Summary, generate_latest, CONTENT_TYPE_LATEST

from ..config.settings import get_settings

logger = structlog.get_logger(__name__)


class MetricsCollector:
    """Metrics collection and monitoring system."""
    
    def __init__(self):
        self.settings = get_settings()
        
        # Prometheus metrics
        self.cache_operations_total = Counter(
            'cache_operations_total',
            'Total number of cache operations',
            ['operation', 'tenant_id', 'status']
        )
        
        self.cache_hit_ratio = Gauge(
            'cache_hit_ratio',
            'Cache hit ratio percentage',
            ['tenant_id']
        )
        
        self.cache_response_time = Histogram(
            'cache_response_time_seconds',
            'Cache operation response time',
            ['operation', 'tenant_id'],
            buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
        )
        
        self.cache_memory_usage = Gauge(
            'cache_memory_usage_bytes',
            'Cache memory usage in bytes',
            ['tenant_id']
        )
        
        self.active_connections = Gauge(
            'active_connections',
            'Number of active connections',
            ['node_id']
        )
        
        self.system_cpu_usage = Gauge(
            'system_cpu_usage_percent',
            'System CPU usage percentage'
        )
        
        self.system_memory_usage = Gauge(
            'system_memory_usage_percent',
            'System memory usage percentage'
        )
        
        self.redis_connections = Gauge(
            'redis_connections',
            'Number of Redis connections',
            ['node_id', 'status']
        )
        
        self.tenant_quota_usage = Gauge(
            'tenant_quota_usage_percent',
            'Tenant quota usage percentage',
            ['tenant_id', 'resource_type']
        )
        
        # Custom metrics storage
        self.custom_metrics: Dict[str, Any] = {}
        self.metrics_history: List[Dict[str, Any]] = []
        
        # Collection intervals
        self.collection_interval = self.settings.monitoring.metrics_interval
        
    async def initialize(self) -> bool:
        """Initialize the metrics collector."""
        try:
            logger.info("Initializing metrics collector")
            
            # Start background collection
            asyncio.create_task(self._metrics_collector())
            
            logger.info("Metrics collector initialized successfully")
            return True
            
        except Exception as e:
            logger.error("Failed to initialize metrics collector", error=str(e))
            return False
    
    async def record_cache_operation(self, operation: str, tenant_id: str, 
                                   response_time: float, success: bool):
        """Record a cache operation metric."""
        try:
            status = "success" if success else "failure"
            
            # Update Prometheus metrics
            self.cache_operations_total.labels(
                operation=operation,
                tenant_id=tenant_id,
                status=status
            ).inc()
            
            self.cache_response_time.labels(
                operation=operation,
                tenant_id=tenant_id
            ).observe(response_time)
            
            # Store custom metric
            metric_key = f"cache_operation_{operation}_{tenant_id}"
            if metric_key not in self.custom_metrics:
                self.custom_metrics[metric_key] = {
                    "total": 0,
                    "successful": 0,
                    "failed": 0,
                    "total_response_time": 0.0,
                    "min_response_time": float('inf'),
                    "max_response_time": 0.0
                }
            
            metric = self.custom_metrics[metric_key]
            metric["total"] += 1
            metric["total_response_time"] += response_time
            
            if success:
                metric["successful"] += 1
            else:
                metric["failed"] += 1
            
            metric["min_response_time"] = min(metric["min_response_time"], response_time)
            metric["max_response_time"] = max(metric["max_response_time"], response_time)
            
        except Exception as e:
            logger.error("Error recording cache operation metric", error=str(e))
    
    async def update_cache_hit_ratio(self, tenant_id: str, hit_ratio: float):
        """Update cache hit ratio metric."""
        try:
            self.cache_hit_ratio.labels(tenant_id=tenant_id).set(hit_ratio)
            
            # Store custom metric
            metric_key = f"hit_ratio_{tenant_id}"
            self.custom_metrics[metric_key] = {
                "current": hit_ratio,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error("Error updating cache hit ratio", error=str(e))
    
    async def update_memory_usage(self, tenant_id: str, memory_bytes: int):
        """Update memory usage metric."""
        try:
            self.cache_memory_usage.labels(tenant_id=tenant_id).set(memory_bytes)
            
            # Store custom metric
            metric_key = f"memory_usage_{tenant_id}"
            self.custom_metrics[metric_key] = {
                "bytes": memory_bytes,
                "mb": memory_bytes / (1024 * 1024),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error("Error updating memory usage", error=str(e))
    
    async def update_connection_count(self, node_id: str, count: int):
        """Update connection count metric."""
        try:
            self.active_connections.labels(node_id=node_id).set(count)
            
            # Store custom metric
            metric_key = f"connections_{node_id}"
            self.custom_metrics[metric_key] = {
                "count": count,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error("Error updating connection count", error=str(e))
    
    async def update_system_metrics(self, cpu_percent: float, memory_percent: float):
        """Update system metrics."""
        try:
            self.system_cpu_usage.set(cpu_percent)
            self.system_memory_usage.set(memory_percent)
            
            # Store custom metrics
            self.custom_metrics["system_cpu"] = {
                "percent": cpu_percent,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self.custom_metrics["system_memory"] = {
                "percent": memory_percent,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error("Error updating system metrics", error=str(e))
    
    async def update_redis_metrics(self, node_id: str, connected_clients: int, 
                                 used_memory: int, total_commands: int):
        """Update Redis-specific metrics."""
        try:
            self.redis_connections.labels(node_id=node_id, status="connected").set(connected_clients)
            
            # Store custom metrics
            metric_key = f"redis_{node_id}"
            self.custom_metrics[metric_key] = {
                "connected_clients": connected_clients,
                "used_memory_bytes": used_memory,
                "used_memory_mb": used_memory / (1024 * 1024),
                "total_commands": total_commands,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error("Error updating Redis metrics", error=str(e))
    
    async def update_tenant_quota(self, tenant_id: str, resource_type: str, usage_percent: float):
        """Update tenant quota usage metric."""
        try:
            self.tenant_quota_usage.labels(
                tenant_id=tenant_id,
                resource_type=resource_type
            ).set(usage_percent)
            
            # Store custom metric
            metric_key = f"quota_{tenant_id}_{resource_type}"
            self.custom_metrics[metric_key] = {
                "usage_percent": usage_percent,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error("Error updating tenant quota", error=str(e))
    
    async def _metrics_collector(self):
        """Background task to collect and store metrics."""
        while True:
            try:
                # Collect system metrics
                import psutil
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                
                await self.update_system_metrics(cpu_percent, memory.percent)
                
                # Store metrics history
                metrics_snapshot = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "system": {
                        "cpu_percent": cpu_percent,
                        "memory_percent": memory.percent,
                        "memory_available_gb": memory.available / (1024**3)
                    },
                    "custom_metrics": self.custom_metrics.copy()
                }
                
                self.metrics_history.append(metrics_snapshot)
                
                # Keep only last 1000 entries
                if len(self.metrics_history) > 1000:
                    self.metrics_history.pop(0)
                
                await asyncio.sleep(self.collection_interval)
                
            except Exception as e:
                logger.error("Metrics collector error", error=str(e))
                await asyncio.sleep(10)
    
    def get_prometheus_metrics(self) -> str:
        """Get Prometheus metrics in text format."""
        try:
            return generate_latest()
        except Exception as e:
            logger.error("Error generating Prometheus metrics", error=str(e))
            return ""
    
    async def get_metrics_summary(self) -> Dict[str, Any]:
        """Get a summary of all metrics."""
        try:
            summary = {
                "timestamp": datetime.utcnow().isoformat(),
                "system_metrics": {},
                "cache_metrics": {},
                "tenant_metrics": {},
                "redis_metrics": {}
            }
            
            # System metrics
            if "system_cpu" in self.custom_metrics:
                summary["system_metrics"]["cpu_percent"] = self.custom_metrics["system_cpu"]["percent"]
            
            if "system_memory" in self.custom_metrics:
                summary["system_metrics"]["memory_percent"] = self.custom_metrics["system_memory"]["percent"]
            
            # Cache metrics
            cache_operations = {}
            for key, metric in self.custom_metrics.items():
                if key.startswith("cache_operation_"):
                    operation = key.split("_")[2]
                    tenant_id = key.split("_")[3]
                    
                    if operation not in cache_operations:
                        cache_operations[operation] = {}
                    
                    cache_operations[operation][tenant_id] = {
                        "total": metric["total"],
                        "successful": metric["successful"],
                        "failed": metric["failed"],
                        "avg_response_time": metric["total_response_time"] / metric["total"] if metric["total"] > 0 else 0.0,
                        "min_response_time": metric["min_response_time"] if metric["min_response_time"] != float('inf') else 0.0,
                        "max_response_time": metric["max_response_time"]
                    }
            
            summary["cache_metrics"] = cache_operations
            
            # Tenant metrics
            tenant_metrics = {}
            for key, metric in self.custom_metrics.items():
                if key.startswith("hit_ratio_"):
                    tenant_id = key.split("_")[2]
                    tenant_metrics[tenant_id] = {
                        "hit_ratio": metric["current"]
                    }
                
                if key.startswith("memory_usage_"):
                    tenant_id = key.split("_")[2]
                    if tenant_id not in tenant_metrics:
                        tenant_metrics[tenant_id] = {}
                    tenant_metrics[tenant_id]["memory_mb"] = metric["mb"]
            
            summary["tenant_metrics"] = tenant_metrics
            
            # Redis metrics
            redis_metrics = {}
            for key, metric in self.custom_metrics.items():
                if key.startswith("redis_"):
                    node_id = key.split("_")[1]
                    redis_metrics[node_id] = {
                        "connected_clients": metric["connected_clients"],
                        "used_memory_mb": metric["used_memory_mb"],
                        "total_commands": metric["total_commands"]
                    }
            
            summary["redis_metrics"] = redis_metrics
            
            return summary
            
        except Exception as e:
            logger.error("Error getting metrics summary", error=str(e))
            return {"error": str(e)}
    
    async def get_metrics_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get metrics history for the specified number of hours."""
        try:
            # Calculate cutoff time
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            # Filter history
            filtered_history = []
            for entry in self.metrics_history:
                entry_time = datetime.fromisoformat(entry["timestamp"])
                if entry_time >= cutoff_time:
                    filtered_history.append(entry)
            
            return filtered_history
            
        except Exception as e:
            logger.error("Error getting metrics history", error=str(e))
            return []
    
    async def get_tenant_metrics(self, tenant_id: str) -> Dict[str, Any]:
        """Get metrics for a specific tenant."""
        try:
            tenant_metrics = {
                "tenant_id": tenant_id,
                "timestamp": datetime.utcnow().isoformat(),
                "operations": {},
                "performance": {},
                "quota": {}
            }
            
            # Get operation metrics
            for key, metric in self.custom_metrics.items():
                if key.startswith(f"cache_operation_") and tenant_id in key:
                    operation = key.split("_")[2]
                    tenant_metrics["operations"][operation] = {
                        "total": metric["total"],
                        "successful": metric["successful"],
                        "failed": metric["failed"],
                        "success_rate": (metric["successful"] / metric["total"] * 100) if metric["total"] > 0 else 0.0,
                        "avg_response_time": metric["total_response_time"] / metric["total"] if metric["total"] > 0 else 0.0
                    }
            
            # Get performance metrics
            hit_ratio_key = f"hit_ratio_{tenant_id}"
            if hit_ratio_key in self.custom_metrics:
                tenant_metrics["performance"]["hit_ratio"] = self.custom_metrics[hit_ratio_key]["current"]
            
            memory_key = f"memory_usage_{tenant_id}"
            if memory_key in self.custom_metrics:
                tenant_metrics["performance"]["memory_mb"] = self.custom_metrics[memory_key]["mb"]
            
            # Get quota metrics
            for key, metric in self.custom_metrics.items():
                if key.startswith(f"quota_{tenant_id}_"):
                    resource_type = key.split("_")[2]
                    tenant_metrics["quota"][resource_type] = metric["usage_percent"]
            
            return tenant_metrics
            
        except Exception as e:
            logger.error(f"Error getting metrics for tenant {tenant_id}", error=str(e))
            return {"error": str(e)}
    
    async def clear_metrics(self, tenant_id: str = None):
        """Clear metrics for a specific tenant or all metrics."""
        try:
            if tenant_id:
                # Clear metrics for specific tenant
                keys_to_remove = []
                for key in self.custom_metrics.keys():
                    if tenant_id in key:
                        keys_to_remove.append(key)
                
                for key in keys_to_remove:
                    del self.custom_metrics[key]
                
                logger.info(f"Cleared metrics for tenant {tenant_id}")
            else:
                # Clear all metrics
                self.custom_metrics.clear()
                self.metrics_history.clear()
                logger.info("Cleared all metrics")
                
        except Exception as e:
            logger.error("Error clearing metrics", error=str(e))
    
    async def export_metrics(self, format: str = "json") -> str:
        """Export metrics in specified format."""
        try:
            if format == "json":
                import json
                return json.dumps(self.custom_metrics, indent=2)
            elif format == "prometheus":
                return self.get_prometheus_metrics()
            else:
                raise ValueError(f"Unsupported format: {format}")
                
        except Exception as e:
            logger.error("Error exporting metrics", error=str(e))
            return ""
    
    async def get_metrics_endpoint_data(self) -> Dict[str, Any]:
        """Get data for metrics endpoint."""
        try:
            return {
                "content_type": CONTENT_TYPE_LATEST,
                "metrics": self.get_prometheus_metrics(),
                "summary": await self.get_metrics_summary(),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error("Error getting metrics endpoint data", error=str(e))
            return {"error": str(e)} 