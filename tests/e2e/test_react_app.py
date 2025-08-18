"""
E2E: React App Creation Test

This test verifies that the OpenHands agent can:
1. Scaffold a minimal React app using vite
2. Build and serve the app on a known port bound to 0.0.0.0
3. Return an accessible link via the web-hosts API endpoint
"""

import os
import time

import requests
from playwright.sync_api import Page, expect


def test_react_app_creation_and_serving(page: Page):
    """
    Test that the agent can create, build, and serve a React app:
    1. Navigate to OpenHands and start a conversation
    2. Ask the agent to create a React app with vite
    3. Ask the agent to build and serve the app on port 3000
    4. Retrieve web hosts via API and verify the app is accessible
    """
    # Create test-results directory if it doesn't exist
    os.makedirs('test-results', exist_ok=True)

    # Navigate to the OpenHands application
    print('Step 1: Navigating to OpenHands application...')
    page.goto('http://localhost:12000')
    page.wait_for_load_state('networkidle', timeout=30000)

    # Take initial screenshot
    page.screenshot(path='test-results/react_01_initial_load.png')
    print('Screenshot saved: react_01_initial_load.png')

    # Step 2: Select a repository (we'll use the current OpenHands repo)
    print('Step 2: Selecting repository...')

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

    page.screenshot(path='test-results/react_02_repo_selected.png')
    print('Screenshot saved: react_02_repo_selected.png')

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

    page.screenshot(path='test-results/react_04_after_launch.png')
    print('Screenshot saved: react_04_after_launch.png')

    # Wait for conversation interface to be ready
    start_time = time.time()
    conversation_loaded = False
    navigation_timeout = 180  # 3 minutes (reduced for CI)

    while time.time() - start_time < navigation_timeout:
        try:
            selectors = [
                '[data-testid="chat-input"]',
                '[data-testid="conversation-screen"]',
                '[data-testid="message-input"]',
                'textarea',
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

            page.wait_for_timeout(5000)
        except Exception as e:
            print(f'Error checking for conversation interface: {e}')
            page.wait_for_timeout(5000)

    if not conversation_loaded:
        print('Timed out waiting for conversation interface to load')
        page.screenshot(path='test-results/react_05_timeout.png')
        print('Screenshot saved: react_05_timeout.png')
        raise TimeoutError('Timed out waiting for conversation interface to load')

    # Step 5: Wait for agent to be ready
    print('Step 5: Waiting for agent to be ready for input...')

    max_wait_time = 240  # 4 minutes (reduced for CI)
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

            if input_ready and submit_ready:
                print('✅ Agent is ready for user input')
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

    # Step 6: Ask the agent to create a React app
    print('Step 6: Asking agent to create a React app...')

    # Find the message input
    input_selectors = [
        '[data-testid="chat-input"] textarea',
        '[data-testid="message-input"]',
        'textarea',
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
        page.screenshot(path='test-results/react_06_no_input_found.png')
        print('Screenshot saved: react_06_no_input_found.png')
        raise AssertionError('Could not find message input field')

    # Type the React app creation request
    react_request = """Please create a minimal React app using Vite with the following requirements:
1. Create a new React app in a directory called 'react-hello-world'
2. The app should display "Hello World from OpenHands React App!" as the main content
3. Build the app for production
4. Serve the app on port 3000 bound to 0.0.0.0 so it's accessible externally
5. Keep the server running in the background

Please use these exact commands:
- npm create vite@latest react-hello-world -- --template react
- cd react-hello-world && npm install
- Modify src/App.jsx to show the hello message
- npm run build
- npx serve -s dist -l 3000 -H 0.0.0.0 &

Make sure the server stays running so I can access it."""

    try:
        message_input.click()
        message_input.fill(react_request)
        print('Message typed successfully')

        # Find and click submit button
        submit_selectors = [
            '[data-testid="chat-input"] button[type="submit"]',
            'button[type="submit"]',
            'button:has-text("Send")',
        ]

        submit_button = None
        for selector in submit_selectors:
            try:
                button = page.locator(selector)
                if button.is_visible(timeout=2000):
                    print(f'Found submit button with selector: {selector}')
                    submit_button = button
                    break
            except Exception:
                continue

        if submit_button:
            submit_button.click()
            print('Submit button clicked')
        else:
            # Try pressing Enter as fallback
            message_input.press('Enter')
            print('Pressed Enter to submit')

    except Exception as e:
        print(f'Error sending message: {e}')
        page.screenshot(path='test-results/react_07_send_error.png')
        print('Screenshot saved: react_07_send_error.png')
        raise

    page.screenshot(path='test-results/react_08_message_sent.png')
    print('Screenshot saved: react_08_message_sent.png')

    # Step 7: Wait for the agent to complete the React app creation and serving
    print('Step 7: Waiting for agent to complete React app creation and serving...')

    # Wait for agent to process and complete the task
    max_completion_time = (
        300  # 5 minutes for React app creation and serving (reduced for CI)
    )
    start_time = time.time()
    task_completed = False

    # Keywords that indicate the task is progressing or completed
    completion_indicators = [
        'server running',
        'serving on',
        'localhost:3000',
        'serve -s dist',
        'Local:   http',
        'Network: http',
        'ready in',
        'server started',
    ]

    while time.time() - start_time < max_completion_time:
        elapsed = int(time.time() - start_time)
        if elapsed % 60 == 0 and elapsed > 0:
            page.screenshot(path=f'test-results/react_completion_{elapsed}s.png')
            print(
                f'Screenshot saved: react_completion_{elapsed}s.png (waiting {elapsed}s)'
            )

        try:
            # Check the page content for completion indicators
            page_content = page.content()

            for indicator in completion_indicators:
                if indicator.lower() in page_content.lower():
                    print(f'Found completion indicator: {indicator}')
                    task_completed = True
                    break

            if task_completed:
                print(
                    '✅ Agent appears to have completed the React app creation and serving'
                )
                break

            # Also check if the agent is waiting for input again (task might be done)
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
                    # Agent is ready for input, let's check if we can see any server-related output
                    if any(
                        keyword in page_content.lower()
                        for keyword in ['vite', 'react', 'npm', 'serve']
                    ):
                        print(
                            'Agent is ready for input and React-related content found, assuming task completed'
                        )
                        task_completed = True
                        break
            except Exception:
                pass

        except Exception as e:
            print(f'Error checking task completion: {e}')

        page.wait_for_timeout(10000)  # Wait 10 seconds before checking again

    if not task_completed:
        page.screenshot(path='test-results/react_task_timeout.png')
        print('Screenshot saved: react_task_timeout.png')
        print(
            'Warning: Task completion indicators not found, but continuing with web host check...'
        )

    # Step 8: Extract conversation ID from URL and get web hosts
    print('Step 8: Getting web hosts from API...')

    try:
        current_url = page.url
        print(f'Current URL: {current_url}')

        # Extract conversation ID from URL
        conversation_id = None
        if '/conversation/' in current_url:
            conversation_id = (
                current_url.split('/conversation/')[-1].split('?')[0].split('#')[0]
            )
        elif '/chat/' in current_url:
            conversation_id = (
                current_url.split('/chat/')[-1].split('?')[0].split('#')[0]
            )

        if not conversation_id:
            raise ValueError('Could not extract conversation ID from URL')

        print(f'Extracted conversation ID: {conversation_id}')

        # Make API request to get web hosts
        api_url = (
            f'http://localhost:12000/api/conversations/{conversation_id}/web-hosts'
        )
        print(f'Making API request to: {api_url}')

        # Wait a bit for the server to be fully ready
        time.sleep(10)

        response = requests.get(api_url, timeout=30)
        print(f'API response status: {response.status_code}')
        print(f'API response content: {response.text}')

        if response.status_code == 200:
            hosts_data = response.json()
            hosts = hosts_data.get('hosts', {})
            print(f'Web hosts: {hosts}')

            if not hosts:
                raise ValueError('No web hosts returned from API')

            # Step 9: Verify the React app is accessible
            print('Step 9: Verifying React app accessibility...')

            app_accessible = False
            for host_url, port in hosts.items():
                if port == 3000:  # Look for our React app port
                    print(f'Found React app host: {host_url}:{port}')

                    # Try to access the React app
                    try:
                        app_response = requests.get(f'http://{host_url}', timeout=30)
                        print(f'React app response status: {app_response.status_code}')

                        if app_response.status_code == 200:
                            app_content = app_response.text
                            print(f'React app content length: {len(app_content)}')

                            # Check for expected content
                            expected_texts = [
                                'Hello World from OpenHands React App!',
                                'react',
                                'vite',
                            ]

                            content_found = False
                            for expected_text in expected_texts:
                                if expected_text.lower() in app_content.lower():
                                    print(f'✅ Found expected content: {expected_text}')
                                    content_found = True
                                    break

                            if content_found:
                                app_accessible = True
                                print(
                                    '✅ React app is accessible and contains expected content!'
                                )
                                break
                            else:
                                print(
                                    '❌ React app accessible but missing expected content'
                                )
                                print(
                                    f'First 500 chars of content: {app_content[:500]}'
                                )
                        else:
                            print(
                                f'❌ React app returned status {app_response.status_code}'
                            )

                    except Exception as e:
                        print(f'❌ Error accessing React app at {host_url}: {e}')

            if not app_accessible:
                # Try to access any available host as fallback
                print('Trying to access any available host as fallback...')
                for host_url, port in hosts.items():
                    try:
                        fallback_response = requests.get(
                            f'http://{host_url}', timeout=30
                        )
                        print(
                            f'Fallback host {host_url}:{port} status: {fallback_response.status_code}'
                        )
                        if fallback_response.status_code == 200:
                            print(
                                f'Fallback content preview: {fallback_response.text[:200]}'
                            )
                    except Exception as e:
                        print(f'Error accessing fallback host {host_url}: {e}')

                raise AssertionError('React app is not accessible through any web host')

        else:
            raise ValueError(
                f'API request failed with status {response.status_code}: {response.text}'
            )

    except Exception as e:
        print(f'Error in web host verification: {e}')
        page.screenshot(path='test-results/react_09_api_error.png')
        print('Screenshot saved: react_09_api_error.png')
        raise

    # Final success screenshot
    page.screenshot(path='test-results/react_10_success.png')
    print('Screenshot saved: react_10_success.png')
    print('✅ Test completed successfully!')
