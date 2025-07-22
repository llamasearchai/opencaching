"""Autonomous prediction agent for usage forecasting and proactive insights."""

import asyncio
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error
import structlog

from ..config.settings import get_settings, Settings
from ..config.schemas import AgentInfo, CacheMetrics, Tenant
from ..core.cache_manager import MultiTenantCacheManager

logger = structlog.get_logger(__name__)

@dataclass
class UsageForecast:
    """Usage forecast for a specific metric."""
    metric_name: str
    tenant_id: Optional[str]
    predictions: List[float]
    timestamps: List[float]
    confidence_intervals: List[Tuple[float, float]]
    accuracy_score: float

@dataclass
class ScalingPrediction:
    """Scaling prediction result."""
    predicted_load: float
    recommended_nodes: int
    confidence: float
    time_horizon: int  # minutes
    reasoning: str
    urgency: str  # low, medium, high, critical

@dataclass
class AnomalyDetection:
    """Anomaly detection result."""
    metric_name: str
    tenant_id: Optional[str]
    current_value: float
    expected_value: float
    anomaly_score: float
    severity: str  # low, medium, high
    description: str

class PredictionAgent:
    """Autonomous agent for usage forecasting and predictive insights."""
    
    def __init__(self, cache_manager: MultiTenantCacheManager, settings: Settings):
        self.cache_manager = cache_manager
        self.settings = settings
        
        # Prediction state
        self.is_running = False
        self.prediction_interval = 300  # 5 minutes
        self.last_prediction = 0
        
        # Data collection
        self.historical_data: Dict[str, List[Dict[str, Any]]] = {}
        self.max_history_size = 10000
        
        # ML models
        self.models: Dict[str, RandomForestRegressor] = {}
        self.scalers: Dict[str, StandardScaler] = {}
        self.model_metrics: Dict[str, Dict[str, float]] = {}
        
        # Prediction results
        self.current_forecasts: Dict[str, UsageForecast] = {}
        self.scaling_predictions: List[ScalingPrediction] = []
        self.detected_anomalies: List[AnomalyDetection] = []
        
        # Configuration
        self.forecast_horizon = 24  # hours
        self.anomaly_threshold = 2.0  # standard deviations
        
        logger.info("PredictionAgent initialized")
    
    async def initialize(self) -> bool:
        """Initialize the prediction agent."""
        try:
            # Load historical data
            await self._load_historical_data()
            
            # Initialize models
            await self._initialize_models()
            
            # Start data collection
            asyncio.create_task(self._data_collector())
            
            logger.info("PredictionAgent initialized successfully")
            return True
        except Exception as e:
            logger.error("Failed to initialize PredictionAgent", error=str(e))
            return False
    
    async def start(self) -> bool:
        """Start the prediction agent."""
        if self.is_running:
            logger.warning("PredictionAgent is already running")
            return True
        
        self.is_running = True
        asyncio.create_task(self._prediction_loop())
        logger.info("PredictionAgent started")
        return True
    
    async def stop(self) -> bool:
        """Stop the prediction agent."""
        self.is_running = False
        logger.info("PredictionAgent stopped")
        return True
    
    async def _prediction_loop(self):
        """Main prediction loop."""
        while self.is_running:
            try:
                await self._run_prediction_cycle()
                await asyncio.sleep(self.prediction_interval)
            except Exception as e:
                logger.error("Error in prediction loop", error=str(e))
                await asyncio.sleep(60)
    
    async def _run_prediction_cycle(self):
        """Run a complete prediction cycle."""
        current_time = time.time()
        
        # Generate forecasts for all metrics
        await self._generate_forecasts()
        
        # Predict scaling needs
        scaling_prediction = await self._predict_scaling_needs()
        if scaling_prediction:
            self.scaling_predictions.append(scaling_prediction)
        
        # Detect anomalies
        anomalies = await self._detect_anomalies()
        self.detected_anomalies.extend(anomalies)
        
        # Retrain models if needed
        if len(self.historical_data) % 100 == 0:
            await self._retrain_models()
        
        # Clean up old predictions
        await self._cleanup_old_predictions()
        
        self.last_prediction = current_time
        
        logger.info("Prediction cycle completed",
                   forecasts=len(self.current_forecasts),
                   anomalies=len(anomalies))
    
    async def _data_collector(self):
        """Background task for continuous data collection."""
        while self.is_running:
            try:
                await self._collect_current_data()
                await asyncio.sleep(60)  # Collect every minute
            except Exception as e:
                logger.error("Error in data collector", error=str(e))
                await asyncio.sleep(60)
    
    async def _collect_current_data(self):
        """Collect current system data for prediction."""
        current_time = time.time()
        
        # System-level metrics
        system_data = await self._collect_system_metrics()
        self._add_to_history('system', system_data, current_time)
        
        # Tenant-level metrics
        for tenant_id, tenant_metrics in self.cache_manager.tenant_metrics.items():
            tenant_data = await self._collect_tenant_metrics(tenant_id, tenant_metrics)
            self._add_to_history(f'tenant_{tenant_id}', tenant_data, current_time)
    
    async def _collect_system_metrics(self) -> Dict[str, Any]:
        """Collect system-level metrics."""
        try:
            import psutil
            
            return {
                'cpu_usage': psutil.cpu_percent(interval=1),
                'memory_usage': psutil.virtual_memory().percent,
                'disk_usage': psutil.disk_usage('/').percent,
                'network_io': psutil.net_io_counters().bytes_sent + psutil.net_io_counters().bytes_recv,
                'hour_of_day': time.localtime().tm_hour,
                'day_of_week': time.localtime().tm_wday,
                'is_weekend': time.localtime().tm_wday >= 5
            }
        except ImportError:
            # Mock data if psutil not available
            return {
                'cpu_usage': np.random.uniform(20, 80),
                'memory_usage': np.random.uniform(30, 70),
                'disk_usage': np.random.uniform(40, 60),
                'network_io': np.random.uniform(1000000, 10000000),
                'hour_of_day': time.localtime().tm_hour,
                'day_of_week': time.localtime().tm_wday,
                'is_weekend': time.localtime().tm_wday >= 5
            }
    
    async def _collect_tenant_metrics(self, tenant_id: str, tenant_metrics: CacheMetrics) -> Dict[str, Any]:
        """Collect tenant-specific metrics."""
        return {
            'hit_ratio': tenant_metrics.hit_ratio,
            'total_requests': tenant_metrics.total_requests,
            'cache_hits': tenant_metrics.cache_hits,
            'cache_misses': tenant_metrics.total_requests - tenant_metrics.cache_hits,
            'avg_response_time': tenant_metrics.avg_response_time,
            'memory_usage_mb': tenant_metrics.memory_usage_mb,
            'hour_of_day': time.localtime().tm_hour,
            'day_of_week': time.localtime().tm_wday
        }
    
    def _add_to_history(self, key: str, data: Dict[str, Any], timestamp: float):
        """Add data point to historical data."""
        if key not in self.historical_data:
            self.historical_data[key] = []
        
        data_point = {
            'timestamp': timestamp,
            **data
        }
        
        self.historical_data[key].append(data_point)
        
        # Keep only recent data
        if len(self.historical_data[key]) > self.max_history_size:
            self.historical_data[key] = self.historical_data[key][-self.max_history_size:]
    
    async def _generate_forecasts(self):
        """Generate forecasts for all tracked metrics."""
        self.current_forecasts.clear()
        
        # System-level forecasts
        system_forecasts = await self._forecast_system_metrics()
        self.current_forecasts.update(system_forecasts)
        
        # Tenant-level forecasts
        tenant_forecasts = await self._forecast_tenant_metrics()
        self.current_forecasts.update(tenant_forecasts)
    
    async def _forecast_system_metrics(self) -> Dict[str, UsageForecast]:
        """Generate forecasts for system-level metrics."""
        forecasts = {}
        
        if 'system' not in self.historical_data or len(self.historical_data['system']) < 100:
            return forecasts
        
        # Forecast CPU usage
        cpu_forecast = await self._forecast_metric('system', 'cpu_usage', None)
        if cpu_forecast:
            forecasts['system_cpu'] = cpu_forecast
        
        # Forecast memory usage
        memory_forecast = await self._forecast_metric('system', 'memory_usage', None)
        if memory_forecast:
            forecasts['system_memory'] = memory_forecast
        
        # Forecast network I/O
        network_forecast = await self._forecast_metric('system', 'network_io', None)
        if network_forecast:
            forecasts['system_network'] = network_forecast
        
        return forecasts
    
    async def _forecast_tenant_metrics(self) -> Dict[str, UsageForecast]:
        """Generate forecasts for tenant-level metrics."""
        forecasts = {}
        
        for tenant_id in self.cache_manager.tenants.keys():
            history_key = f'tenant_{tenant_id}'
            
            if history_key not in self.historical_data or len(self.historical_data[history_key]) < 50:
                continue
            
            # Forecast hit ratio
            hit_ratio_forecast = await self._forecast_metric(history_key, 'hit_ratio', tenant_id)
            if hit_ratio_forecast:
                forecasts[f'{tenant_id}_hit_ratio'] = hit_ratio_forecast
            
            # Forecast request rate
            request_forecast = await self._forecast_metric(history_key, 'total_requests', tenant_id)
            if request_forecast:
                forecasts[f'{tenant_id}_requests'] = request_forecast
            
            # Forecast response time
            response_forecast = await self._forecast_metric(history_key, 'avg_response_time', tenant_id)
            if response_forecast:
                forecasts[f'{tenant_id}_response_time'] = response_forecast
        
        return forecasts
    
    async def _forecast_metric(self, history_key: str, metric_name: str, tenant_id: Optional[str]) -> Optional[UsageForecast]:
        """Forecast a specific metric."""
        try:
            history = self.historical_data[history_key]
            if len(history) < 50:
                return None
            
            # Prepare features
            df = pd.DataFrame(history)
            features = self._extract_features(df)
            
            if len(features) < 20:
                return None
            
            # Get target values
            targets = df[metric_name].values
            
            # Train or update model
            model_key = f"{history_key}_{metric_name}"
            if model_key not in self.models:
                await self._train_model(model_key, features, targets)
            else:
                # Update model with new data
                await self._update_model(model_key, features, targets)
            
            # Generate predictions
            predictions = await self._generate_predictions(model_key, features[-1:])
            
            if not predictions:
                return None
            
            # Calculate confidence intervals
            confidence_intervals = self._calculate_confidence_intervals(predictions, model_key)
            
            # Calculate accuracy
            accuracy = self.model_metrics.get(model_key, {}).get('mae', 0.0)
            
            # Generate future timestamps
            timestamps = [time.time() + i * 3600 for i in range(self.forecast_horizon)]
            
            return UsageForecast(
                metric_name=metric_name,
                tenant_id=tenant_id,
                predictions=predictions,
                timestamps=timestamps,
                confidence_intervals=confidence_intervals,
                accuracy_score=1.0 / (1.0 + accuracy)  # Convert MAE to accuracy score
            )
        
        except Exception as e:
            logger.error("Failed to forecast metric",
                        metric=metric_name,
                        tenant_id=tenant_id,
                        error=str(e))
            return None
    
    def _extract_features(self, df: pd.DataFrame) -> np.ndarray:
        """Extract features from historical data."""
        features = []
        
        for i in range(len(df)):
            if i < 24:  # Need at least 24 hours of history
                continue
            
            # Time-based features
            hour = df.iloc[i]['hour_of_day']
            day_of_week = df.iloc[i]['day_of_week']
            is_weekend = df.iloc[i].get('is_weekend', day_of_week >= 5)
            
            # Lag features (previous values)
            lag_1 = df.iloc[i-1]['cpu_usage'] if 'cpu_usage' in df.columns else 0
            lag_6 = df.iloc[i-6]['cpu_usage'] if i >= 6 and 'cpu_usage' in df.columns else 0
            lag_24 = df.iloc[i-24]['cpu_usage'] if i >= 24 and 'cpu_usage' in df.columns else 0
            
            # Rolling statistics
            if i >= 6:
                rolling_mean = df.iloc[i-6:i]['cpu_usage'].mean() if 'cpu_usage' in df.columns else 0
                rolling_std = df.iloc[i-6:i]['cpu_usage'].std() if 'cpu_usage' in df.columns else 0
            else:
                rolling_mean = rolling_std = 0
            
            feature_vector = [
                hour, day_of_week, is_weekend,
                lag_1, lag_6, lag_24,
                rolling_mean, rolling_std
            ]
            
            features.append(feature_vector)
        
        return np.array(features)
    
    async def _train_model(self, model_key: str, features: np.ndarray, targets: np.ndarray):
        """Train a new model."""
        try:
            # Scale features
            scaler = StandardScaler()
            features_scaled = scaler.fit_transform(features)
            
            # Train model
            model = RandomForestRegressor(n_estimators=100, random_state=42)
            model.fit(features_scaled, targets)
            
            # Calculate metrics
            predictions = model.predict(features_scaled)
            mae = mean_absolute_error(targets, predictions)
            mse = mean_squared_error(targets, predictions)
            
            # Store model and metrics
            self.models[model_key] = model
            self.scalers[model_key] = scaler
            self.model_metrics[model_key] = {
                'mae': mae,
                'mse': mse,
                'rmse': np.sqrt(mse)
            }
            
            logger.info("Model trained successfully",
                       model_key=model_key,
                       mae=mae,
                       data_points=len(features))
        
        except Exception as e:
            logger.error("Failed to train model",
                        model_key=model_key,
                        error=str(e))
    
    async def _update_model(self, model_key: str, features: np.ndarray, targets: np.ndarray):
        """Update an existing model with new data."""
        # For simplicity, retrain the model with all data
        # In production, you might use online learning or incremental updates
        await self._train_model(model_key, features, targets)
    
    async def _generate_predictions(self, model_key: str, features: np.ndarray) -> List[float]:
        """Generate predictions using a trained model."""
        try:
            model = self.models.get(model_key)
            scaler = self.scalers.get(model_key)
            
            if not model or not scaler:
                return []
            
            # Scale features
            features_scaled = scaler.transform(features)
            
            # Generate predictions for future time points
            predictions = []
            current_features = features_scaled[0].copy()
            
            for i in range(self.forecast_horizon):
                # Make prediction
                pred = model.predict([current_features])[0]
                predictions.append(pred)
                
                # Update features for next prediction (simplified)
                # In a real implementation, you'd update time-based features
                current_features[0] = (current_features[0] + 1) % 24  # Update hour
            
            return predictions
        
        except Exception as e:
            logger.error("Failed to generate predictions",
                        model_key=model_key,
                        error=str(e))
            return []
    
    def _calculate_confidence_intervals(self, predictions: List[float], model_key: str) -> List[Tuple[float, float]]:
        """Calculate confidence intervals for predictions."""
        # Simplified confidence intervals based on model error
        rmse = self.model_metrics.get(model_key, {}).get('rmse', 0.1)
        
        intervals = []
        for pred in predictions:
            # 95% confidence interval: ±2 * RMSE
            margin = 2 * rmse
            intervals.append((max(0, pred - margin), pred + margin))
        
        return intervals
    
    async def _predict_scaling_needs(self) -> Optional[ScalingPrediction]:
        """Predict scaling needs based on forecasts."""
        try:
            # Get CPU forecast
            cpu_forecast = self.current_forecasts.get('system_cpu')
            if not cpu_forecast:
                return None
            
            # Find peak CPU usage in next few hours
            peak_cpu = max(cpu_forecast.predictions[:6])  # Next 6 hours
            
            # Determine scaling recommendation
            current_nodes = 3  # Assume current node count
            recommended_nodes = current_nodes
            
            if peak_cpu > 90:
                recommended_nodes = min(current_nodes + 2, 10)
                urgency = "critical"
                reasoning = f"Critical CPU usage predicted: {peak_cpu:.1f}%"
            elif peak_cpu > 80:
                recommended_nodes = min(current_nodes + 1, 10)
                urgency = "high"
                reasoning = f"High CPU usage predicted: {peak_cpu:.1f}%"
            elif peak_cpu < 30:
                recommended_nodes = max(current_nodes - 1, 1)
                urgency = "low"
                reasoning = f"Low CPU usage predicted: {peak_cpu:.1f}%, can scale down"
            else:
                urgency = "medium"
                reasoning = f"Moderate CPU usage predicted: {peak_cpu:.1f}%"
            
            # Calculate confidence based on forecast accuracy
            confidence = cpu_forecast.accuracy_score
            
            return ScalingPrediction(
                predicted_load=peak_cpu,
                recommended_nodes=recommended_nodes,
                confidence=confidence,
                time_horizon=360,  # 6 hours
                reasoning=reasoning,
                urgency=urgency
            )
        
        except Exception as e:
            logger.error("Failed to predict scaling needs", error=str(e))
            return None
    
    async def _detect_anomalies(self) -> List[AnomalyDetection]:
        """Detect anomalies in current metrics."""
        anomalies = []
        
        # Check system metrics
        system_anomalies = await self._detect_system_anomalies()
        anomalies.extend(system_anomalies)
        
        # Check tenant metrics
        tenant_anomalies = await self._detect_tenant_anomalies()
        anomalies.extend(tenant_anomalies)
        
        return anomalies
    
    async def _detect_system_anomalies(self) -> List[AnomalyDetection]:
        """Detect anomalies in system metrics."""
        anomalies = []
        
        if 'system' not in self.historical_data or len(self.historical_data['system']) < 24:
            return anomalies
        
        # Get recent system data
        recent_data = self.historical_data['system'][-24:]  # Last 24 hours
        
        # Check CPU usage
        cpu_values = [d['cpu_usage'] for d in recent_data]
        current_cpu = cpu_values[-1]
        expected_cpu = np.mean(cpu_values[:-1])  # Exclude current value
        cpu_std = np.std(cpu_values[:-1])
        
        if cpu_std > 0:
            cpu_z_score = abs(current_cpu - expected_cpu) / cpu_std
            if cpu_z_score > self.anomaly_threshold:
                severity = "high" if cpu_z_score > 3 else "medium"
                anomalies.append(AnomalyDetection(
                    metric_name="cpu_usage",
                    tenant_id=None,
                    current_value=current_cpu,
                    expected_value=expected_cpu,
                    anomaly_score=cpu_z_score,
                    severity=severity,
                    description=f"CPU usage anomaly: {current_cpu:.1f}% (expected ~{expected_cpu:.1f}%)"
                ))
        
        # Check memory usage
        memory_values = [d['memory_usage'] for d in recent_data]
        current_memory = memory_values[-1]
        expected_memory = np.mean(memory_values[:-1])
        memory_std = np.std(memory_values[:-1])
        
        if memory_std > 0:
            memory_z_score = abs(current_memory - expected_memory) / memory_std
            if memory_z_score > self.anomaly_threshold:
                severity = "high" if memory_z_score > 3 else "medium"
                anomalies.append(AnomalyDetection(
                    metric_name="memory_usage",
                    tenant_id=None,
                    current_value=current_memory,
                    expected_value=expected_memory,
                    anomaly_score=memory_z_score,
                    severity=severity,
                    description=f"Memory usage anomaly: {current_memory:.1f}% (expected ~{expected_memory:.1f}%)"
                ))
        
        return anomalies
    
    async def _detect_tenant_anomalies(self) -> List[AnomalyDetection]:
        """Detect anomalies in tenant metrics."""
        anomalies = []
        
        for tenant_id in self.cache_manager.tenants.keys():
            history_key = f'tenant_{tenant_id}'
            
            if history_key not in self.historical_data or len(self.historical_data[history_key]) < 24:
                continue
            
            # Get recent tenant data
            recent_data = self.historical_data[history_key][-24:]
            
            # Check hit ratio
            hit_ratios = [d['hit_ratio'] for d in recent_data]
            current_hit_ratio = hit_ratios[-1]
            expected_hit_ratio = np.mean(hit_ratios[:-1])
            hit_ratio_std = np.std(hit_ratios[:-1])
            
            if hit_ratio_std > 0:
                hit_ratio_z_score = abs(current_hit_ratio - expected_hit_ratio) / hit_ratio_std
                if hit_ratio_z_score > self.anomaly_threshold:
                    severity = "high" if hit_ratio_z_score > 3 else "medium"
                    anomalies.append(AnomalyDetection(
                        metric_name="hit_ratio",
                        tenant_id=tenant_id,
                        current_value=current_hit_ratio,
                        expected_value=expected_hit_ratio,
                        anomaly_score=hit_ratio_z_score,
                        severity=severity,
                        description=f"Hit ratio anomaly for tenant {tenant_id}: {current_hit_ratio:.2f} (expected ~{expected_hit_ratio:.2f})"
                    ))
        
        return anomalies
    
    async def _retrain_models(self):
        """Retrain all models with updated data."""
        logger.info("Retraining prediction models")
        
        for model_key in list(self.models.keys()):
            try:
                # Extract history key and metric from model key
                parts = model_key.split('_', 2)
                if len(parts) >= 3:
                    history_key = f"{parts[0]}_{parts[1]}"
                    metric_name = parts[2]
                    
                    if history_key in self.historical_data:
                        history = self.historical_data[history_key]
                        if len(history) >= 50:
                            df = pd.DataFrame(history)
                            features = self._extract_features(df)
                            targets = df[metric_name].values
                            
                            if len(features) >= 20:
                                await self._train_model(model_key, features, targets)
            
            except Exception as e:
                logger.error("Failed to retrain model",
                            model_key=model_key,
                            error=str(e))
    
    async def _cleanup_old_predictions(self):
        """Clean up old predictions and anomalies."""
        current_time = time.time()
        cutoff_time = current_time - 86400  # 24 hours
        
        # Remove old scaling predictions
        self.scaling_predictions = [
            pred for pred in self.scaling_predictions
            if pred.time_horizon > 0  # Keep active predictions
        ]
        
        # Remove old anomalies
        self.detected_anomalies = [
            anomaly for anomaly in self.detected_anomalies
            if current_time - anomaly.anomaly_score < 3600  # Keep recent anomalies
        ]
    
    async def _initialize_models(self):
        """Initialize ML models."""
        # Models will be created on-demand when enough data is available
        pass
    
    async def _load_historical_data(self):
        """Load historical data from persistent storage."""
        # In a real implementation, this would load from database/file
        # For now, we start with empty data
        pass
    
    def get_agent_info(self) -> AgentInfo:
        """Get current agent information."""
        return AgentInfo(
            name="PredictionAgent",
            status="running" if self.is_running else "stopped",
            last_activity=time.time(),
            metrics={
                'active_forecasts': len(self.current_forecasts),
                'scaling_predictions': len(self.scaling_predictions),
                'detected_anomalies': len(self.detected_anomalies),
                'trained_models': len(self.models),
                'avg_model_accuracy': np.mean([metrics.get('mae', 0) for metrics in self.model_metrics.values()]) if self.model_metrics else 0.0
            }
        ) 