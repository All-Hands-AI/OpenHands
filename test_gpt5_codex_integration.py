#!/usr/bin/env python3
"""
Integration test for gpt-5-codex using the real OpenAI API.
This test verifies that gpt-5-codex works correctly with the Responses API integration.
"""

import os
import sys
from pathlib import Path

# Add the OpenHands directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from openhands.core.config import LLMConfig
from openhands.llm.llm import LLM


def test_gpt5_codex_real_api():
    """Test gpt-5-codex with real OpenAI API (no mocking)."""
    print("🧪 Testing gpt-5-codex with real OpenAI API...")
    
    # Check if API key is available
    api_key = os.getenv('LLM_API_KEY') or os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ No API key found. Set LLM_API_KEY or OPENAI_API_KEY environment variable.")
        return False
    
    # Configure LLM for gpt-5-codex
    config = LLMConfig(
        model='gpt-5-codex',
        api_key=api_key,
        base_url=os.getenv('LLM_BASE_URL'),
    )
    
    llm = LLM(config=config, service_id='integration_test')
    
    # Verify it requires Responses API
    assert llm.requires_responses_api(), "gpt-5-codex should require Responses API"
    print("✅ gpt-5-codex correctly detected as requiring Responses API")
    
    # Test with a simple coding task
    messages = [
        {
            'role': 'user', 
            'content': 'Write a Python function that calculates the factorial of a number. Keep it simple and include a docstring.'
        }
    ]
    
    try:
        print("🔄 Making API call to gpt-5-codex...")
        response = llm.completion(messages=messages)
        
        # Verify we got a response
        assert response is not None, "Response should not be None"
        assert hasattr(response, 'choices'), "Response should have choices"
        assert len(response.choices) > 0, "Response should have at least one choice"
        assert hasattr(response.choices[0], 'message'), "Choice should have a message"
        assert hasattr(response.choices[0].message, 'content'), "Message should have content"
        
        content = response.choices[0].message.content
        assert content is not None and len(content.strip()) > 0, "Content should not be empty"
        
        print("✅ Successfully received response from gpt-5-codex")
        print(f"📝 Response length: {len(content)} characters")
        
        # Check if the response contains expected elements for a factorial function
        content_lower = content.lower()
        if 'factorial' in content_lower or 'def ' in content_lower:
            print("✅ Response appears to contain a function definition")
        else:
            print("⚠️  Response may not contain expected function definition")
        
        # Print first 200 characters of response for verification
        print(f"📄 Response preview: {content[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ API call failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_gpt5_mini_real_api():
    """Test gpt-5-mini with real OpenAI API (no mocking) to ensure it still works."""
    print("🧪 Testing gpt-5-mini with real OpenAI API...")
    
    # Check if API key is available
    api_key = os.getenv('LLM_API_KEY') or os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ No API key found. Set LLM_API_KEY or OPENAI_API_KEY environment variable.")
        return False
    
    # Configure LLM for gpt-5-mini
    config = LLMConfig(
        model='gpt-5-mini',
        api_key=api_key,
        base_url=os.getenv('LLM_BASE_URL'),
    )
    
    llm = LLM(config=config, service_id='integration_test')
    
    # Verify it does NOT require Responses API
    assert not llm.requires_responses_api(), "gpt-5-mini should NOT require Responses API"
    print("✅ gpt-5-mini correctly detected as NOT requiring Responses API")
    
    # Test with a simple task
    messages = [
        {
            'role': 'user', 
            'content': 'Write a simple Python function that adds two numbers.'
        }
    ]
    
    try:
        print("🔄 Making API call to gpt-5-mini...")
        response = llm.completion(messages=messages)
        
        # Verify we got a response
        assert response is not None, "Response should not be None"
        assert hasattr(response, 'choices'), "Response should have choices"
        assert len(response.choices) > 0, "Response should have at least one choice"
        assert hasattr(response.choices[0], 'message'), "Choice should have a message"
        assert hasattr(response.choices[0].message, 'content'), "Message should have content"
        
        content = response.choices[0].message.content
        assert content is not None and len(content.strip()) > 0, "Content should not be empty"
        
        print("✅ Successfully received response from gpt-5-mini")
        print(f"📝 Response length: {len(content)} characters")
        
        # Print first 200 characters of response for verification
        print(f"📄 Response preview: {content[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ API call failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print("=" * 60)
    print("🧪 GPT-5-CODEX INTEGRATION TEST")
    print("=" * 60)
    print("This test uses real OpenAI API calls (no mocking)")
    print("Make sure you have a valid API key set in LLM_API_KEY or OPENAI_API_KEY")
    print()
    
    tests = [
        ("GPT-5-Codex Real API", test_gpt5_codex_real_api),
        ("GPT-5-Mini Real API", test_gpt5_mini_real_api),
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
    print("🎯 INTEGRATION TEST SUMMARY")
    print("=" * 60)
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Total: {passed + failed}")
    
    if failed == 0:
        print("\n🎉 ALL INTEGRATION TESTS PASSED!")
        print("✅ gpt-5-codex Responses API integration is working!")
        print("✅ gpt-5-mini regular completion API is working!")
        print("\n🚀 Ready for production use!")
        sys.exit(0)
    else:
        print(f"\n❌ {failed} integration test(s) failed.")
        print("Please check your API key and network connection.")
        sys.exit(1)