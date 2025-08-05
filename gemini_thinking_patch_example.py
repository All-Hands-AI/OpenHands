#!/usr/bin/env python3
"""
Example script demonstrating how to monkey-patch litellm to automatically
include thinkingConfig in Gemini API calls.

This approach allows you to enable Gemini's thinking/reasoning capabilities
without modifying the litellm source code.

This version patches both sync and async transformation functions to ensure
compatibility with both litellm.completion() and litellm.acompletion().
OpenHands uses the sync version, so this is important for real-world usage.
"""

import asyncio
import litellm
from litellm.llms.vertex_ai.gemini.transformation import (
    async_transform_request_body,
    sync_transform_request_body,
)


def apply_gemini_thinking_patch():
    """
    Apply a monkey patch to litellm to automatically include thinkingConfig
    in all Gemini API calls (both sync and async).
    """
    # Store the original transformation functions
    original_async_transform = async_transform_request_body
    original_sync_transform = sync_transform_request_body
    
    # Create patched async version that adds thinkingConfig
    async def patched_async_transform_with_thinking(*args, **kwargs):
        # Add thinkingConfig to optional_params before calling the original function
        if 'optional_params' in kwargs:
            # Configure thinking settings - customize as needed
            kwargs['optional_params']['thinkingConfig'] = {
                'includeThoughts': True,
                # Add other thinking config options here if needed
            }
        # Call the original function with modified params
        return await original_async_transform(*args, **kwargs)
    
    # Create patched sync version that adds thinkingConfig
    def patched_sync_transform_with_thinking(*args, **kwargs):
        # Add thinkingConfig to optional_params before calling the original function
        if 'optional_params' in kwargs:
            # Configure thinking settings - customize as needed
            kwargs['optional_params']['thinkingConfig'] = {
                'includeThoughts': True,
                # Add other thinking config options here if needed
            }
        # Call the original function with modified params
        return original_sync_transform(*args, **kwargs)
    
    # Apply the monkey patches
    import litellm.llms.vertex_ai.gemini.vertex_and_google_ai_studio_gemini as gemini_module
    gemini_module.async_transform_request_body = patched_async_transform_with_thinking
    gemini_module.sync_transform_request_body = patched_sync_transform_with_thinking
    
    print("✅ Gemini thinking patch applied successfully (both sync and async)!")
    print("   All Gemini API calls will now include thinkingConfig with includeThoughts=True")
    
    return original_async_transform, original_sync_transform


def remove_gemini_thinking_patch(original_functions):
    """Remove the monkey-patch and restore original functions."""
    original_async_transform, original_sync_transform = original_functions
    import litellm.llms.vertex_ai.gemini.vertex_and_google_ai_studio_gemini as gemini_module
    gemini_module.async_transform_request_body = original_async_transform
    gemini_module.sync_transform_request_body = original_sync_transform
    print("✅ Gemini thinking patch removed successfully!")


async def example_async_usage():
    """
    Example of using litellm.acompletion() with the thinking patch applied.
    """
    try:
        # Make an async completion request - thinkingConfig will be automatically included
        response = await litellm.acompletion(
            model="gemini/gemini-pro",
            messages=[
                {"role": "user", "content": "Explain the concept of quantum entanglement in simple terms."}
            ],
            temperature=0.7,
            max_tokens=200,
            api_key="your-gemini-api-key-here"  # Replace with your actual API key
        )
        
        print("\n🔮 Async Response:")
        print(response.choices[0].message.content)
        
    except Exception as e:
        print(f"❌ Error in async call: {e}")


def example_sync_usage():
    """
    Example of using litellm.completion() with the thinking patch applied.
    This is the version that OpenHands uses.
    """
    try:
        # Make a sync completion request - thinkingConfig will be automatically included
        response = litellm.completion(
            model="gemini/gemini-pro",
            messages=[
                {"role": "user", "content": "What are the key principles of machine learning?"}
            ],
            temperature=0.7,
            max_tokens=200,
            api_key="your-gemini-api-key-here"  # Replace with your actual API key
        )
        
        print("\n🔮 Sync Response:")
        print(response.choices[0].message.content)
        
    except Exception as e:
        print(f"❌ Error in sync call: {e}")


async def main():
    """
    Main function demonstrating the complete workflow.
    """
    print("🚀 Gemini Thinking Patch Example")
    print("=" * 40)
    
    # Apply the patch
    original_functions = apply_gemini_thinking_patch()
    
    try:
        print("\n📝 Testing sync completion (like OpenHands uses)...")
        example_sync_usage()
        
        print("\n📝 Testing async completion...")
        await example_async_usage()
        
    finally:
        # Clean up - restore original functions
        remove_gemini_thinking_patch(original_functions)
    
    print("\n✨ Example completed!")


if __name__ == "__main__":
    # Note: You'll need to set your Gemini API key for this to work
    # export GEMINI_API_KEY="your-api-key-here"
    # or replace "your-gemini-api-key-here" in the examples above
    
    asyncio.run(main())