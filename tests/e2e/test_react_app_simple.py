"""E2E: React app creation test (simplified version).

This test verifies that the OpenHands agent can create and serve a React app.
It's a simplified version focused on core functionality.
"""

import os
import re
import time

from playwright.sync_api import Page, expect


def test_react_app_creation_simple(page: Page):
    """Simplified test for React app creation.

    1. Navigate to OpenHands (assumes GitHub token is already configured)
    2. Select the OpenHands repository
    3. Click Launch
    4. Wait for the agent to initialize
    5. Ask the agent to create a simple React app
    6. Verify the agent responds and starts working
    """
    # Create test-results directory if it doesn't exist
    os.makedirs('test-results', exist_ok=True)

    print('Starting simplified React app creation test...')

    # Navigate to the OpenHands application
    print('Step 1: Navigating to OpenHands...')
    page.goto('http://localhost:12000')
    page.wait_for_load_state('networkidle', timeout=30000)

    # Debug: Print page title and URL
    print(f'Page title: {page.title()}')
    print(f'Page URL: {page.url}')

    # Debug: Check if page has any content
    body_text = page.locator('body').text_content()
    print(f'Page body text length: {len(body_text) if body_text else 0}')
    if body_text and len(body_text) > 0:
        print(f'First 200 chars of body: {body_text[:200]}...')

    page.screenshot(path='test-results/react_simple_01_home.png')
    print('Screenshot saved: react_simple_01_home.png')

    # Step 2: Launch from scratch (do NOT select a repository)
    print('Step 2: Launching from scratch via header button...')

    # Wait for the home screen to load
    home_screen = page.locator('[data-testid="home-screen"]')
    expect(home_screen).to_be_visible(timeout=15000)
    print('Home screen is visible')

    # Find and click the "Launch from Scratch" header button
    header_button = page.locator('[data-testid="header-launch-button"]')
    expect(header_button).to_be_visible(timeout=15000)
    page.screenshot(path='test-results/react_simple_02_header_visible.png')
    print('Screenshot saved: react_simple_02_header_visible.png')

    # Wait until the button is enabled
    max_wait_attempts = 30
    button_enabled = False
    for attempt in range(max_wait_attempts):
        try:
            if header_button.is_enabled():
                print(f'Header Launch button is now enabled (attempt {attempt + 1})')
                button_enabled = True
                break
            else:
                print(
                    f'Header Launch button still disabled, waiting... (attempt {attempt + 1}/{max_wait_attempts})'
                )
                page.wait_for_timeout(2000)
        except Exception as e:
            print(f'Error checking header button state: {e}')
            page.wait_for_timeout(2000)

    if not button_enabled:
        print('Header Launch button never became enabled')
        page.screenshot(path='test-results/react_simple_03_header_disabled.png')
        print('Screenshot saved: react_simple_03_header_disabled.png')
        raise Exception('Header Launch button never became enabled')

    # Click the header launch button
    header_button.click()
    print('Header Launch button clicked successfully')

    page.screenshot(path='test-results/react_simple_03_after_launch_click.png')
    print('Screenshot saved: react_simple_03_after_launch_click.png')

    # Step 4: Wait for conversation interface to load (following working test pattern)
    print('Step 4: Waiting for conversation interface to load...')

    navigation_timeout = 300000  # 5 minutes
    check_interval = 10000  # 10 seconds

    page.screenshot(path='test-results/react_simple_05_after_launch.png')
    print('Screenshot saved: react_simple_05_after_launch.png')

    # Check for loading indicators first
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

    # Check URL to see if we're on conversation page
    try:
        current_url = page.url
        print(f'Current URL: {current_url}')
        if '/conversation/' in current_url or '/chat/' in current_url:
            print('URL indicates conversation page has loaded')
    except Exception as e:
        print(f'Error checking URL: {e}')

    # Wait for conversation interface elements
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

        except Exception as e:
            print(f'Error checking conversation interface: {e}')

        time.sleep(check_interval / 1000)

    if not conversation_loaded:
        print('Conversation interface not loaded within timeout')
        page.screenshot(path='test-results/react_simple_05_no_conversation.png')
        print('Screenshot saved: react_simple_05_no_conversation.png')
        raise Exception('Conversation interface not loaded')

    page.screenshot(path='test-results/react_simple_05_conversation_ready.png')
    print('Screenshot saved: react_simple_05_conversation_ready.png')

    # Wait for agent to be ready (using same approach as working conversation test)
    print('Step 6: Waiting for agent to be ready...')
    max_wait_time = 480  # 8 minutes (same as conversation test)
    start_time = time.time()
    agent_ready = False
    print(f'Waiting up to {max_wait_time} seconds for agent to be ready...')

    while time.time() - start_time < max_wait_time:
        elapsed = int(time.time() - start_time)
        if elapsed % 30 == 0 and elapsed > 0:
            page.screenshot(path=f'test-results/react_simple_waiting_{elapsed}s.png')
            print(
                f'Screenshot saved: react_simple_waiting_{elapsed}s.png (waiting {elapsed}s)'
            )

        try:
            # Check for ready indicators
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
        page.screenshot(path='test-results/react_simple_timeout_waiting_for_agent.png')
        raise AssertionError(
            f'Agent did not become ready for input within {max_wait_time} seconds'
        )

    page.screenshot(path='test-results/react_simple_06_agent_ready.png')
    print('Screenshot saved: react_simple_06_agent_ready.png')

    # Send message to create React app
    print('Step 7: Sending React app creation request...')
    message = "Create a simple React app using Vite. Set it up with a basic component that displays 'Hello from OpenHands React App!' and make sure it can be served locally."

    try:
        # Find and fill the input field (using same selectors as working conversation test)
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
            page.screenshot(path='test-results/react_simple_07_no_input_found.png')
            print('Screenshot saved: react_simple_07_no_input_found.png')

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
                page.screenshot(path='test-results/react_simple_07_reload_failed.png')
                print('Screenshot saved: react_simple_07_reload_failed.png')
                raise AssertionError('Could not find message input field after reload')

        message_input.fill(message)
        print('Message filled in input field')

        # Find and click submit button (using same selectors as working conversation test)
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
            print(
                'Submit button not found or never became enabled, trying alternatives'
            )
            try:
                message_input.press('Enter')
                print('Pressed Enter to submit message')
            except Exception as e:
                print(f'Error pressing Enter: {e}')
                raise AssertionError('Could not submit message')
        else:
            submit_button.click()
            print('Submit button clicked')

    except Exception as e:
        print(f'Error sending message: {e}')
        page.screenshot(path='test-results/react_simple_07_send_error.png')
        print('Screenshot saved: react_simple_07_send_error.png')
        raise

    page.screenshot(path='test-results/react_simple_07_message_sent.png')
    print('Screenshot saved: react_simple_07_message_sent.png')

    # Wait for agent to complete the React app creation task
    print('Step 8: Waiting for agent to demonstrate React app creation...')
    max_completion_time = 600  # 10 minutes for full task completion
    start_time = time.time()

    # Track evidence of actual work completed
    evidence_found = {
        'file_structure': False,
        'package_json': False,
        'app_component': False,
        'server_running': False,
        'app_accessible': False,
    }

    # Look for actual demonstrations of work, not just claims
    while time.time() - start_time < max_completion_time:
        elapsed = int(time.time() - start_time)
        if elapsed % 60 == 0 and elapsed > 0:  # Every minute
            page.screenshot(path=f'test-results/react_simple_waiting_{elapsed}s.png')
            print(f'Progress screenshot saved at {elapsed}s')

        try:
            # Look for agent messages that show actual evidence
            messages = page.locator('[data-testid="agent-message"]').all()
            for i, msg in enumerate(messages):
                try:
                    content = msg.text_content() or ''
                    content_lower = content.lower()

                    # Look for evidence of file structure being shown
                    if not evidence_found['file_structure']:
                        file_structure_patterns = [
                            r'src/.*app\.(jsx|tsx)',
                            r'public/.*index\.html',
                            r'package\.json',
                            r'vite\.config\.(js|ts)',
                            r'node_modules',
                            r'├──.*src',
                            r'└──.*public',
                        ]
                        for pattern in file_structure_patterns:
                            if re.search(pattern, content, re.IGNORECASE):
                                print(f'✅ Found file structure evidence: {pattern}')
                                evidence_found['file_structure'] = True
                                break

                    # Look for evidence of package.json contents being shown
                    if not evidence_found['package_json']:
                        package_patterns = [
                            r'"react":\s*"[^"]*"',
                            r'"vite":\s*"[^"]*"',
                            r'"@vitejs/plugin-react"',
                            r'"scripts":\s*{[^}]*"dev"',
                            r'"dependencies":\s*{[^}]*"react"',
                        ]
                        for pattern in package_patterns:
                            if re.search(pattern, content, re.IGNORECASE):
                                print(f'✅ Found package.json evidence: {pattern}')
                                evidence_found['package_json'] = True
                                break

                    # Look for evidence of App component source code being shown
                    if not evidence_found['app_component']:
                        app_component_patterns = [
                            r'hello from openhands react app',
                            r'function App\(\)',
                            r'const App = \(\)',
                            r'export default App',
                            r'<div.*>.*hello.*openhands.*</div>',
                            r'return \([^)]*hello from openhands',
                        ]
                        for pattern in app_component_patterns:
                            if re.search(pattern, content, re.IGNORECASE):
                                print(f'✅ Found App component evidence: {pattern}')
                                evidence_found['app_component'] = True
                                break

                    # Look for evidence of development server running
                    if not evidence_found['server_running']:
                        server_patterns = [
                            r'local:\s*http://localhost:\d+',
                            r'network:\s*http://[^:]+:\d+',
                            r'ready in \d+ms',
                            r'vite.*ready',
                            r'dev server running',
                            r'server started.*port \d+',
                            r'npm run dev',
                            r'yarn dev',
                        ]
                        for pattern in server_patterns:
                            if re.search(pattern, content, re.IGNORECASE):
                                print(f'✅ Found server running evidence: {pattern}')
                                evidence_found['server_running'] = True
                                break

                    # Look for evidence of app being accessible (curl/browser output)
                    if not evidence_found['app_accessible']:
                        accessible_patterns = [
                            r'<title>.*vite.*react.*</title>',
                            r'<div id="root">.*hello from openhands.*</div>',
                            r'curl.*localhost:\d+',
                            r'http status.*200',
                            r'<!doctype html>.*hello from openhands',
                            r'response.*hello from openhands react app',
                        ]
                        for pattern in accessible_patterns:
                            if re.search(pattern, content, re.IGNORECASE):
                                print(f'✅ Found app accessibility evidence: {pattern}')
                                evidence_found['app_accessible'] = True
                                break

                except Exception as e:
                    print(f'Error processing agent message {i}: {e}')
                    continue

        except Exception as e:
            print(f'Error checking for agent messages: {e}')

        # Check if we have sufficient evidence
        evidence_count = sum(evidence_found.values())
        print(f'Evidence found: {evidence_count}/5 - {evidence_found}')

        # We need at least 3 pieces of evidence to consider it successful
        # (file structure + package.json + app component) OR (app component + server + accessible)
        if evidence_count >= 3 and evidence_found['app_component']:
            print('✅ Sufficient evidence found for React app creation!')
            
            # Take final screenshots
            page.screenshot(path='test-results/react_simple_08_evidence_found.png')
            print('Screenshot saved: react_simple_08_evidence_found.png')
            
            page.screenshot(path='test-results/react_simple_08_final_state.png')
            print('Screenshot saved: react_simple_08_final_state.png')

            print('✅ SUCCESS: React app creation demonstrated successfully!')
            print(f'- File structure shown: {evidence_found["file_structure"]} ✓')
            print(f'- Package.json contents shown: {evidence_found["package_json"]} ✓')
            print(f'- App component source shown: {evidence_found["app_component"]} ✓')
            print(f'- Development server running: {evidence_found["server_running"]} ✓')
            print(f'- App accessible via HTTP: {evidence_found["app_accessible"]} ✓')
            print('- Agent demonstrated actual work completion ✓')
            return

        time.sleep(15)  # Check every 15 seconds

    # If we get here, insufficient evidence was provided
    page.screenshot(path='test-results/react_simple_08_final_state.png')
    print('Screenshot saved: react_simple_08_final_state.png')

    evidence_count = sum(evidence_found.values())
    print(f'❌ FAILURE: Insufficient evidence of React app creation ({evidence_count}/5)')
    print(f'Evidence found: {evidence_found}')
    print('Agent must DEMONSTRATE the work by showing:')
    print('- File structure (ls, tree commands)')
    print('- Package.json contents (cat package.json)')
    print('- App component source code (cat src/App.jsx)')
    print('- Development server running (npm run dev output)')
    print('- App accessible via HTTP (curl localhost:port)')
    
    raise AssertionError(
        f'Agent did not demonstrate React app creation with sufficient evidence. '
        f'Found {evidence_count}/5 pieces of evidence: {evidence_found}'
    )
