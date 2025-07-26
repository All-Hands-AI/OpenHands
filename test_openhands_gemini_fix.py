#!/usr/bin/env python3
"""
Test OpenHands Gemini performance fix with tool calls.

This script tests the optimized Gemini configuration in OpenHands
that uses thinking={"budget_tokens": 128} instead of reasoning_effort,
using realistic tool call workflows.

Based on performance investigation showing:
- reasoning_effort='high' → ~25s (slow)
- reasoning_effort='medium' → ~27s (slowest)
- thinking={"budget_tokens": 128} → ~11s (fast, 2.4x speedup)
"""

import os

from openhands.core.config import LLMConfig
from openhands.llm.llm import LLM

# Import shared utilities
from test_utils import (
    check_credentials,
    run_tool_call_test,
)


def create_openhands_llm_completion_func(
    reasoning_effort: str = None, use_litellm_proxy: bool = False
):
    """Create completion function using OpenHands LLM with secure credentials."""

    if use_litellm_proxy:
        # Use LiteLLM proxy credentials
        api_key = os.getenv('LITELLM_PROXY_API_KEY')
        base_url = os.getenv('LITELLM_BASE_URL')

        if not api_key or not base_url:
            return None

        config = LLMConfig(
            model='litellm_proxy/gemini/gemini-2.5-pro',
            api_key=api_key,
            base_url=base_url,
            max_output_tokens=1000,
            temperature=0.0,
            reasoning_effort=reasoning_effort,
        )
    else:
        # Use direct Gemini API
        api_key = os.getenv('GEMINI_API_KEY')

        if not api_key:
            return None

        config = LLMConfig(
            model='gemini-2.5-pro',
            api_key=api_key,
            max_output_tokens=1000,
            temperature=0.0,
            reasoning_effort=reasoning_effort,
        )

    llm = LLM(config)

    def completion_func(messages, tools=None, **kwargs):
        return llm.completion(messages=messages, tools=tools)

    return completion_func


def test_openhands_gemini_configurations():
    """Test various OpenHands Gemini configurations with tool calls."""
    print('🚀 Testing OpenHands Gemini Configurations with Tool Calls')
    print('=' * 70)

    # Check credentials
    success, credentials = check_credentials()
    if not success:
        return []

    all_results = []

    # Test configurations
    test_configs = [
        {
            'name': 'OpenHands Direct API (No Reasoning)',
            'func': create_openhands_llm_completion_func(),
            'available': credentials['gemini_api_key'] is not None,
        },
        {
            'name': 'OpenHands Direct API (High Reasoning)',
            'func': create_openhands_llm_completion_func(reasoning_effort='high'),
            'available': credentials['gemini_api_key'] is not None,
        },
        {
            'name': 'OpenHands via LiteLLM Proxy (No Reasoning)',
            'func': create_openhands_llm_completion_func(use_litellm_proxy=True),
            'available': credentials['litellm_api_key'] is not None
            and credentials['litellm_base_url'] is not None,
        },
        {
            'name': 'OpenHands via LiteLLM Proxy (High Reasoning)',
            'func': create_openhands_llm_completion_func(
                reasoning_effort='high', use_litellm_proxy=True
            ),
            'available': credentials['litellm_api_key'] is not None
            and credentials['litellm_base_url'] is not None,
        },
    ]

    # Run tests
    for config in test_configs:
        if not config['available'] or config['func'] is None:
            print(f'\n⏭️  Skipping {config["name"]} - not available')
            continue

        print(f'\n🧪 Testing: {config["name"]}')
        print('-' * 50)

        try:
            result = run_tool_call_test(config['func'], config['name'])
            result_dict = result.to_dict()
            result_dict['config_name'] = config['name']
            all_results.append(result_dict)

            if result.success:
                print(f'✅ Success - Total: {result.total_duration:.3f}s')
                print(f'   Step 1 (Tool Request): {result.step1_duration:.3f}s')
                print(f'   Step 2 (Tool Response): {result.step2_duration:.3f}s')
                print(f'   Step 3 (Summary): {result.step3_duration:.3f}s')
                print(f'   Tool Result: {result.tool_call_result}')

                # Performance analysis
                if result.total_duration < 15:
                    print('   🎉 EXCELLENT: Fast performance!')
                elif result.total_duration < 25:
                    print('   👍 GOOD: Reasonable performance')
                else:
                    print('   🐌 SLOW: May need optimization')
            else:
                print(f'❌ Failed: {result.error}')

        except Exception as e:
            print(f'❌ Test failed with exception: {e}')
            all_results.append(
                {
                    'config_name': config['name'],
                    'success': False,
                    'error': str(e),
                    'total_duration': 0,
                }
            )

    return all_results


def analyze_openhands_results(results):
    """Analyze and compare OpenHands test results."""
    print('\n📊 OPENHANDS PERFORMANCE ANALYSIS')
    print('=' * 70)

    successful_results = [r for r in results if r['success']]

    if not successful_results:
        print('❌ No successful tests to analyze')
        return

    # Performance summary
    print('📈 Performance Summary:')
    sorted_results = sorted(successful_results, key=lambda x: x['total_duration'])
    for i, result in enumerate(sorted_results, 1):
        print(f'   {i}. {result["config_name"]}: {result["total_duration"]:.3f}s')

    # Group by API type
    direct_results = [r for r in successful_results if 'Direct API' in r['config_name']]
    proxy_results = [
        r for r in successful_results if 'LiteLLM Proxy' in r['config_name']
    ]

    # Compare direct vs proxy
    if direct_results and proxy_results:
        avg_direct = sum(r['total_duration'] for r in direct_results) / len(
            direct_results
        )
        avg_proxy = sum(r['total_duration'] for r in proxy_results) / len(proxy_results)

        print('\n🔄 Direct API vs LiteLLM Proxy:')
        print(f'   Average Direct API: {avg_direct:.3f}s')
        print(f'   Average LiteLLM Proxy: {avg_proxy:.3f}s')

        if avg_direct > 0:
            advantage = (
                avg_direct / avg_proxy
                if avg_proxy < avg_direct
                else avg_proxy / avg_direct
            )
            faster = 'LiteLLM Proxy' if avg_proxy < avg_direct else 'Direct API'
            print(f'   {faster} is {advantage:.2f}x faster')

    # Analyze reasoning effort impact
    no_reasoning_results = [
        r for r in successful_results if 'No Reasoning' in r['config_name']
    ]
    high_reasoning_results = [
        r for r in successful_results if 'High Reasoning' in r['config_name']
    ]

    if no_reasoning_results and high_reasoning_results:
        avg_no_reasoning = sum(r['total_duration'] for r in no_reasoning_results) / len(
            no_reasoning_results
        )
        avg_high_reasoning = sum(
            r['total_duration'] for r in high_reasoning_results
        ) / len(high_reasoning_results)

        print('\n🧠 Reasoning Effort Impact:')
        print(f'   Average No Reasoning: {avg_no_reasoning:.3f}s')
        print(f'   Average High Reasoning: {avg_high_reasoning:.3f}s')

        if avg_no_reasoning > 0:
            overhead = avg_high_reasoning / avg_no_reasoning
            print(f'   High Reasoning Overhead: {overhead:.2f}x')

    # Performance fix verification
    fastest = min(successful_results, key=lambda x: x['total_duration'])
    print('\n🏆 Performance Fix Verification:')
    print(f'   Fastest Configuration: {fastest["config_name"]}')
    print(f'   Duration: {fastest["total_duration"]:.3f}s')

    if fastest['total_duration'] < 15:
        print('   ✅ EXCELLENT: Performance fix is working!')
    elif fastest['total_duration'] < 25:
        print('   👍 GOOD: Significant improvement achieved')
    else:
        print('   ⚠️  NEEDS WORK: Still slower than expected')

    # Tool call accuracy
    correct_results = sum(
        1 for r in successful_results if r.get('result_correct', False)
    )
    accuracy = correct_results / len(successful_results) * 100
    print(
        f'\n🎯 Tool Call Accuracy: {accuracy:.1f}% ({correct_results}/{len(successful_results)})'
    )


def main():
    """Run OpenHands Gemini performance tests with tool calls."""
    print('🚀 OPENHANDS GEMINI PERFORMANCE TEST WITH TOOL CALLS')
    print('=' * 70)
    print(
        'This test verifies the OpenHands Gemini performance fix using tool call workflows'
    )
    print('Expected: ~11s with thinking budget fix vs ~25s with reasoning_effort')
    print()

    results = test_openhands_gemini_configurations()

    if results:
        analyze_openhands_results(results)
    else:
        print('❌ No test results to analyze')


if __name__ == '__main__':
    main()
