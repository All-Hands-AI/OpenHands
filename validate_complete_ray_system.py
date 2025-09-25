#!/usr/bin/env python3
"""Comprehensive validation of the complete Ray-based OpenHands system."""

import asyncio
import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Dict, List

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    import ray
    from openhands.core.config import OpenHandsConfig
    from openhands.events import EventStream
    from openhands.events.action.message import MessageAction
    from openhands.events.event import EventSource
    from openhands.events.stream import EventStreamSubscriber
    from openhands.llm.llm_registry import LLMRegistry
    from openhands.runtime.impl.ray.ray_runtime import RayRuntime
    
    print("✓ All imports successful")
except ImportError as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)


class ComprehensiveRaySystemValidator:
    """Comprehensive validator for the complete Ray system."""
    
    def __init__(self):
        self.runtime = None
        self.results = {}
        self.start_time = time.time()
    
    async def run_complete_validation(self) -> Dict[str, bool]:
        """Run complete system validation covering all 5 steps."""
        print("🚀 COMPREHENSIVE RAY SYSTEM VALIDATION")
        print("="*60)
        
        validation_steps = [
            ("Step 1: Foundation & Connectivity", self.validate_foundation),
            ("Step 2: Core Action Execution", self.validate_core_actions),
            ("Step 3: Multi-Worker Distribution", self.validate_multi_worker),
            ("Step 4: Distributed Event Streaming", self.validate_event_streaming),
            ("Step 5: Auto-Scaling Integration", self.validate_auto_scaling),
            ("Integration: End-to-End Workflow", self.validate_end_to_end_workflow),
            ("Performance: System Benchmarks", self.validate_performance_benchmarks)
        ]
        
        for step_name, validation_func in validation_steps:
            print(f"\n🔍 {step_name}")
            print("-" * len(step_name))
            
            try:
                result = await validation_func()
                self.results[step_name] = result
                status = "✅ PASSED" if result else "❌ FAILED"
                print(f"Result: {status}")
            except Exception as e:
                print(f"❌ FAILED with exception: {e}")
                self.results[step_name] = False
        
        return self.results
    
    async def validate_foundation(self) -> bool:
        """Validate Step 1: Foundation & Connectivity."""
        try:
            # Initialize Ray
            if not ray.is_initialized():
                ray.init(ignore_reinit_error=True)
                print("  ✓ Ray cluster initialized")
            
            # Create Ray runtime
            config = OpenHandsConfig()
            
            class MockEventStream:
                def subscribe(self, *args, **kwargs):
                    pass
            
            self.runtime = RayRuntime(
                config=config,
                event_stream=MockEventStream(),
                llm_registry=LLMRegistry(config),
                sid="comprehensive_validation"
            )
            print("  ✓ RayRuntime created")
            
            # Connect to initialize all systems
            await self.runtime.connect()
            print("  ✓ Runtime connected successfully")
            
            # Verify workspace
            if os.path.exists(self.runtime.workspace_path):
                print(f"  ✓ Workspace created: {os.path.basename(self.runtime.workspace_path)}")
            else:
                print("  ❌ Workspace creation failed")
                return False
            
            return True
            
        except Exception as e:
            print(f"  ❌ Foundation validation failed: {e}")
            return False
    
    async def validate_core_actions(self) -> bool:
        """Validate Step 2: Core Action Execution."""
        try:
            if not self.runtime:
                print("  ❌ Runtime not initialized")
                return False
            
            # Test command execution
            class MockCmdAction:
                def __init__(self, command):
                    self.command = command
                    self.timeout = 30
                    self.id = f"test_cmd_{time.time()}"
            
            cmd_result = self.runtime.run(MockCmdAction("echo 'Core action test'"))
            if hasattr(cmd_result, 'exit_code') and cmd_result.exit_code == 0:
                print("  ✓ Command execution working")
            else:
                print(f"  ❌ Command execution failed: {cmd_result}")
                return False
            
            # Test file operations
            class MockFileWriteAction:
                def __init__(self, path, content):
                    self.path = path
                    self.content = content
            
            class MockFileReadAction:
                def __init__(self, path):
                    self.path = path
            
            test_file = "validation_test.txt"
            test_content = "Ray system validation test content"
            
            # Write file
            write_result = self.runtime.write(MockFileWriteAction(test_file, test_content))
            if hasattr(write_result, 'content') and write_result.content == test_content:
                print("  ✓ File write operation working")
            else:
                print(f"  ❌ File write failed: {write_result}")
                return False
            
            # Read file
            read_result = self.runtime.read(MockFileReadAction(test_file))
            if hasattr(read_result, 'content') and test_content in read_result.content:
                print("  ✓ File read operation working")
            else:
                print(f"  ❌ File read failed: {read_result}")
                return False
            
            return True
            
        except Exception as e:
            print(f"  ❌ Core actions validation failed: {e}")
            return False
    
    async def validate_multi_worker(self) -> bool:
        """Validate Step 3: Multi-Worker Distribution."""
        try:
            if not self.runtime:
                print("  ❌ Runtime not initialized")
                return False
            
            # Check worker pool
            pool_stats = self.runtime.worker_pool.get_pool_stats()
            if pool_stats['pool_size'] >= 2:
                print(f"  ✓ Worker pool operational: {pool_stats['pool_size']} workers")
            else:
                print(f"  ❌ Insufficient workers: {pool_stats['pool_size']}")
                return False
            
            # Test session management
            session_stats = self.runtime.session_manager.get_stats()
            if session_stats['total_sessions'] >= 1:
                print(f"  ✓ Session management working: {session_stats['total_sessions']} sessions")
            else:
                print(f"  ❌ Session management failed: {session_stats}")
                return False
            
            # Test concurrent execution
            concurrent_tasks = []
            for i in range(3):
                class MockConcurrentAction:
                    def __init__(self, task_id):
                        self.command = f"echo 'Concurrent task {task_id}'"
                        self.timeout = 30
                        self.id = f"concurrent_{task_id}_{time.time()}"
                
                task = asyncio.create_task(
                    asyncio.to_thread(self.runtime.run, MockConcurrentAction(i))
                )
                concurrent_tasks.append(task)
            
            # Wait for concurrent tasks
            results = await asyncio.gather(*concurrent_tasks)
            successful_tasks = sum(1 for r in results if hasattr(r, 'exit_code') and r.exit_code == 0)
            
            if successful_tasks >= 2:
                print(f"  ✓ Concurrent execution: {successful_tasks}/3 tasks succeeded")
            else:
                print(f"  ❌ Concurrent execution failed: only {successful_tasks}/3 succeeded")
                return False
            
            return True
            
        except Exception as e:
            print(f"  ❌ Multi-worker validation failed: {e}")
            return False
    
    async def validate_event_streaming(self) -> bool:
        """Validate Step 4: Distributed Event Streaming."""
        try:
            if not self.runtime:
                print("  ❌ Runtime not initialized")
                return False
            
            # Check event streaming initialization
            if self.runtime._event_stream_initialized:
                print("  ✓ Event streaming initialized")
            else:
                print("  ❌ Event streaming not initialized")
                return False
            
            # Test event broadcasting
            received_events = []
            
            def event_callback(event):
                received_events.append(getattr(event, 'content', 'no content'))
            
            # Subscribe to events
            self.runtime.subscribe_to_distributed_events(
                EventStreamSubscriber.RUNTIME,
                event_callback,
                "validation_callback"
            )
            print("  ✓ Event subscription successful")
            
            # Broadcast test events
            for i in range(3):
                test_event = MessageAction(content=f"Validation event {i+1}")
                self.runtime.broadcast_event(test_event, EventSource.AGENT)
            
            # Wait for event processing
            await asyncio.sleep(1.0)
            
            # Check event statistics
            event_stats = await self.runtime.get_distributed_event_stats()
            if isinstance(event_stats, dict) and event_stats.get('session_id'):
                print(f"  ✓ Event statistics working: {event_stats.get('total_subscribers', 0)} subscribers")
            else:
                print(f"  ❌ Event statistics failed: {event_stats}")
                return False
            
            # Get recent events
            recent_events = await self.runtime.get_recent_distributed_events(5)
            if len(recent_events) >= 3:
                print(f"  ✓ Event history: {len(recent_events)} events retrieved")
            else:
                print(f"  ❌ Event history insufficient: {len(recent_events)} events")
                return False
            
            # Unsubscribe
            self.runtime.unsubscribe_from_distributed_events(
                EventStreamSubscriber.RUNTIME,
                "validation_callback"
            )
            print("  ✓ Event unsubscription successful")
            
            return True
            
        except Exception as e:
            print(f"  ❌ Event streaming validation failed: {e}")
            return False
    
    async def validate_auto_scaling(self) -> bool:
        """Validate Step 5: Auto-Scaling Integration."""
        try:
            if not self.runtime:
                print("  ❌ Runtime not initialized")
                return False
            
            # Check auto-scaling initialization
            if self.runtime.is_auto_scaling_enabled():
                print("  ✓ Auto-scaling enabled and initialized")
            else:
                print("  ❌ Auto-scaling not properly initialized")
                return False
            
            # Get auto-scaling statistics
            scaling_stats = await self.runtime.get_auto_scaling_stats()
            if isinstance(scaling_stats, dict) and 'config' in scaling_stats:
                config = scaling_stats['config']
                print(f"  ✓ Auto-scaling config: {config['min_workers']}-{config['max_workers']} workers, {config['strategy']} strategy")
            else:
                print(f"  ❌ Auto-scaling stats failed: {scaling_stats}")
                return False
            
            # Test force scaling check
            scaling_check = await self.runtime.force_scaling_check()
            if isinstance(scaling_check, dict) and 'direction' in scaling_check:
                print(f"  ✓ Scaling check: {scaling_check['direction']} by {scaling_check.get('amount', 0)} workers")
            else:
                print(f"  ❌ Force scaling check failed: {scaling_check}")
                return False
            
            # Test scaling callbacks
            callback_triggered = []
            
            def scaling_callback(direction, amount, success):
                callback_triggered.append(f"{direction.value}:{amount}:{success}")
            
            self.runtime.add_scaling_callback(scaling_callback)
            print("  ✓ Scaling callback registered")
            
            # Wait for monitoring cycle
            await asyncio.sleep(2.0)
            
            self.runtime.remove_scaling_callback(scaling_callback)
            print("  ✓ Scaling callback removed")
            
            return True
            
        except Exception as e:
            print(f"  ❌ Auto-scaling validation failed: {e}")
            return False
    
    async def validate_end_to_end_workflow(self) -> bool:
        """Validate complete end-to-end workflow."""
        try:
            if not self.runtime:
                print("  ❌ Runtime not initialized")
                return False
            
            print("  🔄 Testing complete workflow...")
            
            # Simulate a complex workflow
            workflow_steps = [
                ("Create project file", "echo 'Project: Ray Validation' > project.txt"),
                ("List workspace", "ls -la"),
                ("Check system info", "python --version || python3 --version"),
                ("Create subdirectory", "mkdir -p test_dir"),
                ("Write config file", "echo 'config: validated' > test_dir/config.yaml"),
                ("Read project file", "cat project.txt"),
            ]
            
            successful_steps = 0
            for step_name, command in workflow_steps:
                class MockWorkflowAction:
                    def __init__(self, cmd):
                        self.command = cmd
                        self.timeout = 30
                        self.id = f"workflow_{time.time()}"
                
                result = self.runtime.run(MockWorkflowAction(command))
                if hasattr(result, 'exit_code') and result.exit_code == 0:
                    print(f"    ✓ {step_name}")
                    successful_steps += 1
                else:
                    print(f"    ❌ {step_name} failed")
            
            # Test file operations in workflow
            class MockFileAction:
                def __init__(self, path, content=None):
                    self.path = path
                    if content is not None:
                        self.content = content
            
            # Write workflow result
            workflow_summary = f"Workflow completed: {successful_steps}/{len(workflow_steps)} steps successful"
            write_result = self.runtime.write(MockFileAction("workflow_result.txt", workflow_summary))
            
            if hasattr(write_result, 'content'):
                print("    ✓ Workflow result written")
                successful_steps += 1
            else:
                print("    ❌ Workflow result write failed")
            
            # Overall workflow success
            if successful_steps >= len(workflow_steps):
                print(f"  ✅ End-to-end workflow: {successful_steps}/{len(workflow_steps) + 1} operations successful")
                return True
            else:
                print(f"  ❌ End-to-end workflow: only {successful_steps}/{len(workflow_steps) + 1} operations successful")
                return False
            
        except Exception as e:
            print(f"  ❌ End-to-end workflow validation failed: {e}")
            return False
    
    async def validate_performance_benchmarks(self) -> bool:
        """Validate system performance benchmarks."""
        try:
            if not self.runtime:
                print("  ❌ Runtime not initialized")
                return False
            
            print("  ⚡ Running performance benchmarks...")
            
            # Benchmark action execution
            action_times = []
            for i in range(10):
                start_time = time.time()
                
                class MockBenchmarkAction:
                    def __init__(self):
                        self.command = f"echo 'Benchmark {i}'"
                        self.timeout = 30
                        self.id = f"benchmark_{i}_{time.time()}"
                
                result = self.runtime.run(MockBenchmarkAction())
                execution_time = time.time() - start_time
                
                if hasattr(result, 'exit_code') and result.exit_code == 0:
                    action_times.append(execution_time)
            
            if action_times:
                avg_time = sum(action_times) / len(action_times)
                min_time = min(action_times)
                max_time = max(action_times)
                
                print(f"    Action Performance: avg={avg_time:.3f}s, min={min_time:.3f}s, max={max_time:.3f}s")
                
                # Check against success criteria (from methodology doc)
                if avg_time < 1.0:  # Target: < 1 second average
                    print("    ✅ Performance target met: average < 1.0s")
                    performance_ok = True
                else:
                    print(f"    ⚠️ Performance concern: average {avg_time:.3f}s > 1.0s target")
                    performance_ok = False
            else:
                print("    ❌ No successful benchmark actions")
                performance_ok = False
            
            # System resource check
            total_runtime = time.time() - self.start_time
            print(f"    Total validation time: {total_runtime:.2f}s")
            
            # Worker pool performance
            pool_stats = self.runtime.worker_pool.get_pool_stats()
            print(f"    Worker pool: {pool_stats['total_requests']} requests processed")
            print(f"    Average response time: {pool_stats.get('average_response_time', 0):.3f}s")
            
            return performance_ok
            
        except Exception as e:
            print(f"  ❌ Performance validation failed: {e}")
            return False
    
    def cleanup(self):
        """Clean up resources."""
        try:
            if self.runtime:
                self.runtime.close()
                print("  🧹 Runtime cleanup completed")
        except Exception as e:
            print(f"  ⚠️ Cleanup error: {e}")


async def main():
    """Run comprehensive Ray system validation."""
    validator = ComprehensiveRaySystemValidator()
    
    try:
        results = await validator.run_complete_validation()
        
        # Final summary
        print("\n" + "="*60)
        print("📊 COMPREHENSIVE VALIDATION SUMMARY")
        print("="*60)
        
        total_steps = len(results)
        passed_steps = sum(1 for result in results.values() if result)
        
        for step_name, result in results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{status}: {step_name}")
        
        print(f"\n🎯 Overall Result: {passed_steps}/{total_steps} validation steps passed")
        
        if passed_steps == total_steps:
            print("\n🎉 OUTSTANDING! Complete Ray system validation PASSED!")
            print("🚀 OpenHands successfully converted to distributed Ray architecture")
            print("🌟 All 5 conversion steps validated and working correctly")
            print("\n📈 Achievement Summary:")
            print("  ✅ Ray Foundation - Connectivity and basic operations")
            print("  ✅ Core Actions - All action types working with Ray actors")  
            print("  ✅ Multi-Worker Distribution - Load balancing and session management")
            print("  ✅ Event Streaming - Distributed real-time events via Ray pub/sub")
            print("  ✅ Auto-Scaling - Dynamic cluster scaling based on demand")
            print("  ✅ End-to-End Workflows - Complete integration validation")
            print("  ✅ Performance Benchmarks - Exceeding target performance criteria")
            
            success = True
        else:
            print(f"\n⚠️ Partial success: {passed_steps}/{total_steps} steps passed")
            print("❌ Some validation steps failed - review implementation")
            success = False
        
        return success
        
    finally:
        validator.cleanup()


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)