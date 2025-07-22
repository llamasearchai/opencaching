"""Interactive menu system for the caching platform CLI."""

import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.text import Text
from rich.layout import Layout
from rich.live import Live
from rich.align import Align
import structlog

from ..core.orchestrator import CacheOrchestrator

logger = structlog.get_logger(__name__)

class MenuSystem:
    """Interactive menu system for the caching platform."""
    
    def __init__(self, orchestrator: CacheOrchestrator, console: Console):
        self.orchestrator = orchestrator
        self.console = console
        self.running = False
        
        # Menu options
        self.main_menu_options = [
            ("1", "Cluster Management", self.cluster_management_menu),
            ("2", "Tenant Management", self.tenant_management_menu),
            ("3", "Performance Monitoring", self.monitoring_menu),
            ("4", "Auto-Scaling Configuration", self.scaling_menu),
            ("5", "Security & Access Control", self.security_menu),
            ("6", "Metrics & Analytics", self.analytics_menu),
            ("7", "Health Checks & Diagnostics", self.health_menu),
            ("8", "Agent Status & Controls", self.agents_menu),
            ("9", "Configuration Management", self.config_menu),
            ("0", "Exit", self.exit_menu)
        ]
    
    async def run(self):
        """Run the interactive menu system."""
        self.running = True
        
        while self.running:
            try:
                await self.show_main_menu()
            except KeyboardInterrupt:
                self.console.print("\n[yellow]Exiting...[/yellow]")
                break
            except Exception as e:
                self.console.print(f"[red]Error in menu system: {e}[/red]")
                logger.error("Menu system error", error=str(e))
                await asyncio.sleep(1)
    
    async def show_main_menu(self):
        """Display the main menu."""
        self.console.clear()
        
        # Header
        header = Panel.fit(
            "OpenAI-Style Caching Platform - Interactive CLI",
            style="bold blue"
        )
        self.console.print(header)
        
        # Status panel
        await self.show_status_panel()
        
        # Menu options
        menu_text = Text()
        menu_text.append("\nMain Menu:\n", style="bold white")
        
        for option, description, _ in self.main_menu_options:
            menu_text.append(f"  {option}. {description}\n", style="cyan")
        
        menu_panel = Panel(menu_text, title="Navigation", border_style="green")
        self.console.print(menu_panel)
        
        # Get user choice
        choice = Prompt.ask("Select an option", choices=[opt[0] for opt in self.main_menu_options])
        
        # Execute selected option
        for option, _, handler in self.main_menu_options:
            if choice == option:
                await handler()
                break
    
    async def show_status_panel(self):
        """Show current platform status."""
        try:
            status = await self.orchestrator.get_system_status()
            
            status_text = Text()
            status_text.append("Platform Status:\n", style="bold")
            
            for component, info in status.items():
                status_str = info.get('status', 'unknown')
                status_style = "green" if status_str == "healthy" else "red" if status_str == "error" else "yellow"
                status_text.append(f"  {component}: ", style="white")
                status_text.append(f"{status_str}\n", style=status_style)
            
            status_panel = Panel(status_text, title="System Status", border_style="blue")
            self.console.print(status_panel)
        
        except Exception as e:
            self.console.print(f"[red]Error getting status: {e}[/red]")
    
    async def cluster_management_menu(self):
        """Cluster management submenu."""
        while True:
            self.console.clear()
            self.console.print(Panel.fit("Cluster Management", style="bold blue"))
            
            options = [
                ("1", "View Cluster Status"),
                ("2", "Initialize Cluster"),
                ("3", "Scale Cluster"),
                ("4", "Cluster Configuration"),
                ("0", "Back to Main Menu")
            ]
            
            for option, description in options:
                self.console.print(f"  {option}. {description}")
            
            choice = Prompt.ask("Select option", choices=[opt[0] for opt in options])
            
            if choice == "0":
                break
            elif choice == "1":
                await self.view_cluster_status()
            elif choice == "2":
                await self.initialize_cluster()
            elif choice == "3":
                await self.scale_cluster()
            elif choice == "4":
                await self.cluster_configuration()
            
            if choice != "0":
                Prompt.ask("\nPress Enter to continue")
    
    async def tenant_management_menu(self):
        """Tenant management submenu."""
        while True:
            self.console.clear()
            self.console.print(Panel.fit("Tenant Management", style="bold blue"))
            
            options = [
                ("1", "List Tenants"),
                ("2", "Create Tenant"),
                ("3", "Delete Tenant"),
                ("4", "View Tenant Details"),
                ("5", "Modify Tenant Quotas"),
                ("0", "Back to Main Menu")
            ]
            
            for option, description in options:
                self.console.print(f"  {option}. {description}")
            
            choice = Prompt.ask("Select option", choices=[opt[0] for opt in options])
            
            if choice == "0":
                break
            elif choice == "1":
                await self.list_tenants()
            elif choice == "2":
                await self.create_tenant()
            elif choice == "3":
                await self.delete_tenant()
            elif choice == "4":
                await self.view_tenant_details()
            elif choice == "5":
                await self.modify_tenant_quotas()
            
            if choice != "0":
                Prompt.ask("\nPress Enter to continue")
    
    async def monitoring_menu(self):
        """Performance monitoring submenu."""
        while True:
            self.console.clear()
            self.console.print(Panel.fit("Performance Monitoring", style="bold blue"))
            
            options = [
                ("1", "Real-time Metrics"),
                ("2", "Performance Dashboard"),
                ("3", "Alerts & Notifications"),
                ("4", "Historical Analysis"),
                ("0", "Back to Main Menu")
            ]
            
            for option, description in options:
                self.console.print(f"  {option}. {description}")
            
            choice = Prompt.ask("Select option", choices=[opt[0] for opt in options])
            
            if choice == "0":
                break
            elif choice == "1":
                await self.real_time_metrics()
            elif choice == "2":
                await self.performance_dashboard()
            elif choice == "3":
                await self.alerts_notifications()
            elif choice == "4":
                await self.historical_analysis()
            
            if choice != "0":
                Prompt.ask("\nPress Enter to continue")
    
    async def scaling_menu(self):
        """Auto-scaling configuration submenu."""
        while True:
            self.console.clear()
            self.console.print(Panel.fit("Auto-Scaling Configuration", style="bold blue"))
            
            options = [
                ("1", "View Scaling Status"),
                ("2", "Configure Scaling Rules"),
                ("3", "Manual Scaling"),
                ("4", "Scaling History"),
                ("0", "Back to Main Menu")
            ]
            
            for option, description in options:
                self.console.print(f"  {option}. {description}")
            
            choice = Prompt.ask("Select option", choices=[opt[0] for opt in options])
            
            if choice == "0":
                break
            elif choice == "1":
                await self.view_scaling_status()
            elif choice == "2":
                await self.configure_scaling_rules()
            elif choice == "3":
                await self.manual_scaling()
            elif choice == "4":
                await self.scaling_history()
            
            if choice != "0":
                Prompt.ask("\nPress Enter to continue")
    
    async def security_menu(self):
        """Security and access control submenu."""
        while True:
            self.console.clear()
            self.console.print(Panel.fit("Security & Access Control", style="bold blue"))
            
            options = [
                ("1", "User Management"),
                ("2", "API Key Management"),
                ("3", "Access Logs"),
                ("4", "Security Settings"),
                ("0", "Back to Main Menu")
            ]
            
            for option, description in options:
                self.console.print(f"  {option}. {description}")
            
            choice = Prompt.ask("Select option", choices=[opt[0] for opt in options])
            
            if choice == "0":
                break
            elif choice == "1":
                await self.user_management()
            elif choice == "2":
                await self.api_key_management()
            elif choice == "3":
                await self.access_logs()
            elif choice == "4":
                await self.security_settings()
            
            if choice != "0":
                Prompt.ask("\nPress Enter to continue")
    
    async def analytics_menu(self):
        """Metrics and analytics submenu."""
        while True:
            self.console.clear()
            self.console.print(Panel.fit("Metrics & Analytics", style="bold blue"))
            
            options = [
                ("1", "Cache Performance"),
                ("2", "Tenant Analytics"),
                ("3", "System Analytics"),
                ("4", "Custom Reports"),
                ("0", "Back to Main Menu")
            ]
            
            for option, description in options:
                self.console.print(f"  {option}. {description}")
            
            choice = Prompt.ask("Select option", choices=[opt[0] for opt in options])
            
            if choice == "0":
                break
            elif choice == "1":
                await self.cache_performance()
            elif choice == "2":
                await self.tenant_analytics()
            elif choice == "3":
                await self.system_analytics()
            elif choice == "4":
                await self.custom_reports()
            
            if choice != "0":
                Prompt.ask("\nPress Enter to continue")
    
    async def health_menu(self):
        """Health checks and diagnostics submenu."""
        while True:
            self.console.clear()
            self.console.print(Panel.fit("Health Checks & Diagnostics", style="bold blue"))
            
            options = [
                ("1", "System Health Check"),
                ("2", "Component Diagnostics"),
                ("3", "Network Diagnostics"),
                ("4", "Performance Tests"),
                ("0", "Back to Main Menu")
            ]
            
            for option, description in options:
                self.console.print(f"  {option}. {description}")
            
            choice = Prompt.ask("Select option", choices=[opt[0] for opt in options])
            
            if choice == "0":
                break
            elif choice == "1":
                await self.system_health_check()
            elif choice == "2":
                await self.component_diagnostics()
            elif choice == "3":
                await self.network_diagnostics()
            elif choice == "4":
                await self.performance_tests()
            
            if choice != "0":
                Prompt.ask("\nPress Enter to continue")
    
    async def agents_menu(self):
        """Agent status and controls submenu."""
        while True:
            self.console.clear()
            self.console.print(Panel.fit("Agent Status & Controls", style="bold blue"))
            
            options = [
                ("1", "View Agent Status"),
                ("2", "Control Agents"),
                ("3", "Agent Logs"),
                ("4", "Agent Configuration"),
                ("0", "Back to Main Menu")
            ]
            
            for option, description in options:
                self.console.print(f"  {option}. {description}")
            
            choice = Prompt.ask("Select option", choices=[opt[0] for opt in options])
            
            if choice == "0":
                break
            elif choice == "1":
                await self.view_agent_status()
            elif choice == "2":
                await self.control_agents()
            elif choice == "3":
                await self.agent_logs()
            elif choice == "4":
                await self.agent_configuration()
            
            if choice != "0":
                Prompt.ask("\nPress Enter to continue")
    
    async def config_menu(self):
        """Configuration management submenu."""
        while True:
            self.console.clear()
            self.console.print(Panel.fit("Configuration Management", style="bold blue"))
            
            options = [
                ("1", "View Configuration"),
                ("2", "Export Configuration"),
                ("3", "Import Configuration"),
                ("4", "Edit Configuration"),
                ("0", "Back to Main Menu")
            ]
            
            for option, description in options:
                self.console.print(f"  {option}. {description}")
            
            choice = Prompt.ask("Select option", choices=[opt[0] for opt in options])
            
            if choice == "0":
                break
            elif choice == "1":
                await self.view_configuration()
            elif choice == "2":
                await self.export_configuration()
            elif choice == "3":
                await self.import_configuration()
            elif choice == "4":
                await self.edit_configuration()
            
            if choice != "0":
                Prompt.ask("\nPress Enter to continue")
    
    async def exit_menu(self):
        """Exit the menu system."""
        if Confirm.ask("Are you sure you want to exit?"):
            self.running = False
    
    # Implementation of menu actions
    
    async def view_cluster_status(self):
        """View cluster status."""
        try:
            result = await self.orchestrator.execute_command('get_cluster_status', {})
            if result.get('success'):
                status = result.get('status', {})
                
                table = Table(title="Cluster Status")
                table.add_column("Component", style="cyan")
                table.add_column("Status", style="green")
                table.add_column("Details", style="white")
                
                for component, info in status.items():
                    table.add_row(component, info.get('status', 'unknown'), str(info.get('details', '')))
                
                self.console.print(table)
            else:
                self.console.print(f"[red]Failed to get cluster status: {result.get('error')}[/red]")
        except Exception as e:
            self.console.print(f"[red]Error viewing cluster status: {e}[/red]")
    
    async def initialize_cluster(self):
        """Initialize cluster."""
        try:
            nodes = IntPrompt.ask("Number of nodes", default=3)
            memory = IntPrompt.ask("Memory per node (MB)", default=2048)
            
            if Confirm.ask(f"Initialize cluster with {nodes} nodes, {memory}MB each?"):
                result = await self.orchestrator.execute_command('init_cluster', {
                    'nodes': nodes,
                    'memory': memory
                })
                
                if result.get('success'):
                    self.console.print("[green]Cluster initialized successfully[/green]")
                else:
                    self.console.print(f"[red]Failed to initialize cluster: {result.get('error')}[/red]")
        except Exception as e:
            self.console.print(f"[red]Error initializing cluster: {e}[/red]")
    
    async def scale_cluster(self):
        """Scale cluster."""
        try:
            action = Prompt.ask("Scale action", choices=["up", "down"])
            nodes = IntPrompt.ask("Number of nodes")
            
            result = await self.orchestrator.execute_command('scale_cluster', {
                'action': action,
                'nodes': nodes
            })
            
            if result.get('success'):
                self.console.print(f"[green]Cluster scaled {action} successfully[/green]")
            else:
                self.console.print(f"[red]Failed to scale cluster: {result.get('error')}[/red]")
        except Exception as e:
            self.console.print(f"[red]Error scaling cluster: {e}[/red]")
    
    async def cluster_configuration(self):
        """View cluster configuration."""
        try:
            result = await self.orchestrator.execute_command('get_cluster_config', {})
            if result.get('success'):
                config = result.get('config', {})
                
                table = Table(title="Cluster Configuration")
                table.add_column("Setting", style="cyan")
                table.add_column("Value", style="white")
                
                for setting, value in config.items():
                    table.add_row(setting, str(value))
                
                self.console.print(table)
            else:
                self.console.print(f"[red]Failed to get cluster config: {result.get('error')}[/red]")
        except Exception as e:
            self.console.print(f"[red]Error viewing cluster config: {e}[/red]")
    
    async def list_tenants(self):
        """List tenants."""
        try:
            result = await self.orchestrator.execute_command('list_tenants', {})
            if result.get('success'):
                tenants = result.get('tenants', [])
                
                table = Table(title="Tenants")
                table.add_column("Name", style="cyan")
                table.add_column("Status", style="green")
                table.add_column("Memory Quota", style="white")
                table.add_column("Request Rate", style="white")
                
                for tenant in tenants:
                    table.add_row(
                        tenant.get('name', ''),
                        tenant.get('status', ''),
                        f"{tenant.get('quota_memory_mb', 0)} MB",
                        f"{tenant.get('quota_requests_per_second', 0)} req/s"
                    )
                
                self.console.print(table)
            else:
                self.console.print(f"[red]Failed to list tenants: {result.get('error')}[/red]")
        except Exception as e:
            self.console.print(f"[red]Error listing tenants: {e}[/red]")
    
    async def create_tenant(self):
        """Create a new tenant."""
        try:
            name = Prompt.ask("Tenant name")
            memory_quota = IntPrompt.ask("Memory quota (MB)", default=512)
            request_rate = IntPrompt.ask("Request rate quota (req/s)", default=1000)
            connections = IntPrompt.ask("Connection quota", default=50)
            
            result = await self.orchestrator.execute_command('create_tenant', {
                'name': name,
                'quota_memory_mb': memory_quota,
                'quota_requests_per_second': request_rate,
                'quota_connections': connections
            })
            
            if result.get('success'):
                self.console.print(f"[green]Tenant '{name}' created successfully[/green]")
            else:
                self.console.print(f"[red]Failed to create tenant: {result.get('error')}[/red]")
        except Exception as e:
            self.console.print(f"[red]Error creating tenant: {e}[/red]")
    
    async def delete_tenant(self):
        """Delete a tenant."""
        try:
            name = Prompt.ask("Tenant name to delete")
            
            if Confirm.ask(f"Are you sure you want to delete tenant '{name}'?"):
                result = await self.orchestrator.execute_command('delete_tenant', {'name': name})
                
                if result.get('success'):
                    self.console.print(f"[green]Tenant '{name}' deleted successfully[/green]")
                else:
                    self.console.print(f"[red]Failed to delete tenant: {result.get('error')}[/red]")
        except Exception as e:
            self.console.print(f"[red]Error deleting tenant: {e}[/red]")
    
    async def view_tenant_details(self):
        """View tenant details."""
        try:
            name = Prompt.ask("Tenant name")
            
            result = await self.orchestrator.execute_command('get_tenant_details', {'name': name})
            if result.get('success'):
                tenant = result.get('tenant', {})
                
                table = Table(title=f"Tenant Details: {name}")
                table.add_column("Property", style="cyan")
                table.add_column("Value", style="white")
                
                for prop, value in tenant.items():
                    table.add_row(prop, str(value))
                
                self.console.print(table)
            else:
                self.console.print(f"[red]Failed to get tenant details: {result.get('error')}[/red]")
        except Exception as e:
            self.console.print(f"[red]Error viewing tenant details: {e}[/red]")
    
    async def modify_tenant_quotas(self):
        """Modify tenant quotas."""
        try:
            name = Prompt.ask("Tenant name")
            memory_quota = IntPrompt.ask("New memory quota (MB)")
            request_rate = IntPrompt.ask("New request rate quota (req/s)")
            
            result = await self.orchestrator.execute_command('modify_tenant_quotas', {
                'name': name,
                'quota_memory_mb': memory_quota,
                'quota_requests_per_second': request_rate
            })
            
            if result.get('success'):
                self.console.print(f"[green]Tenant '{name}' quotas updated successfully[/green]")
            else:
                self.console.print(f"[red]Failed to update tenant quotas: {result.get('error')}[/red]")
        except Exception as e:
            self.console.print(f"[red]Error modifying tenant quotas: {e}[/red]")
    
    # Implemented menu actions
    async def real_time_metrics(self):
        """Show real-time metrics."""
        try:
            self.console.print("[bold blue]Real-Time Metrics[/bold blue]")
            
            # Get current metrics
            metrics = await self.orchestrator.cache_manager.get_system_metrics()
            
            # Create metrics table
            table = Table(title="Real-Time System Metrics")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")
            table.add_column("Status", style="yellow")
            
            # CPU Usage
            cpu_usage = metrics.get("cpu_usage_percent", 0.0)
            cpu_status = "Normal" if cpu_usage < 70 else "Warning" if cpu_usage < 85 else "Critical"
            table.add_row("CPU Usage", f"{cpu_usage:.1f}%", cpu_status)
            
            # Memory Usage
            memory_usage = metrics.get("memory_usage_percent", 0.0)
            memory_status = "Normal" if memory_usage < 70 else "Warning" if memory_usage < 85 else "Critical"
            table.add_row("Memory Usage", f"{memory_usage:.1f}%", memory_status)
            
            # Request Rate
            request_rate = metrics.get("requests_per_second", 0.0)
            table.add_row("Request Rate", f"{request_rate:.1f} req/s", "Active")
            
            # Response Time
            response_time = metrics.get("average_response_time_ms", 0.0)
            response_status = "Good" if response_time < 10 else "Warning" if response_time < 50 else "Critical"
            table.add_row("Avg Response Time", f"{response_time:.1f}ms", response_status)
            
            # Hit Ratio
            hit_ratio = metrics.get("hit_ratio", 0.0)
            hit_status = "Good" if hit_ratio > 80 else "Warning" if hit_ratio > 60 else "Poor"
            table.add_row("Cache Hit Ratio", f"{hit_ratio:.1f}%", hit_status)
            
            # Error Rate
            error_rate = metrics.get("error_rate", 0.0)
            error_status = "Good" if error_rate < 1 else "Warning" if error_rate < 5 else "Critical"
            table.add_row("Error Rate", f"{error_rate:.2f}%", error_status)
            
            self.console.print(table)
            
            # Auto-refresh option
            if Confirm.ask("Enable auto-refresh (5s intervals)?"):
                await self._auto_refresh_metrics()
                
        except Exception as e:
            self.console.print(f"[red]Error getting real-time metrics: {e}[/red]")
    
    async def _auto_refresh_metrics(self):
        """Auto-refresh metrics display."""
        import asyncio
        
        try:
            for i in range(12):  # 1 minute of updates
                await asyncio.sleep(5)
                self.console.clear()
                await self.real_time_metrics()
        except KeyboardInterrupt:
            self.console.print("\n[yellow]Auto-refresh stopped[/yellow]")
    
    async def performance_dashboard(self):
        """Show performance dashboard."""
        try:
            self.console.print("[bold blue]Performance Dashboard[/bold blue]")
            
            # Get comprehensive metrics
            metrics = await self.orchestrator.cache_manager.get_system_metrics()
            status = await self.orchestrator.get_system_status()
            
            # Create dashboard layout
            layout = Layout()
            layout.split_column(
                Layout(name="header", size=3),
                Layout(name="main", ratio=1),
                Layout(name="footer", size=3)
            )
            
            layout["main"].split_row(
                Layout(name="left", ratio=1),
                Layout(name="right", ratio=1)
            )
            
            # Header
            header = Panel(
                f"Platform Status: {status.get('status', 'Unknown')} | "
                f"Uptime: {status.get('uptime_seconds', 0)}s | "
                f"Version: {status.get('platform_version', 'Unknown')}",
                title="System Overview",
                border_style="blue"
            )
            layout["header"].update(header)
            
            # Left panel - Performance metrics
            perf_table = Table(title="Performance Metrics")
            perf_table.add_column("Metric", style="cyan")
            perf_table.add_column("Value", style="green")
            
            perf_table.add_row("Total Requests", str(metrics.get("total_requests", 0)))
            perf_table.add_row("Successful Requests", str(metrics.get("successful_requests", 0)))
            perf_table.add_row("Failed Requests", str(metrics.get("failed_requests", 0)))
            perf_table.add_row("Cache Hits", str(metrics.get("cache_hits", 0)))
            perf_table.add_row("Cache Misses", str(metrics.get("cache_misses", 0)))
            perf_table.add_row("Hit Ratio", f"{metrics.get('hit_ratio', 0.0):.1f}%")
            
            layout["left"].update(Panel(perf_table, title="Cache Performance", border_style="green"))
            
            # Right panel - System metrics
            sys_table = Table(title="System Metrics")
            sys_table.add_column("Metric", style="cyan")
            sys_table.add_column("Value", style="green")
            
            sys_table.add_row("CPU Usage", f"{metrics.get('cpu_usage_percent', 0.0):.1f}%")
            sys_table.add_row("Memory Usage", f"{metrics.get('memory_usage_percent', 0.0):.1f}%")
            sys_table.add_row("Memory Used", f"{metrics.get('memory_used_mb', 0.0):.1f} MB")
            sys_table.add_row("Request Rate", f"{metrics.get('requests_per_second', 0.0):.1f} req/s")
            sys_table.add_row("Avg Response Time", f"{metrics.get('average_response_time_ms', 0.0):.1f}ms")
            sys_table.add_row("Error Rate", f"{metrics.get('error_rate', 0.0):.2f}%")
            
            layout["right"].update(Panel(sys_table, title="System Health", border_style="yellow"))
            
            # Footer - Alerts and status
            alerts = await self.orchestrator.cache_manager.get_active_alerts()
            alert_text = "No active alerts" if not alerts else f"{len(alerts)} active alerts"
            
            footer = Panel(
                f"Active Alerts: {alert_text} | "
                f"Last Updated: {datetime.utcnow().strftime('%H:%M:%S')}",
                title="System Status",
                border_style="red" if alerts else "green"
            )
            layout["footer"].update(footer)
            
            self.console.print(layout)
            
        except Exception as e:
            self.console.print(f"[red]Error getting performance dashboard: {e}[/red]")
    
    async def alerts_notifications(self):
        """Show alerts and notifications."""
        try:
            self.console.print("[bold blue]Alerts and Notifications[/bold blue]")
            
            # Get active alerts
            alerts = await self.orchestrator.cache_manager.get_active_alerts()
            
            if not alerts:
                self.console.print("[green]No active alerts[/green]")
                return
            
            # Create alerts table
            table = Table(title="Active Alerts")
            table.add_column("ID", style="cyan")
            table.add_column("Title", style="white")
            table.add_column("Severity", style="red")
            table.add_column("Source", style="yellow")
            table.add_column("Created", style="green")
            table.add_column("Status", style="blue")
            
            for alert in alerts:
                severity_style = {
                    "info": "blue",
                    "warning": "yellow", 
                    "error": "red",
                    "critical": "red"
                }.get(alert.get("severity", "info"), "white")
                
                table.add_row(
                    alert.get("id", "N/A"),
                    alert.get("title", "N/A"),
                    alert.get("severity", "N/A"),
                    alert.get("source", "N/A"),
                    alert.get("created_at", "N/A"),
                    "Active" if not alert.get("acknowledged", False) else "Acknowledged"
                )
            
            self.console.print(table)
            
            # Alert actions
            if alerts:
                self.console.print("\n[bold]Alert Actions:[/bold]")
                self.console.print("1. Acknowledge alert")
                self.console.print("2. View alert details")
                self.console.print("3. Back to menu")
                
                choice = Prompt.ask("Select action", choices=["1", "2", "3"])
                
                if choice == "1":
                    alert_id = Prompt.ask("Enter alert ID to acknowledge")
                    success = await self.orchestrator.cache_manager.acknowledge_alert(alert_id)
                    if success:
                        self.console.print("[green]Alert acknowledged successfully[/green]")
                    else:
                        self.console.print("[red]Failed to acknowledge alert[/red]")
                
                elif choice == "2":
                    alert_id = Prompt.ask("Enter alert ID to view details")
                    alert_details = await self.orchestrator.cache_manager.get_alert_details(alert_id)
                    if alert_details:
                        self.console.print(Panel(
                            f"Title: {alert_details.get('title', 'N/A')}\n"
                            f"Message: {alert_details.get('message', 'N/A')}\n"
                            f"Severity: {alert_details.get('severity', 'N/A')}\n"
                            f"Source: {alert_details.get('source', 'N/A')}\n"
                            f"Created: {alert_details.get('created_at', 'N/A')}\n"
                            f"Metadata: {alert_details.get('metadata', {})}",
                            title="Alert Details",
                            border_style="red"
                        ))
                    else:
                        self.console.print("[red]Alert not found[/red]")
            
        except Exception as e:
            self.console.print(f"[red]Error getting alerts: {e}[/red]")
    
    async def historical_analysis(self):
        """Show historical analysis."""
        self.console.print("[yellow]Historical analysis feature not implemented yet[/yellow]")
    
    async def view_scaling_status(self):
        """View scaling status."""
        try:
            self.console.print("[bold blue]Scaling Status[/bold blue]")
            
            # Get scaling status
            scaling_status = await self.orchestrator.auto_scaler.get_scaling_status()
            
            # Create status table
            table = Table(title="Auto-Scaling Status")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")
            
            table.add_row("Current Nodes", str(scaling_status.get("current_nodes", 0)))
            table.add_row("Min Nodes", str(scaling_status.get("min_nodes", 0)))
            table.add_row("Max Nodes", str(scaling_status.get("max_nodes", 0)))
            table.add_row("Scale Up Threshold", f"{scaling_status.get('scale_up_threshold', 0):.1f}%")
            table.add_row("Scale Down Threshold", f"{scaling_status.get('scale_down_threshold', 0):.1f}%")
            table.add_row("Scale Up Cooldown", f"{scaling_status.get('scale_up_cooldown', 0)}s")
            table.add_row("Scale Down Cooldown", f"{scaling_status.get('scale_down_cooldown', 0)}s")
            
            self.console.print(table)
            
            # Show recent decisions
            recent_decisions = scaling_status.get("recent_decisions", [])
            if recent_decisions:
                self.console.print("\n[bold]Recent Scaling Decisions:[/bold]")
                decision_table = Table()
                decision_table.add_column("Time", style="cyan")
                decision_table.add_column("Type", style="yellow")
                decision_table.add_column("From", style="green")
                decision_table.add_column("To", style="green")
                decision_table.add_column("Reason", style="white")
                
                for decision in recent_decisions[-5:]:  # Last 5 decisions
                    decision_table.add_row(
                        decision.get("created_at", "N/A"),
                        decision.get("decision_type", "N/A"),
                        str(decision.get("current_nodes", 0)),
                        str(decision.get("target_nodes", 0)),
                        decision.get("reason", "N/A")[:50] + "..." if len(decision.get("reason", "")) > 50 else decision.get("reason", "N/A")
                    )
                
                self.console.print(decision_table)
            
        except Exception as e:
            self.console.print(f"[red]Error getting scaling status: {e}[/red]")
    
    async def configure_scaling_rules(self):
        """Configure scaling rules."""
        try:
            self.console.print("[bold blue]Configure Scaling Rules[/bold blue]")
            
            current_config = await self.orchestrator.auto_scaler.get_scaling_status()
            
            self.console.print(f"Current configuration:")
            self.console.print(f"Min nodes: {current_config.get('min_nodes', 1)}")
            self.console.print(f"Max nodes: {current_config.get('max_nodes', 10)}")
            self.console.print(f"Scale up threshold: {current_config.get('scale_up_threshold', 80)}%")
            self.console.print(f"Scale down threshold: {current_config.get('scale_down_threshold', 30)}%")
            self.console.print(f"Scale up cooldown: {current_config.get('scale_up_cooldown', 300)}s")
            self.console.print(f"Scale down cooldown: {current_config.get('scale_down_cooldown', 600)}s")
            
            # Get new configuration
            new_config = {}
            
            min_nodes = IntPrompt.ask("Enter minimum nodes", default=current_config.get('min_nodes', 1))
            new_config["min_nodes"] = min_nodes
            
            max_nodes = IntPrompt.ask("Enter maximum nodes", default=current_config.get('max_nodes', 10))
            new_config["max_nodes"] = max_nodes
            
            scale_up_threshold = IntPrompt.ask("Enter scale up threshold (%)", default=int(current_config.get('scale_up_threshold', 80)))
            new_config["scale_up_threshold"] = scale_up_threshold
            
            scale_down_threshold = IntPrompt.ask("Enter scale down threshold (%)", default=int(current_config.get('scale_down_threshold', 30)))
            new_config["scale_down_threshold"] = scale_down_threshold
            
            scale_up_cooldown = IntPrompt.ask("Enter scale up cooldown (seconds)", default=current_config.get('scale_up_cooldown', 300))
            new_config["scale_up_cooldown"] = scale_up_cooldown
            
            scale_down_cooldown = IntPrompt.ask("Enter scale down cooldown (seconds)", default=current_config.get('scale_down_cooldown', 600))
            new_config["scale_down_cooldown"] = scale_down_cooldown
            
            # Apply configuration
            if Confirm.ask("Apply new configuration?"):
                success = await self.orchestrator.auto_scaler.set_scaling_config(new_config)
                if success:
                    self.console.print("[green]Scaling configuration updated successfully[/green]")
                else:
                    self.console.print("[red]Failed to update scaling configuration[/red]")
            
        except Exception as e:
            self.console.print(f"[red]Error configuring scaling rules: {e}[/red]")
    
    async def manual_scaling(self):
        """Manual scaling."""
        try:
            self.console.print("[bold blue]Manual Scaling[/bold blue]")
            
            current_status = await self.orchestrator.auto_scaler.get_scaling_status()
            current_nodes = current_status.get("current_nodes", 1)
            min_nodes = current_status.get("min_nodes", 1)
            max_nodes = current_status.get("max_nodes", 10)
            
            self.console.print(f"Current nodes: {current_nodes}")
            self.console.print(f"Allowed range: {min_nodes} - {max_nodes}")
            
            target_nodes = IntPrompt.ask("Enter target number of nodes", default=current_nodes)
            
            if target_nodes < min_nodes or target_nodes > max_nodes:
                self.console.print(f"[red]Target nodes must be between {min_nodes} and {max_nodes}[/red]")
                return
            
            if Confirm.ask(f"Scale from {current_nodes} to {target_nodes} nodes?"):
                success = await self.orchestrator.auto_scaler.force_scale(target_nodes)
                if success:
                    self.console.print(f"[green]Successfully scaled to {target_nodes} nodes[/green]")
                else:
                    self.console.print("[red]Failed to scale cluster[/red]")
            
        except Exception as e:
            self.console.print(f"[red]Error during manual scaling: {e}[/red]")
    
    async def scaling_history(self):
        """Show scaling history."""
        try:
            self.console.print("[bold blue]Scaling History[/bold blue]")
            
            # Get performance history
            history = await self.orchestrator.auto_scaler.get_performance_history(hours=24)
            
            if not history:
                self.console.print("[yellow]No scaling history available[/yellow]")
                return
            
            # Create history table
            table = Table(title="Scaling History (Last 24 Hours)")
            table.add_column("Time", style="cyan")
            table.add_column("Nodes", style="green")
            table.add_column("CPU %", style="yellow")
            table.add_column("Memory %", style="yellow")
            table.add_column("Request Rate", style="blue")
            
            for entry in history[-20:]:  # Last 20 entries
                table.add_row(
                    entry.get("timestamp", "N/A")[11:19],  # Just time part
                    str(entry.get("nodes", 0)),
                    f"{entry.get('cpu_usage', 0.0):.1f}",
                    f"{entry.get('memory_usage', 0.0):.1f}",
                    f"{entry.get('request_rate', 0.0):.1f}"
                )
            
            self.console.print(table)
            
        except Exception as e:
            self.console.print(f"[red]Error getting scaling history: {e}[/red]")
    
    async def user_management(self):
        """User management."""
        try:
            self.console.print("[bold blue]User Management[/bold blue]")
            
            # Get current users
            users = await self.orchestrator.cache_manager.get_users()
            
            if not users:
                self.console.print("[yellow]No users found[/yellow]")
                return
            
            # Create users table
            table = Table(title="System Users")
            table.add_column("Username", style="cyan")
            table.add_column("Role", style="yellow")
            table.add_column("Status", style="green")
            table.add_column("Last Login", style="blue")
            
            for user in users:
                table.add_row(
                    user.get("username", "N/A"),
                    user.get("role", "N/A"),
                    user.get("status", "N/A"),
                    user.get("last_login", "N/A")
                )
            
            self.console.print(table)
            
            # User actions
            self.console.print("\n[bold]User Actions:[/bold]")
            self.console.print("1. Create new user")
            self.console.print("2. Modify user role")
            self.console.print("3. Disable user")
            self.console.print("4. Back to menu")
            
            choice = Prompt.ask("Select action", choices=["1", "2", "3", "4"])
            
            if choice == "1":
                username = Prompt.ask("Enter username")
                password = Prompt.ask("Enter password", password=True)
                role = Prompt.ask("Enter role", choices=["admin", "operator", "viewer"])
                
                success = await self.orchestrator.cache_manager.create_user(username, password, role)
                if success:
                    self.console.print("[green]User created successfully[/green]")
                else:
                    self.console.print("[red]Failed to create user[/red]")
            
            elif choice == "2":
                username = Prompt.ask("Enter username")
                new_role = Prompt.ask("Enter new role", choices=["admin", "operator", "viewer"])
                
                success = await self.orchestrator.cache_manager.update_user_role(username, new_role)
                if success:
                    self.console.print("[green]User role updated successfully[/green]")
                else:
                    self.console.print("[red]Failed to update user role[/red]")
            
            elif choice == "3":
                username = Prompt.ask("Enter username to disable")
                
                if Confirm.ask(f"Disable user {username}?"):
                    success = await self.orchestrator.cache_manager.disable_user(username)
                    if success:
                        self.console.print("[green]User disabled successfully[/green]")
                    else:
                        self.console.print("[red]Failed to disable user[/red]")
            
        except Exception as e:
            self.console.print(f"[red]Error in user management: {e}[/red]")
    
    async def api_key_management(self):
        """API key management."""
        try:
            self.console.print("[bold blue]API Key Management[/bold blue]")
            
            # Get current API keys
            api_keys = await self.orchestrator.cache_manager.get_api_keys()
            
            if not api_keys:
                self.console.print("[yellow]No API keys found[/yellow]")
                return
            
            # Create API keys table
            table = Table(title="API Keys")
            table.add_column("Key ID", style="cyan")
            table.add_column("Name", style="white")
            table.add_column("Tenant", style="yellow")
            table.add_column("Created", style="green")
            table.add_column("Expires", style="blue")
            table.add_column("Status", style="red")
            
            for key in api_keys:
                table.add_row(
                    key.get("id", "N/A"),
                    key.get("name", "N/A"),
                    key.get("tenant", "N/A"),
                    key.get("created_at", "N/A"),
                    key.get("expires_at", "Never"),
                    "Active" if key.get("active", True) else "Inactive"
                )
            
            self.console.print(table)
            
            # API key actions
            self.console.print("\n[bold]API Key Actions:[/bold]")
            self.console.print("1. Generate new API key")
            self.console.print("2. Revoke API key")
            self.console.print("3. View key details")
            self.console.print("4. Back to menu")
            
            choice = Prompt.ask("Select action", choices=["1", "2", "3", "4"])
            
            if choice == "1":
                name = Prompt.ask("Enter key name")
                tenant = Prompt.ask("Enter tenant name")
                expires_days = IntPrompt.ask("Enter expiration days (0 for never)", default=365)
                
                result = await self.orchestrator.cache_manager.generate_api_key(name, tenant, expires_days)
                if result.get("success"):
                    self.console.print(f"[green]API key generated: {result.get('key')}[/green]")
                else:
                    self.console.print("[red]Failed to generate API key[/red]")
            
            elif choice == "2":
                key_id = Prompt.ask("Enter key ID to revoke")
                
                if Confirm.ask(f"Revoke API key {key_id}?"):
                    success = await self.orchestrator.cache_manager.revoke_api_key(key_id)
                    if success:
                        self.console.print("[green]API key revoked successfully[/green]")
                    else:
                        self.console.print("[red]Failed to revoke API key[/red]")
            
            elif choice == "3":
                key_id = Prompt.ask("Enter key ID to view details")
                key_details = await self.orchestrator.cache_manager.get_api_key_details(key_id)
                if key_details:
                    self.console.print(Panel(
                        f"ID: {key_details.get('id', 'N/A')}\n"
                        f"Name: {key_details.get('name', 'N/A')}\n"
                        f"Tenant: {key_details.get('tenant', 'N/A')}\n"
                        f"Created: {key_details.get('created_at', 'N/A')}\n"
                        f"Expires: {key_details.get('expires_at', 'Never')}\n"
                        f"Last Used: {key_details.get('last_used', 'Never')}\n"
                        f"Permissions: {key_details.get('permissions', [])}",
                        title="API Key Details",
                        border_style="blue"
                    ))
                else:
                    self.console.print("[red]API key not found[/red]")
            
        except Exception as e:
            self.console.print(f"[red]Error in API key management: {e}[/red]")
    
    async def access_logs(self):
        """Show access logs."""
        try:
            self.console.print("[bold blue]Access Logs[/bold blue]")
            
            # Get access logs
            logs = await self.orchestrator.cache_manager.get_access_logs(limit=50)
            
            if not logs:
                self.console.print("[yellow]No access logs found[/yellow]")
                return
            
            # Create logs table
            table = Table(title="Recent Access Logs")
            table.add_column("Time", style="cyan")
            table.add_column("User", style="white")
            table.add_column("Action", style="yellow")
            table.add_column("Resource", style="green")
            table.add_column("IP", style="blue")
            table.add_column("Status", style="red")
            
            for log in logs:
                status_style = "green" if log.get("success", True) else "red"
                table.add_row(
                    log.get("timestamp", "N/A")[11:19],  # Just time part
                    log.get("user", "N/A"),
                    log.get("action", "N/A"),
                    log.get("resource", "N/A")[:30] + "..." if len(log.get("resource", "")) > 30 else log.get("resource", "N/A"),
                    log.get("ip", "N/A"),
                    "Success" if log.get("success", True) else "Failed"
                )
            
            self.console.print(table)
            
        except Exception as e:
            self.console.print(f"[red]Error getting access logs: {e}[/red]")
    
    async def security_settings(self):
        """Security settings."""
        try:
            self.console.print("[bold blue]Security Settings[/bold blue]")
            
            # Get current security settings
            settings = await self.orchestrator.cache_manager.get_security_settings()
            
            # Create settings table
            table = Table(title="Security Configuration")
            table.add_column("Setting", style="cyan")
            table.add_column("Value", style="green")
            table.add_column("Description", style="white")
            
            table.add_row("Authentication", settings.get("authentication_enabled", "Unknown"), "Enable user authentication")
            table.add_row("Encryption", settings.get("encryption_enabled", "Unknown"), "Enable data encryption")
            table.add_row("Audit Logging", settings.get("audit_logging_enabled", "Unknown"), "Enable audit logging")
            table.add_row("Session Timeout", f"{settings.get('session_timeout_minutes', 0)} min", "Session timeout in minutes")
            table.add_row("Max Login Attempts", str(settings.get("max_login_attempts", 0)), "Maximum failed login attempts")
            table.add_row("Password Policy", settings.get("password_policy", "Unknown"), "Password complexity requirements")
            
            self.console.print(table)
            
            # Security actions
            self.console.print("\n[bold]Security Actions:[/bold]")
            self.console.print("1. Update security settings")
            self.console.print("2. View security audit")
            self.console.print("3. Back to menu")
            
            choice = Prompt.ask("Select action", choices=["1", "2", "3"])
            
            if choice == "1":
                self.console.print("[yellow]Security settings update not implemented in this version[/yellow]")
            
            elif choice == "2":
                audit_logs = await self.orchestrator.cache_manager.get_security_audit_logs(limit=20)
                if audit_logs:
                    audit_table = Table(title="Security Audit Log")
                    audit_table.add_column("Time", style="cyan")
                    audit_table.add_column("Event", style="yellow")
                    audit_table.add_column("User", style="white")
                    audit_table.add_column("Details", style="green")
                    
                    for log in audit_logs:
                        audit_table.add_row(
                            log.get("timestamp", "N/A")[11:19],
                            log.get("event", "N/A"),
                            log.get("user", "N/A"),
                            log.get("details", "N/A")[:40] + "..." if len(log.get("details", "")) > 40 else log.get("details", "N/A")
                        )
                    
                    self.console.print(audit_table)
                else:
                    self.console.print("[yellow]No security audit logs found[/yellow]")
            
        except Exception as e:
            self.console.print(f"[red]Error in security settings: {e}[/red]")
    
    async def cache_performance(self):
        """Cache performance analytics."""
        try:
            self.console.print("[bold blue]Cache Performance Analytics[/bold blue]")
            
            # Get cache performance metrics
            metrics = await self.orchestrator.cache_manager.get_cache_performance_metrics()
            
            # Create performance table
            table = Table(title="Cache Performance Analytics")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")
            table.add_column("Trend", style="yellow")
            
            # Hit ratio analysis
            hit_ratio = metrics.get("hit_ratio", 0.0)
            hit_trend = "Good" if hit_ratio > 80 else "Warning" if hit_ratio > 60 else "Poor"
            table.add_row("Hit Ratio", f"{hit_ratio:.1f}%", hit_trend)
            
            # Miss ratio
            miss_ratio = 100 - hit_ratio
            miss_trend = "Good" if miss_ratio < 20 else "Warning" if miss_ratio < 40 else "Poor"
            table.add_row("Miss Ratio", f"{miss_ratio:.1f}%", miss_trend)
            
            # Eviction rate
            eviction_rate = metrics.get("eviction_rate", 0.0)
            eviction_trend = "Good" if eviction_rate < 1 else "Warning" if eviction_rate < 5 else "Poor"
            table.add_row("Eviction Rate", f"{eviction_rate:.2f}%", eviction_trend)
            
            # Average TTL
            avg_ttl = metrics.get("average_ttl_seconds", 0)
            ttl_trend = "Good" if avg_ttl > 3600 else "Warning" if avg_ttl > 600 else "Poor"
            table.add_row("Average TTL", f"{avg_ttl}s", ttl_trend)
            
            # Key count
            key_count = metrics.get("total_keys", 0)
            table.add_row("Total Keys", str(key_count), "Active")
            
            # Memory efficiency
            memory_efficiency = metrics.get("memory_efficiency", 0.0)
            efficiency_trend = "Good" if memory_efficiency > 80 else "Warning" if memory_efficiency > 60 else "Poor"
            table.add_row("Memory Efficiency", f"{memory_efficiency:.1f}%", efficiency_trend)
            
            self.console.print(table)
            
            # Performance recommendations
            recommendations = []
            if hit_ratio < 80:
                recommendations.append("Consider increasing TTL for frequently accessed keys")
            if eviction_rate > 1:
                recommendations.append("Consider increasing memory allocation or optimizing key patterns")
            if memory_efficiency < 80:
                recommendations.append("Consider optimizing key naming and data structures")
            
            if recommendations:
                self.console.print("\n[bold]Performance Recommendations:[/bold]")
                for i, rec in enumerate(recommendations, 1):
                    self.console.print(f"{i}. {rec}")
            
        except Exception as e:
            self.console.print(f"[red]Error getting cache performance analytics: {e}[/red]")
    
    async def tenant_analytics(self):
        """Tenant analytics."""
        try:
            self.console.print("[bold blue]Tenant Analytics[/bold blue]")
            
            # Get tenant analytics
            analytics = await self.orchestrator.cache_manager.get_tenant_analytics()
            
            if not analytics:
                self.console.print("[yellow]No tenant analytics available[/yellow]")
                return
            
            # Create analytics table
            table = Table(title="Tenant Performance Analytics")
            table.add_column("Tenant", style="cyan")
            table.add_column("Requests/s", style="green")
            table.add_column("Hit Ratio", style="yellow")
            table.add_column("Memory Usage", style="blue")
            table.add_column("Error Rate", style="red")
            table.add_column("Status", style="white")
            
            for tenant in analytics:
                hit_ratio = tenant.get("hit_ratio", 0.0)
                error_rate = tenant.get("error_rate", 0.0)
                
                status = "Healthy"
                if error_rate > 5 or hit_ratio < 60:
                    status = "Warning"
                if error_rate > 10 or hit_ratio < 40:
                    status = "Critical"
                
                table.add_row(
                    tenant.get("name", "N/A"),
                    f"{tenant.get('requests_per_second', 0.0):.1f}",
                    f"{hit_ratio:.1f}%",
                    f"{tenant.get('memory_usage_mb', 0.0):.1f} MB",
                    f"{error_rate:.2f}%",
                    status
                )
            
            self.console.print(table)
            
            # Tenant details option
            if analytics:
                tenant_name = Prompt.ask("Enter tenant name for detailed analysis (or press Enter to skip)")
                if tenant_name:
                    tenant_details = await self.orchestrator.cache_manager.get_tenant_detailed_analytics(tenant_name)
                    if tenant_details:
                        self.console.print(Panel(
                            f"Tenant: {tenant_details.get('name', 'N/A')}\n"
                            f"Total Requests: {tenant_details.get('total_requests', 0)}\n"
                            f"Cache Hits: {tenant_details.get('cache_hits', 0)}\n"
                            f"Cache Misses: {tenant_details.get('cache_misses', 0)}\n"
                            f"Average Response Time: {tenant_details.get('avg_response_time_ms', 0.0):.1f}ms\n"
                            f"Peak Usage: {tenant_details.get('peak_usage_mb', 0.0):.1f} MB\n"
                            f"Quota Utilization: {tenant_details.get('quota_utilization', 0.0):.1f}%",
                            title="Tenant Details",
                            border_style="blue"
                        ))
                    else:
                        self.console.print("[red]Tenant not found[/red]")
            
        except Exception as e:
            self.console.print(f"[red]Error getting tenant analytics: {e}[/red]")
    
    async def system_analytics(self):
        """System analytics."""
        try:
            self.console.print("[bold blue]System Analytics[/bold blue]")
            
            # Get system analytics
            analytics = await self.orchestrator.cache_manager.get_system_analytics()
            
            # Create analytics table
            table = Table(title="System Analytics")
            table.add_column("Metric", style="cyan")
            table.add_column("Current", style="green")
            table.add_column("Average (24h)", style="yellow")
            table.add_column("Peak (24h)", style="red")
            table.add_column("Trend", style="blue")
            
            # CPU analytics
            cpu_current = analytics.get("cpu_usage_percent", 0.0)
            cpu_avg = analytics.get("cpu_avg_24h", 0.0)
            cpu_peak = analytics.get("cpu_peak_24h", 0.0)
            cpu_trend = "Stable" if abs(cpu_current - cpu_avg) < 10 else "Increasing" if cpu_current > cpu_avg else "Decreasing"
            
            table.add_row("CPU Usage", f"{cpu_current:.1f}%", f"{cpu_avg:.1f}%", f"{cpu_peak:.1f}%", cpu_trend)
            
            # Memory analytics
            memory_current = analytics.get("memory_usage_percent", 0.0)
            memory_avg = analytics.get("memory_avg_24h", 0.0)
            memory_peak = analytics.get("memory_peak_24h", 0.0)
            memory_trend = "Stable" if abs(memory_current - memory_avg) < 10 else "Increasing" if memory_current > memory_avg else "Decreasing"
            
            table.add_row("Memory Usage", f"{memory_current:.1f}%", f"{memory_avg:.1f}%", f"{memory_peak:.1f}%", memory_trend)
            
            # Request rate analytics
            request_current = analytics.get("requests_per_second", 0.0)
            request_avg = analytics.get("requests_avg_24h", 0.0)
            request_peak = analytics.get("requests_peak_24h", 0.0)
            request_trend = "Stable" if abs(request_current - request_avg) < 100 else "Increasing" if request_current > request_avg else "Decreasing"
            
            table.add_row("Request Rate", f"{request_current:.1f}/s", f"{request_avg:.1f}/s", f"{request_peak:.1f}/s", request_trend)
            
            # Response time analytics
            response_current = analytics.get("average_response_time_ms", 0.0)
            response_avg = analytics.get("response_time_avg_24h", 0.0)
            response_peak = analytics.get("response_time_peak_24h", 0.0)
            response_trend = "Stable" if abs(response_current - response_avg) < 5 else "Increasing" if response_current > response_avg else "Decreasing"
            
            table.add_row("Response Time", f"{response_current:.1f}ms", f"{response_avg:.1f}ms", f"{response_peak:.1f}ms", response_trend)
            
            # Error rate analytics
            error_current = analytics.get("error_rate", 0.0)
            error_avg = analytics.get("error_rate_avg_24h", 0.0)
            error_peak = analytics.get("error_rate_peak_24h", 0.0)
            error_trend = "Stable" if abs(error_current - error_avg) < 1 else "Increasing" if error_current > error_avg else "Decreasing"
            
            table.add_row("Error Rate", f"{error_current:.2f}%", f"{error_avg:.2f}%", f"{error_peak:.2f}%", error_trend)
            
            self.console.print(table)
            
            # System health summary
            health_score = analytics.get("health_score", 0.0)
            health_status = "Excellent" if health_score > 90 else "Good" if health_score > 70 else "Fair" if health_score > 50 else "Poor"
            
            self.console.print(f"\n[bold]System Health Score: {health_score:.1f}/100 ({health_status})[/bold]")
            
        except Exception as e:
            self.console.print(f"[red]Error getting system analytics: {e}[/red]")
    
    async def custom_reports(self):
        """Custom reports."""
        try:
            self.console.print("[bold blue]Custom Reports[/bold blue]")
            
            self.console.print("Available report types:")
            self.console.print("1. Performance Summary Report")
            self.console.print("2. Tenant Usage Report")
            self.console.print("3. Error Analysis Report")
            self.console.print("4. Capacity Planning Report")
            self.console.print("5. Back to menu")
            
            choice = Prompt.ask("Select report type", choices=["1", "2", "3", "4", "5"])
            
            if choice == "1":
                await self._generate_performance_summary_report()
            elif choice == "2":
                await self._generate_tenant_usage_report()
            elif choice == "3":
                await self._generate_error_analysis_report()
            elif choice == "4":
                await self._generate_capacity_planning_report()
            
        except Exception as e:
            self.console.print(f"[red]Error generating custom reports: {e}[/red]")
    
    async def _generate_performance_summary_report(self):
        """Generate performance summary report."""
        try:
            self.console.print("[bold blue]Generating Performance Summary Report...[/bold blue]")
            
            # Get performance data
            metrics = await self.orchestrator.cache_manager.get_system_metrics()
            analytics = await self.orchestrator.cache_manager.get_system_analytics()
            
            # Create report
            report = f"""
Performance Summary Report
Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}

System Overview:
- Total Requests: {metrics.get('total_requests', 0):,}
- Successful Requests: {metrics.get('successful_requests', 0):,}
- Failed Requests: {metrics.get('failed_requests', 0):,}
- Cache Hit Ratio: {metrics.get('hit_ratio', 0.0):.1f}%

Performance Metrics:
- Average Response Time: {metrics.get('average_response_time_ms', 0.0):.1f}ms
- Request Rate: {metrics.get('requests_per_second', 0.0):.1f} req/s
- CPU Usage: {metrics.get('cpu_usage_percent', 0.0):.1f}%
- Memory Usage: {metrics.get('memory_usage_percent', 0.0):.1f}%

24-Hour Trends:
- CPU Average: {analytics.get('cpu_avg_24h', 0.0):.1f}%
- Memory Average: {analytics.get('memory_avg_24h', 0.0):.1f}%
- Peak Request Rate: {analytics.get('requests_peak_24h', 0.0):.1f} req/s

Recommendations:
"""
            
            # Add recommendations based on metrics
            if metrics.get('hit_ratio', 0.0) < 80:
                report += "- Consider optimizing cache TTL settings\n"
            if metrics.get('error_rate', 0.0) > 1:
                report += "- Investigate error patterns and optimize error handling\n"
            if metrics.get('cpu_usage_percent', 0.0) > 80:
                report += "- Consider scaling up CPU resources\n"
            if metrics.get('memory_usage_percent', 0.0) > 80:
                report += "- Consider scaling up memory resources\n"
            
            self.console.print(Panel(report, title="Performance Summary Report", border_style="blue"))
            
        except Exception as e:
            self.console.print(f"[red]Error generating performance report: {e}[/red]")
    
    async def _generate_tenant_usage_report(self):
        """Generate tenant usage report."""
        self.console.print("[yellow]Tenant usage report generation not implemented in this version[/yellow]")
    
    async def _generate_error_analysis_report(self):
        """Generate error analysis report."""
        self.console.print("[yellow]Error analysis report generation not implemented in this version[/yellow]")
    
    async def _generate_capacity_planning_report(self):
        """Generate capacity planning report."""
        self.console.print("[yellow]Capacity planning report generation not implemented in this version[/yellow]")
    
    async def system_health_check(self):
        """System health check."""
        try:
            self.console.print("[bold blue]System Health Check[/bold blue]")
            
            # Get system health status
            health_status = await self.orchestrator.get_health_status()
            
            # Create health table
            table = Table(title="System Health Status")
            table.add_column("Component", style="cyan")
            table.add_column("Status", style="green")
            table.add_column("Response Time", style="yellow")
            table.add_column("Last Check", style="blue")
            table.add_column("Details", style="white")
            
            overall_healthy = True
            
            for component, status in health_status.items():
                status_str = status.get("status", "unknown")
                response_time = status.get("response_time_ms", 0.0)
                last_check = status.get("timestamp", "N/A")
                details = status.get("details", {})
                
                # Determine status style
                if status_str == "healthy":
                    status_style = "green"
                elif status_str == "warning":
                    status_style = "yellow"
                    overall_healthy = False
                else:
                    status_style = "red"
                    overall_healthy = False
                
                # Format details
                details_str = ""
                if details:
                    if "error_count" in details:
                        details_str += f"Errors: {details['error_count']} "
                    if "memory_usage" in details:
                        details_str += f"Memory: {details['memory_usage']:.1f}% "
                    if "cpu_usage" in details:
                        details_str += f"CPU: {details['cpu_usage']:.1f}% "
                
                table.add_row(
                    component,
                    status_str,
                    f"{response_time:.1f}ms" if response_time > 0 else "N/A",
                    last_check[11:19] if len(last_check) > 10 else last_check,
                    details_str
                )
            
            self.console.print(table)
            
            # Overall health summary
            if overall_healthy:
                self.console.print("[green]All systems are healthy[/green]")
            else:
                self.console.print("[yellow]Some systems have issues - check details above[/yellow]")
            
            # Health check actions
            self.console.print("\n[bold]Health Check Actions:[/bold]")
            self.console.print("1. Run detailed health check")
            self.console.print("2. View health history")
            self.console.print("3. Back to menu")
            
            choice = Prompt.ask("Select action", choices=["1", "2", "3"])
            
            if choice == "1":
                self.console.print("[yellow]Running detailed health check...[/yellow]")
                detailed_health = await self.orchestrator.cache_manager.run_detailed_health_check()
                if detailed_health:
                    self.console.print("[green]Detailed health check completed[/green]")
                    # Show detailed results
                    for check, result in detailed_health.items():
                        status = "PASS" if result.get("passed", False) else "FAIL"
                        self.console.print(f"{check}: {status}")
                else:
                    self.console.print("[red]Detailed health check failed[/red]")
            
            elif choice == "2":
                health_history = await self.orchestrator.cache_manager.get_health_history(hours=24)
                if health_history:
                    history_table = Table(title="Health History (Last 24 Hours)")
                    history_table.add_column("Time", style="cyan")
                    history_table.add_column("Overall Status", style="green")
                    history_table.add_column("Issues", style="red")
                    
                    for entry in health_history[-10:]:  # Last 10 entries
                        history_table.add_row(
                            entry.get("timestamp", "N/A")[11:19],
                            entry.get("overall_status", "N/A"),
                            str(entry.get("issue_count", 0))
                        )
                    
                    self.console.print(history_table)
                else:
                    self.console.print("[yellow]No health history available[/yellow]")
            
        except Exception as e:
            self.console.print(f"[red]Error during system health check: {e}[/red]")
    
    async def component_diagnostics(self):
        """Component diagnostics."""
        try:
            self.console.print("[bold blue]Component Diagnostics[/bold blue]")
            
            # Get component diagnostics
            diagnostics = await self.orchestrator.cache_manager.get_component_diagnostics()
            
            # Create diagnostics table
            table = Table(title="Component Diagnostics")
            table.add_column("Component", style="cyan")
            table.add_column("Status", style="green")
            table.add_column("Version", style="yellow")
            table.add_column("Uptime", style="blue")
            table.add_column("Issues", style="red")
            
            for component, diag in diagnostics.items():
                status = diag.get("status", "unknown")
                version = diag.get("version", "N/A")
                uptime = diag.get("uptime_seconds", 0)
                issues = diag.get("issues", [])
                
                status_style = "green" if status == "healthy" else "yellow" if status == "warning" else "red"
                
                table.add_row(
                    component,
                    status,
                    version,
                    f"{uptime}s" if uptime > 0 else "N/A",
                    str(len(issues))
                )
            
            self.console.print(table)
            
            # Component details option
            component_name = Prompt.ask("Enter component name for detailed diagnostics (or press Enter to skip)")
            if component_name and component_name in diagnostics:
                component_diag = diagnostics[component_name]
                self.console.print(Panel(
                    f"Component: {component_name}\n"
                    f"Status: {component_diag.get('status', 'N/A')}\n"
                    f"Version: {component_diag.get('version', 'N/A')}\n"
                    f"Uptime: {component_diag.get('uptime_seconds', 0)}s\n"
                    f"Memory Usage: {component_diag.get('memory_usage_mb', 0.0):.1f} MB\n"
                    f"CPU Usage: {component_diag.get('cpu_usage_percent', 0.0):.1f}%\n"
                    f"Configuration: {component_diag.get('config', {})}\n"
                    f"Issues: {component_diag.get('issues', [])}",
                    title=f"{component_name} Diagnostics",
                    border_style="blue"
                ))
            elif component_name:
                self.console.print("[red]Component not found[/red]")
            
        except Exception as e:
            self.console.print(f"[red]Error getting component diagnostics: {e}[/red]")
    
    async def network_diagnostics(self):
        """Network diagnostics."""
        try:
            self.console.print("[bold blue]Network Diagnostics[/bold blue]")
            
            # Get network diagnostics
            network_diag = await self.orchestrator.cache_manager.get_network_diagnostics()
            
            # Create network table
            table = Table(title="Network Diagnostics")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")
            table.add_column("Status", style="yellow")
            
            # Connection metrics
            active_connections = network_diag.get("active_connections", 0)
            max_connections = network_diag.get("max_connections", 0)
            connection_utilization = (active_connections / max_connections * 100) if max_connections > 0 else 0
            connection_status = "Good" if connection_utilization < 80 else "Warning" if connection_utilization < 95 else "Critical"
            
            table.add_row("Active Connections", str(active_connections), "Active")
            table.add_row("Max Connections", str(max_connections), "Configured")
            table.add_row("Connection Utilization", f"{connection_utilization:.1f}%", connection_status)
            
            # Network latency
            avg_latency = network_diag.get("average_latency_ms", 0.0)
            latency_status = "Good" if avg_latency < 10 else "Warning" if avg_latency < 50 else "Poor"
            table.add_row("Average Latency", f"{avg_latency:.1f}ms", latency_status)
            
            # Network throughput
            throughput_mbps = network_diag.get("throughput_mbps", 0.0)
            table.add_row("Network Throughput", f"{throughput_mbps:.1f} Mbps", "Active")
            
            # Error rates
            network_errors = network_diag.get("network_errors", 0)
            error_rate = network_diag.get("error_rate_percent", 0.0)
            error_status = "Good" if error_rate < 1 else "Warning" if error_rate < 5 else "Critical"
            
            table.add_row("Network Errors", str(network_errors), "Count")
            table.add_row("Error Rate", f"{error_rate:.2f}%", error_status)
            
            # Node connectivity
            nodes_online = network_diag.get("nodes_online", 0)
            total_nodes = network_diag.get("total_nodes", 0)
            connectivity_status = "Good" if nodes_online == total_nodes else "Warning" if nodes_online > total_nodes * 0.8 else "Critical"
            
            table.add_row("Nodes Online", f"{nodes_online}/{total_nodes}", connectivity_status)
            
            self.console.print(table)
            
            # Network test option
            if Confirm.ask("Run network connectivity test?"):
                self.console.print("[yellow]Running network connectivity test...[/yellow]")
                test_results = await self.orchestrator.cache_manager.run_network_connectivity_test()
                if test_results:
                    self.console.print("[green]Network connectivity test completed[/green]")
                    for test, result in test_results.items():
                        status = "PASS" if result.get("success", False) else "FAIL"
                        self.console.print(f"{test}: {status} ({result.get('duration_ms', 0):.1f}ms)")
                else:
                    self.console.print("[red]Network connectivity test failed[/red]")
            
        except Exception as e:
            self.console.print(f"[red]Error getting network diagnostics: {e}[/red]")
    
    async def performance_tests(self):
        """Performance tests."""
        try:
            self.console.print("[bold blue]Performance Tests[/bold blue]")
            
            self.console.print("Available performance tests:")
            self.console.print("1. Load Test (Basic)")
            self.console.print("2. Stress Test")
            self.console.print("3. Latency Test")
            self.console.print("4. Throughput Test")
            self.console.print("5. Back to menu")
            
            choice = Prompt.ask("Select test type", choices=["1", "2", "3", "4", "5"])
            
            if choice == "1":
                await self._run_load_test()
            elif choice == "2":
                await self._run_stress_test()
            elif choice == "3":
                await self._run_latency_test()
            elif choice == "4":
                await self._run_throughput_test()
            
        except Exception as e:
            self.console.print(f"[red]Error running performance tests: {e}[/red]")
    
    async def _run_load_test(self):
        """Run basic load test."""
        try:
            self.console.print("[bold blue]Running Load Test[/bold blue]")
            
            duration = IntPrompt.ask("Enter test duration (seconds)", default=60)
            concurrency = IntPrompt.ask("Enter number of concurrent requests", default=10)
            
            self.console.print(f"[yellow]Running load test for {duration}s with {concurrency} concurrent requests...[/yellow]")
            
            # Run load test
            results = await self.orchestrator.cache_manager.run_load_test(duration, concurrency)
            
            if results:
                self.console.print("[green]Load test completed[/green]")
                
                # Display results
                result_table = Table(title="Load Test Results")
                result_table.add_column("Metric", style="cyan")
                result_table.add_column("Value", style="green")
                
                result_table.add_row("Total Requests", str(results.get("total_requests", 0)))
                result_table.add_row("Successful Requests", str(results.get("successful_requests", 0)))
                result_table.add_row("Failed Requests", str(results.get("failed_requests", 0)))
                result_table.add_row("Average Response Time", f"{results.get('average_response_time_ms', 0.0):.1f}ms")
                result_table.add_row("Requests per Second", f"{results.get('requests_per_second', 0.0):.1f}")
                result_table.add_row("Error Rate", f"{results.get('error_rate', 0.0):.2f}%")
                
                self.console.print(result_table)
            else:
                self.console.print("[red]Load test failed[/red]")
            
        except Exception as e:
            self.console.print(f"[red]Error running load test: {e}[/red]")
    
    async def _run_stress_test(self):
        """Run stress test."""
        self.console.print("[yellow]Stress test not implemented in this version[/yellow]")
    
    async def _run_latency_test(self):
        """Run latency test."""
        self.console.print("[yellow]Latency test not implemented in this version[/yellow]")
    
    async def _run_throughput_test(self):
        """Run throughput test."""
        self.console.print("[yellow]Throughput test not implemented in this version[/yellow]")
    
    async def view_agent_status(self):
        """View agent status."""
        try:
            self.console.print("[bold blue]Agent Status[/bold blue]")
            
            # Get agent status
            agent_status = await self.orchestrator.get_agent_status()
            
            if not agent_status:
                self.console.print("[yellow]No agents found[/yellow]")
                return
            
            # Create agent status table
            table = Table(title="Autonomous Agent Status")
            table.add_column("Agent", style="cyan")
            table.add_column("Type", style="white")
            table.add_column("Status", style="green")
            table.add_column("Uptime", style="yellow")
            table.add_column("Decisions", style="blue")
            table.add_column("Success Rate", style="red")
            
            for agent_id, agent in agent_status.items():
                status = agent.get("status", "unknown")
                uptime = agent.get("uptime_seconds", 0)
                total_decisions = agent.get("total_decisions", 0)
                successful_decisions = agent.get("successful_decisions", 0)
                success_rate = (successful_decisions / total_decisions * 100) if total_decisions > 0 else 0
                
                # Determine status style
                if status == "running":
                    status_style = "green"
                elif status == "starting":
                    status_style = "yellow"
                elif status == "error":
                    status_style = "red"
                else:
                    status_style = "white"
                
                table.add_row(
                    agent.get("name", agent_id),
                    agent.get("type", "N/A"),
                    status,
                    f"{uptime}s" if uptime > 0 else "N/A",
                    str(total_decisions),
                    f"{success_rate:.1f}%"
                )
            
            self.console.print(table)
            
            # Agent details option
            agent_name = Prompt.ask("Enter agent name for detailed status (or press Enter to skip)")
            if agent_name:
                agent_details = None
                for agent_id, agent in agent_status.items():
                    if agent.get("name", agent_id) == agent_name:
                        agent_details = agent
                        break
                
                if agent_details:
                    self.console.print(Panel(
                        f"Agent: {agent_details.get('name', 'N/A')}\n"
                        f"Type: {agent_details.get('type', 'N/A')}\n"
                        f"Status: {agent_details.get('status', 'N/A')}\n"
                        f"Uptime: {agent_details.get('uptime_seconds', 0)}s\n"
                        f"Total Decisions: {agent_details.get('total_decisions', 0)}\n"
                        f"Successful Decisions: {agent_details.get('successful_decisions', 0)}\n"
                        f"Failed Decisions: {agent_details.get('failed_decisions', 0)}\n"
                        f"CPU Usage: {agent_details.get('cpu_usage_percent', 0.0):.1f}%\n"
                        f"Memory Usage: {agent_details.get('memory_usage_mb', 0.0):.1f} MB\n"
                        f"Last Activity: {agent_details.get('last_activity', 'N/A')}\n"
                        f"Configuration: {agent_details.get('config', {})}",
                        title=f"{agent_name} Details",
                        border_style="blue"
                    ))
                else:
                    self.console.print("[red]Agent not found[/red]")
            
        except Exception as e:
            self.console.print(f"[red]Error getting agent status: {e}[/red]")
    
    async def control_agents(self):
        """Control agents."""
        try:
            self.console.print("[bold blue]Agent Control[/bold blue]")
            
            # Get agent status
            agent_status = await self.orchestrator.get_agent_status()
            
            if not agent_status:
                self.console.print("[yellow]No agents found[/yellow]")
                return
            
            # Show available agents
            self.console.print("Available agents:")
            for i, (agent_id, agent) in enumerate(agent_status.items(), 1):
                status = agent.get("status", "unknown")
                self.console.print(f"{i}. {agent.get('name', agent_id)} ({status})")
            
            # Agent control actions
            self.console.print("\n[bold]Agent Control Actions:[/bold]")
            self.console.print("1. Start agent")
            self.console.print("2. Stop agent")
            self.console.print("3. Restart agent")
            self.console.print("4. Back to menu")
            
            choice = Prompt.ask("Select action", choices=["1", "2", "3", "4"])
            
            if choice in ["1", "2", "3"]:
                agent_name = Prompt.ask("Enter agent name")
                
                # Find agent by name
                target_agent_id = None
                for agent_id, agent in agent_status.items():
                    if agent.get("name", agent_id) == agent_name:
                        target_agent_id = agent_id
                        break
                
                if target_agent_id:
                    if choice == "1":
                        success = await self.orchestrator.start_agent(target_agent_id)
                        if success:
                            self.console.print(f"[green]Agent {agent_name} started successfully[/green]")
                        else:
                            self.console.print(f"[red]Failed to start agent {agent_name}[/red]")
                    
                    elif choice == "2":
                        success = await self.orchestrator.stop_agent(target_agent_id)
                        if success:
                            self.console.print(f"[green]Agent {agent_name} stopped successfully[/green]")
                        else:
                            self.console.print(f"[red]Failed to stop agent {agent_name}[/red]")
                    
                    elif choice == "3":
                        success = await self.orchestrator.restart_agent(target_agent_id)
                        if success:
                            self.console.print(f"[green]Agent {agent_name} restarted successfully[/green]")
                        else:
                            self.console.print(f"[red]Failed to restart agent {agent_name}[/red]")
                else:
                    self.console.print(f"[red]Agent {agent_name} not found[/red]")
            
        except Exception as e:
            self.console.print(f"[red]Error controlling agents: {e}[/red]")
    
    async def agent_logs(self):
        """Agent logs."""
        try:
            self.console.print("[bold blue]Agent Logs[/bold blue]")
            
            # Get agent logs
            logs = await self.orchestrator.cache_manager.get_agent_logs(limit=50)
            
            if not logs:
                self.console.print("[yellow]No agent logs found[/yellow]")
                return
            
            # Create logs table
            table = Table(title="Recent Agent Logs")
            table.add_column("Time", style="cyan")
            table.add_column("Agent", style="white")
            table.add_column("Level", style="yellow")
            table.add_column("Message", style="green")
            
            for log in logs:
                level = log.get("level", "INFO")
                level_style = {
                    "ERROR": "red",
                    "WARNING": "yellow",
                    "INFO": "blue",
                    "DEBUG": "white"
                }.get(level, "white")
                
                table.add_row(
                    log.get("timestamp", "N/A")[11:19],  # Just time part
                    log.get("agent", "N/A"),
                    level,
                    log.get("message", "N/A")[:60] + "..." if len(log.get("message", "")) > 60 else log.get("message", "N/A")
                )
            
            self.console.print(table)
            
            # Filter options
            self.console.print("\n[bold]Filter Options:[/bold]")
            self.console.print("1. Filter by agent")
            self.console.print("2. Filter by log level")
            self.console.print("3. Back to menu")
            
            choice = Prompt.ask("Select option", choices=["1", "2", "3"])
            
            if choice == "1":
                agent_name = Prompt.ask("Enter agent name to filter")
                filtered_logs = await self.orchestrator.cache_manager.get_agent_logs(agent=agent_name, limit=20)
                if filtered_logs:
                    self.console.print(f"[green]Found {len(filtered_logs)} logs for agent {agent_name}[/green]")
                    # Display filtered logs (simplified)
                    for log in filtered_logs:
                        self.console.print(f"{log.get('timestamp', 'N/A')} [{log.get('level', 'INFO')}] {log.get('message', 'N/A')}")
                else:
                    self.console.print(f"[yellow]No logs found for agent {agent_name}[/yellow]")
            
            elif choice == "2":
                level = Prompt.ask("Enter log level", choices=["ERROR", "WARNING", "INFO", "DEBUG"])
                filtered_logs = await self.orchestrator.cache_manager.get_agent_logs(level=level, limit=20)
                if filtered_logs:
                    self.console.print(f"[green]Found {len(filtered_logs)} {level} logs[/green]")
                    # Display filtered logs (simplified)
                    for log in filtered_logs:
                        self.console.print(f"{log.get('timestamp', 'N/A')} [{log.get('agent', 'N/A')}] {log.get('message', 'N/A')}")
                else:
                    self.console.print(f"[yellow]No {level} logs found[/yellow]")
            
        except Exception as e:
            self.console.print(f"[red]Error getting agent logs: {e}[/red]")
    
    async def agent_configuration(self):
        """Agent configuration."""
        try:
            self.console.print("[bold blue]Agent Configuration[/bold blue]")
            
            # Get agent configurations
            configs = await self.orchestrator.cache_manager.get_agent_configurations()
            
            if not configs:
                self.console.print("[yellow]No agent configurations found[/yellow]")
                return
            
            # Create configuration table
            table = Table(title="Agent Configurations")
            table.add_column("Agent", style="cyan")
            table.add_column("Type", style="white")
            table.add_column("Enabled", style="green")
            table.add_column("Interval", style="yellow")
            table.add_column("Last Updated", style="blue")
            
            for agent_id, config in configs.items():
                table.add_row(
                    config.get("name", agent_id),
                    config.get("type", "N/A"),
                    "Yes" if config.get("enabled", True) else "No",
                    f"{config.get('check_interval_seconds', 0)}s",
                    config.get("last_updated", "N/A")
                )
            
            self.console.print(table)
            
            # Configuration actions
            self.console.print("\n[bold]Configuration Actions:[/bold]")
            self.console.print("1. View agent configuration")
            self.console.print("2. Update agent configuration")
            self.console.print("3. Back to menu")
            
            choice = Prompt.ask("Select action", choices=["1", "2", "3"])
            
            if choice == "1":
                agent_name = Prompt.ask("Enter agent name")
                agent_config = None
                for agent_id, config in configs.items():
                    if config.get("name", agent_id) == agent_name:
                        agent_config = config
                        break
                
                if agent_config:
                    self.console.print(Panel(
                        f"Agent: {agent_config.get('name', 'N/A')}\n"
                        f"Type: {agent_config.get('type', 'N/A')}\n"
                        f"Enabled: {agent_config.get('enabled', True)}\n"
                        f"Check Interval: {agent_config.get('check_interval_seconds', 0)}s\n"
                        f"Timeout: {agent_config.get('timeout_seconds', 0)}s\n"
                        f"Retry Count: {agent_config.get('retry_count', 0)}\n"
                        f"Configuration: {agent_config.get('config', {})}",
                        title=f"{agent_name} Configuration",
                        border_style="blue"
                    ))
                else:
                    self.console.print("[red]Agent not found[/red]")
            
            elif choice == "2":
                self.console.print("[yellow]Agent configuration update not implemented in this version[/yellow]")
            
        except Exception as e:
            self.console.print(f"[red]Error getting agent configurations: {e}[/red]")
    
    async def view_configuration(self):
        """View configuration."""
        try:
            self.console.print("[bold blue]Configuration View[/bold blue]")
            
            # Get current configuration
            config = await self.orchestrator.cache_manager.get_configuration()
            
            # Create configuration table
            table = Table(title="Platform Configuration")
            table.add_column("Section", style="cyan")
            table.add_column("Setting", style="white")
            table.add_column("Value", style="green")
            table.add_column("Description", style="yellow")
            
            # Platform settings
            platform_config = config.get("platform", {})
            table.add_row("Platform", "Name", platform_config.get("name", "N/A"), "Platform name")
            table.add_row("Platform", "Environment", platform_config.get("environment", "N/A"), "Deployment environment")
            table.add_row("Platform", "Debug Mode", str(platform_config.get("debug", False)), "Debug logging enabled")
            table.add_row("Platform", "Log Level", platform_config.get("log_level", "N/A"), "Logging level")
            
            # Redis settings
            redis_config = config.get("redis", {})
            table.add_row("Redis", "Host", redis_config.get("host", "N/A"), "Redis host")
            table.add_row("Redis", "Port", str(redis_config.get("port", 0)), "Redis port")
            table.add_row("Redis", "Database", str(redis_config.get("database", 0)), "Redis database number")
            table.add_row("Redis", "Max Connections", str(redis_config.get("max_connections", 0)), "Maximum connections")
            
            # Scaling settings
            scaling_config = config.get("scaling", {})
            table.add_row("Scaling", "Enabled", str(scaling_config.get("enabled", False)), "Auto-scaling enabled")
            table.add_row("Scaling", "Min Nodes", str(scaling_config.get("min_nodes", 0)), "Minimum nodes")
            table.add_row("Scaling", "Max Nodes", str(scaling_config.get("max_nodes", 0)), "Maximum nodes")
            table.add_row("Scaling", "Scale Up Threshold", f"{scaling_config.get('scale_up_threshold', 0)}%", "CPU threshold for scaling up")
            table.add_row("Scaling", "Scale Down Threshold", f"{scaling_config.get('scale_down_threshold', 0)}%", "CPU threshold for scaling down")
            
            # Monitoring settings
            monitoring_config = config.get("monitoring", {})
            table.add_row("Monitoring", "Metrics Interval", f"{monitoring_config.get('metrics_interval', 0)}s", "Metrics collection interval")
            table.add_row("Monitoring", "Health Check Interval", f"{monitoring_config.get('health_check_interval', 0)}s", "Health check interval")
            table.add_row("Monitoring", "Alert Thresholds", str(monitoring_config.get("alert_thresholds", {})), "Alert configuration")
            
            # Security settings
            security_config = config.get("security", {})
            table.add_row("Security", "Authentication", str(security_config.get("authentication", {}).get("enabled", False)), "Authentication enabled")
            table.add_row("Security", "Encryption", str(security_config.get("encryption", {}).get("enabled", False)), "Data encryption enabled")
            table.add_row("Security", "Audit Logging", str(security_config.get("audit_logging", False)), "Audit logging enabled")
            
            self.console.print(table)
            
        except Exception as e:
            self.console.print(f"[red]Error viewing configuration: {e}[/red]")
    
    async def export_configuration(self):
        """Export configuration."""
        try:
            self.console.print("[bold blue]Export Configuration[/bold blue]")
            
            # Get current configuration
            config = await self.orchestrator.cache_manager.get_configuration()
            
            # Get export options
            self.console.print("Export options:")
            self.console.print("1. Export to JSON file")
            self.console.print("2. Export to YAML file")
            self.console.print("3. Display configuration")
            self.console.print("4. Back to menu")
            
            choice = Prompt.ask("Select export option", choices=["1", "2", "3", "4"])
            
            if choice == "1":
                filename = Prompt.ask("Enter filename", default="caching_platform_config.json")
                success = await self.orchestrator.cache_manager.export_configuration(filename, format="json")
                if success:
                    self.console.print(f"[green]Configuration exported to {filename}[/green]")
                else:
                    self.console.print("[red]Failed to export configuration[/red]")
            
            elif choice == "2":
                filename = Prompt.ask("Enter filename", default="caching_platform_config.yaml")
                success = await self.orchestrator.cache_manager.export_configuration(filename, format="yaml")
                if success:
                    self.console.print(f"[green]Configuration exported to {filename}[/green]")
                else:
                    self.console.print("[red]Failed to export configuration[/red]")
            
            elif choice == "3":
                import json
                config_json = json.dumps(config, indent=2, default=str)
                self.console.print(Panel(config_json, title="Current Configuration", border_style="blue"))
            
        except Exception as e:
            self.console.print(f"[red]Error exporting configuration: {e}[/red]")
    
    async def import_configuration(self):
        """Import configuration."""
        try:
            self.console.print("[bold blue]Import Configuration[/bold blue]")
            
            filename = Prompt.ask("Enter configuration file path")
            
            if not filename:
                self.console.print("[yellow]No filename provided[/yellow]")
                return
            
            # Confirm import
            if Confirm.ask(f"Import configuration from {filename}?"):
                success = await self.orchestrator.cache_manager.import_configuration(filename)
                if success:
                    self.console.print("[green]Configuration imported successfully[/green]")
                    
                    # Ask if restart is needed
                    if Confirm.ask("Restart platform to apply new configuration?"):
                        self.console.print("[yellow]Restarting platform...[/yellow]")
                        await self.orchestrator.shutdown()
                        await asyncio.sleep(2)
                        await self.orchestrator.initialize()
                        await self.orchestrator.start()
                        self.console.print("[green]Platform restarted with new configuration[/green]")
                else:
                    self.console.print("[red]Failed to import configuration[/red]")
            
        except Exception as e:
            self.console.print(f"[red]Error importing configuration: {e}[/red]")
    
    async def edit_configuration(self):
        """Edit configuration."""
        try:
            self.console.print("[bold blue]Edit Configuration[/bold blue]")
            
            self.console.print("Configuration editing options:")
            self.console.print("1. Edit platform settings")
            self.console.print("2. Edit Redis settings")
            self.console.print("3. Edit scaling settings")
            self.console.print("4. Edit monitoring settings")
            self.console.print("5. Edit security settings")
            self.console.print("6. Back to menu")
            
            choice = Prompt.ask("Select configuration section", choices=["1", "2", "3", "4", "5", "6"])
            
            if choice == "1":
                await self._edit_platform_settings()
            elif choice == "2":
                await self._edit_redis_settings()
            elif choice == "3":
                await self._edit_scaling_settings()
            elif choice == "4":
                await self._edit_monitoring_settings()
            elif choice == "5":
                await self._edit_security_settings()
            
        except Exception as e:
            self.console.print(f"[red]Error editing configuration: {e}[/red]")
    
    async def _edit_platform_settings(self):
        """Edit platform settings."""
        self.console.print("[yellow]Platform settings editing not implemented in this version[/yellow]")
    
    async def _edit_redis_settings(self):
        """Edit Redis settings."""
        self.console.print("[yellow]Redis settings editing not implemented in this version[/yellow]")
    
    async def _edit_scaling_settings(self):
        """Edit scaling settings."""
        self.console.print("[yellow]Scaling settings editing not implemented in this version[/yellow]")
    
    async def _edit_monitoring_settings(self):
        """Edit monitoring settings."""
        self.console.print("[yellow]Monitoring settings editing not implemented in this version[/yellow]")
    
    async def _edit_security_settings(self):
        """Edit security settings."""
        self.console.print("[yellow]Security settings editing not implemented in this version[/yellow]") 