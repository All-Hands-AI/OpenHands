
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
        elif key == 'api_key':
            print(f"  {key}: [REDACTED]")
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
    """Fixture for LLMConfig - using gemini-pro-ah config (proxy)."""
    from openhands.core.config import get_llm_config_arg
    return get_llm_config_arg("gemini-pro-ah")

def test_gemini_api_call_parameters(llm_config):
    """Test that the Gemini thinking patch is working and show the parameters being sent."""
    
    try:
        # Initialize the LLM (debug patching already done at module level)
        llm = LLM(config=llm_config)

        # Create a sample message
        messages = [{'role': 'user', 'content': 'Hello, world!'}]

        # Call the completion method with thinking disabled
        print("Making LLM completion call with includeThoughts=False...")
        
        # Override the generation config to disable thinking inclusion
        custom_kwargs = {
            'messages': messages,
            'generationConfig': {
                'temperature': 0,
                'topP': 1,
                'thinkingConfig': {'includeThoughts': False}
            }
        }
        
        response = llm.completion(**custom_kwargs)
        
        print(f"\nResponse received!")
        
        # Let's see what the actual response content looks like
        print(f"\n🔍 RESPONSE ANALYSIS:")
        if hasattr(response, 'usage'):
            print(f"Input tokens: {response.usage.prompt_tokens} | Output tokens: {response.usage.completion_tokens}")
        
        # Check what attributes the response has
        print(f"Response type: {type(response)}")
        print(f"Response attributes: {[attr for attr in dir(response) if not attr.startswith('_')]}")
        
        # Check for any attributes that might contain raw data
        for attr in ['raw', '_raw_response', 'raw_response', 'original_response']:
            if hasattr(response, attr):
                value = getattr(response, attr)
                print(f"Found {attr}: {type(value)} - {value is not None}")
        
        # Try to get the text content
        response_text = ""
        if hasattr(response, 'choices') and response.choices:
            if hasattr(response.choices[0], 'message') and hasattr(response.choices[0].message, 'content'):
                response_text = response.choices[0].message.content or ""
        
        print(f"Response text length: {len(response_text)} characters")
        if response_text:
            print(f"First 200 chars: {response_text[:200]}...")
            print(f"Last 200 chars: ...{response_text[-200:]}")
        
        # Check if we got thinking content in the raw response
        print(f"\n🔍 CHECKING FOR RAW RESPONSE:")
        print(f"Has 'raw' attribute: {hasattr(response, 'raw')}")
        if hasattr(response, 'raw'):
            print(f"Raw response type: {type(response.raw)}")
            print(f"Raw response is None: {response.raw is None}")
        
        if hasattr(response, 'raw') and response.raw:
            raw_response = response.raw
            print(f"\n🔍 RAW RESPONSE STRUCTURE:")
            if 'candidates' in raw_response and raw_response['candidates']:
                candidate = raw_response['candidates'][0]
                if 'content' in candidate and 'parts' in candidate['content']:
                    parts = candidate['content']['parts']
                    print(f"Total parts in response: {len(parts)}")
                    
                    for i, part in enumerate(parts):
                        part_type = "thinking" if part.get('thought', False) else "regular"
                        text_len = len(part.get('text', '')) if 'text' in part else 0
                        print(f"  Part {i}: {part_type}, {text_len} chars")
                        if part.get('thought', False) and text_len > 0:
                            print(f"    Thinking preview: {part.get('text', '')[:100]}...")
                    
                    thinking_parts = [part for part in parts if part.get('thought', False)]
                    if thinking_parts:
                        total_thinking_chars = sum(len(part.get('text', '')) for part in thinking_parts)
                        print(f"✅ SUCCESS: Found {len(thinking_parts)} thinking part(s)! Total thinking chars: {total_thinking_chars}")
                    else:
                        print("❌ No thinking parts found in response")
                
                # Check usage metadata for thinking tokens
                if 'usageMetadata' in raw_response:
                    usage = raw_response['usageMetadata']
                    thinking_tokens = usage.get('thoughtsTokenCount', 0)
                    total_tokens = usage.get('totalTokenCount', 0)
                    output_tokens = usage.get('candidatesTokenCount', 0)
                    print(f"\n📊 TOKEN BREAKDOWN:")
                    print(f"  Total tokens: {total_tokens}")
                    print(f"  Output tokens: {output_tokens}")
                    print(f"  Thinking tokens: {thinking_tokens}")
                    if thinking_tokens > 0:
                        print(f"✅ Thinking represents {thinking_tokens}/{output_tokens} = {thinking_tokens/output_tokens*100:.1f}% of output")
                    else:
                        print("❌ No thinking tokens reported")
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        raise

if __name__ == '__main__':
    # Run the test directly
    from openhands.core.config import get_llm_config_arg
    config = get_llm_config_arg("gemini-pro-ah")
    test_gemini_api_call_parameters(config)
