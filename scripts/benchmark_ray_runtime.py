#!/usr/bin/env python3
"""
Ray Runtime Performance Benchmark Script

This script validates the performance of the Ray runtime implementation
against established success criteria and generates detailed performance reports.

Usage:
    poetry run python scripts/benchmark_ray_runtime.py

The script will:
1. Initialize Ray runtime and measure startup time
2. Execute various OpenHands actions and measure latency
3. Test complex multi-step workflows
4. Validate against performance criteria
5. Generate detailed performance report

Results are saved to ray_runtime_benchmark_results.json
"""

import asyncio
import json
import os
import psutil
import statistics
import sys
import time
from pathlib import Path
import tempfile

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from openhands.core.config import OpenHandsConfig
from openhands.events import EventStream
from openhands.events.action import (
    CmdRunAction,
    FileReadAction,
    FileWriteAction,
    FileEditAction,
    IPythonRunCellAction,
)
from openhands.llm.llm_registry import LLMRegistry
from openhands.storage.memory import InMemoryFileStore
from openhands.runtime import get_runtime_cls


class RayRuntimeBenchmark:
    """Comprehensive benchmark suite for Ray runtime performance validation."""
    
    def __init__(self):
        self.results = []
        self.config = OpenHandsConfig()
        self.start_time = time.time()
    
    def measure_time(self, test_name):
        """Decorator to measure execution time and memory usage."""
        def decorator(func):
            async def wrapper(*args, **kwargs):
                process = psutil.Process()
                memory_before = process.memory_info().rss / 1024 / 1024  # MB
                
                start_time = time.perf_counter()
                try:
                    result = await func(*args, **kwargs)
                    success = True
                    error = None
                except Exception as e:
                    result = None
                    success = False
                    error = str(e)
                    print(f"❌ {test_name}: {error}")
                
                end_time = time.perf_counter()
                duration_ms = (end_time - start_time) * 1000
                
                memory_after = process.memory_info().rss / 1024 / 1024  # MB
                memory_delta = memory_after - memory_before
                
                self.results.append({
                    'test_name': test_name,
                    'duration_ms': duration_ms,
                    'memory_mb': memory_delta,
                    'success': success,
                    'error': error,
                    'timestamp': time.time()
                })
                
                if success:
                    print(f"✅ {test_name}: {duration_ms:.2f}ms")
                
                return result
            return wrapper
        return decorator
    
    async def run_comprehensive_benchmark(self):
        """Run the complete benchmark suite."""
        print("🚀 Ray Runtime Performance Benchmark")
        print("=" * 60)
        print(f"Started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Setup runtime
        file_store = InMemoryFileStore()
        event_stream = EventStream('ray-benchmark', file_store)
        llm_registry = LLMRegistry(self.config)
        
        ray_runtime_cls = get_runtime_cls('ray')
        
        # Phase 1: Runtime Initialization
        print("📋 Phase 1: Runtime Initialization")
        print("-" * 40)
        
        @self.measure_time("runtime_initialization")
        async def test_runtime_init():
            runtime = ray_runtime_cls(
                config=self.config,
                event_stream=event_stream,
                llm_registry=llm_registry,
                sid='ray-benchmark-session',
                headless_mode=True
            )
            await runtime.connect()
            return runtime
        
        runtime = await test_runtime_init()
        if not runtime:
            print("❌ Failed to initialize Ray runtime. Aborting benchmark.")
            return False
        
        # Phase 2: Basic Action Performance
        print("\n📋 Phase 2: Basic Action Performance")
        print("-" * 40)
        
        @self.measure_time("simple_command")
        async def test_simple_command():
            action = CmdRunAction(command="echo 'Ray benchmark test'")
            obs = runtime.run(action)
            assert obs.exit_code == 0, f"Command failed with exit code {obs.exit_code}"
            return obs
        
        @self.measure_time("complex_command")
        async def test_complex_command():
            action = CmdRunAction(command="python -c \"import math; [print(f'sqrt({i}) = {math.sqrt(i):.2f}') for i in range(1,6)]\"")
            obs = runtime.run(action)
            assert obs.exit_code == 0, f"Command failed with exit code {obs.exit_code}"
            return obs
        
        await test_simple_command()
        await test_complex_command()
        
        # Phase 3: File Operations
        print("\n📋 Phase 3: File Operations")
        print("-" * 40)
        
        @self.measure_time("file_write_small")
        async def test_file_write():
            content = "Ray benchmark test file\n" * 10
            action = FileWriteAction(path="test_small.txt", content=content)
            obs = runtime.write(action)
            return obs
        
        @self.measure_time("file_read_small")
        async def test_file_read():
            action = FileReadAction(path="test_small.txt")
            obs = runtime.read(action)
            assert "Ray benchmark test file" in obs.content
            return obs
        
        @self.measure_time("file_edit")
        async def test_file_edit():
            action = FileEditAction(
                path="test_small.txt",
                new_str="EDITED: Ray benchmark test file\n",
                old_str="Ray benchmark test file\n"
            )
            obs = runtime.edit(action)
            return obs
        
        @self.measure_time("file_write_large")
        async def test_large_file():
            # 1MB file test
            content = "Large file line for benchmarking purposes.\n" * 20000
            action = FileWriteAction(path="test_large.txt", content=content)
            obs = runtime.write(action)
            return obs
        
        @self.measure_time("file_read_large")
        async def test_large_file_read():
            action = FileReadAction(path="test_large.txt")
            obs = runtime.read(action)
            assert len(obs.content) > 800000  # Should be close to 1MB
            return obs
        
        await test_file_write()
        await test_file_read()
        await test_file_edit()
        await test_large_file()
        await test_large_file_read()
        
        # Phase 4: IPython Operations
        print("\n📋 Phase 4: IPython Operations")
        print("-" * 40)
        
        @self.measure_time("ipython_simple")
        async def test_ipython_simple():
            action = IPythonRunCellAction(code="result = 42 + 8\nprint(f'Answer: {result}')\nresult")
            obs = runtime.run_ipython(action)
            assert "50" in obs.content
            return obs
        
        @self.measure_time("ipython_computation")
        async def test_ipython_computation():
            code = '''
import math
import time

# Perform some computation
start = time.time()
results = []
for i in range(1000):
    val = math.sin(i * 0.01) * math.cos(i * 0.01)
    results.append(val)

end = time.time()
duration = end - start

print(f"Computed {len(results)} values in {duration:.4f} seconds")
print(f"Sample results: {results[:5]}")

{"count": len(results), "duration": duration, "sample": results[:3]}
'''
            action = IPythonRunCellAction(code=code)
            obs = runtime.run_ipython(action)
            assert "Computed 1000 values" in obs.content
            return obs
        
        await test_ipython_simple()
        await test_ipython_computation()
        
        # Phase 5: Multi-step Workflows
        print("\n📋 Phase 5: Multi-step Workflows")
        print("-" * 40)
        
        @self.measure_time("workflow_data_processing")
        async def test_data_workflow():
            # Step 1: Create data generation script
            script_content = '''
import json
import random

# Generate test data
data = {
    "experiment_id": "ray_benchmark_001",
    "timestamp": "2025-01-25T10:00:00Z",
    "measurements": [random.gauss(100, 15) for _ in range(1000)],
    "metadata": {
        "sensor_count": 5,
        "duration_minutes": 30
    }
}

# Save raw data
with open("raw_data.json", "w") as f:
    json.dump(data, f)

print(f"Generated {len(data['measurements'])} measurements")
'''
            runtime.write(FileWriteAction(path="generate_data.py", content=script_content))
            
            # Step 2: Execute data generation
            result = runtime.run(CmdRunAction(command="python generate_data.py"))
            assert result.exit_code == 0
            
            # Step 3: Process data with IPython
            analysis_code = '''
import json
import statistics

# Load data
with open("raw_data.json", "r") as f:
    data = json.load(f)

measurements = data["measurements"]

# Calculate statistics
stats = {
    "count": len(measurements),
    "mean": statistics.mean(measurements),
    "median": statistics.median(measurements),
    "std_dev": statistics.stdev(measurements),
    "min": min(measurements),
    "max": max(measurements)
}

# Save analysis
with open("analysis_results.json", "w") as f:
    json.dump(stats, f, indent=2)

print(f"Analyzed {stats['count']} measurements")
print(f"Mean: {stats['mean']:.2f}, Std Dev: {stats['std_dev']:.2f}")

stats
'''
            runtime.run_ipython(IPythonRunCellAction(code=analysis_code))
            
            # Step 4: Verify results
            results = runtime.read(FileReadAction(path="analysis_results.json"))
            assert "mean" in results.content and "std_dev" in results.content
            
            return True
        
        @self.measure_time("workflow_text_processing")
        async def test_text_workflow():
            # Multi-step text processing workflow
            
            # Create sample text files
            for i in range(5):
                content = f"Document {i}\n" + f"Content line {j} in document {i}\n" * 100 for j in range(10)
                content = f"Document {i}\n" + "".join([f"Content line {j} in document {i}\n" for j in range(100)])
                runtime.write(FileWriteAction(path=f"doc_{i}.txt", content=content))
            
            # Process with shell commands
            runtime.run(CmdRunAction(command="wc -l doc_*.txt > word_counts.txt"))
            
            # Combine and analyze
            combine_script = '''
import glob

all_docs = []
for filename in sorted(glob.glob("doc_*.txt")):
    with open(filename, "r") as f:
        content = f.read()
        all_docs.append({
            "filename": filename,
            "lines": len(content.split("\\n")),
            "chars": len(content)
        })

# Write summary
with open("text_summary.json", "w") as f:
    import json
    json.dump(all_docs, f, indent=2)

total_lines = sum(doc["lines"] for doc in all_docs)
print(f"Processed {len(all_docs)} documents with {total_lines} total lines")
'''
            runtime.write(FileWriteAction(path="combine_docs.py", content=combine_script))
            runtime.run(CmdRunAction(command="python combine_docs.py"))
            
            # Verify
            summary = runtime.read(FileReadAction(path="text_summary.json"))
            assert "filename" in summary.content
            
            return True
        
        await test_data_workflow()
        await test_text_workflow()
        
        # Phase 6: Stress Testing
        print("\n📋 Phase 6: Stress Testing")
        print("-" * 40)
        
        @self.measure_time("stress_rapid_commands")
        async def test_rapid_commands():
            for i in range(20):
                action = CmdRunAction(command=f"echo 'Rapid command {i}'")
                obs = runtime.run(action)
                assert obs.exit_code == 0
            return True
        
        @self.measure_time("stress_file_operations")
        async def test_file_stress():
            # Create, read, and modify multiple files rapidly
            for i in range(10):
                # Write
                content = f"Stress test file {i}\n" * 50
                runtime.write(FileWriteAction(path=f"stress_{i}.txt", content=content))
                
                # Read
                read_obs = runtime.read(FileReadAction(path=f"stress_{i}.txt"))
                assert f"Stress test file {i}" in read_obs.content
                
                # Edit
                runtime.edit(FileEditAction(
                    path=f"stress_{i}.txt",
                    new_str=f"MODIFIED stress test file {i}\n",
                    old_str=f"Stress test file {i}\n"
                ))
            
            return True
        
        await test_rapid_commands()
        await test_file_stress()
        
        # Cleanup
        runtime.close()
        
        # Generate report
        await self.generate_report()
        
        return True
    
    async def generate_report(self):
        """Generate comprehensive performance report."""
        print("\n" + "=" * 60)
        print("📊 PERFORMANCE BENCHMARK REPORT")
        print("=" * 60)
        
        # Calculate summary statistics
        successful_tests = [r for r in self.results if r['success']]
        failed_tests = [r for r in self.results if not r['success']]
        
        total_time = sum(r['duration_ms'] for r in successful_tests)
        avg_time = statistics.mean([r['duration_ms'] for r in successful_tests]) if successful_tests else 0
        
        # Exclude initialization time for action average
        action_tests = [r for r in successful_tests if r['test_name'] != 'runtime_initialization']
        avg_action_time = statistics.mean([r['duration_ms'] for r in action_tests]) if action_tests else 0
        
        print(f"📈 SUMMARY")
        print(f"  Total Tests: {len(self.results)}")
        print(f"  Successful: {len(successful_tests)}")
        print(f"  Failed: {len(failed_tests)}")
        print(f"  Success Rate: {len(successful_tests)/len(self.results)*100:.1f}%")
        print(f"  Total Time: {total_time:.2f}ms ({total_time/1000:.2f}s)")
        print(f"  Average Action Time: {avg_action_time:.2f}ms")
        print()
        
        # Detailed results
        print(f"🔍 DETAILED RESULTS")
        print(f"{'Test Name':<30} | {'Time (ms)':<10} | {'Memory (MB)':<12} | {'Status':<8}")
        print("-" * 70)
        
        for result in self.results:
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            print(f"{result['test_name']:<30} | {result['duration_ms']:>8.2f} | {result['memory_mb']:>10.2f} | {status}")
        
        # Performance analysis by category
        print(f"\n🎯 PERFORMANCE ANALYSIS")
        print("-" * 30)
        
        categories = {
            'Command Operations': [r for r in successful_tests if 'command' in r['test_name']],
            'File Operations': [r for r in successful_tests if 'file' in r['test_name']],
            'IPython Operations': [r for r in successful_tests if 'ipython' in r['test_name']],
            'Workflow Operations': [r for r in successful_tests if 'workflow' in r['test_name']],
            'Stress Tests': [r for r in successful_tests if 'stress' in r['test_name']]
        }
        
        for category, tests in categories.items():
            if tests:
                avg_time = statistics.mean([t['duration_ms'] for t in tests])
                print(f"  {category:<20}: {avg_time:>8.2f}ms average ({len(tests)} tests)")
        
        # Success criteria validation
        print(f"\n✅ SUCCESS CRITERIA VALIDATION")
        print("-" * 35)
        
        # Get specific test results
        init_time = next((r['duration_ms'] for r in self.results if r['test_name'] == 'runtime_initialization'), 0)
        
        # Criteria checks
        init_ok = init_time < 10000  # <10s
        action_ok = avg_action_time < 1000  # <1s
        max_time = max([r['duration_ms'] for r in successful_tests])
        max_ok = max_time < 5000  # <5s
        success_rate = len(successful_tests) / len(self.results) if self.results else 0
        reliability_ok = success_rate >= 0.95  # 95% success rate
        
        print(f"Runtime Initialization: {init_time:.2f}ms {'✅ PASS' if init_ok else '❌ FAIL'} (<10s)")
        print(f"Average Action Time: {avg_action_time:.2f}ms {'✅ PASS' if action_ok else '❌ FAIL'} (<1s)")
        print(f"Maximum Operation Time: {max_time:.2f}ms {'✅ PASS' if max_ok else '❌ FAIL'} (<5s)")
        print(f"Success Rate: {success_rate*100:.1f}% {'✅ PASS' if reliability_ok else '❌ FAIL'} (≥95%)")
        
        overall_pass = init_ok and action_ok and max_ok and reliability_ok
        
        print(f"\n🏆 OVERALL RESULT: {'✅ PASS' if overall_pass else '❌ FAIL'}")
        
        if overall_pass:
            print("Ray runtime meets all performance criteria!")
            print("🚀 Ready for production deployment and multi-worker distribution.")
        else:
            print("Ray runtime requires performance optimization before proceeding.")
        
        # Failed tests summary
        if failed_tests:
            print(f"\n❌ FAILED TESTS")
            for test in failed_tests:
                print(f"  {test['test_name']}: {test['error']}")
        
        # Save detailed results
        report_data = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'summary': {
                'total_tests': len(self.results),
                'successful_tests': len(successful_tests),
                'failed_tests': len(failed_tests),
                'success_rate': success_rate,
                'total_time_ms': total_time,
                'average_action_time_ms': avg_action_time
            },
            'success_criteria': {
                'initialization_ok': init_ok,
                'action_time_ok': action_ok,
                'max_time_ok': max_ok,
                'reliability_ok': reliability_ok,
                'overall_pass': overall_pass
            },
            'detailed_results': self.results,
            'performance_by_category': {
                category: {
                    'count': len(tests),
                    'average_time_ms': statistics.mean([t['duration_ms'] for t in tests]) if tests else 0,
                    'total_time_ms': sum([t['duration_ms'] for t in tests])
                }
                for category, tests in categories.items() if tests
            }
        }
        
        with open('ray_runtime_benchmark_results.json', 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"\n💾 Detailed results saved to: ray_runtime_benchmark_results.json")
        
        return overall_pass


async def main():
    """Main benchmark execution."""
    benchmark = RayRuntimeBenchmark()
    
    try:
        success = await benchmark.run_comprehensive_benchmark()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n⚠️ Benchmark interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Benchmark failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit_code = asyncio.run(main())
    sys.exit(exit_code)