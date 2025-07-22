"""Data schemas and validation for the caching platform."""

from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
from enum import Enum
from pydantic import BaseModel, Field, validator, root_validator


class TenantStatus(str, Enum):
    """Tenant status enumeration."""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    PENDING = "pending"
    DELETED = "deleted"


class NodeStatus(str, Enum):
    """Redis node status enumeration."""
    ONLINE = "online"
    OFFLINE = "offline"
    FAILING = "failing"
    MAINTENANCE = "maintenance"


class AgentStatus(str, Enum):
    """Agent status enumeration."""
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"
    STARTING = "starting"


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class CacheOperation(str, Enum):
    """Cache operation types."""
    GET = "get"
    SET = "set"
    DELETE = "delete"
    EXISTS = "exists"
    INCR = "incr"
    DECR = "decr"
    EXPIRE = "expire"
    TTL = "ttl"


class Tenant(BaseModel):
    """Tenant model for multi-tenancy."""
    
    id: str = Field(..., description="Unique tenant identifier")
    name: str = Field(..., description="Tenant name")
    status: TenantStatus = Field(default=TenantStatus.ACTIVE, description="Tenant status")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    
    # Resource quotas
    memory_limit_mb: int = Field(default=512, description="Memory limit in MB")
    requests_per_second: int = Field(default=100, description="Request rate limit")
    max_connections: int = Field(default=50, description="Maximum connections")
    
    # Usage tracking
    current_memory_mb: float = Field(default=0.0, description="Current memory usage")
    current_requests_per_second: float = Field(default=0.0, description="Current request rate")
    current_connections: int = Field(default=0, description="Current connections")
    
    # Configuration
    namespace: str = Field(..., description="Tenant namespace")
    api_key: Optional[str] = Field(None, description="API key for authentication")
    settings: Dict[str, Any] = Field(default_factory=dict, description="Tenant-specific settings")
    
    @validator("id")
    def validate_id(cls, v):
        if not v or len(v) < 3:
            raise ValueError("Tenant ID must be at least 3 characters")
        return v.lower()
    
    @validator("name")
    def validate_name(cls, v):
        if not v or len(v) < 2:
            raise ValueError("Tenant name must be at least 2 characters")
        return v
    
    @validator("memory_limit_mb")
    def validate_memory_limit(cls, v):
        if v < 64 or v > 8192:
            raise ValueError("Memory limit must be between 64 and 8192 MB")
        return v
    
    @validator("requests_per_second")
    def validate_requests_per_second(cls, v):
        if v < 1 or v > 10000:
            raise ValueError("Requests per second must be between 1 and 10000")
        return v


class RedisNode(BaseModel):
    """Redis node model."""
    
    id: str = Field(..., description="Node identifier")
    host: str = Field(..., description="Node host")
    port: int = Field(default=6379, description="Node port")
    status: NodeStatus = Field(default=NodeStatus.OFFLINE, description="Node status")
    
    # Node information
    role: str = Field(default="master", description="Node role (master/slave)")
    master_id: Optional[str] = Field(None, description="Master node ID if slave")
    slots: List[int] = Field(default_factory=list, description="Hash slots assigned")
    
    # Performance metrics
    memory_used_mb: float = Field(default=0.0, description="Memory usage in MB")
    memory_max_mb: float = Field(default=1024.0, description="Maximum memory in MB")
    cpu_percent: float = Field(default=0.0, description="CPU usage percentage")
    connected_clients: int = Field(default=0, description="Connected clients")
    total_commands_processed: int = Field(default=0, description="Total commands processed")
    
    # Health information
    last_ping: Optional[datetime] = Field(None, description="Last ping timestamp")
    ping_latency_ms: float = Field(default=0.0, description="Ping latency in milliseconds")
    
    @validator("port")
    def validate_port(cls, v):
        if v < 1 or v > 65535:
            raise ValueError("Port must be between 1 and 65535")
        return v


class ClusterInfo(BaseModel):
    """Redis cluster information."""
    
    cluster_name: str = Field(default="caching-cluster", description="Cluster name")
    cluster_state: str = Field(default="fail", description="Cluster state")
    cluster_slots_assigned: int = Field(default=0, description="Assigned slots")
    cluster_slots_ok: int = Field(default=0, description="OK slots")
    cluster_slots_pfail: int = Field(default=0, description="PFAIL slots")
    cluster_slots_fail: int = Field(default=0, description="FAIL slots")
    cluster_known_nodes: int = Field(default=0, description="Known nodes")
    cluster_size: int = Field(default=0, description="Cluster size")
    cluster_current_epoch: int = Field(default=0, description="Current epoch")
    cluster_my_epoch: int = Field(default=0, description="My epoch")
    cluster_stats_messages_sent: int = Field(default=0, description="Messages sent")
    cluster_stats_messages_received: int = Field(default=0, description="Messages received")
    
    nodes: List[RedisNode] = Field(default_factory=list, description="Cluster nodes")


class CacheMetrics(BaseModel):
    """Cache performance metrics."""
    
    # Basic metrics
    total_requests: int = Field(default=0, description="Total requests")
    successful_requests: int = Field(default=0, description="Successful requests")
    failed_requests: int = Field(default=0, description="Failed requests")
    
    # Hit/miss ratios
    cache_hits: int = Field(default=0, description="Cache hits")
    cache_misses: int = Field(default=0, description="Cache misses")
    hit_ratio: float = Field(default=0.0, description="Hit ratio percentage")
    
    # Performance metrics
    average_response_time_ms: float = Field(default=0.0, description="Average response time")
    p50_response_time_ms: float = Field(default=0.0, description="50th percentile response time")
    p95_response_time_ms: float = Field(default=0.0, description="95th percentile response time")
    p99_response_time_ms: float = Field(default=0.0, description="99th percentile response time")
    
    # Throughput metrics
    requests_per_second: float = Field(default=0.0, description="Requests per second")
    operations_per_second: float = Field(default=0.0, description="Operations per second")
    
    # Memory metrics
    memory_used_mb: float = Field(default=0.0, description="Memory used in MB")
    memory_available_mb: float = Field(default=0.0, description="Memory available in MB")
    memory_usage_percent: float = Field(default=0.0, description="Memory usage percentage")
    
    # Error metrics
    error_rate: float = Field(default=0.0, description="Error rate percentage")
    timeout_errors: int = Field(default=0, description="Timeout errors")
    connection_errors: int = Field(default=0, description="Connection errors")
    
    # Timestamp
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Metrics timestamp")
    
    @validator("hit_ratio")
    def validate_hit_ratio(cls, v):
        return max(0.0, min(100.0, v))
    
    @validator("error_rate")
    def validate_error_rate(cls, v):
        return max(0.0, min(100.0, v))


class AgentInfo(BaseModel):
    """Autonomous agent information."""
    
    id: str = Field(..., description="Agent identifier")
    name: str = Field(..., description="Agent name")
    type: str = Field(..., description="Agent type")
    status: AgentStatus = Field(default=AgentStatus.STOPPED, description="Agent status")
    
    # Agent metrics
    uptime_seconds: int = Field(default=0, description="Agent uptime in seconds")
    total_decisions: int = Field(default=0, description="Total decisions made")
    successful_decisions: int = Field(default=0, description="Successful decisions")
    failed_decisions: int = Field(default=0, description="Failed decisions")
    
    # Performance metrics
    cpu_usage_percent: float = Field(default=0.0, description="CPU usage")
    memory_usage_mb: float = Field(default=0.0, description="Memory usage")
    
    # Configuration
    config: Dict[str, Any] = Field(default_factory=dict, description="Agent configuration")
    last_activity: Optional[datetime] = Field(None, description="Last activity timestamp")
    
    # Error information
    last_error: Optional[str] = Field(None, description="Last error message")
    error_count: int = Field(default=0, description="Error count")


class Alert(BaseModel):
    """Alert model for monitoring."""
    
    id: str = Field(..., description="Alert identifier")
    title: str = Field(..., description="Alert title")
    message: str = Field(..., description="Alert message")
    severity: AlertSeverity = Field(..., description="Alert severity")
    
    # Alert metadata
    source: str = Field(..., description="Alert source")
    category: str = Field(..., description="Alert category")
    tenant_id: Optional[str] = Field(None, description="Related tenant ID")
    node_id: Optional[str] = Field(None, description="Related node ID")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    acknowledged_at: Optional[datetime] = Field(None, description="Acknowledgment timestamp")
    resolved_at: Optional[datetime] = Field(None, description="Resolution timestamp")
    
    # Status
    acknowledged: bool = Field(default=False, description="Alert acknowledged")
    resolved: bool = Field(default=False, description="Alert resolved")
    
    # Additional data
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class CacheOperation(BaseModel):
    """Cache operation model."""
    
    operation: str = Field(..., description="Operation type")
    key: str = Field(..., description="Cache key")
    value: Optional[Any] = Field(None, description="Cache value")
    tenant_id: str = Field(..., description="Tenant ID")
    
    # Operation metadata
    ttl: Optional[int] = Field(None, description="Time to live in seconds")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Operation timestamp")
    
    # Performance tracking
    response_time_ms: Optional[float] = Field(None, description="Response time in milliseconds")
    success: bool = Field(default=True, description="Operation success")
    error_message: Optional[str] = Field(None, description="Error message if failed")


class BackupInfo(BaseModel):
    """Backup information model."""
    
    id: str = Field(..., description="Backup identifier")
    filename: str = Field(..., description="Backup filename")
    size_bytes: int = Field(default=0, description="Backup size in bytes")
    
    # Backup metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    
    # Backup configuration
    include_data: bool = Field(default=True, description="Include cache data")
    include_config: bool = Field(default=True, description="Include configuration")
    compression: bool = Field(default=True, description="Use compression")
    
    # Status
    status: str = Field(default="pending", description="Backup status")
    progress_percent: float = Field(default=0.0, description="Progress percentage")
    
    # Validation
    checksum: Optional[str] = Field(None, description="Backup checksum")
    verified: bool = Field(default=False, description="Backup verified")


class ScalingDecision(BaseModel):
    """Auto-scaling decision model."""
    
    id: str = Field(..., description="Decision identifier")
    agent_id: str = Field(..., description="Agent that made the decision")
    decision_type: str = Field(..., description="Type of decision (scale_up/scale_down)")
    
    # Decision parameters
    current_nodes: int = Field(..., description="Current number of nodes")
    target_nodes: int = Field(..., description="Target number of nodes")
    reason: str = Field(..., description="Reason for decision")
    
    # Metrics that triggered the decision
    cpu_usage: float = Field(..., description="CPU usage percentage")
    memory_usage: float = Field(..., description="Memory usage percentage")
    request_rate: float = Field(..., description="Request rate")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Decision timestamp")
    executed_at: Optional[datetime] = Field(None, description="Execution timestamp")
    
    # Status
    executed: bool = Field(default=False, description="Decision executed")
    successful: Optional[bool] = Field(None, description="Execution success")
    
    # Additional data
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class HealthCheck(BaseModel):
    """Health check model."""
    
    component: str = Field(..., description="Component name")
    status: str = Field(..., description="Health status")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Check timestamp")
    
    # Health details
    details: Dict[str, Any] = Field(default_factory=dict, description="Health details")
    error_message: Optional[str] = Field(None, description="Error message if unhealthy")
    
    # Performance metrics
    response_time_ms: Optional[float] = Field(None, description="Response time")
    last_check_duration_ms: Optional[float] = Field(None, description="Check duration")


class SystemStatus(BaseModel):
    """Overall system status model."""
    
    # System information
    platform_version: str = Field(..., description="Platform version")
    uptime_seconds: int = Field(..., description="System uptime")
    environment: str = Field(..., description="Environment")
    
    # Component status
    redis_cluster: HealthCheck = Field(..., description="Redis cluster health")
    agents: List[HealthCheck] = Field(default_factory=list, description="Agent health checks")
    monitoring: HealthCheck = Field(..., description="Monitoring system health")
    
    # Performance overview
    total_tenants: int = Field(default=0, description="Total tenants")
    active_tenants: int = Field(default=0, description="Active tenants")
    total_nodes: int = Field(default=0, description="Total nodes")
    online_nodes: int = Field(default=0, description="Online nodes")
    
    # Metrics summary
    overall_cpu_usage: float = Field(default=0.0, description="Overall CPU usage")
    overall_memory_usage: float = Field(default=0.0, description="Overall memory usage")
    total_requests_per_second: float = Field(default=0.0, description="Total requests per second")
    average_response_time_ms: float = Field(default=0.0, description="Average response time")
    
    # Alerts
    active_alerts: int = Field(default=0, description="Active alerts")
    critical_alerts: int = Field(default=0, description="Critical alerts")
    
    # Timestamp
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Status timestamp") 