#!/usr/bin/env python3
"""Test the impact of thinking budget on Gemini 2.5 Pro performance"""

import os
import time

import google.generativeai as genai


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

    # Test 2: With thinking budget via request_options (try different approach)
    print('\n🔍 Test 2: With thinking budget via request_options')
    model2 = genai.GenerativeModel('gemini-2.5-pro')
    start_time = time.time()
    try:
        response2 = model2.generate_content(
            prompt,
            request_options={
                'thinkingConfig': {'thinkingBudget': 4096, 'includeThoughts': True}
            },
        )
        duration2 = time.time() - start_time
        print(f'✅ Duration: {duration2:.3f}s')
        print(f'📝 Response length: {len(response2.text)} chars')
    except Exception as e:
        print(f'❌ Error: {e}')
        duration2 = None

    # Test 3: Try with reasoning_effort parameter (LiteLLM style)
    print("\n🔍 Test 3: Try with reasoning_effort = 'low'")
    model3 = genai.GenerativeModel('gemini-2.5-pro')
    start_time = time.time()
    try:
        response3 = model3.generate_content(
            prompt, generation_config={'reasoning_effort': 'low'}
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

    # Summary
    print('\n📊 SUMMARY')
    print('=' * 60)
    if duration1:
        print(f'No thinking config:     {duration1:.3f}s')
    if duration2:
        print(f'Request options test:   {duration2:.3f}s')
    if duration3:
        print(f'Reasoning effort test:  {duration3:.3f}s')
    if duration4:
        print(f'Thinking disabled:      {duration4:.3f}s')
    if duration5:
        print(f'Small thinking budget:  {duration5:.3f}s')

    # Find the fastest approach
    durations = [
        d
        for d in [duration1, duration2, duration3, duration4, duration5]
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
