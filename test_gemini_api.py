
import asyncio
import os
from unittest.mock import MagicMock, patch

import pytest
from pydantic import SecretStr

# PATCH LITELLM BEFORE ANY IMPORTS THAT MIGHT CACHE IT
import litellm
original_completion = litellm.completion

def debug_completion(*args, **kwargs):
    print("🔍 DEBUG_COMPLETION CALLED!")
    print(f"\n" + "="*80)
    print("ALL PARAMETERS SENT TO GEMINI API:")
    print("="*80)
    print(f"args: {args}")
    print(f"\nkwargs ({len(kwargs)} total):")
    for key, value in sorted(kwargs.items()):
        if key == 'messages':
            print(f"  {key}: [{len(value)} messages]")
            for i, msg in enumerate(value):
                print(f"    [{i}] {msg.get('role', 'unknown')}: {msg.get('content', '')[:50]}...")
        else:
            print(f"  {key}: {value}")
    print("="*80)
    
    # Call the original function
    return original_completion(*args, **kwargs)

# Patch immediately
litellm.completion = debug_completion
print(f"🔧 EARLY PATCH: litellm.completion = {litellm.completion}")

from openhands.core.config import LLMConfig
from openhands.llm.llm import LLM

# Set dummy API key for testing
os.environ['GOOGLE_API_KEY'] = 'test_api_key'
# Enable debug mode to see parameters
os.environ['DEBUG_LLM'] = 'true'

@pytest.fixture
def llm_config():
    """Fixture for LLMConfig - using direct Gemini API, not proxy."""
    return LLMConfig(
        model='gemini-2.5-pro',  # Direct API, not proxy
        api_key=SecretStr('test_api_key'),
        temperature=0.5,
        max_output_tokens=100,
    )

def test_gemini_api_call_parameters(llm_config):
    """Test that the Gemini thinking patch is working and show the parameters being sent."""
    import litellm
    
    # Patch litellm.completion to intercept and show parameters
    original_completion = litellm.completion
    
    def debug_completion(*args, **kwargs):
        print("🔍 DEBUG_COMPLETION CALLED!")
        print(f"\n" + "="*80)
        print("ALL PARAMETERS SENT TO GEMINI API:")
        print("="*80)
        print(f"args: {args}")
        print(f"\nkwargs ({len(kwargs)} total):")
        for key, value in sorted(kwargs.items()):
            if key == 'messages':
                print(f"  {key}: [{len(value)} messages]")
                for i, msg in enumerate(value):
                    print(f"    [{i}] {msg.get('role', 'unknown')}: {msg.get('content', '')[:50]}...")
            else:
                print(f"  {key}: {value}")
        print("="*80)
        
        # Call the original function
        return original_completion(*args, **kwargs)
    
    # Temporarily replace the completion function BEFORE creating LLM
    litellm.completion = debug_completion  # Show exact parameters being sent
    print(f"✅ Patched litellm.completion: {litellm.completion}")
    print(f"Original was: {original_completion}")
    
    try:
        # Initialize the LLM AFTER patching
        llm = LLM(config=llm_config)

        # Create a sample message
        messages = [{'role': 'user', 'content': 'Hello, world!'}]

        # Call the completion method
        print("Making LLM completion call...")
        response = llm.completion(messages=messages)
        
        print(f"\nResponse received!")
        # Removed detailed response content printing
        
        # Check if we got thinking content in the raw response
        if hasattr(response, 'raw') and response.raw:
            raw_response = response.raw
            if 'candidates' in raw_response and raw_response['candidates']:
                candidate = raw_response['candidates'][0]
                if 'content' in candidate and 'parts' in candidate['content']:
                    parts = candidate['content']['parts']
                    thinking_parts = [part for part in parts if part.get('thought', False)]
                    if thinking_parts:
                        print(f"✅ SUCCESS: Found {len(thinking_parts)} thinking part(s)!")
                    else:
                        print("❌ No thinking parts found in response")
                
                # Check usage metadata for thinking tokens
                if 'usageMetadata' in raw_response:
                    usage = raw_response['usageMetadata']
                    thinking_tokens = usage.get('thoughtsTokenCount', 0)
                    if thinking_tokens > 0:
                        print(f"✅ Thinking tokens used: {thinking_tokens}")
                    else:
                        print("❌ No thinking tokens reported")
        
    finally:
        # Restore the original function
        litellm.completion = original_completion

if __name__ == '__main__':
    # Run the test directly
    config = LLMConfig(model='gemini-2.5-pro', api_key=SecretStr('test_api_key'))
    test_gemini_api_call_parameters(config)
