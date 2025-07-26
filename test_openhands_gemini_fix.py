#!/usr/bin/env python3
"""
Test OpenHands Gemini performance fix.

This script tests the optimized Gemini configuration in OpenHands
that uses thinking={"budget_tokens": 128} instead of reasoning_effort.

Based on performance investigation showing:
- reasoning_effort='high' → ~25s (slow)
- reasoning_effort='medium' → ~27s (slowest)
- thinking={"budget_tokens": 128} → ~11s (fast, 2.4x speedup)
"""

import os
import time

from openhands.core.config import LLMConfig
from openhands.llm.llm import LLM


def test_openhands_gemini_performance():
    """Test OpenHands with optimized Gemini configuration."""

    # Ensure we have the API key
    if not os.getenv('GEMINI_API_KEY'):
        print('❌ GEMINI_API_KEY environment variable not set')
        return

    print('🧪 Testing OpenHands Gemini Performance Fix')
    print('=' * 50)

    # Create LLM config for Gemini 2.5 Pro
    config = LLMConfig(
        model='gemini-2.5-pro',
        api_key=os.getenv('GEMINI_API_KEY'),
        max_output_tokens=1000,
        temperature=0.7,
        reasoning_effort='high',  # This should be overridden by our fix
    )

    # Create LLM instance
    llm = LLM(config)

    # Test message
    messages = [
        {
            'role': 'user',
            'content': 'Explain the concept of recursion in programming with a simple example. Be concise but thorough.',
        }
    ]

    print(f'📝 Model: {config.model}')
    print(f'🔧 Config reasoning_effort: {config.reasoning_effort}')
    print('⏱️  Starting request...')

    start_time = time.time()

    try:
        # Make the request
        response = llm.completion(messages=messages)

        end_time = time.time()
        duration = end_time - start_time

        print(f'✅ Request completed in {duration:.3f}s')
        print('📊 Expected: ~11s (with thinking budget fix)')
        print('📊 Previous: ~25s (with reasoning_effort)')

        if duration < 15:
            print('🎉 SUCCESS: Performance improvement achieved!')
            print(
                '🔧 Fix is working - using thinking budget instead of reasoning_effort'
            )
        elif duration < 20:
            print('⚠️  PARTIAL: Some improvement, but not optimal')
        else:
            print('❌ SLOW: Fix may not be working properly')

        # Show response preview
        if hasattr(response, 'choices') and response.choices:
            content = response.choices[0].message.content
            preview = content[:200] + '...' if len(content) > 200 else content
            print(f'\n📄 Response preview:\n{preview}')

        return duration

    except Exception as e:
        end_time = time.time()
        duration = end_time - start_time
        print(f'❌ Error after {duration:.3f}s: {e}')
        return None


def test_configuration_inspection():
    """Inspect the actual configuration being used."""
    print('\n🔍 Configuration Inspection')
    print('=' * 30)

    config = LLMConfig(
        model='gemini-2.5-pro',
        api_key='dummy',  # Just for config inspection
        reasoning_effort='high',
    )

    LLM(config)

    # Check if gemini is in reasoning effort supported models
    from openhands.llm.llm import REASONING_EFFORT_SUPPORTED_MODELS

    is_supported = (
        config.model.lower() in REASONING_EFFORT_SUPPORTED_MODELS
        or config.model.split('/')[-1] in REASONING_EFFORT_SUPPORTED_MODELS
    )

    print(f'📋 Model: {config.model}')
    print(f'🎯 In REASONING_EFFORT_SUPPORTED_MODELS: {is_supported}')
    print(f'🔧 Config reasoning_effort: {config.reasoning_effort}')
    print(f'🧠 Should use thinking budget: {"gemini" in config.model.lower()}')

    if is_supported and 'gemini' in config.model.lower():
        print("✅ Fix should apply: thinking={'budget_tokens': 128}")
    else:
        print('❌ Fix may not apply - check model name matching')


if __name__ == '__main__':
    # Run configuration inspection first
    test_configuration_inspection()

    # Run performance test
    duration = test_openhands_gemini_performance()

    if duration:
        print(f'\n🎯 Final Result: {duration:.3f}s')
        if duration < 15:
            print('🏆 EXCELLENT: Significant performance improvement!')
        elif duration < 20:
            print('👍 GOOD: Noticeable improvement')
        else:
            print('🐌 NEEDS WORK: Still slow, investigate further')
