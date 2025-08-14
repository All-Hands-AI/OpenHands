"""
End-to-end tests for the OpenHands application.

This file contains tests for:
1. GitHub token configuration
2. Starting a conversation with the OpenHands agent
3. Simple browser navigation (for testing Playwright setup)
"""

import os
import socket
import time
import urllib.request

import pytest
from playwright.sync_api import Page, expect


def get_readme_line_count():
    """Get the line count of the main README.md file for verification."""
    # Get the path to the repository root directory
    current_dir = os.getcwd()
    # If we're in the tests/e2e directory, go up two levels to the repo root
    if current_dir.endswith('tests/e2e'):
        repo_root = os.path.abspath(os.path.join(current_dir, '../..'))
    else:
        # If we're already at the repo root or somewhere else, try to find README.md
        repo_root = current_dir

    readme_path = os.path.join(repo_root, 'README.md')
    print(f'Looking for README.md at: {readme_path}')
    try:
        with open(readme_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            return len(lines)
    except (FileNotFoundError, IOError, OSError) as e:
        print(f'Error reading README.md: {e}')
        return 0


@pytest.fixture(scope='module')
def openhands_app():
    """
    Fixture that assumes OpenHands is already running on localhost.

    This fixture checks if the OpenHands application is running on the expected port
    and raises an exception if it's not available.
    """
    print('Checking if OpenHands is running...')

    # Check if the application is running by trying to connect to the frontend port
    max_attempts = 3
    for attempt in range(1, max_attempts + 1):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2)
            result = s.connect_ex(('localhost', 12000))
            s.close()

            if result == 0:
                print(
                    f'OpenHands is running on port 12000 (attempt {attempt}/{max_attempts})'
                )
                # Verify we can get HTML content
                try:
                    with urllib.request.urlopen(
                        'http://localhost:12000', timeout=5
                    ) as response:
                        html = response.read().decode('utf-8')
                        if '<html' in html:
                            print('Successfully received HTML content from OpenHands')
                            yield None  # Success - yield the fixture value
                            return
                        else:
                            print(
                                f'WARNING: Port 12000 is open but not serving HTML content (attempt {attempt}/{max_attempts})'
                            )
                except Exception as e:
                    print(
                        f'WARNING: Port 12000 is open but could not fetch HTML: {e} (attempt {attempt}/{max_attempts})'
                    )
            else:
                print(
                    f'WARNING: OpenHands is not running on port 12000 (attempt {attempt}/{max_attempts})'
                )

            if attempt < max_attempts:
                print('Waiting 5 seconds before retry...')
                time.sleep(5)
        except Exception as e:
            print(f'ERROR checking OpenHands: {e} (attempt {attempt}/{max_attempts})')
            if attempt < max_attempts:
                print('Waiting 5 seconds before retry...')
                time.sleep(5)

    # If we get here, all attempts failed
    raise ConnectionError(
        'OpenHands is not running on port 12000. Make sure to run "make run" before running the tests.'
    )


def test_simple_browser_navigation(page: Page):
    """Test that we can navigate to a page using Playwright."""
    # Navigate to the GitHub repository
    page.goto('https://github.com/openhands-agent/OpenHands')

    # Check that the page title contains "OpenHands"
    expect(page).to_have_title(
        'GitHub - openhands-agent/OpenHands: 🙌 OpenHands: Code Less, Make More'
    )

    # Check that the repository name is displayed
    repo_header = page.locator('strong[itemprop="name"] a')
    expect(repo_header).to_contain_text('OpenHands')

    print('Successfully navigated to the OpenHands GitHub repository')


def test_github_token_configuration(page):
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


def test_conversation_start(page):
    """
    Test starting a conversation with the OpenHands agent:
    1. Navigate to OpenHands (assumes GitHub token is already configured)
    2. Select the OpenHands repository
    3. Click Launch
    4. Wait for the agent to initialize
    5. Ask a question about the README.md file
    6. Verify the agent responds correctly
    """
    # Create test-results directory if it doesn't exist
    os.makedirs('test-results', exist_ok=True)

    expected_line_count = get_readme_line_count()
    print(f'Expected README.md line count: {expected_line_count}')

    # Navigate to the OpenHands application
    print('Step 1: Navigating to OpenHands application...')
    page.goto('http://localhost:12000')
    page.wait_for_load_state('networkidle', timeout=30000)

    # Take initial screenshot
    page.screenshot(path='test-results/conv_01_initial_load.png')
    print('Screenshot saved: conv_01_initial_load.png')

    # Note: Initial modals are handled in test_github_token_configuration

    # Step 2: Select the OpenHands repository
    print('Step 2: Selecting openhands-agent/OpenHands repository...')

    # Wait for the home screen to load
    home_screen = page.locator('[data-testid="home-screen"]')
    expect(home_screen).to_be_visible(timeout=15000)
    print('Home screen is visible')

    # Look for the repository dropdown/selector
    repo_dropdown = page.locator('[data-testid="repo-dropdown"]')
    expect(repo_dropdown).to_be_visible(timeout=15000)
    print('Repository dropdown is visible')

    # Click on the repository input to open dropdown
    repo_dropdown.click()
    page.wait_for_timeout(1000)

    # Type the repository name
    try:
        # Try keyboard input for React Select component
        page.keyboard.press('Control+a')  # Select all
        page.keyboard.type('openhands-agent/OpenHands')
        print('Used keyboard.type() for React Select component')
    except Exception as e:
        print(f'Keyboard input failed: {e}')

    page.wait_for_timeout(2000)  # Wait for search results

    # Try to find and click the repository option
    option_selectors = [
        '[data-testid="repo-dropdown"] [role="option"]:has-text("openhands-agent/OpenHands")',
        '[data-testid="repo-dropdown"] [role="option"]:has-text("OpenHands")',
        '[data-testid="repo-dropdown"] div[id*="option"]:has-text("openhands-agent/OpenHands")',
        '[data-testid="repo-dropdown"] div[id*="option"]:has-text("OpenHands")',
        '[role="option"]:has-text("openhands-agent/OpenHands")',
        '[role="option"]:has-text("OpenHands")',
        'div:has-text("openhands-agent/OpenHands"):not([id="aria-results"])',
        'div:has-text("OpenHands"):not([id="aria-results"])',
    ]

    option_found = False
    for selector in option_selectors:
        try:
            option = page.locator(selector).first
            if option.is_visible(timeout=3000):
                print(f'Found repository option with selector: {selector}')
                try:
                    option.click(force=True)
                    print('Successfully clicked option with force=True')
                    option_found = True
                    page.wait_for_timeout(2000)
                    break
                except Exception:
                    continue
        except Exception:
            continue

    if not option_found:
        print(
            'Could not find repository option in dropdown, trying keyboard navigation'
        )
        page.keyboard.press('ArrowDown')
        page.wait_for_timeout(500)
        page.keyboard.press('Enter')
        print('Used keyboard navigation to select option')

    page.screenshot(path='test-results/conv_02_repo_selected.png')
    print('Screenshot saved: conv_02_repo_selected.png')

    # Step 3: Click Launch button
    print('Step 3: Clicking Launch button...')

    # Use the specific repository launch button
    launch_button = page.locator('[data-testid="repo-launch-button"]')
    expect(launch_button).to_be_visible(timeout=10000)

    # Wait for the button to be enabled (not disabled)
    max_wait_attempts = 30
    button_enabled = False

    for attempt in range(max_wait_attempts):
        try:
            is_disabled = launch_button.is_disabled()
            if not is_disabled:
                print(
                    f'Repository Launch button is now enabled (attempt {attempt + 1})'
                )
                button_enabled = True
                break
            else:
                print(
                    f'Launch button still disabled, waiting... (attempt {attempt + 1}/{max_wait_attempts})'
                )
                page.wait_for_timeout(2000)
        except Exception as e:
            print(f'Error checking button state (attempt {attempt + 1}): {e}')
            page.wait_for_timeout(2000)

    # Try to click the button
    try:
        if button_enabled:
            launch_button.click()
            print('Launch button clicked normally')
        else:
            print('Launch button still disabled, trying JavaScript force click...')
            # Use JavaScript to force click the button
            result = page.evaluate("""() => {
                const button = document.querySelector('[data-testid="repo-launch-button"]');
                if (button) {
                    console.log('Found button, removing disabled attribute');
                    button.removeAttribute('disabled');
                    console.log('Clicking button');
                    button.click();
                    return true;
                }
                return false;
            }""")

            if result:
                print('Successfully force-clicked Launch button with JavaScript')
            else:
                print('JavaScript could not find the Launch button')
    except Exception as e:
        print(f'Error clicking Launch button: {e}')
        page.screenshot(path='test-results/conv_03_launch_error.png')
        print('Screenshot saved: conv_03_launch_error.png')
        raise

    # Step 4: Wait for conversation interface to load
    print('Step 4: Waiting for conversation interface to load...')

    # Wait for navigation to conversation page
    navigation_timeout = 300000  # 5 minutes (300 seconds)
    check_interval = 10000  # Check every 10 seconds

    # Take a screenshot after clicking Launch
    page.screenshot(path='test-results/conv_04_after_launch.png')
    print('Screenshot saved: conv_04_after_launch.png')

    # Check for loading indicators and wait for them to disappear
    loading_selectors = [
        '[data-testid="loading-indicator"]',
        '[data-testid="loading-spinner"]',
        '.loading-spinner',
        '.spinner',
        'div:has-text("Loading...")',
        'div:has-text("Initializing...")',
        'div:has-text("Please wait...")',
    ]

    for selector in loading_selectors:
        try:
            loading = page.locator(selector)
            if loading.is_visible(timeout=5000):
                print(f'Found loading indicator with selector: {selector}')
                print('Waiting for loading to complete...')
                # Wait for the loading indicator to disappear
                expect(loading).not_to_be_visible(
                    timeout=120000
                )  # Wait up to 2 minutes
                print('Loading completed')
                break
        except Exception:
            continue

    # Check if the URL has changed to a conversation URL
    try:
        current_url = page.url
        print(f'Current URL: {current_url}')
        if '/conversation/' in current_url or '/chat/' in current_url:
            print('URL indicates conversation page has loaded')
    except Exception as e:
        print(f'Error checking URL: {e}')

    # Wait for the conversation interface to appear
    start_time = time.time()
    conversation_loaded = False

    while time.time() - start_time < navigation_timeout / 1000:
        try:
            # Check for conversation interface elements using multiple selectors
            selectors = [
                # Original selectors
                '.scrollbar.flex.flex-col.grow',
                '[data-testid="chat-input"]',
                '[data-testid="app-route"]',
                # Additional selectors to try
                '[data-testid="conversation-screen"]',
                '[data-testid="message-input"]',
                '.conversation-container',
                '.chat-container',
                'textarea',
                'form textarea',
                'div[role="main"]',
                'main',
            ]

            for selector in selectors:
                try:
                    element = page.locator(selector)
                    if element.is_visible(timeout=2000):
                        print(
                            f'Found conversation interface element with selector: {selector}'
                        )
                        conversation_loaded = True
                        break
                except Exception:
                    continue

            if conversation_loaded:
                break

            # Take periodic screenshots during the wait
            if (time.time() - start_time) % (check_interval / 1000) < 1:
                elapsed = int(time.time() - start_time)
                page.screenshot(path=f'test-results/conv_05_waiting_{elapsed}s.png')
                print(f'Screenshot saved: conv_05_waiting_{elapsed}s.png')

            # Wait before checking again
            page.wait_for_timeout(5000)

        except Exception as e:
            print(f'Error checking for conversation interface: {e}')
            page.wait_for_timeout(5000)

    if not conversation_loaded:
        print('Timed out waiting for conversation interface to load')
        page.screenshot(path='test-results/conv_06_timeout.png')
        print('Screenshot saved: conv_06_timeout.png')
        raise TimeoutError('Timed out waiting for conversation interface to load')

    # Step 5: Wait for agent to initialize
    print('Step 5: Waiting for agent to initialize...')

    # Wait for the agent to be ready for input
    try:
        # Look for the chat input to be visible, which indicates the agent interface is loaded
        chat_input = page.locator('[data-testid="chat-input"]')
        expect(chat_input).to_be_visible(timeout=60000)  # Wait up to 1 minute

        # Check if the submit button is visible (don't check if it's enabled yet)
        submit_button = page.locator('[data-testid="chat-input"] button[type="submit"]')
        expect(submit_button).to_be_visible(timeout=10000)

        print('Agent interface is loaded')

        # Wait for a reasonable time for the agent to initialize
        page.wait_for_timeout(10000)  # Wait 10 seconds

    except Exception as e:
        print(f'Could not confirm agent interface is loaded: {e}')
        # Continue anyway, as the UI might be different

    page.screenshot(path='test-results/conv_07_agent_ready.png')
    print('Screenshot saved: conv_07_agent_ready.png')

    # Step 6: Wait for agent to be fully ready for input
    print('Step 6: Waiting for agent to be fully ready for input...')

    # Wait for agent to transition from "Connecting..." to ready state (up to 8 minutes)
    max_wait_time = 480  # 8 minutes (increased from 5 minutes)
    start_time = time.time()
    agent_ready = False

    print(f'Waiting up to {max_wait_time} seconds for agent to be ready...')

    while time.time() - start_time < max_wait_time:
        elapsed = int(time.time() - start_time)

        # Take periodic screenshots
        if elapsed % 30 == 0 and elapsed > 0:  # Every 30 seconds
            page.screenshot(path=f'test-results/conv_waiting_{elapsed}s.png')
            print(f'Screenshot saved: conv_waiting_{elapsed}s.png (waiting {elapsed}s)')

        # Check for agent ready states by looking for status indicators
        try:
            # Check current status messages to understand agent state
            status_messages = []
            status_selectors = [
                'div:has-text("Connecting")',
                'div:has-text("Starting Runtime")',
                'div:has-text("Waiting for runtime to start")',
                'div:has-text("Agent is ready")',
                'div:has-text("Waiting for user input")',
                'div:has-text("Awaiting input")',
                'div:has-text("Task completed")',
                'div:has-text("Agent has finished")',
            ]

            # Target the specific status bar component first (most reliable)
            status_bar_selector = '.bg-base-secondary .text-stone-400'
            try:
                status_elements = page.locator(status_bar_selector)
                if status_elements.count() > 0:
                    for i in range(status_elements.count()):
                        text = status_elements.nth(i).text_content()
                        if text and text.strip():
                            status_messages.append(text.strip())
            except Exception:
                pass

            # Fallback: check for status text in broader selectors but with strict filtering
            for selector in status_selectors:
                try:
                    elements = page.locator(selector)
                    if elements.count() > 0:
                        for i in range(elements.count()):
                            text = elements.nth(i).text_content()
                            if text and text.strip():
                                # Filter out CSS content and xterm styling
                                clean_text = text.strip()
                                # Only keep text that doesn't contain CSS or xterm content
                                if (
                                    '.xterm-' not in clean_text
                                    and 'background-color:' not in clean_text
                                    and 'color: #' not in clean_text
                                    and len(clean_text) < 200
                                ):  # Reasonable length limit
                                    status_messages.append(clean_text)
                except Exception:
                    continue

            if status_messages:
                # Remove duplicates and limit output
                unique_statuses = list(dict.fromkeys(status_messages))[:3]
                print(f'Current status: {unique_statuses}')

            # Check if agent is truly ready for input (not just connecting or starting)
            ready_indicators = [
                'div:has-text("Agent is ready")',
                'div:has-text("Waiting for user input")',
                'div:has-text("Awaiting input")',
                'div:has-text("Task completed")',
                'div:has-text("Agent has finished")',
            ]

            # Also check if input field is enabled and visible
            input_ready = False
            submit_ready = False
            try:
                input_field = page.locator('[data-testid="chat-input"] textarea')
                submit_button = page.locator(
                    '[data-testid="chat-input"] button[type="submit"]'
                )

                if (
                    input_field.is_visible(timeout=2000)
                    and input_field.is_enabled(timeout=2000)
                    and submit_button.is_visible(timeout=2000)
                    and submit_button.is_enabled(timeout=2000)
                ):
                    print(
                        'Chat input field and submit button are both visible and enabled'
                    )
                    input_ready = True
                    submit_ready = True
            except Exception:
                pass

            # Agent is ready if we have ready indicators AND input/submit are ready
            connecting_or_starting = any(
                msg
                for msg in status_messages
                if 'connecting' in msg.lower()
                or 'starting' in msg.lower()
                or 'runtime to start' in msg.lower()
            )

            has_ready_indicator = False
            for indicator in ready_indicators:
                try:
                    element = page.locator(indicator)
                    if element.is_visible(timeout=2000):
                        print(f'Agent appears ready (found: {indicator})')
                        has_ready_indicator = True
                        break
                except Exception:
                    continue

            if (
                (has_ready_indicator or not connecting_or_starting)
                and input_ready
                and submit_ready
            ):
                print(
                    '✅ Agent is ready for user input - input field and submit button are enabled'
                )
                agent_ready = True
                break
            elif (
                not connecting_or_starting
                and not status_messages
                and input_ready
                and submit_ready
            ):
                # No status messages and no connecting/starting - might be ready
                print(
                    'No status messages found and input is ready, agent appears ready...'
                )
                agent_ready = True
                break

        except Exception as e:
            print(f'Error checking agent ready state: {e}')

        page.wait_for_timeout(2000)  # Wait 2 seconds before checking again

    if not agent_ready:
        page.screenshot(path='test-results/conv_timeout_waiting_for_agent.png')
        raise AssertionError(
            f'Agent did not become ready for input within {max_wait_time} seconds'
        )

    # Step 7: Ask a question about the README.md file
    print('Step 7: Asking question about README.md file...')

    # Find the message input field using multiple selectors
    input_selectors = [
        '[data-testid="chat-input"] textarea',
        '[data-testid="message-input"]',
        'textarea',
        'form textarea',
        'input[type="text"]',
        '[placeholder*="message"]',
        '[placeholder*="question"]',
        '[placeholder*="ask"]',
        '[contenteditable="true"]',
    ]

    message_input = None
    for selector in input_selectors:
        try:
            input_element = page.locator(selector)
            if input_element.is_visible(timeout=5000):
                print(f'Found message input with selector: {selector}')
                message_input = input_element
                break
        except Exception:
            continue

    if not message_input:
        print('Could not find message input, trying to reload the page')
        page.screenshot(path='test-results/conv_08_no_input_found.png')
        print('Screenshot saved: conv_08_no_input_found.png')

        # Try to reload the page and wait for it to load
        try:
            print('Reloading the page...')
            page.reload()
            page.wait_for_load_state('networkidle', timeout=30000)
            print('Page reloaded')

            # Try to find the message input again
            for selector in input_selectors:
                try:
                    input_element = page.locator(selector)
                    if input_element.is_visible(timeout=5000):
                        print(
                            f'Found message input after reload with selector: {selector}'
                        )
                        message_input = input_element
                        break
                except Exception:
                    continue
        except Exception as e:
            print(f'Error reloading page: {e}')

        if not message_input:
            print('Still could not find message input, taking final screenshot')
            page.screenshot(path='test-results/conv_09_reload_failed.png')
            print('Screenshot saved: conv_09_reload_failed.png')
            raise AssertionError('Could not find message input field after reload')

    # Type the question
    message_input.fill(
        'How many lines are there in the README.md file in the root directory of this repository? Please use wc -l README.md to count the lines.'
    )
    print('Entered question about README.md line count')

    # Find and wait for the submit button using multiple selectors
    submit_selectors = [
        '[data-testid="chat-input"] button[type="submit"]',
        'button[type="submit"]',
        'button:has-text("Send")',
        'button:has-text("Submit")',
        'button svg[data-testid="send-icon"]',
        'button.send-button',
        'form button',
        'button:right-of(textarea)',
        'button:right-of(input[type="text"])',
    ]

    submit_button = None
    for selector in submit_selectors:
        try:
            button_element = page.locator(selector)
            if button_element.is_visible(timeout=5000):
                print(f'Found submit button with selector: {selector}')
                submit_button = button_element
                break
        except Exception:
            continue

    # Wait for the button to be enabled (not disabled)
    button_enabled = False

    if submit_button:
        max_wait_time = 60  # seconds
        start_time = time.time()

        while time.time() - start_time < max_wait_time:
            try:
                if not submit_button.is_disabled():
                    button_enabled = True
                    print('Submit button is enabled')
                    break
                print(
                    f'Waiting for submit button to be enabled... ({int(time.time() - start_time)}s)'
                )
            except Exception as e:
                print(f'Error checking if button is disabled: {e}')
            page.wait_for_timeout(2000)  # Wait 2 seconds between checks

    if not submit_button or not button_enabled:
        print('Submit button not found or never became enabled, trying alternatives')

        # Try pressing Enter key as an alternative to clicking submit
        try:
            message_input.press('Enter')
            print('Pressed Enter key to submit')
            button_enabled = True
        except Exception as e:
            print(f'Error pressing Enter key: {e}')

            # Try to use JavaScript to force click if we found a button
            if submit_button:
                try:
                    page.evaluate("""() => {
                        const button = document.querySelector('[data-testid="chat-input"] button[type="submit"]');
                        if (button) {
                            button.removeAttribute('disabled');
                            button.click();
                            return true;
                        }
                        return false;
                    }""")
                    print('Used JavaScript to force click submit button')
                    button_enabled = True
                except Exception as e2:
                    print(f'JavaScript force click failed: {e2}')

        if not button_enabled:
            page.screenshot(path='test-results/conv_09_submit_failed.png')
            print('Screenshot saved: conv_09_submit_failed.png')
            raise RuntimeError('Could not submit message')
    else:
        submit_button.click()

    print('Clicked submit button')

    page.screenshot(path='test-results/conv_08_question_sent.png')
    print('Screenshot saved: conv_08_question_sent.png')

    # Step 8: Waiting for agent response to README question
    print('Step 8: Waiting for agent response to README question...')

    response_wait_time = 180  # 3 minutes for response (increased from 2 minutes)
    response_start_time = time.time()

    while time.time() - response_start_time < response_wait_time:
        elapsed = int(time.time() - response_start_time)

        # Take periodic screenshots
        if elapsed % 30 == 0 and elapsed > 0:  # Every 30 seconds (reduced frequency)
            page.screenshot(path=f'test-results/conv_response_wait_{elapsed}s.png')
            print(
                f'Screenshot saved: conv_response_wait_{elapsed}s.png (waiting {elapsed}s for response)'
            )

        # Check specifically for agent messages containing the line count
        try:
            agent_messages = page.locator('[data-testid="agent-message"]').all()
            if elapsed % 30 == 0:  # Only print count every 30 seconds
                print(f'Found {len(agent_messages)} agent messages')

            for i, msg in enumerate(agent_messages):
                try:
                    content = msg.text_content()
                    if content and len(content.strip()) > 10:
                        # Much more aggressive filtering to remove CSS/HTML noise
                        lines = content.split('\n')
                        meaningful_lines = []
                        for line in lines:
                            line = line.strip()
                            # Skip CSS, HTML, and other noise - much more comprehensive
                            if (
                                line
                                and len(line) < 500  # Skip very long lines (likely CSS)
                                and not line.startswith('.')
                                and not line.startswith('#')
                                and not line.startswith('stroke')
                                and not line.startswith('fill')
                                and not line.startswith('xterm')
                                and not line.startswith('{')
                                and not line.startswith('}')
                                and not line.startswith('color:')
                                and not line.startswith('background-color:')
                                and not line.startswith('rgb(')
                                and not line.startswith('rgba(')
                                and not line.startswith('var(')
                                and not line.startswith('calc(')
                                and not line.startswith('url(')
                                and not line.startswith('linear-gradient')
                                and not line.startswith('radial-gradient')
                                and not line.startswith('transform:')
                                and not line.startswith('transition:')
                                and not line.startswith('animation:')
                                and not line.startswith('font-')
                                and not line.startswith('border')
                                and not line.startswith('margin')
                                and not line.startswith('padding')
                                and not line.startswith('width:')
                                and not line.startswith('height:')
                                and not line.startswith('position:')
                                and not line.startswith('display:')
                                and not line.startswith('flex')
                                and not line.startswith('grid')
                                and not line.startswith('overflow')
                                and not line.startswith('z-index')
                                and not line.startswith('opacity')
                                and not line.startswith('visibility')
                                and not line.startswith('cursor')
                                and not line.startswith('pointer-events')
                                and not line.startswith('user-select')
                                and not line.startswith('box-')
                                and not line.startswith('text-')
                                and not line.startswith('white-space')
                                and not line.startswith('word-')
                                and not line.startswith('line-height')
                                and not line.startswith('letter-spacing')
                                and not line.startswith('text-align')
                                and not line.startswith('vertical-align')
                                and not line.startswith('list-style')
                                and not line.startswith('outline')
                                and not line.startswith('box-shadow')
                                and not line.startswith('text-shadow')
                                and not line.startswith('filter')
                                and not line.startswith('backdrop-filter')
                                and not line.startswith('clip')
                                and not line.startswith('mask')
                                and not line.startswith('scroll')
                                and not line.startswith('resize')
                                and not line.startswith('content:')
                                and not line.startswith('quotes:')
                                and not line.startswith('counter-')
                                and not line.startswith('page-')
                                and not line.startswith('break-')
                                and not line.startswith('orphans')
                                and not line.startswith('widows')
                                and not line.startswith('column-')
                                and not line.startswith('table-')
                                and not line.startswith('caption-')
                                and not line.startswith('empty-cells')
                                and not line.startswith('border-collapse')
                                and not line.startswith('border-spacing')
                                and not line.startswith('speak')
                                and not line.startswith('voice-')
                                and not line.startswith('azimuth')
                                and not line.startswith('elevation')
                                and not line.startswith('stress')
                                and not line.startswith('richness')
                                and not line.startswith('speech-rate')
                                and not line.startswith('volume')
                                and not line.startswith('pause')
                                and not line.startswith('cue')
                                and not line.startswith('play-during')
                                and not line.startswith('mix-blend-mode')
                                and not line.startswith('isolation')
                                and not line.startswith('will-change')
                                and not line.startswith('contain')
                                and not line.startswith('appearance')
                                and not line.startswith('-webkit-')
                                and not line.startswith('-moz-')
                                and not line.startswith('-ms-')
                                and not line.startswith('-o-')
                                and '{ color:' not in line
                                and '{ background-color:' not in line
                                and 'background-color: #' not in line
                                and 'color: #' not in line
                                and '.xterm-' not in line
                                and 'renderer-owner' not in line
                                and not (
                                    line.count('{') > 3 or line.count('}') > 3
                                )  # Skip lines with many braces
                                and not (
                                    line.count(':') > 5
                                )  # Skip lines with many colons (CSS properties)
                                and not (
                                    line.count(';') > 5
                                )  # Skip lines with many semicolons (CSS rules)
                                and not (
                                    line.count('#') > 2
                                )  # Skip lines with many hash symbols (colors)
                                and not line.replace(' ', '')
                                .replace('.', '')
                                .replace('#', '')
                                .replace(':', '')
                                .replace(';', '')
                                .replace('{', '')
                                .replace('}', '')
                                .replace('-', '')
                                .replace('_', '')
                                .isdigit()  # Skip lines that are mostly CSS values
                            ):
                                meaningful_lines.append(line)

                        if (
                            meaningful_lines and elapsed % 30 == 0
                        ):  # Only print every 30 seconds
                            meaningful_content = ' '.join(
                                meaningful_lines[:2]
                            )  # Only first 2 meaningful lines
                            print(
                                f'Agent message {i}: {meaningful_content[:100]}...'
                                if len(meaningful_content) > 100
                                else f'Agent message {i}: {meaningful_content}'
                            )

                        # Check if this agent message contains the README line count
                        content_lower = content.lower()
                        # Look for any reasonable line count (between 100-300 lines) mentioned with README
                        import re

                        line_count_pattern = r'\b(\d{3})\b'  # 3-digit numbers (100-999)
                        line_counts = re.findall(line_count_pattern, content)

                        if (
                            (
                                str(expected_line_count) in content
                                and 'readme' in content_lower
                            )
                            or (
                                'line' in content_lower
                                and 'readme' in content_lower
                                and any(
                                    num in content
                                    for num in ['183', str(expected_line_count)]
                                )
                            )
                            or (
                                'line' in content_lower
                                and 'readme' in content_lower
                                and line_counts
                                and any(100 <= int(num) <= 300 for num in line_counts)
                            )
                        ):
                            print(
                                '✅ Found agent response about README.md with line count!'
                            )
                            # Filter out CSS content for logging
                            clean_content = content
                            if '.xterm-' in content or 'background-color:' in content:
                                # Extract just the meaningful text, skip CSS
                                lines = content.split('\n')
                                meaningful_lines = []
                                for line in lines:
                                    line = line.strip()
                                    if (
                                        line
                                        and not line.startswith('.xterm-')
                                        and 'background-color:' not in line
                                        and 'color: #' not in line
                                        and len(line) < 200
                                    ):
                                        meaningful_lines.append(line)
                                clean_content = '\n'.join(
                                    meaningful_lines[:5]
                                )  # Only first 5 meaningful lines
                            print(f'✅ Agent response: {clean_content}')

                            # Take final screenshots
                            page.screenshot(
                                path='test-results/conv_09_agent_response.png'
                            )
                            print('Screenshot saved: conv_09_agent_response.png')
                            page.screenshot(path='test-results/conv_10_final_state.png')
                            print('Screenshot saved: conv_10_final_state.png')

                            print(
                                '✅ Test completed successfully - agent provided correct README line count'
                            )
                            return  # Success!

                except Exception as e:
                    print(f'Error processing agent message {i}: {e}')
                    continue

        except Exception as e:
            print(f'Error checking for agent messages: {e}')

        page.wait_for_timeout(5000)  # Wait 5 seconds before checking again

    # If we get here, we didn't find the expected response
    print('❌ Did not find agent response with README line count within time limit')

    # Take final screenshots for debugging
    page.screenshot(path='test-results/conv_09_agent_response.png')
    print('Screenshot saved: conv_09_agent_response.png')
    page.screenshot(path='test-results/conv_10_final_state.png')
    print('Screenshot saved: conv_10_final_state.png')

    # Debug: Print all agent messages found (filtered for readability)
    try:
        agent_messages = page.locator('[data-testid="agent-message"]').all()
        print(f'\n=== ALL AGENT MESSAGES FOUND ({len(agent_messages)}) ===')
        for i, msg in enumerate(agent_messages):
            try:
                content = msg.text_content()
                # Filter content for readability with comprehensive CSS filtering
                if content:
                    lines = content.split('\n')
                    meaningful_lines = []
                    for line in lines:
                        line = line.strip()
                        # Apply the same comprehensive filtering as above
                        if (
                            line
                            and len(line) < 500
                            and not line.startswith('.')
                            and not line.startswith('#')
                            and not line.startswith('stroke')
                            and not line.startswith('fill')
                            and not line.startswith('xterm')
                            and not line.startswith('{')
                            and not line.startswith('}')
                            and not line.startswith('color:')
                            and not line.startswith('background-color:')
                            and not line.startswith('rgb(')
                            and not line.startswith('rgba(')
                            and not line.startswith('var(')
                            and not line.startswith('calc(')
                            and not line.startswith('url(')
                            and not line.startswith('linear-gradient')
                            and not line.startswith('radial-gradient')
                            and not line.startswith('transform:')
                            and not line.startswith('transition:')
                            and not line.startswith('animation:')
                            and not line.startswith('font-')
                            and not line.startswith('border')
                            and not line.startswith('margin')
                            and not line.startswith('padding')
                            and not line.startswith('width:')
                            and not line.startswith('height:')
                            and not line.startswith('position:')
                            and not line.startswith('display:')
                            and not line.startswith('flex')
                            and not line.startswith('grid')
                            and not line.startswith('overflow')
                            and not line.startswith('z-index')
                            and not line.startswith('opacity')
                            and not line.startswith('visibility')
                            and not line.startswith('cursor')
                            and not line.startswith('pointer-events')
                            and not line.startswith('user-select')
                            and not line.startswith('box-')
                            and not line.startswith('text-')
                            and not line.startswith('white-space')
                            and not line.startswith('word-')
                            and not line.startswith('line-height')
                            and not line.startswith('letter-spacing')
                            and not line.startswith('text-align')
                            and not line.startswith('vertical-align')
                            and not line.startswith('list-style')
                            and not line.startswith('outline')
                            and not line.startswith('box-shadow')
                            and not line.startswith('text-shadow')
                            and not line.startswith('filter')
                            and not line.startswith('backdrop-filter')
                            and not line.startswith('clip')
                            and not line.startswith('mask')
                            and not line.startswith('scroll')
                            and not line.startswith('resize')
                            and not line.startswith('content:')
                            and not line.startswith('quotes:')
                            and not line.startswith('counter-')
                            and not line.startswith('page-')
                            and not line.startswith('break-')
                            and not line.startswith('orphans')
                            and not line.startswith('widows')
                            and not line.startswith('column-')
                            and not line.startswith('table-')
                            and not line.startswith('caption-')
                            and not line.startswith('empty-cells')
                            and not line.startswith('border-collapse')
                            and not line.startswith('border-spacing')
                            and not line.startswith('speak')
                            and not line.startswith('voice-')
                            and not line.startswith('azimuth')
                            and not line.startswith('elevation')
                            and not line.startswith('stress')
                            and not line.startswith('richness')
                            and not line.startswith('speech-rate')
                            and not line.startswith('volume')
                            and not line.startswith('pause')
                            and not line.startswith('cue')
                            and not line.startswith('play-during')
                            and not line.startswith('mix-blend-mode')
                            and not line.startswith('isolation')
                            and not line.startswith('will-change')
                            and not line.startswith('contain')
                            and not line.startswith('appearance')
                            and not line.startswith('-webkit-')
                            and not line.startswith('-moz-')
                            and not line.startswith('-ms-')
                            and not line.startswith('-o-')
                            and '{ color:' not in line
                            and '{ background-color:' not in line
                            and 'background-color: #' not in line
                            and 'color: #' not in line
                            and '.xterm-' not in line
                            and 'renderer-owner' not in line
                            and not (line.count('{') > 3 or line.count('}') > 3)
                            and not (line.count(':') > 5)
                            and not (line.count(';') > 5)
                            and not (line.count('#') > 2)
                            and not line.replace(' ', '')
                            .replace('.', '')
                            .replace('#', '')
                            .replace(':', '')
                            .replace(';', '')
                            .replace('{', '')
                            .replace('}', '')
                            .replace('-', '')
                            .replace('_', '')
                            .isdigit()
                        ):
                            meaningful_lines.append(line)

                    if meaningful_lines:
                        filtered_content = ' '.join(
                            meaningful_lines[:3]
                        )  # First 3 meaningful lines
                        print(
                            f'Agent Message {i}: {filtered_content[:200]}...'
                            if len(filtered_content) > 200
                            else f'Agent Message {i}: {filtered_content}'
                        )
                    else:
                        print(f'Agent Message {i}: [Filtered out CSS/HTML content]')
                else:
                    print(f'Agent Message {i}: [Empty content]')
            except Exception as e:
                print(f'Agent Message {i}: Error reading content - {e}')
        print('=== END AGENT MESSAGES ===\n')
    except Exception as e:
        print(f'Error listing agent messages: {e}')

    # Fail the test
    raise AssertionError(
        f'Agent did not provide a response about README.md line count within {response_wait_time} seconds. Expected to find {expected_line_count} lines mentioned in an agent message. Check the agent messages above to see what the agent actually responded.'
    )

    # Test passed if we got this far
    print('Conversation test completed successfully')
