import os

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
    try:
        import socket

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        result = s.connect_ex(('localhost', 12000))
        s.close()

        if result != 0:
            raise Exception(
                'OpenHands is not running on port 12000. Make sure to run "make run" before running the tests.'
            )

        print('OpenHands is running on port 12000')
    except Exception as e:
        print(f'Error checking if OpenHands is running: {e}')
        raise

    # No process to yield since we're not starting the app
    yield None

    # No cleanup needed since we're not starting the app


def test_readme_line_count():
    """Test that we can count the lines in the README.md file."""
    line_count = get_readme_line_count()
    print(f'README.md has {line_count} lines')
    assert line_count > 0, 'README.md should have at least one line'


@pytest.mark.skip(reason='Browser environment is disabled')
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


def test_openhands_workflow(page, openhands_app):
    """
    Test the OpenHands end-to-end workflow.

    This test follows the complete user journey:
    1. Start OpenHands
    2. Select the All-Hands-AI/OpenHands repository
    3. Launch the agent
    4. Ask a question about the README.md file
    5. Verify the agent's response
    """
    # Create test-results directory if it doesn't exist
    os.makedirs('test-results', exist_ok=True)

    # Get the actual line count of README.md for verification later
    line_count = get_readme_line_count()
    print(f'README.md has {line_count} lines')
    assert line_count > 0, 'README.md should have at least one line'

    # Navigate to the OpenHands application
    print('Navigating to OpenHands application...')
    page.goto('http://localhost:12000')

    # First check if the page loaded at all
    print('Checking if page loaded...')
    try:
        # Wait for any content to appear
        page.wait_for_load_state('networkidle', timeout=30000)
        print('Page loaded successfully')

        # Take a screenshot for debugging
        page.screenshot(path='test-results/page_loaded.png')
        print('Screenshot saved as page_loaded.png')

        # Print the page title
        print(f'Page title: {page.title()}')

        # Print the page URL
        print(f'Page URL: {page.url}')

        # Check if there's any content on the page
        body_content = page.content()
        print(f'Page content length: {len(body_content)} characters')
        print(f'First 200 characters of page content: {body_content[:200]}')

    except Exception as e:
        print(f'Error checking page load: {e}')
        page.screenshot(path='test-results/page_error.png')
        raise

    # Wait for the page to load and the repository dropdown to be visible
    print('Waiting for repository dropdown to be visible...')
    try:
        # First check if the app container is visible
        app_container = page.locator('#app')
        expect(app_container).to_be_visible(timeout=10000)
        print('App container is visible')

        # Now look for the repository dropdown
        repo_dropdown = page.locator('[data-testid="repo-dropdown"]')
        expect(repo_dropdown).to_be_visible(timeout=20000)
    except Exception as e:
        print(f'Error finding repository dropdown: {e}')
        page.screenshot(path='test-results/dropdown_error.png')
        raise

    # Click on the repository dropdown
    print('Clicking on repository dropdown...')
    repo_dropdown.click()

    # Type "All-Hands-AI/OpenHands" in the dropdown
    print('Typing repository name...')
    repo_dropdown.fill('All-Hands-AI/OpenHands')

    # Wait for the dropdown item to appear and click it
    print('Selecting repository from dropdown...')
    page.locator('text=All-Hands-AI/OpenHands').first.click()

    # Wait for the Launch button to be enabled
    print('Waiting for Launch button to be enabled...')
    launch_button = page.locator('[data-testid="repo-launch-button"]')
    expect(launch_button).to_be_enabled(timeout=30000)

    # Click the Launch button
    print('Clicking Launch button...')
    launch_button.click()

    # Check that the interface changes to the agent control interface
    print('Checking that interface changes to agent control...')
    chat_input = page.locator('[data-testid="chat-input"]')
    expect(chat_input).to_be_visible(timeout=60000)

    # Check for the "Connecting" state
    print("Checking for 'Connecting' state...")
    expect(page.locator('text=Connecting')).to_be_visible(timeout=30000)

    # Check for the "Initializing Agent" state
    print("Checking for 'Initializing Agent' state...")
    expect(page.locator('text=Initializing Agent')).to_be_visible(timeout=60000)

    # Check for the "Agent is waiting for user input..." state
    print("Checking for 'Agent is waiting for user input...' state...")
    expect(page.locator('text=Agent is waiting for user input')).to_be_visible(
        timeout=120000
    )

    # Enter the question about README.md lines
    print('Entering question about README.md lines...')
    question = 'How many lines are there in the main README.md file?'
    chat_input.fill(question)

    # Click the submit button
    print('Clicking submit button...')
    page.locator('[data-testid="submit-button"]').click()

    # Check for the "Agent is running task" state
    print("Checking for 'Agent is running task' state...")
    expect(page.locator('text=Agent is running task')).to_be_visible(timeout=30000)

    # Check for the "Agent has finished the task." state
    print("Checking for 'Agent has finished the task.' state...")
    expect(page.locator('text=Agent has finished the task')).to_be_visible(
        timeout=300000
    )

    # Check that the final agent message contains a number that matches the line count
    print('Checking that final agent message contains the correct line count...')
    # Wait for the agent's response to appear
    page.wait_for_timeout(5000)  # Give a little time for the response to fully render

    # Get all messages from the agent
    agent_messages = page.locator('.prose').all()

    # Check the last message from the agent
    if len(agent_messages) > 0:
        last_message = agent_messages[-1].text_content()
        print(f"Agent's last message: {last_message}")

        # Check if the message contains the line count
        assert str(line_count) in last_message, (
            f"Expected line count {line_count} not found in agent's response: {last_message}"
        )
        print(
            f"Successfully verified that the agent's response contains the correct line count: {line_count}"
        )
    else:
        raise AssertionError('No agent messages found')
