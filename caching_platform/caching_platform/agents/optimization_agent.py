"""Autonomous optimization agent for cache performance tuning."""

import asyncio
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import structlog

from ..config.settings import get_settings, Settings
from ..config.schemas import AgentInfo, CacheMetrics, Tenant
from ..core.cache_manager import MultiTenantCacheManager

logger = structlog.get_logger(__name__)

@dataclass
class OptimizationRecommendation:
    """Optimization recommendation result."""
    tenant_id: str
    parameter: str
    current_value: Any
    recommended_value: Any
    expected_improvement: float
    confidence: float
    reasoning: str

@dataclass
class CachePattern:
    """Cache access pattern analysis."""
    tenant_id: str
    access_frequency: Dict[str, int]
    key_patterns: Dict[str, int]
    ttl_distribution: Dict[str, int]
    size_distribution: Dict[str, int]
    temporal_patterns: Dict[str, float]

class OptimizationAgent:
    """Autonomous agent for cache performance optimization."""
    
    def __init__(self, cache_manager: MultiTenantCacheManager, settings: Settings):
        self.cache_manager = cache_manager
        self.settings = settings
        
        # Optimization state
        self.is_running = False
        self.optimization_interval = 300  # 5 minutes
        self.last_optimization = 0
        
        # Pattern analysis
        self.cache_patterns: Dict[str, CachePattern] = {}
        self.access_history: Dict[str, List[Dict[str, Any]]] = {}
        self.max_history_size = 10000
        
        # Optimization tracking
        self.optimizations_applied: List[Dict[str, Any]] = []
        self.performance_improvements: Dict[str, List[float]] = {}
        
        # ML models
        self.pattern_clusterer = KMeans(n_clusters=5, random_state=42)
        self.scaler = StandardScaler()
        self.models_trained = False
        
        logger.info("OptimizationAgent initialized")
    
    async def initialize(self) -> bool:
        """Initialize the optimization agent."""
        try:
            # Load historical optimization data
            await self._load_optimization_history()
            
            # Start pattern analysis
            asyncio.create_task(self._pattern_analyzer())
            
            logger.info("OptimizationAgent initialized successfully")
            return True
        except Exception as e:
            logger.error("Failed to initialize OptimizationAgent", error=str(e))
            return False
    
    async def start(self) -> bool:
        """Start the optimization agent."""
        if self.is_running:
            logger.warning("OptimizationAgent is already running")
            return True
        
        self.is_running = True
        asyncio.create_task(self._optimization_loop())
        logger.info("OptimizationAgent started")
        return True
    
    async def stop(self) -> bool:
        """Stop the optimization agent."""
        self.is_running = False
        logger.info("OptimizationAgent stopped")
        return True
    
    async def _optimization_loop(self):
        """Main optimization loop."""
        while self.is_running:
            try:
                await self._run_optimization_cycle()
                await asyncio.sleep(self.optimization_interval)
            except Exception as e:
                logger.error("Error in optimization loop", error=str(e))
                await asyncio.sleep(60)
    
    async def _run_optimization_cycle(self):
        """Run a complete optimization cycle."""
        current_time = time.time()
        
        # Collect current performance metrics
        current_metrics = await self._collect_performance_metrics()
        
        # Analyze cache patterns
        await self._analyze_cache_patterns()
        
        # Generate optimization recommendations
        recommendations = await self._generate_recommendations(current_metrics)
        
        # Apply optimizations
        for recommendation in recommendations:
            if recommendation.expected_improvement > 0.05:  # 5% improvement threshold
                success = await self._apply_optimization(recommendation)
                
                if success:
                    self.optimizations_applied.append({
                        'timestamp': current_time,
                        'tenant_id': recommendation.tenant_id,
                        'parameter': recommendation.parameter,
                        'old_value': recommendation.current_value,
                        'new_value': recommendation.recommended_value,
                        'expected_improvement': recommendation.expected_improvement
                    })
                    
                    logger.info("Optimization applied",
                               tenant_id=recommendation.tenant_id,
                               parameter=recommendation.parameter,
                               improvement=recommendation.expected_improvement)
        
        self.last_optimization = current_time
    
    async def _collect_performance_metrics(self) -> Dict[str, Any]:
        """Collect current performance metrics for all tenants."""
        metrics = {}
        
        for tenant_id, tenant_metrics in self.cache_manager.tenant_metrics.items():
            tenant = self.cache_manager.tenants.get(tenant_id)
            if not tenant:
                continue
            
            # Calculate performance indicators
            hit_ratio = tenant_metrics.hit_ratio
            avg_response_time = tenant_metrics.avg_response_time
            memory_usage = tenant_metrics.memory_usage_mb / tenant.quota_memory_mb if tenant.quota_memory_mb > 0 else 0
            
            # Calculate efficiency score
            efficiency_score = self._calculate_efficiency_score(hit_ratio, avg_response_time, memory_usage)
            
            metrics[tenant_id] = {
                'hit_ratio': hit_ratio,
                'avg_response_time': avg_response_time,
                'memory_usage': memory_usage,
                'efficiency_score': efficiency_score,
                'total_requests': tenant_metrics.total_requests,
                'cache_hits': tenant_metrics.cache_hits,
                'cache_misses': tenant_metrics.total_requests - tenant_metrics.cache_hits
            }
        
        return metrics
    
    def _calculate_efficiency_score(self, hit_ratio: float, response_time: float, memory_usage: float) -> float:
        """Calculate overall efficiency score for a tenant."""
        # Normalize metrics (higher is better for hit_ratio, lower is better for others)
        hit_score = hit_ratio / 100.0
        response_score = max(0, 1 - (response_time / 1000.0))  # Normalize to 1 second
        memory_score = 1 - memory_usage  # Lower memory usage is better
        
        # Weighted average
        efficiency = (hit_score * 0.5 + response_score * 0.3 + memory_score * 0.2)
        return max(0, min(1, efficiency))
    
    async def _analyze_cache_patterns(self):
        """Analyze cache access patterns for optimization insights."""
        for tenant_id in self.cache_manager.tenants.keys():
            # Get recent access patterns (simulated)
            access_data = await self._get_access_patterns(tenant_id)
            
            if not access_data:
                continue
            
            # Analyze patterns
            pattern = CachePattern(
                tenant_id=tenant_id,
                access_frequency=self._analyze_access_frequency(access_data),
                key_patterns=self._analyze_key_patterns(access_data),
                ttl_distribution=self._analyze_ttl_distribution(access_data),
                size_distribution=self._analyze_size_distribution(access_data),
                temporal_patterns=self._analyze_temporal_patterns(access_data)
            )
            
            self.cache_patterns[tenant_id] = pattern
    
    async def _get_access_patterns(self, tenant_id: str) -> List[Dict[str, Any]]:
        """Get recent access patterns for a tenant (simulated)."""
        # In a real implementation, this would query Redis for actual access patterns
        # For now, we simulate based on metrics
        
        tenant_metrics = self.cache_manager.tenant_metrics.get(tenant_id)
        if not tenant_metrics:
            return []
        
        # Generate simulated access patterns
        patterns = []
        base_time = time.time() - 3600  # Last hour
        
        for i in range(min(100, tenant_metrics.total_requests)):
            patterns.append({
                'timestamp': base_time + i * 36,  # Spread over hour
                'key': f'key_{i % 20}',  # 20 different keys
                'operation': 'get' if np.random.random() > 0.3 else 'set',
                'ttl': np.random.choice([300, 600, 1800, 3600, 7200]),  # Common TTL values
                'size': np.random.randint(100, 10000),  # Key size in bytes
                'hit': np.random.random() < tenant_metrics.hit_ratio
            })
        
        return patterns
    
    def _analyze_access_frequency(self, access_data: List[Dict[str, Any]]) -> Dict[str, int]:
        """Analyze access frequency patterns."""
        frequency = {}
        for entry in access_data:
            key = entry['key']
            frequency[key] = frequency.get(key, 0) + 1
        return dict(sorted(frequency.items(), key=lambda x: x[1], reverse=True)[:10])
    
    def _analyze_key_patterns(self, access_data: List[Dict[str, Any]]) -> Dict[str, int]:
        """Analyze key naming patterns."""
        patterns = {}
        for entry in access_data:
            key = entry['key']
            # Extract pattern (e.g., "user:*", "session:*")
            if ':' in key:
                pattern = key.split(':')[0] + ':*'
            else:
                pattern = 'plain:*'
            patterns[pattern] = patterns.get(pattern, 0) + 1
        return patterns
    
    def _analyze_ttl_distribution(self, access_data: List[Dict[str, Any]]) -> Dict[str, int]:
        """Analyze TTL distribution patterns."""
        ttl_dist = {}
        for entry in access_data:
            ttl = entry['ttl']
            ttl_range = f"{ttl//60}m-{(ttl//60)+1}m"
            ttl_dist[ttl_range] = ttl_dist.get(ttl_range, 0) + 1
        return ttl_dist
    
    def _analyze_size_distribution(self, access_data: List[Dict[str, Any]]) -> Dict[str, int]:
        """Analyze key size distribution."""
        size_dist = {}
        for entry in access_data:
            size = entry['size']
            if size < 1000:
                size_range = "small"
            elif size < 10000:
                size_range = "medium"
            else:
                size_range = "large"
            size_dist[size_range] = size_dist.get(size_range, 0) + 1
        return size_dist
    
    def _analyze_temporal_patterns(self, access_data: List[Dict[str, Any]]) -> Dict[str, float]:
        """Analyze temporal access patterns."""
        if not access_data:
            return {}
        
        # Analyze by hour of day
        hourly_patterns = {}
        for entry in access_data:
            hour = time.localtime(entry['timestamp']).tm_hour
            hourly_patterns[hour] = hourly_patterns.get(hour, 0) + 1
        
        # Normalize
        total = sum(hourly_patterns.values())
        if total > 0:
            hourly_patterns = {k: v/total for k, v in hourly_patterns.items()}
        
        return hourly_patterns
    
    async def _generate_recommendations(self, current_metrics: Dict[str, Any]) -> List[OptimizationRecommendation]:
        """Generate optimization recommendations based on analysis."""
        recommendations = []
        
        for tenant_id, metrics in current_metrics.items():
            tenant = self.cache_manager.tenants.get(tenant_id)
            pattern = self.cache_patterns.get(tenant_id)
            
            if not tenant or not pattern:
                continue
            
            # TTL optimization
            ttl_rec = await self._optimize_ttl(tenant_id, pattern, metrics)
            if ttl_rec:
                recommendations.append(ttl_rec)
            
            # Memory optimization
            memory_rec = await self._optimize_memory(tenant_id, pattern, metrics)
            if memory_rec:
                recommendations.append(memory_rec)
            
            # Eviction policy optimization
            eviction_rec = await self._optimize_eviction_policy(tenant_id, pattern, metrics)
            if eviction_rec:
                recommendations.append(eviction_rec)
        
        return recommendations
    
    async def _optimize_ttl(self, tenant_id: str, pattern: CachePattern, metrics: Dict[str, Any]) -> Optional[OptimizationRecommendation]:
        """Optimize TTL values based on access patterns."""
        if not pattern.ttl_distribution:
            return None
        
        # Analyze current TTL distribution
        most_common_ttl = max(pattern.ttl_distribution.items(), key=lambda x: x[1])[0]
        hit_ratio = metrics['hit_ratio']
        
        # Recommend TTL adjustments based on hit ratio
        if hit_ratio < 0.7:  # Low hit ratio
            # Increase TTL for frequently accessed keys
            recommended_ttl = 3600  # 1 hour
            reasoning = "Low hit ratio detected, increasing TTL for better cache efficiency"
        elif hit_ratio > 0.95:  # Very high hit ratio
            # Could reduce TTL to save memory
            recommended_ttl = 1800  # 30 minutes
            reasoning = "Very high hit ratio, reducing TTL to optimize memory usage"
        else:
            return None
        
        return OptimizationRecommendation(
            tenant_id=tenant_id,
            parameter="default_ttl",
            current_value=1800,  # Assume current default
            recommended_value=recommended_ttl,
            expected_improvement=0.05,
            confidence=0.7,
            reasoning=reasoning
        )
    
    async def _optimize_memory(self, tenant_id: str, pattern: CachePattern, metrics: Dict[str, Any]) -> Optional[OptimizationRecommendation]:
        """Optimize memory usage based on patterns."""
        memory_usage = metrics['memory_usage']
        
        if memory_usage > 0.9:  # High memory usage
            # Recommend memory increase
            tenant = self.cache_manager.tenants.get(tenant_id)
            if tenant:
                current_quota = tenant.quota_memory_mb
                recommended_quota = int(current_quota * 1.5)
                
                return OptimizationRecommendation(
                    tenant_id=tenant_id,
                    parameter="quota_memory_mb",
                    current_value=current_quota,
                    recommended_value=recommended_quota,
                    expected_improvement=0.1,
                    confidence=0.8,
                    reasoning="High memory usage detected, increasing quota to prevent evictions"
                )
        
        return None
    
    async def _optimize_eviction_policy(self, tenant_id: str, pattern: CachePattern, metrics: Dict[str, Any]) -> Optional[OptimizationRecommendation]:
        """Optimize eviction policy based on access patterns."""
        hit_ratio = metrics['hit_ratio']
        
        # Analyze access patterns to recommend eviction policy
        if pattern.access_frequency:
            # Check if there are clear hot/cold patterns
            access_counts = list(pattern.access_frequency.values())
            if len(access_counts) > 1:
                hot_ratio = max(access_counts) / sum(access_counts)
                
                if hot_ratio > 0.5:  # Clear hot/cold pattern
                    recommended_policy = "allkeys-lru"
                    reasoning = "Clear hot/cold access pattern detected, using LRU eviction"
                else:
                    recommended_policy = "allkeys-random"
                    reasoning = "Uniform access pattern, using random eviction"
                
                return OptimizationRecommendation(
                    tenant_id=tenant_id,
                    parameter="eviction_policy",
                    current_value="allkeys-lru",  # Assume current policy
                    recommended_value=recommended_policy,
                    expected_improvement=0.03,
                    confidence=0.6,
                    reasoning=reasoning
                )
        
        return None
    
    async def _apply_optimization(self, recommendation: OptimizationRecommendation) -> bool:
        """Apply an optimization recommendation."""
        try:
            tenant = self.cache_manager.tenants.get(recommendation.tenant_id)
            if not tenant:
                return False
            
            # Apply the optimization based on parameter type
            if recommendation.parameter == "default_ttl":
                # Update tenant's default TTL
                tenant.default_ttl = recommendation.recommended_value
            elif recommendation.parameter == "quota_memory_mb":
                # Update tenant's memory quota
                tenant.quota_memory_mb = recommendation.recommended_value
            elif recommendation.parameter == "eviction_policy":
                # Update eviction policy (would need Redis config update)
                pass  # Implementation depends on Redis configuration management
            
            logger.info("Optimization applied successfully",
                       tenant_id=recommendation.tenant_id,
                       parameter=recommendation.parameter,
                       new_value=recommendation.recommended_value)
            
            return True
        except Exception as e:
            logger.error("Failed to apply optimization",
                        tenant_id=recommendation.tenant_id,
                        parameter=recommendation.parameter,
                        error=str(e))
            return False
    
    async def _pattern_analyzer(self):
        """Background task for continuous pattern analysis."""
        while self.is_running:
            try:
                # Update access history
                await self._update_access_history()
                
                # Train ML models if we have enough data
                if len(self.access_history) > 100 and not self.models_trained:
                    await self._train_ml_models()
                
                await asyncio.sleep(60)  # Update every minute
            except Exception as e:
                logger.error("Error in pattern analyzer", error=str(e))
                await asyncio.sleep(60)
    
    async def _update_access_history(self):
        """Update access history with recent data."""
        # In a real implementation, this would collect actual access data
        # For now, we simulate based on current metrics
        
        for tenant_id, tenant_metrics in self.cache_manager.tenant_metrics.items():
            if tenant_id not in self.access_history:
                self.access_history[tenant_id] = []
            
            # Add current metrics to history
            history_entry = {
                'timestamp': time.time(),
                'hit_ratio': tenant_metrics.hit_ratio,
                'total_requests': tenant_metrics.total_requests,
                'memory_usage': tenant_metrics.memory_usage_mb,
                'avg_response_time': tenant_metrics.avg_response_time
            }
            
            self.access_history[tenant_id].append(history_entry)
            
            # Keep only recent history
            if len(self.access_history[tenant_id]) > self.max_history_size:
                self.access_history[tenant_id] = self.access_history[tenant_id][-self.max_history_size:]
    
    async def _train_ml_models(self):
        """Train ML models for pattern recognition."""
        try:
            # Prepare training data
            features = []
            for tenant_id, history in self.access_history.items():
                if len(history) >= 10:
                    # Extract features from recent history
                    recent = history[-10:]
                    feature_vector = [
                        np.mean([h['hit_ratio'] for h in recent]),
                        np.mean([h['total_requests'] for h in recent]),
                        np.mean([h['memory_usage'] for h in recent]),
                        np.mean([h['avg_response_time'] for h in recent]),
                        np.std([h['hit_ratio'] for h in recent]),
                        np.std([h['total_requests'] for h in recent])
                    ]
                    features.append(feature_vector)
            
            if len(features) >= 5:
                # Scale features
                features_scaled = self.scaler.fit_transform(features)
                
                # Train clustering model
                self.pattern_clusterer.fit(features_scaled)
                self.models_trained = True
                
                logger.info("ML models trained successfully", 
                           data_points=len(features),
                           clusters=self.pattern_clusterer.n_clusters)
        except Exception as e:
            logger.error("Failed to train ML models", error=str(e))
    
    async def _load_optimization_history(self):
        """Load historical optimization data."""
        # In a real implementation, this would load from persistent storage
        # For now, we start with empty history
        pass
    
    def get_agent_info(self) -> AgentInfo:
        """Get current agent information."""
        return AgentInfo(
            name="OptimizationAgent",
            status="running" if self.is_running else "stopped",
            last_activity=time.time(),
            metrics={
                'optimizations_applied': len(self.optimizations_applied),
                'tenants_analyzed': len(self.cache_patterns),
                'models_trained': self.models_trained,
                'avg_improvement': np.mean([opt['expected_improvement'] for opt in self.optimizations_applied[-10:]]) if self.optimizations_applied else 0.0
            }
        ) 