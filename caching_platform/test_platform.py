#!/usr/bin/env python3
"""Simple test script to verify the caching platform functionality."""

import asyncio
import sys
import os

# Add the package to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from caching_platform.config.settings import get_settings
from caching_platform.core.orchestrator import CacheOrchestrator
from rich.console import Console

console = Console()

async def test_platform():
    """Test the caching platform functionality."""
    console.print("[bold blue]Testing OpenAI-Style Caching Platform[/bold blue]")
    
    try:
        # Initialize settings
        console.print("[yellow]1. Initializing settings...[/yellow]")
        settings = get_settings()
        console.print(f"[green]✓ Settings loaded: {settings.platform_name}[/green]")
        
        # Initialize orchestrator
        console.print("[yellow]2. Initializing orchestrator...[/yellow]")
        orchestrator = CacheOrchestrator(settings)
        success = await orchestrator.initialize()
        
        if not success:
            console.print("[red]✗ Failed to initialize orchestrator[/red]")
            return False
        
        console.print("[green]✓ Orchestrator initialized successfully[/green]")
        
        # Start orchestrator
        console.print("[yellow]3. Starting orchestrator...[/yellow]")
        success = await orchestrator.start()
        
        if not success:
            console.print("[red]✗ Failed to start orchestrator[/red]")
            return False
        
        console.print("[green]✓ Orchestrator started successfully[/green]")
        
        # Test basic operations
        console.print("[yellow]4. Testing basic operations...[/yellow]")
        
        # Create a test tenant
        result = await orchestrator.execute_command('create_tenant', {
            'name': 'test_tenant',
            'quota_memory_mb': 512,
            'quota_requests_per_second': 1000,
            'quota_connections': 50
        })
        
        if result.get('success'):
            console.print("[green]✓ Test tenant created successfully[/green]")
        else:
            console.print(f"[red]✗ Failed to create test tenant: {result.get('error')}[/red]")
        
        # Test cache operations
        result = await orchestrator.execute_command('cache_set', {
            'tenant': 'test_tenant',
            'key': 'test_key',
            'value': 'test_value',
            'ttl': 3600
        })
        
        if result.get('success'):
            console.print("[green]✓ Cache set operation successful[/green]")
        else:
            console.print(f"[red]✗ Cache set operation failed: {result.get('error')}[/red]")
        
        # Get cache value
        result = await orchestrator.execute_command('cache_get', {
            'tenant': 'test_tenant',
            'key': 'test_key'
        })
        
        if result.get('success'):
            value = result.get('value')
            console.print(f"[green]✓ Cache get operation successful: {value}[/green]")
        else:
            console.print(f"[red]✗ Cache get operation failed: {result.get('error')}[/red]")
        
        # Get system status
        console.print("[yellow]5. Getting system status...[/yellow]")
        status = await orchestrator.get_system_status()
        
        if status:
            console.print("[green]✓ System status retrieved successfully[/green]")
            for component, info in status.items():
                status_str = info.get('status', 'unknown')
                console.print(f"  {component}: {status_str}")
        else:
            console.print("[red]✗ Failed to get system status[/red]")
        
        # Get metrics
        console.print("[yellow]6. Getting metrics...[/yellow]")
        result = await orchestrator.execute_command('get_metrics', {
            'tenant': 'all',
            'limit': 10
        })
        
        if result.get('success'):
            console.print("[green]✓ Metrics retrieved successfully[/green]")
        else:
            console.print(f"[red]✗ Failed to get metrics: {result.get('error')}[/red]")
        
        # Shutdown
        console.print("[yellow]7. Shutting down...[/yellow]")
        await orchestrator.shutdown()
        console.print("[green]✓ Platform shutdown successfully[/green]")
        
        console.print("[bold green]All tests passed! Platform is working correctly.[/bold green]")
        return True
        
    except Exception as e:
        console.print(f"[red]✗ Test failed with error: {e}[/red]")
        return False

def main():
    """Main test function."""
    console.print("[bold blue]OpenAI-Style Caching Platform - Test Suite[/bold blue]")
    console.print("=" * 60)
    
    success = asyncio.run(test_platform())
    
    if success:
        console.print("\n[bold green]Platform test completed successfully![/bold green]")
        sys.exit(0)
    else:
        console.print("\n[bold red]Platform test failed![/bold red]")
        sys.exit(1)

if __name__ == "__main__":
    main() 