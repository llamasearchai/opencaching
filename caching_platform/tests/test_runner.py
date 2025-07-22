#!/usr/bin/env python3
"""
Test runner for the caching platform
"""

import asyncio
import time
import random
import json
from typing import Dict, Any, List
from dataclasses import dataclass
import aiohttp
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class TestResult:
    """Test result data structure"""
    name: str
    success: bool
    duration: float
    error: str = None
    details: Dict[str, Any] = None

class TestRunner:
    """Comprehensive test runner for the caching platform"""
    
    def __init__(self, orchestrator, output_dir: str = "./tests"):
        self.orchestrator = orchestrator
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.results: List[TestResult] = []
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all test suites"""
        start_time = time.time()
        
        logger.info("Starting comprehensive test suite")
        
        # Test suites to run
        test_suites = [
            self._test_basic_operations,
            self._test_multi_tenant_isolation,
            self._test_scaling_functionality,
            self._test_health_monitoring,
            self._test_security_features,
            self._test_performance_metrics,
            self._test_agent_functionality,
            self._test_cluster_operations,
        ]
        
        for test_suite in test_suites:
            try:
                await test_suite()
            except Exception as e:
                logger.exception(f"Test suite {test_suite.__name__} failed: {e}")
                self.results.append(TestResult(
                    name=test_suite.__name__,
                    success=False,
                    duration=0,
                    error=str(e)
                ))
        
        duration = time.time() - start_time
        
        # Generate test report
        report = self._generate_test_report(duration)
        
        # Save results
        await self._save_test_results(report)
        
        return report
    
    async def run_load_tests(self, duration: int = 60) -> Dict[str, Any]:
        """Run load tests for specified duration"""
        logger.info(f"Starting load tests for {duration} seconds")
        
        start_time = time.time()
        end_time = start_time + duration
        
        # Load test configuration
        config = {
            'concurrent_clients': 50,
            'operations_per_second': 1000,
            'test_duration': duration,
            'key_space_size': 10000,
            'value_size_bytes': 1024,
        }
        
        # Metrics tracking
        metrics = {
            'total_operations': 0,
            'successful_operations': 0,
            'failed_operations': 0,
            'response_times': [],
            'errors': [],
            'throughput_samples': [],
        }
        
        # Create test tenants
        test_tenants = await self._create_test_tenants(5)
        
        # Run concurrent load
        tasks = []
        for i in range(config['concurrent_clients']):
            task = asyncio.create_task(
                self._load_test_worker(
                    worker_id=i,
                    end_time=end_time,
                    config=config,
                    metrics=metrics,
                    tenants=test_tenants
                )
            )
            tasks.append(task)
        
        # Monitor progress
        monitor_task = asyncio.create_task(
            self._monitor_load_test(metrics, duration)
        )
        
        # Wait for completion
        await asyncio.gather(*tasks, monitor_task)
        
        # Calculate final metrics
        total_duration = time.time() - start_time
        avg_response_time = sum(metrics['response_times']) / len(metrics['response_times']) if metrics['response_times'] else 0
        throughput = metrics['total_operations'] / total_duration
        
        # Cleanup test tenants
        await self._cleanup_test_tenants(test_tenants)
        
        report = {
            'success': metrics['failed_operations'] == 0,
            'duration': total_duration,
            'config': config,
            'metrics': {
                'total_operations': metrics['total_operations'],
                'successful_operations': metrics['successful_operations'],
                'failed_operations': metrics['failed_operations'],
                'success_rate': metrics['successful_operations'] / metrics['total_operations'] if metrics['total_operations'] > 0 else 0,
                'average_response_time': avg_response_time,
                'throughput_ops_per_sec': throughput,
                'p95_response_time': self._calculate_percentile(metrics['response_times'], 95),
                'p99_response_time': self._calculate_percentile(metrics['response_times'], 99),
            },
            'errors': metrics['errors'][:100],  # Limit error samples
        }
        
        await self._save_load_test_results(report)
        
        return report
    
    async def _test_basic_operations(self):
        """Test basic cache operations"""
        logger.info("Testing basic cache operations")
        
        test_tenant = "test_basic"
        
        # Create test tenant
        await self.orchestrator.execute_command('create_tenant', {
            'name': test_tenant,
            'quota_memory': 100,
            'quota_requests': 1000
        })
        
        # Test SET operation
        start_time = time.time()
        result = await self.orchestrator.execute_command('cache_set', {
            'tenant': test_tenant,
            'key': 'test_key',
            'value': 'test_value',
            'ttl': 3600
        })
        duration = time.time() - start_time
        
        self.results.append(TestResult(
            name="basic_set_operation",
            success=result.get('success', False),
            duration=duration,
            error=result.get('error'),
            details={'result': result}
        ))
        
        # Test GET operation
        start_time = time.time()
        result = await self.orchestrator.execute_command('cache_get', {
            'tenant': test_tenant,
            'key': 'test_key'
        })
        duration = time.time() - start_time
        
        self.results.append(TestResult(
            name="basic_get_operation",
            success=result.get('success', False) and result.get('value') == 'test_value',
            duration=duration,
            error=result.get('error'),
            details={'result': result}
        ))
        
        # Test DELETE operation
        start_time = time.time()
        result = await self.orchestrator.execute_command('cache_delete', {
            'tenant': test_tenant,
            'key': 'test_key'
        })
        duration = time.time() - start_time
        
        self.results.append(TestResult(
            name="basic_delete_operation",
            success=result.get('success', False),
            duration=duration,
            error=result.get('error'),
            details={'result': result}
        ))
        
        # Cleanup
        await self.orchestrator.execute_command('delete_tenant', {'name': test_tenant})
    
    async def _test_multi_tenant_isolation(self):
        """Test multi-tenant isolation"""
        logger.info("Testing multi-tenant isolation")
        
        tenant1 = "test_tenant_1"
        tenant2 = "test_tenant_2"
        
        # Create test tenants
        for tenant in [tenant1, tenant2]:
            await self.orchestrator.execute_command('create_tenant', {
                'name': tenant,
                'quota_memory': 100,
                'quota_requests': 1000
            })
        
        # Set same key in both tenants
        key = "isolation_test_key"
        value1 = "tenant1_value"
        value2 = "tenant2_value"
        
        start_time = time.time()
        
        # Set values
        result1 = await self.orchestrator.execute_command('cache_set', {
            'tenant': tenant1,
            'key': key,
            'value': value1
        })
        
        result2 = await self.orchestrator.execute_command('cache_set', {
            'tenant': tenant2,
            'key': key,
            'value': value2
        })
        
        # Get values and verify isolation
        get_result1 = await self.orchestrator.execute_command('cache_get', {
            'tenant': tenant1,
            'key': key
        })
        
        get_result2 = await self.orchestrator.execute_command('cache_get', {
            'tenant': tenant2,
            'key': key
        })
        
        duration = time.time() - start_time
        
        # Verify isolation
        isolation_success = (
            get_result1.get('value') == value1 and
            get_result2.get('value') == value2 and
            get_result1.get('value') != get_result2.get('value')
        )
        
        self.results.append(TestResult(
            name="multi_tenant_isolation",
            success=isolation_success,
            duration=duration,
            details={
                'tenant1_value': get_result1.get('value'),
                'tenant2_value': get_result2.get('value'),
                'expected_isolation': True
            }
        ))
        
        # Cleanup
        for tenant in [tenant1, tenant2]:
            await self.orchestrator.execute_command('delete_tenant', {'name': tenant})
    
    async def _test_scaling_functionality(self):
        """Test auto-scaling functionality"""
        logger.info("Testing scaling functionality")
        
        start_time = time.time()
        
        # Get current scaling status
        scaling_status = await self.orchestrator.execute_command('get_scaling_status')
        
        # Test scaling configuration
        scaling_config = {
            'enabled': True,
            'min_nodes': 2,
            'max_nodes': 10,
            'target_cpu': 70,
            'target_memory': 80
        }
        
        config_result = await self.orchestrator.execute_command('configure_scaling', scaling_config)
        
        # Verify configuration was applied
        new_status = await self.orchestrator.execute_command('get_scaling_status')
        
        duration = time.time() - start_time
        
        self.results.append(TestResult(
            name="scaling_configuration",
            success=config_result.get('success', False),
            duration=duration,
            details={
                'original_status': scaling_status,
                'new_status': new_status,
                'config_applied': config_result
            }
        ))
    
    async def _test_health_monitoring(self):
        """Test health monitoring functionality"""
        logger.info("Testing health monitoring")
        
        start_time = time.time()
        
        # Get system health
        health_status = await self.orchestrator.get_health_status()
        
        # Get detailed component health
        components = ['redis', 'agents', 'network', 'storage']
        component_health = {}
        
        for component in components:
            component_status = await self.orchestrator.execute_command('get_component_health', {
                'component': component
            })
            component_health[component] = component_status
        
        duration = time.time() - start_time
        
        overall_health = health_status.get('healthy', False)
        
        self.results.append(TestResult(
            name="health_monitoring",
            success=overall_health,
            duration=duration,
            details={
                'overall_health': health_status,
                'component_health': component_health
            }
        ))
    
    async def _test_security_features(self):
        """Test security features"""
        logger.info("Testing security features")
        
        start_time = time.time()
        
        # Test authentication
        auth_result = await self.orchestrator.execute_command('test_authentication', {
            'username': 'test_user',
            'password': 'test_password'
        })
        
        # Test authorization
        authz_result = await self.orchestrator.execute_command('test_authorization', {
            'user': 'test_user',
            'resource': 'tenant:test',
            'action': 'read'
        })
        
        # Test encryption
        encryption_result = await self.orchestrator.execute_command('test_encryption', {
            'data': 'sensitive_test_data'
        })
        
        duration = time.time() - start_time
        
        security_success = all([
            auth_result.get('success', False),
            authz_result.get('success', False),
            encryption_result.get('success', False)
        ])
        
        self.results.append(TestResult(
            name="security_features",
            success=security_success,
            duration=duration,
            details={
                'authentication': auth_result,
                'authorization': authz_result,
                'encryption': encryption_result
            }
        ))
    
    async def _test_performance_metrics(self):
        """Test performance metrics collection"""
        logger.info("Testing performance metrics")
        
        start_time = time.time()
        
        # Get system metrics
        metrics_result = await self.orchestrator.execute_command('get_metrics', {
            'limit': 100
        })
        
        # Verify required metrics are present
        required_metrics = [
            'cpu_usage_percent',
            'memory_usage_percent',
            'cache_hit_ratio',
            'request_latency',
            'throughput_ops_per_sec'
        ]
        
        metrics_data = metrics_result.get('metrics', {})
        metrics_present = all(metric in metrics_data for metric in required_metrics)
        
        duration = time.time() - start_time
        
        self.results.append(TestResult(
            name="performance_metrics",
            success=metrics_result.get('success', False) and metrics_present,
            duration=duration,
            details={
                'metrics_available': list(metrics_data.keys()),
                'required_metrics': required_metrics,
                'all_present': metrics_present
            }
        ))
    
    async def _test_agent_functionality(self):
        """Test autonomous agent functionality"""
        logger.info("Testing agent functionality")
        
        start_time = time.time()
        
        # Get agent status
        agents = ['scaling_agent', 'optimization_agent', 'healing_agent', 'prediction_agent']
        agent_status = {}
        
        for agent in agents:
            status = await self.orchestrator.execute_command('get_agent_status', {
                'agent': agent
            })
            agent_status[agent] = status
        
        # Test agent decision making
        decision_result = await self.orchestrator.execute_command('test_agent_decisions')
        
        duration = time.time() - start_time
        
        agents_healthy = all(
            status.get('healthy', False) for status in agent_status.values()
        )
        
        self.results.append(TestResult(
            name="agent_functionality",
            success=agents_healthy and decision_result.get('success', False),
            duration=duration,
            details={
                'agent_status': agent_status,
                'decision_test': decision_result
            }
        ))
    
    async def _test_cluster_operations(self):
        """Test cluster operations"""
        logger.info("Testing cluster operations")
        
        start_time = time.time()
        
        # Get cluster status
        cluster_status = await self.orchestrator.execute_command('get_cluster_status')
        
        # Test cluster health check
        health_check = await self.orchestrator.execute_command('cluster_health_check')
        
        # Test node operations (if safe to do so)
        node_info = await self.orchestrator.execute_command('get_node_info')
        
        # Test cluster metrics
        cluster_metrics = await self.orchestrator.execute_command('get_cluster_metrics')
        
        duration = time.time() - start_time
        
        cluster_healthy = (
            cluster_status.get('healthy', False) and
            health_check.get('success', False) and
            len(node_info.get('nodes', [])) > 0
        )
        
        self.results.append(TestResult(
            name="cluster_operations",
            success=cluster_healthy,
            duration=duration,
            details={
                'cluster_status': cluster_status,
                'health_check': health_check,
                'node_info': node_info,
                'cluster_metrics': cluster_metrics
            }
        ))
    
    async def _load_test_worker(self, worker_id: int, end_time: float, config: Dict[str, Any], 
                               metrics: Dict[str, Any], tenants: List[str]):
        """Individual load test worker"""
        operations = ['get', 'set', 'delete', 'incr']
        operation_weights = [0.7, 0.2, 0.05, 0.05]  # Read-heavy workload
        
        while time.time() < end_time:
            try:
                # Select random tenant and operation
                tenant = random.choice(tenants)
                operation = random.choices(operations, weights=operation_weights)[0]
                
                # Generate test data
                key = f"load_test_key_{random.randint(1, config['key_space_size'])}"
                value = 'x' * config['value_size_bytes']
                
                # Execute operation
                start_op_time = time.time()
                
                if operation == 'set':
                    result = await self.orchestrator.execute_command('cache_set', {
                        'tenant': tenant,
                        'key': key,
                        'value': value,
                        'ttl': 3600
                    })
                elif operation == 'get':
                    result = await self.orchestrator.execute_command('cache_get', {
                        'tenant': tenant,
                        'key': key
                    })
                elif operation == 'delete':
                    result = await self.orchestrator.execute_command('cache_delete', {
                        'tenant': tenant,
                        'key': key
                    })
                elif operation == 'incr':
                    result = await self.orchestrator.execute_command('cache_incr', {
                        'tenant': tenant,
                        'key': f"counter_{random.randint(1, 100)}"
                    })
                
                op_duration = time.time() - start_op_time
                
                # Update metrics
                metrics['total_operations'] += 1
                metrics['response_times'].append(op_duration)
                
                if result.get('success', False):
                    metrics['successful_operations'] += 1
                else:
                    metrics['failed_operations'] += 1
                    metrics['errors'].append({
                        'worker_id': worker_id,
                        'operation': operation,
                        'error': result.get('error', 'Unknown error'),
                        'timestamp': time.time()
                    })
                
                # Rate limiting
                await asyncio.sleep(1.0 / (config['operations_per_second'] / config['concurrent_clients']))
                
            except Exception as e:
                metrics['failed_operations'] += 1
                metrics['errors'].append({
                    'worker_id': worker_id,
                    'error': str(e),
                    'timestamp': time.time()
                })
                await asyncio.sleep(0.1)  # Brief pause on error
    
    async def _monitor_load_test(self, metrics: Dict[str, Any], duration: int):
        """Monitor load test progress"""
        start_time = time.time()
        last_sample_time = start_time
        last_operations = 0
        
        while time.time() - start_time < duration:
            await asyncio.sleep(10)  # Sample every 10 seconds
            
            current_time = time.time()
            current_operations = metrics['total_operations']
            
            # Calculate throughput for this sample
            time_delta = current_time - last_sample_time
            ops_delta = current_operations - last_operations
            
            if time_delta > 0:
                throughput = ops_delta / time_delta
                metrics['throughput_samples'].append({
                    'timestamp': current_time,
                    'throughput': throughput,
                    'total_operations': current_operations,
                    'success_rate': metrics['successful_operations'] / current_operations if current_operations > 0 else 0
                })
            
            last_sample_time = current_time
            last_operations = current_operations
            
            # Log progress
            elapsed = current_time - start_time
            remaining = duration - elapsed
            logger.info(f"Load test progress: {elapsed:.1f}s elapsed, {remaining:.1f}s remaining, "
                       f"{current_operations} operations, {throughput:.1f} ops/sec")
    
    async def _create_test_tenants(self, count: int) -> List[str]:
        """Create test tenants for load testing"""
        tenants = []
        
        for i in range(count):
            tenant_name = f"load_test_tenant_{i}"
            result = await self.orchestrator.execute_command('create_tenant', {
                'name': tenant_name,
                'quota_memory': 1024,  # 1GB per tenant
                'quota_requests': 10000  # 10k requests per second
            })
            
            if result.get('success', False):
                tenants.append(tenant_name)
            else:
                logger.warning(f"Failed to create test tenant {tenant_name}: {result.get('error')}")
        
        return tenants
    
    async def _cleanup_test_tenants(self, tenants: List[str]):
        """Clean up test tenants"""
        for tenant in tenants:
            try:
                await self.orchestrator.execute_command('delete_tenant', {'name': tenant})
            except Exception as e:
                logger.warning(f"Failed to cleanup tenant {tenant}: {e}")
    
    def _calculate_percentile(self, values: List[float], percentile: int) -> float:
        """Calculate percentile from list of values"""
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        index = int((percentile / 100.0) * len(sorted_values))
        index = min(index, len(sorted_values) - 1)
        return sorted_values[index]
    
    def _generate_test_report(self, duration: float) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        total_tests = len(self.results)
        successful_tests = sum(1 for result in self.results if result.success)
        failed_tests = total_tests - successful_tests
        
        # Calculate statistics
        test_durations = [result.duration for result in self.results]
        avg_duration = sum(test_durations) / len(test_durations) if test_durations else 0
        
        # Group results by category
        results_by_category = {}
        for result in self.results:
            category = result.name.split('_')[0]
            if category not in results_by_category:
                results_by_category[category] = []
            results_by_category[category].append(result)
        
        return {
            'success': failed_tests == 0,
            'total_tests': total_tests,
            'successful_tests': successful_tests,
            'failed_tests': failed_tests,
            'success_rate': successful_tests / total_tests if total_tests > 0 else 0,
            'duration': duration,
            'average_test_duration': avg_duration,
            'results_by_category': {
                category: {
                    'total': len(results),
                    'successful': sum(1 for r in results if r.success),
                    'failed': sum(1 for r in results if not r.success)
                }
                for category, results in results_by_category.items()
            },
            'detailed_results': [
                {
                    'name': result.name,
                    'success': result.success,
                    'duration': result.duration,
                    'error': result.error,
                    'details': result.details
                }
                for result in self.results
            ],
            'errors': [result.error for result in self.results if result.error],
            'timestamp': time.time()
        }
    
    async def _save_test_results(self, report: Dict[str, Any]):
        """Save test results to file"""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = self.output_dir / f"test_results_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"Test results saved to {filename}")
    
    async def _save_load_test_results(self, report: Dict[str, Any]):
        """Save load test results to file"""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = self.output_dir / f"load_test_results_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"Load test results saved to {filename}")

# Standalone test execution
async def main():
    """Main function for standalone test execution"""
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description='Caching Platform Test Runner')
    parser.add_argument('--load-test', action='store_true', help='Run load tests')
    parser.add_argument('--duration', type=int, default=60, help='Load test duration in seconds')
    parser.add_argument('--output-dir', default='./test_results', help='Output directory for results')
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Import and initialize platform
    try:
        from core.orchestrator import CacheOrchestrator
        orchestrator = CacheOrchestrator()
        await orchestrator.initialize()
        
        # Create test runner
        test_runner = TestRunner(orchestrator, args.output_dir)
        
        # Run tests
        if args.load_test:
            results = await test_runner.run_load_tests(args.duration)
            print(f"\nLoad Test Results:")
            print(f"Duration: {results['duration']:.2f}s")
            print(f"Total Operations: {results['metrics']['total_operations']}")
            print(f"Success Rate: {results['metrics']['success_rate']:.2%}")
            print(f"Throughput: {results['metrics']['throughput_ops_per_sec']:.1f} ops/sec")
            print(f"Avg Response Time: {results['metrics']['average_response_time']*1000:.2f}ms")
            print(f"P95 Response Time: {results['metrics']['p95_response_time']*1000:.2f}ms")
            print(f"P99 Response Time: {results['metrics']['p99_response_time']*1000:.2f}ms")
        else:
            results = await test_runner.run_all_tests()
            print(f"\nTest Results:")
            print(f"Total Tests: {results['total_tests']}")
            print(f"Successful: {results['successful_tests']}")
            print(f"Failed: {results['failed_tests']}")
            print(f"Success Rate: {results['success_rate']:.2%}")
            print(f"Duration: {results['duration']:.2f}s")
        
        # Exit with appropriate code
        sys.exit(0 if results['success'] else 1)
        
    except Exception as e:
        logger.exception(f"Test execution failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    asyncio.run(main())