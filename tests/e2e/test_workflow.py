import os
import signal
import subprocess
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
    """Start the OpenHands application before tests and stop it after."""
    print('Starting OpenHands application...')

    # Set environment variables
    env = os.environ.copy()
    env['INSTALL_DOCKER'] = '0'
    env['RUNTIME'] = 'local'
    env['FRONTEND_PORT'] = '12000'
    env['FRONTEND_HOST'] = '0.0.0.0'
    env['BACKEND_HOST'] = '0.0.0.0'

    # Check for required environment variables and set defaults if needed
    required_vars = ['GITHUB_TOKEN', 'LLM_MODEL', 'LLM_API_KEY']
    for var in required_vars:
        if var not in os.environ:
            print(f'Warning: {var} not set, using default value for testing')
            if var == 'GITHUB_TOKEN':
                env[var] = 'test-token'
            elif var == 'LLM_MODEL':
                env[var] = 'gpt-4o'
            elif var == 'LLM_API_KEY':
                env[var] = 'test-key'
        else:
            env[var] = os.environ[var]

    # Pass through optional environment variables
    if 'LLM_BASE_URL' in os.environ:
        env['LLM_BASE_URL'] = os.environ['LLM_BASE_URL']

    # Get the path to the repository root directory
    current_dir = os.getcwd()
    # If we're in the tests/e2e directory, go up two levels to the repo root
    if current_dir.endswith('tests/e2e'):
        repo_root = os.path.abspath(os.path.join(current_dir, '../..'))
    else:
        # If we're already at the repo root or somewhere else, use current directory
        repo_root = current_dir

    print(f'Starting OpenHands from directory: {repo_root}')

    # First build the application according to the development workflow
    print('Building OpenHands application...')
    build_log_file = open('/tmp/openhands-e2e-build.log', 'w')
    build_process = subprocess.Popen(
        ['make', 'build'],
        env=env,
        stdout=build_log_file,
        stderr=subprocess.STDOUT,
        cwd=repo_root,
    )

    # Wait for the build to complete
    try:
        build_process.wait(timeout=300)  # 5 minutes timeout for build
        print(f'Build process completed with exit code: {build_process.returncode}')
    except subprocess.TimeoutExpired:
        build_process.kill()
        print('Build process timed out and was killed')
        raise Exception('Build process timed out')

    build_log_file.close()

    if build_process.returncode != 0:
        raise Exception(
            f'Build process failed with exit code: {build_process.returncode}'
        )

    # Start OpenHands in the background
    print('Starting OpenHands application with "make run"...')
    log_file = open('/tmp/openhands-e2e-test.log', 'w')
    process = subprocess.Popen(
        ['make', 'run'],
        env=env,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        cwd=repo_root,
    )

    # Wait for the application to start
    print('Waiting for OpenHands to start...')
    time.sleep(90)  # Give it more time to start (90 seconds)

    # Check if the application is running by trying to connect to the frontend port
    try:
        import socket

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        result = s.connect_ex(('localhost', 12000))
        s.close()

        if result != 0:
            print('Warning: Could not connect to OpenHands frontend on port 12000')
            print('Waiting additional time...')
            time.sleep(30)  # Wait an additional 30 seconds
    except Exception as e:
        print(f'Error checking if OpenHands is running: {e}')

    yield process

    # Stop OpenHands after tests
    print('Stopping OpenHands application...')
    process.send_signal(signal.SIGTERM)
    try:
        process.wait(timeout=30)  # Increased timeout to 30 seconds
    except subprocess.TimeoutExpired:
        print('Process did not terminate gracefully, killing it...')
        process.kill()

    log_file.close()

    # Kill any remaining processes
    try:
        subprocess.run(['pkill', '-f', 'make run'], check=False)
        subprocess.run(['pkill', '-f', 'python -m openhands'], check=False)
        # Kill any other related processes
        subprocess.run(['pkill', '-f', 'node'], check=False)
        subprocess.run(['pkill', '-f', 'npm'], check=False)
    except Exception as e:
        print(f'Error cleaning up processes: {e}')


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
    # Get the actual line count of README.md for verification later
    line_count = get_readme_line_count()
    print(f'README.md has {line_count} lines')
    assert line_count > 0, 'README.md should have at least one line'

    # Navigate to the OpenHands application
    print('Navigating to OpenHands application...')
    page.goto('http://localhost:12000')

    # Wait for the page to load and the repository dropdown to be visible
    print('Waiting for repository dropdown to be visible...')
    repo_dropdown = page.locator('[data-testid="repo-dropdown"]')
    expect(repo_dropdown).to_be_visible(timeout=30000)

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
