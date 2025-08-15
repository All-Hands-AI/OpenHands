"""
E2E: Web search test using Tavily (strict validation)

This test verifies that the agent uses Tavily search (not browser tools) 
to answer questions requiring web search. It includes strict validation
to ensure proper tool usage and will fail if browser tools are detected.
"""

import os
import time

from playwright.sync_api import Page, expect


def test_web_search_current_us_president(page: Page):
    """
    Test web search functionality using Tavily (not browser) to find current US president:
    1. Navigate to OpenHands (assumes GitHub token is already configured)
    2. Select the OpenHands repository
    3. Click Launch
    4. Wait for the agent to initialize
    5. Ask question requiring web search
    6. Verify agent uses Tavily search (not browser tools) - STRICT VALIDATION
    7. Verify response contains relevant president information
    """
    # Create test-results directory if it doesn't exist
    os.makedirs('test-results', exist_ok=True)

    # Navigate to the OpenHands application
    print('Step 1: Navigating to OpenHands application...')
    page.goto('http://localhost:3000')
    page.wait_for_load_state('networkidle', timeout=30000)
    page.screenshot(path='test-results/search_01_initial_load.png')
    print('Screenshot saved: search_01_initial_load.png')

    # Step 2: Select repository
    print('Step 2: Selecting repository...')
    
    # Wait for and click the repository dropdown
    repo_dropdown = page.locator('[data-testid="repo-selector"]')
    expect(repo_dropdown).to_be_visible(timeout=30000)
    repo_dropdown.click()
    page.wait_for_timeout(2000)

    # Look for OpenHands repository option
    option_found = False
    selectors = [
        'div[role="option"]:has-text("OpenHands")',
        'div[role="option"]:has-text("openhands")',
        'li:has-text("OpenHands")',
        'li:has-text("openhands")',
        '[data-testid*="repo"]:has-text("OpenHands")',
        '[data-testid*="repo"]:has-text("openhands")',
    ]

    for selector in selectors:
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
        print('Could not find repository option in dropdown, trying keyboard navigation')
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

    # Wait for the button to be enabled
    max_wait_attempts = 30
    button_enabled = False
    for attempt in range(max_wait_attempts):
        try:
            is_disabled = launch_button.is_disabled()
            if not is_disabled:
                print(f'Repository Launch button is now enabled (attempt {attempt + 1})')
                button_enabled = True
                break
            else:
                print(f'Launch button still disabled, waiting... (attempt {attempt + 1}/{max_wait_attempts})')
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
    start_time = time.time()
    conversation_loaded = False

    while time.time() - start_time < navigation_timeout / 1000:
        try:
            # Check if conversation interface is loaded
            chat_input = page.locator('[data-testid="chat-input"]')
            if chat_input.is_visible(timeout=5000):
                print('Conversation interface loaded successfully')
                conversation_loaded = True
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
            print(f'Screenshot saved: search_waiting_{elapsed}s.png (waiting {elapsed}s)')

        try:
            # Check if input field and submit button are ready
            input_field = page.locator('[data-testid="chat-input"] textarea')
            submit_button = page.locator('[data-testid="chat-input"] button[type="submit"]')
            
            if (input_field.is_visible(timeout=2000) and input_field.is_enabled(timeout=2000) and
                submit_button.is_visible(timeout=2000) and submit_button.is_enabled(timeout=2000)):
                print('✅ Agent is ready for user input - input field and submit button are enabled')
                agent_ready = True
                break
        except Exception as e:
            print(f'Error checking agent ready state: {e}')

        page.wait_for_timeout(2000)

    if not agent_ready:
        page.screenshot(path='test-results/search_timeout_waiting_for_agent.png')
        raise AssertionError(f'Agent did not become ready for input within {max_wait_time} seconds')

    # Step 7: Ask question requiring web search
    print('Step 7: Asking question requiring web search...')
    
    input_field = page.locator('[data-testid="chat-input"] textarea')
    question = "Who is the current US president? Please use web search to find the most up-to-date information."
    
    input_field.fill(question)
    print(f'Entered question: {question}')

    page.screenshot(path='test-results/search_10_question_typed.png')
    print('Screenshot saved: search_10_question_typed.png')

    # Submit the question
    submit_button = page.locator('[data-testid="chat-input"] button[type="submit"]')
    submit_button.click()
    print('Clicked submit button')

    page.screenshot(path='test-results/search_11_question_submitted.png')
    print('Screenshot saved: search_11_question_submitted.png')

    # Step 8: Wait for agent response and verify Tavily usage (STRICT VALIDATION)
    print('Step 8: Waiting for agent response and verifying Tavily usage (STRICT VALIDATION)...')
    
    response_wait_time = 300  # 5 minutes
    response_start_time = time.time()
    search_tool_detected = False
    browser_tool_detected = False
    valid_response_found = False

    while time.time() - response_start_time < response_wait_time:
        elapsed = int(time.time() - response_start_time)

        if elapsed % 30 == 0 and elapsed > 0:
            page.screenshot(path=f'test-results/search_response_wait_{elapsed}s.png')
            print(f'Screenshot saved: search_response_wait_{elapsed}s.png (waiting {elapsed}s for response)')

        try:
            # Check for agent messages
            agent_messages = page.locator('[data-testid="agent-message"]').all()
            
            for i, msg in enumerate(agent_messages):
                try:
                    content = msg.text_content()
                    if content and len(content.strip()) > 10:
                        content_lower = content.lower()
                        
                        # Check for search tool indicators (REQUIRED)
                        search_indicators = [
                            'tavily', 'search_web', 'web search', 'searching the web',
                            'search tool', 'search engine', 'web_search', 'tavily search'
                        ]
                        
                        # Check for browser tool usage (FORBIDDEN - causes immediate failure)
                        browser_indicators = [
                            'fetch', 'browse', 'browser', 'http request', 'curl', 'wget',
                            'mcp tool: fetch', 'calling mcp tool: fetch', 'microagent stdio server: fetch'
                        ]
                        
                        # Check for president-related content (REQUIRED)
                        president_indicators = [
                            'president', 'biden', 'joe biden', 'joseph biden', 'white house',
                            'commander in chief', 'potus', 'united states president'
                        ]
                        
                        # Detect search tool usage
                        if any(indicator in content_lower for indicator in search_indicators):
                            search_tool_detected = True
                            print('✅ Detected search tool usage in agent response')
                        
                        # Detect browser tool usage (CRITICAL FAILURE)
                        if any(indicator in content_lower for indicator in browser_indicators):
                            browser_tool_detected = True
                            print('❌ CRITICAL: Detected browser tool usage instead of search tools')
                        
                        # Check for valid president information
                        if any(indicator in content_lower for indicator in president_indicators):
                            valid_response_found = True
                            print('✅ Found valid president information in response')
                            
                except Exception as e:
                    print(f'Error processing agent message {i}: {e}')
                    continue
        except Exception as e:
            print(f'Error checking for agent messages: {e}')

        page.wait_for_timeout(5000)

    # Final screenshot
    page.screenshot(path='test-results/search_12_final_response.png')
    print('Screenshot saved: search_12_final_response.png')
    
    # STRICT VALIDATION - test must fail if requirements not met
    failure_reasons = []
    
    # CRITICAL: Browser tools detected - immediate failure
    if browser_tool_detected:
        failure_reasons.append('CRITICAL: Browser tools (fetch/browse) were used instead of Tavily search')
    
    # REQUIRED: Search tool usage must be detected
    if not search_tool_detected:
        failure_reasons.append('REQUIRED: No search tool usage detected (Tavily search not used)')
    
    # REQUIRED: Valid response must be found
    if not valid_response_found:
        failure_reasons.append('REQUIRED: No valid president information found in response')
    
    if failure_reasons:
        failure_message = f"❌ Test FAILED: {'; '.join(failure_reasons)}"
        print(failure_message)
        print("\n=== STRICT VALIDATION REQUIREMENTS ===")
        print("1. Agent MUST use Tavily search tools (not browser tools)")
        print("2. Agent MUST provide valid president information")
        print("3. NO browser/fetch tools should be used")
        print("4. TAVILY_API_KEY must be properly configured")
        raise AssertionError(failure_message)
    
    print('✅ Test PASSED: Agent successfully used Tavily search and provided president information')
    return