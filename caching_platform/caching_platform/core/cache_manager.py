"""Multi-tenant cache manager for the caching platform."""

import asyncio
import json
import hashlib
import time
from typing import Dict, Any, Optional, List, Tuple, Union
from datetime import datetime, timedelta
import redis.asyncio as redis
from redis.asyncio import Redis, ConnectionPool
import structlog

from ..config.schemas import Tenant, CacheMetrics, CacheOperation as CacheOp
from ..config.settings import get_settings

logger = structlog.get_logger(__name__)


class MultiTenantCacheManager:
    """Multi-tenant cache manager with isolation and quota enforcement."""
    
    def __init__(self, redis_config=None):
        self.settings = get_settings()
        self.redis_config = redis_config or self.settings.redis
        self.redis_pool: Optional[ConnectionPool] = None
        self.redis_client: Optional[Redis] = None
        
        # Tenant management
        self.tenants: Dict[str, Tenant] = {}
        self.tenant_metrics: Dict[str, CacheMetrics] = {}
        self.tenant_connections: Dict[str, int] = {}
        
        # Performance tracking
        self.operation_history: List[CacheOp] = []
        self.metrics_history: List[CacheMetrics] = []
        
        # Rate limiting
        self.rate_limiters: Dict[str, Dict[str, float]] = {}
        
        # Statistics
        self.total_operations = 0
        self.total_hits = 0
        self.total_misses = 0
        self.start_time = datetime.utcnow()
    
    async def initialize(self) -> bool:
        """Initialize the cache manager."""
        try:
            logger.info("Initializing multi-tenant cache manager")
            
            # Create Redis connection pool
            self.redis_pool = ConnectionPool.from_url(
                f"redis://{self.redis_config.host}:{self.redis_config.port}",
                password=self.redis_config.password,
                db=self.redis_config.db,
                max_connections=self.redis_config.max_connections,
                retry_on_timeout=self.redis_config.retry_on_timeout,
                health_check_interval=self.redis_config.health_check_interval
            )
            
            # Create Redis client
            self.redis_client = Redis(connection_pool=self.redis_pool)
            
            # Test connection
            await self.redis_client.ping()
            
            # Load existing tenants
            await self._load_tenants()
            
            # Initialize metrics collection
            asyncio.create_task(self._metrics_collector())
            
            logger.info("Cache manager initialized successfully")
            return True
            
        except Exception as e:
            logger.error("Failed to initialize cache manager", error=str(e))
            return False
    
    async def shutdown(self):
        """Shutdown the cache manager."""
        logger.info("Shutting down cache manager")
        
        if self.redis_client:
            await self.redis_client.close()
        
        if self.redis_pool:
            await self.redis_pool.disconnect()
        
        logger.info("Cache manager shutdown complete")
    
    async def _load_tenants(self):
        """Load existing tenants from Redis."""
        try:
            tenant_keys = await self.redis_client.keys("tenant:*")
            for key in tenant_keys:
                tenant_data = await self.redis_client.get(key)
                if tenant_data:
                    tenant_dict = json.loads(tenant_data)
                    tenant = Tenant(**tenant_dict)
                    self.tenants[tenant.id] = tenant
                    self.tenant_metrics[tenant.id] = CacheMetrics()
                    self.tenant_connections[tenant.id] = 0
            
            logger.info(f"Loaded {len(self.tenants)} tenants")
            
        except Exception as e:
            logger.error("Failed to load tenants", error=str(e))
    
    async def create_tenant(self, tenant_data: Dict[str, Any]) -> Optional[Tenant]:
        """Create a new tenant."""
        try:
            tenant = Tenant(**tenant_data)
            
            # Validate tenant
            if tenant.id in self.tenants:
                raise ValueError(f"Tenant {tenant.id} already exists")
            
            # Store tenant in Redis
            tenant_key = f"tenant:{tenant.id}"
            await self.redis_client.set(tenant_key, tenant.json())
            
            # Add to local cache
            self.tenants[tenant.id] = tenant
            self.tenant_metrics[tenant.id] = CacheMetrics()
            self.tenant_connections[tenant.id] = 0
            
            logger.info(f"Created tenant {tenant.id}")
            return tenant
            
        except Exception as e:
            logger.error(f"Failed to create tenant {tenant_data.get('id')}", error=str(e))
            return None
    
    async def delete_tenant(self, tenant_id: str) -> bool:
        """Delete a tenant and all its data."""
        try:
            if tenant_id not in self.tenants:
                return False
            
            # Delete tenant data
            tenant_key = f"tenant:{tenant_id}"
            tenant_namespace = f"cache:{tenant_id}:*"
            
            # Get all keys for this tenant
            keys = await self.redis_client.keys(tenant_namespace)
            if keys:
                await self.redis_client.delete(*keys)
            
            # Delete tenant record
            await self.redis_client.delete(tenant_key)
            
            # Remove from local cache
            del self.tenants[tenant_id]
            del self.tenant_metrics[tenant_id]
            del self.tenant_connections[tenant_id]
            
            logger.info(f"Deleted tenant {tenant_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete tenant {tenant_id}", error=str(e))
            return False
    
    async def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        """Get tenant information."""
        return self.tenants.get(tenant_id)
    
    async def list_tenants(self) -> List[Tenant]:
        """List all tenants."""
        return list(self.tenants.values())
    
    async def _check_tenant_quota(self, tenant_id: str, operation: str) -> bool:
        """Check if tenant has quota for operation."""
        if tenant_id not in self.tenants:
            return False
        
        tenant = self.tenants[tenant_id]
        metrics = self.tenant_metrics[tenant_id]
        
        # Check memory quota
        if metrics.memory_used_mb > tenant.memory_limit_mb:
            logger.warning(f"Tenant {tenant_id} exceeded memory quota")
            return False
        
        # Check rate limiting
        current_time = time.time()
        if tenant_id not in self.rate_limiters:
            self.rate_limiters[tenant_id] = {}
        
        rate_key = f"rate:{operation}"
        last_request = self.rate_limiters[tenant_id].get(rate_key, 0)
        
        if current_time - last_request < (1.0 / tenant.requests_per_second):
            logger.warning(f"Tenant {tenant_id} rate limit exceeded for {operation}")
            return False
        
        self.rate_limiters[tenant_id][rate_key] = current_time
        return True
    
    async def _get_cache_key(self, tenant_id: str, key: str) -> str:
        """Get namespaced cache key for tenant."""
        return f"cache:{tenant_id}:{key}"
    
    async def get(self, tenant_id: str, key: str, default: Any = None) -> Any:
        """Get value from cache for tenant."""
        start_time = time.time()
        success = False
        
        try:
            # Check tenant quota
            if not await self._check_tenant_quota(tenant_id, "get"):
                return default
            
            cache_key = await self._get_cache_key(tenant_id, key)
            value = await self.redis_client.get(cache_key)
            
            if value is not None:
                # Cache hit
                self.total_hits += 1
                self.tenant_metrics[tenant_id].cache_hits += 1
                success = True
                result = json.loads(value)
            else:
                # Cache miss
                self.total_misses += 1
                self.tenant_metrics[tenant_id].cache_misses += 1
                result = default
            
            # Update metrics
            response_time = (time.time() - start_time) * 1000
            await self._update_operation_metrics(tenant_id, "get", response_time, success)
            
            return result
            
        except Exception as e:
            logger.error(f"Cache get error for tenant {tenant_id}, key {key}", error=str(e))
            await self._update_operation_metrics(tenant_id, "get", 0, False)
            return default
    
    async def set(self, tenant_id: str, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache for tenant."""
        start_time = time.time()
        success = False
        
        try:
            # Check tenant quota
            if not await self._check_tenant_quota(tenant_id, "set"):
                return False
            
            cache_key = await self._get_cache_key(tenant_id, key)
            serialized_value = json.dumps(value)
            
            # Check memory usage before setting
            value_size = len(serialized_value.encode('utf-8')) / (1024 * 1024)  # MB
            current_memory = self.tenant_metrics[tenant_id].memory_used_mb
            
            if current_memory + value_size > self.tenants[tenant_id].memory_limit_mb:
                logger.warning(f"Tenant {tenant_id} would exceed memory quota")
                return False
            
            # Set value in Redis
            if ttl:
                await self.redis_client.setex(cache_key, ttl, serialized_value)
            else:
                await self.redis_client.set(cache_key, serialized_value)
            
            # Update memory usage
            self.tenant_metrics[tenant_id].memory_used_mb += value_size
            success = True
            
            # Update metrics
            response_time = (time.time() - start_time) * 1000
            await self._update_operation_metrics(tenant_id, "set", response_time, success)
            
            return True
            
        except Exception as e:
            logger.error(f"Cache set error for tenant {tenant_id}, key {key}", error=str(e))
            await self._update_operation_metrics(tenant_id, "set", 0, False)
            return False
    
    async def delete(self, tenant_id: str, key: str) -> bool:
        """Delete value from cache for tenant."""
        start_time = time.time()
        success = False
        
        try:
            # Check tenant quota
            if not await self._check_tenant_quota(tenant_id, "delete"):
                return False
            
            cache_key = await self._get_cache_key(tenant_id, key)
            
            # Get value size before deletion for memory tracking
            value = await self.redis_client.get(cache_key)
            if value:
                value_size = len(value) / (1024 * 1024)  # MB
                self.tenant_metrics[tenant_id].memory_used_mb -= value_size
            
            # Delete from Redis
            result = await self.redis_client.delete(cache_key)
            success = result > 0
            
            # Update metrics
            response_time = (time.time() - start_time) * 1000
            await self._update_operation_metrics(tenant_id, "delete", response_time, success)
            
            return success
            
        except Exception as e:
            logger.error(f"Cache delete error for tenant {tenant_id}, key {key}", error=str(e))
            await self._update_operation_metrics(tenant_id, "delete", 0, False)
            return False
    
    async def exists(self, tenant_id: str, key: str) -> bool:
        """Check if key exists for tenant."""
        try:
            cache_key = await self._get_cache_key(tenant_id, key)
            return await self.redis_client.exists(cache_key) > 0
        except Exception as e:
            logger.error(f"Cache exists error for tenant {tenant_id}, key {key}", error=str(e))
            return False
    
    async def expire(self, tenant_id: str, key: str, ttl: int) -> bool:
        """Set expiration for key."""
        try:
            cache_key = await self._get_cache_key(tenant_id, key)
            return await self.redis_client.expire(cache_key, ttl)
        except Exception as e:
            logger.error(f"Cache expire error for tenant {tenant_id}, key {key}", error=str(e))
            return False
    
    async def ttl(self, tenant_id: str, key: str) -> int:
        """Get TTL for key."""
        try:
            cache_key = await self._get_cache_key(tenant_id, key)
            return await self.redis_client.ttl(cache_key)
        except Exception as e:
            logger.error(f"Cache TTL error for tenant {tenant_id}, key {key}", error=str(e))
            return -1
    
    async def incr(self, tenant_id: str, key: str, amount: int = 1) -> Optional[int]:
        """Increment value for tenant."""
        start_time = time.time()
        success = False
        
        try:
            # Check tenant quota
            if not await self._check_tenant_quota(tenant_id, "incr"):
                return None
            
            cache_key = await self._get_cache_key(tenant_id, key)
            result = await self.redis_client.incrby(cache_key, amount)
            success = True
            
            # Update metrics
            response_time = (time.time() - start_time) * 1000
            await self._update_operation_metrics(tenant_id, "incr", response_time, success)
            
            return result
            
        except Exception as e:
            logger.error(f"Cache incr error for tenant {tenant_id}, key {key}", error=str(e))
            await self._update_operation_metrics(tenant_id, "incr", 0, False)
            return None
    
    async def decr(self, tenant_id: str, key: str, amount: int = 1) -> Optional[int]:
        """Decrement value for tenant."""
        start_time = time.time()
        success = False
        
        try:
            # Check tenant quota
            if not await self._check_tenant_quota(tenant_id, "decr"):
                return None
            
            cache_key = await self._get_cache_key(tenant_id, key)
            result = await self.redis_client.decrby(cache_key, amount)
            success = True
            
            # Update metrics
            response_time = (time.time() - start_time) * 1000
            await self._update_operation_metrics(tenant_id, "decr", response_time, success)
            
            return result
            
        except Exception as e:
            logger.error(f"Cache decr error for tenant {tenant_id}, key {key}", error=str(e))
            await self._update_operation_metrics(tenant_id, "decr", 0, False)
            return None
    
    async def mget(self, tenant_id: str, keys: List[str]) -> List[Any]:
        """Get multiple values for tenant."""
        start_time = time.time()
        success = False
        
        try:
            # Check tenant quota
            if not await self._check_tenant_quota(tenant_id, "mget"):
                return [None] * len(keys)
            
            cache_keys = [await self._get_cache_key(tenant_id, key) for key in keys]
            values = await self.redis_client.mget(*cache_keys)
            
            # Deserialize values
            result = []
            for value in values:
                if value is not None:
                    result.append(json.loads(value))
                    self.total_hits += 1
                    self.tenant_metrics[tenant_id].cache_hits += 1
                else:
                    result.append(None)
                    self.total_misses += 1
                    self.tenant_metrics[tenant_id].cache_misses += 1
            
            success = True
            
            # Update metrics
            response_time = (time.time() - start_time) * 1000
            await self._update_operation_metrics(tenant_id, "mget", response_time, success)
            
            return result
            
        except Exception as e:
            logger.error(f"Cache mget error for tenant {tenant_id}", error=str(e))
            await self._update_operation_metrics(tenant_id, "mget", 0, False)
            return [None] * len(keys)
    
    async def mset(self, tenant_id: str, key_values: Dict[str, Any]) -> bool:
        """Set multiple values for tenant."""
        start_time = time.time()
        success = False
        
        try:
            # Check tenant quota
            if not await self._check_tenant_quota(tenant_id, "mset"):
                return False
            
            # Prepare cache keys and values
            cache_data = {}
            total_size = 0
            
            for key, value in key_values.items():
                cache_key = await self._get_cache_key(tenant_id, key)
                serialized_value = json.dumps(value)
                cache_data[cache_key] = serialized_value
                total_size += len(serialized_value.encode('utf-8')) / (1024 * 1024)  # MB
            
            # Check memory quota
            current_memory = self.tenant_metrics[tenant_id].memory_used_mb
            if current_memory + total_size > self.tenants[tenant_id].memory_limit_mb:
                logger.warning(f"Tenant {tenant_id} would exceed memory quota")
                return False
            
            # Set values in Redis
            await self.redis_client.mset(cache_data)
            
            # Update memory usage
            self.tenant_metrics[tenant_id].memory_used_mb += total_size
            success = True
            
            # Update metrics
            response_time = (time.time() - start_time) * 1000
            await self._update_operation_metrics(tenant_id, "mset", response_time, success)
            
            return True
            
        except Exception as e:
            logger.error(f"Cache mset error for tenant {tenant_id}", error=str(e))
            await self._update_operation_metrics(tenant_id, "mset", 0, False)
            return False
    
    async def _update_operation_metrics(self, tenant_id: str, operation: str, response_time: float, success: bool):
        """Update operation metrics for tenant."""
        if tenant_id not in self.tenant_metrics:
            return
        
        metrics = self.tenant_metrics[tenant_id]
        
        # Update basic metrics
        metrics.total_requests += 1
        if success:
            metrics.successful_requests += 1
        else:
            metrics.failed_requests += 1
        
        # Update response time metrics
        if response_time > 0:
            metrics.average_response_time_ms = (
                (metrics.average_response_time_ms * (metrics.total_requests - 1) + response_time) / 
                metrics.total_requests
            )
        
        # Update hit ratio
        total_operations = metrics.cache_hits + metrics.cache_misses
        if total_operations > 0:
            metrics.hit_ratio = (metrics.cache_hits / total_operations) * 100
        
        # Update error rate
        if metrics.total_requests > 0:
            metrics.error_rate = (metrics.failed_requests / metrics.total_requests) * 100
        
        # Update timestamp
        metrics.timestamp = datetime.utcnow()
    
    async def _metrics_collector(self):
        """Background task to collect and store metrics."""
        while True:
            try:
                # Collect system-wide metrics
                total_operations = sum(m.total_requests for m in self.tenant_metrics.values())
                total_hits = sum(m.cache_hits for m in self.tenant_metrics.values())
                total_misses = sum(m.cache_misses for m in self.tenant_metrics.values())
                
                # Calculate overall hit ratio
                if total_operations > 0:
                    overall_hit_ratio = (total_hits / total_operations) * 100
                else:
                    overall_hit_ratio = 0.0
                
                # Store metrics in Redis
                metrics_data = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "total_operations": total_operations,
                    "total_hits": total_hits,
                    "total_misses": total_misses,
                    "overall_hit_ratio": overall_hit_ratio,
                    "active_tenants": len(self.tenants),
                    "uptime_seconds": (datetime.utcnow() - self.start_time).total_seconds()
                }
                
                await self.redis_client.setex(
                    "metrics:system",
                    self.settings.monitoring.metrics_interval * 2,
                    json.dumps(metrics_data)
                )
                
                # Store metrics history (keep last 100 entries)
                self.metrics_history.append(metrics_data)
                if len(self.metrics_history) > 100:
                    self.metrics_history.pop(0)
                
                await asyncio.sleep(self.settings.monitoring.metrics_interval)
                
            except Exception as e:
                logger.error("Metrics collector error", error=str(e))
                await asyncio.sleep(10)
    
    async def get_tenant_metrics(self, tenant_id: str) -> Optional[CacheMetrics]:
        """Get metrics for a specific tenant."""
        return self.tenant_metrics.get(tenant_id)
    
    async def get_all_metrics(self) -> Dict[str, CacheMetrics]:
        """Get metrics for all tenants."""
        return self.tenant_metrics.copy()
    
    async def get_system_metrics(self) -> Dict[str, Any]:
        """Get system-wide metrics."""
        return {
            "total_operations": self.total_operations,
            "total_hits": self.total_hits,
            "total_misses": self.total_misses,
            "hit_ratio": (self.total_hits / max(1, self.total_operations)) * 100,
            "active_tenants": len(self.tenants),
            "uptime_seconds": (datetime.utcnow() - self.start_time).total_seconds(),
            "memory_usage_mb": sum(m.memory_used_mb for m in self.tenant_metrics.values()),
            "average_response_time_ms": sum(m.average_response_time_ms for m in self.tenant_metrics.values()) / max(1, len(self.tenant_metrics))
        }
    
    async def clear_tenant_data(self, tenant_id: str) -> bool:
        """Clear all data for a tenant."""
        try:
            if tenant_id not in self.tenants:
                return False
            
            # Get all keys for this tenant
            pattern = f"cache:{tenant_id}:*"
            keys = await self.redis_client.keys(pattern)
            
            if keys:
                await self.redis_client.delete(*keys)
            
            # Reset metrics
            self.tenant_metrics[tenant_id] = CacheMetrics()
            
            logger.info(f"Cleared all data for tenant {tenant_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear tenant data for {tenant_id}", error=str(e))
            return False
    
    async def backup_tenant_data(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Create backup of tenant data."""
        try:
            if tenant_id not in self.tenants:
                return None
            
            # Get all keys for this tenant
            pattern = f"cache:{tenant_id}:*"
            keys = await self.redis_client.keys(pattern)
            
            # Get all values
            backup_data = {}
            for key in keys:
                value = await self.redis_client.get(key)
                ttl = await self.redis_client.ttl(key)
                backup_data[key] = {
                    "value": value,
                    "ttl": ttl if ttl > 0 else None
                }
            
            return {
                "tenant_id": tenant_id,
                "timestamp": datetime.utcnow().isoformat(),
                "keys_count": len(keys),
                "data": backup_data
            }
            
        except Exception as e:
            logger.error(f"Failed to backup tenant data for {tenant_id}", error=str(e))
            return None
    
    async def restore_tenant_data(self, tenant_id: str, backup_data: Dict[str, Any]) -> bool:
        """Restore tenant data from backup."""
        try:
            if tenant_id not in self.tenants:
                return False
            
            # Clear existing data
            await self.clear_tenant_data(tenant_id)
            
            # Restore data
            for key, item in backup_data["data"].items():
                if item["ttl"]:
                    await self.redis_client.setex(key, item["ttl"], item["value"])
                else:
                    await self.redis_client.set(key, item["value"])
            
            logger.info(f"Restored data for tenant {tenant_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to restore tenant data for {tenant_id}", error=str(e))
            return False 