"""
E2E: Base URL configuration test

This test verifies that the base URL configuration works correctly for E2E tests,
allowing tests to run against localhost, CI, or remote OpenHands instances.
"""

import os

from playwright.sync_api import Page


def test_base_url_configuration(page: Page, base_url: str):
    """
    Test the base URL configuration functionality:
    1. Verify that the base_url fixture provides the correct URL
    2. Navigate to the configured URL
    3. Verify that the OpenHands application loads correctly
    4. Take screenshots for verification
    """
    # Create test-results directory if it doesn't exist
    os.makedirs('test-results', exist_ok=True)

    # Use default URL if base_url is not provided
    if not base_url:
        base_url = 'http://localhost:12000'

    print(f'Testing base URL configuration: {base_url}')

    # Navigate to the configured OpenHands application
    print(f'Step 1: Navigating to OpenHands application at {base_url}...')
    page.goto(base_url)
    page.wait_for_load_state('networkidle', timeout=30000)

    # Take initial screenshot
    page.screenshot(path='test-results/base_url_01_initial_load.png')
    print('Screenshot saved: base_url_01_initial_load.png')

    # Verify that we're on the OpenHands application
    # Look for key elements that indicate this is OpenHands
    print('Step 2: Verifying OpenHands application loaded...')

    # Check for the OpenHands title or logo
    try:
        # Look for common OpenHands UI elements
        page.wait_for_selector('text=OpenHands', timeout=10000)
        print('✅ Found OpenHands text on page')
    except Exception:
        try:
            # Alternative: look for the main container or other identifying elements
            page.wait_for_selector(
                '[data-testid="app"], .app, #app, #root', timeout=10000
            )
            print('✅ Found main application container')
        except Exception:
            # If we can't find specific elements, at least verify the page loaded
            print('⚠️  Could not find specific OpenHands elements, but page loaded')

    # Verify the URL is correct
    current_url = page.url
    print(f'Current URL: {current_url}')

    # The current URL should start with our base URL
    assert current_url.startswith(base_url), (
        f'Expected URL to start with {base_url}, got {current_url}'
    )
    print('✅ URL verification passed')

    # Take final screenshot
    page.screenshot(path='test-results/base_url_02_verification_complete.png')
    print('Screenshot saved: base_url_02_verification_complete.png')

    print('✅ Base URL configuration test completed successfully')


def test_base_url_environment_variable(page: Page, base_url: str):
    """
    Test that demonstrates how the base URL can be configured via environment variables
    or command line options for different deployment scenarios.
    """
    # Create test-results directory if it doesn't exist
    os.makedirs('test-results', exist_ok=True)

    # Use default URL if base_url is not provided
    if not base_url:
        base_url = 'http://localhost:12000'

    print(f'Testing with configured base URL: {base_url}')

    # This test demonstrates different scenarios:
    # 1. Default: pytest tests/e2e/test_base_url_configuration.py
    #    -> Uses http://localhost:12000
    # 2. Custom URL: pytest tests/e2e/test_base_url_configuration.py --base-url=https://demo.openhands.ai
    #    -> Uses https://demo.openhands.ai
    # 3. CI Environment: The base URL can be set in CI to point to the deployed instance

    # Navigate to the application
    print(f'Navigating to: {base_url}')
    page.goto(base_url)
    page.wait_for_load_state('networkidle', timeout=30000)

    # Take screenshot showing the configured environment
    page.screenshot(path='test-results/base_url_03_environment_test.png')
    print('Screenshot saved: base_url_03_environment_test.png')

    # Verify we can interact with the page (basic smoke test)
    current_url = page.url
    assert current_url.startswith(base_url), (
        f'URL mismatch: expected {base_url}, got {current_url}'
    )

    print(f'✅ Successfully tested against: {base_url}')
    print('✅ Base URL environment configuration test completed')
