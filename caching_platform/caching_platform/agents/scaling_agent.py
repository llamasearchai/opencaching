"""Autonomous scaling agent for intelligent cache cluster management."""

import asyncio
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
import structlog

from ..config.settings import get_settings, Settings
from ..config.schemas import ScalingDecision, AgentInfo, CacheMetrics
from ..core.cache_manager import MultiTenantCacheManager
from ..core.auto_scaler import AutoScaler

logger = structlog.get_logger(__name__)

@dataclass
class ScalingPrediction:
    """Prediction result for scaling decisions."""
    predicted_load: float
    confidence: float
    recommended_nodes: int
    reasoning: str
    features_used: List[str]

class ScalingAgent:
    """Autonomous agent for intelligent cache cluster scaling."""
    
    def __init__(self, cache_manager: MultiTenantCacheManager, auto_scaler: AutoScaler, settings: Settings):
        self.cache_manager = cache_manager
        self.auto_scaler = auto_scaler
        self.settings = settings
        self.scaling_config = settings.scaling
        
        # ML model for load prediction
        self.load_predictor = LinearRegression()
        self.scaler = StandardScaler()
        self.model_trained = False
        
        # Historical data for training
        self.historical_data: List[Dict[str, Any]] = []
        self.max_history_size = 1000
        
        # Performance tracking
        self.scaling_decisions: List[ScalingDecision] = []
        self.prediction_accuracy: List[float] = []
        
        # Agent state
        self.is_running = False
        self.last_prediction_time = 0
        self.prediction_interval = 60  # seconds
        
        logger.info("ScalingAgent initialized", 
                   min_nodes=self.scaling_config.min_nodes,
                   max_nodes=self.scaling_config.max_nodes)
    
    async def initialize(self) -> bool:
        """Initialize the scaling agent."""
        try:
            # Load historical data if available
            await self._load_historical_data()
            
            # Train initial model if we have data
            if len(self.historical_data) > 10:
                await self._train_model()
            
            logger.info("ScalingAgent initialized successfully")
            return True
        except Exception as e:
            logger.error("Failed to initialize ScalingAgent", error=str(e))
            return False
    
    async def start(self) -> bool:
        """Start the scaling agent."""
        if self.is_running:
            logger.warning("ScalingAgent is already running")
            return True
        
        self.is_running = True
        asyncio.create_task(self._scaling_loop())
        logger.info("ScalingAgent started")
        return True
    
    async def stop(self) -> bool:
        """Stop the scaling agent."""
        self.is_running = False
        logger.info("ScalingAgent stopped")
        return True
    
    async def _scaling_loop(self):
        """Main scaling decision loop."""
        while self.is_running:
            try:
                await self._make_scaling_decision()
                await asyncio.sleep(self.prediction_interval)
            except Exception as e:
                logger.error("Error in scaling loop", error=str(e))
                await asyncio.sleep(10)
    
    async def _make_scaling_decision(self):
        """Make intelligent scaling decision based on predictions."""
        current_time = time.time()
        
        # Collect current metrics
        current_metrics = await self._collect_current_metrics()
        
        # Make prediction
        prediction = await self._predict_load(current_metrics)
        
        # Evaluate if scaling is needed
        scaling_decision = await self._evaluate_scaling_needs(prediction, current_metrics)
        
        if scaling_decision:
            # Execute scaling decision
            success = await self.auto_scaler.execute_scaling_decision(scaling_decision)
            
            # Record decision
            self.scaling_decisions.append(scaling_decision)
            
            # Update historical data
            await self._update_historical_data(current_metrics, scaling_decision, success)
            
            # Retrain model periodically
            if len(self.historical_data) % 50 == 0:
                await self._train_model()
            
            logger.info("Scaling decision executed",
                       decision=scaling_decision.action,
                       target_nodes=scaling_decision.target_nodes,
                       success=success)
        
        self.last_prediction_time = current_time
    
    async def _collect_current_metrics(self) -> Dict[str, Any]:
        """Collect current system metrics for prediction."""
        metrics = {
            'timestamp': time.time(),
            'cpu_usage': 0.0,
            'memory_usage': 0.0,
            'request_rate': 0.0,
            'hit_ratio': 0.0,
            'active_connections': 0,
            'current_nodes': self.auto_scaler.current_nodes,
            'hour_of_day': time.localtime().tm_hour,
            'day_of_week': time.localtime().tm_wday,
        }
        
        # Get system metrics (simulated)
        try:
            import psutil
            metrics['cpu_usage'] = psutil.cpu_percent(interval=1)
            metrics['memory_usage'] = psutil.virtual_memory().percent
        except ImportError:
            # Mock data if psutil not available
            metrics['cpu_usage'] = np.random.uniform(20, 80)
            metrics['memory_usage'] = np.random.uniform(30, 70)
        
        # Get cache metrics
        total_requests = 0
        total_hits = 0
        total_connections = 0
        
        for tenant_id, tenant_metrics in self.cache_manager.tenant_metrics.items():
            total_requests += tenant_metrics.total_requests
            total_hits += tenant_metrics.cache_hits
            total_connections += self.cache_manager.tenant_connections.get(tenant_id, 0)
        
        if total_requests > 0:
            metrics['hit_ratio'] = total_hits / total_requests
            metrics['request_rate'] = total_requests / 60  # requests per minute
        metrics['active_connections'] = total_connections
        
        return metrics
    
    async def _predict_load(self, current_metrics: Dict[str, Any]) -> ScalingPrediction:
        """Predict future load using ML model."""
        if not self.model_trained:
            # Fallback to simple heuristics
            return await self._heuristic_prediction(current_metrics)
        
        try:
            # Prepare features for prediction
            features = self._extract_features(current_metrics)
            features_scaled = self.scaler.transform([features])
            
            # Make prediction
            predicted_load = self.load_predictor.predict(features_scaled)[0]
            predicted_load = max(0, min(100, predicted_load))  # Clamp to 0-100
            
            # Calculate confidence based on model performance
            confidence = min(0.95, max(0.5, np.mean(self.prediction_accuracy[-10:]) if self.prediction_accuracy else 0.7))
            
            # Recommend nodes based on predicted load
            recommended_nodes = self._calculate_recommended_nodes(predicted_load)
            
            return ScalingPrediction(
                predicted_load=predicted_load,
                confidence=confidence,
                recommended_nodes=recommended_nodes,
                reasoning=f"ML model prediction with {confidence:.2f} confidence",
                features_used=list(current_metrics.keys())
            )
        except Exception as e:
            logger.warning("ML prediction failed, using heuristic", error=str(e))
            return await self._heuristic_prediction(current_metrics)
    
    async def _heuristic_prediction(self, current_metrics: Dict[str, Any]) -> ScalingPrediction:
        """Fallback heuristic prediction when ML model is not available."""
        # Simple heuristic based on current metrics
        cpu_weight = 0.4
        memory_weight = 0.3
        request_weight = 0.3
        
        predicted_load = (
            current_metrics['cpu_usage'] * cpu_weight +
            current_metrics['memory_usage'] * memory_weight +
            min(100, current_metrics['request_rate'] * 10) * request_weight
        )
        
        # Add time-based patterns
        hour_factor = 1.0
        if 9 <= current_metrics['hour_of_day'] <= 17:  # Business hours
            hour_factor = 1.2
        elif 18 <= current_metrics['hour_of_day'] <= 22:  # Evening peak
            hour_factor = 1.1
        
        predicted_load *= hour_factor
        predicted_load = max(0, min(100, predicted_load))
        
        recommended_nodes = self._calculate_recommended_nodes(predicted_load)
        
        return ScalingPrediction(
            predicted_load=predicted_load,
            confidence=0.6,
            recommended_nodes=recommended_nodes,
            reasoning="Heuristic prediction based on current metrics and time patterns",
            features_used=['cpu_usage', 'memory_usage', 'request_rate', 'hour_of_day']
        )
    
    def _calculate_recommended_nodes(self, predicted_load: float) -> int:
        """Calculate recommended number of nodes based on predicted load."""
        min_nodes = self.scaling_config.min_nodes
        max_nodes = self.scaling_config.max_nodes
        
        # Linear scaling based on load
        if predicted_load < 30:
            recommended = min_nodes
        elif predicted_load > 80:
            recommended = max_nodes
        else:
            # Linear interpolation
            load_factor = (predicted_load - 30) / 50
            recommended = int(min_nodes + (max_nodes - min_nodes) * load_factor)
        
        return max(min_nodes, min(max_nodes, recommended))
    
    async def _evaluate_scaling_needs(self, prediction: ScalingPrediction, current_metrics: Dict[str, Any]) -> Optional[ScalingDecision]:
        """Evaluate if scaling is needed based on prediction."""
        current_nodes = self.auto_scaler.current_nodes
        recommended_nodes = prediction.recommended_nodes
        
        # Check if scaling is needed
        if recommended_nodes > current_nodes:
            action = "scale_up"
        elif recommended_nodes < current_nodes and current_metrics['cpu_usage'] < 40:
            action = "scale_down"
        else:
            return None
        
        # Check cooldown period
        if self.scaling_decisions:
            last_decision = self.scaling_decisions[-1]
            time_since_last = time.time() - last_decision.timestamp
            if time_since_last < self.scaling_config.cooldown_period:
                return None
        
        return ScalingDecision(
            action=action,
            target_nodes=recommended_nodes,
            reason=prediction.reasoning,
            confidence=prediction.confidence,
            metrics=current_metrics,
            timestamp=time.time()
        )
    
    def _extract_features(self, metrics: Dict[str, Any]) -> List[float]:
        """Extract numerical features for ML model."""
        return [
            metrics['cpu_usage'],
            metrics['memory_usage'],
            metrics['request_rate'],
            metrics['hit_ratio'],
            metrics['active_connections'],
            metrics['current_nodes'],
            metrics['hour_of_day'],
            metrics['day_of_week']
        ]
    
    async def _train_model(self):
        """Train the ML model on historical data."""
        if len(self.historical_data) < 10:
            return
        
        try:
            # Prepare training data
            X = []
            y = []
            
            for data_point in self.historical_data[-100:]:  # Use last 100 points
                features = self._extract_features(data_point['metrics'])
                X.append(features)
                y.append(data_point['actual_load'])
            
            X = np.array(X)
            y = np.array(y)
            
            # Scale features
            X_scaled = self.scaler.fit_transform(X)
            
            # Train model
            self.load_predictor.fit(X_scaled, y)
            self.model_trained = True
            
            # Calculate accuracy
            predictions = self.load_predictor.predict(X_scaled)
            accuracy = 1 - np.mean(np.abs(predictions - y) / (y + 1e-6))
            self.prediction_accuracy.append(accuracy)
            
            logger.info("ML model trained successfully",
                       data_points=len(X),
                       accuracy=accuracy)
        except Exception as e:
            logger.error("Failed to train ML model", error=str(e))
    
    async def _update_historical_data(self, metrics: Dict[str, Any], decision: ScalingDecision, success: bool):
        """Update historical data with actual results."""
        # Calculate actual load after scaling
        actual_load = metrics['cpu_usage']  # Simplified for now
        
        data_point = {
            'timestamp': time.time(),
            'metrics': metrics,
            'decision': decision.action if decision else None,
            'target_nodes': decision.target_nodes if decision else metrics['current_nodes'],
            'actual_load': actual_load,
            'success': success
        }
        
        self.historical_data.append(data_point)
        
        # Keep only recent data
        if len(self.historical_data) > self.max_history_size:
            self.historical_data = self.historical_data[-self.max_history_size:]
    
    async def _load_historical_data(self):
        """Load historical data from persistent storage."""
        # In a real implementation, this would load from database/file
        # For now, we start with empty data
        pass
    
    def get_agent_info(self) -> AgentInfo:
        """Get current agent information."""
        return AgentInfo(
            name="ScalingAgent",
            status="running" if self.is_running else "stopped",
            last_activity=time.time(),
            metrics={
                'predictions_made': len(self.scaling_decisions),
                'model_accuracy': np.mean(self.prediction_accuracy[-10:]) if self.prediction_accuracy else 0.0,
                'historical_data_points': len(self.historical_data),
                'model_trained': self.model_trained
            }
        ) 