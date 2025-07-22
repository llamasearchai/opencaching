"""Configuration management for the caching platform."""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from pydantic_settings import BaseSettings
from pydantic import validator


@dataclass
class RedisConfig:
    """Redis cluster configuration."""
    host: str = "localhost"
    port: int = 6379
    password: Optional[str] = None
    db: int = 0
    max_connections: int = 100
    connection_timeout: float = 5.0
    read_timeout: float = 30.0
    write_timeout: float = 30.0
    retry_on_timeout: bool = True
    health_check_interval: int = 30
    cluster_mode: bool = False
    cluster_nodes: List[str] = field(default_factory=list)


@dataclass
class ScalingConfig:
    """Auto-scaling configuration."""
    enabled: bool = True
    min_nodes: int = 3
    max_nodes: int = 20
    target_cpu_percent: float = 70.0
    target_memory_percent: float = 80.0
    scale_up_threshold: float = 85.0
    scale_down_threshold: float = 30.0
    scale_up_cooldown: int = 300
    scale_down_cooldown: int = 600
    prediction_window: int = 3600


@dataclass
class MonitoringConfig:
    """Monitoring and metrics configuration."""
    metrics_interval: int = 30
    health_check_interval: int = 10
    alert_thresholds: Dict[str, float] = field(default_factory=lambda: {
        "cpu_usage": 85.0,
        "memory_usage": 90.0,
        "response_time": 100.0,
        "error_rate": 5.0
    })
    prometheus_enabled: bool = True
    prometheus_port: int = 9090
    grafana_enabled: bool = True
    grafana_port: int = 3000


@dataclass
class SecurityConfig:
    """Security configuration."""
    authentication_enabled: bool = True
    jwt_secret: str = "your-secret-key-change-in-production"
    jwt_expiry_hours: int = 24
    encryption_enabled: bool = True
    encryption_key: str = "your-encryption-key-change-in-production"
    audit_logging: bool = True
    rate_limiting_enabled: bool = True
    max_requests_per_minute: int = 1000


@dataclass
class TenantConfig:
    """Multi-tenant configuration."""
    default_memory_mb: int = 512
    default_requests_per_second: int = 100
    default_connections: int = 50
    isolation_level: str = "strict"
    quota_enforcement: bool = True
    billing_enabled: bool = True


class Settings(BaseSettings):
    """Main application settings."""
    
    # Platform configuration
    platform_name: str = "OpenAI-Style Caching Platform"
    environment: str = "development"
    debug: bool = False
    log_level: str = "INFO"
    
    # Service configuration
    host: str = "0.0.0.0"
    port: int = 8080
    workers: int = 4
    
    # Redis configuration
    redis: RedisConfig = field(default_factory=RedisConfig)
    
    # Scaling configuration
    scaling: ScalingConfig = field(default_factory=ScalingConfig)
    
    # Monitoring configuration
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    
    # Security configuration
    security: SecurityConfig = field(default_factory=SecurityConfig)
    
    # Tenant configuration
    tenants: TenantConfig = field(default_factory=TenantConfig)
    
    # Kubernetes configuration
    kubernetes_enabled: bool = False
    kubernetes_namespace: str = "caching-platform"
    kubernetes_config_path: Optional[str] = None
    
    # File paths
    config_file: Optional[str] = None
    log_file: Optional[str] = None
    backup_dir: str = "./backups"
    data_dir: str = "./data"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    @validator("environment")
    def validate_environment(cls, v):
        valid_environments = ["development", "staging", "production"]
        if v not in valid_environments:
            raise ValueError(f"Environment must be one of {valid_environments}")
        return v
    
    @validator("log_level")
    def validate_log_level(cls, v):
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of {valid_levels}")
        return v.upper()


class ConfigManager:
    """Configuration manager for dynamic configuration updates."""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file
        self.settings = Settings()
        self._load_config()
    
    def _load_config(self):
        """Load configuration from file if specified."""
        if self.config_file and Path(self.config_file).exists():
            with open(self.config_file, 'r') as f:
                config_data = yaml.safe_load(f)
                self._update_settings(config_data)
    
    def _update_settings(self, config_data: Dict[str, Any]):
        """Update settings from configuration data."""
        for key, value in config_data.items():
            if hasattr(self.settings, key):
                setattr(self.settings, key, value)
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a specific setting value."""
        return getattr(self.settings, key, default)
    
    def update_setting(self, key: str, value: Any) -> bool:
        """Update a specific setting value."""
        if hasattr(self.settings, key):
            setattr(self.settings, key, value)
            return True
        return False
    
    def reload_config(self):
        """Reload configuration from file."""
        self._load_config()
    
    def export_config(self, file_path: str):
        """Export current configuration to file."""
        config_data = self.settings.dict()
        with open(file_path, 'w') as f:
            yaml.dump(config_data, f, default_flow_style=False)
    
    def get_redis_config(self) -> RedisConfig:
        """Get Redis configuration."""
        return self.settings.redis
    
    def get_scaling_config(self) -> ScalingConfig:
        """Get scaling configuration."""
        return self.settings.scaling
    
    def get_monitoring_config(self) -> MonitoringConfig:
        """Get monitoring configuration."""
        return self.settings.monitoring
    
    def get_security_config(self) -> SecurityConfig:
        """Get security configuration."""
        return self.settings.security
    
    def get_tenant_config(self) -> TenantConfig:
        """Get tenant configuration."""
        return self.settings.tenants


# Global configuration instance
config_manager = ConfigManager()


def get_settings() -> Settings:
    """Get the current settings."""
    return config_manager.settings


def get_config_manager() -> ConfigManager:
    """Get the configuration manager."""
    return config_manager 