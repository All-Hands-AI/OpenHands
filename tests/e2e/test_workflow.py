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


def test_openhands_web_interface(page, openhands_app):
    """
    Test the OpenHands web interface loading and basic functionality.

    This test focuses on the web UI without requiring full agent functionality:
    1. Navigate to OpenHands web interface
    2. Verify the page loads correctly
    3. Check that basic UI elements are present
    4. Verify the interface is responsive
    """
    # Create test-results directory if it doesn't exist
    os.makedirs('test-results', exist_ok=True)

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

        # Verify the page contains expected content
        expect(page).to_have_title('OpenHands')
        print('Page title is correct')

    except Exception as e:
        print(f'Error checking page load: {e}')
        page.screenshot(path='test-results/page_error.png')
        raise

    # Check for basic UI elements
    print('Checking for basic UI elements...')
    try:
        # Check if the root layout container is visible
        root_layout = page.locator('[data-testid="root-layout"]')
        expect(root_layout).to_be_visible(timeout=10000)
        print('Root layout container is visible')

        # Check for the root outlet (main content area)
        root_outlet = page.locator('#root-outlet')
        expect(root_outlet).to_be_visible(timeout=10000)
        print('Root outlet (main content area) is visible')

        # Take a screenshot of the loaded interface
        page.screenshot(path='test-results/interface_loaded.png')
        print('Screenshot saved as interface_loaded.png')

    except Exception as e:
        print(f'Error checking UI elements: {e}')
        page.screenshot(path='test-results/ui_error.png')
        raise

    print('OpenHands web interface test completed successfully!')
