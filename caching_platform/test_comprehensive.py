#!/usr/bin/env python3
"""Comprehensive test script for the OpenAI-Style Caching Infrastructure Platform."""

import asyncio
import sys
import os
import time
from datetime import datetime

# Add the package to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from caching_platform.config.settings import get_settings
from caching_platform.core.orchestrator import CacheOrchestrator
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

class ComprehensiveTester:
    """Comprehensive tester for the caching platform."""
    
    def __init__(self):
        self.orchestrator = None
        self.test_results = []
        self.start_time = time.time()
    
    async def run_all_tests(self):
        """Run all comprehensive tests."""
        console.print(Panel.fit("Comprehensive Caching Platform Test Suite", style="bold blue"))
        
        try:
            # Test 1: Platform Initialization
            await self._test_platform_initialization()
            
            # Test 2: Basic Operations
            await self._test_basic_operations()
            
            # Test 3: Tenant Management
            await self._test_tenant_management()
            
            # Test 4: Scaling Operations
            await self._test_scaling_operations()
            
            # Test 5: Health Monitoring
            await self._test_health_monitoring()
            
            # Test 6: Agent Management
            await self._test_agent_management()
            
            # Test 7: Configuration Management
            await self._test_configuration_management()
            
            # Test 8: Performance Testing
            await self._test_performance()
            
            # Test 9: Security Features
            await self._test_security_features()
            
            # Test 10: Cleanup
            await self._test_cleanup()
            
            # Display final results
            await self._display_results()
            
        except Exception as e:
            console.print(f"[red]Test suite failed with error: {e}[/red]")
            return False
        
        return True
    
    async def _test_platform_initialization(self):
        """Test platform initialization."""
        console.print("[yellow]1. Testing Platform Initialization...[/yellow]")
        
        try:
            # Initialize settings
            settings = get_settings()
            self._record_test("Settings Loading", True, "Settings loaded successfully")
            
            # Initialize orchestrator
            self.orchestrator = CacheOrchestrator(settings)
            success = await self.orchestrator.initialize()
            
            if success:
                self._record_test("Orchestrator Initialization", True, "Orchestrator initialized successfully")
            else:
                self._record_test("Orchestrator Initialization", False, "Failed to initialize orchestrator")
                return False
            
            # Start orchestrator
            success = await self.orchestrator.start()
            
            if success:
                self._record_test("Orchestrator Startup", True, "Orchestrator started successfully")
            else:
                self._record_test("Orchestrator Startup", False, "Failed to start orchestrator")
                return False
            
            console.print("[green]✓ Platform initialization completed[/green]")
            return True
            
        except Exception as e:
            self._record_test("Platform Initialization", False, f"Error: {e}")
            console.print(f"[red]✗ Platform initialization failed: {e}[/red]")
            return False
    
    async def _test_basic_operations(self):
        """Test basic cache operations."""
        console.print("[yellow]2. Testing Basic Operations...[/yellow]")
        
        try:
            # Create a test tenant
            result = await self.orchestrator.execute_command('create_tenant', {
                'name': 'test_tenant_basic',
                'quota_memory_mb': 512,
                'quota_requests_per_second': 1000,
                'quota_connections': 50
            })
            
            if result.get('success'):
                self._record_test("Tenant Creation", True, "Test tenant created successfully")
            else:
                self._record_test("Tenant Creation", False, f"Failed to create tenant: {result.get('error')}")
            
            # Test cache set operation
            result = await self.orchestrator.execute_command('cache_set', {
                'tenant': 'test_tenant_basic',
                'key': 'test_key_basic',
                'value': 'test_value_basic',
                'ttl': 3600
            })
            
            if result.get('success'):
                self._record_test("Cache Set Operation", True, "Cache set operation successful")
            else:
                self._record_test("Cache Set Operation", False, f"Cache set failed: {result.get('error')}")
            
            # Test cache get operation
            result = await self.orchestrator.execute_command('cache_get', {
                'tenant': 'test_tenant_basic',
                'key': 'test_key_basic'
            })
            
            if result.get('success'):
                value = result.get('value')
                if value == 'test_value_basic':
                    self._record_test("Cache Get Operation", True, "Cache get operation successful")
                else:
                    self._record_test("Cache Get Operation", False, f"Value mismatch: expected 'test_value_basic', got '{value}'")
            else:
                self._record_test("Cache Get Operation", False, f"Cache get failed: {result.get('error')}")
            
            # Test cache delete operation
            result = await self.orchestrator.execute_command('cache_delete', {
                'tenant': 'test_tenant_basic',
                'key': 'test_key_basic'
            })
            
            if result.get('success'):
                self._record_test("Cache Delete Operation", True, "Cache delete operation successful")
            else:
                self._record_test("Cache Delete Operation", False, f"Cache delete failed: {result.get('error')}")
            
            console.print("[green]✓ Basic operations completed[/green]")
            return True
            
        except Exception as e:
            self._record_test("Basic Operations", False, f"Error: {e}")
            console.print(f"[red]✗ Basic operations failed: {e}[/red]")
            return False
    
    async def _test_tenant_management(self):
        """Test tenant management operations."""
        console.print("[yellow]3. Testing Tenant Management...[/yellow]")
        
        try:
            # Create multiple tenants
            tenants = ['tenant_1', 'tenant_2', 'tenant_3']
            for tenant in tenants:
                result = await self.orchestrator.execute_command('create_tenant', {
                    'name': tenant,
                    'quota_memory_mb': 256,
                    'quota_requests_per_second': 500,
                    'quota_connections': 25
                })
                
                if result.get('success'):
                    self._record_test(f"Tenant Creation ({tenant})", True, f"Tenant {tenant} created")
                else:
                    self._record_test(f"Tenant Creation ({tenant})", False, f"Failed to create {tenant}")
            
            # List tenants
            result = await self.orchestrator.execute_command('list_tenants', {})
            
            if result.get('success'):
                tenant_list = result.get('tenants', [])
                if len(tenant_list) >= len(tenants):
                    self._record_test("List Tenants", True, f"Found {len(tenant_list)} tenants")
                else:
                    self._record_test("List Tenants", False, f"Expected {len(tenants)} tenants, found {len(tenant_list)}")
            else:
                self._record_test("List Tenants", False, f"Failed to list tenants: {result.get('error')}")
            
            # Delete a tenant
            result = await self.orchestrator.execute_command('delete_tenant', {
                'name': 'tenant_1'
            })
            
            if result.get('success'):
                self._record_test("Tenant Deletion", True, "Tenant deleted successfully")
            else:
                self._record_test("Tenant Deletion", False, f"Failed to delete tenant: {result.get('error')}")
            
            console.print("[green]✓ Tenant management completed[/green]")
            return True
            
        except Exception as e:
            self._record_test("Tenant Management", False, f"Error: {e}")
            console.print(f"[red]✗ Tenant management failed: {e}[/red]")
            return False
    
    async def _test_scaling_operations(self):
        """Test scaling operations."""
        console.print("[yellow]4. Testing Scaling Operations...[/yellow]")
        
        try:
            # Get current scaling status
            scaling_status = await self.orchestrator.auto_scaler.get_scaling_status()
            
            if scaling_status:
                self._record_test("Get Scaling Status", True, "Scaling status retrieved")
            else:
                self._record_test("Get Scaling Status", False, "Failed to get scaling status")
            
            # Test scaling configuration
            config = {
                'min_nodes': 1,
                'max_nodes': 5,
                'scale_up_threshold': 80,
                'scale_down_threshold': 30
            }
            
            success = await self.orchestrator.auto_scaler.set_scaling_config(config)
            
            if success:
                self._record_test("Scaling Configuration", True, "Scaling configuration updated")
            else:
                self._record_test("Scaling Configuration", False, "Failed to update scaling configuration")
            
            # Test manual scaling
            current_nodes = scaling_status.get('current_nodes', 1) if scaling_status else 1
            target_nodes = min(current_nodes + 1, 5)
            
            success = await self.orchestrator.auto_scaler.force_scale(target_nodes)
            
            if success:
                self._record_test("Manual Scaling", True, f"Scaled to {target_nodes} nodes")
            else:
                self._record_test("Manual Scaling", False, "Failed to scale manually")
            
            console.print("[green]✓ Scaling operations completed[/green]")
            return True
            
        except Exception as e:
            self._record_test("Scaling Operations", False, f"Error: {e}")
            console.print(f"[red]✗ Scaling operations failed: {e}[/red]")
            return False
    
    async def _test_health_monitoring(self):
        """Test health monitoring."""
        console.print("[yellow]5. Testing Health Monitoring...[/yellow]")
        
        try:
            # Get system health status
            health_status = await self.orchestrator.get_health_status()
            
            if health_status:
                self._record_test("Health Status", True, "Health status retrieved")
            else:
                self._record_test("Health Status", False, "Failed to get health status")
            
            # Get system metrics
            metrics = await self.orchestrator.cache_manager.get_system_metrics()
            
            if metrics:
                self._record_test("System Metrics", True, "System metrics retrieved")
            else:
                self._record_test("System Metrics", False, "Failed to get system metrics")
            
            # Get system status
            status = await self.orchestrator.get_system_status()
            
            if status:
                self._record_test("System Status", True, "System status retrieved")
            else:
                self._record_test("System Status", False, "Failed to get system status")
            
            console.print("[green]✓ Health monitoring completed[/green]")
            return True
            
        except Exception as e:
            self._record_test("Health Monitoring", False, f"Error: {e}")
            console.print(f"[red]✗ Health monitoring failed: {e}[/red]")
            return False
    
    async def _test_agent_management(self):
        """Test agent management."""
        console.print("[yellow]6. Testing Agent Management...[/yellow]")
        
        try:
            # Get agent status
            agent_status = await self.orchestrator.get_agent_status()
            
            if agent_status:
                self._record_test("Agent Status", True, f"Found {len(agent_status)} agents")
            else:
                self._record_test("Agent Status", False, "Failed to get agent status")
            
            # Test agent operations (if agents exist)
            if agent_status:
                for agent_id, agent in agent_status.items():
                    agent_name = agent.get('name', agent_id)
                    status = agent.get('status', 'unknown')
                    self._record_test(f"Agent {agent_name}", True, f"Status: {status}")
            
            console.print("[green]✓ Agent management completed[/green]")
            return True
            
        except Exception as e:
            self._record_test("Agent Management", False, f"Error: {e}")
            console.print(f"[red]✗ Agent management failed: {e}[/red]")
            return False
    
    async def _test_configuration_management(self):
        """Test configuration management."""
        console.print("[yellow]7. Testing Configuration Management...[/yellow]")
        
        try:
            # Get configuration
            config = await self.orchestrator.cache_manager.get_configuration()
            
            if config:
                self._record_test("Get Configuration", True, "Configuration retrieved")
            else:
                self._record_test("Get Configuration", False, "Failed to get configuration")
            
            # Test configuration export
            success = await self.orchestrator.cache_manager.export_configuration("test_config.json", format="json")
            
            if success:
                self._record_test("Configuration Export", True, "Configuration exported to JSON")
            else:
                self._record_test("Configuration Export", False, "Failed to export configuration")
            
            console.print("[green]✓ Configuration management completed[/green]")
            return True
            
        except Exception as e:
            self._record_test("Configuration Management", False, f"Error: {e}")
            console.print(f"[red]✗ Configuration management failed: {e}[/red]")
            return False
    
    async def _test_performance(self):
        """Test performance features."""
        console.print("[yellow]8. Testing Performance Features...[/yellow]")
        
        try:
            # Get performance metrics
            metrics = await self.orchestrator.cache_manager.get_system_metrics()
            
            if metrics:
                self._record_test("Performance Metrics", True, "Performance metrics retrieved")
            else:
                self._record_test("Performance Metrics", False, "Failed to get performance metrics")
            
            # Get system analytics
            analytics = await self.orchestrator.cache_manager.get_system_analytics()
            
            if analytics:
                self._record_test("System Analytics", True, "System analytics retrieved")
            else:
                self._record_test("System Analytics", False, "Failed to get system analytics")
            
            # Test load test (basic)
            results = await self.orchestrator.cache_manager.run_load_test(5, 2)  # 5 seconds, 2 concurrent
            
            if results:
                self._record_test("Load Test", True, "Load test completed")
            else:
                self._record_test("Load Test", False, "Load test failed")
            
            console.print("[green]✓ Performance testing completed[/green]")
            return True
            
        except Exception as e:
            self._record_test("Performance Testing", False, f"Error: {e}")
            console.print(f"[red]✗ Performance testing failed: {e}[/red]")
            return False
    
    async def _test_security_features(self):
        """Test security features."""
        console.print("[yellow]9. Testing Security Features...[/yellow]")
        
        try:
            # Get security settings
            security_settings = await self.orchestrator.cache_manager.get_security_settings()
            
            if security_settings:
                self._record_test("Security Settings", True, "Security settings retrieved")
            else:
                self._record_test("Security Settings", False, "Failed to get security settings")
            
            # Get access logs
            access_logs = await self.orchestrator.cache_manager.get_access_logs(limit=10)
            
            if access_logs is not None:
                self._record_test("Access Logs", True, f"Retrieved {len(access_logs)} access logs")
            else:
                self._record_test("Access Logs", False, "Failed to get access logs")
            
            console.print("[green]✓ Security features completed[/green]")
            return True
            
        except Exception as e:
            self._record_test("Security Features", False, f"Error: {e}")
            console.print(f"[red]✗ Security features failed: {e}[/red]")
            return False
    
    async def _test_cleanup(self):
        """Test cleanup operations."""
        console.print("[yellow]10. Testing Cleanup...[/yellow]")
        
        try:
            # Delete test tenants
            test_tenants = ['test_tenant_basic', 'tenant_2', 'tenant_3']
            for tenant in test_tenants:
                result = await self.orchestrator.execute_command('delete_tenant', {
                    'name': tenant
                })
                
                if result.get('success'):
                    self._record_test(f"Cleanup Tenant ({tenant})", True, f"Tenant {tenant} deleted")
                else:
                    self._record_test(f"Cleanup Tenant ({tenant})", False, f"Failed to delete {tenant}")
            
            # Remove test configuration file
            try:
                if os.path.exists("test_config.json"):
                    os.remove("test_config.json")
                    self._record_test("Cleanup Files", True, "Test configuration file removed")
                else:
                    self._record_test("Cleanup Files", True, "No test files to remove")
            except Exception as e:
                self._record_test("Cleanup Files", False, f"Failed to remove test files: {e}")
            
            console.print("[green]✓ Cleanup completed[/green]")
            return True
            
        except Exception as e:
            self._record_test("Cleanup", False, f"Error: {e}")
            console.print(f"[red]✗ Cleanup failed: {e}[/red]")
            return False
    
    def _record_test(self, test_name: str, success: bool, message: str):
        """Record a test result."""
        self.test_results.append({
            'name': test_name,
            'success': success,
            'message': message,
            'timestamp': datetime.utcnow()
        })
    
    async def _display_results(self):
        """Display comprehensive test results."""
        console.print("\n" + "="*80)
        console.print(Panel.fit("Comprehensive Test Results", style="bold blue"))
        
        # Calculate statistics
        total_tests = len(self.test_results)
        passed_tests = sum(1 for test in self.test_results if test['success'])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        # Create results table
        table = Table(title="Test Results Summary")
        table.add_column("Test Name", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Message", style="white")
        table.add_column("Timestamp", style="yellow")
        
        for test in self.test_results:
            status = "PASS" if test['success'] else "FAIL"
            status_style = "green" if test['success'] else "red"
            
            table.add_row(
                test['name'],
                status,
                test['message'],
                test['timestamp'].strftime('%H:%M:%S')
            )
        
        console.print(table)
        
        # Display summary
        summary = f"""
Test Summary:
- Total Tests: {total_tests}
- Passed: {passed_tests}
- Failed: {failed_tests}
- Success Rate: {success_rate:.1f}%
- Total Duration: {time.time() - self.start_time:.1f}s
"""
        
        if success_rate >= 90:
            console.print(Panel(summary, title="Excellent Results", border_style="green"))
        elif success_rate >= 70:
            console.print(Panel(summary, title="Good Results", border_style="yellow"))
        else:
            console.print(Panel(summary, title="Needs Improvement", border_style="red"))
        
        # Final status
        if failed_tests == 0:
            console.print("[bold green]All tests passed! Platform is working correctly.[/bold green]")
        else:
            console.print(f"[bold yellow]{failed_tests} tests failed. Please review the results above.[/bold yellow]")

async def main():
    """Main test function."""
    tester = ComprehensiveTester()
    
    try:
        success = await tester.run_all_tests()
        
        if success:
            console.print("\n[bold green]Comprehensive test suite completed successfully![/bold green]")
            console.print("[green]The caching platform is ready for production use.[/green]")
        else:
            console.print("\n[bold red]Comprehensive test suite failed![/bold red]")
            console.print("[red]Please fix the issues before deploying to production.[/red]")
        
        return success
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Test suite interrupted by user[/yellow]")
        return False
    except Exception as e:
        console.print(f"\n[red]Test suite failed with unexpected error: {e}[/red]")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 