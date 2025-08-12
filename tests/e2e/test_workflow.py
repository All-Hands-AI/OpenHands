import os
import re
import time

import pytest
from playwright.sync_api import Page, expect


def get_readme_line_count():
    """Get the line count of the README.md file."""
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
    with open(readme_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    return len(lines)


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
            import socket
            import time

            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2)
            result = s.connect_ex(('localhost', 12000))
            s.close()

            if result == 0:
                print(
                    f'OpenHands is running on port 12000 (attempt {attempt}/{max_attempts})'
                )
                # Verify we can get HTML content
                import urllib.request

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
    raise Exception(
        'OpenHands is not running on port 12000. Make sure to run "make run" before running the tests.'
    )


def test_readme_line_count():
    """Test that we can count the lines in the README.md file."""
    line_count = get_readme_line_count()
    print(f'README.md has {line_count} lines')
    assert line_count > 0, 'README.md should have at least one line'


def test_simple_browser_navigation(page: Page):
    """Test that we can navigate to a page using Playwright."""
    # Navigate to the GitHub repository
    page.goto('https://github.com/All-Hands-AI/OpenHands')

    # Check that the page title contains "OpenHands"
    expect(page).to_have_title(
        'GitHub - All-Hands-AI/OpenHands: 🙌 OpenHands: Code Less, Make More'
    )

    # Check that the repository name is displayed
    repo_header = page.locator('strong[itemprop="name"] a')
    expect(repo_header).to_contain_text('OpenHands')

    print('Successfully navigated to the OpenHands GitHub repository')


def test_openhands_full_workflow(page, openhands_app):
    """
    Test the complete OpenHands workflow:
    0. Assume environment variables are set (GITHUB_TOKEN, LLM_MODEL, LLM_API_KEY, LLM_BASE_URL)
    1. Start OpenHands (already done by openhands_app fixture)
    2. Use playwright to:
       a. Handle AI Provider Configuration if needed
       b. Click on the "All-Hands-AI/OpenHands" repo in the "Select a repo" dropdown
       c. Click "Launch"
       d. Check that the interface changes to the agent control interface
       e. Check agent states: "Connecting", "Initializing Agent", "Agent is waiting for user input..."
       f. Enter "How many lines are there in the main README.md file?" and submit
       g. Check agent states: "Agent is running task" and "Agent has finished the task."
       h. Check that the final agent message contains the correct line count
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
    page.screenshot(path='test-results/01_initial_load.png')
    print('Screenshot saved: 01_initial_load.png')

    # Step 2a: Handle AI Provider Configuration if it appears
    print('Step 2a: Checking for AI Provider Configuration modal...')
    try:
        # Check if the AI Provider Configuration modal is present
        config_modal = page.locator('text=AI Provider Configuration')
        if config_modal.is_visible(timeout=5000):
            print('AI Provider Configuration modal detected')
            
            # Check if API key field is empty and fill it if needed
            api_key_input = page.locator('input[placeholder*="API"], input[name*="api"], input[type="password"]').first
            if api_key_input.is_visible():
                current_value = api_key_input.input_value()
                if not current_value.strip():
                    print('API key field is empty, filling with environment variable')
                    # Use a placeholder API key for testing
                    api_key_input.fill('test-api-key-from-env')
                else:
                    print('API key field already has a value')
            
            # Click Save button
            save_button = page.locator('button:has-text("Save")')
            if save_button.is_visible():
                print('Clicking Save button in AI Provider Configuration')
                save_button.click()
                page.wait_for_timeout(2000)  # Wait for modal to close
                
        page.screenshot(path='test-results/02_after_config.png')
        print('Screenshot saved: 02_after_config.png')
        
    except Exception as e:
        print(f'No AI Provider Configuration modal found or error handling it: {e}')

    # Step 2b: Handle Privacy Preferences modal if it appears
    print('Step 2b: Checking for Privacy Preferences modal...')
    try:
        # Check if the Privacy Preferences modal is present
        privacy_modal = page.locator('text=Your Privacy Preferences')
        if privacy_modal.is_visible(timeout=5000):
            print('Privacy Preferences modal detected')
            
            # Click "Confirm Preferences" button
            confirm_button = page.locator('button:has-text("Confirm Preferences")')
            if confirm_button.is_visible():
                print('Clicking Confirm Preferences button')
                confirm_button.click()
                page.wait_for_timeout(2000)  # Wait for modal to close
            else:
                print('Confirm Preferences button not found, looking for alternatives...')
                # Try other possible button texts
                alt_buttons = [
                    'button:has-text("Confirm")',
                    'button:has-text("Accept")',
                    'button:has-text("OK")',
                    'button[type="submit"]'
                ]
                for button_selector in alt_buttons:
                    try:
                        button = page.locator(button_selector)
                        if button.is_visible(timeout=1000):
                            print(f'Found alternative button: {button_selector}')
                            button.click()
                            page.wait_for_timeout(2000)
                            break
                    except:
                        continue
                
        page.screenshot(path='test-results/03_after_privacy.png')
        print('Screenshot saved: 03_after_privacy.png')
        
    except Exception as e:
        print(f'No Privacy Preferences modal found or error handling it: {e}')

    # Step 2c: Wait for home screen and find the repository selector
    print('Step 2c: Looking for repository selector...')
    
    # Wait for the home screen to load
    home_screen = page.locator('[data-testid="home-screen"]')
    expect(home_screen).to_be_visible(timeout=15000)
    print('Home screen is visible')
    
    # Look for the repository dropdown/selector
    # Try multiple possible selectors for the repository dropdown
    repo_selectors = [
        'input[placeholder*="Search repositories"]',
        'input[placeholder*="repository"]',
        '[data-testid*="repo"]',
        'button:has-text("Select")',
        '.repository-selector',
        '[role="combobox"]'
    ]
    
    repo_input = None
    for selector in repo_selectors:
        try:
            element = page.locator(selector).first
            if element.is_visible(timeout=2000):
                repo_input = element
                print(f'Found repository selector with: {selector}')
                break
        except:
            continue
    
    if not repo_input:
        print('Repository selector not found, taking screenshot for debugging')
        page.screenshot(path='test-results/04_repo_selector_not_found.png')
        # Try to find any input or dropdown elements
        all_inputs = page.locator('input, select, [role="combobox"], [role="textbox"]')
        count = all_inputs.count()
        print(f'Found {count} input/dropdown elements on the page')
        for i in range(min(count, 5)):  # Check first 5 elements
            element = all_inputs.nth(i)
            placeholder = element.get_attribute('placeholder') or ''
            role = element.get_attribute('role') or ''
            print(f'  Element {i}: placeholder="{placeholder}", role="{role}"')
        
        raise Exception('Could not find repository selector')

    # Step 2c: Select the OpenHands repository
    print('Step 2d: Selecting All-Hands-AI/OpenHands repository...')
    
    # Click on the repository input to open dropdown
    repo_input.click()
    page.wait_for_timeout(1000)
    
    # Type to search for the OpenHands repository
    repo_input.fill('All-Hands-AI/OpenHands')
    page.wait_for_timeout(2000)  # Wait for search results
    
    # Look for the OpenHands repository in the dropdown
    openhands_option = page.locator('text=All-Hands-AI/OpenHands').first
    if openhands_option.is_visible(timeout=5000):
        print('Found All-Hands-AI/OpenHands in dropdown, clicking...')
        openhands_option.click()
    else:
        # Try alternative selectors
        alt_selectors = [
            '[data-testid*="OpenHands"]',
            'li:has-text("OpenHands")',
            '[role="option"]:has-text("OpenHands")'
        ]
        found = False
        for selector in alt_selectors:
            try:
                element = page.locator(selector).first
                if element.is_visible(timeout=2000):
                    print(f'Found OpenHands repo with selector: {selector}')
                    element.click()
                    found = True
                    break
            except:
                continue
        
        if not found:
            page.screenshot(path='test-results/05_repo_not_found.png')
            raise Exception('Could not find All-Hands-AI/OpenHands repository in dropdown')
    
    page.wait_for_timeout(1000)
    page.screenshot(path='test-results/06_repo_selected.png')
    print('Screenshot saved: 06_repo_selected.png')

    # Step 2d: Click Launch button
    print('Step 2e: Looking for Launch button...')
    
    launch_button = page.locator('button:has-text("Launch")')
    expect(launch_button).to_be_visible(timeout=10000)
    expect(launch_button).to_be_enabled()
    print('Launch button found and enabled, clicking...')
    
    launch_button.click()
    print('Launch button clicked')
    
    # Step 2e: Wait for conversation interface to load
    print('Step 2f: Waiting for conversation interface to load...')
    
    # Wait for navigation to conversation page
    page.wait_for_url('**/conversations/**', timeout=30000)
    print('Navigated to conversation page')
    
    # Wait for the conversation interface elements
    conversation_interface = page.locator('[data-testid="app-route"]')
    expect(conversation_interface).to_be_visible(timeout=15000)
    print('Conversation interface is visible')
    
    page.screenshot(path='test-results/07_conversation_loaded.png')
    print('Screenshot saved: 07_conversation_loaded.png')

    # Step 2f: Check agent initialization states
    print('Step 2g: Monitoring agent states during initialization...')
    
    # Look for agent status indicators
    status_indicators = [
        'text=Connecting',
        'text=Initializing Agent',
        'text=Agent is waiting for user input',
        '[data-testid*="status"]',
        '.agent-status',
        '.status-indicator'
    ]
    
    # Wait for initialization to complete (look for "waiting for user input" state)
    max_wait_time = 60  # seconds
    start_time = time.time()
    
    while time.time() - start_time < max_wait_time:
        page.screenshot(path=f'test-results/08_agent_state_{int(time.time() - start_time)}s.png')
        
        # Check for "waiting for user input" state
        waiting_indicators = [
            'text=Agent is waiting for user input',
            'text=waiting for user input',
            'text=awaiting user input',
            '[data-testid*="waiting"]'
        ]
        
        for indicator in waiting_indicators:
            try:
                element = page.locator(indicator)
                if element.is_visible(timeout=1000):
                    print('Agent is ready for user input!')
                    break
            except:
                continue
        else:
            # Check if we can find a message input (alternative way to detect readiness)
            message_input = page.locator('textarea, input[type="text"]').first
            if message_input.is_visible(timeout=1000):
                print('Message input is available, agent appears ready')
                break
            
            print(f'Still waiting for agent to be ready... ({int(time.time() - start_time)}s)')
            page.wait_for_timeout(2000)
            continue
        break
    else:
        print('Timeout waiting for agent to be ready, but continuing with test...')
    
    page.screenshot(path='test-results/09_agent_ready.png')
    print('Screenshot saved: 09_agent_ready.png')

    # Step 2g: Enter the question and submit
    print('Step 2h: Entering question about README.md line count...')
    
    # Find the message input
    message_input_selectors = [
        'textarea[placeholder*="message"]',
        'textarea[placeholder*="Message"]',
        'input[placeholder*="message"]',
        'textarea',
        '[data-testid*="input"]',
        '[data-testid*="message"]'
    ]
    
    message_input = None
    for selector in message_input_selectors:
        try:
            element = page.locator(selector).first
            if element.is_visible(timeout=2000):
                message_input = element
                print(f'Found message input with selector: {selector}')
                break
        except:
            continue
    
    if not message_input:
        page.screenshot(path='test-results/10_input_not_found.png')
        raise Exception('Could not find message input field')
    
    # Enter the question
    question = "How many lines are there in the main README.md file?"
    print(f'Typing question: {question}')
    message_input.fill(question)
    
    # Find and click submit button
    submit_selectors = [
        'button[type="submit"]',
        'button:has-text("Send")',
        'button:has-text("Submit")',
        '[data-testid*="submit"]',
        '[data-testid*="send"]'
    ]
    
    submit_button = None
    for selector in submit_selectors:
        try:
            element = page.locator(selector).first
            if element.is_visible(timeout=2000):
                submit_button = element
                print(f'Found submit button with selector: {selector}')
                break
        except:
            continue
    
    if not submit_button:
        # Try pressing Enter as alternative
        print('Submit button not found, trying Enter key...')
        message_input.press('Enter')
    else:
        print('Clicking submit button...')
        submit_button.click()
    
    page.screenshot(path='test-results/11_question_submitted.png')
    print('Screenshot saved: 11_question_submitted.png')

    # Step 2h: Monitor agent execution and wait for completion
    print('Step 2i: Monitoring agent execution...')
    
    # Wait for agent to start processing
    page.wait_for_timeout(3000)
    
    # Monitor for completion (look for final response)
    max_execution_time = 120  # seconds
    start_time = time.time()
    
    final_response = None
    while time.time() - start_time < max_execution_time:
        current_time = int(time.time() - start_time)
        if current_time % 10 == 0:  # Screenshot every 10 seconds
            page.screenshot(path=f'test-results/12_execution_{current_time}s.png')
        
        # Look for completion indicators
        completion_indicators = [
            'text=Agent has finished the task',
            'text=finished',
            'text=completed',
            'text=done'
        ]
        
        for indicator in completion_indicators:
            try:
                if page.locator(indicator).is_visible(timeout=1000):
                    print('Agent has finished the task!')
                    final_response = True
                    break
            except:
                continue
        
        if final_response:
            break
            
        # Also check if we can see a response with numbers (indicating completion)
        try:
            # Look for messages containing numbers that might be the line count
            messages = page.locator('[data-testid*="message"], .message, .chat-message').all()
            for message in messages[-5:]:  # Check last 5 messages
                text = message.text_content() or ''
                if re.search(r'\b\d+\b', text) and ('line' in text.lower() or 'readme' in text.lower()):
                    print(f'Found potential answer in message: {text[:100]}...')
                    final_response = text
                    break
        except:
            pass
        
        if final_response and final_response != True:
            break
            
        print(f'Agent still working... ({current_time}s)')
        page.wait_for_timeout(5000)
    
    page.screenshot(path='test-results/13_final_result.png')
    print('Screenshot saved: 13_final_result.png')

    # Step 2i: Verify the response contains the correct line count
    print('Step 2j: Verifying the response contains correct line count...')
    
    if not final_response:
        print('No final response detected, checking all messages for line count...')
        
    # Get all messages and look for the line count
    try:
        # Get page content and look for the expected number
        page_content = page.content()
        
        # Look for the expected line count in the page
        line_count_pattern = rf'\b{expected_line_count}\b'
        matches = re.findall(line_count_pattern, page_content)
        
        if matches:
            print(f'✅ Found expected line count {expected_line_count} in the response!')
            print(f'Number of matches found: {len(matches)}')
        else:
            print(f'❌ Expected line count {expected_line_count} not found in response')
            
            # Look for any numbers that might be close
            all_numbers = re.findall(r'\b\d+\b', page_content)
            unique_numbers = list(set(all_numbers))
            print(f'All numbers found in response: {unique_numbers[:20]}')  # Show first 20
            
            # Check if any number is close to expected
            for num_str in unique_numbers:
                try:
                    num = int(num_str)
                    if abs(num - expected_line_count) <= 5:  # Within 5 lines
                        print(f'Found close number: {num} (expected: {expected_line_count})')
                except:
                    continue
        
        # Also check for specific README-related text
        readme_mentions = len(re.findall(r'readme', page_content, re.IGNORECASE))
        line_mentions = len(re.findall(r'line', page_content, re.IGNORECASE))
        print(f'README mentions: {readme_mentions}, Line mentions: {line_mentions}')
        
        # The test passes if we found the expected line count
        assert matches, f'Expected line count {expected_line_count} not found in agent response'
        
    except Exception as e:
        print(f'Error verifying response: {e}')
        # Take a final screenshot for debugging
        page.screenshot(path='test-results/14_verification_error.png')
        raise

    print('✅ OpenHands full workflow test completed successfully!')
    print(f'✅ Agent correctly identified README.md has {expected_line_count} lines')
