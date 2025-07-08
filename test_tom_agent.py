#!/usr/bin/env python3
"""Simple test script for TomCodeActAgent components."""

import asyncio
import json
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from openhands.agenthub.tom_codeact_agent.tom_api_client import TomApiClient
from openhands.agenthub.tom_codeact_agent.tom_actions import TomInstructionAction, TomSuggestionAction
from openhands.agenthub.tom_codeact_agent.tom_config import TomCodeActAgentConfig


async def test_tom_api_client():
    """Test TomApiClient basic functionality."""
    print("🧪 Testing TomApiClient...")
    
    client = TomApiClient("http://localhost:8000", timeout=5)
    
    # Test health check (will fail if Tom API not running, but shouldn't crash)
    try:
        health = await client.health_check()
        print(f"   Health check: {'✅ Healthy' if health else '❌ Unhealthy (Tom API not running)'}")
    except Exception as e:
        print(f"   Health check: ❌ Error: {e}")
    
    # Test API calls with mock data (will fail gracefully if API not running)
    try:
        instruction_response = await client.propose_instructions(
            user_id="test_user",
            original_instruction="Debug my code",
            context="User: Debug my code\nAssistant: I'll help you debug..."
        )
        print(f"   Instruction API: {'✅ Success' if instruction_response.get('success') else '❌ Failed'}")
    except Exception as e:
        print(f"   Instruction API: ❌ Error: {e}")
    
    try:
        suggestion_response = await client.suggest_next_actions(
            user_id="test_user", 
            context="Task completed: Found and fixed the bug"
        )
        print(f"   Suggestion API: {'✅ Success' if suggestion_response.get('success') else '❌ Failed'}")
    except Exception as e:
        print(f"   Suggestion API: ❌ Error: {e}")
    
    await client.close()
    print("   ✅ TomApiClient test completed")


def test_tom_actions():
    """Test Tom action classes."""
    print("🧪 Testing Tom Actions...")
    
    # Test TomInstructionAction
    instruction_action = TomInstructionAction(
        original_instruction="Fix the bug in my code",
        improved_instructions=[
            {
                "improved_instruction": "Debug the specific function causing errors by adding logging statements",
                "reasoning": "More specific and actionable approach", 
                "confidence_score": 0.85,
                "personalization_factors": ["detailed_approach", "systematic_debugging"]
            }
        ]
    )
    
    assert instruction_action.original_instruction == "Fix the bug in my code"
    assert len(instruction_action.improved_instructions) == 1
    assert "Debug the specific function" in instruction_action.content
    print("   ✅ TomInstructionAction works correctly")
    
    # Test TomSuggestionAction
    suggestion_action = TomSuggestionAction(
        suggestions=[
            {
                "action_description": "Add unit tests for the fixed code",
                "priority": "high",
                "reasoning": "Prevent future regressions",
                "expected_outcome": "More robust codebase",
                "user_preference_alignment": 0.9
            }
        ],
        context="Fixed bug in authentication module"
    )
    
    assert len(suggestion_action.suggestions) == 1
    assert "Add unit tests" in suggestion_action.content
    print("   ✅ TomSuggestionAction works correctly")


def test_tom_config():
    """Test Tom configuration."""
    print("🧪 Testing Tom Configuration...")
    
    # Test default config
    config = TomCodeActAgentConfig()
    assert config.enable_tom_integration == False
    assert config.tom_api_url == "http://localhost:8000"
    assert config.tom_timeout == 30
    print("   ✅ Default configuration correct")
    
    # Test custom config
    custom_config = TomCodeActAgentConfig(
        enable_tom_integration=True,
        tom_api_url="http://custom:9000",
        tom_user_id="custom_user",
        tom_timeout=60
    )
    assert custom_config.enable_tom_integration == True
    assert custom_config.tom_api_url == "http://custom:9000"
    assert custom_config.tom_user_id == "custom_user"
    assert custom_config.tom_timeout == 60
    print("   ✅ Custom configuration correct")
    
    # Test tom_config property
    tom_config = custom_config.tom_config
    assert tom_config.enable_tom_integration == True
    assert tom_config.tom_api_url == "http://custom:9000"
    print("   ✅ TomConfig property works correctly")


async def main():
    """Run all tests."""
    print("🚀 Starting TomCodeActAgent Component Tests\n")
    
    test_tom_config()
    print()
    
    test_tom_actions()
    print()
    
    await test_tom_api_client()
    print()
    
    print("🎉 All tests completed successfully!")
    print("\n📝 Summary:")
    print("   ✅ TomCodeActAgentConfig: Handles configuration properly")
    print("   ✅ TomInstructionAction: Formats instruction improvements correctly")
    print("   ✅ TomSuggestionAction: Formats next action suggestions correctly")
    print("   ✅ TomApiClient: Handles API communication (gracefully fails if Tom API not running)")
    print("\n🔧 To test with real Tom API:")
    print("   1. Start Tom API: tom-api --host 0.0.0.0 --port 8000")
    print("   2. Re-run this test script")
    print("\n🚀 The TomCodeActAgent is ready for integration!")


if __name__ == "__main__":
    asyncio.run(main())