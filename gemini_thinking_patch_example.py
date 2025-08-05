#!/usr/bin/env python3
"""
Example script demonstrating how to monkey-patch litellm to automatically
include thinkingConfig in Gemini API calls.

This approach allows you to enable Gemini's thinking/reasoning capabilities
without modifying the litellm source code.
"""

import asyncio
import litellm
from litellm.llms.vertex_ai.gemini.transformation import async_transform_request_body


def apply_gemini_thinking_patch():
    """
    Apply a monkey patch to litellm to automatically include thinkingConfig
    in all Gemini API calls.
    """
    # Store the original transformation function
    original_transform = async_transform_request_body
    
    # Create a patched version that adds thinkingConfig
    async def patched_transform_with_thinking(*args, **kwargs):
        # Add thinkingConfig to optional_params before calling the original function
        if 'optional_params' in kwargs:
            # Configure thinking settings - customize as needed
            kwargs['optional_params']['thinkingConfig'] = {
                'includeThoughts': True,
                # Add other thinking config options here if needed
            }
        # Call the original function with modified params
        return await original_transform(*args, **kwargs)
    
    # Apply the monkey patch
    import litellm.llms.vertex_ai.gemini.vertex_and_google_ai_studio_gemini as gemini_module
    gemini_module.async_transform_request_body = patched_transform_with_thinking
    
    print("✅ Gemini thinking patch applied successfully!")
    print("   All Gemini API calls will now include thinkingConfig with includeThoughts=True")


async def example_usage():
    """
    Example of using litellm with the thinking patch applied.
    """
    try:
        # Make a completion request - thinkingConfig will be automatically included
        response = await litellm.acompletion(
            model="gemini/gemini-pro",
            messages=[
                {"role": "user", "content": "Explain the concept of quantum entanglement in simple terms."}
            ],
            temperature=0.7,
            max_tokens=200,
            # No need to manually specify thinkingConfig - it's added automatically!
        )
        
        print("Response:", response.choices[0].message.content)
        
    except Exception as e:
        print(f"Error: {e}")
        print("Note: This example requires valid Gemini API credentials.")


def main():
    """
    Main function demonstrating the patch application and usage.
    """
    print("🧠 Gemini Thinking Patch Example")
    print("=" * 40)
    
    # Apply the monkey patch
    apply_gemini_thinking_patch()
    
    print("\n📝 Example usage:")
    print("   The following call will automatically include thinkingConfig:")
    print("   await litellm.acompletion(model='gemini/gemini-pro', messages=[...])")
    
    # Uncomment the following lines to test with real API calls:
    # print("\n🚀 Testing with actual API call...")
    # asyncio.run(example_usage())


if __name__ == "__main__":
    main()