#!/usr/bin/env python3
"""Quick test with RooCode's exact model"""

import os
import time

import google.generativeai as genai


def test_roocode_model():
    """Test with RooCode's default model: gemini-2.0-flash-001"""
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print('❌ GEMINI_API_KEY not set')
        return

    genai.configure(api_key=api_key)

    # Use the model we want to test
    model = genai.GenerativeModel('gemini-2.5-pro')

    # Simple prompt
    prompt = 'Hello! Please respond with a short greeting.'

    print(f'🧪 Testing {model.model_name} with simple prompt...')

    start_time = time.time()
    try:
        response = model.generate_content(prompt)
        duration = time.time() - start_time

        print(f'✅ Success! Duration: {duration:.3f}s')
        print(f'📝 Response: {response.text[:100]}...')

    except Exception as e:
        print(f'❌ Error: {e}')


if __name__ == '__main__':
    test_roocode_model()
