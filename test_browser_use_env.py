#!/usr/bin/env python3
"""
Test script for the new Browser-Use environment.

This script tests the basic functionality of the Browser-Use environment
to ensure it works correctly before integrating with the main codebase.
"""

import asyncio
import sys
import time
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from openhands.runtime.browser.browser_use_env import BrowserUseEnv
from openhands.core.logger import openhands_logger as logger


def test_browser_use_env():
    """Test the Browser-Use environment with basic operations."""
    print("Testing Browser-Use environment...")

    try:
        # Initialize the environment
        print("Initializing Browser-Use environment...")
        env = BrowserUseEnv()

        # Test basic navigation
        print("Testing navigation to a simple page...")
        obs = env.step('goto("https://example.com")')
        print(f"Navigation result: URL={obs.get('url', 'N/A')}, Error={obs.get('error', False)}")

        if obs.get('error'):
            print(f"Error message: {obs.get('last_action_error', 'Unknown error')}")
        else:
            print("Navigation successful!")

            # Test taking a screenshot
            print("Testing screenshot capture...")
            screenshot = obs.get('screenshot', '')
            if screenshot:
                print(f"Screenshot captured: {len(screenshot)} characters")
            else:
                print("No screenshot captured")

        # Test page content
        print("Testing page content retrieval...")
        text_content = obs.get('text_content', '')
        if text_content:
            print(f"Page content length: {len(text_content)} characters")
            print(f"First 200 characters: {text_content[:200]}...")
        else:
            print("No page content retrieved")

        # Test alive check
        print("Testing alive check...")
        is_alive = env.check_alive()
        print(f"Environment alive: {is_alive}")

        # Close the environment
        print("Closing environment...")
        env.close()
        print("Test completed successfully!")

    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True


def test_action_mapper():
    """Test the action mapper functionality."""
    print("\nTesting action mapper...")

    try:
        from openhands.runtime.browser.action_mapper import ActionMapper

        mapper = ActionMapper()

        # Test various action patterns
        test_actions = [
            'goto("https://example.com")',
            'click("123")',
            'fill("456", "test text")',
            'scroll(0, 100)',
            'search_google("test query")',
        ]

        for action_str in test_actions:
            print(f"Testing action: {action_str}")
            action = mapper.parse_action(action_str)
            if action:
                print(f"  -> Parsed successfully: {type(action).__name__}")
            else:
                print(f"  -> Failed to parse")

        print("Action mapper test completed!")

    except Exception as e:
        print(f"Action mapper test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True


def main():
    """Main test function."""
    print("Starting Browser-Use environment tests...")

    # Test action mapper first (doesn't require browser)
    if not test_action_mapper():
        print("Action mapper test failed, stopping.")
        return

    # Test browser environment
    if not test_browser_use_env():
        print("Browser environment test failed.")
        return

    print("\nAll tests completed successfully!")


if __name__ == "__main__":
    main()
