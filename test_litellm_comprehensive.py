#!/usr/bin/env python3
"""
Comprehensive LiteLLM performance test for Gemini.

This script tests LiteLLM performance with various configurations including:
1. Different parameter combinations (streaming, temperature, etc.)
2. OpenHands-style configuration and calls
3. Reasoning effort and thinking budget parameters

Consolidates functionality from test_litellm_performance.py and test_openhands_litellm.py
"""

import os
import time
from functools import partial
from typing import Any

import litellm

# Test configurations to compare
BASIC_CONFIGS = [
    {
        'name': 'Minimal Config',
        'params': {
            'model': 'gemini-2.5-pro',
            'temperature': 0,
        },
    },
    {
        'name': 'Streaming Config',
        'params': {
            'model': 'gemini-2.5-pro',
            'temperature': 0,
            'stream': True,
            'max_tokens': 8192,
        },
    },
    {
        'name': 'OpenHands Default (No Stream)',
        'params': {
            'model': 'gemini-2.5-pro',
            'temperature': 0.0,
            'stream': False,
            'max_tokens': None,
            'drop_params': True,
        },
    },
    {
        'name': 'OpenHands with Streaming',
        'params': {
            'model': 'gemini-2.5-pro',
            'temperature': 0.0,
            'stream': True,
            'max_tokens': None,
            'drop_params': True,
        },
    },
]

# Reasoning/thinking configurations
REASONING_CONFIGS = [
    {
        'name': 'Reasoning Effort: Low',
        'params': {
            'model': 'gemini-2.5-pro',
            'temperature': 0.0,
            'reasoning_effort': 'low',
        },
    },
    {
        'name': 'Reasoning Effort: Medium',
        'params': {
            'model': 'gemini-2.5-pro',
            'temperature': 0.0,
            'reasoning_effort': 'medium',
        },
    },
    {
        'name': 'Reasoning Effort: High',
        'params': {
            'model': 'gemini-2.5-pro',
            'temperature': 0.0,
            'reasoning_effort': 'high',
        },
    },
    {
        'name': 'Thinking Budget: 128 tokens',
        'params': {
            'model': 'gemini-2.5-pro',
            'temperature': 0.0,
            'thinking': {'budget_tokens': 128},
        },
    },
    {
        'name': 'Thinking Budget: 1024 tokens',
        'params': {
            'model': 'gemini-2.5-pro',
            'temperature': 0.0,
            'thinking': {'budget_tokens': 1024},
        },
    },
]

TEST_PROMPT = [
    {
        'role': 'user',
        'content': 'Write a simple Python function that calculates the factorial of a number. Include error handling for negative numbers.',
    }
]


def create_openhands_completion_function():
    """Create a completion function exactly like OpenHands does."""
    config = {
        'model': 'gemini-2.5-pro',
        'api_key': os.getenv('GEMINI_API_KEY'),
        'base_url': None,
        'api_version': None,
        'custom_llm_provider': None,
        'timeout': None,
        'drop_params': True,
        'seed': None,
        'temperature': 0.0,
        'top_p': 1.0,
        'top_k': None,
        'max_output_tokens': None,
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

    return completion_func, config


def test_litellm_config(config: dict[str, Any]) -> dict[str, Any]:
    """Test a specific LiteLLM configuration and measure performance."""
    print(f'\n🧪 Testing: {config["name"]}')
    print(f'Parameters: {config["params"]}')

    start_time = time.time()

    try:
        # Make the API call
        response = litellm.completion(messages=TEST_PROMPT, **config['params'])

        end_time = time.time()
        duration = end_time - start_time

        # Handle streaming vs non-streaming response
        if config['params'].get('stream', False):
            # For streaming, we need to consume the generator
            full_response = ''
            chunk_count = 0
            first_chunk_time = None

            for chunk in response:
                if first_chunk_time is None:
                    first_chunk_time = time.time()

                if hasattr(chunk, 'choices') and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if hasattr(delta, 'content') and delta.content:
                        full_response += delta.content
                        chunk_count += 1

            final_time = time.time()
            total_duration = final_time - start_time
            time_to_first_chunk = (
                first_chunk_time - start_time if first_chunk_time else None
            )

            return {
                'success': True,
                'total_duration': total_duration,
                'time_to_first_chunk': time_to_first_chunk,
                'chunk_count': chunk_count,
                'response_length': len(full_response),
                'streaming': True,
            }
        else:
            # Non-streaming response
            content = response.choices[0].message.content if response.choices else ''

            return {
                'success': True,
                'total_duration': duration,
                'time_to_first_chunk': duration,  # Same as total for non-streaming
                'chunk_count': 1,
                'response_length': len(content),
                'streaming': False,
            }

    except Exception as e:
        end_time = time.time()
        duration = end_time - start_time

        return {'success': False, 'error': str(e), 'duration': duration}


def test_openhands_style_call(
    stream: bool = False, reasoning_effort: str = None, thinking: dict = None
):
    """Test LiteLLM call exactly like OpenHands would make it."""
    completion_func, config = create_openhands_completion_function()

    # Additional parameters that might be passed at call time
    call_params = {
        'messages': TEST_PROMPT,
        'temperature': config['temperature'],
        'top_p': config['top_p'],
        'stream': stream,
    }

    if config['top_k'] is not None:
        call_params['top_k'] = config['top_k']

    if config['max_output_tokens'] is not None:
        call_params['max_tokens'] = config['max_output_tokens']

    if reasoning_effort:
        call_params['reasoning_effort'] = reasoning_effort

    if thinking:
        call_params['thinking'] = thinking

    config_desc = f'stream={stream}'
    if reasoning_effort:
        config_desc += f', reasoning_effort={reasoning_effort}'
    if thinking:
        config_desc += f', thinking={thinking}'

    print(f'\n🔧 OpenHands-style call ({config_desc})')

    start_time = time.time()

    try:
        response = completion_func(**call_params)

        if stream:
            # Handle streaming response
            full_response = ''
            chunk_count = 0
            first_chunk_time = None

            for chunk in response:
                if first_chunk_time is None:
                    first_chunk_time = time.time()

                if hasattr(chunk, 'choices') and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if hasattr(delta, 'content') and delta.content:
                        full_response += delta.content
                        chunk_count += 1

            end_time = time.time()
            total_duration = end_time - start_time
            time_to_first_chunk = (
                first_chunk_time - start_time if first_chunk_time else None
            )

            return {
                'success': True,
                'total_duration': total_duration,
                'time_to_first_chunk': time_to_first_chunk,
                'streaming': True,
                'response_length': len(full_response),
                'config_desc': config_desc,
            }
        else:
            # Handle non-streaming response
            end_time = time.time()
            duration = end_time - start_time

            content = response.choices[0].message.content if response.choices else ''

            return {
                'success': True,
                'total_duration': duration,
                'time_to_first_chunk': duration,
                'streaming': False,
                'response_length': len(content),
                'config_desc': config_desc,
            }

    except Exception as e:
        end_time = time.time()
        duration = end_time - start_time

        return {
            'success': False,
            'error': str(e),
            'duration': duration,
            'config_desc': config_desc,
        }


def run_basic_tests():
    """Run basic LiteLLM configuration tests."""
    print('🚀 Basic LiteLLM Configuration Tests')
    print('=' * 50)

    results = []

    for config in BASIC_CONFIGS:
        result = test_litellm_config(config)
        result['config_name'] = config['name']
        results.append(result)

        if result['success']:
            print('✅ Success!')
            print(f'   Total Duration: {result["total_duration"]:.3f}s')
            if result.get('time_to_first_chunk'):
                print(f'   Time to First Chunk: {result["time_to_first_chunk"]:.3f}s')
            print(f'   Response Length: {result["response_length"]} chars')
            if result['streaming']:
                print(f'   Chunks Received: {result["chunk_count"]}')
        else:
            print(f'❌ Failed: {result["error"]}')
            print(f'   Duration: {result["duration"]:.3f}s')

    return results


def run_reasoning_tests():
    """Run reasoning/thinking configuration tests."""
    print('\n🧠 Reasoning & Thinking Configuration Tests')
    print('=' * 50)

    results = []

    for config in REASONING_CONFIGS:
        result = test_litellm_config(config)
        result['config_name'] = config['name']
        results.append(result)

        if result['success']:
            print('✅ Success!')
            print(f'   Total Duration: {result["total_duration"]:.3f}s')
            print(f'   Response Length: {result["response_length"]} chars')
        else:
            print(f'❌ Failed: {result["error"]}')
            print(f'   Duration: {result["duration"]:.3f}s')

    return results


def run_openhands_tests():
    """Run OpenHands-style tests."""
    print('\n🔧 OpenHands-Style Configuration Tests')
    print('=' * 50)

    test_cases = [
        {'stream': False, 'reasoning_effort': None, 'thinking': None},
        {'stream': True, 'reasoning_effort': None, 'thinking': None},
        {'stream': False, 'reasoning_effort': 'high', 'thinking': None},
        {'stream': False, 'reasoning_effort': None, 'thinking': {'budget_tokens': 128}},
    ]

    results = []

    for case in test_cases:
        result = test_openhands_style_call(**case)
        results.append(result)

        if result['success']:
            print('✅ Success!')
            print(f'   Total Duration: {result["total_duration"]:.3f}s')
            print(f'   Response Length: {result["response_length"]} chars')
        else:
            print(f'❌ Failed: {result["error"]}')

    return results


def print_summary(all_results):
    """Print comprehensive performance summary."""
    print('\n📊 COMPREHENSIVE PERFORMANCE SUMMARY')
    print('=' * 60)

    successful_results = [r for r in all_results if r['success']]
    if not successful_results:
        print('❌ No successful tests to summarize')
        return

    # Find fastest and slowest
    fastest = min(successful_results, key=lambda x: x['total_duration'])
    slowest = max(successful_results, key=lambda x: x['total_duration'])

    print(
        f'🏆 Fastest: {fastest.get("config_name", fastest.get("config_desc", "Unknown"))} ({fastest["total_duration"]:.3f}s)'
    )
    print(
        f'🐌 Slowest: {slowest.get("config_name", slowest.get("config_desc", "Unknown"))} ({slowest["total_duration"]:.3f}s)'
    )

    if fastest['total_duration'] > 0:
        speedup = slowest['total_duration'] / fastest['total_duration']
        print(f'📈 Speed Difference: {speedup:.2f}x')

    # Analyze streaming vs non-streaming
    streaming_results = [r for r in successful_results if r.get('streaming', False)]
    non_streaming_results = [
        r for r in successful_results if not r.get('streaming', False)
    ]

    if streaming_results and non_streaming_results:
        avg_streaming = sum(r['total_duration'] for r in streaming_results) / len(
            streaming_results
        )
        avg_non_streaming = sum(
            r['total_duration'] for r in non_streaming_results
        ) / len(non_streaming_results)

        print('\n🌊 Streaming vs Non-Streaming Analysis:')
        print(f'   Average Streaming: {avg_streaming:.3f}s')
        print(f'   Average Non-Streaming: {avg_non_streaming:.3f}s')

        if avg_non_streaming > 0:
            streaming_advantage = avg_non_streaming / avg_streaming
            print(f'   Streaming Advantage: {streaming_advantage:.2f}x')

    # Show top 5 fastest configurations
    print('\n🏃 Top 5 Fastest Configurations:')
    sorted_results = sorted(successful_results, key=lambda x: x['total_duration'])
    for i, result in enumerate(sorted_results[:5], 1):
        name = result.get('config_name', result.get('config_desc', 'Unknown'))
        print(f'   {i}. {name}: {result["total_duration"]:.3f}s')


def main():
    """Run comprehensive LiteLLM performance tests."""
    # Check for API key
    if not os.getenv('GEMINI_API_KEY'):
        print('❌ Error: GEMINI_API_KEY environment variable not set')
        print('Please set your Google API key: export GEMINI_API_KEY=your_key_here')
        return

    all_results = []

    # Run all test suites
    all_results.extend(run_basic_tests())
    all_results.extend(run_reasoning_tests())
    all_results.extend(run_openhands_tests())

    # Print comprehensive summary
    print_summary(all_results)


if __name__ == '__main__':
    main()
