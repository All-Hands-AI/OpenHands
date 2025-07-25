#!/usr/bin/env python3
"""
Comprehensive performance test runner.

This script runs all performance tests and provides a detailed comparison
to help identify the root cause of Gemini performance issues.
"""

import json
import os
import subprocess
import sys
from typing import Any


def check_dependencies():
    """Check if required dependencies are installed."""
    missing = []

    try:
        import litellm  # noqa: F401
    except ImportError:
        missing.append('litellm')

    try:
        import google.generativeai  # noqa: F401
    except ImportError:
        missing.append('google-generativeai')

    if missing:
        print('❌ Missing dependencies:')
        for dep in missing:
            print(f'   - {dep}')
        print('\nInstall with:')
        for dep in missing:
            print(f'   pip install {dep}')
        return False

    return True


def check_api_key():
    """Check if Google API key is set."""
    if not os.getenv('GOOGLE_API_KEY'):
        print('❌ GOOGLE_API_KEY environment variable not set')
        print('Please set your Google API key:')
        print('   export GOOGLE_API_KEY=your_key_here')
        return False
    return True


def run_test_script(script_name: str) -> dict[str, Any]:
    """Run a test script and capture its output."""
    print(f'\n🏃 Running {script_name}...')
    print('=' * 60)

    try:
        result = subprocess.run(
            [sys.executable, script_name],
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
        )

        return {
            'success': result.returncode == 0,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'error': 'Test timed out after 5 minutes',
            'stdout': '',
            'stderr': '',
        }
    except Exception as e:
        return {'success': False, 'error': str(e), 'stdout': '', 'stderr': ''}


def extract_performance_metrics(output: str) -> dict[str, Any]:
    """Extract performance metrics from test output."""
    lines = output.split('\n')
    metrics = {}

    # Look for duration patterns
    for line in lines:
        if 'Total Duration:' in line:
            try:
                duration = float(line.split('Total Duration:')[1].split('s')[0].strip())
                metrics.setdefault('durations', []).append(duration)
            except (ValueError, IndexError):
                pass
        elif 'Duration:' in line and 'Total' not in line:
            try:
                duration = float(line.split('Duration:')[1].split('s')[0].strip())
                metrics.setdefault('durations', []).append(duration)
            except (ValueError, IndexError):
                pass
        elif 'Time to First Chunk:' in line:
            try:
                ttfc = float(
                    line.split('Time to First Chunk:')[1].split('s')[0].strip()
                )
                metrics['time_to_first_chunk'] = ttfc
            except (ValueError, IndexError):
                pass

    # Calculate average duration if multiple found
    if 'durations' in metrics:
        metrics['avg_duration'] = sum(metrics['durations']) / len(metrics['durations'])
        metrics['min_duration'] = min(metrics['durations'])
        metrics['max_duration'] = max(metrics['durations'])

    return metrics


def main():
    """Run comprehensive performance tests."""
    print('🚀 COMPREHENSIVE GEMINI PERFORMANCE INVESTIGATION')
    print('=' * 60)
    print('This will test:')
    print('1. Pure LiteLLM performance with different configs')
    print('2. OpenHands-style LiteLLM calls')
    print('3. Native Google Generative AI performance')
    print('4. Comparative analysis')
    print()

    # Check prerequisites
    if not check_dependencies():
        return 1

    if not check_api_key():
        return 1

    # Test scripts to run
    test_scripts = [
        'test_litellm_performance.py',
        'test_openhands_litellm.py',
        'test_native_gemini.py',
    ]

    results = {}

    # Run each test
    for script in test_scripts:
        if not os.path.exists(script):
            print(f'❌ Test script {script} not found')
            continue

        result = run_test_script(script)
        results[script] = result

        if result['success']:
            print(result['stdout'])
            if result['stderr']:
                print('STDERR:', result['stderr'])
        else:
            print(f'❌ {script} failed:')
            if 'error' in result:
                print(f'   Error: {result["error"]}')
            if result['stderr']:
                print(f'   STDERR: {result["stderr"]}')

    # Analyze results
    print('\n' + '=' * 60)
    print('🔍 COMPREHENSIVE ANALYSIS')
    print('=' * 60)

    analysis = {}

    for script, result in results.items():
        if result['success']:
            metrics = extract_performance_metrics(result['stdout'])
            analysis[script] = metrics

            print(f'\n📊 {script}:')
            if 'avg_duration' in metrics:
                print(f'   Average Duration: {metrics["avg_duration"]:.3f}s')
                print(f'   Min Duration: {metrics["min_duration"]:.3f}s')
                print(f'   Max Duration: {metrics["max_duration"]:.3f}s')
            if 'time_to_first_chunk' in metrics:
                print(f'   Time to First Chunk: {metrics["time_to_first_chunk"]:.3f}s')

    # Compare performance
    if len(analysis) >= 2:
        print('\n🏆 PERFORMANCE COMPARISON:')

        # Find fastest and slowest
        avg_durations = {}
        for script, metrics in analysis.items():
            if 'avg_duration' in metrics:
                avg_durations[script] = metrics['avg_duration']

        if avg_durations:
            fastest_script = min(avg_durations.keys(), key=lambda k: avg_durations[k])
            slowest_script = max(avg_durations.keys(), key=lambda k: avg_durations[k])

            print(
                f'   🥇 Fastest: {fastest_script} ({avg_durations[fastest_script]:.3f}s)'
            )
            print(
                f'   🐌 Slowest: {slowest_script} ({avg_durations[slowest_script]:.3f}s)'
            )

            if avg_durations[fastest_script] > 0:
                speedup = avg_durations[slowest_script] / avg_durations[fastest_script]
                print(f'   📈 Performance Difference: {speedup:.2f}x')

    # Conclusions
    print('\n💡 CONCLUSIONS:')
    print('   Based on these results, you can determine:')
    print('   1. Is LiteLLM itself slow with Gemini?')
    print('   2. Are OpenHands-specific configs causing slowdown?')
    print('   3. How much faster is native Google API?')
    print('   4. Which specific parameters affect performance most?')

    # Save detailed results
    with open('performance_test_results.json', 'w') as f:
        json.dump({'results': results, 'analysis': analysis}, f, indent=2)

    print('\n💾 Detailed results saved to: performance_test_results.json')

    return 0


if __name__ == '__main__':
    sys.exit(main())
