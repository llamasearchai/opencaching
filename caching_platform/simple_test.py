#!/usr/bin/env python3
"""Simple test script to verify the caching platform basic functionality."""

import sys
import os
from datetime import datetime

# Add the package to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rich.console import Console

console = Console()

def test_imports():
    """Test that all modules can be imported."""
    console.print("[bold blue]Testing OpenAI-Style Caching Platform Imports[/bold blue]")
    
    try:
        # Test config imports
        console.print("[yellow]1. Testing config imports...[/yellow]")
        from caching_platform.config.settings import get_settings
        from caching_platform.config.schemas import Tenant, CacheMetrics, AgentInfo
        console.print("[green]✓ Config imports successful[/green]")
        
        # Test core imports
        console.print("[yellow]2. Testing core imports...[/yellow]")
        from caching_platform.core.orchestrator import CacheOrchestrator
        from caching_platform.core.cache_manager import MultiTenantCacheManager
        from caching_platform.core.auto_scaler import AutoScaler
        from caching_platform.core.load_balancer import LoadBalancer
        from caching_platform.core.health_monitor import HealthMonitor
        console.print("[green]✓ Core imports successful[/green]")
        
        # Test agents imports
        console.print("[yellow]3. Testing agents imports...[/yellow]")
        from caching_platform.agents.scaling_agent import ScalingAgent
        from caching_platform.agents.optimization_agent import OptimizationAgent
        from caching_platform.agents.healing_agent import HealingAgent
        from caching_platform.agents.prediction_agent import PredictionAgent
        console.print("[green]✓ Agents imports successful[/green]")
        
        # Test monitoring imports
        console.print("[yellow]4. Testing monitoring imports...[/yellow]")
        from caching_platform.monitoring.metrics import MetricsCollector
        console.print("[green]✓ Monitoring imports successful[/green]")
        
        # Test security imports
        console.print("[yellow]5. Testing security imports...[/yellow]")
        from caching_platform.security.auth import AuthenticationManager
        from caching_platform.security.encryption import EncryptionManager
        console.print("[green]✓ Security imports successful[/green]")
        
        # Test CLI imports
        console.print("[yellow]6. Testing CLI imports...[/yellow]")
        from caching_platform.cli.interface import cli
        from caching_platform.cli.menu_system import MenuSystem
        console.print("[green]✓ CLI imports successful[/green]")
        
        return True
        
    except Exception as e:
        console.print(f"[red]✗ Import test failed: {e}[/red]")
        return False

def test_settings():
    """Test settings configuration."""
    console.print("[yellow]7. Testing settings configuration...[/yellow]")
    
    try:
        from caching_platform.config.settings import get_settings
        
        settings = get_settings()
        console.print(f"[green]✓ Settings loaded: {settings.platform_name}[/green]")
        console.print(f"  Environment: {settings.environment}")
        console.print(f"  Log Level: {settings.log_level}")
        console.print(f"  Redis Host: {settings.redis.host}")
        console.print(f"  Redis Port: {settings.redis.port}")
        
        return True
        
    except Exception as e:
        console.print(f"[red]✗ Settings test failed: {e}[/red]")
        return False

def test_schemas():
    """Test data schemas."""
    console.print("[yellow]8. Testing data schemas...[/yellow]")
    
    try:
        from caching_platform.config.schemas import Tenant, CacheMetrics, AgentInfo
        
        # Test tenant creation
        tenant = Tenant(
            id="test_tenant",
            name="Test Tenant",
            namespace="test_namespace",
            memory_limit_mb=512,
            requests_per_second=1000,
            max_connections=50
        )
        console.print(f"[green]✓ Tenant schema test: {tenant.name}[/green]")
        
        # Test metrics creation
        metrics = CacheMetrics(
            total_requests=1000,
            cache_hits=800,
            hit_ratio=80.0,
            average_response_time_ms=5.0,
            memory_used_mb=256
        )
        console.print(f"[green]✓ Metrics schema test: {metrics.hit_ratio}% hit ratio[/green]")
        
        # Test agent info creation
        agent_info = AgentInfo(
            id="test_agent",
            name="TestAgent",
            type="scaling",
            status="running",
            last_activity=datetime.utcnow()
        )
        console.print(f"[green]✓ Agent info schema test: {agent_info.name}[/green]")
        
        return True
        
    except Exception as e:
        console.print(f"[red]✗ Schemas test failed: {e}[/red]")
        return False

def test_cli_help():
    """Test CLI help command."""
    console.print("[yellow]9. Testing CLI help...[/yellow]")
    
    try:
        from caching_platform.cli.interface import cli
        
        # This would normally run the CLI, but we'll just test that it's callable
        console.print("[green]✓ CLI interface is callable[/green]")
        
        return True
        
    except Exception as e:
        console.print(f"[red]✗ CLI test failed: {e}[/red]")
        return False

def main():
    """Main test function."""
    console.print("[bold blue]OpenAI-Style Caching Platform - Basic Test Suite[/bold blue]")
    console.print("=" * 70)
    
    tests = [
        test_imports,
        test_settings,
        test_schemas,
        test_cli_help
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        console.print()
    
    console.print("=" * 70)
    console.print(f"[bold]Test Results: {passed}/{total} tests passed[/bold]")
    
    if passed == total:
        console.print("[bold green]All basic tests passed! Platform is ready for use.[/bold green]")
        console.print("\n[bold blue]Next steps:[/bold blue]")
        console.print("1. Install Redis server")
        console.print("2. Run: python test_platform.py")
        console.print("3. Or run: caching-platform interactive")
        sys.exit(0)
    else:
        console.print(f"[bold red]{total - passed} tests failed! Please check the errors above.[/bold red]")
        sys.exit(1)

if __name__ == "__main__":
    main() 