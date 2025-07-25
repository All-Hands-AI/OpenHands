#!/usr/bin/env python3
"""
Test script to isolate LiteLLM performance issues with Gemini.

This script will help us determine if the performance issue is:
1. LiteLLM itself being slow with Gemini
2. How OpenHands configures/calls LiteLLM
3. Specific hyperparameters or configuration issues

Usage:
    python test_litellm_performance.py
"""

import os
import time
from typing import Any

import litellm

# Test configurations to compare
TEST_CONFIGS = [
    {
        'name': 'RooCode-like (Streaming, Temp=0)',
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
    {
        'name': 'Minimal Config',
        'params': {
            'model': 'gemini-2.5-pro',
            'temperature': 0,
        },
    },
]

TEST_PROMPT = [
    {
        'role': 'user',
        'content': 'Write a simple Python function that calculates the factorial of a number. Include error handling for negative numbers.',
    }
]


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


def main():
    """Run performance tests on different LiteLLM configurations."""
    print('🚀 LiteLLM Gemini Performance Test')
    print('=' * 50)

    # Check for API key
    if not os.getenv('GEMINI_API_KEY'):
        print('❌ Error: GEMINI_API_KEY environment variable not set')
        print('Please set your Google API key: export GEMINI_API_KEY=your_key_here')
        return

    results = []

    for config in TEST_CONFIGS:
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

    # Summary
    print('\n📊 PERFORMANCE SUMMARY')
    print('=' * 50)

    successful_results = [r for r in results if r['success']]
    if successful_results:
        fastest = min(successful_results, key=lambda x: x['total_duration'])
        slowest = max(successful_results, key=lambda x: x['total_duration'])

        print(
            f'🏆 Fastest: {fastest["config_name"]} ({fastest["total_duration"]:.3f}s)'
        )
        print(
            f'🐌 Slowest: {slowest["config_name"]} ({slowest["total_duration"]:.3f}s)'
        )

        if fastest['total_duration'] > 0:
            speedup = slowest['total_duration'] / fastest['total_duration']
            print(f'📈 Speed Difference: {speedup:.2f}x')

        # Check if streaming makes a difference
        streaming_results = [r for r in successful_results if r['streaming']]
        non_streaming_results = [r for r in successful_results if not r['streaming']]

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
                streaming_advantage = avg_non_streaming / avg_streaming
                print(f'   Streaming Advantage: {streaming_advantage:.2f}x')


if __name__ == '__main__':
    main()
