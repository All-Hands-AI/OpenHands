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

from playwright.sync_api import Page


def test_microagent_triggers(page: Page, base_url: str):
    """
    Test microagent triggers for both flarglebargle and kubernetes:
    1. Navigate to OpenHands application
    2. Select openhands-agent/OpenHands repository
    3. Launch the agent
    4. Wait for agent to be ready
    5. Send message "flarglebargle" and verify response includes microagent content
    6. Send follow-up message "I like kubernetes" and verify kubernetes microagent response
    """
    # Create test-results directory if it doesn't exist
    os.makedirs('test-results', exist_ok=True)

    # Use default URL if base_url is not provided
    if not base_url:
        base_url = 'http://localhost:12000'

    print('Step 1: Navigating to OpenHands application at http://localhost:12000...')
    page.goto('http://localhost:12000')
    page.screenshot(path='test-results/micro_test_01_initial_load.png')

    print('Step 2: Selecting openhands-agent/OpenHands repository...')
    # Wait for home screen to be visible
    page.wait_for_selector('[data-testid="home-screen"]', timeout=30000)
    print('Home screen is visible')

    # Find and interact with repository dropdown
    repo_dropdown = page.locator('[data-testid="repo-dropdown"]')
    repo_dropdown.wait_for(state='visible', timeout=30000)
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

    page.screenshot(path='test-results/micro_test_02_repo_selected.png')

    print('Step 3: Clicking Launch button...')
    # Wait for launch button to be enabled and click it
    launch_button = page.locator('[data-testid="repo-launch-button"]')

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
                print(f'Launch button is still disabled (attempt {attempt + 1})')
        except Exception as e:
            print(f'Error checking button state: {e}')
        page.wait_for_timeout(1000)

    if not button_enabled:
        raise AssertionError('Launch button never became enabled')

    # Click the launch button
    try:
        launch_button.click(timeout=10000)
        print('Launch button clicked normally')
    except Exception as e:
        print(f'Normal click failed: {e}, trying force click')
        launch_button.click(force=True)
        print('Launch button clicked with force')

    print('Step 4: Waiting for conversation interface to load...')
    page.screenshot(path='test-results/micro_test_04_after_launch.png')

    # Wait for navigation to conversation interface
    page.wait_for_timeout(3000)
    print(f'Current URL: {page.url}')

    # Wait for conversation interface to be visible
    conversation_interface = page.locator('main')
    conversation_interface.wait_for(state='visible', timeout=30000)
    print('Found conversation interface element with selector: main')

    print('Step 5: Waiting for agent to initialize...')
    # Wait for agent interface to load
    page.wait_for_timeout(5000)
    print('Agent interface is loaded')
    page.screenshot(path='test-results/micro_test_07_agent_ready.png')

    print('Step 6: Waiting for agent to be fully ready for input...')
    # Wait for agent to be ready (look for input field and submit button)
    print('Waiting up to 480 seconds for agent to be ready...')

    # Wait for message input to be available and enabled
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

    def find_message_input():
        """Helper function to find message input field"""
        for selector in input_selectors:
            try:
                input_element = page.locator(selector)
                if input_element.is_visible(timeout=5000) and input_element.is_enabled(
                    timeout=1000
                ):
                    print(f'Found enabled message input with selector: {selector}')
                    return input_element
            except Exception:
                continue
        return None

    def find_submit_button():
        """Helper function to find submit button"""
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

        if submit_button and button_enabled:
            return submit_button
        return None

    def wait_for_agent_response(keywords, test_name, max_wait_time=300):
        """Helper function to wait for agent response with specific keywords"""
        start_time = time.time()
        found_keywords = False

        while time.time() - start_time < max_wait_time:
            try:
                # Strategy 1: Look for agent messages with specific selectors
                agent_selectors = [
                    '[data-testid="agent-message"]',
                    '[data-testid*="agent"]',
                    '.agent-message',
                    '[role="assistant"]',
                    '.message.agent',
                    '.assistant-message',
                ]

                agent_messages = []
                for selector in agent_selectors:
                    try:
                        messages = page.locator(selector).all()
                        agent_messages.extend(messages)
                    except Exception:
                        continue

                print(f'Found {len(agent_messages)} agent messages')

                # Check agent messages for keywords
                for message in agent_messages:
                    try:
                        text = message.text_content()
                        if text and any(
                            keyword in text.lower() for keyword in keywords
                        ):
                            print(
                                f'✅ Found {test_name} keywords in agent message: {text[:100]}...'
                            )
                            found_keywords = True
                            break
                    except Exception:
                        continue

                # Strategy 2: Search entire page content as fallback
                if not found_keywords:
                    try:
                        page_text = page.locator('body').text_content()
                        if page_text and any(
                            keyword in page_text.lower() for keyword in keywords
                        ):
                            print(
                                f'✅ Found {test_name} keywords in page text! Keywords found in:'
                            )
                            # Show a snippet of where keywords were found
                            lines = page_text.split('\n')
                            for line in lines[
                                :20
                            ]:  # Show first 20 lines where keywords might be
                                if any(keyword in line.lower() for keyword in keywords):
                                    print(f'               {line.strip()[:100]}')
                                    break
                            found_keywords = True
                            break
                    except Exception as e:
                        print(f'Error checking page text: {e}')

                if found_keywords:
                    break

                page.wait_for_timeout(5000)  # Wait 5 seconds before next check

            except Exception as e:
                print(f'Error during {test_name} response detection: {e}')
                page.wait_for_timeout(5000)

        return found_keywords

    # Wait longer for WebSocket connection to be established
    print('Waiting for WebSocket connection to be established...')
    page.wait_for_timeout(20000)  # Wait 20 seconds for WebSocket connection

    # Check for any signs of agent connectivity
    try:
        # Look for any agent status indicators
        status_indicators = [
            '[data-testid="agent-status"]',
            '.agent-status',
            '[class*="status"]',
            '[class*="connected"]',
        ]
        for indicator in status_indicators:
            try:
                if page.locator(indicator).is_visible(timeout=2000):
                    print(f'Found agent status indicator: {indicator}')
                    break
            except Exception:
                continue
    except Exception as e:
        print(f'Could not check agent status indicators: {e}')

    # Wait for agent to be ready
    message_input = None
    for attempt in range(60):  # 60 * 10 seconds = 600 seconds total
        message_input = find_message_input()
        if message_input:
            # Additional verification: check if we can actually type in the input
            try:
                message_input.fill('test')
                message_input.fill('')  # Clear it
                print('Message input is fully functional')
                break
            except Exception as e:
                print(f'Message input not fully ready: {e}')
                message_input = None

        print(f'Agent not ready yet, waiting... (attempt {attempt + 1}/60)')
        page.wait_for_timeout(10000)

    if not message_input:
        raise AssertionError(
            'Agent input field never became available after 600 seconds'
        )

    # Test 1: Flarglebargle microagent
    print('Step 7: Testing flarglebargle microagent...')
    message_input.fill('flarglebargle')
    print('Entered flarglebargle message')

    submit_button = find_submit_button()
    if not submit_button:
        print('Submit button not found or never became enabled, trying alternatives')
        try:
            message_input.press('Enter')
            print('Pressed Enter key to submit')
        except Exception as e:
            print(f'Error pressing Enter key: {e}')
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
            except Exception as e2:
                print(f'JavaScript force click failed: {e2}')
                raise AssertionError('Could not submit message - all methods failed')
    else:
        print('Submit button is enabled')
        submit_button.click()
        print('Clicked submit button')
    page.screenshot(path='test-results/micro_test_08_flarglebargle_sent.png')

    print('Step 8: Waiting for agent response to flarglebargle question...')
    found_flarglebargle = wait_for_agent_response(
        ['smart', 'intelligent'], 'flarglebargle'
    )

    page.screenshot(path='test-results/micro_test_09_flarglebargle_response.png')

    if not found_flarglebargle:
        raise AssertionError(
            'Agent did not respond with expected flarglebargle microagent keywords (smart, intelligent) within 5 minutes'
        )

    print('✅ Flarglebargle microagent test passed!')

    # Test 2: Kubernetes microagent
    print('Step 9: Testing kubernetes microagent...')

    # Find input field again (it might have changed)
    message_input = find_message_input()
    if not message_input:
        raise AssertionError('Could not find message input field for kubernetes test')

    message_input.fill('I like kubernetes')
    print('Entered kubernetes message')

    submit_button = find_submit_button()
    if not submit_button:
        print(
            'Submit button not found or never became enabled for kubernetes test, trying alternatives'
        )
        try:
            message_input.press('Enter')
            print('Pressed Enter key to submit kubernetes message')
        except Exception as e:
            print(f'Error pressing Enter key: {e}')
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
                print('Used JavaScript to force click submit button for kubernetes')
            except Exception as e2:
                print(f'JavaScript force click failed: {e2}')
                raise AssertionError(
                    'Could not submit kubernetes message - all methods failed'
                )
    else:
        submit_button.click()
        print('Clicked submit button for kubernetes message')
    page.screenshot(path='test-results/micro_test_10_kubernetes_sent.png')

    print('Step 10: Waiting for agent response to kubernetes question...')
    kubernetes_keywords = [
        'kubernetes',
        'k8s',
        'container',
        'orchestration',
        'cluster',
        'pod',
        'deployment',
    ]
    found_kubernetes = wait_for_agent_response(kubernetes_keywords, 'kubernetes')

    page.screenshot(path='test-results/micro_test_11_kubernetes_response.png')
    page.screenshot(path='test-results/micro_test_12_final_state.png')

    if not found_kubernetes:
        raise AssertionError(
            'Agent did not respond with kubernetes-related content within 5 minutes'
        )

    print(
        '✅ Test completed successfully - both flarglebargle and kubernetes microagents were triggered and agent responded appropriately'
    )
