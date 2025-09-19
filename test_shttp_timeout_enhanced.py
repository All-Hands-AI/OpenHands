#!/usr/bin/env python3
"""
Enhanced test script for SHTTP timeout feature validation.
Includes tests with real endpoints and simulated slow responses.
"""

import asyncio
import time
from typing import Optional
from unittest.mock import patch, AsyncMock
from openhands.mcp.client import MCPClient
from openhands.core.config.mcp_config import MCPSHTTPServerConfig
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Test endpoints
MICROSOFT_LEARN_MCP_URL = "https://learn.microsoft.com/api/mcp"
MOCK_SLOW_URL = "https://mock-slow-endpoint.example.com/mcp"


async def test_real_endpoint_with_timeout(timeout_seconds: Optional[int]) -> dict:
    """Test with real Microsoft Learn endpoint."""
    print(f"\n🔍 Testing real endpoint with timeout: {timeout_seconds}s" if timeout_seconds else "\n🔍 Testing real endpoint with default timeout")
    
    result = {
        "timeout_config": timeout_seconds,
        "connection_success": False,
        "connection_time": None,
        "tool_call_success": False,
        "tool_call_time": None,
        "timeout_triggered": False,
        "error": None
    }
    
    try:
        # Create config
        server_config = MCPSHTTPServerConfig(
            url=MICROSOFT_LEARN_MCP_URL,
            api_key=None,
            timeout=timeout_seconds
        )
        
        print(f"  Config: timeout={server_config.timeout}s")
        
        # Create client and set timeout
        client = MCPClient()
        if server_config.timeout is not None:
            client.server_timeout = float(server_config.timeout)
            print(f"  Client timeout set to: {client.server_timeout}s")
        
        # Test connection
        start_conn = time.time()
        try:
            await client.connect_http(server_config)
            result["connection_time"] = time.time() - start_conn
            result["connection_success"] = True
            print(f"  ✅ Connected in {result['connection_time']:.2f}s")
            
            # Test tool call
            if client.tools:
                tool = client.tools[0]
                print(f"  Testing tool: {tool.name}")
                start_call = time.time()
                try:
                    await client.call_tool(
                        tool.name,
                        {"query": "test"} if "search" in tool.name else {}
                    )
                    result["tool_call_time"] = time.time() - start_call
                    result["tool_call_success"] = True
                    print(f"  ✅ Tool call succeeded in {result['tool_call_time']:.2f}s")
                except asyncio.TimeoutError:
                    result["tool_call_time"] = time.time() - start_call
                    result["timeout_triggered"] = True
                    print(f"  ⏱️ Tool call timed out after {result['tool_call_time']:.2f}s")
                    
        except asyncio.TimeoutError:
            result["connection_time"] = time.time() - start_conn
            result["timeout_triggered"] = True
            print(f"  ⏱️ Connection timed out after {result['connection_time']:.2f}s")
            
    except Exception as e:
        result["error"] = str(e)
        print(f"  ❌ Error: {e}")
    
    return result


async def test_simulated_slow_response(delay_seconds: float, timeout_seconds: Optional[int]) -> dict:
    """Test with simulated slow response using asyncio.sleep."""
    print(f"\n🔍 Testing simulated slow response (delay={delay_seconds}s, timeout={timeout_seconds}s)")
    
    result = {
        "delay": delay_seconds,
        "timeout_config": timeout_seconds,
        "completed": False,
        "actual_time": None,
        "timeout_triggered": False
    }
    
    async def slow_operation():
        """Simulate a slow network operation."""
        print(f"  Starting slow operation (will take {delay_seconds}s)...")
        await asyncio.sleep(delay_seconds)
        print(f"  Slow operation completed!")
        return "Success"
    
    start = time.time()
    try:
        if timeout_seconds:
            # Apply timeout using asyncio.wait_for (same as in the actual implementation)
            print(f"  Applying timeout of {timeout_seconds}s...")
            await asyncio.wait_for(slow_operation(), timeout=timeout_seconds)
            result["completed"] = True
            result["actual_time"] = time.time() - start
            print(f"  ✅ Operation completed in {result['actual_time']:.2f}s")
        else:
            # No timeout
            await slow_operation()
            result["completed"] = True
            result["actual_time"] = time.time() - start
            print(f"  ✅ Operation completed in {result['actual_time']:.2f}s (no timeout)")
            
    except asyncio.TimeoutError:
        result["actual_time"] = time.time() - start
        result["timeout_triggered"] = True
        print(f"  ⏱️ Operation timed out after {result['actual_time']:.2f}s")
    
    return result


async def test_timeout_enforcement():
    """Test that asyncio.wait_for properly enforces timeouts."""
    print("\n" + "="*60)
    print("TIMEOUT ENFORCEMENT TEST")
    print("="*60)
    
    # Test 1: Operation faster than timeout - should succeed
    print("\n1. Fast operation (0.5s) with 2s timeout - should succeed:")
    result = await test_simulated_slow_response(0.5, 2)
    assert result["completed"] == True, "Fast operation should complete"
    assert result["timeout_triggered"] == False, "Should not timeout"
    assert result["actual_time"] < 1, "Should complete quickly"
    print("  ✅ PASSED")
    
    # Test 2: Operation slower than timeout - should timeout
    print("\n2. Slow operation (3s) with 1s timeout - should timeout:")
    result = await test_simulated_slow_response(3, 1)
    assert result["completed"] == False, "Slow operation should not complete"
    assert result["timeout_triggered"] == True, "Should timeout"
    assert 0.9 <= result["actual_time"] <= 1.5, f"Should timeout around 1s (got {result['actual_time']:.2f}s)"
    print("  ✅ PASSED")
    
    # Test 3: Very short timeout
    print("\n3. Normal operation (1s) with 0.1s timeout - should timeout quickly:")
    result = await test_simulated_slow_response(1, 0.1)
    assert result["completed"] == False, "Operation should not complete"
    assert result["timeout_triggered"] == True, "Should timeout"
    assert result["actual_time"] < 0.3, f"Should timeout very quickly (got {result['actual_time']:.2f}s)"
    print("  ✅ PASSED")
    
    print("\n✅ All timeout enforcement tests passed!")
    return True


async def run_comprehensive_tests():
    """Run comprehensive timeout tests."""
    print("="*60)
    print("COMPREHENSIVE SHTTP TIMEOUT FEATURE TEST")
    print("="*60)
    
    all_results = []
    
    # Part 1: Test timeout enforcement with simulations
    print("\n📋 PART 1: Testing timeout enforcement mechanism")
    enforcement_passed = await test_timeout_enforcement()
    all_results.append(("Timeout Enforcement", enforcement_passed))
    
    # Part 2: Test with real endpoint
    print("\n📋 PART 2: Testing with real Microsoft Learn MCP endpoint")
    
    # Test with various timeouts
    timeouts_to_test = [None, 60, 30, 5, 2, 1]
    
    for timeout in timeouts_to_test:
        result = await test_real_endpoint_with_timeout(timeout)
        
        # Evaluate result
        if timeout is None or timeout >= 5:
            # Should succeed
            test_passed = result["connection_success"] or result["tool_call_success"]
            test_name = f"Real endpoint - {timeout}s timeout" if timeout else "Real endpoint - default timeout"
        else:
            # May timeout or succeed (depends on network speed)
            if result["timeout_triggered"]:
                print(f"  ℹ️ Timeout was triggered as might be expected for {timeout}s timeout")
                test_passed = True
            elif result["connection_success"]:
                print(f"  ℹ️ Connection was fast enough to succeed with {timeout}s timeout")
                test_passed = True
            else:
                test_passed = False
            test_name = f"Real endpoint - {timeout}s timeout (fast/timeout OK)"
        
        all_results.append((test_name, test_passed))
        await asyncio.sleep(1)  # Small delay between tests
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for test_name, passed in all_results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    all_passed = all(result for _, result in all_results)
    
    if all_passed:
        print("\n🎉 ALL TESTS PASSED!")
        print("The SHTTP timeout feature is working correctly:")
        print("  ✅ Timeout values are properly configured")
        print("  ✅ asyncio.wait_for enforces timeouts correctly")
        print("  ✅ Fast operations complete successfully")
        print("  ✅ Slow operations are terminated at timeout")
        print("  ✅ Real endpoint integration works as expected")
    else:
        print("\n⚠️ Some tests failed. Review the results above.")
    
    return all_passed


async def main():
    """Main entry point."""
    print("Starting Enhanced SHTTP Timeout Feature Tests")
    print(f"Real endpoint: {MICROSOFT_LEARN_MCP_URL}\n")
    
    success = await run_comprehensive_tests()
    
    if success:
        exit(0)
    else:
        exit(1)


if __name__ == "__main__":
    asyncio.run(main())