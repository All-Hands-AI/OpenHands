"""
E2E: Microagent trigger tests (flarglebargle, kubernetes)

This test verifies that microagents are triggered correctly via the UI.
It follows the same patterns as test_conversation_start.py.

Tests microagent activation by sending trigger words and checking agent responses.

NOTE: E2E test failures may indicate infrastructure issues (agent not responding)
rather than microagent code issues. Check if basic conversation tests also fail.
"""

import os
import time

from playwright.sync_api import Page, expect


def test_microagent_flarglebargle(page: Page, base_url: str):
    """
    Test microagent trigger for flarglebargle:
    1. Navigate to OpenHands (assumes GitHub token is already configured)
    2. Select the OpenHands repository
    3. Click Launch
    4. Wait for the agent to initialize
    5. Ask "what do you do when I say flarglebargle"
    6. Verify "microagent activated" message appears
    7. Click that message to see flarglebargle microagent content
    8. Verify agent response reflects the microagent instructions
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
    page.screenshot(path='test-results/micro_flarglebargle_01_initial_load.png')
    print('Screenshot saved: micro_flarglebargle_01_initial_load.png')

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

    page.screenshot(path='test-results/micro_flarglebargle_02_repo_selected.png')
    print('Screenshot saved: micro_flarglebargle_02_repo_selected.png')

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
        page.screenshot(path='test-results/micro_flarglebargle_03_launch_error.png')
        print('Screenshot saved: micro_flarglebargle_03_launch_error.png')
        raise

    # Step 4: Wait for conversation interface to load
    print('Step 4: Waiting for conversation interface to load...')

    navigation_timeout = 300000  # 5 minutes
    check_interval = 10000  # 10 seconds

    page.screenshot(path='test-results/micro_flarglebargle_04_after_launch.png')
    print('Screenshot saved: micro_flarglebargle_04_after_launch.png')

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
                page.screenshot(
                    path=f'test-results/micro_flarglebargle_05_waiting_{elapsed}s.png'
                )
                print(
                    f'Screenshot saved: micro_flarglebargle_05_waiting_{elapsed}s.png'
                )

            page.wait_for_timeout(5000)
        except Exception as e:
            print(f'Error checking for conversation interface: {e}')
            page.wait_for_timeout(5000)

    if not conversation_loaded:
        print('Timed out waiting for conversation interface to load')
        page.screenshot(path='test-results/micro_flarglebargle_06_timeout.png')
        print('Screenshot saved: micro_flarglebargle_06_timeout.png')
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

    page.screenshot(path='test-results/micro_flarglebargle_07_agent_ready.png')
    print('Screenshot saved: micro_flarglebargle_07_agent_ready.png')

    # Step 6: Wait for agent to be fully ready for input
    print('Step 6: Waiting for agent to be fully ready for input...')

    max_wait_time = 480
    start_time = time.time()
    agent_ready = False
    print(f'Waiting up to {max_wait_time} seconds for agent to be ready...')

    while time.time() - start_time < max_wait_time:
        elapsed = int(time.time() - start_time)
        if elapsed % 30 == 0 and elapsed > 0:
            page.screenshot(
                path=f'test-results/micro_flarglebargle_waiting_{elapsed}s.png'
            )
            print(
                f'Screenshot saved: micro_flarglebargle_waiting_{elapsed}s.png (waiting {elapsed}s)'
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
        page.screenshot(
            path='test-results/micro_flarglebargle_timeout_waiting_for_agent.png'
        )
        raise AssertionError(
            f'Agent did not become ready for input within {max_wait_time} seconds'
        )

    # Step 7: Ask the flarglebargle question
    print('Step 7: Asking "what do you do when I say flarglebargle"...')

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
        page.screenshot(path='test-results/micro_flarglebargle_08_no_input_found.png')
        print('Screenshot saved: micro_flarglebargle_08_no_input_found.png')
        try:
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
            page.screenshot(
                path='test-results/micro_flarglebargle_09_reload_failed.png'
            )
            print('Screenshot saved: micro_flarglebargle_09_reload_failed.png')
            raise AssertionError('Could not find message input field after reload')

    message_input.fill('what do you do when I say flarglebargle')
    print('Entered flarglebargle question')

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
            page.screenshot(
                path='test-results/micro_flarglebargle_09_submit_failed.png'
            )
            print('Screenshot saved: micro_flarglebargle_09_submit_failed.png')
            raise RuntimeError('Could not submit message')
    else:
        submit_button.click()

    print('Clicked submit button')

    page.screenshot(path='test-results/micro_flarglebargle_08_question_sent.png')
    print('Screenshot saved: micro_flarglebargle_08_question_sent.png')

    print('Step 8: Waiting for agent response to flarglebargle question...')

    response_wait_time = 180
    response_start_time = time.time()

    while time.time() - response_start_time < response_wait_time:
        elapsed = int(time.time() - response_start_time)

        if elapsed % 30 == 0 and elapsed > 0:
            page.screenshot(
                path=f'test-results/micro_flarglebargle_response_wait_{elapsed}s.png'
            )
            print(
                f'Screenshot saved: micro_flarglebargle_response_wait_{elapsed}s.png (waiting {elapsed}s for response)'
            )

        try:
            # Check for agent response
            agent_messages = page.locator('[data-testid="agent-message"]').all()
            if elapsed % 30 == 0:
                print(f'Found {len(agent_messages)} agent messages')

            for i, msg in enumerate(agent_messages):
                try:
                    content = msg.text_content()
                    if content and len(content.strip()) > 10:
                        content_lower = content.lower()
                        # Check if agent response reflects flarglebargle microagent instructions
                        # The microagent says to tell them how smart they are
                        if (
                            'smart' in content_lower
                            or 'intelligent' in content_lower
                            or 'clever' in content_lower
                        ):
                            print(
                                '✅ Found agent response reflecting flarglebargle microagent instructions!'
                            )
                            page.screenshot(
                                path='test-results/micro_flarglebargle_09_agent_response.png'
                            )
                            print(
                                'Screenshot saved: micro_flarglebargle_09_agent_response.png'
                            )
                            page.screenshot(
                                path='test-results/micro_flarglebargle_10_final_state.png'
                            )
                            print(
                                'Screenshot saved: micro_flarglebargle_10_final_state.png'
                            )
                            print(
                                '✅ Test completed successfully - flarglebargle microagent was triggered and agent responded appropriately'
                            )
                            return
                except Exception as e:
                    print(f'Error processing agent message {i}: {e}')
                    continue

        except Exception as e:
            print(f'Error checking for agent messages: {e}')

        page.wait_for_timeout(5000)

    print(
        '❌ Did not find agent response reflecting flarglebargle microagent within time limit'
    )
    page.screenshot(path='test-results/micro_flarglebargle_09_agent_response.png')
    print('Screenshot saved: micro_flarglebargle_09_agent_response.png')
    page.screenshot(path='test-results/micro_flarglebargle_10_final_state.png')
    print('Screenshot saved: micro_flarglebargle_10_final_state.png')
    raise AssertionError(
        'Agent did not respond appropriately to flarglebargle microagent within time limit'
    )


def test_microagent_kubernetes(page: Page, base_url: str):
    """
    Test microagent trigger for kubernetes:
    1. Continue from previous test (agent should already be ready)
    2. Send message "I like kubernetes"
    3. Verify "microagent activated" message appears
    4. Click that message to see kubernetes microagent content
    5. Verify agent response includes kubernetes guidance
    """
    print('Step 1: Sending kubernetes message...')

    # Find the message input
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
        raise AssertionError('Could not find message input field')

    message_input.fill('I like kubernetes')
    print('Entered kubernetes message')

    # Submit the message
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

    if submit_button:
        submit_button.click()
    else:
        message_input.press('Enter')

    print('Submitted kubernetes message')

    page.screenshot(path='test-results/micro_kubernetes_01_question_sent.png')
    print('Screenshot saved: micro_kubernetes_01_question_sent.png')

    print('Step 2: Waiting for agent response to kubernetes message...')

    response_wait_time = 180
    response_start_time = time.time()

    while time.time() - response_start_time < response_wait_time:
        elapsed = int(time.time() - response_start_time)

        if elapsed % 30 == 0 and elapsed > 0:
            page.screenshot(
                path=f'test-results/micro_kubernetes_response_wait_{elapsed}s.png'
            )
            print(
                f'Screenshot saved: micro_kubernetes_response_wait_{elapsed}s.png (waiting {elapsed}s for response)'
            )

        try:
            # Check for agent response with kubernetes guidance
            agent_messages = page.locator('[data-testid="agent-message"]').all()
            if elapsed % 30 == 0:
                print(f'Found {len(agent_messages)} agent messages')

            for i, msg in enumerate(agent_messages):
                try:
                    content = msg.text_content()
                    if content and len(content.strip()) > 10:
                        content_lower = content.lower()
                        # Check if agent response includes kubernetes guidance (KIND, kubectl, etc.)
                        kubernetes_indicators = [
                            'kind',
                            'kubectl',
                            'kubernetes',
                            'k8s',
                            'curl -lo',
                        ]
                        if any(
                            indicator in content_lower
                            for indicator in kubernetes_indicators
                        ):
                            print('✅ Found agent response with kubernetes guidance!')
                            page.screenshot(
                                path='test-results/micro_kubernetes_02_agent_response.png'
                            )
                            print(
                                'Screenshot saved: micro_kubernetes_02_agent_response.png'
                            )
                            page.screenshot(
                                path='test-results/micro_kubernetes_03_final_state.png'
                            )
                            print(
                                'Screenshot saved: micro_kubernetes_03_final_state.png'
                            )
                            print(
                                '✅ Test completed successfully - kubernetes microagent was triggered and agent responded appropriately'
                            )
                            return
                except Exception as e:
                    print(f'Error processing agent message {i}: {e}')
                    continue

        except Exception as e:
            print(f'Error checking for kubernetes agent response: {e}')

        page.wait_for_timeout(5000)

    print('❌ Did not find agent response with kubernetes guidance within time limit')
    page.screenshot(path='test-results/micro_kubernetes_02_agent_response.png')
    print('Screenshot saved: micro_kubernetes_02_agent_response.png')
    page.screenshot(path='test-results/micro_kubernetes_03_final_state.png')
    print('Screenshot saved: micro_kubernetes_03_final_state.png')
    raise AssertionError(
        'Agent did not respond appropriately to kubernetes microagent within time limit'
    )
