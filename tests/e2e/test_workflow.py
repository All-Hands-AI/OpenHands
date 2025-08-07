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

    # Check for required environment variables
    required_vars = ['GITHUB_TOKEN', 'LLM_MODEL', 'LLM_API_KEY']
    missing_vars = [var for var in required_vars if var not in os.environ]
    if missing_vars:
        pytest.fail(
            f'Required environment variables not set: {", ".join(missing_vars)}'
        )

    # Set environment variables
    env = os.environ.copy()
    env['INSTALL_DOCKER'] = '0'
    env['RUNTIME'] = 'local'
    env['FRONTEND_PORT'] = '12000'
    env['FRONTEND_HOST'] = '0.0.0.0'
    env['BACKEND_HOST'] = '0.0.0.0'

    # Pass through required environment variables
    env['GITHUB_TOKEN'] = os.environ['GITHUB_TOKEN']
    env['LLM_MODEL'] = os.environ['LLM_MODEL']
    env['LLM_API_KEY'] = os.environ['LLM_API_KEY']
    if 'LLM_BASE_URL' in os.environ:
        env['LLM_BASE_URL'] = os.environ['LLM_BASE_URL']

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


def test_openhands_workflow(page: Page, openhands_app):
    """Test the OpenHands end-to-end workflow."""
    try:
        # Navigate to the OpenHands application
        page.goto('http://localhost:12000/')

        # Take a screenshot to see what's on the page
        page.screenshot(path='/tmp/openhands-screenshot.png')

        # Wait for the page to load
        page.wait_for_selector('body', timeout=5000)

        # Print the page content for debugging
        print(f'Page title: {page.title()}')
        print(f'Page URL: {page.url}')

        # Check if we can find any navigation elements
        nav_elements = page.query_selector_all('nav a, a[href], button')
        print(f'Found {len(nav_elements)} navigation elements')
        for i, elem in enumerate(nav_elements):
            try:
                text = elem.inner_text() or elem.get_attribute('href') or '[No text]'
                print(f'  Element {i}: {text}')
            except Exception as e:
                print(f'  Element {i}: Error getting text: {e}')

        # Try to navigate directly to settings page
        try:
            page.goto('http://localhost:12000/settings')
            page.wait_for_selector('body', timeout=5000)
            page.screenshot(path='/tmp/openhands-settings-screenshot.png')
            print(f'Navigated directly to settings page: {page.url}')
        except Exception as e:
            print(f'Failed to navigate directly to settings: {e}')

        # Go back to home page
        page.goto('http://localhost:12000/')
        page.wait_for_selector('body', timeout=5000)

        # Verify we can at least interact with the page
        assert page.url.startswith('http://localhost:12000/'), (
            'Failed to load OpenHands application'
        )

        # Take a final screenshot
        page.screenshot(path='/tmp/openhands-final-screenshot.png')

        print('Successfully completed the OpenHands basic workflow test')
    except Exception as e:
        # Take a screenshot on failure
        try:
            page.screenshot(path='/tmp/openhands-error-screenshot.png')
            print('Error screenshot saved to /tmp/openhands-error-screenshot.png')
        except Exception as screenshot_error:
            print(f'Failed to save error screenshot: {screenshot_error}')
        raise e
