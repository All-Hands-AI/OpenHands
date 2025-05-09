import base64
import os
from unittest.mock import MagicMock

import pytest

from openhands.core.schema import ActionType
from openhands.events.action import BrowseInteractiveAction, BrowseURLAction
from openhands.events.observation import BrowserOutputObservation
from openhands.runtime.browser.utils import browse


@pytest.fixture
def mock_browser():
    browser = MagicMock()
    # Use a synchronous mock instead of AsyncMock for step
    browser.step = MagicMock(return_value={})
    return browser


@pytest.fixture
def sample_screenshot():
    # Create a small 1x1 pixel PNG image in base64
    return 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=='


@pytest.mark.asyncio
async def test_browse_saves_screenshot_when_workspace_provided(
    mock_browser, sample_screenshot, tmp_path
):
    # Setup
    workspace_dir = str(tmp_path)
    mock_browser.step.return_value = {
        'text_content': 'Sample webpage content',
        'url': 'https://example.com',
        'screenshot': sample_screenshot,
        'last_action': 'goto',
    }

    action = BrowseURLAction(url='https://example.com')

    # Execute
    result = await browse(action, mock_browser, workspace_dir)

    # Verify
    assert result.screenshot_path is not None
    assert os.path.exists(result.screenshot_path)
    assert result.screenshot_path.startswith(str(tmp_path / '.browser_screenshots'))

    # Check if the screenshot directory was created
    screenshots_dir = tmp_path / '.browser_screenshots'
    assert screenshots_dir.exists()
    assert screenshots_dir.is_dir()

    # Check if the screenshot file contains the expected data
    with open(result.screenshot_path, 'rb') as f:
        saved_data = f.read()
    expected_data = base64.b64decode(sample_screenshot)
    assert saved_data == expected_data


@pytest.mark.asyncio
async def test_browse_interactive_saves_screenshot_when_workspace_provided(
    mock_browser, sample_screenshot, tmp_path
):
    # Setup
    workspace_dir = str(tmp_path)
    mock_browser.step.return_value = {
        'text_content': 'Sample webpage content',
        'url': 'https://example.com',
        'screenshot': sample_screenshot,
        'last_action': 'click',
    }

    action = BrowseInteractiveAction(browser_actions='click("button")')

    # Execute
    result = await browse(action, mock_browser, workspace_dir)

    # Verify
    assert result.screenshot_path is not None
    assert os.path.exists(result.screenshot_path)
    assert result.screenshot_path.startswith(str(tmp_path / '.browser_screenshots'))


@pytest.mark.asyncio
async def test_browse_does_not_save_screenshot_when_workspace_not_provided(
    mock_browser, sample_screenshot
):
    # Setup
    mock_browser.step.return_value = {
        'text_content': 'Sample webpage content',
        'url': 'https://example.com',
        'screenshot': sample_screenshot,
        'last_action': 'goto',
    }

    action = BrowseURLAction(url='https://example.com')

    # Execute
    result = await browse(action, mock_browser)

    # Verify
    assert result.screenshot_path is None


@pytest.mark.asyncio
async def test_screenshot_path_included_in_agent_obs_text(sample_screenshot):
    # Create a BrowserOutputObservation with a screenshot path for BROWSE_INTERACTIVE
    obs = BrowserOutputObservation(
        url='https://example.com',
        trigger_by_action=ActionType.BROWSE_INTERACTIVE,
        content='Sample content',
        screenshot=sample_screenshot,
        screenshot_path='/path/to/screenshot.png',
    )

    # Get the agent observation text
    agent_text = obs.get_agent_obs_text()

    # Verify the screenshot path is included for BROWSE_INTERACTIVE
    assert '[Screenshot saved to: /path/to/screenshot.png]' in agent_text

    # Test with BROWSE action type - should NOT include screenshot path
    obs.trigger_by_action = ActionType.BROWSE
    agent_text = obs.get_agent_obs_text()
    assert '[Screenshot saved to: /path/to/screenshot.png]' not in agent_text
