#!/usr/bin/env python3
"""
Test script to verify that our Gemini thinking patch works with OpenHands LLM module.
This demonstrates the integration between our patch and the actual OpenHands code.
"""

from unittest.mock import patch, MagicMock
import httpx
from litellm.llms.vertex_ai.gemini.transformation import sync_transform_request_body
import litellm.llms.vertex_ai.gemini.vertex_and_google_ai_studio_gemini as gemini_module


def apply_openhands_gemini_thinking_patch():
    """
    Apply the thinking patch specifically for OpenHands usage.
    OpenHands uses sync litellm.completion(), so we need to patch the sync version.
    """
    # Store the original function
    original_sync_transform = sync_transform_request_body
    
    # Create patched sync version that adds thinkingConfig
    def patched_sync_transform_with_thinking(*args, **kwargs):
        # Add thinkingConfig to optional_params
        if 'optional_params' in kwargs:
            kwargs['optional_params']['thinkingConfig'] = {
                'includeThoughts': True,
            }
        return original_sync_transform(*args, **kwargs)
    
    # Apply the patch
    gemini_module.sync_transform_request_body = patched_sync_transform_with_thinking
    
    print("✅ OpenHands Gemini thinking patch applied!")
    return original_sync_transform


def test_openhands_llm_integration():
    """
    Test that our patch works with the OpenHands LLM module.
    """
    print("🧪 Testing OpenHands LLM integration...")
    
    # Apply our patch
    original_transform = apply_openhands_gemini_thinking_patch()
    
    try:
        # Import the OpenHands LLM module and config
        from openhands.llm.llm import LLM
        from openhands.core.config import LLMConfig
        
        # Mock the HTTP client to capture the request
        with patch('litellm.llms.custom_httpx.http_handler.HTTPHandler.post') as mock_post:
            # Configure the mock response
            mock_request = httpx.Request('POST', 'https://example.com')
            mock_response = httpx.Response(
                200,
                request=mock_request,
                json={
                    'candidates': [
                        {'content': {'parts': [{'text': 'Test response with thinking'}]}}
                    ],
                    'usageMetadata': {
                        'promptTokenCount': 10,
                        'candidatesTokenCount': 5,
                        'totalTokenCount': 15,
                    },
                },
            )
            mock_post.return_value = mock_response
            
            # Create an LLM config for Gemini
            config = LLMConfig(model='gemini/gemini-pro', api_key='dummy-key')
            
            # Create an LLM instance with Gemini
            llm = LLM(config=config)
            
            # Make a completion call (this uses sync litellm.completion internally)
            try:
                response = llm.completion(
                    messages=[{'role': 'user', 'content': 'Test message'}],
                    temperature=0.7,
                )
                
                # Verify the request was made
                if mock_post.called:
                    # Get the final JSON payload
                    args, kwargs = mock_post.call_args
                    final_json_payload = kwargs.get('json', {})
                    
                    # Check if thinkingConfig was included
                    generation_config = final_json_payload.get('generationConfig', {})
                    if 'thinkingConfig' in generation_config:
                        print("✅ SUCCESS: thinkingConfig found in request payload!")
                        print(f"   thinkingConfig: {generation_config['thinkingConfig']}")
                        return True
                    else:
                        print("❌ FAILURE: thinkingConfig not found in request payload")
                        print(f"   generationConfig: {generation_config}")
                        return False
                else:
                    print("❌ FAILURE: HTTP request was not made")
                    return False
                    
            except Exception as e:
                print(f"⚠️  LLM call failed (expected with dummy key): {e}")
                # Even if the call fails due to auth, we can still check if the patch worked
                if mock_post.called:
                    args, kwargs = mock_post.call_args
                    final_json_payload = kwargs.get('json', {})
                    generation_config = final_json_payload.get('generationConfig', {})
                    if 'thinkingConfig' in generation_config:
                        print("✅ SUCCESS: thinkingConfig found despite auth failure!")
                        return True
                return False
                
    except ImportError as e:
        print(f"⚠️  Could not import OpenHands LLM module: {e}")
        print("   This is expected if OpenHands modules are not available")
        return None
        
    finally:
        # Restore original function
        gemini_module.sync_transform_request_body = original_transform
        print("✅ Patch removed, original function restored")


if __name__ == "__main__":
    print("🚀 OpenHands Gemini Thinking Patch Integration Test")
    print("=" * 50)
    
    result = test_openhands_llm_integration()
    
    if result is True:
        print("\n🎉 Integration test PASSED!")
        print("   The patch successfully works with OpenHands LLM module")
    elif result is False:
        print("\n❌ Integration test FAILED!")
        print("   The patch did not work as expected")
    else:
        print("\n⚠️  Integration test SKIPPED!")
        print("   OpenHands modules not available for testing")
    
    print("\n✨ Test completed!")