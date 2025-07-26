#!/usr/bin/env python3
"""
Test script using native Google Generative AI library with tool calls.

This provides a baseline for comparing native performance vs LiteLLM performance
using realistic tool call workflows.
"""

import os

try:
    import google.generativeai as genai

    NATIVE_AVAILABLE = True
except ImportError:
    NATIVE_AVAILABLE = False
    print(
        '⚠️  google-generativeai not installed. Install with: pip install google-generativeai'
    )

# Import shared utilities
from test_utils import (
    MATH_TOOL,
    check_credentials,
    run_tool_call_test,
)


def create_native_gemini_completion_func(stream: bool = False):
    """Create completion function using native Google Generative AI library."""
    if not NATIVE_AVAILABLE:
        return None

    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        return None

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-pro', tools=[MATH_TOOL])

    def completion_func(messages, tools=None, **kwargs):
        # Convert messages to native API format
        if messages and messages[-1]['role'] == 'user':
            prompt = messages[-1]['content']
            return model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0,
                    max_output_tokens=8192,
                ),
                stream=stream,
            )
        return None

    return completion_func


def test_native_gemini_configurations():
    """Test various native Gemini configurations with tool calls."""
    print('🚀 Testing Native Gemini Configurations with Tool Calls')
    print('=' * 70)

    # Check credentials
    success, credentials = check_credentials()
    if not success:
        return []

    if not NATIVE_AVAILABLE:
        print('❌ google-generativeai not installed')
        return []

    if not credentials['gemini_api_key']:
        print('❌ GEMINI_API_KEY not available')
        return []

    all_results = []

    # Test configurations
    test_configs = [
        {
            'name': 'Native Gemini (Non-Streaming)',
            'func': create_native_gemini_completion_func(stream=False),
        },
        {
            'name': 'Native Gemini (Streaming)',
            'func': create_native_gemini_completion_func(stream=True),
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


def analyze_native_gemini_results(results):
    """Analyze and compare native Gemini test results."""
    print('\n📊 NATIVE GEMINI PERFORMANCE ANALYSIS')
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

    # Analyze streaming vs non-streaming
    streaming_results = [
        r
        for r in successful_results
        if 'Streaming' in r['config_name'] and 'Non-Streaming' not in r['config_name']
    ]
    non_streaming_results = [
        r for r in successful_results if 'Non-Streaming' in r['config_name']
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

    # Tool call accuracy
    correct_results = sum(
        1 for r in successful_results if r.get('result_correct', False)
    )
    accuracy = correct_results / len(successful_results) * 100
    print(
        f'\n🎯 Tool Call Accuracy: {accuracy:.1f}% ({correct_results}/{len(successful_results)})'
    )


def main():
    """Run native Gemini performance tests with tool calls."""
    print('🚀 NATIVE GEMINI PERFORMANCE TEST WITH TOOL CALLS')
    print('=' * 70)
    print(
        'This test provides a baseline using native Google API with tool call workflows'
    )
    print()

    if not NATIVE_AVAILABLE:
        print('❌ Cannot run native tests - google-generativeai not installed')
        print('Install with: pip install google-generativeai')
        return

    results = test_native_gemini_configurations()

    if results:
        analyze_native_gemini_results(results)
    else:
        print('❌ No test results to analyze')


if __name__ == '__main__':
    main()
