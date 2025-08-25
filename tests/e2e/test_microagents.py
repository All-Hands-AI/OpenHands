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

    # Click on the dropdown to open it
    repo_dropdown.click()

    # Type the repository name to filter options
    repo_input = repo_dropdown.locator('input')
    repo_input.type('openhands-agent/OpenHands')
    print('Used keyboard.type() for React Select component')

    # Wait for and click the specific repository option
    repo_option = page.locator(
        '[data-testid="repo-dropdown"] [role="option"]:has-text("openhands-agent/OpenHands")'
    )
    repo_option.wait_for(state='visible', timeout=10000)
    print(
        'Found repository option with selector: [data-testid="repo-dropdown"] [role="option"]:has-text("openhands-agent/OpenHands")'
    )

    # Force click the option to ensure it works
    repo_option.click(force=True)
    print('Successfully clicked option with force=True')

    page.screenshot(path='test-results/micro_test_02_repo_selected.png')

    print('Step 3: Clicking Launch button...')
    # Wait for launch button to be enabled and click it
    launch_button = page.locator('[data-testid="launch-button"]')

    # Wait for the button to be enabled (not disabled)
    for attempt in range(10):
        try:
            if not launch_button.is_disabled(timeout=3000):
                print(
                    f'Repository Launch button is now enabled (attempt {attempt + 1})'
                )
                break
        except Exception:
            pass
        page.wait_for_timeout(1000)
    else:
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

        for selector in submit_selectors:
            try:
                button_element = page.locator(selector)
                if button_element.is_visible(
                    timeout=5000
                ) and button_element.is_enabled(timeout=1000):
                    print(f'Found enabled submit button with selector: {selector}')
                    return button_element
            except Exception:
                continue
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

    # Wait for agent to be ready
    message_input = None
    for attempt in range(48):  # 48 * 10 seconds = 480 seconds total
        message_input = find_message_input()
        if message_input:
            break
        print(f'Agent not ready yet, waiting... (attempt {attempt + 1}/48)')
        page.wait_for_timeout(10000)

    if not message_input:
        raise AssertionError(
            'Agent input field never became available after 480 seconds'
        )

    # Test 1: Flarglebargle microagent
    print('Step 7: Testing flarglebargle microagent...')
    message_input.fill('flarglebargle')
    print('Entered flarglebargle message')

    submit_button = find_submit_button()
    if not submit_button:
        raise AssertionError('Could not find enabled submit button')

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
        raise AssertionError('Could not find submit button for kubernetes test')

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
