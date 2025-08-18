"""
E2E: Settings configuration test (GitHub token)

This test navigates to OpenHands, configures the LLM API key if prompted,
then ensures the GitHub token is set in Settings → Integrations and that the
home screen shows the repository selector.
"""

import os

from playwright.sync_api import Page, expect


def test_github_token_configuration(page: Page):
    """
    Test the GitHub token configuration flow:
    1. Navigate to OpenHands
    2. Configure LLM API key if needed
    3. Check if GitHub token is already configured
    4. If not, navigate to settings and configure it
    5. Verify the token is saved and repository selection is available
    """
    # Create test-results directory if it doesn't exist
    os.makedirs('test-results', exist_ok=True)

    # Navigate to the OpenHands application
    print('Step 1: Navigating to OpenHands application...')
    page.goto('http://localhost:12000')
    page.wait_for_load_state('networkidle', timeout=30000)

    # Take initial screenshot
    page.screenshot(path='test-results/token_01_initial_load.png')
    print('Screenshot saved: token_01_initial_load.png')

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
        page.screenshot(path='test-results/token_01_5_modal_error.png')
        print('Screenshot saved: token_01_5_modal_error.png')

    # Step 2: Check if GitHub token is already configured or needs to be set
    print('Step 2: Checking if GitHub token is configured...')

    try:
        # First, check if we're already on the home screen with repository selection
        # This means the GitHub token is already configured in ~/.openhands/settings.json
        connect_to_provider = page.locator('text=Connect to a Repository')

        if connect_to_provider.is_visible(timeout=3000):
            print('Found "Connect to a Repository" section')

            # Check if we need to configure a provider (GitHub token)
            navigate_to_settings_button = page.locator(
                '[data-testid="navigate-to-settings-button"]'
            )

            if navigate_to_settings_button.is_visible(timeout=3000):
                print('GitHub token not configured. Need to navigate to settings...')

                # Click the Settings button to navigate to the settings page
                navigate_to_settings_button.click()
                page.wait_for_load_state('networkidle', timeout=10000)
                page.wait_for_timeout(3000)  # Wait for navigation to complete

                # We should now be on the /settings/integrations page
                print('Navigated to settings page, looking for GitHub token input...')

                # Check if we're on the settings page with the integrations tab
                settings_screen = page.locator('[data-testid="settings-screen"]')
                if settings_screen.is_visible(timeout=5000):
                    print('Settings screen is visible')

                    # Make sure we're on the Integrations tab
                    integrations_tab = page.locator('text=Integrations')
                    if integrations_tab.is_visible(timeout=3000):
                        # Check if we need to click the tab
                        if not page.url.endswith('/settings/integrations'):
                            print('Clicking Integrations tab...')
                            integrations_tab.click()
                            page.wait_for_load_state('networkidle')
                            page.wait_for_timeout(2000)

                    # Now look for the GitHub token input
                    github_token_input = page.locator(
                        '[data-testid="github-token-input"]'
                    )
                    if github_token_input.is_visible(timeout=5000):
                        print('Found GitHub token input field')

                        # Fill in the GitHub token from environment variable
                        github_token = os.getenv('GITHUB_TOKEN', '')
                        if github_token:
                            # Clear the field first, then fill it
                            github_token_input.clear()
                            github_token_input.fill(github_token)
                            print(
                                f'Filled GitHub token from environment variable (length: {len(github_token)})'
                            )

                            # Verify the token was filled
                            filled_value = github_token_input.input_value()
                            if filled_value:
                                print(
                                    f'Token field now contains value of length: {len(filled_value)}'
                                )
                            else:
                                print(
                                    'WARNING: Token field appears to be empty after filling'
                                )

                            # Look for the Save Changes button and ensure it's enabled
                            save_button = page.locator('[data-testid="submit-button"]')
                            if save_button.is_visible(timeout=3000):
                                # Check if button is enabled
                                is_disabled = save_button.is_disabled()
                                print(
                                    f'Save Changes button found, disabled: {is_disabled}'
                                )

                                if not is_disabled:
                                    print('Clicking Save Changes button...')
                                    save_button.click()

                                    # Wait for the save operation to complete
                                    try:
                                        # Wait for the button to show "Saving..." (if it does)
                                        page.wait_for_timeout(1000)

                                        # Wait for the save to complete - button should be disabled again
                                        page.wait_for_function(
                                            'document.querySelector(\'[data-testid="submit-button"]\').disabled === true',
                                            timeout=10000,
                                        )
                                        print(
                                            'Save operation completed - form is now clean'
                                        )
                                    except Exception:
                                        print(
                                            'Save operation completed (timeout waiting for form clean state)'
                                        )

                                    # Navigate back to home page after successful save
                                    print('Navigating back to home page...')
                                    page.goto('http://localhost:12000')
                                    page.wait_for_load_state('networkidle')
                                    page.wait_for_timeout(
                                        5000
                                    )  # Wait longer for providers to be updated
                                else:
                                    print(
                                        'Save Changes button is disabled - form may be invalid'
                                    )
                            else:
                                print('Save Changes button not found')
                        else:
                            print('No GitHub token found in environment variables')
                    else:
                        print('GitHub token input field not found on settings page')
                        # Take a screenshot to see what's on the page
                        page.screenshot(path='test-results/token_02_settings_debug.png')
                        print('Debug screenshot saved: token_02_settings_debug.png')
                else:
                    print('Settings screen not found')
            else:
                # Branch 2: GitHub token is already configured, repository selection is available
                print(
                    'GitHub token is already configured, repository selection is available'
                )

                # Check if we need to update the token by going to settings manually
                settings_button = page.locator('button:has-text("Settings")')
                if settings_button.is_visible(timeout=3000):
                    print(
                        'Settings button found, clicking to navigate to settings page...'
                    )
                    settings_button.click()
                    page.wait_for_load_state('networkidle', timeout=10000)
                    page.wait_for_timeout(3000)  # Wait for navigation to complete

                    # Navigate to the Integrations tab
                    integrations_tab = page.locator('text=Integrations')
                    if integrations_tab.is_visible(timeout=3000):
                        print('Clicking Integrations tab...')
                        integrations_tab.click()
                        page.wait_for_load_state('networkidle')
                        page.wait_for_timeout(2000)

                        # Now look for the GitHub token input
                        github_token_input = page.locator(
                            '[data-testid="github-token-input"]'
                        )
                        if github_token_input.is_visible(timeout=5000):
                            print('Found GitHub token input field')

                            # Fill in the GitHub token from environment variable
                            github_token = os.getenv('GITHUB_TOKEN', '')
                            if github_token:
                                # Clear the field first, then fill it
                                github_token_input.clear()
                                github_token_input.fill(github_token)
                                print(
                                    f'Filled GitHub token from environment variable (length: {len(github_token)})'
                                )

                                # Look for the Save Changes button and ensure it's enabled
                                save_button = page.locator(
                                    '[data-testid="submit-button"]'
                                )
                                if (
                                    save_button.is_visible(timeout=3000)
                                    and not save_button.is_disabled()
                                ):
                                    print('Clicking Save Changes button...')
                                    save_button.click()
                                    page.wait_for_timeout(3000)

                                # Navigate back to home page
                                print('Navigating back to home page...')
                                page.goto('http://localhost:12000')
                                page.wait_for_load_state('networkidle')
                                page.wait_for_timeout(3000)
                        else:
                            print(
                                'GitHub token input field not found, going back to home page'
                            )
                            page.goto('http://localhost:12000')
                            page.wait_for_load_state('networkidle')
                    else:
                        print('Integrations tab not found, going back to home page')
                        page.goto('http://localhost:12000')
                        page.wait_for_load_state('networkidle')
                else:
                    print('Settings button not found, continuing with existing token')
        else:
            print('Could not find "Connect to a Repository" section')

        page.screenshot(path='test-results/token_03_after_settings.png')
        print('Screenshot saved: token_03_after_settings.png')

    except Exception as e:
        print(f'Error checking GitHub token configuration: {e}')
        page.screenshot(path='test-results/token_04_error.png')
        print('Screenshot saved: token_04_error.png')

    # Step 3: Verify we're back on the home screen with repository selection available
    print('Step 3: Verifying repository selection is available...')

    # Wait for the home screen to load
    home_screen = page.locator('[data-testid="home-screen"]')
    expect(home_screen).to_be_visible(timeout=15000)
    print('Home screen is visible')

    # Look for the repository dropdown/selector
    repo_dropdown = page.locator('[data-testid="repo-dropdown"]')
    expect(repo_dropdown).to_be_visible(timeout=15000)
    print('Repository dropdown is visible')

    # Success - we've verified the GitHub token configuration
    print('GitHub token configuration verified successfully')
    page.screenshot(path='test-results/token_05_success.png')
    print('Screenshot saved: token_05_success.png')
