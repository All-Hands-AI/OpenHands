#!/usr/bin/env python3
"""
Comprehensive performance test runner with tool calls.

This script runs all performance tests using realistic tool call workflows
and provides detailed comparison to identify performance characteristics.
"""

import json
import sys
from typing import Any

# Import shared utilities
from test_utils import check_credentials


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

    try:
        import google.genai  # noqa: F401
    except ImportError:
        missing.append('google-genai')

    try:
        from openhands.core.config import LLMConfig  # noqa: F401
        from openhands.llm.llm import LLM  # noqa: F401
    except ImportError:
        print('⚠️  OpenHands modules not available - some tests will be skipped')

    if missing:
        print('❌ Missing dependencies:')
        for dep in missing:
            print(f'   - {dep}')
        print('\nInstall with:')
        for dep in missing:
            print(f'   pip install {dep}')
        return False

    return True


def run_all_tests():
    """Run all performance tests and collect results."""
    print('🚀 Running All Performance Tests with Tool Calls')
    print('=' * 70)

    all_results = []

    # Import and run each test module
    test_modules = [
        ('test_thinking_budget', 'Thinking Budget Tests'),
        ('test_litellm_comprehensive', 'LiteLLM Comprehensive Tests'),
        ('test_native_gemini', 'Native Gemini Tests'),
        ('test_openhands_gemini_fix', 'OpenHands Gemini Fix Tests'),
    ]

    for module_name, description in test_modules:
        print(f'\n🧪 {description}')
        print('-' * 50)

        try:
            # Import the module dynamically
            module = __import__(module_name)

            # Get the test function based on module
            if hasattr(module, 'test_thinking_budget_configurations'):
                results = module.test_thinking_budget_configurations()
            elif hasattr(module, 'test_litellm_configurations'):
                results = module.test_litellm_configurations()
            elif hasattr(module, 'test_native_gemini_configurations'):
                results = module.test_native_gemini_configurations()
            elif hasattr(module, 'test_openhands_gemini_configurations'):
                results = module.test_openhands_gemini_configurations()
            else:
                print(f'⚠️  No test function found in {module_name}')
                continue

            # Add module info to results
            for result in results:
                result['test_module'] = module_name
                result['test_description'] = description

            all_results.extend(results)
            print(f'✅ Completed {len(results)} tests from {module_name}')

        except ImportError as e:
            print(f'⚠️  Could not import {module_name}: {e}')
        except Exception as e:
            print(f'❌ Error running {module_name}: {e}')

    return all_results


def analyze_comprehensive_results(all_results: list[dict[str, Any]]):
    """Analyze results from all test modules."""
    print('\n📊 COMPREHENSIVE PERFORMANCE ANALYSIS')
    print('=' * 70)

    successful_results = [r for r in all_results if r.get('success', False)]

    if not successful_results:
        print('❌ No successful tests to analyze')
        return

    print(f'📈 Total Tests: {len(all_results)}')
    print(f'✅ Successful: {len(successful_results)}')
    print(f'❌ Failed: {len(all_results) - len(successful_results)}')

    # Group by test module
    by_module = {}
    for result in successful_results:
        module = result.get('test_module', 'unknown')
        by_module.setdefault(module, []).append(result)

    print('\n📋 Results by Test Module:')
    for module, results in by_module.items():
        avg_duration = sum(r.get('total_duration', 0) for r in results) / len(results)
        print(f'   {module}: {len(results)} tests, avg {avg_duration:.3f}s')

    # Overall performance ranking
    print('\n🏆 Overall Performance Ranking:')
    sorted_results = sorted(
        successful_results, key=lambda x: x.get('total_duration', float('inf'))
    )

    for i, result in enumerate(sorted_results[:10], 1):  # Top 10
        config_name = result.get('config_name', 'Unknown')
        duration = result.get('total_duration', 0)
        module = result.get('test_module', 'unknown')
        print(f'   {i:2d}. {config_name} ({module}): {duration:.3f}s')

    # Performance categories
    excellent = [r for r in successful_results if r.get('total_duration', 0) < 10]
    good = [r for r in successful_results if 10 <= r.get('total_duration', 0) < 20]
    slow = [r for r in successful_results if r.get('total_duration', 0) >= 20]

    print('\n⚡ Performance Categories:')
    print(f'   🎉 Excellent (<10s): {len(excellent)} tests')
    print(f'   👍 Good (10-20s): {len(good)} tests')
    print(f'   🐌 Slow (≥20s): {len(slow)} tests')

    # Tool call accuracy
    correct_results = sum(
        1 for r in successful_results if r.get('result_correct', False)
    )
    accuracy = (
        correct_results / len(successful_results) * 100 if successful_results else 0
    )
    print(
        f'\n🎯 Overall Tool Call Accuracy: {accuracy:.1f}% ({correct_results}/{len(successful_results)})'
    )

    # API comparison
    litellm_results = [
        r for r in successful_results if 'litellm' in r.get('test_module', '').lower()
    ]
    native_results = [
        r for r in successful_results if 'native' in r.get('test_module', '').lower()
    ]
    openhands_results = [
        r for r in successful_results if 'openhands' in r.get('test_module', '').lower()
    ]

    if litellm_results and native_results:
        avg_litellm = sum(r.get('total_duration', 0) for r in litellm_results) / len(
            litellm_results
        )
        avg_native = sum(r.get('total_duration', 0) for r in native_results) / len(
            native_results
        )

        print('\n🔄 API Comparison:')
        print(f'   LiteLLM Average: {avg_litellm:.3f}s ({len(litellm_results)} tests)')
        print(f'   Native API Average: {avg_native:.3f}s ({len(native_results)} tests)')

        if avg_native > 0:
            advantage = (
                avg_litellm / avg_native
                if avg_native < avg_litellm
                else avg_native / avg_litellm
            )
            faster = 'Native API' if avg_native < avg_litellm else 'LiteLLM'
            print(f'   {faster} is {advantage:.2f}x faster')

    if openhands_results:
        avg_openhands = sum(
            r.get('total_duration', 0) for r in openhands_results
        ) / len(openhands_results)
        print(
            f'   OpenHands Average: {avg_openhands:.3f}s ({len(openhands_results)} tests)'
        )

    # Save comprehensive results
    output_file = 'comprehensive_performance_results.json'
    with open(output_file, 'w') as f:
        json.dump(
            {
                'summary': {
                    'total_tests': len(all_results),
                    'successful_tests': len(successful_results),
                    'failed_tests': len(all_results) - len(successful_results),
                    'overall_accuracy': accuracy,
                },
                'results': all_results,
                'analysis': {
                    'by_module': {
                        module: len(results) for module, results in by_module.items()
                    },
                    'performance_categories': {
                        'excellent': len(excellent),
                        'good': len(good),
                        'slow': len(slow),
                    },
                },
            },
            f,
            indent=2,
        )

    print(f'\n💾 Comprehensive results saved to: {output_file}')


def main():
    """Run comprehensive performance tests with tool calls."""
    print('🚀 COMPREHENSIVE GEMINI PERFORMANCE INVESTIGATION WITH TOOL CALLS')
    print('=' * 70)
    print(
        'This comprehensive test suite uses realistic tool call workflows to evaluate:'
    )
    print('1. 🧠 Thinking Budget Configurations (optimized vs standard)')
    print('2. 🔄 LiteLLM Performance (various configurations)')
    print('3. 🎯 Native Google API Performance (baseline)')
    print('4. 🛠️  OpenHands Gemini Fix Verification (performance improvements)')
    print('5. 📊 Comparative Analysis (identify best configurations)')
    print()
    print('Each test uses a 3-step tool call workflow:')
    print('  Step 1: Ask LLM to calculate 45×126 using math tool')
    print('  Step 2: Execute tool (returns 5670) and send result back')
    print('  Step 3: Ask LLM to summarize the conversation')
    print()

    # Check prerequisites
    if not check_dependencies():
        return 1

    # Check credentials
    success, credentials = check_credentials()
    if not success:
        return 1

    print('✅ All dependencies and credentials available')
    print()

    # Run all tests
    all_results = run_all_tests()

    if all_results:
        analyze_comprehensive_results(all_results)

        print('\n💡 KEY INSIGHTS:')
        print('   Based on these tool call workflow results, you can determine:')
        print('   1. Which API approach (LiteLLM vs Native) performs best with tools')
        print(
            '   2. Impact of reasoning effort and thinking budget on tool call performance'
        )
        print('   3. Whether OpenHands optimizations improve real-world tool usage')
        print('   4. Tool call accuracy across different configurations')
        print('   5. Optimal configuration for production tool-enabled workflows')
    else:
        print('❌ No test results collected')
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
