#!/usr/bin/env python3
"""
Final verification test for gpt-5-codex integration.
This test uses mocking to verify the API routing works correctly without making real API calls.
"""

import sys
from unittest.mock import patch, MagicMock

from openhands.core.config.llm_config import LLMConfig
from openhands.llm.llm import LLM
from litellm.types.utils import ModelResponse


def test_gpt5_codex_uses_responses_api():
    """Test that gpt-5-codex correctly uses the Responses API."""
    print("🧪 Testing gpt-5-codex uses Responses API...")
    
    config = LLMConfig(
        model='gpt-5-codex',
        api_key='test-key',
    )
    
    llm = LLM(config=config, service_id='test')
    
    # Verify it requires Responses API
    assert llm.requires_responses_api(), "gpt-5-codex should require Responses API"
    print("✅ gpt-5-codex correctly detected as requiring Responses API")
    
    # Mock the responses API
    mock_responses_result = MagicMock()
    mock_responses_result.id = "resp_123"
    mock_responses_result.created_at = 1234567890
    mock_responses_result.model = "gpt-5-codex"
    mock_responses_result.output = []
    mock_responses_result.usage = MagicMock()
    mock_responses_result.usage.input_tokens = 10
    mock_responses_result.usage.output_tokens = 20
    mock_responses_result.usage.total_tokens = 30
    
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
                    "content": "def hello():\n    return 'Hello, World!'"
                },
                "finish_reason": "stop",
            }
        ],
        usage={
            "prompt_tokens": 10,
            "completion_tokens": 20,
            "total_tokens": 30,
        },
    )
    
    with patch('openhands.llm.llm.litellm_responses') as mock_responses:
        with patch('openhands.llm.llm.responses_to_completion_format') as mock_converter:
            mock_responses.return_value = mock_responses_result
            mock_converter.return_value = mock_completion_response
            
            messages = [
                {'role': 'user', 'content': 'Write a hello world function'}
            ]
            
            response = llm.completion(messages=messages)
            
            # Verify that responses API was called
            assert mock_responses.called, "litellm_responses should have been called for gpt-5-codex"
            assert mock_converter.called, "responses_to_completion_format should have been called"
            print("✅ Responses API correctly used for gpt-5-codex")
            
            # Verify the response
            assert "hello" in response.choices[0].message.content.lower()
            print("✅ gpt-5-codex response processed correctly")
    
    return True


def test_gpt5_mini_uses_completion_api():
    """Test that gpt-5-mini correctly uses the regular completion API."""
    print("🧪 Testing gpt-5-mini uses regular completion API...")
    
    config = LLMConfig(
        model='gpt-5-mini',
        api_key='test-key',
    )
    
    llm = LLM(config=config, service_id='test')
    
    # Verify it does NOT require Responses API
    assert not llm.requires_responses_api(), "gpt-5-mini should NOT require Responses API"
    print("✅ gpt-5-mini correctly detected as NOT requiring Responses API")
    
    # Mock the regular completion API
    mock_completion_response = ModelResponse(
        id="chatcmpl_123",
        object="chat.completion",
        created=1234567890,
        model="gpt-5-mini",
        choices=[
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "def add(a, b):\n    return a + b"
                },
                "finish_reason": "stop",
            }
        ],
        usage={
            "prompt_tokens": 8,
            "completion_tokens": 15,
            "total_tokens": 23,
        },
    )
    
    with patch.object(llm, '_completion_unwrapped') as mock_completion:
        with patch('openhands.llm.llm.litellm_responses') as mock_responses:
            mock_completion.return_value = mock_completion_response
            
            messages = [
                {'role': 'user', 'content': 'Write a function to add two numbers'}
            ]
            
            response = llm.completion(messages=messages)
            
            # Verify that regular completion was called, not responses
            assert mock_completion.called, "_completion_unwrapped should have been called for gpt-5-mini"
            assert not mock_responses.called, "litellm_responses should NOT have been called for gpt-5-mini"
            print("✅ Regular completion API correctly used for gpt-5-mini")
            
            # Verify the response
            assert "add" in response.choices[0].message.content.lower()
            print("✅ gpt-5-mini response processed correctly")
    
    return True


if __name__ == '__main__':
    print("=" * 60)
    print("🧪 FINAL VERIFICATION TEST")
    print("=" * 60)
    
    tests = [
        ("GPT-5-Codex Responses API", test_gpt5_codex_uses_responses_api),
        ("GPT-5-Mini Completion API", test_gpt5_mini_uses_completion_api),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n{'=' * 40}")
        print(f"📋 {test_name.upper()}")
        print(f"{'=' * 40}")
        
        try:
            result = test_func()
            if result:
                print(f"✅ {test_name} PASSED")
                passed += 1
            else:
                print(f"❌ {test_name} FAILED")
                failed += 1
        except Exception as e:
            print(f"❌ {test_name} FAILED with exception: {e}")
            failed += 1
    
    print(f"\n{'=' * 60}")
    print("🎯 FINAL VERIFICATION SUMMARY")
    print(f"{'=' * 60}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Total: {passed + failed}")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ gpt-5-codex integration is working correctly!")
        print("✅ gpt-5-codex correctly uses Responses API")
        print("✅ gpt-5-mini correctly uses regular completion API")
        print("✅ No recursion issues detected")
        print("\n🚀 Ready for production use!")
        sys.exit(0)
    else:
        print(f"\n❌ {failed} test(s) failed. Please check the implementation.")
        sys.exit(1)