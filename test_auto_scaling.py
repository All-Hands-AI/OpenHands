#!/usr/bin/env python3
"""Test Ray auto-scaling functionality."""

import asyncio
import os
import sys
import tempfile
import time
from pathlib import Path
from typing import List

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    import ray
    from openhands.core.config import OpenHandsConfig
    from openhands.events import EventStream
    from openhands.llm.llm_registry import LLMRegistry
    from openhands.runtime.impl.ray.ray_runtime import RayRuntime
    from openhands.runtime.impl.ray.auto_scaler import (
        RayAutoScaler, AutoScalingManager, ScalingConfig, ScalingDirection, ScalingStrategy
    )
    from openhands.runtime.impl.ray.worker_pool import RayWorkerPool
    
    print("✓ All imports successful")
except ImportError as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)


async def test_ray_auto_scaler_actor():
    """Test the Ray auto-scaler actor."""
    print("\n=== Testing Ray Auto-Scaler Actor ===")
    
    if not ray.is_initialized():
        ray.init(ignore_reinit_error=True)
    
    try:
        # Create scaling configuration
        config = ScalingConfig(
            min_workers=2,
            max_workers=10,
            scale_up_queue_threshold=5,
            scale_down_queue_threshold=1,
            cooldown_period=5.0,  # Short cooldown for testing
            strategy=ScalingStrategy.HYBRID
        )
        
        # Create auto-scaler actor
        auto_scaler = RayAutoScaler.remote(config)
        
        # Test health check
        health = ray.get(auto_scaler.health_check.remote())
        if health.get('status') == 'healthy':
            print("✓ Auto-scaler health check passed")
        else:
            print(f"✗ Auto-scaler health check failed: {health}")
            return False
        
        # Test metrics collection with mock worker pool stats
        mock_worker_stats = {
            'pending_requests': 3,
            'average_response_time': 1.5,
            'active_workers': 3,
            'total_pending': 3
        }
        
        metrics = ray.get(auto_scaler.collect_metrics.remote(mock_worker_stats))
        if metrics.queue_length == 3 and metrics.active_workers == 3:
            print("✓ Metrics collection working correctly")
        else:
            print(f"✗ Metrics collection failed: {metrics}")
            return False
        
        # Test scaling decision with high load
        high_load_stats = {
            'pending_requests': 10,
            'average_response_time': 6.0,
            'active_workers': 3,
            'total_pending': 10
        }
        
        high_load_metrics = ray.get(auto_scaler.collect_metrics.remote(high_load_stats))
        direction, amount = ray.get(auto_scaler.should_scale.remote(high_load_metrics))
        
        if direction == ScalingDirection.UP and amount > 0:
            print(f"✓ Scaling decision correct: {direction.value} by {amount} workers")
        else:
            print(f"✗ Scaling decision failed: {direction}, {amount}")
            return False
        
        # Test recording scaling decision
        ray.get(auto_scaler.record_scaling_decision.remote(
            direction, amount, "Test scaling up", True
        ))
        
        # Get scaling stats
        stats = ray.get(auto_scaler.get_scaling_stats.remote())
        if stats.get('total_decisions') == 1:
            print("✓ Scaling decision recorded correctly")
        else:
            print(f"✗ Scaling decision recording failed: {stats}")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Ray auto-scaler actor test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_auto_scaling_manager():
    """Test the AutoScalingManager class."""
    print("\n=== Testing Auto-Scaling Manager ===")
    
    if not ray.is_initialized():
        ray.init(ignore_reinit_error=True)
    
    try:
        # Create scaling configuration
        config = ScalingConfig(
            min_workers=2,
            max_workers=8,
            scale_up_queue_threshold=3,
            scale_down_queue_threshold=1,
            cooldown_period=2.0,  # Short cooldown for testing
            metrics_collection_interval=1.0,  # Fast collection for testing
            strategy=ScalingStrategy.DEMAND_BASED
        )
        
        # Create worker pool
        workspace_path = tempfile.mkdtemp()
        worker_pool = RayWorkerPool(
            pool_size=2,
            max_pool_size=8,
            workspace_path=workspace_path,
            env_vars={'TEST_AUTO_SCALING': 'true'}
        )
        
        await worker_pool.initialize()
        
        # Create auto-scaling manager
        auto_scaling_manager = AutoScalingManager(config, worker_pool)
        
        # Initialize auto-scaling
        await auto_scaling_manager.initialize()
        print("✓ Auto-scaling manager initialized")
        
        # Track scaling events
        scaling_events = []
        
        def scaling_callback(direction, amount, success):
            scaling_events.append({
                'direction': direction.value,
                'amount': amount,
                'success': success,
                'timestamp': time.time()
            })
        
        auto_scaling_manager.add_scaling_callback(scaling_callback)
        print("✓ Scaling callback registered")
        
        # Get initial stats
        stats = await auto_scaling_manager.get_stats()
        if isinstance(stats, dict) and 'config' in stats:
            print(f"✓ Auto-scaling stats working: {stats['config']['strategy']}")
        else:
            print(f"✗ Auto-scaling stats failed: {stats}")
            return False
        
        # Force a scaling check
        check_result = await auto_scaling_manager.force_scaling_check()
        if isinstance(check_result, dict) and 'direction' in check_result:
            print(f"✓ Force scaling check: {check_result['direction']} by {check_result['amount']}")
        else:
            print(f"✗ Force scaling check failed: {check_result}")
            return False
        
        # Wait briefly for monitoring loop to run
        await asyncio.sleep(3.0)
        
        # Check if monitoring is active
        final_stats = await auto_scaling_manager.get_stats()
        if final_stats.get('monitoring_active'):
            print("✓ Monitoring loop is active")
        else:
            print("✗ Monitoring loop not active")
            return False
        
        # Shutdown
        await auto_scaling_manager.shutdown()
        await worker_pool.shutdown()
        print("✓ Auto-scaling manager shutdown completed")
        
        return True
        
    except Exception as e:
        print(f"✗ Auto-scaling manager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_ray_runtime_auto_scaling():
    """Test auto-scaling integration with RayRuntime."""
    print("\n=== Testing Ray Runtime Auto-Scaling Integration ===")
    
    try:
        if not ray.is_initialized():
            ray.init(ignore_reinit_error=True)
        
        # Create runtime configuration with auto-scaling enabled
        config = OpenHandsConfig()
        
        # Mock event stream and LLM registry
        class MockEventStream:
            def subscribe(self, *args, **kwargs):
                pass
        
        # Create Ray runtime with auto-scaling
        runtime = RayRuntime(
            config=config,
            event_stream=MockEventStream(),
            llm_registry=LLMRegistry(config),
            sid="autoscaling_test_session"
        )
        
        print("✓ Ray runtime created with auto-scaling")
        
        # Connect to initialize all systems
        await runtime.connect()
        print("✓ Ray runtime connected with auto-scaling initialized")
        
        # Check auto-scaling status
        if runtime.is_auto_scaling_enabled():
            print("✓ Auto-scaling is enabled and initialized")
        else:
            print("✗ Auto-scaling not properly initialized")
            runtime.close()
            return False
        
        # Get auto-scaling statistics
        scaling_stats = await runtime.get_auto_scaling_stats()
        if isinstance(scaling_stats, dict) and 'config' in scaling_stats:
            print(f"✓ Auto-scaling stats: {scaling_stats['config']['min_workers']}-{scaling_stats['config']['max_workers']} workers")
        else:
            print(f"✗ Auto-scaling stats failed: {scaling_stats}")
            runtime.close()
            return False
        
        # Force a scaling check
        scaling_check = await runtime.force_scaling_check()
        if isinstance(scaling_check, dict) and 'direction' in scaling_check:
            print(f"✓ Force scaling check: {scaling_check['direction']} by {scaling_check.get('amount', 0)} workers")
            print(f"  Reason: {scaling_check.get('reason', 'No reason provided')}")
        else:
            print(f"✗ Force scaling check failed: {scaling_check}")
            runtime.close()
            return False
        
        # Test adding scaling callback
        callback_triggered = []
        
        def test_callback(direction, amount, success):
            callback_triggered.append(f"Scaling {direction.value} by {amount} ({'success' if success else 'failed'})")
        
        runtime.add_scaling_callback(test_callback)
        print("✓ Added scaling callback")
        
        # Wait for monitoring to run a few cycles
        await asyncio.sleep(5.0)
        
        # Get final statistics
        final_stats = await runtime.get_auto_scaling_stats()
        if final_stats.get('monitoring_active'):
            print("✓ Auto-scaling monitoring is active")
        else:
            print("✗ Auto-scaling monitoring not active")
            runtime.close()
            return False
        
        # Remove callback
        runtime.remove_scaling_callback(test_callback)
        print("✓ Removed scaling callback")
        
        # Cleanup
        runtime.close()
        print("✓ Runtime cleanup completed")
        
        return True
        
    except Exception as e:
        print(f"✗ Ray runtime auto-scaling test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_scaling_strategies():
    """Test different scaling strategies."""
    print("\n=== Testing Scaling Strategies ===")
    
    if not ray.is_initialized():
        ray.init(ignore_reinit_error=True)
    
    try:
        strategies_to_test = [
            ScalingStrategy.DEMAND_BASED,
            ScalingStrategy.RESOURCE_BASED,
            ScalingStrategy.HYBRID
        ]
        
        results = {}
        
        for strategy in strategies_to_test:
            print(f"\n  Testing {strategy.value} strategy...")
            
            # Create configuration for this strategy
            config = ScalingConfig(
                min_workers=2,
                max_workers=6,
                strategy=strategy,
                cooldown_period=1.0  # Short cooldown
            )
            
            # Create auto-scaler
            auto_scaler = RayAutoScaler.remote(config)
            
            # Test with high demand scenario
            high_demand_stats = {
                'pending_requests': 15,  # High queue
                'average_response_time': 8.0,  # Slow responses
                'active_workers': 2,
                'total_pending': 15
            }
            
            metrics = ray.get(auto_scaler.collect_metrics.remote(high_demand_stats))
            direction, amount = ray.get(auto_scaler.should_scale.remote(metrics))
            
            results[strategy.value] = {
                'direction': direction.value,
                'amount': amount,
                'queue_length': metrics.queue_length,
                'response_time': metrics.average_response_time
            }
            
            if direction == ScalingDirection.UP:
                print(f"    ✓ {strategy.value}: Correctly decided to scale UP by {amount} workers")
            else:
                print(f"    ✗ {strategy.value}: Should have scaled up, but decided {direction.value}")
        
        # Verify all strategies made reasonable decisions
        successful_strategies = sum(1 for r in results.values() if r['direction'] == 'up')
        
        if successful_strategies >= 2:  # At least 2 out of 3 should scale up
            print(f"✓ Scaling strategies test passed: {successful_strategies}/3 strategies scaled up")
            return True
        else:
            print(f"✗ Scaling strategies test failed: only {successful_strategies}/3 strategies scaled up")
            return False
        
    except Exception as e:
        print(f"✗ Scaling strategies test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all auto-scaling tests."""
    print("⚡ Ray Auto-Scaling Testing")
    print("="*50)
    
    tests = [
        ("Ray Auto-Scaler Actor", test_ray_auto_scaler_actor()),
        ("Auto-Scaling Manager", test_auto_scaling_manager()),
        ("Ray Runtime Auto-Scaling", test_ray_runtime_auto_scaling()),
        ("Scaling Strategies", test_scaling_strategies())
    ]
    
    results = []
    
    for name, test in tests:
        print(f"\n🧪 Running {name} test...")
        try:
            result = await test
            results.append((name, result))
        except Exception as e:
            print(f"✗ {name} test failed with exception: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "="*50)
    print("⚡ AUTO-SCALING TEST SUMMARY")
    print("="*50)
    
    passed = 0
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{len(results)} auto-scaling tests passed")
    
    if passed == len(results):
        print("🚀 All auto-scaling tests passed! Dynamic scaling is working correctly.")
    else:
        print("⚠️  Some auto-scaling tests failed. Review scaling implementation.")
    
    return passed == len(results)


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)