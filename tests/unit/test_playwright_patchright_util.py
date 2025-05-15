#!/usr/bin/env python3
"""Test script for the playwright_patchright_util module."""

import logging
import sys

from openhands.utils.playwright_patchright_util import use_patchright

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_patchright_import():
    """Test that patchright can be imported and used as a replacement for playwright."""
    # Use patchright as a replacement for playwright
    use_patchright()

    # Now import playwright - this must be imported after use_patchright() is called
    import playwright.sync_api  # noqa: F401

    # Check that the import worked
    assert 'playwright.sync_api' in sys.modules

    # Check that the actual module is patchright
    playwright_modules = [
        name
        for name in sys.modules.keys()
        if name == 'playwright' or name.startswith('playwright.')
    ]
    assert len(playwright_modules) > 0

    # Check that patchright modules are loaded
    patchright_modules = [
        name
        for name in sys.modules.keys()
        if name == 'patchright' or name.startswith('patchright.')
    ]
    assert len(patchright_modules) > 0


def test_patchright_functionality():
    """Test that patchright functionality works through the playwright import."""
    # Use patchright as a replacement for playwright
    use_patchright()

    # Import playwright - this must be imported after use_patchright() is called
    import playwright
    from playwright.sync_api import sync_playwright

    # print the actual package name and file
    print(f'Actual playwright package name: {playwright.__name__}')
    print(f'Actual playwright package file: {playwright.__file__}')
    assert 'patchright' in playwright.__file__

    # Use playwright (which is actually patchright)
    with sync_playwright() as p:
        # Launch a browser
        browser = p.chromium.launch(headless=True)

        # Create a new page
        page = browser.new_page()

        # Navigate to a URL
        page.goto('https://example.com')

        # Check that we can get the title
        title = page.title()
        assert 'Example' in title

        # Close the browser
        browser.close()
