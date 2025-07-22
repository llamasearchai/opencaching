"""Main CLI interface for the caching platform."""

import asyncio
import json
import sys
from typing import Optional, Dict, Any
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm
from rich.text import Text
import structlog

from ..config.settings import get_settings, ConfigManager
from ..core.orchestrator import CacheOrchestrator
from ..cli.menu_system import MenuSystem

console = Console()
logger = structlog.get_logger(__name__)

@click.group()
@click.option('--debug', is_flag=True, help='Enable debug logging')
@click.option('--config-file', type=click.Path(exists=True), help='Configuration file path')
@click.pass_context
def cli(ctx, debug: bool, config_file: Optional[str]):
    """OpenAI-Style Caching Infrastructure Platform CLI."""
    ctx.ensure_object(dict)
    ctx.obj['debug'] = debug
    ctx.obj['config_file'] = config_file
    
    # Configure logging
    if debug:
        structlog.configure(processors=[structlog.dev.ConsoleRenderer()])
    else:
        structlog.configure(processors=[structlog.processors.JSONRenderer()])

@cli.command()
@click.option('--port', default=8080, help='Port for the daemon server')
@click.option('--host', default='0.0.0.0', help='Host for the daemon server')
@click.option('--workers', default=4, help='Number of worker processes')
@click.pass_context
def daemon(ctx, port: int, host: str, workers: int):
    """Start the caching platform in daemon mode."""
    console.print(Panel.fit("Starting Caching Platform Daemon", style="bold blue"))
    
    async def run_daemon():
        try:
            # Initialize orchestrator
            settings = get_settings()
            orchestrator = CacheOrchestrator(settings)
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Initializing platform...", total=None)
                
                # Initialize platform
                success = await orchestrator.initialize()
                if not success:
                    console.print("[red]Failed to initialize platform[/red]")
                    return
                
                progress.update(task, description="Starting platform...")
                
                # Start platform
                success = await orchestrator.start()
                if not success:
                    console.print("[red]Failed to start platform[/red]")
                    return
                
                progress.update(task, description="Platform started successfully")
            
            console.print(f"[green]Platform daemon started on {host}:{port}[/green]")
            console.print("Press Ctrl+C to stop")
            
            # Keep running
            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                console.print("\n[yellow]Shutting down platform...[/yellow]")
                await orchestrator.shutdown()
                console.print("[green]Platform stopped[/green]")
        
        except Exception as e:
            console.print(f"[red]Error starting daemon: {e}[/red]")
            logger.error("Daemon startup failed", error=str(e))
    
    asyncio.run(run_daemon())

@cli.command()
@click.pass_context
def interactive(ctx):
    """Start interactive CLI mode."""
    console.print(Panel.fit("OpenAI-Style Caching Platform - Interactive Mode", style="bold blue"))
    
    async def run_interactive():
        try:
            # Initialize orchestrator
            settings = get_settings()
            orchestrator = CacheOrchestrator(settings)
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Initializing platform...", total=None)
                
                # Initialize platform
                success = await orchestrator.initialize()
                if not success:
                    console.print("[red]Failed to initialize platform[/red]")
                    return
                
                progress.update(task, description="Starting platform...")
                
                # Start platform
                success = await orchestrator.start()
                if not success:
                    console.print("[red]Failed to start platform[/red]")
                    return
                
                progress.update(task, description="Platform ready")
            
            # Start interactive menu
            menu_system = MenuSystem(orchestrator, console)
            await menu_system.run()
            
            # Shutdown
            await orchestrator.shutdown()
        
        except Exception as e:
            console.print(f"[red]Error in interactive mode: {e}[/red]")
            logger.error("Interactive mode failed", error=str(e))
    
    asyncio.run(run_interactive())

@cli.command()
@click.option('--format', 'output_format', default='table', type=click.Choice(['table', 'json']), help='Output format')
@click.pass_context
def status(ctx, output_format: str):
    """Show platform status."""
    async def get_status():
        try:
            settings = get_settings()
            orchestrator = CacheOrchestrator(settings)
            
            # Initialize without starting
            success = await orchestrator.initialize()
            if not success:
                return {"status": "error", "message": "Failed to initialize"}
            
            # Get system status
            status_info = await orchestrator.get_system_status()
            
            if output_format == 'json':
                console.print(json.dumps(status_info, indent=2, default=str))
            else:
                display_status_table(status_info)
        
        except Exception as e:
            console.print(f"[red]Error getting status: {e}[/red]")
    
    asyncio.run(get_status())

@cli.command()
@click.option('--name', required=True, help='Tenant name')
@click.option('--quota-memory', default=512, help='Memory quota in MB')
@click.option('--quota-requests', default=1000, help='Request rate quota')
@click.option('--quota-connections', default=50, help='Connection quota')
@click.pass_context
def create_tenant(ctx, name: str, quota_memory: int, quota_requests: int, quota_connections: int):
    """Create a new tenant."""
    async def create():
        try:
            settings = get_settings()
            orchestrator = CacheOrchestrator(settings)
            
            success = await orchestrator.initialize()
            if not success:
                console.print("[red]Failed to initialize platform[/red]")
                return
            
            # Create tenant
            result = await orchestrator.execute_command('create_tenant', {
                'name': name,
                'quota_memory_mb': quota_memory,
                'quota_requests_per_second': quota_requests,
                'quota_connections': quota_connections
            })
            
            if result.get('success'):
                console.print(f"[green]Tenant '{name}' created successfully[/green]")
                console.print(f"  Memory Quota: {quota_memory} MB")
                console.print(f"  Request Rate: {quota_requests} req/s")
                console.print(f"  Connections: {quota_connections}")
            else:
                console.print(f"[red]Failed to create tenant: {result.get('error', 'Unknown error')}[/red]")
        
        except Exception as e:
            console.print(f"[red]Error creating tenant: {e}[/red]")
    
    asyncio.run(create())

@cli.command()
@click.option('--name', required=True, help='Tenant name')
@click.pass_context
def delete_tenant(ctx, name: str):
    """Delete a tenant."""
    async def delete():
        try:
            settings = get_settings()
            orchestrator = CacheOrchestrator(settings)
            
            success = await orchestrator.initialize()
            if not success:
                console.print("[red]Failed to initialize platform[/red]")
                return
            
            # Confirm deletion
            if not Confirm.ask(f"Are you sure you want to delete tenant '{name}'?"):
                console.print("[yellow]Deletion cancelled[/yellow]")
                return
            
            # Delete tenant
            result = await orchestrator.execute_command('delete_tenant', {'name': name})
            
            if result.get('success'):
                console.print(f"[green]Tenant '{name}' deleted successfully[/green]")
            else:
                console.print(f"[red]Failed to delete tenant: {result.get('error', 'Unknown error')}[/red]")
        
        except Exception as e:
            console.print(f"[red]Error deleting tenant: {e}[/red]")
    
    asyncio.run(delete())

@cli.command()
@click.option('--format', 'output_format', default='table', type=click.Choice(['table', 'json']), help='Output format')
@click.pass_context
def list_tenants(ctx, output_format: str):
    """List all tenants."""
    async def list_tenants_async():
        try:
            settings = get_settings()
            orchestrator = CacheOrchestrator(settings)
            
            success = await orchestrator.initialize()
            if not success:
                console.print("[red]Failed to initialize platform[/red]")
                return
            
            # Get tenants
            result = await orchestrator.execute_command('list_tenants', {})
            
            if result.get('success'):
                tenants = result.get('tenants', [])
                
                if output_format == 'json':
                    console.print(json.dumps(tenants, indent=2, default=str))
                else:
                    display_tenants_table(tenants)
            else:
                console.print(f"[red]Failed to list tenants: {result.get('error', 'Unknown error')}[/red]")
        
        except Exception as e:
            console.print(f"[red]Error listing tenants: {e}[/red]")
    
    asyncio.run(list_tenants_async())

@cli.command()
@click.option('--tenant', required=True, help='Tenant name')
@click.option('--key', required=True, help='Cache key')
@click.option('--value', required=True, help='Cache value')
@click.option('--ttl', default=3600, help='TTL in seconds')
@click.pass_context
def cache_set(ctx, tenant: str, key: str, value: str, ttl: int):
    """Set a cache value."""
    async def set_value():
        try:
            settings = get_settings()
            orchestrator = CacheOrchestrator(settings)
            
            success = await orchestrator.initialize()
            if not success:
                console.print("[red]Failed to initialize platform[/red]")
                return
            
            # Set cache value
            result = await orchestrator.execute_command('cache_set', {
                'tenant': tenant,
                'key': key,
                'value': value,
                'ttl': ttl
            })
            
            if result.get('success'):
                console.print(f"[green]Cache value set successfully[/green]")
                console.print(f"  Tenant: {tenant}")
                console.print(f"  Key: {key}")
                console.print(f"  TTL: {ttl}s")
            else:
                console.print(f"[red]Failed to set cache value: {result.get('error', 'Unknown error')}[/red]")
        
        except Exception as e:
            console.print(f"[red]Error setting cache value: {e}[/red]")
    
    asyncio.run(set_value())

@cli.command()
@click.option('--tenant', required=True, help='Tenant name')
@click.option('--key', required=True, help='Cache key')
@click.pass_context
def cache_get(ctx, tenant: str, key: str):
    """Get a cache value."""
    async def get_value():
        try:
            settings = get_settings()
            orchestrator = CacheOrchestrator(settings)
            
            success = await orchestrator.initialize()
            if not success:
                console.print("[red]Failed to initialize platform[/red]")
                return
            
            # Get cache value
            result = await orchestrator.execute_command('cache_get', {
                'tenant': tenant,
                'key': key
            })
            
            if result.get('success'):
                value = result.get('value')
                console.print(f"[green]Cache value retrieved[/green]")
                console.print(f"  Tenant: {tenant}")
                console.print(f"  Key: {key}")
                console.print(f"  Value: {value}")
            else:
                console.print(f"[red]Failed to get cache value: {result.get('error', 'Unknown error')}[/red]")
        
        except Exception as e:
            console.print(f"[red]Error getting cache value: {e}[/red]")
    
    asyncio.run(get_value())

@cli.command()
@click.option('--tenant', required=True, help='Tenant name')
@click.option('--key', required=True, help='Cache key')
@click.pass_context
def cache_delete(ctx, tenant: str, key: str):
    """Delete a cache value."""
    async def delete_value():
        try:
            settings = get_settings()
            orchestrator = CacheOrchestrator(settings)
            
            success = await orchestrator.initialize()
            if not success:
                console.print("[red]Failed to initialize platform[/red]")
                return
            
            # Delete cache value
            result = await orchestrator.execute_command('cache_delete', {
                'tenant': tenant,
                'key': key
            })
            
            if result.get('success'):
                console.print(f"[green]Cache value deleted successfully[/green]")
                console.print(f"  Tenant: {tenant}")
                console.print(f"  Key: {key}")
            else:
                console.print(f"[red]Failed to delete cache value: {result.get('error', 'Unknown error')}[/red]")
        
        except Exception as e:
            console.print(f"[red]Error deleting cache value: {e}[/red]")
    
    asyncio.run(delete_value())

@cli.command()
@click.option('--tenant', default='all', help='Tenant name or "all"')
@click.option('--limit', default=100, help='Number of metrics to show')
@click.option('--format', 'output_format', default='table', type=click.Choice(['table', 'json']), help='Output format')
@click.pass_context
def metrics(ctx, tenant: str, limit: int, output_format: str):
    """Show platform metrics."""
    async def get_metrics():
        try:
            settings = get_settings()
            orchestrator = CacheOrchestrator(settings)
            
            success = await orchestrator.initialize()
            if not success:
                console.print("[red]Failed to initialize platform[/red]")
                return
            
            # Get metrics
            result = await orchestrator.execute_command('get_metrics', {
                'tenant': tenant,
                'limit': limit
            })
            
            if result.get('success'):
                metrics_data = result.get('metrics', {})
                
                if output_format == 'json':
                    console.print(json.dumps(metrics_data, indent=2, default=str))
                else:
                    display_metrics_table(metrics_data)
            else:
                console.print(f"[red]Failed to get metrics: {result.get('error', 'Unknown error')}[/red]")
        
        except Exception as e:
            console.print(f"[red]Error getting metrics: {e}[/red]")
    
    asyncio.run(get_metrics())

@cli.command()
@click.option('--config-file', type=click.Path(), help='Configuration file path')
@click.pass_context
def export_config(ctx, config_file: str):
    """Export current configuration."""
    try:
        config_manager = ConfigManager()
        config_data = config_manager.export_config()
        
        if config_file:
            with open(config_file, 'w') as f:
                json.dump(config_data, f, indent=2, default=str)
            console.print(f"[green]Configuration exported to {config_file}[/green]")
        else:
            console.print(json.dumps(config_data, indent=2, default=str))
    
    except Exception as e:
        console.print(f"[red]Error exporting configuration: {e}[/red]")

@cli.command()
@click.option('--config-file', type=click.Path(exists=True), required=True, help='Configuration file path')
@click.pass_context
def import_config(ctx, config_file: str):
    """Import configuration from file."""
    try:
        with open(config_file, 'r') as f:
            config_data = json.load(f)
        
        config_manager = ConfigManager()
        config_manager.update_config(config_data)
        
        console.print(f"[green]Configuration imported from {config_file}[/green]")
    
    except Exception as e:
        console.print(f"[red]Error importing configuration: {e}[/red]")

@cli.command()
@click.option('--load-test', is_flag=True, help='Run load test')
@click.option('--duration', default=300, help='Test duration in seconds')
@click.pass_context
def test(ctx, load_test: bool, duration: int):
    """Run platform tests."""
    async def run_tests():
        try:
            settings = get_settings()
            orchestrator = CacheOrchestrator(settings)
            
            success = await orchestrator.initialize()
            if not success:
                console.print("[red]Failed to initialize platform[/red]")
                return
            
            if load_test:
                console.print(f"[yellow]Running load test for {duration} seconds...[/yellow]")
                
                # Run load test
                result = await orchestrator.execute_command('load_test', {
                    'duration': duration
                })
                
                if result.get('success'):
                    test_results = result.get('results', {})
                    display_test_results(test_results)
                else:
                    console.print(f"[red]Load test failed: {result.get('error', 'Unknown error')}[/red]")
            else:
                # Run basic health check
                result = await orchestrator.execute_command('health_check', {})
                
                if result.get('success'):
                    console.print("[green]Health check passed[/green]")
                else:
                    console.print(f"[red]Health check failed: {result.get('error', 'Unknown error')}[/red]")
        
        except Exception as e:
            console.print(f"[red]Error running tests: {e}[/red]")
    
    asyncio.run(run_tests())

def display_status_table(status_info: Dict[str, Any]):
    """Display system status in a table."""
    table = Table(title="Platform Status")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Details", style="white")
    
    for component, info in status_info.items():
        status = info.get('status', 'unknown')
        details = info.get('details', '')
        
        status_style = "green" if status == "healthy" else "red" if status == "error" else "yellow"
        
        table.add_row(component, f"[{status_style}]{status}[/{status_style}]", str(details))
    
    console.print(table)

def display_tenants_table(tenants: list):
    """Display tenants in a table."""
    table = Table(title="Tenants")
    table.add_column("Name", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Memory Quota", style="white")
    table.add_column("Request Rate", style="white")
    table.add_column("Connections", style="white")
    
    for tenant in tenants:
        table.add_row(
            tenant.get('name', ''),
            tenant.get('status', ''),
            f"{tenant.get('quota_memory_mb', 0)} MB",
            f"{tenant.get('quota_requests_per_second', 0)} req/s",
            str(tenant.get('quota_connections', 0))
        )
    
    console.print(table)

def display_metrics_table(metrics_data: Dict[str, Any]):
    """Display metrics in a table."""
    table = Table(title="Platform Metrics")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="white")
    table.add_column("Unit", style="yellow")
    
    for metric, value in metrics_data.items():
        if isinstance(value, dict):
            for sub_metric, sub_value in value.items():
                table.add_row(f"{metric}.{sub_metric}", str(sub_value), "")
        else:
            table.add_row(metric, str(value), "")
    
    console.print(table)

def display_test_results(results: Dict[str, Any]):
    """Display test results in a table."""
    table = Table(title="Load Test Results")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="white")
    table.add_column("Unit", style="yellow")
    
    for metric, value in results.items():
        unit = ""
        if "latency" in metric.lower():
            unit = "ms"
        elif "throughput" in metric.lower():
            unit = "ops/s"
        elif "error" in metric.lower():
            unit = "%"
        
        table.add_row(metric, str(value), unit)
    
    console.print(table)

def main():
    """Main entry point for the CLI."""
    cli()

if __name__ == '__main__':
    main() 