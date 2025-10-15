#!/usr/bin/env python3
"""
Test script to verify that the completion API routing works correctly.
This test verifies the logic without making actual API calls.
"""

import sys
from pathlib import Path

# Add the OpenHands directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from openhands.core.config import LLMConfig
from openhands.llm.llm import LLM


def test_gpt5_mini_routing():
    """Test that gpt-5-mini is correctly routed to regular completion API."""
    print("🧪 Testing gpt-5-mini API routing...")
    
    config = LLMConfig(
        model='gpt-5-mini',
        api_key='fake-key',
    )
    
    llm = LLM(config=config, service_id='test')
    
    # Verify it doesn't require Responses API
    assert not llm.requires_responses_api(), "gpt-5-mini should NOT require Responses API"
    print("✅ gpt-5-mini correctly detected as NOT requiring Responses API")
    
    return True


def test_gpt5_codex_routing():
    """Test that gpt-5-codex is correctly routed to Responses API."""
    print("🧪 Testing gpt-5-codex API routing...")
    
    config = LLMConfig(
        model='gpt-5-codex',
        api_key='fake-key',
    )
    
    llm = LLM(config=config, service_id='test')
    
    # Verify it requires Responses API
    requires_responses = llm.requires_responses_api()
    print(f"Debug: llm.config.model = '{llm.config.model}'")
    print(f"Debug: requires_responses_api() = {requires_responses}")
    
    assert requires_responses, "gpt-5-codex should require Responses API"
    print("✅ gpt-5-codex correctly detected as requiring Responses API")
    
    return True


if __name__ == '__main__':
    print("=" * 60)
    print("🧪 COMPLETION API ROUTING TEST")
    print("=" * 60)
    
    tests = [
        ("GPT-5-Mini Routing", test_gpt5_mini_routing),
        ("GPT-5-Codex Routing", test_gpt5_codex_routing),
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
        print("✅ API routing logic is working correctly!")
        print("✅ gpt-5-mini correctly routed to regular completion API")
        print("✅ gpt-5-codex correctly routed to Responses API")
        print("\n🚀 Ready for production use!")
        sys.exit(0)
    else:
        print(f"\n❌ {failed} test(s) failed. Please check the implementation.")
        sys.exit(1)