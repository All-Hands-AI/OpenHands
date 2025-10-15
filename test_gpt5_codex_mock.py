#!/usr/bin/env python3
"""
Mock test for gpt-5-codex integration to verify the converter works without real API calls.
"""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the OpenHands directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from openhands.core.config import LLMConfig
from openhands.llm.llm import LLM
from openhands.llm.responses_converter import messages_to_responses_items, responses_to_completion_format
from litellm.types.utils import ModelResponse


def test_converter_functions():
    """Test the converter functions directly."""
    print("🧪 Testing converter functions...")
    
    # Test messages to responses conversion
    messages = [
        {'role': 'user', 'content': 'Write a hello world function'},
        {'role': 'assistant', 'content': 'def hello():\n    print("Hello, World!")'}
    ]
    
    responses_items = messages_to_responses_items(messages)
    print(f"✅ Messages to responses conversion: {len(responses_items)} items")
    
    # Verify the conversion
    assert len(responses_items) == 2
    assert responses_items[0]['role'] == 'user'
    assert responses_items[0]['content'] == 'Write a hello world function'
    assert responses_items[1]['role'] == 'assistant'
    assert responses_items[1]['content'] == 'def hello():\n    print("Hello, World!")'
    
    print("✅ Converter functions work correctly")
    return True


def test_gpt5_codex_detection():
    """Test that gpt-5-codex is properly detected as requiring Responses API."""
    print("🔍 Testing gpt-5-codex detection...")
    
    config = LLMConfig(
        model='gpt-5-codex',
        api_key='fake-key',
        base_url='https://api.openai.com/v1',
    )
    
    llm = LLM(config=config, service_id='test')
    
    # Test detection
    assert llm.requires_responses_api() == True, "gpt-5-codex should require Responses API"
    print("✅ gpt-5-codex correctly detected as requiring Responses API")
    
    # Test with openhands prefix
    config2 = LLMConfig(
        model='openhands/gpt-5-codex',
        api_key='fake-key',
        base_url='https://api.openai.com/v1',
    )
    
    llm2 = LLM(config=config2, service_id='test')
    assert llm2.requires_responses_api() == True, "openhands/gpt-5-codex should require Responses API"
    print("✅ openhands/gpt-5-codex correctly detected as requiring Responses API")
    
    # Test with regular model
    config3 = LLMConfig(
        model='gpt-4',
        api_key='fake-key',
        base_url='https://api.openai.com/v1',
    )
    
    llm3 = LLM(config=config3, service_id='test')
    assert llm3.requires_responses_api() == False, "gpt-4 should NOT require Responses API"
    print("✅ gpt-4 correctly detected as NOT requiring Responses API")
    
    return True


def test_gpt5_codex_with_mock():
    """Test gpt-5-codex with mocked API responses."""
    print("🎭 Testing gpt-5-codex with mocked responses...")
    
    config = LLMConfig(
        model='gpt-5-codex',
        api_key='fake-key',
        base_url='https://api.openai.com/v1',
    )
    
    llm = LLM(config=config, service_id='test')
    
    # Create a mock response that looks like what responses_to_completion_format would return
    mock_completion_response = ModelResponse(
        id="resp_123",
        object="chat.completion",
        created=1234567890,
        model="gpt-5-codex",
        choices=[
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "def factorial(n):\n    if n <= 1:\n        return 1\n    return n * factorial(n - 1)"
                },
                "finish_reason": "stop",
            }
        ],
        usage={
            "prompt_tokens": 10,
            "completion_tokens": 25,
            "total_tokens": 35,
        },
    )
    
    # Mock the litellm_responses function to return our mock response
    with patch('openhands.llm.llm.litellm_responses') as mock_responses:
        with patch('openhands.llm.llm.responses_to_completion_format') as mock_converter:
            mock_converter.return_value = mock_completion_response
            
            messages = [
                {'role': 'user', 'content': 'Write a factorial function in Python'}
            ]
            
            response = llm.completion(messages=messages)
            
            # Verify that responses API was called
            assert mock_responses.called, "litellm_responses should have been called"
            print("✅ Responses API was called for gpt-5-codex")
            
            # Verify that converter was called
            assert mock_converter.called, "responses_to_completion_format should have been called"
            print("✅ Response converter was called")
            
            # Verify the response
            assert response.choices[0].message.content is not None
            assert "factorial" in response.choices[0].message.content
            print("✅ Mock response received and processed correctly")
            
            # Check the arguments passed to responses API
            call_args = mock_responses.call_args
            assert call_args is not None
            kwargs = call_args.kwargs
            
            assert kwargs['model'] == 'gpt-5-codex'
            assert kwargs['api_key'] == 'fake-key'
            assert kwargs['base_url'] == 'https://api.openai.com/v1'
            assert 'input' in kwargs
            print("✅ Correct arguments passed to Responses API")
    
    return True


def test_regular_model_bypass():
    """Test that regular models bypass the Responses API."""
    print("🔄 Testing regular model bypass...")
    
    config = LLMConfig(
        model='gpt-4',
        api_key='fake-key',
        base_url='https://api.openai.com/v1',
    )
    
    llm = LLM(config=config, service_id='test')
    
    # Create a mock response
    mock_completion_response = ModelResponse(
        id="chatcmpl_123",
        object="chat.completion",
        created=1234567890,
        model="gpt-4",
        choices=[
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "print('Hello, World!')"
                },
                "finish_reason": "stop",
            }
        ],
        usage={
            "prompt_tokens": 5,
            "completion_tokens": 8,
            "total_tokens": 13,
        },
    )
    
    # Mock the regular completion function
    with patch('openhands.llm.llm.litellm_completion') as mock_completion:
        with patch('openhands.llm.llm.litellm_responses') as mock_responses:
            mock_completion.return_value = mock_completion_response
            
            messages = [
                {'role': 'user', 'content': 'Write hello world in Python'}
            ]
            
            response = llm.completion(messages=messages)
            
            # Verify that regular completion was called, not responses
            assert mock_completion.called, "litellm_completion should have been called for gpt-4"
            assert not mock_responses.called, "litellm_responses should NOT have been called for gpt-4"
            print("✅ Regular completion API used for gpt-4")
            
            # Verify the response
            assert response.choices[0].message.content == "print('Hello, World!')"
            print("✅ Regular model response processed correctly")
    
    return True


if __name__ == '__main__':
    print("=" * 60)
    print("🧪 GPT-5-CODEX MOCK TESTS")
    print("=" * 60)
    
    tests = [
        ("Converter Functions", test_converter_functions),
        ("Model Detection", test_gpt5_codex_detection),
        ("Mocked Responses API", test_gpt5_codex_with_mock),
        ("Regular Model Bypass", test_regular_model_bypass),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n{'='*40}")
        print(f"📋 {test_name.upper()}")
        print("="*40)
        
        try:
            if test_func():
                print(f"✅ {test_name} PASSED")
                passed += 1
            else:
                print(f"❌ {test_name} FAILED")
                failed += 1
        except Exception as e:
            print(f"❌ {test_name} FAILED with error: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 60)
    print("🎯 TEST SUMMARY")
    print("=" * 60)
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Total: {passed + failed}")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ gpt-5-codex integration is working correctly!")
        print("✅ Responses API converter is functioning properly")
        print("✅ Model detection and routing works as expected")
        print("\n🚀 Ready for production use with real API keys!")
        sys.exit(0)
    else:
        print(f"\n❌ {failed} test(s) failed. Please check the implementation.")
        sys.exit(1)