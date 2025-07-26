#!/usr/bin/env python3
"""Test the impact of thinking budget on Gemini 2.5 Pro performance"""

import os
import time

import google.generativeai as genai
from google import genai as new_genai
from google.genai import types

# Add LiteLLM import
try:
    import litellm

    LITELLM_AVAILABLE = True
except ImportError:
    LITELLM_AVAILABLE = False
    print('⚠️  LiteLLM not available - skipping LiteLLM tests')


def test_thinking_budget():
    """Test Gemini 2.5 Pro with and without thinking budget"""
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print('❌ GEMINI_API_KEY not set')
        return

    genai.configure(api_key=api_key)

    prompt = 'Write a simple Python function that calculates the factorial of a number. Include error handling for negative numbers.'

    print('🧪 Testing Gemini 2.5 Pro Thinking Budget Impact')
    print('=' * 60)

    # Test 1: No thinking config (default behavior)
    print('\n🔍 Test 1: No thinking config (default)')
    model1 = genai.GenerativeModel('gemini-2.5-pro')
    start_time = time.time()
    try:
        response1 = model1.generate_content(prompt)
        duration1 = time.time() - start_time
        print(f'✅ Duration: {duration1:.3f}s')
        print(f'📝 Response length: {len(response1.text)} chars')
    except Exception as e:
        print(f'❌ Error: {e}')
        duration1 = None

    # Test 2: With thinking budget using new google.genai API
    print('\n🔍 Test 2: With thinking budget using new google.genai API (4096)')
    start_time = time.time()
    try:
        client = new_genai.Client(api_key=api_key)
        config = types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(thinking_budget=4096)
        )
        response2 = client.models.generate_content(
            model='gemini-2.5-pro', contents=prompt, config=config
        )
        duration2 = time.time() - start_time
        print(f'✅ Duration: {duration2:.3f}s')
        print(f'📝 Response length: {len(response2.text)} chars')
    except Exception as e:
        print(f'❌ Error: {e}')
        duration2 = None

    # Test 3: Try with small thinking budget like Gemini CLI (128)
    print('\n🔍 Test 3: Try with small thinking budget like Gemini CLI (128)')
    start_time = time.time()
    try:
        client = new_genai.Client(api_key=api_key)
        config = types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(thinking_budget=128)
        )
        response3 = client.models.generate_content(
            model='gemini-2.5-pro', contents=prompt, config=config
        )
        duration3 = time.time() - start_time
        print(f'✅ Duration: {duration3:.3f}s')
        print(f'📝 Response length: {len(response3.text)} chars')
    except Exception as e:
        print(f'❌ Error: {e}')
        duration3 = None

    # Test 4: Try disabling thinking entirely
    print('\n🔍 Test 4: Try disabling thinking entirely')
    import requests

    start_time = time.time()
    try:
        url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro:generateContent?key={api_key}'
        payload = {
            'contents': [{'parts': [{'text': prompt}]}],
            'generationConfig': {'thinkingConfig': {'includeThoughts': False}},
        }
        response = requests.post(url, json=payload)
        duration4 = time.time() - start_time
        if response.status_code == 200:
            result = response.json()
            text = (
                result.get('candidates', [{}])[0]
                .get('content', {})
                .get('parts', [{}])[0]
                .get('text', '')
            )
            print(f'✅ Duration: {duration4:.3f}s')
            print(f'📝 Response length: {len(text)} chars')
        else:
            print(f'❌ HTTP Error: {response.status_code} - {response.text}')
            duration4 = None
    except Exception as e:
        print(f'❌ Error: {e}')
        duration4 = None

    # Test 5: Try with small thinking budget
    print('\n🔍 Test 5: Try with small thinking budget (1024)')
    start_time = time.time()
    try:
        url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro:generateContent?key={api_key}'
        payload = {
            'contents': [{'parts': [{'text': prompt}]}],
            'generationConfig': {
                'thinkingConfig': {'thinkingBudget': 1024, 'includeThoughts': True}
            },
        }
        response = requests.post(url, json=payload)
        duration5 = time.time() - start_time
        if response.status_code == 200:
            result = response.json()
            text = (
                result.get('candidates', [{}])[0]
                .get('content', {})
                .get('parts', [{}])[0]
                .get('text', '')
            )
            print(f'✅ Duration: {duration5:.3f}s')
            print(f'📝 Response length: {len(text)} chars')
        else:
            print(f'❌ HTTP Error: {response.status_code} - {response.text}')
            duration5 = None
    except Exception as e:
        print(f'❌ Error: {e}')
        duration5 = None

    # LiteLLM Tests
    duration6 = duration7 = duration8 = duration9 = None
    if LITELLM_AVAILABLE:
        # Test 6: LiteLLM with reasoning_effort="low"
        print('\n🔍 Test 6: LiteLLM with reasoning_effort="low"')
        start_time = time.time()
        try:
            response6 = litellm.completion(
                model='gemini/gemini-2.5-pro',
                messages=[{'role': 'user', 'content': prompt}],
                reasoning_effort='low',
                api_key=api_key,
            )
            duration6 = time.time() - start_time
            print(f'✅ Duration: {duration6:.3f}s')
            print(
                f'📝 Response length: {len(response6.choices[0].message.content)} chars'
            )
        except Exception as e:
            print(f'❌ Error: {e}')

        # Test 7: LiteLLM with reasoning_effort="medium"
        print('\n🔍 Test 7: LiteLLM with reasoning_effort="medium"')
        start_time = time.time()
        try:
            response7 = litellm.completion(
                model='gemini/gemini-2.5-pro',
                messages=[{'role': 'user', 'content': prompt}],
                reasoning_effort='medium',
                api_key=api_key,
            )
            duration7 = time.time() - start_time
            print(f'✅ Duration: {duration7:.3f}s')
            print(
                f'📝 Response length: {len(response7.choices[0].message.content)} chars'
            )
        except Exception as e:
            print(f'❌ Error: {e}')

        # Test 8: LiteLLM with thinking parameter (Anthropic-style)
        print('\n🔍 Test 8: LiteLLM with thinking parameter (128 tokens)')
        start_time = time.time()
        try:
            response8 = litellm.completion(
                model='gemini/gemini-2.5-pro',
                messages=[{'role': 'user', 'content': prompt}],
                thinking={'type': 'enabled', 'budget_tokens': 128},
                api_key=api_key,
            )
            duration8 = time.time() - start_time
            print(f'✅ Duration: {duration8:.3f}s')
            print(
                f'📝 Response length: {len(response8.choices[0].message.content)} chars'
            )
        except Exception as e:
            print(f'❌ Error: {e}')

        # Test 9: LiteLLM with debug logging enabled
        print('\n🔍 Test 9: LiteLLM with debug logging (reasoning_effort="low")')
        os.environ['LITELLM_LOG'] = 'DEBUG'
        litellm.set_verbose = True
        start_time = time.time()
        try:
            response9 = litellm.completion(
                model='gemini/gemini-2.5-pro',
                messages=[{'role': 'user', 'content': prompt}],
                reasoning_effort='low',
                api_key=api_key,
            )
            duration9 = time.time() - start_time
            print(f'✅ Duration: {duration9:.3f}s')
            print(
                f'📝 Response length: {len(response9.choices[0].message.content)} chars'
            )
        except Exception as e:
            print(f'❌ Error: {e}')
        finally:
            # Reset debug logging
            os.environ.pop('LITELLM_LOG', None)
            litellm.set_verbose = False

    # Summary
    print('\n📊 SUMMARY')
    print('=' * 60)
    if duration1:
        print(f'No thinking config:        {duration1:.3f}s')
    if duration2:
        print(f'New API large budget:      {duration2:.3f}s')
    if duration3:
        print(f'New API Gemini CLI (128):  {duration3:.3f}s')
    if duration4:
        print(f'Thinking disabled:         {duration4:.3f}s')
    if duration5:
        print(f'Medium thinking budget:    {duration5:.3f}s')

    # LiteLLM results
    if LITELLM_AVAILABLE:
        if duration6:
            print(f'LiteLLM reasoning_effort=low:   {duration6:.3f}s')
        if duration7:
            print(f'LiteLLM reasoning_effort=medium: {duration7:.3f}s')
        if duration8:
            print(f'LiteLLM thinking (128 tokens):  {duration8:.3f}s')
        if duration9:
            print(f'LiteLLM debug logging:     {duration9:.3f}s')

    # Find the fastest approach
    durations = [
        d
        for d in [
            duration1,
            duration2,
            duration3,
            duration4,
            duration5,
            duration6,
            duration7,
            duration8,
            duration9,
        ]
        if d is not None
    ]
    if durations:
        fastest = min(durations)
        slowest = max(durations)
        print(f'\n🏆 Fastest: {fastest:.3f}s')
        print(f'🐌 Slowest: {slowest:.3f}s')
        print(f'📈 Speed difference: {slowest / fastest:.2f}x')


if __name__ == '__main__':
    test_thinking_budget()
