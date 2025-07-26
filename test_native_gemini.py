#!/usr/bin/env python3
"""
Test script using native Google Generative AI library (like RooCode does).

This will help us compare native performance vs LiteLLM performance.
"""

import os
import time

try:
    import google.generativeai as genai

    NATIVE_AVAILABLE = True
except ImportError:
    NATIVE_AVAILABLE = False
    print(
        '⚠️  google-generativeai not installed. Install with: pip install google-generativeai'
    )


def test_native_gemini():
    """Test native Google Generative AI library."""
    if not NATIVE_AVAILABLE:
        return {'success': False, 'error': 'google-generativeai not installed'}

    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        return {'success': False, 'error': 'GEMINI_API_KEY not set'}

    print('\n🚀 Testing Native Google Generative AI')
    print('=' * 40)

    # Configure the API
    genai.configure(api_key=api_key)

    # Create model (similar to RooCode)
    model = genai.GenerativeModel('gemini-2.5-pro')

    prompt = 'Write a simple Python function that calculates the factorial of a number. Include error handling for negative numbers.'

    # Test streaming (like RooCode does)
    print('🌊 Testing Native Streaming...')
    start_time = time.time()

    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0,
                max_output_tokens=8192,
            ),
            stream=True,
        )

        full_response = ''
        chunk_count = 0
        first_chunk_time = None

        for chunk in response:
            if first_chunk_time is None:
                first_chunk_time = time.time()

            if chunk.text:
                full_response += chunk.text
                chunk_count += 1

        end_time = time.time()
        total_duration = end_time - start_time
        time_to_first_chunk = (
            first_chunk_time - start_time if first_chunk_time else None
        )

        print('✅ Native Streaming Success!')
        print(f'   Total Duration: {total_duration:.3f}s')
        print(f'   Time to First Chunk: {time_to_first_chunk:.3f}s')
        print(f'   Chunks: {chunk_count}')
        print(f'   Response Length: {len(full_response)} chars')

        streaming_result = {
            'success': True,
            'total_duration': total_duration,
            'time_to_first_chunk': time_to_first_chunk,
            'streaming': True,
            'response_length': len(full_response),
            'chunk_count': chunk_count,
        }

    except Exception as e:
        end_time = time.time()
        duration = end_time - start_time
        print(f'❌ Native Streaming Failed: {str(e)}')
        streaming_result = {'success': False, 'error': str(e), 'duration': duration}

    # Test non-streaming
    print('\n📄 Testing Native Non-Streaming...')
    start_time = time.time()

    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0,
                max_output_tokens=8192,
            ),
            stream=False,
        )

        end_time = time.time()
        duration = end_time - start_time

        content = response.text if response.text else ''

        print('✅ Native Non-Streaming Success!')
        print(f'   Duration: {duration:.3f}s')
        print(f'   Response Length: {len(content)} chars')

        non_streaming_result = {
            'success': True,
            'total_duration': duration,
            'time_to_first_chunk': duration,
            'streaming': False,
            'response_length': len(content),
        }

    except Exception as e:
        end_time = time.time()
        duration = end_time - start_time
        print(f'❌ Native Non-Streaming Failed: {str(e)}')
        non_streaming_result = {'success': False, 'error': str(e), 'duration': duration}

    return {'streaming': streaming_result, 'non_streaming': non_streaming_result}


def main():
    """Test native Google Generative AI performance."""
    print('🧪 Native Google Generative AI Performance Test')
    print('=' * 50)

    if not NATIVE_AVAILABLE:
        print('❌ Cannot run native tests - google-generativeai not installed')
        print('Install with: pip install google-generativeai')
        return

    if not os.getenv('GEMINI_API_KEY'):
        print('❌ Error: GEMINI_API_KEY environment variable not set')
        return

    results = test_native_gemini()

    # Summary
    print('\n📊 NATIVE PERFORMANCE SUMMARY')
    print('=' * 50)

    streaming = results.get('streaming', {})
    non_streaming = results.get('non_streaming', {})

    if streaming.get('success') and non_streaming.get('success'):
        print(f'🌊 Native Streaming: {streaming["total_duration"]:.3f}s')
        print(f'📄 Native Non-Streaming: {non_streaming["total_duration"]:.3f}s')

        if streaming['total_duration'] > 0:
            advantage = non_streaming['total_duration'] / streaming['total_duration']
            print(f'📈 Streaming Advantage: {advantage:.2f}x')

    return results


if __name__ == '__main__':
    main()
