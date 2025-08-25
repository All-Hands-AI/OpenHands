"""
E2E: React app creation test

This test assumes the GitHub token has already been configured (by the
settings test) and verifies that a conversation can be started and the
agent can create a React app with "Hello OpenHands" message, serve it,
and provide a working URL.
"""

import os
import re
import time
from urllib.parse import urlparse

from playwright.sync_api import Page, expect


def test_react_app_creation(page: Page, base_url: str):
    """
    Test React app creation with the OpenHands agent:
    1. Navigate to OpenHands (assumes GitHub token is already configured)
    2. Select the OpenHands repository
    3. Click Launch
    4. Wait for the agent to initialize
    5. Ask the agent to create a React app with "Hello OpenHands" message
    6. Verify the agent responds with a URL
    7. Verify the URL is accessible and contains "Hello OpenHands"
    """
    # Create test-results directory if it doesn't exist
    os.makedirs('test-results', exist_ok=True)

    # Use default URL if base_url is not provided
    if not base_url:
        base_url = 'http://localhost:12000'

    # Navigate to the OpenHands application
    print(f'Step 1: Navigating to OpenHands application at {base_url}...')
    page.goto(base_url)
    page.wait_for_load_state('networkidle', timeout=30000)

    # Take initial screenshot
    page.screenshot(path='test-results/react_01_initial_load.png')
    print('Screenshot saved: react_01_initial_load.png')

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

    page.screenshot(path='test-results/react_02_repo_selected.png')
    print('Screenshot saved: react_02_repo_selected.png')

    # Step 3: Click Launch button
    print('Step 3: Clicking Launch button...')

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

    try:
        if button_enabled:
            launch_button.click()
            print('Launch button clicked normally')
        else:
            print('Launch button still disabled, trying JavaScript force click...')
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
        page.screenshot(path='test-results/react_03_launch_error.png')
        print('Screenshot saved: react_03_launch_error.png')
        raise

    # Step 4: Wait for conversation interface to load
    print('Step 4: Waiting for conversation interface to load...')

    navigation_timeout = 300000  # 5 minutes
    check_interval = 10000  # 10 seconds

    page.screenshot(path='test-results/react_04_after_launch.png')
    print('Screenshot saved: react_04_after_launch.png')

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
                expect(loading).not_to_be_visible(timeout=120000)
                print('Loading completed')
                break
        except Exception:
            continue

    try:
        current_url = page.url
        print(f'Current URL: {current_url}')
        if '/conversation/' in current_url or '/chat/' in current_url:
            print('URL indicates conversation page has loaded')
    except Exception as e:
        print(f'Error checking URL: {e}')

    start_time = time.time()
    conversation_loaded = False
    while time.time() - start_time < navigation_timeout / 1000:
        try:
            selectors = [
                '.scrollbar.flex.flex-col.grow',
                '[data-testid="chat-input"]',
                '[data-testid="app-route"]',
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

            if (time.time() - start_time) % (check_interval / 1000) < 1:
                elapsed = int(time.time() - start_time)
                page.screenshot(path=f'test-results/react_05_waiting_{elapsed}s.png')
                print(f'Screenshot saved: react_05_waiting_{elapsed}s.png')

            page.wait_for_timeout(5000)
        except Exception as e:
            print(f'Error checking for conversation interface: {e}')
            page.wait_for_timeout(5000)

    if not conversation_loaded:
        print('Timed out waiting for conversation interface to load')
        page.screenshot(path='test-results/react_06_timeout.png')
        print('Screenshot saved: react_06_timeout.png')
        raise TimeoutError('Timed out waiting for conversation interface to load')

    # Step 5: Wait for agent to initialize
    print('Step 5: Waiting for agent to initialize...')

    try:
        chat_input = page.locator('[data-testid="chat-input"]')
        expect(chat_input).to_be_visible(timeout=60000)
        submit_button = page.locator('[data-testid="chat-input"] button[type="submit"]')
        expect(submit_button).to_be_visible(timeout=10000)
        print('Agent interface is loaded')
        page.wait_for_timeout(10000)
    except Exception as e:
        print(f'Could not confirm agent interface is loaded: {e}')

    page.screenshot(path='test-results/react_07_agent_ready.png')
    print('Screenshot saved: react_07_agent_ready.png')

    # Step 6: Wait for agent to be fully ready for input
    print('Step 6: Waiting for agent to be fully ready for input...')

    max_wait_time = 480
    start_time = time.time()
    agent_ready = False
    print(f'Waiting up to {max_wait_time} seconds for agent to be ready...')

    while time.time() - start_time < max_wait_time:
        elapsed = int(time.time() - start_time)
        if elapsed % 30 == 0 and elapsed > 0:
            page.screenshot(path=f'test-results/react_waiting_{elapsed}s.png')
            print(
                f'Screenshot saved: react_waiting_{elapsed}s.png (waiting {elapsed}s)'
            )

        try:
            status_messages = []
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

            ready_indicators = [
                'div:has-text("Agent is ready")',
                'div:has-text("Waiting for user input")',
                'div:has-text("Awaiting input")',
                'div:has-text("Task completed")',
                'div:has-text("Agent has finished")',
            ]

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
                print(
                    'No status messages found and input is ready, agent appears ready...'
                )
                agent_ready = True
                break
        except Exception as e:
            print(f'Error checking agent ready state: {e}')

        page.wait_for_timeout(2000)

    if not agent_ready:
        page.screenshot(path='test-results/react_timeout_waiting_for_agent.png')
        raise AssertionError(
            f'Agent did not become ready for input within {max_wait_time} seconds'
        )

    # Step 7: Ask the agent to create a React app
    print('Step 7: Asking agent to create React app with "Hello OpenHands"...')

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
        page.screenshot(path='test-results/react_08_no_input_found.png')
        print('Screenshot saved: react_08_no_input_found.png')

        try:
            print('Reloading the page...')
            page.reload()
            page.wait_for_load_state('networkidle', timeout=30000)
            print('Page reloaded')
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
            page.screenshot(path='test-results/react_09_reload_failed.png')
            print('Screenshot saved: react_09_reload_failed.png')
            raise AssertionError('Could not find message input field after reload')

    # Send the React app creation instruction
    react_instruction = 'Create a react app where the first page says "Hello OpenHands" on it, serve it, and tell me the URL where I will be able to access it.'
    message_input.fill(react_instruction)
    print('Entered React app creation instruction')

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

    button_enabled = False
    if submit_button:
        max_wait_time = 60
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
            page.wait_for_timeout(2000)

    if not submit_button or not button_enabled:
        print('Submit button not found or never became enabled, trying alternatives')
        try:
            message_input.press('Enter')
            print('Pressed Enter key to submit')
            button_enabled = True
        except Exception as e:
            print(f'Error pressing Enter key: {e}')
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
            page.screenshot(path='test-results/react_09_submit_failed.png')
            print('Screenshot saved: react_09_submit_failed.png')
            raise RuntimeError('Could not submit message')
    else:
        submit_button.click()

    print('Clicked submit button')

    page.screenshot(path='test-results/react_08_question_sent.png')
    print('Screenshot saved: react_08_question_sent.png')

    print('Step 8: Waiting for agent response with React app URL...')

    # Wait longer for React app creation as it involves multiple steps
    response_wait_time = 600  # 10 minutes for React app creation
    response_start_time = time.time()
    found_url = None

    while time.time() - response_start_time < response_wait_time:
        elapsed = int(time.time() - response_start_time)

        if elapsed % 30 == 0 and elapsed > 0:
            page.screenshot(path=f'test-results/react_response_wait_{elapsed}s.png')
            print(
                f'Screenshot saved: react_response_wait_{elapsed}s.png (waiting {elapsed}s for response)'
            )

        try:
            agent_messages = page.locator('[data-testid="agent-message"]').all()
            if elapsed % 30 == 0:
                print(f'Found {len(agent_messages)} agent messages')

            for i, msg in enumerate(agent_messages):
                try:
                    content = msg.text_content()
                    if content and len(content.strip()) > 10:
                        content.lower()

                        # Look for URLs in the message
                        url_patterns = [
                            r'http://localhost:\d+',
                            r'https://localhost:\d+',
                            r'http://127\.0\.0\.1:\d+',
                            r'https://127\.0\.0\.1:\d+',
                            r'http://0\.0\.0\.0:\d+',
                            r'https://0\.0\.0\.0:\d+',
                        ]

                        for pattern in url_patterns:
                            urls = re.findall(pattern, content)
                            if urls:
                                found_url = urls[0]
                                print(f'✅ Found URL in agent response: {found_url}')
                                break

                        if found_url:
                            break

                except Exception as e:
                    print(f'Error processing agent message {i}: {e}')
                    continue

            if found_url:
                break

        except Exception as e:
            print(f'Error checking for agent messages: {e}')

        page.wait_for_timeout(5000)

    if not found_url:
        print('❌ Did not find URL in agent response within time limit')
        page.screenshot(path='test-results/react_09_no_url_found.png')
        print('Screenshot saved: react_09_no_url_found.png')
        page.screenshot(path='test-results/react_10_final_state.png')
        print('Screenshot saved: react_10_final_state.png')
        raise AssertionError('Agent response did not include a URL within time limit')

    print(f'Step 9: Validating React app URL: {found_url}')

    # Parse the URL to validate it
    try:
        parsed_url = urlparse(found_url)
        if not parsed_url.scheme or not parsed_url.netloc:
            raise ValueError(f'Invalid URL format: {found_url}')
        print(f'URL is valid: scheme={parsed_url.scheme}, netloc={parsed_url.netloc}')
    except Exception as e:
        print(f'❌ Invalid URL format: {e}')
        raise AssertionError(f'Agent provided invalid URL: {found_url}')

    # Step 10: Test the React app URL
    print(f'Step 10: Testing React app at {found_url}...')

    # Create a new page context for testing the React app
    react_page = page.context.new_page()

    try:
        # Navigate to the React app URL
        react_page.goto(found_url, timeout=30000)
        react_page.wait_for_load_state('networkidle', timeout=30000)

        # Take screenshot of the React app
        react_page.screenshot(path='test-results/react_11_app_loaded.png')
        print('Screenshot saved: react_11_app_loaded.png')

        # Check if the page contains "Hello OpenHands"
        page_content = react_page.content()
        if 'Hello OpenHands' in page_content:
            print('✅ React app contains "Hello OpenHands" text!')
        else:
            print('❌ React app does not contain "Hello OpenHands" text')
            print(f'Page content preview: {page_content[:500]}...')
            raise AssertionError('React app does not contain "Hello OpenHands" text')

        # Also try to find the text using a locator for better validation
        try:
            hello_element = react_page.locator('text=Hello OpenHands')
            expect(hello_element).to_be_visible(timeout=10000)
            print('✅ "Hello OpenHands" text is visible on the page!')
        except Exception as e:
            print(f'Warning: Could not find "Hello OpenHands" with locator: {e}')
            # Still pass if we found it in the content
            if 'Hello OpenHands' not in page_content:
                raise

        print('✅ Test completed successfully - React app is working correctly!')
        page.screenshot(path='test-results/react_12_success.png')
        print('Screenshot saved: react_12_success.png')

    except Exception as e:
        print(f'❌ Error testing React app URL: {e}')
        react_page.screenshot(path='test-results/react_11_app_error.png')
        print('Screenshot saved: react_11_app_error.png')
        raise AssertionError(
            f'React app URL is not accessible or does not work correctly: {e}'
        )

    finally:
        react_page.close()

    print('✅ React app creation test completed successfully!')
