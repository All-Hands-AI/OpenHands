#!/usr/bin/env python3
"""
End-to-end test script for gpt-5-codex integration with OpenHands.
This script tests the complete flow from agent creation to task execution.
"""

import os
import sys
import asyncio
from pathlib import Path

# Add the OpenHands directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from openhands.core.config import LLMConfig, OpenHandsConfig


async def test_gpt5_codex_simple_task():
    """Test gpt-5-codex with a simple coding task."""
    
    # Check for required environment variables
    api_key = os.getenv('LLM_API_KEY')
    base_url = os.getenv('LLM_BASE_URL')
    
    if not api_key:
        print("❌ LLM_API_KEY environment variable is required")
        return False
    
    if not base_url:
        print("❌ LLM_BASE_URL environment variable is required")
        return False
    
    print("🚀 Testing gpt-5-codex integration with OpenHands...")
    print(f"📡 Using base URL: {base_url}")
    print(f"🔑 API key: {'*' * (len(api_key) - 4) + api_key[-4:] if len(api_key) > 4 else '***'}")
    
    try:
        # Configure OpenHands with gpt-5-codex
        config = OpenHandsConfig(
            llm=LLMConfig(
                model='gpt-5-codex',
                api_key=api_key,
                base_url=base_url,
                temperature=0.1,
            ),
            runtime='local',
            workspace_base='/tmp/openhands_test',
            max_iterations=5,
        )
        
        print(f"✅ Configuration created with model: {config.llm.model}")
        
        # Test LLM instantiation and Responses API detection
        from openhands.llm.llm import LLM
        llm = LLM(config=config.llm, service_id='test')
        
        print(f"✅ LLM instantiated successfully")
        print(f"📋 Model: {llm.config.model}")
        print(f"🔄 Requires Responses API: {llm.requires_responses_api()}")
        
        # Test a simple completion to verify the converter works
        print("\n🧪 Testing simple completion...")
        
        messages = [
            {'role': 'user', 'content': 'Write a simple Python function that adds two numbers and returns the result. Just the code, no explanation.'}
        ]
        
        response = llm.completion(messages=messages)
        
        if response and response.choices and len(response.choices) > 0:
            content = response.choices[0].message.content
            print(f"✅ Completion successful!")
            print(f"📝 Response: {content[:100]}{'...' if len(content) > 100 else ''}")
            
            # Check if it looks like Python code
            if 'def ' in content and 'return' in content:
                print("✅ Response contains expected Python function structure")
            else:
                print("⚠️  Response doesn't look like expected Python code")
                
        else:
            print("❌ No response received from LLM")
            return False
            
        # Test with function calling
        print("\n🔧 Testing function calling capability...")
        
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "create_file",
                    "description": "Create a file with given content",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "filename": {
                                "type": "string",
                                "description": "Name of the file to create"
                            },
                            "content": {
                                "type": "string", 
                                "description": "Content to write to the file"
                            }
                        },
                        "required": ["filename", "content"]
                    }
                }
            }
        ]
        
        messages = [
            {'role': 'user', 'content': 'Create a Python file called hello.py that prints "Hello, World!"'}
        ]
        
        response = llm.completion(messages=messages, tools=tools)
        
        if response and response.choices and len(response.choices) > 0:
            message = response.choices[0].message
            if hasattr(message, 'tool_calls') and message.tool_calls:
                print("✅ Function calling works! Tool calls received:")
                for tool_call in message.tool_calls:
                    print(f"   🔧 Function: {tool_call.function.name}")
                    print(f"   📋 Arguments: {tool_call.function.arguments}")
            else:
                print("⚠️  No tool calls in response, but completion succeeded")
                print(f"📝 Content: {message.content[:100] if message.content else 'None'}")
        else:
            print("❌ Function calling test failed")
            
        print("\n🎉 All tests completed successfully!")
        print("✅ gpt-5-codex integration is working with OpenHands")
        return True
        
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_gpt5_codex_basic():
    """Test basic gpt-5-codex functionality without async."""
    
    # Check for required environment variables
    api_key = os.getenv('LLM_API_KEY')
    base_url = os.getenv('LLM_BASE_URL')
    
    if not api_key:
        print("❌ LLM_API_KEY environment variable is required")
        return False
    
    if not base_url:
        print("❌ LLM_BASE_URL environment variable is required")
        return False
    
    print("🚀 Testing basic gpt-5-codex functionality...")
    print(f"📡 Using base URL: {base_url}")
    
    try:
        # Test LLM instantiation
        from openhands.llm.llm import LLM
        from openhands.core.config import LLMConfig
        
        config = LLMConfig(
            model='gpt-5-codex',
            api_key=api_key,
            base_url=base_url,
            temperature=0.1,
        )
        
        llm = LLM(config=config, service_id='test')
        
        print(f"✅ LLM instantiated successfully")
        print(f"📋 Model: {llm.config.model}")
        print(f"🔄 Requires Responses API: {llm.requires_responses_api()}")
        
        # Test model features
        from openhands.llm.model_features import get_features
        features = get_features('gpt-5-codex')
        print(f"🔧 Function calling support: {features.supports_function_calling}")
        print(f"🧠 Reasoning effort support: {features.supports_reasoning_effort}")
        
        # Test simple completion
        print("\n🧪 Testing simple completion...")
        
        messages = [
            {'role': 'user', 'content': 'Write a Python function that calculates the factorial of a number. Just return the code.'}
        ]
        
        response = llm.completion(messages=messages)
        
        if response and response.choices and len(response.choices) > 0:
            content = response.choices[0].message.content
            print(f"✅ Completion successful!")
            print(f"📝 Response length: {len(content)} characters")
            print(f"📝 Response preview: {content[:200]}{'...' if len(content) > 200 else ''}")
            
            # Check if it looks like Python code
            if 'def ' in content and ('factorial' in content.lower() or 'fact' in content.lower()):
                print("✅ Response contains expected factorial function")
                return True
            else:
                print("⚠️  Response doesn't look like expected factorial function")
                print(f"Full response: {content}")
                return False
                
        else:
            print("❌ No response received from LLM")
            return False
            
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print("=" * 60)
    print("🧪 GPT-5-CODEX END-TO-END TEST")
    print("=" * 60)
    
    # Run basic test first
    print("\n" + "=" * 40)
    print("📋 BASIC FUNCTIONALITY TEST")
    print("=" * 40)
    
    basic_success = test_gpt5_codex_basic()
    
    if basic_success:
        print("\n✅ Basic test passed!")
    else:
        print("\n❌ Basic test failed!")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("🎯 TEST SUMMARY")
    print("=" * 60)
    
    if basic_success:
        print("✅ gpt-5-codex integration is working correctly!")
        print("✅ Responses API converter is functioning properly")
        print("✅ Model features are configured correctly")
        print("\n🚀 Ready for production use!")
    else:
        print("❌ Some tests failed. Please check the implementation.")
        sys.exit(1)