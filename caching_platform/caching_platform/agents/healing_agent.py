"""Autonomous healing agent for system issue detection and resolution."""

import asyncio
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import numpy as np
from enum import Enum
import structlog

from ..config.settings import get_settings, Settings
from ..config.schemas import AgentInfo, Alert, AlertSeverity, HealthCheck
from ..core.cache_manager import MultiTenantCacheManager
from ..core.health_monitor import HealthMonitor

logger = structlog.get_logger(__name__)

class IssueType(str, Enum):
    """Types of system issues."""
    HIGH_CPU = "high_cpu"
    HIGH_MEMORY = "high_memory"
    REDIS_CONNECTION = "redis_connection"
    SLOW_RESPONSE = "slow_response"
    LOW_HIT_RATIO = "low_hit_ratio"
    NODE_FAILURE = "node_failure"
    NETWORK_ISSUE = "network_issue"
    QUOTA_EXCEEDED = "quota_exceeded"

class ResolutionAction(str, Enum):
    """Types of resolution actions."""
    RESTART_SERVICE = "restart_service"
    SCALE_UP = "scale_up"
    SCALE_DOWN = "scale_down"
    CLEAR_CACHE = "clear_cache"
    ADJUST_QUOTA = "adjust_quota"
    SWITCH_NODE = "switch_node"
    OPTIMIZE_CONFIG = "optimize_config"
    SEND_ALERT = "send_alert"

@dataclass
class SystemIssue:
    """System issue detection result."""
    issue_type: IssueType
    severity: AlertSeverity
    description: str
    affected_components: List[str]
    metrics: Dict[str, Any]
    timestamp: float
    auto_resolvable: bool

@dataclass
class ResolutionPlan:
    """Resolution plan for a system issue."""
    issue: SystemIssue
    actions: List[ResolutionAction]
    expected_duration: int
    success_probability: float
    reasoning: str

class HealingAgent:
    """Autonomous agent for system issue detection and resolution."""
    
    def __init__(self, cache_manager: MultiTenantCacheManager, health_monitor: HealthMonitor, settings: Settings):
        self.cache_manager = cache_manager
        self.health_monitor = health_monitor
        self.settings = settings
        
        # Healing state
        self.is_running = False
        self.healing_interval = 30  # 30 seconds
        self.last_healing_cycle = 0
        
        # Issue tracking
        self.active_issues: Dict[str, SystemIssue] = {}
        self.resolved_issues: List[SystemIssue] = []
        self.resolution_history: List[Dict[str, Any]] = []
        
        # Health thresholds
        self.thresholds = {
            'cpu_critical': 95.0,
            'cpu_warning': 85.0,
            'memory_critical': 95.0,
            'memory_warning': 85.0,
            'response_time_critical': 1000,  # ms
            'response_time_warning': 500,    # ms
            'hit_ratio_critical': 0.5,
            'hit_ratio_warning': 0.7,
            'error_rate_critical': 0.1,
            'error_rate_warning': 0.05
        }
        
        # Resolution strategies
        self.resolution_strategies = self._initialize_resolution_strategies()
        
        logger.info("HealingAgent initialized")
    
    async def initialize(self) -> bool:
        """Initialize the healing agent."""
        try:
            # Load historical issue data
            await self._load_issue_history()
            
            # Start health monitoring
            asyncio.create_task(self._health_monitor_loop())
            
            logger.info("HealingAgent initialized successfully")
            return True
        except Exception as e:
            logger.error("Failed to initialize HealingAgent", error=str(e))
            return False
    
    async def start(self) -> bool:
        """Start the healing agent."""
        if self.is_running:
            logger.warning("HealingAgent is already running")
            return True
        
        self.is_running = True
        asyncio.create_task(self._healing_loop())
        logger.info("HealingAgent started")
        return True
    
    async def stop(self) -> bool:
        """Stop the healing agent."""
        self.is_running = False
        logger.info("HealingAgent stopped")
        return True
    
    async def _healing_loop(self):
        """Main healing loop."""
        while self.is_running:
            try:
                await self._run_healing_cycle()
                await asyncio.sleep(self.healing_interval)
            except Exception as e:
                logger.error("Error in healing loop", error=str(e))
                await asyncio.sleep(10)
    
    async def _run_healing_cycle(self):
        """Run a complete healing cycle."""
        current_time = time.time()
        
        # Detect new issues
        new_issues = await self._detect_issues()
        
        # Update active issues
        for issue in new_issues:
            issue_id = f"{issue.issue_type}_{issue.affected_components[0]}_{int(issue.timestamp)}"
            self.active_issues[issue_id] = issue
            
            # Create alert for new issue
            await self._create_alert(issue)
        
        # Attempt to resolve active issues
        await self._resolve_active_issues()
        
        # Clean up resolved issues
        await self._cleanup_resolved_issues()
        
        self.last_healing_cycle = current_time
    
    async def _detect_issues(self) -> List[SystemIssue]:
        """Detect system issues based on current metrics."""
        issues = []
        
        # Get current system health
        system_health = self.health_monitor.system_health
        
        # Check CPU usage
        cpu_health = system_health.get('cpu')
        if cpu_health:
            cpu_usage = cpu_health.current_value
            if cpu_usage > self.thresholds['cpu_critical']:
                issues.append(SystemIssue(
                    issue_type=IssueType.HIGH_CPU,
                    severity=AlertSeverity.CRITICAL,
                    description=f"Critical CPU usage: {cpu_usage:.1f}%",
                    affected_components=['system'],
                    metrics={'cpu_usage': cpu_usage},
                    timestamp=time.time(),
                    auto_resolvable=True
                ))
            elif cpu_usage > self.thresholds['cpu_warning']:
                issues.append(SystemIssue(
                    issue_type=IssueType.HIGH_CPU,
                    severity=AlertSeverity.WARNING,
                    description=f"High CPU usage: {cpu_usage:.1f}%",
                    affected_components=['system'],
                    metrics={'cpu_usage': cpu_usage},
                    timestamp=time.time(),
                    auto_resolvable=True
                ))
        
        # Check memory usage
        memory_health = system_health.get('memory')
        if memory_health:
            memory_usage = memory_health.current_value
            if memory_usage > self.thresholds['memory_critical']:
                issues.append(SystemIssue(
                    issue_type=IssueType.HIGH_MEMORY,
                    severity=AlertSeverity.CRITICAL,
                    description=f"Critical memory usage: {memory_usage:.1f}%",
                    affected_components=['system'],
                    metrics={'memory_usage': memory_usage},
                    timestamp=time.time(),
                    auto_resolvable=True
                ))
            elif memory_usage > self.thresholds['memory_warning']:
                issues.append(SystemIssue(
                    issue_type=IssueType.HIGH_MEMORY,
                    severity=AlertSeverity.WARNING,
                    description=f"High memory usage: {memory_usage:.1f}%",
                    affected_components=['system'],
                    metrics={'memory_usage': memory_usage},
                    timestamp=time.time(),
                    auto_resolvable=True
                ))
        
        # Check Redis connection
        redis_health = system_health.get('redis')
        if redis_health and not redis_health.is_healthy:
            issues.append(SystemIssue(
                issue_type=IssueType.REDIS_CONNECTION,
                severity=AlertSeverity.CRITICAL,
                description="Redis connection failure",
                affected_components=['redis'],
                metrics={'redis_status': 'disconnected'},
                timestamp=time.time(),
                auto_resolvable=True
            ))
        
        # Check tenant-specific issues
        tenant_issues = await self._detect_tenant_issues()
        issues.extend(tenant_issues)
        
        return issues
    
    async def _detect_tenant_issues(self) -> List[SystemIssue]:
        """Detect issues specific to individual tenants."""
        issues = []
        
        for tenant_id, tenant_metrics in self.cache_manager.tenant_metrics.items():
            tenant = self.cache_manager.tenants.get(tenant_id)
            if not tenant:
                continue
            
            # Check response time
            if tenant_metrics.avg_response_time > self.thresholds['response_time_critical']:
                issues.append(SystemIssue(
                    issue_type=IssueType.SLOW_RESPONSE,
                    severity=AlertSeverity.CRITICAL,
                    description=f"Critical response time for tenant {tenant_id}: {tenant_metrics.avg_response_time:.1f}ms",
                    affected_components=[tenant_id],
                    metrics={'response_time': tenant_metrics.avg_response_time},
                    timestamp=time.time(),
                    auto_resolvable=True
                ))
            elif tenant_metrics.avg_response_time > self.thresholds['response_time_warning']:
                issues.append(SystemIssue(
                    issue_type=IssueType.SLOW_RESPONSE,
                    severity=AlertSeverity.WARNING,
                    description=f"Slow response time for tenant {tenant_id}: {tenant_metrics.avg_response_time:.1f}ms",
                    affected_components=[tenant_id],
                    metrics={'response_time': tenant_metrics.avg_response_time},
                    timestamp=time.time(),
                    auto_resolvable=True
                ))
            
            # Check hit ratio
            if tenant_metrics.hit_ratio < self.thresholds['hit_ratio_critical']:
                issues.append(SystemIssue(
                    issue_type=IssueType.LOW_HIT_RATIO,
                    severity=AlertSeverity.WARNING,
                    description=f"Low hit ratio for tenant {tenant_id}: {tenant_metrics.hit_ratio:.2f}",
                    affected_components=[tenant_id],
                    metrics={'hit_ratio': tenant_metrics.hit_ratio},
                    timestamp=time.time(),
                    auto_resolvable=True
                ))
            
            # Check quota exceeded
            if tenant.quota_memory_mb > 0:
                memory_usage_ratio = tenant_metrics.memory_usage_mb / tenant.quota_memory_mb
                if memory_usage_ratio > 0.95:
                    issues.append(SystemIssue(
                        issue_type=IssueType.QUOTA_EXCEEDED,
                        severity=AlertSeverity.WARNING,
                        description=f"Memory quota nearly exceeded for tenant {tenant_id}: {memory_usage_ratio:.1%}",
                        affected_components=[tenant_id],
                        metrics={'memory_usage_ratio': memory_usage_ratio},
                        timestamp=time.time(),
                        auto_resolvable=True
                    ))
        
        return issues
    
    async def _resolve_active_issues(self):
        """Attempt to resolve active issues."""
        for issue_id, issue in list(self.active_issues.items()):
            if not issue.auto_resolvable:
                continue
            
            # Create resolution plan
            resolution_plan = await self._create_resolution_plan(issue)
            
            if resolution_plan and resolution_plan.success_probability > 0.7:
                # Execute resolution
                success = await self._execute_resolution(resolution_plan)
                
                if success:
                    # Mark issue as resolved
                    self.resolved_issues.append(issue)
                    del self.active_issues[issue_id]
                    
                    # Record resolution
                    self.resolution_history.append({
                        'timestamp': time.time(),
                        'issue_id': issue_id,
                        'issue_type': issue.issue_type,
                        'resolution_actions': resolution_plan.actions,
                        'success': True
                    })
                    
                    logger.info("Issue resolved successfully",
                               issue_type=issue.issue_type,
                               actions=resolution_plan.actions)
                else:
                    # Record failed resolution
                    self.resolution_history.append({
                        'timestamp': time.time(),
                        'issue_id': issue_id,
                        'issue_type': issue.issue_type,
                        'resolution_actions': resolution_plan.actions,
                        'success': False
                    })
    
    async def _create_resolution_plan(self, issue: SystemIssue) -> Optional[ResolutionPlan]:
        """Create a resolution plan for an issue."""
        strategy = self.resolution_strategies.get(issue.issue_type)
        if not strategy:
            return None
        
        # Get current system state
        current_metrics = await self._get_current_metrics()
        
        # Apply strategy to create resolution plan
        actions = []
        reasoning = ""
        
        if issue.issue_type == IssueType.HIGH_CPU:
            if current_metrics.get('cpu_usage', 0) > 90:
                actions = [ResolutionAction.SCALE_UP, ResolutionAction.OPTIMIZE_CONFIG]
                reasoning = "High CPU usage requires immediate scaling and configuration optimization"
            else:
                actions = [ResolutionAction.OPTIMIZE_CONFIG]
                reasoning = "Moderate CPU usage can be resolved with configuration optimization"
        
        elif issue.issue_type == IssueType.HIGH_MEMORY:
            actions = [ResolutionAction.CLEAR_CACHE, ResolutionAction.SCALE_UP]
            reasoning = "High memory usage requires cache clearing and potential scaling"
        
        elif issue.issue_type == IssueType.REDIS_CONNECTION:
            actions = [ResolutionAction.RESTART_SERVICE]
            reasoning = "Redis connection failure requires service restart"
        
        elif issue.issue_type == IssueType.SLOW_RESPONSE:
            actions = [ResolutionAction.OPTIMIZE_CONFIG, ResolutionAction.SCALE_UP]
            reasoning = "Slow response time requires configuration optimization and scaling"
        
        elif issue.issue_type == IssueType.LOW_HIT_RATIO:
            actions = [ResolutionAction.OPTIMIZE_CONFIG]
            reasoning = "Low hit ratio requires cache configuration optimization"
        
        elif issue.issue_type == IssueType.QUOTA_EXCEEDED:
            actions = [ResolutionAction.ADJUST_QUOTA]
            reasoning = "Quota exceeded requires quota adjustment"
        
        if not actions:
            return None
        
        return ResolutionPlan(
            issue=issue,
            actions=actions,
            expected_duration=60,  # 1 minute
            success_probability=0.8,
            reasoning=reasoning
        )
    
    async def _execute_resolution(self, resolution_plan: ResolutionPlan) -> bool:
        """Execute a resolution plan."""
        try:
            for action in resolution_plan.actions:
                success = await self._execute_action(action, resolution_plan.issue)
                if not success:
                    logger.warning("Resolution action failed",
                                  action=action,
                                  issue_type=resolution_plan.issue.issue_type)
                    return False
            
            return True
        except Exception as e:
            logger.error("Failed to execute resolution plan",
                        error=str(e),
                        issue_type=resolution_plan.issue.issue_type)
            return False
    
    async def _execute_action(self, action: ResolutionAction, issue: SystemIssue) -> bool:
        """Execute a specific resolution action."""
        try:
            if action == ResolutionAction.SCALE_UP:
                # Trigger scaling up (would integrate with AutoScaler)
                logger.info("Executing scale up action")
                return True
            
            elif action == ResolutionAction.SCALE_DOWN:
                # Trigger scaling down (would integrate with AutoScaler)
                logger.info("Executing scale down action")
                return True
            
            elif action == ResolutionAction.CLEAR_CACHE:
                # Clear cache for affected tenants
                for component in issue.affected_components:
                    if component in self.cache_manager.tenants:
                        await self._clear_tenant_cache(component)
                return True
            
            elif action == ResolutionAction.ADJUST_QUOTA:
                # Adjust quota for affected tenants
                for component in issue.affected_components:
                    if component in self.cache_manager.tenants:
                        await self._adjust_tenant_quota(component)
                return True
            
            elif action == ResolutionAction.OPTIMIZE_CONFIG:
                # Optimize configuration (would integrate with OptimizationAgent)
                logger.info("Executing configuration optimization")
                return True
            
            elif action == ResolutionAction.RESTART_SERVICE:
                # Restart Redis service (simulated)
                logger.info("Executing service restart")
                return True
            
            elif action == ResolutionAction.SWITCH_NODE:
                # Switch to backup node (would integrate with LoadBalancer)
                logger.info("Executing node switch")
                return True
            
            elif action == ResolutionAction.SEND_ALERT:
                # Send alert to operators
                await self._send_operator_alert(issue)
                return True
            
            return False
        except Exception as e:
            logger.error("Failed to execute action",
                        action=action,
                        error=str(e))
            return False
    
    async def _clear_tenant_cache(self, tenant_id: str):
        """Clear cache for a specific tenant."""
        try:
            # In a real implementation, this would clear Redis keys for the tenant
            logger.info("Clearing cache for tenant", tenant_id=tenant_id)
            
            # Reset metrics
            if tenant_id in self.cache_manager.tenant_metrics:
                self.cache_manager.tenant_metrics[tenant_id].memory_usage_mb = 0
        except Exception as e:
            logger.error("Failed to clear tenant cache",
                        tenant_id=tenant_id,
                        error=str(e))
    
    async def _adjust_tenant_quota(self, tenant_id: str):
        """Adjust quota for a specific tenant."""
        try:
            tenant = self.cache_manager.tenants.get(tenant_id)
            if tenant:
                # Increase quota by 20%
                new_quota = int(tenant.quota_memory_mb * 1.2)
                tenant.quota_memory_mb = new_quota
                
                logger.info("Adjusted quota for tenant",
                           tenant_id=tenant_id,
                           new_quota=new_quota)
        except Exception as e:
            logger.error("Failed to adjust tenant quota",
                        tenant_id=tenant_id,
                        error=str(e))
    
    async def _send_operator_alert(self, issue: SystemIssue):
        """Send alert to human operators."""
        try:
            # In a real implementation, this would send email/SMS/chat notification
            logger.warning("Sending operator alert",
                          issue_type=issue.issue_type,
                          severity=issue.severity,
                          description=issue.description)
        except Exception as e:
            logger.error("Failed to send operator alert", error=str(e))
    
    async def _create_alert(self, issue: SystemIssue):
        """Create an alert for a detected issue."""
        try:
            alert = Alert(
                id=f"healing_{int(issue.timestamp)}",
                title=f"System Issue: {issue.issue_type.value}",
                message=issue.description,
                severity=issue.severity,
                source="healing_agent",
                category="system_health",
                timestamp=issue.timestamp,
                tenant_id=issue.affected_components[0] if len(issue.affected_components) == 1 else None
            )
            
            # Add to health monitor alerts
            self.health_monitor.alerts.append(alert)
            
            logger.info("Created alert for issue",
                       issue_type=issue.issue_type,
                       severity=issue.severity)
        except Exception as e:
            logger.error("Failed to create alert", error=str(e))
    
    async def _cleanup_resolved_issues(self):
        """Clean up old resolved issues."""
        current_time = time.time()
        cutoff_time = current_time - 86400  # 24 hours
        
        # Remove old resolved issues
        self.resolved_issues = [
            issue for issue in self.resolved_issues
            if issue.timestamp > cutoff_time
        ]
        
        # Remove old resolution history
        self.resolution_history = [
            record for record in self.resolution_history
            if record['timestamp'] > cutoff_time
        ]
    
    async def _health_monitor_loop(self):
        """Background health monitoring loop."""
        while self.is_running:
            try:
                # Update system health
                await self._update_system_health()
                await asyncio.sleep(10)  # Update every 10 seconds
            except Exception as e:
                logger.error("Error in health monitor loop", error=str(e))
                await asyncio.sleep(10)
    
    async def _update_system_health(self):
        """Update system health metrics."""
        try:
            # Get current system metrics
            import psutil
            
            # Update CPU health
            cpu_usage = psutil.cpu_percent(interval=1)
            self.health_monitor.system_health['cpu'] = HealthCheck(
                component="cpu",
                status="healthy" if cpu_usage < self.thresholds['cpu_warning'] else "warning",
                current_value=cpu_usage,
                threshold=self.thresholds['cpu_warning'],
                last_check=time.time()
            )
            
            # Update memory health
            memory = psutil.virtual_memory()
            memory_usage = memory.percent
            self.health_monitor.system_health['memory'] = HealthCheck(
                component="memory",
                status="healthy" if memory_usage < self.thresholds['memory_warning'] else "warning",
                current_value=memory_usage,
                threshold=self.thresholds['memory_warning'],
                last_check=time.time()
            )
            
        except ImportError:
            # Mock data if psutil not available
            self.health_monitor.system_health['cpu'] = HealthCheck(
                component="cpu",
                status="healthy",
                current_value=50.0,
                threshold=self.thresholds['cpu_warning'],
                last_check=time.time()
            )
            
            self.health_monitor.system_health['memory'] = HealthCheck(
                component="memory",
                status="healthy",
                current_value=60.0,
                threshold=self.thresholds['memory_warning'],
                last_check=time.time()
            )
    
    async def _get_current_metrics(self) -> Dict[str, Any]:
        """Get current system metrics."""
        metrics = {}
        
        # System metrics
        for component, health in self.health_monitor.system_health.items():
            metrics[f"{component}_usage"] = health.current_value
        
        # Tenant metrics
        for tenant_id, tenant_metrics in self.cache_manager.tenant_metrics.items():
            metrics[f"tenant_{tenant_id}_hit_ratio"] = tenant_metrics.hit_ratio
            metrics[f"tenant_{tenant_id}_response_time"] = tenant_metrics.avg_response_time
        
        return metrics
    
    def _initialize_resolution_strategies(self) -> Dict[IssueType, Dict[str, Any]]:
        """Initialize resolution strategies for different issue types."""
        return {
            IssueType.HIGH_CPU: {
                'priority': 1,
                'auto_resolvable': True,
                'max_attempts': 3
            },
            IssueType.HIGH_MEMORY: {
                'priority': 1,
                'auto_resolvable': True,
                'max_attempts': 3
            },
            IssueType.REDIS_CONNECTION: {
                'priority': 0,
                'auto_resolvable': True,
                'max_attempts': 2
            },
            IssueType.SLOW_RESPONSE: {
                'priority': 2,
                'auto_resolvable': True,
                'max_attempts': 3
            },
            IssueType.LOW_HIT_RATIO: {
                'priority': 3,
                'auto_resolvable': True,
                'max_attempts': 5
            },
            IssueType.NODE_FAILURE: {
                'priority': 0,
                'auto_resolvable': True,
                'max_attempts': 1
            },
            IssueType.NETWORK_ISSUE: {
                'priority': 0,
                'auto_resolvable': False,
                'max_attempts': 0
            },
            IssueType.QUOTA_EXCEEDED: {
                'priority': 2,
                'auto_resolvable': True,
                'max_attempts': 2
            }
        }
    
    async def _load_issue_history(self):
        """Load historical issue data."""
        # In a real implementation, this would load from persistent storage
        # For now, we start with empty history
        pass
    
    def get_agent_info(self) -> AgentInfo:
        """Get current agent information."""
        return AgentInfo(
            name="HealingAgent",
            status="running" if self.is_running else "stopped",
            last_activity=time.time(),
            metrics={
                'active_issues': len(self.active_issues),
                'resolved_issues': len(self.resolved_issues),
                'resolution_success_rate': self._calculate_success_rate(),
                'avg_resolution_time': self._calculate_avg_resolution_time()
            }
        )
    
    def _calculate_success_rate(self) -> float:
        """Calculate resolution success rate."""
        if not self.resolution_history:
            return 0.0
        
        successful = sum(1 for record in self.resolution_history if record['success'])
        return successful / len(self.resolution_history)
    
    def _calculate_avg_resolution_time(self) -> float:
        """Calculate average resolution time."""
        if len(self.resolution_history) < 2:
            return 0.0
        
        # Calculate time between issue detection and resolution
        resolution_times = []
        for i in range(1, len(self.resolution_history)):
            if self.resolution_history[i]['success']:
                time_diff = self.resolution_history[i]['timestamp'] - self.resolution_history[i-1]['timestamp']
                resolution_times.append(time_diff)
        
        return np.mean(resolution_times) if resolution_times else 0.0 