"""
E2E: Logout — clear provider tokens and verify home screen state

This test verifies the logout functionality:
1. Starts with a configured GitHub token (assumes settings test has run)
2. Performs logout from providers
3. Verifies that provider tokens are cleared
4. Verifies that the home screen shows the correct state (no providers configured)
"""

import os

from playwright.sync_api import Page, expect


def test_logout_clear_provider_tokens(page: Page):
    """
    Test the logout functionality to clear provider tokens:
    1. Navigate to OpenHands (assumes GitHub token is already configured)
    2. Verify that repository selection is available (providers are configured)
    3. Access the user menu and click logout
    4. Verify that the page reloads and shows "Connect to Provider" message
    5. Verify that repository selection is not available (providers cleared)
    """
    # Create test-results directory if it doesn't exist
    os.makedirs('test-results', exist_ok=True)

    # Navigate to the OpenHands application
    print('Step 1: Navigating to OpenHands application...')
    # Try both ports in case the application is running on a different port
    app_url = 'http://localhost:12000'
    try:
        page.goto(app_url)
        page.wait_for_load_state('networkidle', timeout=10000)
    except Exception:
        print('Port 12000 not available, trying port 12001...')
        app_url = 'http://localhost:12001'
        page.goto(app_url)
        page.wait_for_load_state('networkidle', timeout=30000)

    print(f'Successfully connected to OpenHands at {app_url}')

    # Take initial screenshot
    page.screenshot(path='test-results/logout_01_initial_load.png')
    print('Screenshot saved: logout_01_initial_load.png')

    # Step 1.5: Handle any initial modals that might appear (LLM API key configuration)
    try:
        # Check for AI Provider Configuration modal
        config_modal = page.locator('text=AI Provider Configuration')
        if config_modal.is_visible(timeout=5000):
            print('AI Provider Configuration modal detected')

            # Fill in the LLM API key if available
            llm_api_key_input = page.locator('[data-testid="llm-api-key-input"]')
            if llm_api_key_input.is_visible(timeout=3000):
                llm_api_key = os.getenv('LLM_API_KEY', 'test-key')
                llm_api_key_input.fill(llm_api_key)
                print(f'Filled LLM API key (length: {len(llm_api_key)})')

            # Click the Save button
            save_button = page.locator('button:has-text("Save")')
            if save_button.is_visible(timeout=3000):
                save_button.click()
                page.wait_for_timeout(2000)
                print('Saved LLM API key configuration')

        # Check for Privacy Preferences modal
        privacy_modal = page.locator('text=Your Privacy Preferences')
        if privacy_modal.is_visible(timeout=5000):
            print('Privacy Preferences modal detected')
            confirm_button = page.locator('button:has-text("Confirm Preferences")')
            if confirm_button.is_visible(timeout=3000):
                confirm_button.click()
                page.wait_for_timeout(2000)
                print('Confirmed privacy preferences')
    except Exception as e:
        print(f'Error handling initial modals: {e}')
        page.screenshot(path='test-results/logout_01_5_modal_error.png')
        print('Screenshot saved: logout_01_5_modal_error.png')

    # Step 2: Verify that we start with providers configured (repository selection available)
    print('Step 2: Verifying initial state - providers should be configured...')

    # Wait for the home screen to load
    home_screen = page.locator('[data-testid="home-screen"]')
    expect(home_screen).to_be_visible(timeout=15000)
    print('Home screen is visible')

    # Check if we need to configure providers first
    connect_to_provider = page.locator('text=Connect to a Repository')
    navigate_to_settings_button = page.locator(
        '[data-testid="navigate-to-settings-button"]'
    )

    if navigate_to_settings_button.is_visible(timeout=3000):
        print('Providers not configured yet. Setting up GitHub token first...')

        # Navigate to settings to configure GitHub token
        navigate_to_settings_button.click()
        page.wait_for_load_state('networkidle', timeout=10000)
        page.wait_for_timeout(3000)

        # Configure GitHub token
        github_token_input = page.locator('[data-testid="github-token-input"]')
        if github_token_input.is_visible(timeout=5000):
            github_token = os.getenv('GITHUB_TOKEN', '')
            if github_token:
                github_token_input.clear()
                github_token_input.fill(github_token)
                print(f'Filled GitHub token (length: {len(github_token)})')

                # Save the token
                save_button = page.locator('[data-testid="submit-button"]')
                if (
                    save_button.is_visible(timeout=3000)
                    and not save_button.is_disabled()
                ):
                    save_button.click()
                    page.wait_for_timeout(3000)
                    print('Saved GitHub token')

        # Navigate back to home
        page.goto(app_url)
        page.wait_for_load_state('networkidle')
        page.wait_for_timeout(5000)

    # Verify repository selection is now available
    repo_dropdown = page.locator('[data-testid="repo-dropdown"]')
    expect(repo_dropdown).to_be_visible(timeout=15000)
    print('Repository dropdown is visible - providers are configured')

    page.screenshot(path='test-results/logout_02_providers_configured.png')
    print('Screenshot saved: logout_02_providers_configured.png')

    # Step 3: Access the user menu
    print('Step 3: Accessing user menu...')

    # Look for the user actions component (avatar)
    user_actions = page.locator('[data-testid="user-actions"]')
    expect(user_actions).to_be_visible(timeout=10000)
    print('User actions component is visible')

    # Click on the user avatar to open the menu
    user_actions.click()
    page.wait_for_timeout(1000)

    page.screenshot(path='test-results/logout_03_user_menu_opened.png')
    print('Screenshot saved: logout_03_user_menu_opened.png')

    # Step 4: Click the logout button
    print('Step 4: Clicking logout button...')

    # Look for the logout button in the context menu
    logout_button = page.locator('[data-testid="logout-button"]')
    expect(logout_button).to_be_visible(timeout=5000)
    print('Logout button is visible')

    # Click the logout button
    logout_button.click()
    print('Clicked logout button')

    # Step 5: Wait for page reload and verify logout completed
    print('Step 5: Waiting for page reload after logout...')

    # Wait for the page to reload (logout triggers window.location.reload())
    page.wait_for_load_state('networkidle', timeout=30000)
    page.wait_for_timeout(5000)  # Additional wait for providers to be updated

    page.screenshot(path='test-results/logout_04_after_reload.png')
    print('Screenshot saved: logout_04_after_reload.png')

    # Step 6: Verify that providers are cleared and home screen shows correct state
    print('Step 6: Verifying logout completed - providers should be cleared...')

    # Wait for the home screen to load again
    home_screen = page.locator('[data-testid="home-screen"]')
    expect(home_screen).to_be_visible(timeout=15000)
    print('Home screen is visible after logout')

    # Verify that "Connect to a Repository" section is visible
    connect_to_provider = page.locator('text=Connect to a Repository')
    expect(connect_to_provider).to_be_visible(timeout=10000)
    print('Found "Connect to a Repository" section')

    # Verify that the "Settings" button is visible (indicating no providers are configured)
    navigate_to_settings_button = page.locator(
        '[data-testid="navigate-to-settings-button"]'
    )
    expect(navigate_to_settings_button).to_be_visible(timeout=10000)
    print('Settings button is visible - indicating providers are not configured')

    # Verify that repository dropdown is NOT visible (since no providers are configured)
    repo_dropdown = page.locator('[data-testid="repo-dropdown"]')
    expect(repo_dropdown).not_to_be_visible(timeout=5000)
    print('Repository dropdown is not visible - confirming providers are cleared')

    # Step 7: Verify the connect to provider message is displayed
    print('Step 7: Verifying connect to provider message...')

    # Check for the connect to provider message
    connect_message = page.locator(
        'text=Connect to a provider to access your repositories'
    )
    if not connect_message.is_visible(timeout=3000):
        # Try alternative message text
        connect_message = page.locator('[data-testid="repo-connector"] p')
        if connect_message.is_visible(timeout=3000):
            message_text = connect_message.text_content()
            print(f'Found connect message: {message_text}')
        else:
            print('Connect message not found, but settings button is visible')

    page.screenshot(path='test-results/logout_05_logout_verified.png')
    print('Screenshot saved: logout_05_logout_verified.png')

    # Success - logout functionality verified
    print('✅ Logout functionality verified successfully:')
    print('   - Provider tokens were cleared')
    print('   - Home screen shows "Connect to Provider" state')
    print('   - Repository selection is not available')
    print('   - Settings button is visible for reconfiguration')
