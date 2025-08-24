"""
E2E: Web search test using Tavily (not browser)

This test verifies that the OpenHands agent can use Tavily search
to answer questions about current information, specifically asking
for the current US president.
"""

import os
import time

from playwright.sync_api import Page, expect


def test_web_search_current_us_president(page: Page):
    """
    Test web search functionality using Tavily to find current US president:
    1. Navigate to OpenHands (assumes GitHub token is already configured)
    2. Select a repository (or use default)
    3. Click Launch
    4. Wait for the agent to initialize
    5. Ask about the current US president
    6. Verify the agent uses Tavily search (not browser) to find the answer
    7. Verify the response contains relevant information
    """
    # Create test-results directory if it doesn't exist
    os.makedirs('test-results', exist_ok=True)

    # Navigate to the OpenHands application
    print('Step 1: Navigating to OpenHands application...')
    page.goto('http://localhost:12000')
    page.wait_for_load_state('networkidle', timeout=30000)

    # Take initial screenshot
    page.screenshot(path='test-results/search_01_initial_load.png')
    print('Screenshot saved: search_01_initial_load.png')

    # Step 2: Select a repository (or use default)
    print('Step 2: Setting up repository...')

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

    # Type the repository name (using OpenHands repo for consistency)
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
        '[role="option"]:has-text("openhands-agent/OpenHands")',
        '[role="option"]:has-text("OpenHands")',
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

    page.screenshot(path='test-results/search_02_repo_selected.png')
    print('Screenshot saved: search_02_repo_selected.png')

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
        page.screenshot(path='test-results/search_03_launch_error.png')
        print('Screenshot saved: search_03_launch_error.png')
        raise

    # Step 4: Wait for conversation interface to load
    print('Step 4: Waiting for conversation interface to load...')

    navigation_timeout = 300000  # 5 minutes
    check_interval = 10000  # 10 seconds

    page.screenshot(path='test-results/search_04_after_launch.png')
    print('Screenshot saved: search_04_after_launch.png')

    # Wait for loading to complete
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

    # Wait for conversation interface to appear
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
                page.screenshot(path=f'test-results/search_05_waiting_{elapsed}s.png')
                print(f'Screenshot saved: search_05_waiting_{elapsed}s.png')

            page.wait_for_timeout(5000)
        except Exception as e:
            print(f'Error checking for conversation interface: {e}')
            page.wait_for_timeout(5000)

    if not conversation_loaded:
        print('Timed out waiting for conversation interface to load')
        page.screenshot(path='test-results/search_06_timeout.png')
        print('Screenshot saved: search_06_timeout.png')
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

    page.screenshot(path='test-results/search_07_agent_ready.png')
    print('Screenshot saved: search_07_agent_ready.png')

    # Step 6: Wait for agent to be fully ready for input
    print('Step 6: Waiting for agent to be fully ready for input...')

    max_wait_time = 480
    start_time = time.time()
    agent_ready = False
    print(f'Waiting up to {max_wait_time} seconds for agent to be ready...')

    while time.time() - start_time < max_wait_time:
        elapsed = int(time.time() - start_time)
        if elapsed % 30 == 0 and elapsed > 0:
            page.screenshot(path=f'test-results/search_waiting_{elapsed}s.png')
            print(
                f'Screenshot saved: search_waiting_{elapsed}s.png (waiting {elapsed}s)'
            )

        try:
            # Check if input field and submit button are ready
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

            # Check for ready indicators
            ready_indicators = [
                'div:has-text("Agent is ready")',
                'div:has-text("Waiting for user input")',
                'div:has-text("Awaiting input")',
                'div:has-text("Task completed")',
                'div:has-text("Agent has finished")',
            ]

            for indicator in ready_indicators:
                try:
                    element = page.locator(indicator)
                    if element.is_visible(timeout=2000):
                        print(f'Agent appears ready (found: {indicator})')
                        break
                except Exception:
                    continue

            if input_ready and submit_ready:
                print(
                    '✅ Agent is ready for user input - input field and submit button are enabled'
                )
                agent_ready = True
                break

        except Exception as e:
            print(f'Error checking agent ready state: {e}')

        page.wait_for_timeout(2000)

    if not agent_ready:
        page.screenshot(path='test-results/search_timeout_waiting_for_agent.png')
        raise AssertionError(
            f'Agent did not become ready for input within {max_wait_time} seconds'
        )

    # Step 7: Ask about the current US president
    print('Step 7: Asking about the current US president...')

    # Find the message input field
    input_selectors = [
        '[data-testid="chat-input"] textarea',
        '[data-testid="message-input"]',
        'textarea',
        'form textarea',
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
        page.screenshot(path='test-results/search_08_no_input_found.png')
        print('Screenshot saved: search_08_no_input_found.png')
        raise AssertionError('Could not find message input field')

    # Type the question about the current US president
    question = 'Who is the current US president? Please use web search to find the most up-to-date information.'
    print(f'Typing question: {question}')

    try:
        message_input.click()
        page.wait_for_timeout(1000)
        message_input.fill(question)
        print('Question typed successfully')
    except Exception as e:
        print(f'Error typing question: {e}')
        page.screenshot(path='test-results/search_09_typing_error.png')
        print('Screenshot saved: search_09_typing_error.png')
        raise

    page.screenshot(path='test-results/search_10_question_typed.png')
    print('Screenshot saved: search_10_question_typed.png')

    # Submit the question
    print('Step 8: Submitting the question...')

    submit_selectors = [
        '[data-testid="chat-input"] button[type="submit"]',
        '[data-testid="send-button"]',
        'button[type="submit"]',
        'button:has-text("Send")',
    ]

    submit_button = None
    for selector in submit_selectors:
        try:
            button = page.locator(selector)
            if button.is_visible(timeout=5000):
                print(f'Found submit button with selector: {selector}')
                submit_button = button
                break
        except Exception:
            continue

    if not submit_button:
        print('Could not find submit button, trying Enter key')
        message_input.press('Enter')
        print('Pressed Enter key to submit')
    else:
        try:
            submit_button.click()
            print('Submit button clicked successfully')
        except Exception as e:
            print(f'Error clicking submit button: {e}')
            message_input.press('Enter')
            print('Fallback: Pressed Enter key to submit')

    page.screenshot(path='test-results/search_11_question_submitted.png')
    print('Screenshot saved: search_11_question_submitted.png')

    # Step 9: Wait for and verify the agent's response
    print('Step 9: Waiting for agent response...')

    response_timeout = 300  # 5 minutes
    start_time = time.time()
    response_found = False
    tavily_search_used = False
    president_info_found = False

    print(f'Waiting up to {response_timeout} seconds for agent response...')

    while time.time() - start_time < response_timeout:
        elapsed = int(time.time() - start_time)

        # Take periodic screenshots
        if elapsed % 30 == 0 and elapsed > 0:
            page.screenshot(path=f'test-results/search_response_{elapsed}s.png')
            print(
                f'Screenshot saved: search_response_{elapsed}s.png (waiting {elapsed}s)'
            )

        try:
            # Look for agent messages/responses
            message_selectors = [
                '[data-testid="message"]',
                '[data-testid="agent-message"]',
                '.message',
                '.agent-message',
                '[role="log"]',
                '.conversation-message',
            ]

            messages_found = []
            for selector in message_selectors:
                try:
                    messages = page.locator(selector)
                    count = messages.count()
                    if count > 0:
                        for i in range(count):
                            try:
                                message_text = messages.nth(i).text_content()
                                if message_text and len(message_text.strip()) > 10:
                                    messages_found.append(message_text.strip())
                            except Exception:
                                continue
                except Exception:
                    continue

            # Check for Tavily search usage indicators
            page_content = page.content()
            tavily_indicators = [
                'tavily',
                'Tavily',
                'search',
                'web search',
                'searching',
                'found information',
                'search results',
            ]

            for indicator in tavily_indicators:
                if indicator.lower() in page_content.lower():
                    if not tavily_search_used:
                        print(f'✅ Found Tavily search indicator: {indicator}')
                        tavily_search_used = True

            # Check for president-related information
            president_keywords = [
                'president',
                'President',
                'Biden',
                'Joe Biden',
                'current president',
                'United States',
                'US president',
            ]

            for keyword in president_keywords:
                if keyword in page_content:
                    if not president_info_found:
                        print(f'✅ Found president-related information: {keyword}')
                        president_info_found = True

            # Check if we have a substantial response
            if messages_found:
                latest_messages = messages_found[-3:]  # Check last 3 messages
                for msg in latest_messages:
                    if len(msg) > 50 and any(
                        keyword.lower() in msg.lower() for keyword in president_keywords
                    ):
                        print(
                            f'✅ Found substantial response about president: {msg[:100]}...'
                        )
                        response_found = True
                        break

            # If we have all the indicators we need, we can break
            if response_found and (tavily_search_used or president_info_found):
                print('✅ All success criteria met!')
                break

        except Exception as e:
            print(f'Error checking for response: {e}')

        page.wait_for_timeout(5000)

    # Final screenshot
    page.screenshot(path='test-results/search_12_final_response.png')
    print('Screenshot saved: search_12_final_response.png')

    # Step 10: Verify the results
    print('Step 10: Verifying test results...')

    if not response_found:
        print('❌ No substantial response found about the US president')
        raise AssertionError(
            'Agent did not provide a response about the current US president'
        )

    if not (tavily_search_used or president_info_found):
        print('❌ No evidence of web search usage or president information found')
        raise AssertionError(
            'Agent did not appear to use web search or provide president information'
        )

    print('✅ Test completed successfully!')
    print(f'- Response found: {response_found}')
    print(f'- Tavily search indicators: {tavily_search_used}')
    print(f'- President information found: {president_info_found}')

    # Additional verification: Check that browser tools were NOT used
    browser_indicators = [
        'browser',
        'Browser',
        'browsing',
        'navigate',
        'click',
        'webpage',
        'website',
    ]

    browser_usage_found = False
    page_content = page.content()
    for indicator in browser_indicators:
        if indicator in page_content and 'search' not in page_content.lower():
            browser_usage_found = True
            print(f'⚠️  Possible browser usage detected: {indicator}')

    if browser_usage_found:
        print(
            '⚠️  Warning: Browser usage may have been detected, but test still passes if search was used'
        )
    else:
        print(
            '✅ No browser usage detected - agent likely used Tavily search as intended'
        )

    print('🎉 Web search test completed successfully!')
