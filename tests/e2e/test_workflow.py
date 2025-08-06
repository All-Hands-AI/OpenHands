import os
import signal
import subprocess
import time

import pytest
from playwright.sync_api import Page, expect


def get_readme_line_count():
    """Get the line count of the README.md file."""
    readme_path = os.path.join(os.getcwd(), 'README.md')
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

    # Start OpenHands in the background
    log_file = open('/tmp/openhands-e2e-test.log', 'w')
    process = subprocess.Popen(
        ['make', 'run'],
        env=env,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        cwd=os.path.join(os.getcwd()),
    )

    # Wait for the application to start
    print('Waiting for OpenHands to start...')
    time.sleep(30)  # Give it time to start

    yield process

    # Stop OpenHands after tests
    print('Stopping OpenHands application...')
    process.send_signal(signal.SIGTERM)
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()

    log_file.close()

    # Kill any remaining processes
    try:
        subprocess.run(['pkill', '-f', 'make run'], check=False)
        subprocess.run(['pkill', '-f', 'python -m openhands'], check=False)
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


@pytest.mark.skip(reason='Requires full OpenHands setup with Docker')
def test_openhands_workflow(page: Page, openhands_app):
    """Test the OpenHands end-to-end workflow."""
    # Navigate to the OpenHands application
    page.goto('http://localhost:12002/')

    # Wait for the repository selection dropdown to be visible
    page.wait_for_selector('button:has-text("Select a repository")')

    # Click on the repository selection dropdown
    page.click('button:has-text("Select a repository")')

    # Wait for the dropdown to open and select the OpenHands repository
    page.wait_for_selector('div[role="option"]:has-text("All-Hands-AI/OpenHands")')
    page.click('div[role="option"]:has-text("All-Hands-AI/OpenHands")')

    # Click the Launch button
    page.wait_for_selector('button:has-text("Launch")')
    page.click('button:has-text("Launch")')

    # Check that the interface changes to the agent control interface
    page.wait_for_selector('div:has-text("Connecting")', state='visible')

    # Check that we go through the "Initializing Agent" state
    page.wait_for_selector('div:has-text("Initializing Agent")', state='visible')

    # Check that we reach the "Agent is waiting for user input..." state
    page.wait_for_selector(
        'div:has-text("Agent is waiting for user input...")',
        state='visible',
        timeout=60000,
    )

    # Enter the test question and submit
    page.fill(
        'textarea[placeholder="Message OpenHands..."]',
        'How many lines are there in the main README.md file?',
    )
    page.click('button[aria-label="Send message"]')

    # Check that we go through the "Agent is running task" state
    page.wait_for_selector('div:has-text("Agent is running task")', state='visible')

    # Check that we reach the "Agent has finished the task." state
    page.wait_for_selector(
        'div:has-text("Agent has finished the task.")', state='visible', timeout=120000
    )

    # Get the final agent message
    final_message = page.locator('.message-content').last.text_content()

    # Get the actual line count of README.md
    readme_line_count = get_readme_line_count()

    # Check that the final message contains the correct line count
    assert str(readme_line_count) in final_message, (
        f'Expected line count {readme_line_count} not found in message: {final_message}'
    )
