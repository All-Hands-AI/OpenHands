#!/usr/bin/env python3
"""
Test script that mimics exactly how OpenHands calls LiteLLM.

This will help us identify if OpenHands-specific configurations cause the slowdown.
"""

import os
import time
from functools import partial

from litellm import completion as litellm_completion


def create_openhands_completion_function():
    """Create a completion function exactly like OpenHands does."""

    # OpenHands default config (from llm_config.py)
    config = {
        'model': 'gemini-2.5-pro',
        'api_key': os.getenv('GOOGLE_API_KEY'),
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

    # Additional kwargs that OpenHands adds for Gemini
    kwargs = {}

    # Safety settings (if any)
    if 'gemini' in config['model'].lower():
        # OpenHands adds safety_settings if configured
        pass

    # Create the partial function exactly like OpenHands
    completion_func = partial(
        litellm_completion,
        model=config['model'],
        api_key=config['api_key'],
        base_url=config['base_url'],
        api_version=config['api_version'],
        custom_llm_provider=config['custom_llm_provider'],
        timeout=config['timeout'],
        drop_params=config['drop_params'],
        seed=config['seed'],
        **kwargs,
    )

    return completion_func, config


def test_openhands_style_call(stream: bool = False, reasoning_effort: str = None):
    """Test LiteLLM call exactly like OpenHands would make it."""

    completion_func, config = create_openhands_completion_function()

    # Test message
    messages = [
        {
            'role': 'user',
            'content': 'Write a simple Python function that calculates the factorial of a number. Include error handling for negative numbers.',
        }
    ]

    # Additional parameters that might be passed at call time
    call_params = {
        'messages': messages,
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

    print(
        f'\n🔧 OpenHands-style call (stream={stream}, reasoning_effort={reasoning_effort})'
    )
    print(f'Config: {config}')
    print(f'Call params: {call_params}')

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

            print('✅ Streaming Success!')
            print(f'   Total Duration: {total_duration:.3f}s')
            print(f'   Time to First Chunk: {time_to_first_chunk:.3f}s')
            print(f'   Chunks: {chunk_count}')
            print(f'   Response Length: {len(full_response)} chars')

            return {
                'success': True,
                'total_duration': total_duration,
                'time_to_first_chunk': time_to_first_chunk,
                'streaming': True,
                'response_length': len(full_response),
            }
        else:
            # Handle non-streaming response
            end_time = time.time()
            duration = end_time - start_time

            content = response.choices[0].message.content if response.choices else ''

            print('✅ Non-streaming Success!')
            print(f'   Duration: {duration:.3f}s')
            print(f'   Response Length: {len(content)} chars')

            return {
                'success': True,
                'total_duration': duration,
                'time_to_first_chunk': duration,
                'streaming': False,
                'response_length': len(content),
            }

    except Exception as e:
        end_time = time.time()
        duration = end_time - start_time

        print(f'❌ Failed: {str(e)}')
        print(f'   Duration: {duration:.3f}s')

        return {'success': False, 'error': str(e), 'duration': duration}


def main():
    """Test OpenHands-style LiteLLM calls."""
    print('🔍 OpenHands LiteLLM Performance Test')
    print('=' * 50)

    if not os.getenv('GOOGLE_API_KEY'):
        print('❌ Error: GOOGLE_API_KEY environment variable not set')
        return

    # Test different configurations
    test_cases = [
        {'stream': False, 'reasoning_effort': None},
        {'stream': True, 'reasoning_effort': None},
        {'stream': False, 'reasoning_effort': 'high'},
        {'stream': True, 'reasoning_effort': 'high'},
    ]

    results = []

    for case in test_cases:
        result = test_openhands_style_call(**case)
        result.update(case)
        results.append(result)

    # Summary
    print('\n📊 OPENHANDS PERFORMANCE SUMMARY')
    print('=' * 50)

    successful_results = [r for r in results if r['success']]
    if successful_results:
        for result in successful_results:
            stream_str = 'Streaming' if result['streaming'] else 'Non-streaming'
            reasoning_str = f' (reasoning: {result.get("reasoning_effort", "none")})'
            print(f'{stream_str}{reasoning_str}: {result["total_duration"]:.3f}s')

        fastest = min(successful_results, key=lambda x: x['total_duration'])
        slowest = max(successful_results, key=lambda x: x['total_duration'])

        print(f'\n🏆 Fastest Configuration: {fastest["total_duration"]:.3f}s')
        print(f'🐌 Slowest Configuration: {slowest["total_duration"]:.3f}s')

        if fastest['total_duration'] > 0:
            speedup = slowest['total_duration'] / fastest['total_duration']
            print(f'📈 Speed Difference: {speedup:.2f}x')


if __name__ == '__main__':
    main()
