#!/usr/bin/env python3
"""
Comprehensive LiteLLM performance test for Gemini with tool calls.

This script tests LiteLLM performance with various configurations including:
1. Different parameter combinations (streaming, temperature, etc.)
2. OpenHands-style configuration and calls
3. Reasoning effort and thinking budget parameters
4. Tool call workflows for realistic testing

Uses secure credential handling with LITELLM_PROXY_API_KEY and LITELLM_BASE_URL.
"""

import os
from functools import partial

import litellm

# Import shared utilities
from test_utils import (
    check_credentials,
    run_tool_call_test,
)


def create_litellm_completion_func(**config_params):
    """Create LiteLLM completion function with secure credentials."""
    api_key = os.getenv('LITELLM_PROXY_API_KEY')
    base_url = os.getenv('LITELLM_BASE_URL')

    if not api_key or not base_url:
        return None

    def completion_func(messages, tools=None, **kwargs):
        params = {
            'model': 'litellm_proxy/gemini/gemini-2.5-pro',
            'messages': messages,
            'api_key': api_key,
            'base_url': base_url,
            'drop_params': True,
            **config_params,  # Apply configuration parameters
        }

        if tools:
            params['tools'] = tools

        return litellm.completion(**params)

    return completion_func


def create_openhands_completion_func(**additional_params):
    """Create completion function exactly like OpenHands does."""
    api_key = os.getenv('LITELLM_PROXY_API_KEY')
    base_url = os.getenv('LITELLM_BASE_URL')

    if not api_key or not base_url:
        return None

    # OpenHands default config
    config = {
        'model': 'litellm_proxy/gemini/gemini-2.5-pro',
        'api_key': api_key,
        'base_url': base_url,
        'api_version': None,
        'custom_llm_provider': None,
        'timeout': None,
        'drop_params': True,
        'seed': None,
        'temperature': 0.0,
        'top_p': 1.0,
        'top_k': None,
        'max_output_tokens': None,
        **additional_params,  # Apply additional parameters
    }

    completion_func = partial(
        litellm.completion,
        model=config['model'],
        api_key=config['api_key'],
        base_url=config['base_url'],
        api_version=config['api_version'],
        custom_llm_provider=config['custom_llm_provider'],
        timeout=config['timeout'],
        drop_params=config['drop_params'],
        seed=config['seed'],
    )

    return completion_func


def test_litellm_configurations():
    """Test various LiteLLM configurations with tool calls."""
    print('🚀 Testing LiteLLM Configurations with Tool Calls')
    print('=' * 70)

    # Check credentials
    success, credentials = check_credentials()
    if not success:
        return []

    if not credentials['litellm_api_key'] or not credentials['litellm_base_url']:
        print('❌ LiteLLM credentials not available')
        return []

    all_results = []

    # Test configurations
    test_configs = [
        {
            'name': 'Basic LiteLLM',
            'func': create_litellm_completion_func(temperature=0.0),
        },
        {
            'name': 'LiteLLM with Streaming',
            'func': create_litellm_completion_func(temperature=0.0, stream=True),
        },
        {
            'name': 'OpenHands Style (No Stream)',
            'func': create_openhands_completion_func(),
        },
        {
            'name': 'OpenHands Style (Streaming)',
            'func': create_openhands_completion_func(stream=True),
        },
        {
            'name': 'Reasoning Effort: Low',
            'func': create_litellm_completion_func(reasoning_effort='low'),
        },
        {
            'name': 'Reasoning Effort: Medium',
            'func': create_litellm_completion_func(reasoning_effort='medium'),
        },
        {
            'name': 'Reasoning Effort: High',
            'func': create_litellm_completion_func(reasoning_effort='high'),
        },
        {
            'name': 'Thinking Budget: 128',
            'func': create_litellm_completion_func(thinking={'budget_tokens': 128}),
        },
        {
            'name': 'Thinking Budget: 1024',
            'func': create_litellm_completion_func(thinking={'budget_tokens': 1024}),
        },
    ]

    # Run tests
    for config in test_configs:
        if config['func'] is None:
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


def analyze_litellm_results(results):
    """Analyze and compare LiteLLM test results."""
    print('\n📊 LITELLM PERFORMANCE ANALYSIS')
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

    # Group by configuration type
    [
        r
        for r in successful_results
        if 'Basic' in r['config_name'] or 'OpenHands Style' in r['config_name']
    ]
    reasoning_results = [
        r for r in successful_results if 'Reasoning Effort' in r['config_name']
    ]
    thinking_results = [
        r for r in successful_results if 'Thinking Budget' in r['config_name']
    ]

    # Analyze streaming vs non-streaming
    streaming_results = [
        r for r in successful_results if 'Streaming' in r['config_name']
    ]
    non_streaming_results = [
        r for r in successful_results if 'Streaming' not in r['config_name']
    ]

    if streaming_results and non_streaming_results:
        avg_streaming = sum(r['total_duration'] for r in streaming_results) / len(
            streaming_results
        )
        avg_non_streaming = sum(
            r['total_duration'] for r in non_streaming_results
        ) / len(non_streaming_results)

        print('\n🌊 Streaming vs Non-Streaming:')
        print(f'   Average Streaming: {avg_streaming:.3f}s')
        print(f'   Average Non-Streaming: {avg_non_streaming:.3f}s')

        if avg_non_streaming > 0:
            advantage = (
                avg_non_streaming / avg_streaming
                if avg_streaming < avg_non_streaming
                else avg_streaming / avg_non_streaming
            )
            faster = (
                'Streaming' if avg_streaming < avg_non_streaming else 'Non-Streaming'
            )
            print(f'   {faster} is {advantage:.2f}x faster')

    # Analyze reasoning effort impact
    if len(reasoning_results) > 1:
        print('\n🧠 Reasoning Effort Impact:')
        for result in sorted(reasoning_results, key=lambda x: x['total_duration']):
            effort = 'Unknown'
            if 'Low' in result['config_name']:
                effort = 'Low'
            elif 'Medium' in result['config_name']:
                effort = 'Medium'
            elif 'High' in result['config_name']:
                effort = 'High'
            print(f'   {effort}: {result["total_duration"]:.3f}s')

    # Analyze thinking budget impact
    if len(thinking_results) > 1:
        print('\n💭 Thinking Budget Impact:')
        for result in sorted(thinking_results, key=lambda x: x['total_duration']):
            budget = 'Unknown'
            if '128' in result['config_name']:
                budget = '128'
            elif '1024' in result['config_name']:
                budget = '1024'
            print(f'   Budget {budget}: {result["total_duration"]:.3f}s')

    # Tool call accuracy
    correct_results = sum(
        1 for r in successful_results if r.get('result_correct', False)
    )
    accuracy = correct_results / len(successful_results) * 100
    print(
        f'\n🎯 Tool Call Accuracy: {accuracy:.1f}% ({correct_results}/{len(successful_results)})'
    )


def main():
    """Run comprehensive LiteLLM performance tests with tool calls."""
    print('🚀 COMPREHENSIVE LITELLM PERFORMANCE TEST WITH TOOL CALLS')
    print('=' * 70)
    print('This test evaluates LiteLLM performance using realistic tool call workflows')
    print('Uses secure credentials: LITELLM_PROXY_API_KEY and LITELLM_BASE_URL')
    print()

    results = test_litellm_configurations()

    if results:
        analyze_litellm_results(results)
    else:
        print('❌ No test results to analyze')


if __name__ == '__main__':
    main()
